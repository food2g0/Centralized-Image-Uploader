import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, storage as firebase_storage
import datetime
import os
import uuid
import mimetypes
import time
import requests


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

# ✅ Initialize Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()

# -------------------------------
# ✅ Initialize Firebase Admin SDK
# -------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "records-management-faffa.firebasestorage.app"
    })

# ✅ Firestore Client
db = firestore.client()

# ✅ Admin Storage Bucket
bucket = firebase_storage.bucket()




def get_content_type(file_path):
    """Determine the correct content type for a file"""
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        extension = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
            '.tiff': 'image/tiff', '.tif': 'image/tiff', '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain', '.csv': 'text/csv'
        }
        content_type = content_type_map.get(extension, 'application/octet-stream')
    return content_type


def generate_permanent_url(storage_path):
    """Generate a permanent public URL for a file"""
    import urllib.parse
    encoded_path = urllib.parse.quote(storage_path, safe='')
    bucket_name = "records-management-faffa.firebasestorage.app"
    return f"https://storage.googleapis.com/{bucket_name}/{encoded_path}"


def upload_file_with_admin_sdk(file_path, storage_path):
    """Upload file using Admin SDK and make it permanently accessible"""
    try:
        blob = bucket.blob(storage_path)
        content_type = get_content_type(file_path)
        print(f"📋 Setting content type: {content_type} for {storage_path}")

        with open(file_path, 'rb') as file_data:
            blob.upload_from_file(file_data, content_type=content_type)

        print(f"✅ File uploaded using Admin SDK: {storage_path}")
        blob.make_public()
        print(f"✅ Made file publicly accessible")

        permanent_url = generate_permanent_url(storage_path)
        print(f"✅ Generated permanent public URL")
        return permanent_url

    except Exception as e:
        print(f"❌ Error uploading with Admin SDK: {e}")
        raise


def upload_with_pyrebase_and_make_permanent(file_path, storage_path):
    """Upload using Pyrebase then make permanent using Admin SDK"""
    try:
        print(f"📤 Uploading with Pyrebase: {storage_path}")
        storage.child(storage_path).put(file_path)
        time.sleep(2)

        blob = bucket.blob(storage_path)

        # Wait for file to be available
        max_retries = 5
        for attempt in range(max_retries):
            if blob.exists():
                break
            print(f"⏳ Waiting for file (attempt {attempt + 1}/{max_retries})")
            time.sleep(2)

        if not blob.exists():
            raise Exception("File was not uploaded successfully")

        # Fix content type
        content_type = get_content_type(file_path)
        blob.content_type = content_type
        blob.patch()
        print(f"🔧 Fixed content type to: {content_type}")

        blob.make_public()
        print(f"✅ Made file permanently accessible")

        permanent_url = generate_permanent_url(storage_path)
        return permanent_url

    except Exception as e:
        print(f"❌ Error in hybrid upload method: {e}")
        raise


def test_url_accessibility(url):
    """Test if a URL is accessible"""
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ URL is accessible")
            return True
        else:
            print(f"❌ URL returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing URL: {e}")
        return False


# -------------------------------
# ✅ MAIN FUNCTION FOR YOUR EXISTING CODE
# -------------------------------

def get_download_url_with_fallback(storage_path):
    """
    UPDATED: Get permanent URL instead of temporary signed URLs
    This replaces the old function that was causing expiration issues
    """
    try:
        print(f"🔄 Getting permanent URL for {storage_path}")

        blob = bucket.blob(storage_path)

        # Wait for file to be available
        max_retries = 5
        for attempt in range(max_retries):
            if blob.exists():
                break
            print(f"⏳ Waiting for file (attempt {attempt + 1}/{max_retries})")
            time.sleep(2)

        if not blob.exists():
            blob.reload()
            if not blob.exists():
                raise Exception(f"File does not exist at path: {storage_path}")

        # Make it public for permanent access
        blob.make_public()
        print(f"✅ Made file permanently accessible")

        # Generate permanent URL
        permanent_url = generate_permanent_url(storage_path)
        print(f"✅ Generated permanent URL")

        return permanent_url

    except Exception as e:
        print(f"❌ Error generating permanent URL: {e}")
        raise


