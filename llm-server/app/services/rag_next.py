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
    section_filter: Optional[str] = None,
    k: int = 8,
) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    Retrieve the next best question for a session.
    - Constrains search by symptom (required) and optionally by section.
    - De-dupes by both doc id and question text per session.
    - Returns (question_text, metadata) or None if no unasked candidate found.
    """
    # Build filter: must match symptom; optionally match section
    flt = Tag("symptom") == symptom
    if section_filter:
        flt = flt & (Tag("section") == section_filter)

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": flt},
    )

    docs: List[Document] = await retriever.aget_relevant_documents(user_hint or symptom)
    if not docs:
        return None

    ids = asked_ids.setdefault(session_id, set())
    contents = asked_contents.setdefault(session_id, set())

    # Pick the first unasked candidate
    for d in docs:
        doc_id = (d.metadata.get("id") or d.metadata.get("_id") or "").strip()
        content = (d.page_content or "").strip()
        if not content:
            continue

        # Skip anything we've already asked (by id or text)
        if (doc_id and doc_id in ids) or (content in contents):
            continue

        # Mark as asked and return
        if doc_id:
            ids.add(doc_id)
        contents.add(content)

        meta = {
            "id": doc_id,
            "symptom": d.metadata.get("symptom", ""),
            "section": d.metadata.get("section", "HPI"),
        }
        return content, meta

    # All top-k were already asked
    return None

def mark_question_asked(session_id: str, question_text: str, doc_id: str | None = None) -> None:
    """Record a question as already asked so the retriever won't propose it again."""
    ids = asked_ids.setdefault(session_id, set())
    contents = asked_contents.setdefault(session_id, set())
    if doc_id:
        ids.add(doc_id)
    if question_text:
        contents.add(question_text.strip())
