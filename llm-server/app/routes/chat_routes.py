# routes/chat_routes.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncIterator, Dict, List, Optional, Tuple

from app.services.rag_next import get_next_question, mark_question_asked
from app.services.chat_services import extract_symptom, retrieve_symptom_questions
from app.services.dynamodb_services import save_chat_history_to_dynamodb
from app.services.validators import validate_user_input
from app.prompts.symptom_qs_prompt import run_langchain_extraction
from langchain_openai import ChatOpenAI

router = APIRouter()

class Query(BaseModel):
    session_id: str
    patient_id: str
    message: str

SECTION_ORDER = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]

# Coverage targets
SECTION_MIN = {
    "chiefComplaint": 1,
    "HPI": 4,
    "PMH": 1,
    "Medications": 1,
    "SH": 1,
    "FH": 1,
}
SECTION_MAX = {
    "chiefComplaint": 1,
    "HPI": 6,
    "PMH": 2,
    "Medications": 1,
    "SH": 2,
    "FH": 1,
}

# ---- Session state (in-memory) ----
session_symptom_map: Dict[str, str] = {}
# e.g. {"id": "...", "symptom": "...", "section": "HPI", "question_text": "..."}
session_last_doc_meta: Dict[str, Dict[str, str]] = {}
# {sec: [ {"q": "...", "a": "..."} ]}
session_qas_map: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
# Track current section in the conversation flow
session_current_section: Dict[str, str] = {}

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ---------- Coverage helpers ----------
def section_count(session_id: str, section: str) -> int:
    return len(session_qas_map.get(session_id, {}).get(section, []))

def has_met_min_coverage(session_id: str) -> bool:
    for sec in SECTION_ORDER:
        if section_count(session_id, sec) < SECTION_MIN[sec]:
            return False
    return True

def is_at_max_for_section(session_id: str, section: str) -> bool:
    return section_count(session_id, section) >= SECTION_MAX[section]

def advance_to_next_section(session_id: str, current_section: str) -> Optional[str]:
    try:
        idx = SECTION_ORDER.index(current_section)
    except ValueError:
        idx = -1
    for j in range(idx + 1, len(SECTION_ORDER)):
        sec = SECTION_ORDER[j]
        if not is_at_max_for_section(session_id, sec):
            session_current_section[session_id] = sec
            return sec
    return None

async def try_get_next_in_or_after_section(
    session_id: str,
    symptom: str,
    user_hint: str,
    start_section: str,
):
    """Try current section; if none, advance until a question is found or sections are exhausted."""
    # Try current section
    nxt = await get_next_question(
        session_id,
        symptom,
        user_hint=user_hint,
        section_filter=start_section,
    )
    if nxt:
        return start_section, nxt

    # Otherwise advance through remaining sections
    sec = advance_to_next_section(session_id, start_section)
    while sec:
        nxt = await get_next_question(
            session_id,
            symptom,
            user_hint=user_hint,
            section_filter=sec,
        )
        if nxt:
            return sec, nxt
        sec = advance_to_next_section(session_id, sec)

    # Nothing found anywhere
    return None, None

# ---------- Route ----------
@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id
    user_message = (query.message or "").strip()

    # ---- First turn: detect symptom, init state, ask CC first ----
    if session_id not in session_symptom_map:
        symptom = extract_symptom(user_message)
        if not symptom:
            return stream_response(
                "To get started, what symptom brings you in today? (e.g., cough, fever, sore throat)"
            )

        # Initialize session
        session_symptom_map[session_id] = symptom
        session_last_doc_meta[session_id] = {}
        session_qas_map[session_id] = {sec: [] for sec in SECTION_ORDER}
        session_current_section[session_id] = "chiefComplaint"

        # Ask chiefComplaint[0] from JSON if available; otherwise generic CC
        qs = retrieve_symptom_questions(symptom) or {}
        cc_list = qs.get("chiefComplaint", [])
        if cc_list:
            next_question = cc_list[0]
        else:
            next_question = (
                f"What brings you in today related to your {symptom}?"
                if symptom != "unspecified" else
                "What brings you in today?"
            )

        # Mark CC as asked so RAG won’t repeat it later
        mark_question_asked(session_id, next_question)

        # Stash meta so we can store the answer next turn
        session_last_doc_meta[session_id] = {
            "id": "",
            "symptom": symptom,
            "section": "chiefComplaint",
            "question_text": next_question,
        }
        return stream_response(next_question)

    # ---- Subsequent turns ----
    symptom = session_symptom_map[session_id]
    last_q = (session_last_doc_meta.get(session_id, {}).get("question_text") or "").strip()

    # Validate input; do NOT advance on invalid input
    ok, why = await validate_user_input(symptom, user_message, last_question=last_q)
    if not ok:
        msg = why if (not last_q or last_q in why) else f"{why} {last_q}"
        return stream_response(msg)

    # Save Q&A pair for the section we last asked from
    last_meta = session_last_doc_meta.get(session_id, {})
    last_section = last_meta.get("section", "HPI")
    if last_q:
        session_qas_map[session_id][last_section].append({"q": last_q, "a": user_message})

    # Determine current section (may advance if section hit MAX)
    current_section = session_current_section.get(session_id, "chiefComplaint")
    if is_at_max_for_section(session_id, current_section):
        next_sec = advance_to_next_section(session_id, current_section)
        if next_sec:
            current_section = next_sec

    # If ALL mins are already met, finish right away (even if RAG has more)
    if has_met_min_coverage(session_id):
        extracted = await run_langchain_extraction(session_qas_map[session_id])
        save_chat_history_to_dynamodb(patient_id, session_id, extracted)
        _cleanup_session(session_id)
        return stream_response("Thanks! I’ve collected everything I need.")

    # Try to get a question in current section; if none, advance until we find one
    target_section, nxt = await try_get_next_in_or_after_section(
        session_id,
        symptom,
        user_hint=user_message if user_message else symptom,
        start_section=current_section,
    )

    if not nxt:
        # No more questions anywhere → if mins met, finish; otherwise finish best‑effort
        extracted = await run_langchain_extraction(session_qas_map[session_id])
        save_chat_history_to_dynamodb(patient_id, session_id, extracted)
        _cleanup_session(session_id)
        return stream_response("Thanks! I’ve collected everything I need.")

    # Ask the found question
    next_question, meta = nxt
    meta["question_text"] = next_question
    # Update current section in case we advanced
    if target_section:
        session_current_section[session_id] = target_section
        meta["section"] = target_section
    session_last_doc_meta[session_id] = meta

    return stream_response(next_question)

# ---- SSE helper ----
def stream_response(message: str) -> StreamingResponse:
    async def streaming_generator() -> AsyncIterator[str]:
        yield f"data: {message}\n\n"
    return StreamingResponse(streaming_generator(), media_type="text/event-stream")

# ---- cleanup ----
def _cleanup_session(session_id: str) -> None:
    session_symptom_map.pop(session_id, None)
    session_last_doc_meta.pop(session_id, None)
    session_qas_map.pop(session_id, None)
    session_current_section.pop(session_id, None)
