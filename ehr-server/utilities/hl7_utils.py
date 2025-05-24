from hl7apy.core import Message
from datetime import datetime

def build_adt(patient):
    msg = Message("ADT_A01", version="2.5")

    msg.msh.msh_1 = "|"
    msg.msh.msh_2 = "^~\\&"
    msg.msh.msh_3 = "CentralEHR"
    msg.msh.msh_4 = "CentralFacility"
    msg.msh.msh_5 = "ReceivingSystem"
    msg.msh.msh_6 = "ReceivingFacility"
    msg.msh.msh_7 = datetime.now().strftime("%Y%m%d%H%M%S")
    msg.msh.msh_9 = "ADT^A01"
    msg.msh.msh_10 = "MSG12345"
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.5"

    # --- PID Segment ---
    msg.pid.pid_1 = "1"
    msg.pid.pid_3 = patient.id
    msg.pid.pid_5 = patient.name
    msg.pid.pid_7 = patient.dob.replace("-", "")
    msg.pid.pid_8 = patient.gender

    print("ADT HL7 Output:", msg.to_er7())
    return msg.to_er7()


def build_oru(patient, encounter, study_uid=None):
    msg = Message("ORU_R01", version="2.5")
    msg.msh.msh_3 = "CentralEHR"
    msg.msh.msh_7 = datetime.now().strftime("%Y%m%d%H%M%S")
    msg.msh.msh_9 = "ORU^R01"
    msg.msh.msh_10 = "MSG00002"
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.5"

    msg.pid.pid_3 = patient.id
    msg.pid.pid_5 = patient.name

    pv1 = msg.add_segment("PV1")
    pv1.pv1_2 = encounter.type.upper()
    pv1.pv1_44 = encounter.encounter_date.strftime("%Y%m%d%H%M")
    pv1.pv1_19 = encounter.reason
    pv1.pv1_36 = encounter.notes or ""

    obr = msg.add_segment("OBR")
    obr.obr_1 = "1"
    obr.obr_4 = "CBC^Complete Blood Count"

    obx1 = msg.add_segment("OBX")
    obx1.obx_1 = "1"
    obx1.obx_2 = "NM"
    obx1.obx_3 = "WBC^White Blood Cell Count"
    obx1.obx_5 = "5.4"
    obx1.obx_6 = "10^9/L"
    obx1.obx_7 = "4.0-11.0"
    obx1.obx_8 = "N"
    obx1.obx_11 = "F"
    obx1.obx_13 = "Within normal range"

    obx2 = msg.add_segment("OBX")
    obx2.obx_1 = "2"
    obx2.obx_2 = "NM"
    obx2.obx_3 = "HGB^Hemoglobin"
    obx2.obx_5 = "10.2"
    obx2.obx_6 = "g/dL"
    obx2.obx_7 = "12.0-15.5"
    obx2.obx_8 = "L"
    obx2.obx_11 = "F"
    obx2.obx_13 = "Low levels; consider iron deficiency"

    obx3 = msg.add_segment("OBX")
    obx3.obx_1 = "3"
    obx3.obx_2 = "NM"
    obx3.obx_3 = "BP^Blood Pressure"
    obx3.obx_5 = "118/76"
    obx3.obx_6 = "mmHg"
    obx3.obx_11 = "F"

    obx4 = msg.add_segment("OBX")
    obx4.obx_1 = "4"
    obx4.obx_2 = "NM"
    obx4.obx_3 = "HR^Heart Rate"
    obx4.obx_5 = "72"
    obx4.obx_6 = "bpm"
    obx4.obx_11 = "F"

    obx5 = msg.add_segment("OBX")
    obx5.obx_1 = "5"
    obx5.obx_2 = "NM"
    obx5.obx_3 = "TEMP^Temperature"
    obx5.obx_5 = "98.6"
    obx5.obx_6 = "F"
    obx5.obx_11 = "F"

    # --- IMAGING DATA ---
    if study_uid:
        obx6 = msg.add_segment("OBX")
        obx6.obx_1 = "6"
        obx6.obx_2 = "TX"
        obx6.obx_3 = "IMPRESSION^Chest X-ray Impression"
        obx6.obx_5 = "Clear lungs. No pleural effusion."
        obx6.obx_11 = "F"

        obx7 = msg.add_segment("OBX")
        obx7.obx_1 = "7"
        obx7.obx_2 = "TX"
        obx7.obx_3 = "STUDYUID^Study UID"
        obx7.obx_5 = study_uid
        obx7.obx_11 = "F"

        obx8 = msg.add_segment("OBX")
        obx8.obx_1 = "8"
        obx8.obx_2 = "TX"
        obx8.obx_3 = "IMAGEURL^DICOM Viewer"
        obx8.obx_5 = f"https://viewer.example.com/view?studyUID={study_uid}"
        obx8.obx_11 = "F"

    return msg.to_er7()

def build_orm(patient, encounter, provider_name="Dr. Smith", order_status="NW", order_id="ORD123"):
    msg = Message("ORM_O01", version="2.5")
    msg.msh.msh_3 = "CentralEHR"
    msg.msh.msh_7 = datetime.now().strftime("%Y%m%d%H%M%S")
    msg.msh.msh_9 = "ORM^O01"
    msg.msh.msh_10 = "MSG00003"
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.5"

    msg.pid.pid_3 = patient.id
    msg.pid.pid_5 = patient.name

    pv1 = msg.add_segment("PV1")
    pv1.pv1_2 = encounter.type.upper()
    pv1.pv1_44 = encounter.encounter_date.strftime("%Y%m%d%H%M")
    pv1.pv1_19 = encounter.reason
    pv1.pv1_36 = encounter.notes or ""

    orc = msg.add_segment("ORC")
    orc.orc_1 = order_status
    orc.orc_2 = order_id
    orc.orc_12 = provider_name

    obr = msg.add_segment("OBR")
    obr.obr_4 = "XRAYCHEST^Chest X-Ray"
    obr.obr_16 = provider_name  

    return msg.to_er7()