from datetime import datetime
from ..config import (
    table,
)

def save_chat_history_to_dynamodb(
        patient_id: str, 
        session_id: str, 
        extracted: str):
    item = {
        "patientId": patient_id,
        "SK": f"ChatHistory#{session_id}",
        "recordType": "ChatHistory",
        "timestamp": datetime.utcnow().isoformat(),
        "sessionId": session_id,
        "extracted": extracted
    }

    table.put_item(Item=item)