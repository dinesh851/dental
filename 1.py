from fastapi import FastAPI, HTTPException, Depends, Query, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey, Boolean, Text, text, UniqueConstraint 
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, time, datetime, timedelta
from typing import List, Optional, Union, Dict, Any,Optional
import uuid
from sqlalchemy.dialects.postgresql import UUID
from jose import JWTError, jwt
from datetime import date as date_type
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from passlib.context import CryptContext
import re
from enum import Enum

# Security configuration
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # In production, use a secure key and store it safely
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection
DATABASE_URL = "postgresql://postgres:dinesh@localhost/dental_clinic"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # For doctors who are also users
    doctor = relationship("Doctor", back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)# Changed from UUID to Integer
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True, unique=True)
    phone_number = Column(String(20), nullable=False,index=True, unique=True)  # Ensure uniqueness
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    availability = relationship("DoctorAvailability", back_populates="doctor")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Morning slots (10 AM - 2 PM)
    slot1 = Column(Boolean, default=False)    # 10:00-10:30
    slot2 = Column(Boolean, default=False)    # 10:30-11:00
    slot3 = Column(Boolean, default=False)    # 11:00-11:30
    slot4 = Column(Boolean, default=False)    # 11:30-12:00
    slot5 = Column(Boolean, default=False)    # 12:00-12:30
    slot6 = Column(Boolean, default=False)    # 12:30-13:00
    slot7 = Column(Boolean, default=False)    # 13:00-13:30
    slot8 = Column(Boolean, default=False)    # 13:30-14:00
    
    # Evening slots (5 PM - 9 PM)
    slot9 = Column(Boolean, default=False)    # 17:00-17:30
    slot10 = Column(Boolean, default=False)   # 17:30-18:00
    slot11 = Column(Boolean, default=False)   # 18:00-18:30
    slot12 = Column(Boolean, default=False)   # 18:30-19:00
    slot13 = Column(Boolean, default=False)   # 19:00-19:30
    slot14 = Column(Boolean, default=False)   # 19:30-20:00
    slot15 = Column(Boolean, default=False)   # 20:00-20:30
    slot16 = Column(Boolean, default=False)   # 20:30-21:00
    
    doctor = relationship("Doctor", back_populates="availability")
    
    __table_args__ = (
        # Each doctor can have only one record per date
        UniqueConstraint('doctor_id', 'date', name='unique_doctor_date'),
    )

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

# Update the Appointment model to include slot_number
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    slot_number = Column(Integer, nullable=False)  # Changed from appointment_time to slot_number
    appointment_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat(), 
                        onupdate=lambda: datetime.now().isoformat())
    duration_minutes = Column(Integer, default=30)  # Default appointment duration
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
# Holiday/clinic closure dates
class ClinicClosure(Base):
    __tablename__ = "clinic_closures"
    
    id = Column(Integer, primary_key=True, index=True)
    closure_date = Column(Date, nullable=False, unique=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

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

# Authentication helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_slot_time(slot_number):
    """Convert slot number (1-16) to actual start and end times."""
    if 1 <= slot_number <= 8:  # Morning slots (10 AM - 2 PM)
        hour = 10 + (slot_number - 1) // 2
        minute = 0 if (slot_number - 1) % 2 == 0 else 30
        start_time = f"{hour:02d}:{minute:02d}"
        
        end_hour = hour
        end_minute = minute + 30
        if end_minute == 60:
            end_hour += 1
            end_minute = 0
        end_time = f"{end_hour:02d}:{end_minute:02d}"
    else:  # Evening slots (5 PM - 9 PM)
        adjusted_slot = slot_number - 8
        hour = 17 + (adjusted_slot - 1) // 2
        minute = 0 if (adjusted_slot - 1) % 2 == 0 else 30
        start_time = f"{hour:02d}:{minute:02d}"
        
        end_hour = hour
        end_minute = minute + 30
        if end_minute == 60:
            end_hour += 1
            end_minute = 0
        end_time = f"{end_hour:02d}:{end_minute:02d}"
    
    return start_time, end_time

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_doctor_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a doctor"
        )
    return {
        "user": current_user,
        "doctor": doctor
    }

# Pydantic Models for API
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True

class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone_number: str = Field(..., example="555-123-4567")  # Required field
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
    id: int  # Changed from str to int
    
    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str
    phone_number: str
    email: EmailStr

class DoctorCreate(DoctorBase):
    user_id: Optional[int] = None

