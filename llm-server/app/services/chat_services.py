import os, json
import numpy as np
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
