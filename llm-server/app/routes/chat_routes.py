# routes/chat_routes.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncIterator, Dict, List, Optional, Tuple

from app.services.rag_next import get_next_question
from app.services.chat_services import extract_symptom
from app.services.chat_services import save_chat_history_to_dynamodb
from app.prompts.symptom_qs_prompt import run_langchain_extraction
from langchain_openai import ChatOpenAI

router = APIRouter()

class Query(BaseModel):
    session_id: str
    patient_id: str
    message: str

SECTION_ORDER = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]

# ---- Session state (in-memory) ----
# Symptom per session
session_symptom_map: Dict[str, str] = {}
# Last asked question metadata (to file next answer correctly)
# e.g. {"id": "...", "symptom": "...", "section": "HPI", "question_text": "..."}
session_last_doc_meta: Dict[str, Dict[str, str]] = {}
# Q&A pairs per section: {sec: [ {"q": "...", "a": "..."}, ... ] }
session_qas_map: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

# (Optional) Keep an LLM handy for other tasks if you need it later
llm = ChatOpenAI(model="gpt-4o", temperature=0)

@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id
    user_message = (query.message or "").strip()

    # ---- First turn: detect symptom, init state, ask first question ----
    if session_id not in session_symptom_map:
        symptom = extract_symptom(user_message) or "unspecified"
        session_symptom_map[session_id] = symptom
        session_last_doc_meta[session_id] = {}
        session_qas_map[session_id] = {sec: [] for sec in SECTION_ORDER}

        # Ask first question via RAG (hint = symptom)
        nxt = await get_next_question(session_id, symptom, user_hint=symptom)
        if not nxt:
            # Nothing to ask — extract whatever we have (likely empty) and finish
            extracted = await run_langchain_extraction(session_qas_map[session_id])
            save_chat_history_to_dynamodb(patient_id, session_id, extracted)
            _cleanup_session(session_id)
            return stream_response("Thanks! I’ve collected everything I need.")

        next_question, meta = nxt
        # Stash the text so we can pair it with the user's reply on the next turn
        meta["question_text"] = next_question
        session_last_doc_meta[session_id] = meta

        return stream_response(next_question)

    # ---- Subsequent turns: save the answer with the last question, then ask the next ----
    last_meta = session_last_doc_meta.get(session_id, {})
    section = last_meta.get("section", "HPI")
    last_q = (last_meta.get("question_text") or "").strip()

    # Only record if we actually had a question last turn
    if last_q:
        session_qas_map[session_id][section].append({"q": last_q, "a": user_message})

    # Get next question, guided by the user's latest answer
    symptom = session_symptom_map[session_id]
    nxt = await get_next_question(session_id, symptom, user_hint=user_message)

    if not nxt:
        # No more questions — extract structured summary and save
        extracted = await run_langchain_extraction(session_qas_map[session_id])
        save_chat_history_to_dynamodb(patient_id, session_id, extracted)
        _cleanup_session(session_id)
        return stream_response("Thanks! I’ve collected everything I need.")

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
