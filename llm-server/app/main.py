from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel 
from PIL import Image
from io import BytesIO 
import os, redis, openai
import numpy as np
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query as RedisQuery
from redis.exceptions import ResponseError
from .models.xray_model import predict
from decimal import Decimal
import json, gzip 
from boto3.dynamodb.conditions import Key
from io import BytesIO
from datetime import datetime
from .config import (
    OPENAI_API_KEY,
    sqs,
    healthimaging,
    table,
    QUEUE_URL,
    DATASTORE_ID,
    s3,
    BUCKET_NAME
)



app = FastAPI()

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=False,
)

INDEX_NAME = "symptom_index"
VECTOR_DIM = 1536
VECTOR_FIELD_NAME = "embedding"
DISTANCE_METRIC = "COSINE"

def ensure_symptom_index_exists(r):
    try:
        r.ft(INDEX_NAME).info()
        print(f"✅ Index '{INDEX_NAME}' already exists.")
    except ResponseError as e:
        if "no such index" in str(e).lower():
            print(f"⚠️ Index '{INDEX_NAME}' not found. Creating it now...")
            r.ft(INDEX_NAME).create_index(
                fields=[
                    TextField("symptom"),
                    TextField("questions"),
                    VectorField("embedding", "FLAT", {
                        "TYPE": "FLOAT32",
                        "DIM": VECTOR_DIM,
                        "DISTANCE_METRIC": DISTANCE_METRIC
                    })
                ],
                definition=IndexDefinition(prefix=["symptom:"], index_type=IndexType.HASH)
            )
            print(f"✅ Created index '{INDEX_NAME}'")
        else:
            raise e


def load_symptom_question_data():
    base_dir = os.path.dirname(__file__)
    filepath = os.path.join(base_dir, "data", "symptom_questions.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
    
symptom_questions = load_symptom_question_data()

def get_embeddings(text: str, model: str = "text-embedding-3-small") -> np.ndarray:
    try:
        response = openai.embeddings.create(
            input=[text],
            model=model
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"Embedding error: {e}")
        return np.zeros(1536, dtype=np.float32)

for entry in symptom_questions:
    emb = get_embeddings(entry["symptom"])
    r.hset(f"symptom:{entry['symptom']}", mapping={
        "symptom": entry["symptom"],
        "questions": json.dumps(entry["questions"]),
        "embedding": emb.tobytes()
    })

def retrieve_symptom_questions(symptom):
    query_vector = get_embeddings(symptom).astype(np.float32).tobytes()
    base_query = f'*=>[KNN 1 @embedding $vec_param AS score]'
    query = (
        RedisQuery(base_query)
        .return_fields("symptom", "questions", "score")
        .sort_by("score")
        .dialect(2)
    )
    params = {"vec_param": query_vector}
    result = r.ft("symptom_index").search(query, query_params=params)
    if result.docs:
        return json.loads(result.docs[0].questions)
    return []

def extract_symptom(user_input: str) -> str:
    # Very basic: use keyword match (can be improved with NLP later)
    symptom_keywords = ["cough", "fever", "sore throat", "headache", "fatigue", "shortness of breath"]
    for keyword in symptom_keywords:
        if keyword.lower() in user_input.lower():
            return keyword
    return ""

openai.api_key = OPENAI_API_KEY

chat_histories = {}


class Query(BaseModel):
    session_id: str
    message: str

# --- Endpoint 1: Opneai Question and generate asnwer ---

@app.post("/generate-answer")
async def generate_answer(query: Query):
    ensure_symptom_index_exists(r)
    session_id = query.session_id

    if session_id not in chat_histories:
        chat_histories[session_id] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant.\n"
                    "Respond using Markdown formatting:\n"
                    "- Use headings for major sections\n"
                    "- Use **bold** for key points\n"
                    "- Use bullet points where helpful\n"
                    "- Write in clear, concise language"
                )
            },
            {
                "role": "system",
                "content": (
                    "You are a compassionate and intelligent virtual doctor assistant. "
                    "Your task is to take a detailed history from the patient, asking one question at a time like a real physician.\n\n"
                    "Follow this order:\n"
                    "1. Start with the chief complaint.\n"
                    "2. Ask about the history of present illness (onset, duration, severity, triggers).\n"
                    "3. Ask associated symptoms (e.g. fever, fatigue, shortness of breath).\n"
                    "4. Ask about past medical history.\n"
                    "5. Ask about medications, allergies, lifestyle, recent travel, or exposures.\n"
                    "6. Be concise, empathetic, and avoid repeating questions. Stop when you've collected enough history.\n\n"
                    "Only ask one question at a time. Do not jump to conclusions or give advice yet. Just collect information."
                )
            }
        ]

    # Add user's message to chat history
    chat_histories[session_id].append({"role": "user", "content": query.message})

    def stream_response():
        full_reply = ""

        try:
            # 1. Detect symptom from user input
            user_symptom = extract_symptom(query.message)

            # 2. Retrieve symptom-specific questions using RAG
            if user_symptom:
                retrieved_questions = retrieve_symptom_questions(user_symptom)

                if retrieved_questions:
                    question_list = "\n".join([f"- {q}" for q in retrieved_questions])
                    context_msg = {
                        "role": "system",
                        "content": (
                            f"You are helping take a history from a patient who reported **{user_symptom}**.\n"
                            f"Use these symptom-specific questions as guidance:\n{question_list}\n\n"
                            f"Ask them **one at a time**, based on what the user has already said. Be natural and do not repeat questions."
                        )
                    }

                    # Insert symptom-specific RAG context only once (not every time)
                    # Only insert if not already present in session history
                    if not any(
                        context_msg["content"] in entry["content"]
                        for entry in chat_histories[session_id]
                        if entry["role"] == "system"
                    ):
                        chat_histories[session_id].insert(2, context_msg)

            # 3. Call OpenAI with streaming
            stream = openai.chat.completions.create(
                model="gpt-4",
                messages=chat_histories[session_id],
                stream=True
            )

            for chunk in stream:
                content = getattr(chunk.choices[0].delta, "content", "")
                if isinstance(content, str):
                    full_reply += content
                    yield content

            # 4. Save assistant's reply to history
            chat_histories[session_id].append({"role": "assistant", "content": full_reply})

        except Exception as e:
            yield f"[Error]: {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain")

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

# --- Endpoint 3: Fetch DICOM xray data from sqs queue and identify penumunia and store in dynamodb ---
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


# --- Endpoint 4: Extract Image from aws health Imaging, store in s3 and return the blob---
@app.get("/image-url/{patient_id}")
def get_presigned_image_url(patient_id: str):
    
    response = table.query(
        IndexName="patientId-index",
        KeyConditionExpression=Key("patientId").eq(patient_id)
    )
    
    if not response["Items"]:
        return {"error": "Patient ID not found"}
    
    image_set_id = response["Items"][0]["imageSetId"]

    metadata_blob = healthimaging.get_image_set_metadata(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id
    )["imageSetMetadataBlob"]

    metadata_json = json.loads(gzip.decompress(metadata_blob.read()))

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
        return {"error": "No frame found"}
    
    image_bytes = healthimaging.get_image_frame(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id,
        imageFrameInformation={"imageFrameId": frame_id}
    )["imageFrameBlob"].read()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    s3_key = f"{patient_id}/xrays/{image_set_id}.jpeg"
    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=buffer, ContentType="image/jpeg")

    signed_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600
    )

    return {"url": signed_url}