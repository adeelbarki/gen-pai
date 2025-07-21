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

openai.api_key = OPENAI_API_KEY

chat_histories = {}


class Query(BaseModel):
    session_id: str
    message: str

# --- Endpoint 1: Opneai Question and generate asnwer ---

# @app.post("/debug")
# async def debug_payload(request: Request):
#     body = await request.json()
#     return {"received": body}

@app.post("/generate-answer")
async def generate_answer(query: Query):

    print(query)
    session_id = query.session_id
    
    # Initialize history if it's a new session
    if session_id not in chat_histories:
        chat_histories[session_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    

    # Add user's message to history
    chat_histories[session_id].append({"role": "user", "content": query.message})
    
    def stream_response():
        full_reply = ""
        try:
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
            # Save assistant reply to history
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