from sqlalchemy import Column, Integer, String, Text, DateTime,ForeignKey
from datetime import datetime
from .db import Base

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)
    alert_type = Column(String)
    message = Column(Text)
    status = Column(String, default="PENDING")
    video_clip_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)  
    source = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)  
    patient_id = Column(Integer, nullable=True)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    emergency_contact = Column(String) 
    camera_id = Column(String, unique=True)
    primary_user_id = Column(Integer, ForeignKey("users.id"))