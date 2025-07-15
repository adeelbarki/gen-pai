from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel 
from PIL import Image
import io
import os
import redis
import numpy as np
import openai
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query as RedisQuery
from redis.exceptions import ResponseError
from .config import OPENAI_API_KEY, sqs, healthimaging, table, QUEUE_URL, DATASTORE_ID
from .models.xray_model import predict
from decimal import Decimal
import json
from io import BytesIO
from datetime import datetime
import gzip

# os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


app = FastAPI()

openai.api_key = OPENAI_API_KEY

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=False,
)

INDEX_NAME = "item_index"
VECTOR_DIM = 1536
VECTOR_FIELD_NAME = "embedding"
DISTANCE_METRIC = "COSINE"


try:
    r.ft(INDEX_NAME).info()
except:
    try:
        r.ft(INDEX_NAME).dropindex(delete_documents=True)
    except ResponseError:
        pass

    schema = (
        TextField("name"),
        TextField("description"),
        VectorField(VECTOR_FIELD_NAME, "FLAT", {
            "TYPE": "FLOAT32",
            "DIM": VECTOR_DIM,
            "DISTANCE_METRIC": DISTANCE_METRIC
        })
    )

    r.ft(INDEX_NAME).create_index(
        fields=schema,
        definition=IndexDefinition(prefix=["item:"], index_type=IndexType.HASH)
    )

items = {
    "Sneakers": "Comfortable casual shoes for daily wear.",
    "Running Shoes": "Lightweight shoes designed for jogging and running.",
    "Laptop": "High-performance portable computer for work and entertainment."
}

def get_embeddings(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return np.array(response.data[0].embedding)

def store_item_in_redis(name, description, embedding):
    emb_bytes = embedding.astype(np.float32).tobytes()
    r.hset(f"item:{name}", mapping={
        "name": name,
        "description": description,
        VECTOR_FIELD_NAME: emb_bytes
    })

for name, description in items.items():
    key = f"item:{name}"
    if not r.exists(key):
        emb = get_embeddings(description)
        store_item_in_redis(name, description, emb)

def query_similar_items(query_text, top_k=3):
    query_vector = get_embeddings(query_text).astype(np.float32).tobytes()
    base_query = f'*=>[KNN {top_k} @{VECTOR_FIELD_NAME} $vec_param AS score]'

    query = (
        RedisQuery(base_query)
        .sort_by("score")
        .return_fields("name", "description", "score")
        .dialect(2)
    )

    params = {"vec_param": query_vector}
    results = r.ft(INDEX_NAME).search(query, query_params=params)

    matches = []
    for doc in results.docs:
        matches.append({
            "name": doc.name,
            "description": doc.description,
            "score": float(doc.score)
        })

    return matches

# ---------FastAPI route---


class Query(BaseModel):
    question: str

@app.post("/generate-answer")
async def generate_answer(query: Query):
    similar_items = query_similar_items(query.question)
    return {
       "answer": f"✅ [FastAPI] Found similar items for: '{query.question}'",
        "results": similar_items
       }

# --- Endpoint 2: Chest X-ray Classification ---
@app.get("/classify-xray")
async def classify_xray():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(base_dir, "images", "sample03.jpg")
    image = Image.open(image_path).convert("RGB")
    label, confidence = predict(image)
    print({
        "prediction": label,
        "confidence": round(confidence, 3)
    })
    return {
        "prediction": label,
        "confidence": round(confidence, 3)
    }

@app.get("/process-job")
def process_one_job():
    # Fetch one message from the queue
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=3
    )

    if "Messages" not in messages:
        return {"message": "No messages in queue"}

    msg = messages["Messages"][0]
    body = json.loads(msg["Body"])
    print("Received:", body)

    image_set_id = body.get("imageSetId")
    if not image_set_id:
        print("❌ Missing imageSetId in message. Skipping...")
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )
        return {"error": "Message missing imageSetId"}

    # Fetch and decompress image set metadata
    metadata_blob = healthimaging.get_image_set_metadata(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id
    )["imageSetMetadataBlob"]

    metadata_json = json.loads(gzip.decompress(metadata_blob.read()))
    print("Decompressed Metadata:", json.dumps(metadata_json, indent=2))

    # Extract patient ID and frame ID
    patient_id = metadata_json.get("Patient", {}).get("DICOM", {}).get("PatientID")

    # Extract first available image frame ID
    frame_id = next(
        (
            frame.get("ID")
            for series in metadata_json.get("Study", {}).get("Series", {}).values()
            for instance in series.get("Instances", {}).values()
            for frame in instance.get("ImageFrames", [])
            if "ID" in frame
        ),
        None
    )

    if not frame_id:
        return {"error": "No frame ID found in metadata"}

    # Fetch image and run prediction
    image_bytes = healthimaging.get_image_frame(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id,
        imageFrameInformation={"imageFrameId": frame_id}
    )["imageFrameBlob"].read()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    label, confidence = predict(image)

    # Save to DynamoDB
    table.put_item(
        Item={
            "imageSetId": image_set_id,
            "patientId": patient_id,
            "prediction": label,
            "confidence": Decimal(str(confidence)),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Clean up processed message
    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=msg["ReceiptHandle"]
    )

    return {
        "prediction": label,
        "confidence": round(confidence, 3),
        "patientId": patient_id
    }
