from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table

router = APIRouter()

@router.get("/analyzing/lab-reports/{patient_id}")
def analyze_lab_reports(patient_id: str):
    try:
       return {
             patient_id: patient_id,
             "review_summary_lab_reports": "summary" 
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")