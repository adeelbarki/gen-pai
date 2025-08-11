from fastapi import APIRouter
from PIL import Image
from io import BytesIO
from boto3.dynamodb.conditions import Key
import json, gzip
from ..config import (
    healthimaging,
    table,
    DATASTORE_ID,
    s3,
    BUCKET_NAME
)

router = APIRouter()

@router.get("/image-url/{patient_id}")
def get_presigned_image_url(patient_id: str):
    
    response = table.query(
        KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("XRay#")
    )
    
    if not response["Items"]:
        return {"error": "No XRay records found for this patient"}
    
    latest_record = sorted(response["Items"], key=lambda x: x["timestamp"], reverse=True)[0]
    
    image_set_id = latest_record["imageSetId"]

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