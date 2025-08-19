from fastapi import HTTPException
from botocore.exceptions import ClientError
from pdfminer.high_level import extract_text as pdf_extract_text
from io import BytesIO
from ..config import table, s3, S3_BUCKET_PATIENT_RECORDS

def _fetch_bloodtest_text(patient_id: str, encounter_id: str) -> tuple[str, str]:
    key = f"{patient_id}/encounters/{encounter_id}/blood-tests/blood_test_report.pdf"
    try:
        obj = s3.get_object(Bucket=S3_BUCKET_PATIENT_RECORDS, Key=key)
        pdf_bytes = obj["Body"].read()
        text = pdf_extract_text(BytesIO(pdf_bytes)) or ""
        return key, text
    except ClientError as e:
        # Let it be empty text but surface the S3 path in response
        if e.response["Error"]["Code"] in {"NoSuchKey", "404"}:
            return key, ""
        raise HTTPException(status_code=500, detail=f"S3 error: {e.response['Error'].get('Message')}")