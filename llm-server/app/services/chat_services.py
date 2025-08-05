import os, json
import numpy as np
import openai
from boto3.dynamodb.conditions import Key
from ..redis_config import r
from ..config import (
    OPENAI_API_KEY,
    table,
)
from datetime import datetime


openai.api_key = OPENAI_API_KEY


def get_embeddings(text: str, model: str = "text-embedding-3-small") -> np.ndarray:
    try:
        response = openai.embeddings.create(input=[text], model=model)
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"Embedding error: {e}")
        return np.zeros(1536, dtype=np.float32)
    
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

def retrieve_symptom_questions(symptom: str):
    for entry in symptom_questions:
        if entry["symptom"].lower() == symptom.lower():
            return entry.get("questions", {})
    return {}

def save_chat_history_to_dynamodb(
        patient_id: str, 
        session_id: str, 
        history: str):
    item = {
        "patientId": patient_id,
        "SK": f"ChatHistory#{session_id}",
        "recordType": "ChatHistory",
        "timestamp": datetime.utcnow().isoformat(),
        "sessionId": session_id,
        "chat": history
    }

    table.put_item(Item=item)

