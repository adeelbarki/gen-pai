import os, json, gzip
import numpy as np
from PIL import Image
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import openai
from ..redis_config import r
from ..models.xray_model import predict
from ..config import OPENAI_API_KEY



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
    from redis.commands.search.query import Query as RedisQuery

    query_vector = get_embeddings(symptom).astype(np.float32).tobytes()
    query = (
        RedisQuery('*=>[KNN 1 @embedding $vec_param AS score]')
        .return_fields("symptom", "questions", "score")
        .sort_by("score")
        .dialect(2)
    )
    params = {"vec_param": query_vector}
    result = r.ft("symptom_index").search(query, query_params=params)
    if result.docs:
        return json.loads(result.docs[0].questions)
    return []
