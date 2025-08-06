from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory

memories: dict[str, ConversationSummaryBufferMemory] = {}
LLM = ChatOpenAI(model="gpt-4o")

def get_chat_memory(session_id: str) -> ConversationSummaryBufferMemory:
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
