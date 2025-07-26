print("[login_gui.py] Starting login GUI...")

import tkinter as tk
from tkinter import messagebox

try:
    from auth import login_user
    from dashboard import open_dashboard
    from firebase_config import db  # Firebase Firestore instance
except Exception as import_err:
    print(f"[login_gui.py] Import error: {import_err}")

def check_admin_login(username, password):
    try:
        admins = db.collection("Admin").where("username", "==", username).where("password", "==", password).stream()
        for admin in admins:
            admin_data = admin.to_dict()
            return admin_data  # Return full document if found
        return None
    except Exception as e:
        print(f"[login_gui.py] Error checking admin login: {e}")
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

    def on_login():
        global next_screen, next_user_data
        username = entry_username.get().strip()
        password = entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing Info", "Please enter both username and password.")
            return

        # Check if it's an admin login first
        admin_data = check_admin_login(username, password)
        if admin_data:
            group = admin_data.get('group', 'Unknown Group')
            messagebox.showinfo("Login Success", f"Welcome Admin of {group}!")
            root.destroy()
            next_screen = 'admin'
            next_user_data = admin_data
            return

        # Else, check normal user login
        try:
            user_data = login_user(username, password)
            if user_data:
                messagebox.showinfo("Login Success", f"Welcome {user_data['branch']}!")
                root.destroy()
                next_screen = 'dashboard'
                next_user_data = user_data
            else:
                messagebox.showerror("Login Failed", "Invalid credentials.")
        except Exception as login_err:
            import traceback
            tb = traceback.format_exc()
            print(f"[login_gui.py] Error during login: {login_err}\n{tb}")
            messagebox.showerror("Login Error", f"Error: {login_err}\n\n{tb}")

    tk.Button(root, text="Login", font=("Arial", 10, "bold"), width=20, command=on_login).pack(pady=20)

    print("[login_gui.py] Login window should now be visible.")
    global next_screen, next_user_data
    next_screen = None
    next_user_data = None
    root.mainloop()

    # Handle dashboard routing after login
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
                from admin_dashboard import open_admin_dashboard  # fallback
                open_admin_dashboard(next_user_data)
        except Exception as admin_err:
            print(f"[login_gui.py] Error opening admin dashboard: {admin_err}")
            messagebox.showerror("Admin Dashboard Error", f"Could not open admin dashboard: {admin_err}")

    elif next_screen == 'dashboard' and next_user_data:
        from dashboard import open_dashboard
        open_dashboard(next_user_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as main_err:
        print(f"[login_gui.py] Error in main(): {main_err}")
