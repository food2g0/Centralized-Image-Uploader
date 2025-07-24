import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore


firebase_config = {
  "apiKey": "AIzaSyDyoYCZpanf7BIlfi7ZOtYOEDKdjLl7M1s",
  "authDomain": "food2go-44539.firebaseapp.com",
  "databaseURL": "https://food2go-44539-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "food2go-44539",
  "storageBucket": "food2go-44539.appspot.com",
  "messagingSenderId": "844894233705",
  "appId": "1:844894233705:web:9a67330b4ffa82d2a1eef8",
  "measurementId": "G-576G92N335"
}


firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()

# ✅ Initialize Admin SDK only if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # Ensure this path is correct
    firebase_admin.initialize_app(cred)

# ✅ Now this works safely
db = firestore.client()