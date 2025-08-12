import os, json
from typing import Dict, List
import openai
from ..redis_config import r
from ..config import (
    OPENAI_API_KEY
)


openai.api_key = OPENAI_API_KEY

    
def extract_symptom(user_input: str) -> str:
    symptom_keywords = ["cough", "fever", "sore throat", "headache", "fatigue", "shortness of breath"]
    for keyword in symptom_keywords:
        if keyword.lower() in user_input.lower():
            return keyword
    return ""

def load_symptom_question_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, "data", "symptom_questions.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
    
symptom_questions = load_symptom_question_data()

SECTION_ORDER = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]

def build_symptom_index(data: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
    idx: Dict[str, Dict[str, List[str]]] = {}
    for entry in data:
        key = entry.get("symptom", "").strip().lower()
        q = entry.get("questions", {}) or {}
        idx[key] = {sec: list(q.get(sec, []) or []) for sec in SECTION_ORDER}
    return idx

SYMPTOM_QS_INDEX = build_symptom_index(symptom_questions)

def set_symptom_index(idx: Dict[str, Dict[str, List[str]]]) -> None:
    """Setter to refresh the module-level index at startup."""
    global SYMPTOM_QS_INDEX
    SYMPTOM_QS_INDEX = idx

def retrieve_symptom_questions(symptom: str) -> Dict[str, List[str]]:
    key = (symptom or "").strip().lower()
    return SYMPTOM_QS_INDEX.get(key, {sec: [] for sec in SECTION_ORDER})