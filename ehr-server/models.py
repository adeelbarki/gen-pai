from sqlalchemy import Column, String, DateTime, ForeignKey
from database import Base
from datetime import datetime

class PatientModel(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    dob = Column(String)
    gender = Column(String)

class Provider(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True)
    name = Column(String)
    specialty = Column(String)
    contact = Column(String)

class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String, primary_key=True)
    name = Column(String)
    location = Column(String)


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    provider_id = Column(String, ForeignKey("providers.id"))
    facility_id = Column(String, ForeignKey("facilities.id"))
    encounter_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(String)
    type = Column(String)
    notes = Column(String)



class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    study_uid = Column(String, unique=True)
    study_type = Column(String)
    findings = Column(String)
    technique = Column(String)
