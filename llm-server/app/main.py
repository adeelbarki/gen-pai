from fastapi import FastAPI
from pydantic import BaseModel 

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/generate-answer")
async def generate_answer(query: Query):
    return {
        "answer": f"✅ [FastAPI] Received your question: '{query.question}'. This is coming directly from Python!"
    }