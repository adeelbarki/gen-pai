import json, re
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from ..config import OPENAI_API_KEY


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

def clean_json_block(text: str) -> str:
    # Extract JSON inside code block: ```json ... ```
    match = re.search(r"```json\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def ask_gpt_to_extract_vitals(text: str):
    prompt = f"""
      You are a medical assistant. Extract the following values from the given text:

      - Temperature
      - Blood Pressure
      - Heart Rate
      - Respiratory Rate
      - Oxygen Saturation

      Return ONLY a valid JSON object like:
      {{
        "temperature": "...",
        "bloodPressure": "...",
        "heartRate": "...",
        "respiratoryRate": "...",
        "oxygenSaturation": "..."
      }}

      Text:
      {text}
    """

    response = llm([HumanMessage(content=prompt)])
    content = response.content
    cleaned = clean_json_block(content)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("OpenAI did not return valid JSON:\n" + content)

    return result
    