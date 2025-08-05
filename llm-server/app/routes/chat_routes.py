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
from app.services.rag_chain import rag_chain

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.memory import ConversationSummaryBufferMemory
import json

router = APIRouter()

LLM = ChatOpenAI(model="gpt-4o")

memories: dict[str, ConversationSummaryBufferMemory] = {}

class Query(BaseModel):
    session_id: str
    patient_id: str
    message: str

session_symptom_map: dict[str, str] = {}
question_index_map: dict[str, int] = {}
question_progress_map: dict[str, dict[str, int]] = {}
section_order = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]


def get_memory(session_id: str) -> ConversationSummaryBufferMemory:
    if session_id not in memories:
        memory = ConversationSummaryBufferMemory(
            llm=LLM,
            max_token_limit=6_000,
            return_messages=True,
        )
        memory.chat_memory.messages.extend([
            SystemMessage(
                content=(
                    "You are a helpful assistant.\n"
                    "Respond using Markdown formatting:\n"
                    "- Use headings for major sections\n"
                    "- Use **bold** for key points\n"
                    "- Use bullet points where helpful\n"
                    "- Write in clear, concise language"
                )
            ),
            SystemMessage(
                content=(
                    "You are a compassionate and intelligent virtual doctor assistant. "
                    "Your task is to take a detailed history from the patient, asking one question at a time like a real physician.\n\n"
                    "Follow this order:\n"
                    "1. Start with the chief complaint.\n"
                    "2. Ask about the history of present illness (onset, duration, severity, triggers).\n"
                    "3. Ask associated symptoms (e.g. fever, fatigue, shortness of breath).\n"
                    "4. Ask about past medical history.\n"
                    "5. Ask about medications, allergies, lifestyle, recent travel, or exposures.\n"
                    "6. Be concise, empathetic, and avoid repeating questions. Stop when you've collected enough history.\n\n"
                    "Only ask one question at a time. Do not jump to conclusions or give advice yet. Just collect information."
                )
            )
        ])
        memories[session_id] = memory

    return memories[session_id]


@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id
    memory = get_memory(session_id)

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
