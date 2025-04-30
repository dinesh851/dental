# api_test_client.py
import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

# Headers for JSON requests
headers = {
    "Content-Type": "application/json",
}

# Authentication headers (will be updated after login)
auth_headers = {
    "Content-Type": "application/json",
    "Authorization": ""
}

admin_auth_headers = {
    "Content-Type": "application/json",
    "Authorization": ""
}

def  print_response(response,  message=""):
    """Print formatted API response"""
    print(f"\n{'='*50}")
    print(f"{message.upper() if message else 'RESPONSE'}")
    print(f"Status code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print(f"{'='*50}\n")

def send_otp(mobile_number):
    """Send OTP to mobile number"""
    url = f"{BASE_URL}/send-otp/"
    data = {"mobile_number": mobile_number}
    response = requests.post(url, json=data, headers=headers)
    print(data,"data")
    print_response(response,  "Sending OTP")
    return response.json()

def login_patient(mobile_number, otp):
    """Login with OTP"""
    url = f"{BASE_URL}/login/"
    data = {"mobile_number": mobile_number, "otp": otp}
    response = requests.post(url, json=data, headers=headers)
    print(data,"data")
    print_response(response,  "Patient Login")
    
    # Update auth headers with token
    if response.status_code == 200:
        token = response.json()["access_token"]
        auth_headers["Authorization"] = f"Bearer {token}"
        print("Token saved for authenticated requests")
    
    return response.json()

def update_patient_profile(name, email=None, address=None, date_of_birth=None):
    """Update patient profile"""
    url = f"{BASE_URL}/patients/update"
    data = {
        "name": name,
        "mobile_number": mobile_number,  # Using the global mobile_number
        "email": email,
        "address": address,
        "date_of_birth": date_of_birth,
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    response = requests.put(url, json=data, headers=auth_headers)
    print(data,"data")
    print_response(response,  "Updating Patient Profile")
    return response.json()

def get_patient_profile():
    """Get current patient profile"""
    url = f"{BASE_URL}/patients/me"
    response = requests.get(url, headers=auth_headers)
    print_response(response,  "Getting Patient Profile")
    return response.json()

def get_all_doctors():
    """Get list of all doctors"""
    url = f"{BASE_URL}/doctors/"
    response = requests.get(url, headers=headers)
    print_response(response,  "Getting All Doctors")
    return response.json()

def create_appointment(doctor_id, days_from_now=7, notes=None):
    """Create a new appointment"""
    appointment_datetime = (datetime.now() + timedelta(days=days_from_now)).isoformat()
    
    url = f"{BASE_URL}/appointments/"
    data = {
        "doctor_id": doctor_id,
        "appointment_datetime": appointment_datetime,
        "notes": notes
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    response = requests.post(url, json=data, headers=auth_headers)
    print(data,"data")
    print_response(response,  "Creating Appointment")
    return response.json()

def get_patient_appointments():
    """Get all appointments for the current patient"""
    url = f"{BASE_URL}/appointments/"
    response = requests.get(url, headers=auth_headers)
    print_response(response,  "Getting Patient Appointments")
    return response.json()

def get_specific_appointment(appointment_id):
    """Get a specific appointment"""
    url = f"{BASE_URL}/appointments/{appointment_id}"
    response = requests.get(url, headers=auth_headers)
    print_response(response,  f"Getting Appointment {appointment_id}")
    return response.json()

def cancel_appointment(appointment_id):
    """Cancel a specific appointment"""
    url = f"{BASE_URL}/appointments/{appointment_id}/cancel"
    response = requests.put(url, headers=auth_headers)
    print_response(response,  f"Cancelling Appointment {appointment_id}")
    return response.json()

def create_admin(username, password, is_superadmin=False):
    """Create a new admin user"""
    url = f"{BASE_URL}/admin/create"
    data = {
        "username": username,
        "password": password,
        "is_superadmin": is_superadmin
    }
    response = requests.post(url, json=data, headers=headers)
    print(data,"data")
    print_response(response,  "Creating Admin User")
    return response.json() if response.status_code == 200 else response.text

def admin_login(username, password):
    """Admin login"""
    url = f"{BASE_URL}/admin/login?username={username}&password={password}"
    response = requests.post(url, headers=headers)
    print_response(response,  "Admin Login")
    
    # Update admin auth headers with token
    if response.status_code == 200:
        token = response.json()["access_token"]
        admin_auth_headers["Authorization"] = f"Bearer {token}"
        print("Admin token saved for authenticated requests")
    
    return response.json() if response.status_code == 200 else response.text

def get_all_patients():
    """Get all patients (admin only)"""
    url = f"{BASE_URL}/admin/patients"
    response = requests.get(url, headers=admin_auth_headers)
    print_response(response,  "Getting All Patients (Admin)")
    return response.json() if response.status_code == 200 else response.text

def get_all_appointments():
    """Get all appointments (admin only)"""
    url = f"{BASE_URL}/admin/appointments"
    response = requests.get(url, headers=admin_auth_headers)
    print_response(response,  "Getting All Appointments (Admin)")
    return response.json() if response.status_code == 200 else response.text


# ----- Run Test Scenarios -----

if __name__ == "__main__":
    # Patient Flow
    mobile_number = "9876543210"  # Change this to your test number
    
    # Send OTP
    send_otp_response = send_otp(mobile_number)
    
    # For testing, we'll access the OTP directly from the database
    # In a real scenario, the user would receive the OTP via SMS
    # You'll need to manually enter the OTP here or modify the code to fetch it from the database
    otp = input("Enter the OTP you received (or check your database/logs): ")
    
    # Login with OTP
    login_response = login_patient(mobile_number, otp)
    
    # Update profile
    update_profile_response = update_patient_profile(
        name="John Doe",
        email="john.doe@example.com",
        address="123 Main St, Anytown, USA",
        date_of_birth="1990-01-01T00:00:00"
    )
    
    # Get profile
    profile_response = get_patient_profile()
    
    # Get doctors
    doctors_response = get_all_doctors()
    
    # Create an appointment (assuming there's at least one doctor)
    if doctors_response and len(doctors_response) > 0:
        doctor_id = doctors_response[0]["id"]
        appointment_response = create_appointment(
            doctor_id=doctor_id,
            days_from_now=10,
            notes="Regular dental checkup"
        )
        
        # Get all appointments
        appointments_response = get_patient_appointments()
        
        # Get specific appointment
        if appointments_response and len(appointments_response) > 0:
            appointment_id = appointments_response[0]["id"]
            specific_appointment = get_specific_appointment(appointment_id)
            
            # Cancel appointment
            cancel_response = cancel_appointment(appointment_id)
    
    # Admin Flow
    # Create admin user
    create_admin_response = create_admin(
        username="testadmin",
        password="testpassword123",
        is_superadmin=True
    )
    
    # Admin login
    admin_login_response = admin_login(username="testadmin", password="testpassword123")
    
    # Get all patients (admin only)
    all_patients_response = get_all_patients()
    
    # Get all appointments (admin only)
    all_appointments_response = get_all_appointments()
    
    print("\nAll test scenarios completed!")


# ----- Bonus: Create Multiple Mock Patients and Appointments -----

def create_mock_data(num_patients=5):
    """Create multiple mock patients and appointments"""
    print("\n\nCreating mock data...")
    
    for i in range(1, num_patients + 1):
        # Create patient
        mock_mobile = f"98765{i:05d}"
        print(f"\nCreating patient with mobile: {mock_mobile}")
        
        # Send OTP
        send_otp(mock_mobile)
        
        # For testing, we'll use a fixed OTP (in a real scenario, this would be different for each user)
        mock_otp = "123456"  # You'd need to update your database to make this work
        login_patient(mock_mobile, mock_otp)
        
        # Update profile
        update_patient_profile(
            name=f"Mock User {i}",
            email=f"user{i}@example.com",
            address=f"Address {i}, Test City",
            date_of_birth=f"1990-{i:02d}-01T00:00:00"
        )
        
        # Create appointments
        doctors = get_all_doctors()
        if doctors and len(doctors) > 0:
            for j, doctor in enumerate(doctors[:2]):  # Create up to 2 appointments per patient
                create_appointment(
                    doctor_id=doctor["id"],
                    days_from_now=j+5,
                    notes=f"Appointment {j+1} for patient {i}"
                )
    
    print("\nMock data creation completed!")

# Uncomment to create mock data
create_mock_data(num_patients=5)