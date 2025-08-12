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

# Per‑section quotas to keep the convo tidy
SECTION_QUOTAS = {
    "chiefComplaint": 1,
    "HPI": 4,
    "PMH": 1,
    "Medications": 1,
    "SH": 1,
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
    section = last_meta.get("section", "HPI")
    if last_q:
        session_qas_map[session_id][section].append({"q": last_q, "a": user_message})

    # Check quota and advance section if needed
    current_section = session_current_section.get(session_id, "chiefComplaint")
    if len(session_qas_map[session_id][current_section]) >= SECTION_QUOTAS[current_section]:
        curr_idx = SECTION_ORDER.index(current_section)
        if curr_idx + 1 < len(SECTION_ORDER):
            current_section = SECTION_ORDER[curr_idx + 1]
            session_current_section[session_id] = current_section

    # Try to get the next question for the (possibly updated) current section
    nxt = await get_next_question(
        session_id,
        symptom,
        user_hint=user_message if user_message else symptom,
        section_filter=current_section,
    )

    # If no question in the current section, try advancing until we find one or exhaust sections
    if not nxt:
        curr_idx = SECTION_ORDER.index(current_section)
        found = None
        while curr_idx + 1 < len(SECTION_ORDER):
            curr_idx += 1
            session_current_section[session_id] = SECTION_ORDER[curr_idx]
            nxt = await get_next_question(
                session_id,
                symptom,
                user_hint=user_message if user_message else symptom,
                section_filter=session_current_section[session_id],
            )
            if nxt:
                found = nxt
                break

        if not found:
            # No more questions → extract, save, cleanup, finish
            extracted = await run_langchain_extraction(session_qas_map[session_id])
            save_chat_history_to_dynamodb(patient_id, session_id, extracted)
            _cleanup_session(session_id)
            return stream_response("Thanks! I’ve collected everything I need.")
        else:
            next_question, meta = found
            meta["question_text"] = next_question
            session_last_doc_meta[session_id] = meta
            return stream_response(next_question)

    # We have a next question in the current section
    next_question, meta = nxt
    meta["question_text"] = next_question
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