def upload_and_store_file(file_path, user_id, filename=None, collection_name="Uploaded_Images"):
    """Complete upload function with permanent URLs"""
    try:
        if not os.path.exists(file_path):
            raise Exception(f"File does not exist: {file_path}")

        if filename is None:
            filename = os.path.basename(file_path)

        # Generate unique storage path
        unique_id = str(uuid.uuid4())
        storage_path = f"uploads/{user_id}/{unique_id}_{filename}"

        print(f"🚀 Starting upload for: {filename}")

        # Try Admin SDK first
        try:
            permanent_url = upload_file_with_admin_sdk(file_path, storage_path)
        except Exception as admin_error:
            print(f"⚠️ Admin SDK failed: {admin_error}")
            # Fallback to Pyrebase + Admin SDK
            permanent_url = upload_with_pyrebase_and_make_permanent(file_path, storage_path)

        # Test URL
        if test_url_accessibility(permanent_url):
            # Store in Firestore
            doc_data = {
                'filename': filename,
                'storage_path': storage_path,
                'url': permanent_url,
                'user_id': user_id,
                'upload_date': datetime.datetime.now(),
                'permanent_url': True,
                'file_size': os.path.getsize(file_path),
                'content_type': get_content_type(file_path)
            }

            doc_ref = db.collection(collection_name).add(doc_data)
            print(f"✅ Stored in Firestore")

            return {
                'success': True,
                'url': permanent_url,
                'storage_path': storage_path,
                'doc_id': doc_ref[1].id,
                'filename': filename
            }
        else:
            raise Exception("Generated URL is not accessible")

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# -------------------------------
# ✅ LEGACY FUNCTIONS (for backward compatibility)
# -------------------------------

def get_proper_download_url(storage_path):
    """Legacy function - now returns permanent URL"""
    return get_download_url_with_fallback(storage_path)


def get_public_download_url(storage_path):
    """Legacy function - now returns permanent URL"""
    return get_download_url_with_fallback(storage_path)


def get_pyrebase_url_with_manual_token(storage_path):
    """Legacy function - now returns permanent URL"""
    return get_download_url_with_fallback(storage_path)


def fix_content_type_after_pyrebase_upload(storage_path, filename):
    """Fix content type after Pyrebase upload"""
    try:
        blob = bucket.blob(storage_path)
        if not blob.exists():
            print(f"⚠️ File doesn't exist: {storage_path}")
            return

        content_type = get_content_type(filename)
        blob.reload()
        if blob.content_type != content_type:
            print(f"🔧 Fixing content type: {blob.content_type} → {content_type}")
            blob.content_type = content_type
            blob.patch()
        else:
            print(f"✅ Content type already correct: {content_type}")

    except Exception as e:
        print(f"❌ Error fixing content type: {e}")


def make_all_existing_files_permanent(collection_name="Uploaded_Images"):
    """Make all existing files permanent"""
    try:
        print("🔄 Making all existing files permanent...")
        docs = db.collection(collection_name).stream()
        updated_count = 0

        for doc in docs:
            data = doc.to_dict()
            storage_path = data.get('storage_path')

            if storage_path:
                try:
                    permanent_url = get_download_url_with_fallback(storage_path)
                    if test_url_accessibility(permanent_url):
                        doc.reference.update({
                            'url': permanent_url,
                            'permanent_url': True,
                            'updated_at': datetime.datetime.now()
                        })
                        updated_count += 1
                        print(f"✅ Updated: {data.get('filename', storage_path)}")
                except Exception as e:
                    print(f"❌ Error: {e}")

        print(f"✅ Made {updated_count} files permanent")
        return updated_count

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0