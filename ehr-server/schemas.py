from pydantic import BaseModel, Field
from datetime import datetime

class PatientIn(BaseModel):
    name: str = Field(..., example="John Doe")
    dob: str = Field(..., example="1990-01-01")
    gender: str = Field(..., example="M")

class EncounterIn(BaseModel):
    patient_id: str
    provider_id: str
    facility_id: str
    encounter_date: datetime
    reason: str
    type: str
    notes: str = None

    class Config:
        schema_extra = {
            "example": {
                "patient_id": "123",
                "provider_id": "prov-001",
                "facility_id": "fac-001",
                "encounter_date": "2025-04-05T10:00:00",
                "reason": "Annual physical",
                "type": "outpatient",
                "notes": "All good"
            }
        }