# login_gui.py

print("[login_gui.py] Starting login GUI...")
import tkinter as tk
from tkinter import messagebox
try:
    from auth import login_user
    from dashboard import open_dashboard
except Exception as import_err:
    print(f"[login_gui.py] Import error: {import_err}")
# login_gui.py

def main():
    
    global root
    root = tk.Tk()
    root.title("Login")
    root.geometry("300x200")
    root.resizable(False, False)

    tk.Label(root, text="Username:").pack(pady=5)
    entry_username = tk.Entry(root)
    entry_username.pack(pady=5)

    tk.Label(root, text="Password:").pack(pady=5)
    entry_password = tk.Entry(root, show="*")
    entry_password.pack(pady=5)

    def on_login():
        global next_screen, next_user_data
        username = entry_username.get()
        password = entry_password.get()
        if not username or not password:
            messagebox.showwarning("Missing Info", "Please enter both username and password.")
            return
        # 🔐 Check for Admin login
        if username == "Admin" and password == "Admin1234":
            messagebox.showinfo("Login Success", "Welcome Admin!")
            root.quit()
            next_screen = 'admin'
            return
        # 🧑‍💼 Regular branch login
        try:
            user_data = login_user(username, password)
            if user_data:
                messagebox.showinfo("Login Success", f"Welcome {user_data['branch']}!")
                root.quit()
                next_screen = 'dashboard'
                next_user_data = user_data
            else:
                messagebox.showerror("Login Failed", "Invalid credentials.")
        except Exception as login_err:
            import traceback
            tb = traceback.format_exc()
            print(f"[login_gui.py] Error during login: {login_err}\n{tb}")
            messagebox.showerror("Login Error", f"Error: {login_err}\n\n{tb}")

    tk.Button(root, text="Login", command=on_login).pack(pady=15)
    print("[login_gui.py] Login window should now be visible.")
    global next_screen, next_user_data
    next_screen = None
    next_user_data = None
    root.mainloop()
    # After mainloop ends, launch the next screen if set
    if next_screen == 'admin':
        from admin_dashboard import open_admin_dashboard
        open_admin_dashboard()
    elif next_screen == 'dashboard' and next_user_data:
        from dashboard import open_dashboard
        open_dashboard(next_user_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as main_err:
        print(f"[login_gui.py] Error in main(): {main_err}")
