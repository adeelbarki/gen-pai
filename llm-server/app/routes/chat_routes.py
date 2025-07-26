from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os, openai
from ..config import OPENAI_API_KEY
from app.services.chat_services import (
    extract_symptom,
    retrieve_symptom_questions
)

openai.api_key = OPENAI_API_KEY
chat_histories = {}

router = APIRouter()

class Query(BaseModel):
    session_id: str
    message: str



@router.post("/generate-answer")
async def generate_answer(query: Query):
    session_id = query.session_id

    if session_id not in chat_histories:
        chat_histories[session_id] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant.\n"
                    "Respond using Markdown formatting:\n"
                    "- Use headings for major sections\n"
                    "- Use **bold** for key points\n"
                    "- Use bullet points where helpful\n"
                    "- Write in clear, concise language"
                )
            },
            {
                "role": "system",
                "content": (
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
            }
        ]

    # Add user's message to chat history
    chat_histories[session_id].append({"role": "user", "content": query.message})

    def stream_response():
        full_reply = ""

        try:
            # 1. Detect symptom from user input
            user_symptom = extract_symptom(query.message)

            # 2. Retrieve symptom-specific questions using RAG
            if user_symptom:
                retrieved_questions = retrieve_symptom_questions(user_symptom)

                if retrieved_questions:
                    question_list = "\n".join([f"- {q}" for q in retrieved_questions])
                    context_msg = {
                        "role": "system",
                        "content": (
                            f"You are helping take a history from a patient who reported **{user_symptom}**.\n"
                            f"Use these symptom-specific questions as guidance:\n{question_list}\n\n"
                            f"Ask them **one at a time**, based on what the user has already said. Be natural and do not repeat questions."
                        )
                    }

                    # Insert symptom-specific RAG context only once (not every time)
                    # Only insert if not already present in session history
                    if not any(
                        context_msg["content"] in entry["content"]
                        for entry in chat_histories[session_id]
                        if entry["role"] == "system"
                    ):
                        chat_histories[session_id].insert(2, context_msg)

            # 3. Call OpenAI with streaming
            stream = openai.chat.completions.create(
                model="gpt-4",
                messages=chat_histories[session_id],
                stream=True
            )

            for chunk in stream:
                content = getattr(chunk.choices[0].delta, "content", "")
                if isinstance(content, str):
                    full_reply += content
                    yield content

            # 4. Save assistant's reply to history
            chat_histories[session_id].append({"role": "assistant", "content": full_reply})

        except Exception as e:
            yield f"[Error]: {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain")