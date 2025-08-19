from app.prompts.persona_prompt import RED_FLAGS, DOCTOR_SYSTEM
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional
import random

def screen_red_flags(text: str) -> list[str]:
    s = (text or "").lower()
    hits = []
    for cat, items in RED_FLAGS.items():
        for k in items:
            if k in s:
                hits.append(f"{cat}:{k}")
    return hits

_convo_llm = ChatOpenAI(model="gpt-4o", temperature=0.2, top_p=0.9)

def _safe_ack(last_user_reply: Optional[str]) -> str:
    if random.random() < 0.5:
        return ""
    if not last_user_reply:
        return "Thanks for sharing."
    s = last_user_reply.strip().lower()
    if len(s.split()) < 3 or s in {"yes","no","yup","nope","ok","okay","fine","good"}:
        return "Thanks for sharing."
    return f'Thanks for sharing — you said: "{s[:120]}".'

def _is_valid_question(q: str) -> bool:
    q = (q or "").strip()
    if not q or len(q) > 180: return False
    if "\n" in q: return False
    # must be a single question
    return q.endswith("?") and q.count("?") == 1

async def rewrite_question_with_persona(
    question: str,
    last_user_reply: Optional[str] = None,
    symptom: Optional[str] = None,
) -> str:
    ack = _safe_ack(last_user_reply)
    prompt = f"""
        Rewrite the following clinical follow-up question so it sounds like a compassionate primary-care clinician.

        Rules (mandatory):
        - Keep the clinical intent IDENTICAL.
        - Ask ONE question only.
        - Do NOT add, remove, or assume any facts about the patient.
        - If you add an acknowledgement, use this EXACT text and nothing else: "{ack}"
        - Do NOT use phrases like "I'm hearing".
        - Keep total under 28 words.
        - Return ONLY the question line (ack + question), nothing else.

        Original question: "{question}"
        """.strip()

    msg = await _convo_llm.ainvoke([
        SystemMessage(content=DOCTOR_SYSTEM),
        HumanMessage(content=prompt)
    ])
    text = (msg.content or "").strip()
    if not _is_valid_question(text):
        return question
    return text


