import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, storage as firebase_storage

# -------------------------------
# ✅ Pyrebase Config for Client-side Auth & Upload
# -------------------------------
firebase_config = {
    "apiKey": "AIzaSyCsynYGglyDldPZ15LniRS-lOvYa50Zyns",
    "authDomain": "records-management-faffa.firebaseapp.com",
    "projectId": "records-management-faffa",
    "storageBucket": "records-management-faffa.firebasestorage.app",  # ✅ Corrected from .firebasestorage.app
    "messagingSenderId": "344649128709",
    "appId": "1:344649128709:web:b7b02511caaf5633e9356c",
    "measurementId": "G-BHVLRPV7J8",
    "databaseURL": "https://records-management-faffa.firebaseio.com"
}

# ✅ Initialize Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()  # For upload/download via user session

# -------------------------------
# ✅ Initialize Firebase Admin SDK (for Firestore & Admin Storage Access)
# -------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # ⚠️ Ensure this file exists
    firebase_admin.initialize_app(cred, {
        "storageBucket": "records-management-faffa.firebasestorage.app"  # ✅ Required for Admin SDK storage
    })

# ✅ Firestore Client
db = firestore.client()

# ✅ Admin Storage Bucket (used for delete operations)
bucket = firebase_storage.bucket()
