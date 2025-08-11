def format_qa_for_prompt(answers_by_section: dict[str, list[str]]) -> str:
    formatted = ""
    for section, answers in answers_by_section.items():
        answer_str = " ".join(answers).strip()
        formatted += f"{section}:\n{answer_str}\n\n"
    return formatted.strip()


def build_extraction_prompt(answers_by_section: dict[str, list[str]]) -> str:
    return f"""
You are a clinical assistant AI. Based on the following patient answers, extract structured clinical history.

Only return a JSON object with the following fields:
- chiefComplaint
- HPI (History of Present Illness)
- PMH (Past Medical History)
- Medications
- SH (Social History)
- FH (Family History)

Use natural language to summarize each section. Be concise and clinically accurate.

Patient answers:
{format_qa_for_prompt(answers_by_section)}
""".strip()
