import hashlib
from typing import List, Dict
from langchain_core.documents import Document

def build_question_docs(symptom_questions: List[Dict]) -> tuple[list[Document], list[str]]:
    docs, ids = [], []
    for entry in symptom_questions:
        symptom = entry["symptom"]
        # entry["questions"] is a dict: { "chiefComplaint": [...], "HPI": [...], ... }
        for section, questions in entry["questions"].items():
            for q in questions:
                # stable ID so re-runs don’t duplicate
                doc_id = f"{symptom}::{section}::{hashlib.md5(q.encode('utf-8')).hexdigest()}"
                ids.append(doc_id)
                docs.append(
                    Document(
                        page_content=q,
                        metadata={"symptom": symptom, "section": section}
                    )
                )
    return docs, ids

def upsert_symptom_questions_to_vectorstore(vectorstore, symptom_questions: List[Dict]) -> None:
    docs, ids = build_question_docs(symptom_questions)
    if docs:
        vectorstore.add_documents(documents=docs, ids=ids)
