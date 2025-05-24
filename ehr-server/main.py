from fastapi import FastAPI, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import PatientModel, Encounter
from schemas import PatientIn, EncounterIn
from database import Base, engine, SessionLocal
from utilities.hl7_utils import build_adt, build_oru, build_orm
import uuid


app = FastAPI()


async def get_db():
    async with SessionLocal() as session:
        yield session

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def read_root():
    status = {"status": "ok"}
    return status

@app.post("/patients/")
async def add_patient(patient: PatientIn, db: AsyncSession = Depends(get_db)):
    new_patient = PatientModel(
        id=str(uuid.uuid4()),
        name=patient.name,
        dob=patient.dob,
        gender=patient.gender
    )
    db.add(new_patient)
    await db.commit()
    return {
        "message": "Patient added successfully",
        "patient": {
            "id": new_patient.id,
            "name": new_patient.name,
            "dob": new_patient.dob,
            "gender": new_patient.gender
        }
    }

@app.post("/encounters/", tags=["Encounters"])
async def create_encounter(encounter: EncounterIn, db: AsyncSession = Depends(get_db)):
    new_encounter = Encounter(
        id=str(uuid.uuid4()),
        patient_id=encounter.patient_id,
        provider_id=encounter.provider_id,
        facility_id=encounter.facility_id,
        encounter_date=encounter.encounter_date,
        reason=encounter.reason,
        type=encounter.type,
        notes=encounter.notes,
    )
    db.add(new_encounter)
    await db.commit()
    return {
        "message": "Encounter added successfully",
        "encounter_id": new_encounter.id
    }


@app.get("/patients/{patient_id}/hl7/{msg_type}", tags=["HL7"])
async def get_patient_hl7(patient_id: str, msg_type: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PatientModel).where(PatientModel.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    msg_type = msg_type.upper()
    
    if msg_type in ["ORU", "ORM"]:
        encounter_result = await db.execute(
            select(Encounter).where(Encounter.patient_id == patient_id)
        )
        encounter = encounter_result.scalar_one_or_none()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        if msg_type == "ORU":
            hl7 = build_oru(patient, encounter)
        else:  # ORM
            hl7 = build_orm(patient, encounter)

    elif msg_type == "ADT":
        hl7 = build_adt(patient)  # optional: pass encounter here too if you want
        print("ADT HL7:\n", hl7)  # ✅ log the message
        return {"hl7": hl7}

    else:
        raise HTTPException(status_code=400, detail="Unsupported message type")
    
@app.post("/generate-fake-data/", summary="Generate test data", tags=["Utilities"])
async def generate_data(
    count: int = Body(default=10, description="Number of patients to generate"),
    db: AsyncSession = Depends(get_db)):
    from fake_data_generator import generate_fake_data
    summary = await generate_fake_data(db, count)
    return {"message": "Fake data generated", **summary}

@app.get("/patients/", tags=["Patients"])
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PatientModel))
    patients = result.scalars().all()
    return [{"id": p.id, "name": p.name} for p in patients]
