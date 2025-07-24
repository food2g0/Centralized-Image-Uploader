# login_gui.py

import tkinter as tk
from tkinter import messagebox
from auth import login_user
from dashboard import open_dashboard

def main():
    def on_login():
        username = entry_username.get()
        password = entry_password.get()

        if not username or not password:
            messagebox.showwarning("Missing Info", "Please enter both username and password.")
            return

    # 🔐 Check for Admin login
        if username == "Admin" and password == "Admin1234":
            messagebox.showinfo("Login Success", "Welcome Admin!")
            root.destroy()
            from admin_dashboard import open_admin_dashboard
            open_admin_dashboard()
            return

    # 🧑‍💼 Regular branch login
        user_data = login_user(username, password)
        if user_data:
            messagebox.showinfo("Login Success", f"Welcome {user_data['branch']}!")
            root.destroy()
            from dashboard import open_dashboard
            open_dashboard(user_data)
        else:
            messagebox.showerror("Login Failed", "Invalid credentials.")


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

    tk.Button(root, text="Login", command=on_login).pack(pady=15)
    root.mainloop()

if __name__ == "__main__":
    main()
