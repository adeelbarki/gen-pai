from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncIterator, Dict, List, Optional, Set, Tuple
from app.services.rag_next import get_next_question
from app.services.chat_services import (
    extract_symptom, 
    save_chat_history_to_dynamodb, 
    retrieve_symptom_questions
)
from app.prompts.symptom_qs_prompt import run_langchain_extraction
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

router = APIRouter()


class Query(BaseModel):
    session_id: str
    patient_id: str
    message: str

# ---- Session state (in-memory) ----
# Answers per section
session_answers_map: Dict[str, Dict[str, List[str]]] = {}
# Symptom per session
session_symptom_map: Dict[str, str] = {}
# Asked doc IDs (to avoid repeats)
session_asked_ids: Dict[str, Set[str]] = {}
# Last asked question's doc metadata (so we know which section to save the user's answer to)
session_last_doc_meta: Dict[str, Dict[str, str]] = {}

# Fixed section order if you want to use it later (optional)
SECTION_ORDER = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]

# Your LLM for any downstream use (not used to generate questions here)
llm = ChatOpenAI(model="gpt-4o", temperature=0)



@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id
    user_message = query.message.strip()

    if session_id not in session_symptom_map:
        symptom = extract_symptom(user_message) or "unspecified"
        session_symptom_map[session_id] = symptom
        session_answers_map[session_id] = {sec: [] for sec in SECTION_ORDER}
        session_asked_ids[session_id] = set()
        session_last_doc_meta[session_id] = {}

        # Ask first question via RAG (no prior hint besides symptom)
        nxt = await get_next_question(session_id, symptom, user_hint=symptom)
        if not nxt:
            # no questions available; end flow
            extracted = await run_langchain_extraction(session_answers_map[session_id])
            save_chat_history_to_dynamodb(patient_id, session_id, extracted)
            _cleanup_session(session_id)
            return stream_response("Thanks! I’ve collected everything I need.")
        
        next_question, meta = nxt
        session_last_doc_meta[session_id] = meta
        print(">>> next_q:", repr(next_question))
        return stream_response(next_question)
    
    last_meta = session_last_doc_meta.get(session_id, {})
    section = last_meta.get("section", "HPI")
    session_answers_map[session_id][section].append(user_message)

    symptom = session_symptom_map[session_id]
    nxt = await get_next_question(session_id, symptom, user_hint=user_message)

    if not nxt:
        extracted = await run_langchain_extraction(session_answers_map[session_id])
        save_chat_history_to_dynamodb(patient_id, session_id, extracted)
        _cleanup_session(session_id)
        return stream_response("Thanks! I’ve collected everything I need.")

    next_question, meta = nxt
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
    session_answers_map.pop(session_id, None)
    session_asked_ids.pop(session_id, None)
    session_last_doc_meta.pop(session_id, None)
