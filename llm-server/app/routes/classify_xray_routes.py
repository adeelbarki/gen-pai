from fastapi import APIRouter
from PIL import Image
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import json, gzip
from ..config import (
    sqs,
    healthimaging,
    table,
    DICOM_IMPORT_QUEUE_URL,
    DATASTORE_ID,
)
from ..models.xray_model import predict

router = APIRouter()

@router.get("/process-job")
def process_one_job():
    messages = sqs.receive_message(
        QueueUrl=DICOM_IMPORT_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=3
    )

    if "Messages" not in messages:
        return {"message": "No messages in queue"}

    msg = messages["Messages"][0]
    body = json.loads(msg["Body"])

    image_set_id = body.get("imageSetId")
    if not image_set_id:
        print("❌ Missing imageSetId in message. Skipping...")
        sqs.delete_message(
            QueueUrl=DICOM_IMPORT_QUEUE_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )
        return {"error": "Message missing imageSetId"}

    # Fetch and decompress image set metadata
    metadata_blob = healthimaging.get_image_set_metadata(
        datastoreId=DATASTORE_ID,
        imageSetId=image_set_id
    )["imageSetMetadataBlob"]

    metadata_json = json.loads(gzip.decompress(metadata_blob.read()))

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
        QueueUrl=DICOM_IMPORT_QUEUE_URL,
        ReceiptHandle=msg["ReceiptHandle"]
    )

    return {
        "prediction": label,
        "confidence": round(confidence, 3),
        "patientId": patient_id
    }
