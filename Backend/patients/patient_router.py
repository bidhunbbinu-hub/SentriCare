
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from database.models import Patient, User
from auth.jwt_handler import get_current_user

router = APIRouter(prefix="/patients", tags=["Patients"])


class PatientSetupRequest(BaseModel):
    name: str
    age: int
    emergency_contact: str
    camera_id: str

@router.post("/setup")
def setup_patient(
    request: PatientSetupRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) 
):
    
    if current_user.role != "PRIMARY":
        raise HTTPException(status_code=403, detail="Only Primary Users can set up patients.")

    
    existing_camera = db.query(Patient).filter(Patient.camera_id == request.camera_id).first()
    if existing_camera:
        raise HTTPException(status_code=400, detail="This Camera ID is already registered.")

    
    new_patient = Patient(
        name=request.name,
        age=request.age,
        emergency_contact=request.emergency_contact,
        camera_id=request.camera_id,
        primary_user_id=current_user.id
    )
    
    db.add(new_patient)
    db.flush()
    current_user.patient_id = new_patient.id
    db.commit()
    db.refresh(new_patient)
    
    

    return {"status": "success","message": "Patient and Camera registered successfully", "patient_id": new_patient.id}