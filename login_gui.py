import tkinter as tk
from tkinter import messagebox
import os

try:
    from auth import login_user
    from dashboard import open_dashboard
    from firebase_config import db  # Firestore instance
except Exception as import_err:
    print(f"[login_gui.py] Import error: {import_err}")

CREDENTIALS_FILE = "saved_credentials.txt"

def save_credentials(username, password):
    try:
        with open(CREDENTIALS_FILE, "w") as f:
            f.write(f"{username}\n{password}")
    except Exception as e:
        print(f"[login_gui.py] Failed to save credentials: {e}")

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    return lines[0].strip(), lines[1].strip()
        except Exception as e:
            print(f"[login_gui.py] Failed to load credentials: {e}")
    return "", ""

def check_admin_login(username, password):
    try:
        admins = db.collection("Admin").where("username", "==", username).where("password", "==", password).stream()
        for admin in admins:
            return admin.to_dict()
        return None
    except Exception as e:
        print(f"[login_gui.py] Error checking admin login: {e}")
        return None

def check_user_login(username, password):
    try:
        users = db.collection("Users_db").where("username", "==", username).where("password", "==", password).stream()
        for user in users:
            return user.to_dict()
        return None
    except Exception as e:
        print(f"[login_gui.py] Error checking user login: {e}")
        return None

def check_head_office_login(username, password):
    """Check if user exists in Head_Office_USR collection"""
    try:
        head_office_users = db.collection("Head_Office_USR").where("username", "==", username).where("password", "==", password).stream()
        for user in head_office_users:
            return user.to_dict()
        return None
    except Exception as e:
        print(f"[login_gui.py] Error checking head office login: {e}")
        return None

def main():
    global root
    root = tk.Tk()
    root.title("Record Management System")
    root.geometry("500x400")
    root.resizable(False, False)

    tk.Label(root, text="Record Management System", font=("Arial", 14, "bold")).pack(pady=20)

    form_frame = tk.Frame(root)
    form_frame.pack(pady=10)

    tk.Label(form_frame, text="Username:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    entry_username = tk.Entry(form_frame, width=25, font=("Arial", 10))
    entry_username.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(form_frame, text="Password:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    entry_password = tk.Entry(form_frame, show="*", width=25, font=("Arial", 10))
    entry_password.grid(row=1, column=1, padx=10, pady=10)

    remember_var = tk.BooleanVar()
    remember_check = tk.Checkbutton(root, text="Remember Me", variable=remember_var, font=("Arial", 9))
    remember_check.pack()

    # Load saved credentials
    saved_user, saved_pass = load_credentials()
    entry_username.insert(0, saved_user)
    entry_password.insert(0, saved_pass)
    if saved_user and saved_pass:
        remember_var.set(True)

    def on_login():
        global next_screen, next_user_data
        username = entry_username.get().strip()
        password = entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing Info", "Please enter both username and password.")
            return

        if remember_var.get():
            save_credentials(username, password)
        else:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)

        # 1. Try Admin login
        admin_data = check_admin_login(username, password)
        if admin_data:
            group = admin_data.get('group', 'Unknown Group')
            messagebox.showinfo("Login Success", f"Welcome Admin of {group}!")
            root.destroy()
            next_screen = 'admin'
            next_user_data = admin_data
            return

        # 2. Try Head Office login
        head_office_data = check_head_office_login(username, password)
        if head_office_data:
            messagebox.showinfo("Login Success", f"Welcome Head Office User!")
            root.destroy()
            next_screen = 'head_office'
            next_user_data = head_office_data
            return

        # 3. Try Branch user login
        user_data = check_user_login(username, password)
        if user_data:
            messagebox.showinfo("Login Success", f"Welcome {user_data.get('branch', 'User')}!")
            root.destroy()
            next_screen = 'dashboard'
            next_user_data = user_data
            return

        # 4. If no match
        messagebox.showerror("Login Failed", "Invalid credentials.")

    tk.Button(root, text="Login", font=("Arial", 10, "bold"), width=20, command=on_login).pack(pady=20)

    print("[login_gui.py] Login window should now be visible.")
    global next_screen, next_user_data
    next_screen = None
    next_user_data = None
    root.mainloop()

    # Route based on user type
    if next_screen == 'admin':
        try:
            group = next_user_data.get('group', '').lower()
            if group == 'group 1':
                from admin_dashboard_group1 import open_admin_dashboard_group1
                open_admin_dashboard_group1(next_user_data)
            elif group == 'group 2':
                from admin_dashboard_group2 import open_admin_dashboard_group2
                open_admin_dashboard_group2(next_user_data)
            elif group == 'group 3':
                from admin_dashboard import open_admin_dashboard_group3
                open_admin_dashboard_group3(next_user_data)
            else:
                from admin_dashboard import open_admin_dashboard
                open_admin_dashboard(next_user_data)
        except Exception as admin_err:
            print(f"[login_gui.py] Error opening admin dashboard: {admin_err}")
            messagebox.showerror("Admin Dashboard Error", f"Could not open admin dashboard: {admin_err}")

    elif next_screen == 'head_office':
        try:
            print(f"[login_gui.py] Attempting to open head office dashboard with user data: {next_user_data}")
            # Import the main dashboard function that accepts user_data
            from head_office_dashboard import open_head_office_dashboard
            open_head_office_dashboard(next_user_data)
        except ImportError as import_err:
            print(f"[login_gui.py] Import error for head office dashboard: {import_err}")
            messagebox.showerror("Import Error", "Could not import head_office_dashboard module. Please ensure the file exists.")
        except Exception as head_office_err:
            print(f"[login_gui.py] Error opening head office dashboard: {head_office_err}")
            print(f"[login_gui.py] User data type: {type(next_user_data)}")
            messagebox.showerror("Head Office Dashboard Error", f"Could not open head office dashboard: {head_office_err}")

    elif next_screen == 'dashboard' and next_user_data:
        open_dashboard(next_user_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as main_err:
        print(f"[login_gui.py] Error in main(): {main_err}")