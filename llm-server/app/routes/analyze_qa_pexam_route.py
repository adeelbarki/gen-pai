from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table

router = APIRouter()

@router.get("/analyzing/qa-pexam/{patient_id}")
def analyze_qa_pexam(patient_id: str):
    try:
        chat_resp = table.query(
            KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("ChatHistory#"),
            ScanIndexForward=False
        )
        chat_items = chat_resp.get("Items", [])

        pexam_resp = table.query(
                KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("PExamResults#"),
                ScanIndexForward=False
        )
        pexam_items = pexam_resp.get("Items", [])

        if not chat_items and not pexam_items:
                raise HTTPException(status_code=404, detail="No records found for this patient.")
        
        return {
             patient_id: patient_id,
             "review_summary": "review summary" 
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")