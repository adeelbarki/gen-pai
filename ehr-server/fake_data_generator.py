import uuid
from datetime import datetime, timedelta
from random import choice, randint
from models import PatientModel, Provider, Facility, Encounter
from sqlalchemy.ext.asyncio import AsyncSession

GENDERS = ["M", "F"]
REASONS = ["Check-up", "Follow-up", "Chest pain", "Fever", "Routine test"]
ENCOUNTER_TYPES = ["inpatient", "outpatient"]

async def generate_fake_data(db: AsyncSession, count: int = 10):
    patients = []
    providers = []
    facilities = []
    encounters = []

    # Create providers
    for i in range(3):
        provider = Provider(
            id=str(uuid.uuid4()),
            name=f"Dr. Provider {i+1}",
            specialty=choice(["General", "Cardiology", "Dermatology"]),
            contact=f"provider{i+1}@hospital.com"
        )
        db.add(provider)
        providers.append(provider)

    # Create facilities
    for i in range(2):
        facility = Facility(
            id=str(uuid.uuid4()),
            name=f"Facility {i+1}",
            location=f"{randint(100, 999)} Main St"
        )
        db.add(facility)
        facilities.append(facility)

    # Create patients and encounters
    for i in range(count):
        patient_id = str(uuid.uuid4())
        patient = PatientModel(
            id=patient_id,
            name=f"Patient {i+1}",
            dob=(datetime.now() - timedelta(days=randint(8000, 20000))).strftime("%Y-%m-%d"),
            gender=choice(GENDERS)
        )
        db.add(patient)
        patients.append(patient)

        encounter = Encounter(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            provider_id=choice(providers).id,
            facility_id=choice(facilities).id,
            encounter_date=datetime.now() - timedelta(days=randint(0, 30)),
            reason=choice(REASONS),
            type=choice(ENCOUNTER_TYPES),
            notes="Auto-generated encounter."
        )
        db.add(encounter)
        encounters.append(encounter)

    await db.commit()
    return {
        "patients": len(patients),
        "providers": len(providers),
        "facilities": len(facilities),
        "encounters": len(encounters)
    }
