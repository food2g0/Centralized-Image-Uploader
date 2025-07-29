import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from firebase_config import db

def get_next_username():
    try:
        users = db.collection("Users_db").stream()
        max_id = 0
        for user in users:
            data = user.to_dict()
            uname = data.get("username", "")
            if uname.startswith("usr-"):
                try:
                    num = int(uname.split("-")[1])
                    max_id = max(max_id, num)
                except ValueError:
                    continue
        next_id = max_id + 1
        return f"usr-{next_id:05d}"
    except Exception as e:
        print(f"Error fetching username: {e}")
        return "usr-00001"

def open_add_user_popup_group2(parent):
    
    popup = tk.Toplevel(parent)
    popup.title("Add New User")
    popup.geometry("420x400")
    popup.resizable(False, False)
    popup.grab_set()

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("TEntry", padding=4)
    style.configure("TCombobox", padding=4)

    # Title label
    title_label = ttk.Label(popup, text="Add New User", font=("Segoe UI", 14, "bold"))
    title_label.pack(pady=10)

    form_frame = ttk.Frame(popup, padding=10)
    form_frame.pack()

    uname_var = tk.StringVar()
    pwd_var = tk.StringVar()
    cpwd_var = tk.StringVar()
    branch_var = tk.StringVar()
    corporate_var = tk.StringVar()
    show_password_var = tk.BooleanVar(value=False)

    def refresh_username():
        try:
            new_uname = get_next_username()
            uname_var.set(new_uname)
        except Exception as e:
            print("Error in refresh_username:", e)

    refresh_username()

    # Row 0 - Username + refresh
    ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    username_entry = ttk.Entry(form_frame, textvariable=uname_var, state="readonly", width=25)
    username_entry.grid(row=0, column=1, sticky="w")
    refresh_btn = ttk.Button(form_frame, text="↻", width=3, command=refresh_username)
    refresh_btn.grid(row=0, column=2, padx=2)

    # Row 1 - Password
    ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    pwd_entry = ttk.Entry(form_frame, textvariable=pwd_var, show="*", width=25)
    pwd_entry.grid(row=1, column=1, sticky="w")

    # Row 2 - Confirm Password
    ttk.Label(form_frame, text="Confirm Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    cpwd_entry = ttk.Entry(form_frame, textvariable=cpwd_var, show="*", width=25)
    cpwd_entry.grid(row=2, column=1, sticky="w")

    # Row 3 - Show Password checkbox
    show_pwd_check = ttk.Checkbutton(
        form_frame,
        text="Show Password",
        variable=show_password_var,
        command=lambda: toggle_password_visibility()
    )
    show_pwd_check.grid(row=3, column=1, sticky="w", pady=(0, 5))

    def toggle_password_visibility():
        if show_password_var.get():
            pwd_entry.config(show="")
            cpwd_entry.config(show="")
        else:
            pwd_entry.config(show="*")
            cpwd_entry.config(show="*")

    # Row 4 - Branch
    ttk.Label(form_frame, text="Branch:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
    branch_entry = ttk.Entry(form_frame, textvariable=branch_var, width=25)
    branch_entry.grid(row=4, column=1, sticky="w")

    # Row 5 - Corporation Dropdown
    ttk.Label(form_frame, text="Corporation:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
    corporate_options = [
       "ASIAPHIL STAR", "MAJOREVIM", "MEGAWORLD DOMESTIC", "NORTHERN SUNSTAR",
        "SAINT BARBARA PRIME", "SAN RAMON PLATINUM", "SILVERSTAR (J)"
    ]
    corporate_dropdown = ttk.Combobox(
        form_frame,
        textvariable=corporate_var,
        values=corporate_options,
        width=23,
        state="readonly"
    )
    corporate_dropdown.grid(row=5, column=1, sticky="w", pady=5)
    corporate_dropdown.set("Select Corporation")

    # Save Button
    save_btn = ttk.Button(popup, text="Save User", command=lambda: save_user())
    save_btn.pack(pady=15)

    def save_user():
        username = uname_var.get().strip()
        password = pwd_var.get().strip()
        confirm_password = cpwd_var.get().strip()
        branch = branch_var.get().strip()
        corporation = corporate_var.get().strip()

        if not password or not confirm_password or not branch or corporation == "Select Corporation":
            messagebox.showwarning("Incomplete Data", "Please fill in all fields.")
            return
        if password != confirm_password:
            messagebox.showerror("Password Mismatch", "Passwords do not match.")
            return

        try:
            db.collection("Users_db").document().set({
                "username": username,
                "password": password,
                "branch": branch,
                "corporations": corporation
            })
            messagebox.showinfo("Success", f"User {username} added successfully.")
            popup.destroy()
        except Exception as e:
            print(f"Error saving user: {e}")
            messagebox.showerror("Error", "Failed to save user to Firestore.")
