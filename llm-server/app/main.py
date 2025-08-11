from fastapi import FastAPI
import os, json
from contextlib import asynccontextmanager
from .redis_config import r, ensure_symptom_index_exists
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
from app.services.rag_setup import upsert_symptom_questions_to_vectorstore
from langchain_redis import RedisVectorStore
from langchain_redis.config import RedisConfig
from redis import Redis
from langchain_openai import OpenAIEmbeddings



RAG_INDEX_NAME = "symptom_question_rag"
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

config = RedisConfig(
    index_name=RAG_INDEX_NAME,
    dimensions=1536,
    distance_metric="COSINE",
    vector_index_type="FLAT",
    vector_datatype="FLOAT32",
    # make metadata filterable
    metadata_schema=[
        {"name": "symptom", "type": "tag"},
        {"name": "section", "type": "tag"},
    ],
    key_prefix="doc"
)

vectorstore = RedisVectorStore(
    redis_url="redis://localhost:6379",
    # index_name=RAG_INDEX_NAME,
    config=config,
    embeddings=embedding_model,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_symptom_index_exists()

    upsert_symptom_questions_to_vectorstore(vectorstore, symptom_questions)
    
    from redisvl.query.filter import Tag

    flt = Tag("symptom") == "cough"
    docs2 = vectorstore.similarity_search("start", k=3, filter=flt)
    print("with-filter:", [(d.page_content, d.metadata) for d in docs2])
   
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
