import json, urllib.parse
from google.cloud import vision
from io import BytesIO
from ..config import sqs, s3, OCR_UPLOAD_QUEUE_URL

def poll_sqs_and_process():
    print("Polling SQS for messages...")

    messages = sqs.receive_message(
        QueueUrl=OCR_UPLOAD_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=3
    )

    if "Messages" not in messages:
        return {"message": "No messages in queue"}
    
    msg = messages["Messages"][0]
    receipt_handle = msg["ReceiptHandle"]
    body = json.loads(msg["Body"])

    if "Records" not in body:
        return {"message": "Not a valid S3 event"}
    
    record = body["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
    print(f"🧾 Processing file: {bucket}/{key}")

    image_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text

    print(f"📝 Extracted text:\n{text}")


    sqs.delete_message(
        QueueUrl=OCR_UPLOAD_QUEUE_URL,
        ReceiptHandle=receipt_handle
    )