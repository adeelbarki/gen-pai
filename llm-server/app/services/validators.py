# app/services/validators.py
import re
from typing import Tuple, Optional
from redisvl.query.filter import Tag
from app.vectorstore_config import vectorstore

# exact chit-chat phrases (lowercased)
CHITCHAT_PAT = re.compile(
    r"^(?:hi|hello|hey|thanks|thank you|good morning|good night|how are you|what's up|lol|ok|okay|k|cool)[\s\.\!\?]*$",
    re.I,
)

YESNO = {
    "yes", "yeah", "yep", "yup", "no", "nope", "nah",
    "not really", "i don't", "i do not", "i am not"
}

WORD_NUM = r"one|two|three|four|five|six|seven|eight|nine|ten|couple|few|several"

DURATION_RE = re.compile(
    rf"\b((\d+)|({WORD_NUM}))\s*(min|mins|minute|minutes|hr|hour|hours|day|days|week|weeks|month|months|year|years)\b"
    r"|today|yesterday|last night|this morning|this evening|tonight",
    re.I,
)

TEMPERATURE_RE = re.compile(r"\b(1[0-1]\d(\.\d+)?|[3-4]\d(\.\d+)?)[°\s]?(c|f)\b", re.I)  # e.g., 38.2 C, 101 F
SEVERITY_RE    = re.compile(r"\b(mild|moderate|severe|worse|improving|unchanged)\b", re.I)
BREVITY_WORDS  = re.compile(r"\b(none|no|yes)\b", re.I)

def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def is_trivial(s: str) -> bool:
    """True only if the input is empty/whitespace."""
    return len(_norm(s)) == 0

def is_chitchat(s: str) -> bool:
    """Only treat as chit-chat if the entire message is a chit-chat phrase (no substring matching)."""
    return bool(CHITCHAT_PAT.match((s or "").strip()))

def looks_like_answer(s: str, last_question: Optional[str]) -> bool:
    """
    Be generous: accept typical clinical replies (yes/no, durations, severity,
    symptoms, temperatures). If we have a last question, accept nearly anything non-empty.
    """
    s2 = _norm(s)
    if not s2:
        return False

    if s2 in YESNO or s2 in {"no fever", "no chills"}:
        return True
    if DURATION_RE.search(s2):
        return True
    if TEMPERATURE_RE.search(s2):
        return True
    if SEVERITY_RE.search(s2):
        return True
    if len(s2) <= 4 and BREVITY_WORDS.search(s2):
        return True
    if any(tok in s2 for tok in ["cough", "fever", "phlegm", "sputum", "chest", "shortness", "asthma", "smoke", "pain", "chills"]):
        return True
    if last_question:
        return True
    return False

async def is_medically_relevant(symptom: str, user_text: str, threshold: float = 0.35) -> Tuple[bool, float]:
    """
    OPTIONAL soft relevance check against the symptom's question space.
    If scores are unavailable, don't block the flow.
    """
    try:
        flt = Tag("symptom") == symptom
        try:
            # Prefer with-score API if available
            hits = vectorstore.similarity_search_with_score(user_text, k=1, filter=flt)  # type: ignore[attr-defined]
            if not hits:
                return (False, 999.0)
            _, score = hits[0]
            return (score < threshold, score)  # cosine distance: lower is closer
        except Exception:
            # Fallback: existence check via retriever
            docs = await vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 1, "filter": flt}
            ).aget_relevant_documents(user_text)
            return (bool(docs), 0.0 if docs else 999.0)
    except Exception:
        # Fail open: don't block flow if retrieval fails
        return (True, 0.0)

async def validate_user_input(symptom: str, user_text: str, last_question: Optional[str] = None) -> Tuple[bool, str]:
    """
    Accept unless it's clearly empty or chit-chat. Relevance is a soft fallback.
    """
    if is_trivial(user_text):
        return False, "I didn’t catch that. Could you share a bit more?"
    # Prioritize actual answers before chit-chat check
    if looks_like_answer(user_text, last_question):
        return True, ""
    if is_chitchat(user_text):
        return False, "Let’s focus on your symptoms."
    # Optional soft relevance nudge
    relevant, _ = await is_medically_relevant(symptom, user_text)
    if not relevant and last_question:
        return False, "That doesn’t seem related to the question."
    return True, ""
