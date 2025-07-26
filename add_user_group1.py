import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Make sure this is at the top
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

def open_add_user_popup_group1(parent):
    popup = tk.Toplevel(parent)
    popup.title("Add User")
    popup.geometry("300x200")
    popup.grab_set()

    form_frame = tk.Frame(popup)
    form_frame.pack(pady=20)

    uname_var = tk.StringVar()

    def refresh_username():
        try:
            new_uname = get_next_username()
            print("Generated username:", new_uname)
            uname_var.set(new_uname)
        except Exception as e:
            print("Error in refresh_username:", e)

    refresh_username()

    uname_label = tk.Label(form_frame, text="Username:", font=("Arial", 11))
    uname_label.grid(row=0, column=0, sticky="e", padx=5)

    uname_entry = tk.Entry(form_frame, textvariable=uname_var, font=("Arial", 11), state="readonly")
    uname_entry.grid(row=0, column=1, pady=5)

    refresh_btn = tk.Button(form_frame, text="↻", command=refresh_username, font=("Arial", 10), width=3)
    refresh_btn.grid(row=0, column=2, padx=2)

    pwd_var = tk.StringVar()
    cpwd_var = tk.StringVar()
    branch_var = tk.StringVar()

    pwd_label = tk.Label(form_frame, text="Password:", font=("Arial", 11))
    pwd_label.grid(row=1, column=0, sticky="e", padx=5)
    pwd_entry = tk.Entry(form_frame, textvariable=pwd_var, font=("Arial", 11), show="*")
    pwd_entry.grid(row=1, column=1, pady=5)

    cpwd_label = tk.Label(form_frame, text="Confirm Password:", font=("Arial", 11))
    cpwd_label.grid(row=2, column=0, sticky="e", padx=5)
    cpwd_entry = tk.Entry(form_frame, textvariable=cpwd_var, font=("Arial", 11), show="*")
    cpwd_entry.grid(row=2, column=1, pady=5)

    branch_label = tk.Label(form_frame, text="Branch:", font=("Arial", 11))
    branch_label.grid(row=3, column=0, sticky="e", padx=5)
    branch_entry = tk.Entry(form_frame, textvariable=branch_var, font=("Arial", 11))
    branch_entry.grid(row=3, column=1, pady=5)
    
    corporate_var = tk.StringVar()
    corporate_options = [
        "ATLANTIC STARGEM", "GALLIUM GRANITE", "GOLD BARS", "GREEN AMBER (J)",
        "KING-ASIA GROUP", "KRYPTON KNIGHT", "MAXI-WEALTH", "METROGOLD STAR",
        "NORTH-WESTERN PACIFIC", "PACIFIC METROSTAR", "PUREGOLD KARAT",
        "SAN SEBASTIAN SILVER", "WORLDCREST", "WORLDGEM"
    ]

    corporate_label = tk.Label(form_frame, text="Corporation:", font=("Arial", 11))
    corporate_label.grid(row=4, column=0, sticky="e", padx=5)

    corporate_dropdown = ttk.Combobox(form_frame, textvariable=corporate_var, values=corporate_options, font=("Arial", 11), state="readonly")
    corporate_dropdown.grid(row=4, column=1, pady=5)
    corporate_dropdown.set("Select Corporation")  # Set default value
    
    
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
            # Save user to Firestore
            db.collection("Users_db").document().set({
                "username": username,
                "password": password,
                "branch": branch,
                "corporations": corporation  # save as a list
            })
            messagebox.showinfo("Success", f"User {username} added successfully.")
            popup.destroy()
        except Exception as e:
            print(f"Error saving user: {e}")
            messagebox.showerror("Error", "Failed to save user to Firestore.")

    save_btn = tk.Button(popup, text="Save User", font=("Arial", 11), bg="#27ae60", fg="white", command=save_user)
    save_btn.pack(pady=10)

