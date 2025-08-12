# keep this in some module, e.g., services/rag_next.py

from typing import Optional, Set, Tuple, Dict, List
from langchain_core.documents import Document
from redisvl.query.filter import Tag
from ..vectorstore_config import vectorstore

asked_ids: dict[str, Set[str]] = {}
asked_contents: Dict[str, Set[str]] = {}

async def get_next_question(
    session_id: str,
    symptom: str,
    user_hint: str = "follow-up question",
    k: int = 8,
) -> Optional[Tuple[str, Dict[str, str]]]:
    flt = Tag("symptom") == symptom
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": flt},
    )

    docs: List[Document] = await retriever.aget_relevant_documents(user_hint or symptom)
    if not docs:
        return None

    ids = asked_ids.setdefault(session_id, set())
    contents = asked_contents.setdefault(session_id, set())
    
    for d in docs:
        doc_id = (d.metadata.get("id") or d.metadata.get("_id") or "").strip()
        content = (d.page_content or "").strip()

        if (doc_id and doc_id in ids) or (content and content in contents):
            continue

        if doc_id:
            ids.add(doc_id)
        if content:
            contents.add(content)

        meta = {
            "id": doc_id,
            "symptom": d.metadata.get("symptom", ""),
            "section": d.metadata.get("section", "HPI"),
        }
        return content, meta
    
    return None
