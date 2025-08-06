# routes/chat_routes.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncIterator

from app.services.chat_services import (
    extract_symptom, 
    save_chat_history_to_dynamodb, 
    retrieve_symptom_questions
)
from app.prompts.chat_memory import get_chat_memory
from langchain.schema import AIMessage, HumanMessage, SystemMessage

router = APIRouter()


class Query(BaseModel):
    session_id: str
    patient_id: str
    message: str

session_symptom_map: dict[str, str] = {}
question_index_map: dict[str, int] = {}
question_progress_map: dict[str, dict[str, int]] = {}
section_order = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]



@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id
    memory = get_chat_memory(session_id)

    # Add user message to memory
    memory.chat_memory.add_message(HumanMessage(content=query.message))

    # Init session state if needed
    if session_id not in question_progress_map:
        extracted_symptom = extract_symptom(query.message) or "unspecified"
        session_symptom_map[session_id] = extracted_symptom
        question_progress_map[session_id] = {section: 0 for section in section_order}
        question_progress_map[session_id]["current_section"] = section_order[0]

    # Get session state
    current_symptom = session_symptom_map[session_id]
    questions_by_section = retrieve_symptom_questions(current_symptom)
    session_progress = question_progress_map[session_id]

    # Default response
    next_question = "Thank you. I’ve collected enough information for now."

    # Determine current section and where to start
    current_section = session_progress["current_section"]
    current_index = section_order.index(current_section)

    for section in section_order[current_index:]:
        questions = questions_by_section.get(section, [])
        index = session_progress.get(section, 0)

        if index < len(questions):
            next_question = questions[index]
            session_progress[section] += 1
            session_progress["current_section"] = section
            break

    # Add assistant message to memory
    memory.chat_memory.add_message(AIMessage(content=next_question))

    # Save full history to DynamoDB
    full_history = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in memory.chat_memory.messages
        if isinstance(msg, (SystemMessage, HumanMessage, AIMessage))
    )

    save_chat_history_to_dynamodb(
        patient_id=patient_id,
        session_id=session_id,
        history=full_history
    )

    # Stream response
    async def streaming_generator() -> AsyncIterator[str]:
        yield f"data: {next_question}\n\n"

    return StreamingResponse(streaming_generator(), media_type="text/event-stream")
