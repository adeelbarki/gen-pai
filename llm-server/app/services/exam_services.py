import os
from datetime import datetime
from ..config import table

def load_examination_results_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, "data", "physical_exam_report.txt")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
    
def save_physical_exam_result_to_dynamodb(
        patient_id: str, 
        session_id: str, 
        extracted_vitals: str):
    item = {
        "patientId": patient_id,
        "SK": f"PExamResults#{session_id}",
        "recordType": "PhysicalExamResults",
        "timestamp": datetime.utcnow().isoformat(),
        "sessionId": session_id,
        "extracted_vitals": extracted_vitals
    }

    table.put_item(Item=item)
    
