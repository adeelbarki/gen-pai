from fastapi import FastAPI
from contextlib import asynccontextmanager
from .redis_config import r, ensure_symptom_index_exists
import json
from app.services.chat_services import (
    symptom_questions,
    get_embeddings
)
from app.routes import (
    chat_routes, 
    classify_xray_routes,
    imaging_routes,
    process_ocr_routes,
    physical_exam_results_routes
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_symptom_index_exists()

    for entry in symptom_questions:
        key = f"symptom:{entry['symptom']}"
        if not r.exists(key):
            emb = get_embeddings(entry["symptom"])
            r.hset(key, mapping={
                "symptom": entry["symptom"],
                "questions": json.dumps(entry["questions"]),
                "embedding": emb.tobytes()
            })
    yield


app = FastAPI(lifespan=lifespan)

# --- Endpoint 1: Opneai Question and generate asnwer ---
app.include_router(chat_routes.router)

# --- Endpoint 2: Fetch DICOM xray data from sqs queue and identify penumunia and store in dynamodb ---
app.include_router(classify_xray_routes.router)

# --- Endpoint 3: Extract Image from aws health Imaging, store in s3 and return signed url---
app.include_router(imaging_routes.router)

# --- Endpoint 4: Fetch handwritten note using sqs queue and convert to text---
app.include_router(process_ocr_routes.router)

# --- Endpoint 4: Fetch physical exam results in text file and save to patient records---
app.include_router(physical_exam_results_routes.router)
