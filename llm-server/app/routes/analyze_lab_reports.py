from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table, s3, S3_BUCKET_PATIENT_RECORDS
from app.services.fetch_bloodtest_text import _fetch_bloodtest_text
from app.services._format_xray_items import _format_xray_items
from app.prompts._summarize_lab_results import _summarize_doctor_style
from app.services.hp_summary_service import build_hp_summary_for_patient


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

       hp_summary = build_hp_summary_for_patient(patient_id)

       summary = _summarize_doctor_style(patient_id, encounter_id, hp_summary, xray_text, lab_text)

       return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "lab_report_s3_key": f"s3://{S3_BUCKET_PATIENT_RECORDS}/{lab_key}",
            "hp_summary_included": bool(hp_summary and hp_summary.strip() and hp_summary != "No H&P data found."),
            "xray_items_count": len(xray_items),
            "review_summary_lab_reports": summary,
            "partials": {
                "hp_summary": hp_summary,
                "xray_text": xray_text,
                "lab_excerpt": lab_text[:500] + ("..." if lab_text and len(lab_text) > 500 else "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")