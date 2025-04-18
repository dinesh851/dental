from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, time, datetime, timedelta
from typing import List, Optional
import re
from enum import Enum

# Database connection
DATABASE_URL = "postgresql://postgres:dinesh@localhost/dental_clinic"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Define database models
class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    address = Column(String(255), nullable=True)
    medical_history = Column(Text, nullable=True)
    insurance_info = Column(String(255), nullable=True)
    
    appointments = relationship("Appointment", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    
    appointments = relationship("Appointment", back_populates="doctor")

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    REGULAR_CHECKUP = "regular_checkup"
    CLEANING = "cleaning"
    FILLING = "filling"
    ROOT_CANAL = "root_canal"
    EXTRACTION = "extraction"
    ORTHODONTIC = "orthodontic"
    COSMETIC = "cosmetic"
    EMERGENCY = "emergency"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    appointment_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat(), 
                        onupdate=lambda: datetime.now().isoformat())
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

# Create tables in the database
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(title="Dental Clinic Appointment System", 
              description="API for managing dental appointment bookings",
              version="1.0.0")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models for API
class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone_number: str = Field(..., example="555-123-4567")
    age: int = Field(..., gt=0, lt=120, example=35)
    address: Optional[str] = Field(None, example="123 Main St, City, State 12345")
    medical_history: Optional[str] = Field(None, example="No allergies, diabetes type 2")
    insurance_info: Optional[str] = Field(None, example="Blue Cross Blue Shield #12345678")

    @validator('phone_number')
    def validate_phone_number(cls, v):
        pattern = r'^\+?[0-9\-\(\) ]{10,20}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    
    class Config:
        orm_mode = True

class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str
    phone_number: str
    email: EmailStr

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int
    
    class Config:
        orm_mode = True

class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: time
    appointment_type: AppointmentType
    reason: Optional[str] = None
    notes: Optional[str] = None

    @validator('appointment_date')
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    doctor_id: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    status: AppointmentStatus
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class AppointmentWithDetails(AppointmentResponse):
    patient: PatientResponse
    doctor: DoctorResponse
    
    class Config:
        orm_mode = True

class Message(BaseModel):
    message: str

# API Endpoints for Patients
@app.post("/patients/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    # Check if patient with email already exists
    existing_patient = db.query(Patient).filter(Patient.email == patient.email).first()
    if existing_patient:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients/", response_model=List[PatientResponse])
def get_patients(
    skip: int = 0, 
    limit: int = 100, 
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Patient)
    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))
    return query.offset(skip).limit(limit).all()

@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.put("/patients/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, patient: PatientBase, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update patient details
    for key, value in patient.dict().items():
        setattr(db_patient, key, value)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.delete("/patients/{patient_id}", response_model=Message)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if patient has appointments before deletion
    appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).all()
    if appointments:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete patient with existing appointments. Cancel appointments first."
        )
    
    db.delete(db_patient)
    db.commit()
    return {"message": "Patient deleted successfully"}

# API Endpoints for Doctors
@app.post("/doctors/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    db_doctor = Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

@app.get("/doctors/", response_model=List[DoctorResponse])
def get_doctors(
    skip: int = 0, 
    limit: int = 100, 
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    return query.offset(skip).limit(limit).all()

# API Endpoints for Appointments
@app.post("/appointments/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Check if the appointment time is available
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.appointment_time == appointment.appointment_time,
        Appointment.status.in_(["scheduled", "confirmed"])
    ).first()
    
    if existing_appointment:
        raise HTTPException(status_code=400, detail="This time slot is already booked")
    
    # Business hours check (assuming clinic is open 9 AM to 5 PM)
    appointment_datetime = datetime.combine(appointment.appointment_date, appointment.appointment_time)
    if appointment_datetime.time() < time(9, 0) or appointment_datetime.time() > time(17, 0):
        raise HTTPException(status_code=400, detail="Appointments must be during business hours (9 AM to 5 PM)")
    
    # Weekend check (assuming clinic is closed on weekends)
    if appointment_datetime.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        raise HTTPException(status_code=400, detail="Appointments cannot be scheduled on weekends")
    
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.get("/appointments/", response_model=List[AppointmentWithDetails])
def get_appointments(
    skip: int = 0, 
    limit: int = 100, 
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    
    if date_from:
        query = query.filter(Appointment.appointment_date >= date_from)
    if date_to:
        query = query.filter(Appointment.appointment_date <= date_to)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.offset(skip).limit(limit).all()

@app.get("/appointments/{appointment_id}", response_model=AppointmentWithDetails)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@app.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(appointment_id: int, appointment: AppointmentUpdate, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update only the fields that are provided
    update_data = appointment.dict(exclude_unset=True)
    
    # If we're updating date or time, check for conflicts
    if "appointment_date" in update_data or "appointment_time" in update_data:
        new_date = update_data.get("appointment_date", db_appointment.appointment_date)
        new_time = update_data.get("appointment_time", db_appointment.appointment_time)
        doctor_id = update_data.get("doctor_id", db_appointment.doctor_id)
        
        # Check for time conflicts
        existing_appointment = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == new_date,
            Appointment.appointment_time == new_time,
            Appointment.id != appointment_id,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).first()
        
        if existing_appointment:
            raise HTTPException(status_code=400, detail="This time slot is already booked")
    
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    
    # Update the updated_at timestamp
    db_appointment.updated_at = datetime.now().isoformat()
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if db_appointment.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")
    
    db_appointment.status = "cancelled"
    db_appointment.updated_at = datetime.now().isoformat()
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.get("/available-slots/", response_model=List[dict])
def get_available_slots(
    doctor_id: int = Query(..., description="Doctor ID to check availability for"),
    date: date = Query(..., description="Date to check availability for"),
    db: Session = Depends(get_db)
):
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Get all booked appointments for this doctor on the given date
    booked_slots = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == date,
        Appointment.status.in_(["scheduled", "confirmed"])
    ).all()
    
    # Create a set of booked times
    booked_times = {appointment.appointment_time for appointment in booked_slots}
    
    # Generate all possible time slots (assuming 30-minute appointments from 9 AM to 5 PM)
    all_slots = []
    current_time = datetime.combine(date, time(9, 0))
    end_time = datetime.combine(date, time(17, 0))
    
    while current_time < end_time:
        slot_time = current_time.time()
        if slot_time not in booked_times:
            all_slots.append({
                "time": slot_time.strftime("%H:%M"),
                "doctor_id": doctor_id,
                "doctor_name": doctor.name,
                "available": True
            })
        
        current_time += timedelta(minutes=30)
    
    return all_slots

# Root endpoint
@app.get("/", response_model=Message)
def root():
    return {"message": "Welcome to the Dental Clinic Appointment Booking API"}