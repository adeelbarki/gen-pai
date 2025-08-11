# keep this in some module, e.g., services/rag_next.py

from typing import Optional, Set
from redisvl.query.filter import Tag
from vectorstore_config import vectorstore

# session_asked_ids[session_id] = set([...doc_ids...])
session_asked_ids: dict[str, Set[str]] = {}

async def get_next_question(
    session_id: str,
    symptom: str,
    user_hint: str = "follow-up question",
    k: int = 5,
) -> Optional[str]:
    flt = Tag("symptom") == symptom
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": flt},
    )

    docs = await retriever.aget_relevant_documents(user_hint)
    if not docs:
        return None

    asked = session_asked_ids.setdefault(session_id, set())
    # Find first doc we haven't asked yet
    for d in docs:
        doc_id = d.metadata.get("id") or d.metadata.get("_id")  # depends on your upsert; store an id in metadata
        if doc_id and doc_id in asked:
            continue
        # mark asked & return
        if doc_id:
            asked.add(doc_id)
        return d.page_content

    # If all top-k already asked, try the first anyway
    return docs[0].page_content
