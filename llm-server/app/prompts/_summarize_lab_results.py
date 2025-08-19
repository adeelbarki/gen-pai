from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

def _summarize_doctor_style(patient_id: str, encounter_id: str, hp_summary: str, xray_text: str, lab_text: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    system = SystemMessage(content=(
        "You are a careful clinician. Synthesize X-ray AI findings and a lab-report into a concise, "
        "clinically useful summary. Include: (1) salient positives/negatives with numbers if present, "
        "(2) differential considerations as appropriate, (3) recommended next steps in neutral, "
        "non-prescriptive language, and (4) short bracketed citations like [XRay] or [Lab]. Avoid guessing."
    ))

    context = (
        f"Patient: {patient_id}\nEncounter: {encounter_id}\n\n"
        f"== H&P Summary == [H&P]\n{hp_summary}\n\n"
        f"== XRay ==\n{xray_text}\n\n"
        f"== Lab Report (PDF Text) ==\n{lab_text if lab_text.strip() else 'No lab text extracted.'}\n"
    )

    user = HumanMessage(content=(
        "Provide an integrated doctor-style summary of the encounter using the context above. "
        "If certain data points are missing, state 'not stated'."
        "\n\nContext:\n" + context
    ))

    resp = llm.invoke([system, user])
    return resp.content