class DoctorResponse(DoctorBase):
    id: int
    
    class Config:
        from_attributes = True
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    slot_number: int = Field(..., ge=1, le=16)  # Slot number between 1-16
    appointment_type: AppointmentType
    reason: Optional[str] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = 30

    @validator('appointment_date')
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    slot_number: Optional[int] = Field(None, ge=1, le=16)  # Slot number between 1-16
    doctor_id: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    slot_number: int
    appointment_type: AppointmentType
    reason: Optional[str] = None
    notes: Optional[str] = None
    duration_minutes: int
    status: AppointmentStatus
    created_at: str
    updated_at: str
    slot_time: Optional[str] = None  # Make this optional or ensure it's computed

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Add this if needed

    @validator('slot_time', always=True)
    def set_slot_time(cls, v, values):
        if 'slot_number' in values:
            start_time, _ = get_slot_time(values['slot_number'])
            return start_time
        return None
class AppointmentWithDetails(AppointmentResponse):
    patient: PatientResponse
    doctor: DoctorResponse
    
    class Config:
        from_attributes = True

class SlotUpdate(BaseModel):
    slot_number: int
    is_available: bool

# For updating a specific date's availability
class DateAvailabilityUpdate(BaseModel):
    date: date
    slots: List[SlotUpdate]
class DoctorAvailabilityCreate(BaseModel):
    doctor_id: int
    date: date
    slot1: bool = False
    slot2: bool = False
    slot3: bool = False
    slot4: bool = False
    slot5: bool = False
    slot6: bool = False
    slot7: bool = False
    slot8: bool = False
    slot9: bool = False
    slot10: bool = False
    slot11: bool = False
    slot12: bool = False
    slot13: bool = False
    slot14: bool = False
    slot15: bool = False
    slot16: bool = False
# For bulk updates across multiple dates
class AvailabilitySlot(BaseModel):
    date: date_type
    slot_values: Dict[str, bool]  # Maps slot names to availability

class DoctorAvailabilityBulkUpdate(BaseModel):
    doctor_id: int
    availability: List[AvailabilitySlot]
# Alternative format for complete slot definition
class CompleteDayAvailability(BaseModel):
    date: date
    slot_values: Dict[str, bool]  # Key: slot_number as string, Value: is_available

class CompleteBulkUpdate(BaseModel):
    doctor_id: int
    availability: List[CompleteDayAvailability]

# Response models
class DoctorAvailabilityResponse(BaseModel):
    id: int
    doctor_id: int
    date: date
    slot1: bool
    slot2: bool
    slot3: bool
    slot4: bool
    slot5: bool
    slot6: bool
    slot7: bool
    slot8: bool
    slot9: bool
    slot10: bool
    slot11: bool
    slot12: bool
    slot13: bool
    slot14: bool
    slot15: bool
    slot16: bool

    class Config:
        from_attributes = True

class DayAvailabilityResponse(BaseModel):
    date: date
    slots: List[DoctorAvailabilityResponse]

class AvailableSlot(BaseModel):
    time: str
    doctor_id: int
    doctor_name: str
    available: bool

class ClinicClosureBase(BaseModel):
    closure_date: date
    reason: Optional[str] = None

class ClinicClosureCreate(ClinicClosureBase):
    pass

class ClinicClosureResponse(ClinicClosureBase):
    id: int
    created_at: str
    
    class Config:
        from_attributes = True

class Message(BaseModel):
    message: str

# Authentication Endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/admin/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    user: UserCreate, 
    is_admin: bool = Query(False, description="Set to true to create an admin user"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Check if username exists
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user with admin privileges
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# API Endpoints for Patients
@app.post("/patients/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient: PatientCreate, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    # Check if patient with email already exists
    existing_patient = db.query(Patient).filter(
        (Patient.email == patient.email) | (Patient.phone_number == patient.phone_number)
    ).first()
    if existing_patient:
        raise HTTPException(status_code=400, detail="Email or phone number already registered")
    
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Patient)
    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))
    return query.offset(skip).limit(limit).all()

@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,  # Changed from str to int
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient

