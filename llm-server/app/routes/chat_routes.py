# routes/chat_routes.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncIterator

from app.services.chat_services import extract_symptom, retrieve_symptom_questions
from ..config import OPENAI_API_KEY

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.memory import ConversationSummaryBufferMemory

router = APIRouter()

LLM = ChatOpenAI(model="gpt-4o")

memories: dict[str, ConversationSummaryBufferMemory] = {}

class Query(BaseModel):
    session_id: str
    message: str


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
    memory = get_memory(session_id)

    # Extract symptom
    user_symptom = extract_symptom(query.message)

    # Inject RAG symptom questions
    if user_symptom:
        qs = retrieve_symptom_questions(user_symptom)
        if qs:
            rag_msg = SystemMessage(content=(
                f"You are helping take a history from a patient who reported **{user_symptom}**.\n"
                f"Use these symptom-specific questions as guidance:\n"
                + "\n".join(f"- {q}" for q in qs)
                + "\n\nAsk them **one at a time**, based on what the user has already said. "
                  "Be natural and do not repeat questions."
            ))
            if all(rag_msg.content != m.content for m in memory.chat_memory.messages
                   if isinstance(m, SystemMessage)):
                memory.chat_memory.messages.insert(2, rag_msg)

    # Add user's latest message to history
    memory.chat_memory.add_message(HumanMessage(content=query.message))

    # Streaming response
    async def streaming_generator() -> AsyncIterator[str]:
        handler = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(
            model="gpt-4o",
            streaming=True,
            callbacks=[handler]
        )

        async def task():
            try:
                response = await llm.ainvoke(memory.chat_memory.messages)
                memory.chat_memory.add_message(AIMessage(content=response.content))
            except Exception as e:
                await handler.on_llm_error(e)

        import asyncio
        asyncio.create_task(task())
        async for token in handler.aiter():
            yield token


    return StreamingResponse(streaming_generator(), media_type="text/event-stream")
