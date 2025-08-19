# ------------- Doctor persona -------------
DOCTOR_SYSTEM = """You are a compassionate primary-care clinician.
- Ask exactly ONE concise question at a time.
- Use layperson-friendly language; avoid jargon unless essential.
- Never infer or restate facts about the patient.
- Acknowledge only sometimes; if you do, keep it short and neutral (e.g., “Thanks for sharing.”).
- Do not use phrases like “I'm hearing”.
- If an emergency is suspected, advise urgent care and stop routine questions."""

# ------------- Red‑flag triage rails -------------
RED_FLAGS = {
    "respiratory": [
        "severe shortness of breath", "trouble breathing", "breathless at rest",
        "blue lips", "cyanosis", "cannot speak full sentences",
        "coughing up blood", "hemoptysis", "oxygen below 90", "confusion"
    ],
    "cardiac": [
        "crushing chest pain", "chest pain with sweating", "chest pain with nausea",
        "fainting", "passed out"
    ],
    "neuro": [
        "new weakness on one side", "slurred speech", "seizure", "severe headache"
    ],
    "general": [
        "severe dehydration", "unable to keep fluids down"
    ],
}

EMERGENCY_MESSAGE = (
    "Your description could suggest an urgent issue. "
    "Please seek immediate in‑person medical care or call local emergency services. "
    "I won’t continue routine questions right now."
)