@app.put("/patients/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,  # Changed from str to int
    patient: PatientBase, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
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
def delete_patient(
    patient_id: int,  # Changed from str to int
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
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
def create_doctor(
    doctor: DoctorCreate, 
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # If user_id is provided, check if it exists and is not already associated with a doctor
    if doctor.user_id:
        user = db.query(User).filter(User.id == doctor.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        existing_doctor = db.query(Doctor).filter(Doctor.user_id == doctor.user_id).first()
        if existing_doctor:
            raise HTTPException(status_code=400, detail="User is already associated with a doctor")
    
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    return query.offset(skip).limit(limit).all()

# Doctor Availability Management
@app.post("/doctor-availability/bulk/", response_model=Dict[str, str])
def update_doctor_availability_bulk(
    bulk_data: DoctorAvailabilityBulkUpdate,
    current_user: User = Depends(get_admin_user),  # Only admin can use this
    db: Session = Depends(get_db)
):
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == bulk_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Process each date in the bulk update
    for avail_slot in bulk_data.availability:
        # Check if this date already exists for this doctor
        existing = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == bulk_data.doctor_id,
            DoctorAvailability.date == avail_slot.date
        ).first()
        
        if existing:
            # Update existing record
            for slot_name, value in avail_slot.slot_values.items():
                if hasattr(existing, slot_name):
                    setattr(existing, slot_name, value)
        else:
            # Create new record
            new_data = {
                "doctor_id": bulk_data.doctor_id,
                "date": avail_slot.date
            }
            # Add slot values to new_data
            for slot_name, value in avail_slot.slot_values.items():
                new_data[slot_name] = value
                
            new_record = DoctorAvailability(**new_data)
            db.add(new_record)
    
    db.commit()
    return {"message": f"Updated availability for Dr. {doctor.name}"}

@app.delete("/doctor-availability/{availability_id}", response_model=Message)
def delete_doctor_availability(
    availability_id: int,
    current_user: Dict = Depends(get_doctor_user),
    db: Session = Depends(get_db)
):
    doctor = current_user["doctor"]
    
    # Check if availability exists and belongs to this doctor
    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == availability_id,
        DoctorAvailability.doctor_id == doctor.id
    ).first()
    
    if not availability:
        raise HTTPException(
            status_code=404, 
            detail="Availability slot not found or you don't have permission to delete it"
        )
    
    db.delete(availability)
    db.commit()
    return {"message": "Availability slot deleted successfully"}

# Clinic Closure Management
@app.post("/clinic-closures/", response_model=ClinicClosureResponse, status_code=status.HTTP_201_CREATED)
def create_clinic_closure(
    closure: ClinicClosureCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Check if date is already marked as closed
    existing = db.query(ClinicClosure).filter(
        ClinicClosure.closure_date == closure.closure_date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Date {closure.closure_date} is already marked as a clinic closure"
        )
    
    # Check if there are existing appointments on this date
    existing_appointments = db.query(Appointment).filter(
        Appointment.appointment_date == closure.closure_date,
        Appointment.status.in_(["scheduled", "confirmed"])
    ).all()
    
    if existing_appointments:
        raise HTTPException(
            status_code=400,
            detail=f"There are {len(existing_appointments)} active appointments on {closure.closure_date}. Cancel them first."
        )
    
    db_closure = ClinicClosure(**closure.dict(), created_at=datetime.now().isoformat())
    db.add(db_closure)
    db.commit()
    db.refresh(db_closure)
    return db_closure

@app.get("/clinic-closures/", response_model=List[ClinicClosureResponse])
def get_clinic_closures(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(ClinicClosure)
    
    if start_date:
        query = query.filter(ClinicClosure.closure_date >= start_date)
    if end_date:
        query = query.filter(ClinicClosure.closure_date <= end_date)
    
    return query.all()

@app.delete("/clinic-closures/{closure_id}", response_model=Message)
def delete_clinic_closure(
    closure_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    closure = db.query(ClinicClosure).filter(ClinicClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="Clinic closure not found")
    
    db.delete(closure)
    db.commit()
    return {"message": "Clinic closure deleted successfully"}

# API Endpoints for Appointments
@app.post("/appointments/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment: AppointmentCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Received appointment creation request: {appointment}")
        
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        if not patient:
            logger.error(f"Patient not found: {appointment.patient_id}")
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
        if not doctor:
            logger.error(f"Doctor not found: {appointment.doctor_id}")
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Validate slot number
        if not 1 <= appointment.slot_number <= 16:
            logger.error(f"Invalid slot number: {appointment.slot_number}")
            raise HTTPException(
                status_code=400,
                detail="Slot number must be between 1 and 16"
            )
        
        # Check if the date is a clinic closure
        is_closed = db.query(ClinicClosure).filter(
            ClinicClosure.closure_date == appointment.appointment_date
        ).first()
        if is_closed:
            logger.error(f"Clinic closed on: {appointment.appointment_date}")
            raise HTTPException(
                status_code=400, 
                detail=f"The clinic is closed on {appointment.appointment_date}"
            )
        
        # Check doctor availability for this date
        availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == appointment.doctor_id,
            DoctorAvailability.date == appointment.appointment_date
        ).first()
        
        if not availability:
            logger.error(f"No availability for doctor {appointment.doctor_id} on {appointment.appointment_date}")
            raise HTTPException(
                status_code=400,
                detail="Doctor is not available on this date"
            )
        
        # Check if the requested slot is available
        slot_field = f"slot{appointment.slot_number}"
        if not getattr(availability, slot_field, False):
            logger.error(f"Slot {appointment.slot_number} not available")
            raise HTTPException(
                status_code=400,
                detail=f"Slot {appointment.slot_number} is not available"
            )
        
        # Check for existing appointments in this slot
        existing_appointment = db.query(Appointment).filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == appointment.appointment_date,
            Appointment.slot_number == appointment.slot_number,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).first()
        
        if existing_appointment:
            logger.error(f"Slot already booked: {appointment.slot_number}")
            raise HTTPException(
                status_code=400,
                detail="This slot is already booked"
            )
        
        # Create appointment
        db_appointment = Appointment(
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            appointment_date=appointment.appointment_date,
            slot_number=appointment.slot_number,
            appointment_type=appointment.appointment_type,
            reason=appointment.reason,
            notes=appointment.notes,
            duration_minutes=appointment.duration_minutes,
            status=AppointmentStatus.SCHEDULED,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        db.add(db_appointment)
        
        # Mark the slot as unavailable
        setattr(availability, slot_field, False)
        db.add(availability)
        
        db.commit()
        db.refresh(db_appointment)
        
        # Ensure the response includes slot_time
        response_data = db_appointment.__dict__
        response_data['slot_time'] = get_slot_time(db_appointment.slot_number)[0]
        
        logger.debug(f"Appointment created successfully: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/appointments/", response_model=List[AppointmentResponse])
def get_appointments(
    patient_id: Optional[str] = None,  # Changed from int to str
    doctor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    
    if patient_id:
        try:
            patient_uuid = uuid.UUID(patient_id)
            query = query.filter(Appointment.patient_id == patient_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    # Convert UUID to string in responses
    responses = []
    for appointment in appointments:
        appointment_dict = appointment.__dict__.copy()
        appointment_dict['patient_id'] = str(appointment.patient_id)
        responses.append(AppointmentResponse(**appointment_dict))
    
    return responses

@app.get("/appointments/detailed/", response_model=List[AppointmentWithDetails])
def get_appointments_with_details(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment).join(Patient).join(Doctor)
    
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

@app.get("/appointments/my/", response_model=List[AppointmentResponse])
def get_my_appointments(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    current_user: Dict = Depends(get_doctor_user),
    db: Session = Depends(get_db)
):
    doctor = current_user["doctor"]
    
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor.id)
    
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

@app.get("/appointments/{appointment_id}", response_model=AppointmentWithDetails)
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@app.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    update_data = appointment_update.dict(exclude_unset=True)
    
    # If date or slot is being updated, validate availability
    if "appointment_date" in update_data or "slot_number" in update_data:
        new_date = update_data.get("appointment_date", db_appointment.appointment_date)
        new_slot = update_data.get("slot_number", db_appointment.slot_number)
        doctor_id = update_data.get("doctor_id", db_appointment.doctor_id)
        
        # Check if the date is a clinic closure
        is_closed = db.query(ClinicClosure).filter(
            ClinicClosure.closure_date == new_date
        ).first()
        if is_closed:
            raise HTTPException(
                status_code=400, 
                detail=f"The clinic is closed on {new_date}"
            )
        
        # Check doctor availability for new date
        new_availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.date == new_date
        ).first()
        
        if not new_availability:
            raise HTTPException(
                status_code=400,
                detail="Doctor is not available on this date"
            )
        
        # Check if the new slot is available
        slot_field = f"slot{new_slot}"
        if not getattr(new_availability, slot_field, False):
            raise HTTPException(
                status_code=400,
                detail=f"Slot {new_slot} is not available"
            )
        
        # Check for existing appointments in this slot (excluding current appointment)
        existing_appointment = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == new_date,
            Appointment.slot_number == new_slot,
            Appointment.id != appointment_id,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).first()
        
        if existing_appointment:
            raise HTTPException(
                status_code=400,
                detail="This slot is already booked"
            )
        
        # If changing date/slot, free up the old slot
        if (new_date != db_appointment.appointment_date or 
            new_slot != db_appointment.slot_number):
            
            old_availability = db.query(DoctorAvailability).filter(
                DoctorAvailability.doctor_id == db_appointment.doctor_id,
                DoctorAvailability.date == db_appointment.appointment_date
            ).first()
            
            if old_availability:
                setattr(old_availability, f"slot{db_appointment.slot_number}", True)
                db.add(old_availability)
            
            # Mark new slot as unavailable
            setattr(new_availability, slot_field, False)
            db.add(new_availability)
    
    # Update appointment with validated data
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    
    # Update the updated_at timestamp
    db_appointment.updated_at = datetime.now().isoformat()
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.delete("/appointments/{appointment_id}", response_model=Message)
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Free up the slot
    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == db_appointment.doctor_id,
        DoctorAvailability.date == db_appointment.appointment_date
    ).first()
    
    if availability:
        setattr(availability, f"slot{db_appointment.slot_number}", True)
        db.add(availability)
    
    db.delete(db_appointment)
    db.commit()
    return {"message": "Appointment deleted successfully"}

@app.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    db_appointment.status = status
    if notes:
        db_appointment.notes = notes if not db_appointment.notes else f"{db_appointment.notes}\n\n{notes}"
    
    db_appointment.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.get("/available-slots/", response_model=Dict[str, List[AvailableSlot]])
def get_available_slots(
    doctor_id: int,
    date_from: date = Query(..., description="Start date to check availability"),
    date_to: date = Query(..., description="End date to check availability"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Get all clinic closures for the specified date range
    closures = {
        closure.closure_date for closure in db.query(ClinicClosure).filter(
            ClinicClosure.closure_date >= date_from,
            ClinicClosure.closure_date <= date_to
        ).all()
    }
    
    # Get all availabilities for the doctor
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.is_available == True
    ).all()
    
    # Get all existing appointments for the doctor within the date range
    existing_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= date_from,
        Appointment.appointment_date <= date_to,
        Appointment.status.in_(["scheduled", "confirmed"])
    ).all()
    
    # Organize appointments by date and time
    booked_slots = {}
    for appt in existing_appointments:
        date_str = appt.appointment_date.isoformat()
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        
        appt_end_time = (datetime.combine(appt.appointment_date, appt.appointment_time) + 
                         timedelta(minutes=appt.duration_minutes)).time()
        
        booked_slots[date_str].append({
            "start": appt.appointment_time,
            "end": appt_end_time
        })
    
    # Generate available slots
    result = {}
    current_date = date_from
    while current_date <= date_to:
        # Skip if clinic is closed
        if current_date in closures:
            current_date += timedelta(days=1)
            continue
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = current_date.weekday()
        
        # Find availabilities for this day
        day_availabilities = [a for a in availabilities if a.day_of_week == day_of_week]
        
        if day_availabilities:
            date_str = current_date.isoformat()
            result[date_str] = []
            
            for availability in day_availabilities:
                # Generate 30-minute slots within this availability period
                current_time = availability.start_time
                while current_time < availability.end_time:
                    # Check if slot overlaps with existing appointments
                    is_available = True
                    slot_end_time = (datetime.combine(date.today(), current_time) + 
                                    timedelta(minutes=30)).time()
                    
                    if date_str in booked_slots:
                        for booked in booked_slots[date_str]:
                            if not (slot_end_time <= booked["start"] or current_time >= booked["end"]):
                                is_available = False
                                break
                    
                    # Add slot if available
                    if is_available:
                        result[date_str].append(
                            AvailableSlot(
                                time=current_time.strftime("%H:%M"),
                                doctor_id=doctor_id,
                                doctor_name=doctor.name,
                                available=True
                            )
                        )
                    
                    # Move to next slot
                    current_time = (datetime.combine(date.today(), current_time) + 
                                   timedelta(minutes=30)).time()
        
        current_date += timedelta(days=1)
    
    return result
# Root endpoint
@app.get("/", response_model=Message)
def root():
    return {"message": "Welcome to the Dental Clinic Appointment Booking API"}
# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)