from flask import Flask, render_template, request, jsonify,session,redirect,url_for
from pymongo import MongoClient

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from pymongo.server_api import ServerApi

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# connection_string='mongodb+srv://2001uditagrawal:kATGc2ILD8MoECiP@cluster0.4mlly09.mongodb.net/'

uri = "mongodb+srv://2001uditagrawal:vlirYE5ha9tPy6ec@cluster0.4mlly09.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


app = Flask(__name__)
app.secret_key = os.urandom(24)


# MongoDB connection
db = client['medicine_reminder']  # Replace 'medicine_reminder' with your database name
medicines_collection = db['medicines']  # Collection to store medicines

users_collection = db['users']



@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'username': username, 'password': password})

        if user:
            session['user_id'] = str(user['_id'])  # Convert ObjectId to string
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if user_id:
        # Perform actions for a logged-in user
        return render_template('index.html',user_id=user_id)

    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            return render_template('register.html', error='Username already exists')

        # If username is not already taken, insert the new user into the database
        new_user = {'username': username, 'password': password}
        users_collection.insert_one(new_user)

        return redirect(url_for('login'))

    return render_template('register.html')




@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

# Route for the dashboard page



@app.route("/index",methods=['GET','POST'])
def index():
  if request.method == 'POST':
    userName=request.form['userName']
    medicalHistory=request.form['medicalHistory']
    user_details={
      'userName':userName,
      'medicalHistory':medicalHistory
    } 
    result=users_collection.insert_one(user_details)   
    
    return render_template('add_medicines.html')  # Render the HTML form here

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
  last_medicine = medicines_collection.find_one(sort=[('_id', -1)])

  # medicines = list(medicines_collection.find())


  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
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

    events = {
            "summary": f"Take {last_medicine['repetition_count']} {last_medicine['medicine_name']}",
            "location": "home",
            "description": f"Reminder to take {last_medicine['repetition_count']} {last_medicine['medicine_name']}",
            "start": {
                "dateTime": datetime.now().isoformat(),  # Remove time zone offset here
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "recurrence": [f"RRULE:FREQ={last_medicine['repetitiveness'].upper()};COUNT={last_medicine['repetition_count']}"],
            "attendees": [
                {"email": "08udit@bhu.ac.in"},
            ],
        }
    event=service.events().insert(calendarId="primary", body=events).execute()
    print("Event created: %s" % (event.get("htmlLink")))
    

  except HttpError as error:
    print(f"An error occurred: {error}")

  return render_template('add_medicines.html')

# if __name__ == '__main__':
#     app.run(debug=True)
