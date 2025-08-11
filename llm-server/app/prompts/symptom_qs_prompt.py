import json
import re
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

SECTION_ORDER = ["chiefComplaint", "HPI", "PMH", "Medications", "SH", "FH"]

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join([str(x).strip() for x in value if str(x).strip()]).strip()
    return str(value).strip()

def format_qa_for_prompt(answers_by_section: dict[str, list[str]]) -> str:
    """
    answers_by_section like:
      {"chiefComplaint": ["..."], "HPI": ["...","..."], ...}
    Accepts lists or strings and formats in a stable section order.
    """
    parts: List[str] = []
    keys = [k for k in SECTION_ORDER if k in answers_by_section] + \
           [k for k in answers_by_section.keys() if k not in SECTION_ORDER]

    for section in keys:
        joined = _coerce_text(answers_by_section.get(section, ""))
        parts.append(f"{section}:\n{joined or '(no response)'}")
    return "\n\n".join(parts)

def _extract_json_block(text: str) -> str:
    """
    Best-effort: if model wraps JSON in code fences or adds prose,
    pull the first {...} block.
    """
    # Try plain first
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    # Try code-fence or mixed output
    m = re.search(r"\{(?:[^{}]|(?R))*\}", s, re.DOTALL)  # recursive-like JSON block
    return m.group(0) if m else s

async def run_langchain_extraction(answers_by_section: dict[str, list[str]]) -> dict[str, str]:
    """
    Summarize answers into structured clinical history.
    """
    body = format_qa_for_prompt(answers_by_section)
    prompt = f"""
You are a clinical assistant AI. Based on the following patient answers, extract a structured clinical history.

Only return a valid JSON object with exactly these fields:
- chiefComplaint
- HPI
- PMH
- Medications
- SH
- FH

Be concise and clinically accurate.

Patient answers:
{body}
""".strip()

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    raw = (resp.content or "").strip()

    # Try strict JSON parsing (with code-fence/mixed-output tolerance)
    try:
        payload = json.loads(_extract_json_block(raw))
        return {
            "chiefComplaint": _coerce_text(payload.get("chiefComplaint", "")),
            "HPI":            _coerce_text(payload.get("HPI", "")),
            "PMH":            _coerce_text(payload.get("PMH", "")),
            "Medications":    _coerce_text(payload.get("Medications", "")),
            "SH":             _coerce_text(payload.get("SH", "")),
            "FH":             _coerce_text(payload.get("FH", "")),
        }
    except Exception:
        # Fallback: pass through concatenated answers
        return {
            "chiefComplaint": _coerce_text(answers_by_section.get("chiefComplaint", "")),
            "HPI":            _coerce_text(answers_by_section.get("HPI", "")),
            "PMH":            _coerce_text(answers_by_section.get("PMH", "")),
            "Medications":    _coerce_text(answers_by_section.get("Medications", "")),
            "SH":             _coerce_text(answers_by_section.get("SH", "")),
            "FH":             _coerce_text(answers_by_section.get("FH", "")),
        }



