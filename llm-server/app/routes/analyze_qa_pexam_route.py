from fastapi import APIRouter, HTTPException
from app.services.hp_summary_service import build_hp_summary_for_patient

router = APIRouter()

@router.get("/analyzing/qa-pexam/{patient_id}")
def analyze_qa_pexam(patient_id: str):
    try:
        summary = build_hp_summary_for_patient(patient_id)
        return {
             patient_id: patient_id,
             "review_summary": summary 
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")