
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from database.db import get_db, SessionLocal
from database.models import User
from auth.jwt_handler import verify_password, create_access_token, get_password_hash, get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    role: str
class CaregiverRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
   
    user = db.query(User).filter(User.email == request.email).first()
    
    # 2. Verify password
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    
    token = create_access_token({"sub": user.email, "role": user.role, "name": user.name})
    
   
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=get_password_hash(request.password),
        role=request.role.upper()
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}


@router.post("/add-caregiver")
def add_caregiver(
    request: CaregiverRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    
    if current_user.role != "PRIMARY":
        raise HTTPException(status_code=403, detail="Only Primary Users can add caregivers.")
        
   
    if not current_user.patient_id:
        raise HTTPException(status_code=400, detail="Please set up a patient profile first.")

   
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    
    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=get_password_hash(request.password),
        role="MAIN",
        patient_id=current_user.patient_id 
    )
    
    db.add(new_user)
    db.commit()
    
    return {"message": "Caregiver account created and linked successfully."}

@router.get("/me")
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "patient_id": current_user.patient_id 
    }