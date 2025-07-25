# services.py

import os, json, gzip
import numpy as np
from PIL import Image
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import openai
from .redis_config import r
from .models.xray_model import predict
from .config import (
    OPENAI_API_KEY, sqs, healthimaging, table,
    QUEUE_URL, DATASTORE_ID, s3, BUCKET_NAME
)
from .memory_store import chat_histories


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
    base_dir = os.path.dirname(__file__)
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


def classify_sample_xray():
    image_path = os.path.join(os.path.dirname(__file__), "images", "sample03.jpg")
    image = Image.open(image_path).convert("RGB")
    label, confidence = predict(image)
    return {"prediction": label, "confidence": round(confidence, 3)}

def process_one_job():
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=3
    )
    if "Messages" not in messages:
        return {"message": "No messages in queue"}

    msg = messages["Messages"][0]
    body = json.loads(msg["Body"])
    image_set_id = body.get("imageSetId")

    if not image_set_id:
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
        return {"error": "Missing imageSetId"}

    metadata_blob = healthimaging.get_image_set_metadata(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id
    )["imageSetMetadataBlob"]
    metadata_json = json.loads(gzip.decompress(metadata_blob.read()))

    patient_id = metadata_json.get("Patient", {}).get("DICOM", {}).get("PatientID")

    frame_id = next((
        frame.get("ID")
        for series in metadata_json.get("Study", {}).get("Series", {}).values()
        for instance in series.get("Instances", {}).values()
        for frame in instance.get("ImageFrames", [])
        if "ID" in frame
    ), None)

    if not frame_id:
        return {"error": "No frame ID found"}

    image_bytes = healthimaging.get_image_frame(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id,
        imageFrameInformation={"imageFrameId": frame_id}
    )["imageFrameBlob"].read()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    label, confidence = predict(image)

    table.put_item(
        Item={
            "imageSetId": image_set_id,
            "patientId": patient_id,
            "prediction": label,
            "confidence": Decimal(str(confidence)),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])

    return {"prediction": label, "confidence": round(confidence, 3), "patientId": patient_id}

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

    frame_id = next((
        frame.get("ID")
        for series in metadata_json.get("Study", {}).get("Series", {}).values()
        for instance in series.get("Instances", {}).values()
        for frame in instance.get("ImageFrames", [])
        if "ID" in frame
    ), None)

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
