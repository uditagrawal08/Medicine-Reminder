from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import tkinter.messagebox as tkMessageBox

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['medicine_reminder']  # Replace 'medicine_reminder' with your database name
medicines_collection = db['medicines']  # Collection to store medicines

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML form here

@app.route('/add_medicines', methods=['GET', 'POST'])
def add_medicines():
    if request.method == 'POST':
        medicine_name = request.form['medicineName']
        repetitiveness = request.form['repetitiveness']
        repetition_count = int(request.form['repetitionCount'])

        medicine_data = {
            'medicine_name': medicine_name,
            'repetitiveness': repetitiveness,
            'repetition_count': repetition_count
        }

        result = medicines_collection.insert_one(medicine_data)
        
        if result.inserted_id:
            return render_template('index.html')
    # Handle POST request for adding medicines to the database
        # Your logic to process form data and interact with the database
    
    # Render the add_medicines.html page for GET requests
    return render_template('add_medicines.html')


@app.route('/medicines_report')
def medicines_report():
    medicines = list(medicines_collection.find())
      # Retrieve all medicines from MongoDB
    return render_template('medicines_report.html', medicines=medicines)


@app.route('/add_calender')
def add_calender():
  medicines = list(medicines_collection.find())
  
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    events={
      "summary": "Mediciene",
      "location": "Home",
      "description": "Be Healthy Tke Mediciene On Time",
      "start": {
      "dateTime": "2024-02-01T09:00:00",  # Remove time zone offset here
      "timeZone": "Asia/Kolkata"
        },
      "end": {
      "dateTime": "2024-02-03T17:00:00",
      "timeZone": "Asia/Kolkata"
      },
      "recurrence": ["RRULE:FREQ={ medicine.repetitiveness};COUNT={ medicine.repetition_count }"],
      "attendees": [
        {"email": "08udit@bhu.ac.in"},
    
      ],
    }
    event=service.events().insert(calendarId="primary", body=events).execute()
    print("Event created: %s" % (event.get("htmlLink")))
    

  except HttpError as error:
    print(f"An error occurred: {error}")
    

    
    return tkMessageBox.showinfo("Your Event is Saved")
 

if __name__ == '__main__':
    app.run(debug=True)
