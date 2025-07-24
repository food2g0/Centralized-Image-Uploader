# auth.py

from firebase_config import db

def login_user(username, password):
    try:
        # Query Firestore for matching username and password
        users_ref = db.collection('Users_db')
        query = users_ref.where('username', '==', username).where('password', '==', password).stream()

        for doc in query:
            user_data = doc.to_dict()
            print(f"✅ Login successful! Branch: {user_data['branch']}")
            return user_data  # Return branch or user info

        # If no matching user is found
        print("❌ Invalid username or password.")
        return None

    except Exception as e:
        print("🔥 Error during login:", e)
        return None
