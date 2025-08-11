# rag_setup.py
import hashlib
from typing import List, Dict, Tuple
from langchain_core.documents import Document

def build_question_docs(symptom_questions: List[Dict]) -> Tuple[List[Document], List[str]]:
    """
    Expects:
    [
      {
        "symptom": "cough",
        "questions": {
          "chiefComplaint": [...],
          "HPI": [...],
          "PMH": [...],
          "Medications": [...],
          "SH": [...],
          "FH": [...]
        }
      },
      ...
    ]
    """
    docs: List[Document] = []
    ids: List[str] = []

    for entry in symptom_questions:
        symptom = entry["symptom"]
        for section, questions in entry["questions"].items():
            for q in questions:
                q_hash = hashlib.md5(q.encode("utf-8")).hexdigest()
                doc_id = f"{symptom}::{section}::{q_hash}"

                ids.append(doc_id)
                docs.append(
                    Document(
                        page_content=q,
                        metadata={
                            "symptom": symptom,
                            "section": section,
                            "id": doc_id,  # put the stable id in metadata for de-dupe/tracking
                        },
                    )
                )
    return docs, ids


def upsert_symptom_questions_to_vectorstore(vectorstore, symptom_questions: List[Dict]) -> None:
    docs, ids = build_question_docs(symptom_questions)
    if not docs:
        return
    # idempotent upsert (same ids => no duplicates)
    vectorstore.add_documents(documents=docs, ids=ids)
