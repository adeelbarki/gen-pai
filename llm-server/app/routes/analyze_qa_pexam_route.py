from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table
from app.services.analyze_history_pexam_services import _to_documents, _chunk_documents, _redis_tag_escape
from app.prompts._summarize_history_pexam import _summarize
from ..vectorstore_config import vectorstore

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

        chat_items = chat_resp.get("Items", [])
        pexam_items = pexam_resp.get("Items", [])

        if not chat_items and not pexam_items:
                raise HTTPException(status_code=404, detail="No records found for this patient.")
        
        docs = _to_documents(patient_id, chat_items, pexam_items)
        chunks = _chunk_documents(docs)

        ids = []
        for d in chunks:
            sk = d.metadata.get("sk", "nosk")
            section = d.metadata.get("section", "nosec")
            ids.append(f"{patient_id}:{section}:{sk}:{abs(hash(d.page_content))}")

        vectorstore.add_documents(documents=chunks, ids=ids)

        tag = _redis_tag_escape(patient_id)
        rs_filter = f"@symptom:{{{tag}}}"

        retrieved = vectorstore.similarity_search(
            "Summarize this patient's chat and physical exam.",
            k=6,
            filter=rs_filter  # <-- critical: string filter, not dict
        )
        context_text = "\n\n---\n\n".join(d.page_content for d in retrieved) if retrieved else ""

        summary = _summarize(context_text) if context_text else "No relevant clinical information available."
        
        return {
             patient_id: patient_id,
             "review_summary": summary 
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")