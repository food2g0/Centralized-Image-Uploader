import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import os
import time
import datetime
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
    corporation = user_data.get("corporations", "Unknown Corporation")

    def upload_images():
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not files:
            return

        max_size_bytes = 5 * 1024 * 1024  # 5MB

        oversized_files = []
        valid_files = []
        for file_path in files:
            if os.path.getsize(file_path) <= max_size_bytes:
                valid_files.append(file_path)
            else:
                oversized_files.append(os.path.basename(file_path))

        if not valid_files:
            messagebox.showwarning("All Files Too Large", "All selected files exceed the 5MB size limit.")
            return

        if oversized_files:
            messagebox.showwarning("Some Files Skipped", f"The following files were skipped for exceeding 5MB:\n\n" + "\n".join(oversized_files))

        def confirm_upload():
            confirmed_transaction = transaction_var.get()
            confirmed_date = date_var.get()
            uploaded = 0

            confirm_win.destroy()
            progress_label.config(text=f"Uploading 0/{len(valid_files)} images...")
            dash.update_idletasks()

            for idx, file_path in enumerate(valid_files, 1):
                try:
                    filename = os.path.basename(file_path)
                    timestamp = str(int(time.time()))
                    branch_folder = branch if branch else "Unknown_Branch"
                    storage_path = f"{branch_folder}/{confirmed_date}_{timestamp}_{filename}"

                    storage.child(storage_path).put(file_path)
                    url = storage.child(storage_path).get_url(None)

                    doc_data = {
                        "branch": branch,
                        "transaction_type": confirmed_transaction,
                        "date": confirmed_date,
                        "image_url": url,
                        "filename": filename,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "corporations": corporation,
                    }

                    db.collection("Uploaded_Images").add(doc_data)

                    uploaded += 1
                    progress_label.config(text=f"Uploading {uploaded}/{len(valid_files)} images...")
                    dash.update_idletasks()
                    print(f"✅ Uploaded {filename}")
                except Exception as e:
                    print("🔥 Upload error:", e)
                    messagebox.showerror("Upload Failed", f"Error uploading {filename}")

            progress_label.config(text="Upload complete!")
            messagebox.showinfo("Upload Complete", "Images uploaded successfully!")

        confirm_win = tk.Toplevel(dash)
        confirm_win.title("Confirm Upload")
        confirm_win.geometry("540x400")
        confirm_win.configure(bg="#f5f6fa")
        confirm_win.grab_set()
        confirm_win.geometry(f"+{dash.winfo_rootx()+100}+{dash.winfo_rooty()+80}")

        tk.Label(confirm_win, text="📋 Confirm Images to Upload", font=("Poppins", 13, "bold"), bg="#f5f6fa", fg="#2f3640").pack(pady=10)

        table_frame = tk.Frame(confirm_win)
        table_frame.pack(expand=True, fill="both", padx=10)

        cols = ("Filename", "Transaction Type", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=160)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        current_transaction = transaction_var.get()
        current_date = date_var.get()
        for file in valid_files:
            filename = os.path.basename(file)
            tree.insert("", "end", values=(filename, current_transaction, current_date))

        btn_frame = tk.Frame(confirm_win, bg="#f5f6fa")
        btn_frame.pack(pady=12)

        tk.Button(btn_frame, text="Cancel", bg="#d63031", fg="white", font=("Poppins", 10, "bold"), width=12, command=confirm_win.destroy).pack(side="left", padx=12)
        tk.Button(btn_frame, text="Confirm Upload", bg="#00b894", fg="white", font=("Poppins", 10, "bold"), width=16, command=confirm_upload).pack(side="right", padx=12)

    dash = tk.Tk()
    dash.title(f"Dashboard - {branch}")
    dash.geometry("700x550")
    dash.configure(bg="#ecf0f1")
    dash.resizable(False, False)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff", foreground="#2d3436", font=("Poppins", 10))

    header = tk.Frame(dash, bg="#2f3640", height=60)
    header.pack(fill="x")
    tk.Label(header, text="📁  Record Management System", font=("Poppins", 17, "bold"), bg="#2f3640", fg="#ffffff").pack(side="left", padx=20, pady=10)
    tk.Label(header, text=f"Branch: {branch}", font=("Poppins", 12), bg="#2f3640", fg="#dcdde1").pack(side="right", padx=20)

    card = tk.Frame(dash, bg="#ffffff", bd=0, relief="flat")
    card.place(relx=0.5, rely=0.55, anchor="center", width=420, height=390)

    tk.Label(card, text="Upload Images", font=("Poppins", 15, "bold"), bg="#ffffff", fg="#2f3640").pack(pady=(20, 8))

    tk.Label(card, text="Transaction Type:", font=("Poppins", 11), bg="#ffffff", anchor="w").pack(pady=(5, 0), padx=30, fill="x")
    transaction_types = ["Palawan Payout", "Palawan Sendout", "Money Changer", "KYC Records"]
    transaction_var = tk.StringVar(value=transaction_types[0])
    transaction_dropdown = ttk.Combobox(card, textvariable=transaction_var, values=transaction_types, state="readonly", font=("Poppins", 10))
    transaction_dropdown.current(0)
    transaction_dropdown.pack(pady=5, padx=30, fill="x")

    tk.Label(card, text="Select Date:", font=("Poppins", 11), bg="#ffffff", anchor="w").pack(pady=(10, 0), padx=30, fill="x")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_var = tk.StringVar(value=today_str)
    date_picker = DateEntry(card, textvariable=date_var, date_pattern="yyyy-mm-dd", font=("Poppins", 10))
    date_picker.set_date(datetime.date.today())
    date_picker.pack(pady=5, padx=30, fill="x")

    progress_label = tk.Label(card, text="", font=("Poppins", 11), fg="#0984e3", bg="#ffffff")
    progress_label.pack(pady=(8, 5))

    tk.Button(card, text="📤 Select & Upload Images", font=("Poppins", 11, "bold"), bg="#00b894", fg="#ffffff", activebackground="#00cec9", activeforeground="#ffffff", width=30, height=2, command=upload_images, bd=0, cursor="hand2").pack(pady=(10, 5))

    tk.Button(card, text="Logout", font=("Poppins", 11, "bold"), bg="#d63031", fg="#ffffff", activebackground="#e17055", activeforeground="#ffffff", width=30, height=1, command=logout, bd=0, cursor="hand2").pack(pady=(5, 10))

    dash.mainloop()
