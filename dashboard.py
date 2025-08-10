import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import os
import time
import datetime
import tempfile
from firebase_config import storage, db
from firebase_admin import firestore
from PIL import Image, ImageTk  # For viewing image


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
        files = filedialog.askopenfilenames(filetypes=[("Image Files",
                                                        "*.bmp;*.dib;*.jpeg;*.jpg;*.jpe;*.jfif;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pnm;*.tiff;*.tif;*.ras;*.sgi;*.tga")])
        if not files:
            return

        max_size_bytes = 50 * 1024 * 1024
        oversized_files = []
        valid_files = []

        for file_path in files:
            if os.path.getsize(file_path) <= max_size_bytes:
                valid_files.append(file_path)
            else:
                oversized_files.append(os.path.basename(file_path))

        if not valid_files:
            messagebox.showwarning("All Files Too Large", "All selected files exceed the 50MB size limit.")
            return

        if oversized_files:
            messagebox.showwarning("Some Files Skipped",
                                   f"The following files were skipped for exceeding 50MB:\n\n" + "\n".join(
                                       oversized_files))

        def confirm_upload():
            confirmed_transaction = transaction_var.get()
            confirmed_date = date_var.get()
            uploaded = 0

            confirm_win.destroy()
            progress_label.config(text=f"Uploading 0/{len(valid_files)} images...")
            dash.update_idletasks()
            uploaded_by = name_var.get().strip()
            if not uploaded_by:
                messagebox.showerror("Missing Name", "Please enter your name before uploading.")
                return

            for idx, file_path in enumerate(valid_files, 1):
                try:
                    filename = os.path.basename(file_path)
                    timestamp = str(int(time.time()))
                    branch_folder = branch if branch else "Unknown_Branch"
                    storage_path = f"{branch_folder}/{confirmed_date}_{timestamp}_{filename}"

                    # ✅ NEW: Try Admin SDK upload method first
                    from firebase_config import upload_file_with_admin_sdk, get_download_url_with_fallback, \
                        test_url_accessibility, fix_content_type_after_pyrebase_upload

                    try:
                        print(f"🔄 Trying Admin SDK upload for {filename}")
                        url = upload_file_with_admin_sdk(file_path, storage_path)
                        print(f"✅ Admin SDK upload successful for {filename}")

                    except Exception as admin_error:
                        print(f"⚠️ Admin SDK upload failed: {admin_error}")
                        print(f"🔄 Falling back to Pyrebase upload for {filename}")

                        # Fallback to Pyrebase method
                        upload_result = storage.child(storage_path).put(file_path)
                        print(f"✅ Pyrebase upload completed for {filename}")

                        # Fix content type after Pyrebase upload
                        fix_content_type_after_pyrebase_upload(storage_path, filename)

                        print(f"🔄 Generating download URL for {filename}")
                        url = get_download_url_with_fallback(storage_path)

                    # Test if the URL actually works
                    if test_url_accessibility(url):
                        print(f"✅ Upload successful - URL verified: {filename}")
                    else:
                        print(f"⚠️ Upload successful but URL may not be accessible: {filename}")

                    doc_data = {
                        "branch": branch,
                        "transaction_type": confirmed_transaction,
                        "date": confirmed_date,
                        "uploaded_by": uploaded_by,
                        "image_url": url,
                        "storage_path": storage_path,
                        "filename": filename,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "corporations": corporation,
                    }

                    db.collection("Uploaded_Images").add(doc_data)

                    uploaded += 1
                    progress_label.config(text=f"Uploading {uploaded}/{len(valid_files)} images...")
                    dash.update_idletasks()
                    print(f"✅ Database record created for {filename}")
                    print(f"✅ Final working URL: {url}")

                except Exception as e:
                    print(f"🔥 Upload error for {filename}: {e}")
                    messagebox.showerror("Upload Failed", f"Error uploading {filename}: {str(e)}")

            progress_label.config(text="Upload complete!")
            messagebox.showinfo("Upload Complete", "Images uploaded successfully!")

        def view_image(path):
            img_win = tk.Toplevel(confirm_win)
            img_win.title("Image Viewer")
            img_win.geometry("700x500")
            img_win.grab_set()

            img = Image.open(path)
            img.thumbnail((650, 450))
            img_tk = ImageTk.PhotoImage(img)

            label = tk.Label(img_win, image=img_tk)
            label.image = img_tk
            label.pack(padx=10, pady=10)

        confirm_win = tk.Toplevel(dash)
        confirm_win.title("Confirm Upload")
        confirm_win.geometry("600x450")
        confirm_win.configure(bg="#f5f6fa")
        confirm_win.grab_set()
        confirm_win.geometry(f"+{dash.winfo_rootx() + 100}+{dash.winfo_rooty() + 80}")

        tk.Label(confirm_win, text="📋 Confirm Images to Upload", font=("Poppins", 13, "bold"), bg="#f5f6fa",
                 fg="#2f3640").pack(pady=(10, 5))

        # Show selected transaction type and date
        info_frame = tk.Frame(confirm_win, bg="#f5f6fa")
        info_frame.pack(pady=(0, 10))

        tk.Label(info_frame, text=f"📝 Transaction Type: {transaction_var.get()}", font=("Poppins", 10),
                 bg="#f5f6fa").pack(anchor="w")
        tk.Label(info_frame, text=f"📅 Date: {date_var.get()}", font=("Poppins", 10), bg="#f5f6fa").pack(anchor="w")

        table_frame = tk.Frame(confirm_win)
        table_frame.pack(expand=True, fill="both", padx=10)

        tree = ttk.Treeview(table_frame, columns=("Filename", "View"), show="headings", height=10)
        tree.heading("Filename", text="Filename")
        tree.heading("View", text="Action")
        tree.column("Filename", anchor="center", width=300)
        tree.column("View", anchor="center", width=100)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # Populate rows and add buttons
        for i, path in enumerate(valid_files):
            filename = os.path.basename(path)
            tree.insert("", "end", iid=i, values=(filename, "View"))

        def on_tree_click(event):
            item_id = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if item_id and col == "#2":
                index = int(item_id)
                view_image(valid_files[index])

        tree.bind("<ButtonRelease-1>", on_tree_click)

        btn_frame = tk.Frame(confirm_win, bg="#f5f6fa")
        btn_frame.pack(pady=12)

        tk.Button(btn_frame, text="Cancel", bg="#d63031", fg="white", font=("Poppins", 10, "bold"),
                  width=12, command=confirm_win.destroy).pack(side="left", padx=12)
        tk.Button(btn_frame, text="Confirm Upload", bg="#00b894", fg="white", font=("Poppins", 10, "bold"),
                  width=16, command=confirm_upload).pack(side="right", padx=12)

    def capture_and_upload():
        try:
            import cv2
        except ImportError:
            messagebox.showerror("OpenCV Not Installed", "Please install OpenCV with `pip install opencv-python`.")
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Could not access the camera.")
            return

        messagebox.showinfo("Camera Instructions", "Press SPACE to capture the image. Press ESC to cancel.")

        while True:
            ret, frame = cap.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to capture image.")
                break

            cv2.imshow("Capture Image - Press SPACE to Save", frame)
            key = cv2.waitKey(1)
            if key % 256 == 27:
                break
            elif key % 256 == 32:
                timestamp = int(time.time())
                default_name = f"captured_{timestamp}.jpg"
                temp_path = os.path.join(os.path.expanduser("~"), "Documents", default_name)
                cv2.imwrite(temp_path, frame)

                cap.release()
                cv2.destroyAllWindows()

                def confirm_filename():
                    custom_name = name_entry.get().strip()
                    if not custom_name:
                        messagebox.showerror("Filename Error", "Filename cannot be empty.")
                        return
                    if not custom_name.lower().endswith(".jpg"):
                        custom_name += ".jpg"

                    new_temp_path = os.path.join(os.getcwd(), custom_name)
                    try:
                        os.rename(temp_path, new_temp_path)
                    except Exception as e:
                        messagebox.showerror("Rename Error", f"Could not rename file: {e}")
                        return

                    prompt.destroy()
                    upload_camera_image(new_temp_path)

                prompt = tk.Toplevel(dash)
                prompt.title("Edit Image Filename")
                prompt.geometry("350x150")
                prompt.grab_set()
                prompt.geometry(f"+{dash.winfo_rootx() + 100}+{dash.winfo_rooty() + 80}")

                tk.Label(prompt, text="Enter image filename:", font=("Poppins", 11)).pack(pady=(15, 5))
                name_entry = tk.Entry(prompt, font=("Poppins", 10))
                name_entry.insert(0, default_name)
                name_entry.pack(pady=5, padx=20, fill="x")

                tk.Button(prompt, text="Confirm & Upload", bg="#00b894", fg="white", font=("Poppins", 10, "bold"),
                          command=confirm_filename).pack(pady=10)
                return

        cap.release()
        cv2.destroyAllWindows()

    def upload_camera_image(temp_path):
        confirmed_transaction = transaction_var.get()
        confirmed_date = date_var.get()
        uploaded_by = name_var.get().strip()

        if not uploaded_by:
            messagebox.showerror("Missing Name", "Please enter your name before uploading.")
            os.remove(temp_path)
            return

        try:
            filename = os.path.basename(temp_path)
            timestamp = str(int(time.time()))
            branch_folder = branch if branch else "Unknown_Branch"
            storage_path = f"{branch_folder}/{confirmed_date}_{timestamp}_{filename}"

            # ✅ NEW: Try Admin SDK upload method first
            from firebase_config import upload_file_with_admin_sdk, get_download_url_with_fallback, \
                test_url_accessibility, fix_content_type_after_pyrebase_upload

            try:
                print(f"🔄 Trying Admin SDK upload for camera image {filename}")
                url = upload_file_with_admin_sdk(temp_path, storage_path)
                print(f"✅ Admin SDK camera upload successful")

            except Exception as admin_error:
                print(f"⚠️ Admin SDK camera upload failed: {admin_error}")
                print(f"🔄 Falling back to Pyrebase upload for camera image {filename}")

                # Fallback to Pyrebase method
                upload_result = storage.child(storage_path).put(temp_path)
                print(f"✅ Pyrebase camera upload completed for {filename}")

                # Fix content type after Pyrebase upload
                fix_content_type_after_pyrebase_upload(storage_path, filename)

                print(f"🔄 Generating download URL for camera image {filename}")
                url = get_download_url_with_fallback(storage_path)

            # Test if the URL actually works
            if test_url_accessibility(url):
                print(f"✅ Camera upload successful - URL verified")
            else:
                print(f"⚠️ Camera upload successful but URL may not be accessible")

            doc_data = {
                "branch": branch,
                "transaction_type": confirmed_transaction,
                "date": confirmed_date,
                "uploaded_by": uploaded_by,
                "image_url": url,
                "filename": filename,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "storage_path": storage_path,
                "corporations": corporation,
            }

            db.collection("Uploaded_Images").add(doc_data)

            progress_label.config(text="Camera image uploaded successfully!")
            messagebox.showinfo("Success", "Captured image uploaded successfully.")
            print(f"✅ Camera image database record created")
            print(f"✅ Final working URL: {url}")

        except Exception as e:
            print(f"🔥 Camera upload error: {e}")
            messagebox.showerror("Upload Failed", f"Error uploading captured image: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    VERSION = "v1.0.9"  # Updated version

    dash = tk.Tk()
    dash.title(f"Dashboard - {branch} ({VERSION})")
    dash.geometry("700x550")
    dash.configure(bg="#ecf0f1")
    dash.resizable(False, False)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff", foreground="#2d3436",
                    font=("Poppins", 10))

    header = tk.Frame(dash, bg="#2f3640", height=60)
    header.pack(fill="x")
    tk.Label(header, text="📁  Record Management System", font=("Poppins", 17, "bold"), bg="#2f3640", fg="#ffffff").pack(
        side="left", padx=20, pady=10)
    tk.Label(header, text=f"Branch: {branch}", font=("Poppins", 12), bg="#2f3640", fg="#dcdde1").pack(side="right",
                                                                                                      padx=20)

    card = tk.Frame(dash, bg="#ffffff", bd=0, relief="flat")
    card.place(relx=0.5, rely=0.55, anchor="center", width=420, height=480)

    tk.Label(card, text="Upload Images", font=("Poppins", 15, "bold"), bg="#ffffff", fg="#2f3640").pack(pady=(20, 8))

    tk.Label(card, text="Transaction Type:", font=("Poppins", 11), bg="#ffffff", anchor="w").pack(pady=(5, 0), padx=30,
                                                                                                  fill="x")
    transaction_types = ["Palawan Payout", "Palawan Sendout", "Money Changer Buy", "Money Changer Sell",
                         "Cars & Motors", "Auction Sales", "KYC Individual Records", "KYC Corporate Records",
                         "RIA In", "RIA Out",
                         "Gcash In", "Gcash Out", "i2i In", "i2i Out", "Palawan Pay In", "Palawan Pay Out",
                         "Jewelry New", "Jewelry Renew", "Jewelry Redeem", "Storage New", "Storage Renew",
                         "Storage Redeem","Cars & Motors New", "Cars & Motors Renew", "Cars & Motors Redeem"
                         ]
    transaction_var = tk.StringVar(value=transaction_types[0])
    transaction_dropdown = ttk.Combobox(card, textvariable=transaction_var, values=transaction_types, state="readonly",
                                        font=("Poppins", 10))
    transaction_dropdown.current(0)
    transaction_dropdown.pack(pady=5, padx=30, fill="x")

    tk.Label(card, text="Select Date:", font=("Poppins", 11), bg="#ffffff", anchor="w").pack(pady=(10, 0), padx=30,
                                                                                             fill="x")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_var = tk.StringVar(value=today_str)
    date_picker = DateEntry(card, textvariable=date_var, date_pattern="yyyy-mm-dd", font=("Poppins", 10),
                            state="readonly")
    date_picker.set_date(datetime.date.today())
    date_picker.pack(pady=5, padx=30, fill="x")

    tk.Label(card, text="Uploaded by:", font=("Poppins", 11), bg="#ffffff", anchor="w").pack(pady=(10, 0), padx=30,
                                                                                             fill="x")
    name_var = tk.StringVar()
    name_entry = tk.Entry(card, textvariable=name_var, font=("Poppins", 10))
    name_entry.pack(pady=5, padx=30, fill="x")

    progress_label = tk.Label(card, text="", font=("Poppins", 11), fg="#0984e3", bg="#ffffff")
    progress_label.pack(pady=(8, 5))

    tk.Button(card, text="📤 Select & Upload Images", font=("Poppins", 11, "bold"), bg="#00b894", fg="#ffffff",
              activebackground="#00cec9", activeforeground="#ffffff", width=30, height=2, command=upload_images,
              bd=0, cursor="hand2").pack(pady=(10, 5))

    tk.Button(card, text="📸 Capture & Upload from Camera", font=("Poppins", 11, "bold"), bg="#0984e3", fg="#ffffff",
              activebackground="#74b9ff", activeforeground="#ffffff", width=30, height=2, command=capture_and_upload,
              bd=0, cursor="hand2").pack(pady=(5, 5))

    tk.Button(card, text="Logout", font=("Poppins", 11, "bold"), bg="#d63031", fg="#ffffff",
              activebackground="#e17055", activeforeground="#ffffff", width=30, height=1,
              command=logout, bd=0, cursor="hand2").pack(pady=(5, 10))
    footer = tk.Label(dash, text="Developed by Paolo Somido", font=("Poppins", 9), bg="#ecf0f1", fg="#636e72")
    footer.pack(side="bottom", pady=(0, 5))

    dash.mainloop()