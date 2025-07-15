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
from .config import OPENAI_API_KEY
from .models.xray_model import predict
import boto3
import json
from io import BytesIO
import gzip

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
session = boto3.Session(profile_name="medical-image-user")
sqs = session.client('sqs', region_name="us-east-1")
healthimaging = session.client('medical-imaging')

# Constants
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/891377377689/DICOMImportMetadataQueue"
DATASTORE_ID = "d9e0f11e8cc44d49aef0703b89372fcd"


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
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=3
    )

    if "Messages" not in messages:
        return {"message": "No messages in queue"}

    for msg in messages["Messages"]:
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
        
        response = healthimaging.get_image_set_metadata(
            datastoreId=DATASTORE_ID,
            imageSetId=image_set_id
        )

        blob_stream = response["imageSetMetadataBlob"]
        decompressed_bytes = gzip.decompress(blob_stream.read())
        metadata_json = json.loads(decompressed_bytes)

        print("Decompressed Metadata:", json.dumps(metadata_json, indent=2))

        series_dict = metadata_json.get("Study", {}).get("Series", {})

        frame_id = None

        for series_uid, series_data in series_dict.items():
            instances = series_data.get("Instances", {})
            for instance_uid, instance_data in instances.items():
                frames = instance_data.get("ImageFrames", [])
                if frames:
                    frame_id = frames[0].get("ID")
                    break
            if frame_id:
                break

        if not frame_id:
            return {"error": "No frame ID found in decompressed metadata"}

        image_response = healthimaging.get_image_frame(
            datastoreId=DATASTORE_ID,
            imageSetId=image_set_id,
            imageFrameInformation={
                "imageFrameId": frame_id
            }
        )

        image_bytes = image_response["imageFrameBlob"].read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        label, confidence = predict(image)

        # Delete message
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )

        return {
            "prediction": label,
            "confidence": confidence
        }

    return {"message": "Finished processing"}