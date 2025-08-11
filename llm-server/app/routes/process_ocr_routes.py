from fastapi import APIRouter
from app.services.ocr_services import poll_sqs_and_process

router = APIRouter()

@router.get("/trigger-ocr")
def trigger_ocr():
    poll_sqs_and_process()
    return {"message": "OCR processed"}