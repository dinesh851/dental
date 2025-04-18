import requests
import json
from datetime import date, timedelta

# API base URL
base_url = "http://localhost:8000/"

# Admin authentication token
admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0NDMwMDA0N30.QxfebnB3CZDwMUHF8-APK6XUWLK7YDJ5g1xRBM9MuL4"
# Request headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {admin_token}"
}

# Get next 7 days
today = date.today()
dates = [(today + timedelta(days=i)).isoformat() for i in range(7)]

# Request body - setting availability for all slots across multiple dates
 
data = {
    "doctor_id": 1,
    "availability": [
        {
            "date": "2025-04-30",
            "slot_values": {
                "slot1": True, "slot2": True, "slot3": True, "slot4": True,
                "slot5": False, "slot6": False, "slot7": False, "slot8": False,
                "slot9": True, "slot10": True, "slot11": True, "slot12": True,
                "slot13": False, "slot14": False, "slot15": False, "slot16": False
            }
        },
        {
            "date": "2025-05-01",
            "slot_values": {
                "slot1": True, "slot2": False, "slot3": False, "slot4": False,
                "slot5": True, "slot6": True, "slot7": True, "slot8": True,
                "slot9": False, "slot10": False, "slot11": False, "slot12": False,
                "slot13": True, "slot14": True, "slot15": True, "slot16": True
            }
        }
    ]
}
  
# Send POST request
response = requests.post(
    f"{base_url}/doctor-availability/bulk/", 
    headers=headers,
    data=json.dumps(data)
)

# Print response
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")