from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table, s3, S3_BUCKET_PATIENT_RECORDS
from app.services.fetch_bloodtest_text import _fetch_bloodtest_text
from app.services._format_xray_items import _format_xray_items
from app.prompts._summarize_lab_results import _summarize_doctor_style


router = APIRouter()

@router.get("/analyzing/lab-reports/{patient_id}")
def analyze_lab_reports(patient_id: str):
    encounter_id: str = "encounter-20250819-7f3a4c92"
    try:
       # Fetching xray results from dynamodb - json
       xray_result_resp = table.query(
           KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("XRay#"),
           ScanIndexForward=False
       )
       xray_items = xray_result_resp.get("Items", [])
       
       # Fetching blood test report from s3 - pdf
       lab_key, lab_text = _fetch_bloodtest_text(patient_id, encounter_id)

       xray_text = _format_xray_items(xray_items)

       summary = _summarize_doctor_style(patient_id, encounter_id, xray_text, lab_text)

       return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "lab_report_s3_key": f"s3://{S3_BUCKET_PATIENT_RECORDS}/{lab_key}",
            "xray_items_count": len(xray_items),
            "review_summary_lab_reports": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")