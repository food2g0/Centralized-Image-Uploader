import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore


firebase_config = {

  "apiKey": "AIzaSyCsynYGglyDldPZ15LniRS-lOvYa50Zyns",
  "authDomain": "records-management-faffa.firebaseapp.com",
  "projectId": "records-management-faffa",
  "storageBucket": "records-management-faffa.firebasestorage.app",
  "messagingSenderId": "344649128709",
  "appId": "1:344649128709:web:b7b02511caaf5633e9356c",
  "measurementId": "G-BHVLRPV7J8",
  "databaseURL": "https://records-management-faffa.firebaseio.com"
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