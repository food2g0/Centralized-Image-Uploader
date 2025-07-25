# dashboard.py

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkcalendar import DateEntry  # Make sure to install tkcalendar: pip install tkcalendar
import os
import time
from firebase_config import storage, db
from firebase_admin import firestore

def open_dashboard(user_data):
    def logout():
        dash.destroy()
        try:
            import login_gui
            if hasattr(login_gui, 'open_login_gui'):
                login_gui.open_login_gui()
            elif hasattr(login_gui, 'main'):
                login_gui.main()
            else:
                messagebox.showerror("Error", "Could not open login: No valid entry point found.")
        except Exception as err:
            messagebox.showerror("Error", f"Could not open login: {err}")
    branch = user_data["branch"]

    def upload_images():
        transaction_type = transaction_var.get()
        selected_date = date_var.get()
        if not transaction_type:
            messagebox.showerror("Missing Info", "Please select a transaction type.")
            return
        if not selected_date:
            messagebox.showerror("Missing Info", "Please select a date.")
            return

        files = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not files:
            return

        progress_label.config(text=f"Uploading 0/{len(files)} images...")
        dash.update_idletasks()

        uploaded = 0
        for idx, file_path in enumerate(files, 1):
            try:
                filename = os.path.basename(file_path)
                timestamp = str(int(time.time()))
                storage_path = f"{branch}/{transaction_type}/{selected_date}_{timestamp}_{filename}"

                # Upload to Firebase Storage
                storage.child(storage_path).put(file_path)

                # Get download URL
                url = storage.child(storage_path).get_url(None)

                # Save to Firestore
                db.collection("Uploaded_Images").add({
                    "branch": branch,
                    "transaction_type": transaction_type,
                    "date": selected_date,
                    "image_url": url,
                    "filename": filename,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                uploaded += 1
                progress_label.config(text=f"Uploading {uploaded}/{len(files)} images...")
                dash.update_idletasks()
                print(f"✅ Uploaded {filename}")
            except Exception as e:
                print("🔥 Upload error:", e)
                messagebox.showerror("Upload Failed", f"Error uploading {filename}")

        progress_label.config(text="Upload complete!")
        messagebox.showinfo("Upload Complete", "Images uploaded successfully!")

    # Create new root for dashboard
    dash = tk.Tk()
    dash.title(f"Dashboard - {branch}")
    dash.geometry("480x340")
    dash.resizable(False, False)
    dash.configure(bg="#f5f6fa")

    # Header
    header = tk.Frame(dash, bg="#273c75", height=60)
    header.pack(fill="x")
    tk.Label(header, text="Image Uploader", font=("Poppins", 16, "bold"), bg="#273c75", fg="#fff").pack(side="left", padx=20, pady=10)
    tk.Label(header, text=f"Branch: {branch}", font=("Poppins", 12), bg="#273c75", fg="#dff9fb").pack(side="right", padx=20)

    # Card-like main area
    card = tk.Frame(dash, bg="#fff", bd=2, relief="groove")
    card.place(relx=0.5, rely=0.55, anchor="center", width=400, height=260)

    tk.Label(card, text="Upload Images", font=("Poppins", 14, "bold"), bg="#fff", fg="#192a56").pack(pady=(18, 8))

    # Transaction type dropdown
    tk.Label(card, text="Transaction Type:", font=("Poppins", 11), bg="#fff").pack()
    transaction_var = tk.StringVar()
    transaction_types = ["Deposit", "Withdrawal", "Transfer", "Other"]
    transaction_dropdown = ttk.Combobox(card, textvariable=transaction_var, values=transaction_types, state="readonly", font=("Poppins", 10))
    transaction_dropdown.pack(pady=2)

    # Date picker
    tk.Label(card, text="Select Date:", font=("Poppins", 11), bg="#fff").pack()
    date_var = tk.StringVar()
    date_picker = DateEntry(card, textvariable=date_var, date_pattern="yyyy-mm-dd", font=("Poppins", 10))
    date_picker.pack(pady=2)

    progress_label = tk.Label(card, text="", font=("Poppins", 11), fg="#0097e6", bg="#fff")
    progress_label.pack(pady=2)

    upload_btn = tk.Button(card, text="Select & Upload Images", font=("Poppins", 11), bg="#00b894", fg="#fff", activebackground="#00cec9", activeforeground="#fff", width=22, height=2, command=upload_images, bd=0, cursor="hand2")
    upload_btn.pack(pady=10)

    logout_btn = tk.Button(card, text="Logout", font=("Poppins", 11), bg="#d63031", fg="#fff", activebackground="#e17055", activeforeground="#fff", width=22, height=1, command=logout, bd=0, cursor="hand2")
    logout_btn.pack(pady=5)

    dash.mainloop()
