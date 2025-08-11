from fastapi import APIRouter
from pydantic import BaseModel
from app.prompts.physical_examination import ask_gpt_to_extract_vitals
from app.services.exam_services import load_examination_results_data, save_physical_exam_result_to_dynamodb

router = APIRouter()

class Query(BaseModel):
    session_id: str
    patient_id: str


@router.post("/upload-physical-exam")
async def upload_physical_exam(query: Query):
    session_id = query.session_id
    patient_id = query.patient_id

    exam_results = load_examination_results_data()

    extracted_vitals = ask_gpt_to_extract_vitals(exam_results)

    save_physical_exam_result_to_dynamodb(
        patient_id=patient_id,
        session_id=session_id,
        extracted_vitals=extracted_vitals
    )
    
    return {"message": "physical examination completed"}
