# app/services/hp_summary_service.py
from fastapi import HTTPException
from boto3.dynamodb.conditions import Key
from ..config import table
from app.services.analyze_history_pexam_services import _to_documents, _chunk_documents, _redis_tag_escape
from app.prompts._summarize_history_pexam import _summarize
from ..vectorstore_config import vectorstore

def build_hp_summary_for_patient(patient_id: str) -> str:
    chat_resp = table.query(
        KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("ChatHistory#"),
        ScanIndexForward=False
    )
    pexam_resp = table.query(
        KeyConditionExpression=Key("patientId").eq(patient_id) & Key("SK").begins_with("PExamResults#"),
        ScanIndexForward=False
    )
    chat_items = chat_resp.get("Items", [])
    pexam_items = pexam_resp.get("Items", [])

    if not chat_items and not pexam_items:
        # Return a neutral string instead of raising; the caller can still summarize labs/X-rays.
        return "No H&P data found."

    docs = _to_documents(patient_id, chat_items, pexam_items)
    chunks = _chunk_documents(docs)

    ids = []
    for d in chunks:
        sk = d.metadata.get("sk", "nosk")
        section = d.metadata.get("section", "nosec")
        # deterministic ID so re-adding is idempotent
        ids.append(f"{patient_id}:{section}:{sk}:{abs(hash(d.page_content))}")

    # It's fine to call add_documents with stable IDs; most stores upsert.
    vectorstore.add_documents(documents=chunks, ids=ids)

    tag = _redis_tag_escape(patient_id)
    rs_filter = f"@symptom:{{{tag}}}"

    retrieved = vectorstore.similarity_search(
        "Summarize this patient's chat and physical exam.",
        k=6,
        filter=rs_filter
    )
    context_text = "\n\n---\n\n".join(d.page_content for d in retrieved) if retrieved else ""

    return _summarize(context_text) if context_text else "No relevant clinical information available."
