from typing import List, Dict, Any
import json

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def _fmt_chat_item(it: Dict[str, Any]) -> str:
    role = it.get("role") or it.get("type") or "unknown"
    content = it.get("message") or it.get("content") or ""
    ts = it.get("createdAt") or it.get("timestamp") or it.get("SK")
    return f"[Chat | {ts} | {role}]\n{content}".strip()

def _fmt_pexam_item(it: Dict[str, Any]) -> str:
    ts = it.get("createdAt") or it.get("timestamp") or it.get("SK")
    fields = []
    for k in ["vitals", "general", "respiratory", "cardio", "neuro", "abdomen", "msk", "skin", "assessment", "impression"]:
        if k in it and it[k] not in (None, ""):
            v = it[k]
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            fields.append(f"{k.capitalize()}: {v}")
    if not fields:
        clone = {k: v for k, v in it.items() if k not in ["embedding", "blob"]}
        fields.append(json.dumps(clone, ensure_ascii=False))
    return f"[Physical Exam | {ts}]\n" + "\n".join(fields)

def _to_documents(patient_id: str, chat_items: List[Dict[str, Any]], pexam_items: List[Dict[str, Any]]) -> List[Document]:
    docs: List[Document] = []
    for it in chat_items:
        docs.append(
            Document(
                page_content=_fmt_chat_item(it),
                metadata={
                    # Workaround: store patientId under 'symptom' to make it filterable with your current schema
                    "symptom": patient_id,
                    "section": "chat",
                    "sk": it.get("SK")
                }
            )
        )
    for it in pexam_items:
        docs.append(
            Document(
                page_content=_fmt_pexam_item(it),
                metadata={
                    "symptom": patient_id,  # see note above
                    "section": "pexam",
                    "sk": it.get("SK")
                }
            )
        )
    return docs

def _redis_tag_escape(val: str) -> str:
    """
    Escape a value for use inside a RediSearch TAG query: @field:{value}
    We escape spaces/braces/pipes/commas/colons/hyphens conservatively.
    """
    v = str(val)
    for ch in ["\\", " ", "{", "}", "|", ",", ":", "-"]:
        v = v.replace(ch, f"\\{ch}")
    return v

def _chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(docs)