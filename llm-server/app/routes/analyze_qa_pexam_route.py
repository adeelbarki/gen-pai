from fastapi import APIRouter

router = APIRouter()

@router.get("/analyzing/qa-pexam/{patient_id}")
def analyze_qa_pexam(patient_id: str):
    print(patient_id)
    return {"message": "Analyzing"}