import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import os
import time
import datetime
from firebase_config import storage, db
from PIL import Image, ImageTk  # For viewing image


def open_dashboard(user_data):


    branch = user_data["branch"]
    corporation = user_data.get("corporations", "Unknown Corporation")

    def upload_images():
        files = filedialog.askopenfilenames(filetypes=[("Image Files",
                                                        "*.bmp;*.dib;*.jpeg;*.jpg;*.jpe;*.jfif;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pnm;*.tiff;*.tif;*.ras;*.sgi;*.tga;*.docx")])
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

            # Show progress bar and initialize
            progress_bar.pack(pady=(0, 10))
            progress_bar['maximum'] = len(valid_files)
            progress_bar['value'] = 0
            progress_label.config(text=f"Uploading 0/{len(valid_files)} images...")
            dash.update_idletasks()

            uploaded_by = name_var.get().strip()
            if not uploaded_by:
                messagebox.showerror("Missing Name", "Please enter your name before uploading.")
                progress_bar.pack_forget()
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
                        "timestamp": datetime.datetime.now(),  # ✅ FIXED: Using user's current local time
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
            img_win.title("Image Preview")
            img_win.geometry("750x650")
            img_win.configure(bg="#f8f9fa")
            img_win.grab_set()

            # Header
            header_frame = tk.Frame(img_win, bg="#1e293b", height=50)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)

            tk.Label(header_frame, text="Image Preview", font=("Segoe UI", 14, "bold"),
                     bg="#1e293b", fg="white").pack(side="left", padx=20, pady=10)

            # Image container
            img_container = tk.Frame(img_win, bg="white", relief="solid", bd=1)
            img_container.pack(expand=True, fill="both", padx=20, pady=20)

            try:
                img = Image.open(path)
                img.thumbnail((700, 450))
                img_tk = ImageTk.PhotoImage(img)

                label = tk.Label(img_container, image=img_tk, bg="white")
                label.image = img_tk
                label.pack(expand=True, pady=20)
            except Exception as e:
                tk.Label(img_container, text=f"Cannot display image: {e}",
                         font=("Segoe UI", 11), fg="#ef4444", bg="white").pack(expand=True)

            # Close button
            btn_frame = tk.Frame(img_win, bg="#f8f9fa")
            btn_frame.pack(fill="x", padx=20, pady=(0, 20))

            close_btn = tk.Button(btn_frame, text="Close", font=("Segoe UI", 10, "bold"),
                                  bg="#6b7280", fg="white", activebackground="#4b5563",
                                  relief="flat", padx=30, pady=8, cursor="hand2",
                                  command=img_win.destroy)
            close_btn.pack(side="right")

        confirm_win = tk.Toplevel(dash)
        confirm_win.title("Upload Confirmation")
        confirm_win.geometry("700x600")
        confirm_win.configure(bg="#f8f9fa")
        confirm_win.grab_set()
        confirm_win.geometry(f"+{dash.winfo_rootx() + 50}+{dash.winfo_rooty() + 50}")

        # Header
        header_frame = tk.Frame(confirm_win, bg="#1e293b", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="Upload Confirmation", font=("Segoe UI", 16, "bold"),
                 bg="#1e293b", fg="white").pack(side="left", padx=30, pady=15)

        # Info section
        info_section = tk.Frame(confirm_win, bg="white", relief="solid", bd=1)
        info_section.pack(fill="x", padx=20, pady=(20, 10))

        info_inner = tk.Frame(info_section, bg="white")
        info_inner.pack(fill="x", padx=20, pady=15)

        tk.Label(info_inner, text="Upload Details", font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#1f2937").pack(anchor="w")

        details_frame = tk.Frame(info_inner, bg="white")
        details_frame.pack(fill="x", pady=(8, 0))

        tk.Label(details_frame, text=f"Transaction Type: {transaction_var.get()}",
                 font=("Segoe UI", 10), bg="white", fg="#4b5563").pack(anchor="w")
        tk.Label(details_frame, text=f"Date: {date_var.get()}",
                 font=("Segoe UI", 10), bg="white", fg="#4b5563").pack(anchor="w")

        # Files section
        files_section = tk.Frame(confirm_win, bg="white", relief="solid", bd=1)
        files_section.pack(expand=True, fill="both", padx=20, pady=(0, 10))

        files_header = tk.Frame(files_section, bg="#f1f5f9")
        files_header.pack(fill="x")
        tk.Label(files_header, text="Selected Files", font=("Segoe UI", 12, "bold"),
                 bg="#f1f5f9", fg="#1f2937").pack(side="left", padx=20, pady=10)

        table_frame = tk.Frame(files_section, bg="white")
        table_frame.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        # Configure treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        fieldbackground="white",
                        background="white",
                        foreground="#374151",
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#e5e7eb",
                        foreground="#111827",
                        font=("Segoe UI", 10, "bold"))

        tree = ttk.Treeview(table_frame, columns=("Filename", "View"), show="headings", height=8)
        tree.heading("Filename", text="Filename")
        tree.heading("View", text="Action")
        tree.column("Filename", anchor="w", width=400)
        tree.column("View", anchor="center", width=80)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # Populate rows
        for i, path in enumerate(valid_files):
            filename = os.path.basename(path)
            tree.insert("", "end", iid=i, values=(filename, "👁 View"))

        def on_tree_click(event):
            item_id = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if item_id and col == "#2":
                index = int(item_id)
                view_image(valid_files[index])

        tree.bind("<ButtonRelease-1>", on_tree_click)

        # Buttons
        btn_frame = tk.Frame(confirm_win, bg="#f8f9fa")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11, "bold"),
                               bg="#ef4444", fg="white", activebackground="#dc2626",
                               relief="flat", padx=25, pady=10, cursor="hand2",
                               command=confirm_win.destroy)
        cancel_btn.pack(side="left")

        upload_btn = tk.Button(btn_frame, text="Confirm Upload", font=("Segoe UI", 11, "bold"),
                               bg="#10b981", fg="white", activebackground="#059669",
                               relief="flat", padx=25, pady=10, cursor="hand2",
                               command=confirm_upload)
        upload_btn.pack(side="right")

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
                prompt.title("Edit Filename")
                prompt.geometry("400x200")
                prompt.configure(bg="#f8f9fa")
                prompt.grab_set()
                prompt.geometry(f"+{dash.winfo_rootx() + 150}+{dash.winfo_rooty() + 150}")

                # Header
                header_frame = tk.Frame(prompt, bg="#1e293b", height=50)
                header_frame.pack(fill="x")
                header_frame.pack_propagate(False)

                tk.Label(header_frame, text="Edit Filename", font=("Segoe UI", 12, "bold"),
                         bg="#1e293b", fg="white").pack(side="left", padx=20, pady=12)

                # Content
                content_frame = tk.Frame(prompt, bg="white", relief="solid", bd=1)
                content_frame.pack(expand=True, fill="both", padx=20, pady=20)

                tk.Label(content_frame, text="Enter image filename:", font=("Segoe UI", 11),
                         bg="white", fg="#374151").pack(pady=(20, 5))

                name_entry = tk.Entry(content_frame, font=("Segoe UI", 11), relief="solid", bd=1,
                                      bg="#f9fafb")
                name_entry.insert(0, default_name)
                name_entry.pack(pady=5, padx=30, fill="x")

                btn_frame = tk.Frame(content_frame, bg="white")
                btn_frame.pack(fill="x", padx=30, pady=20)

                tk.Button(btn_frame, text="Confirm & Upload", font=("Segoe UI", 10, "bold"),
                          bg="#10b981", fg="white", activebackground="#059669",
                          relief="flat", padx=20, pady=8, cursor="hand2",
                          command=confirm_filename).pack()
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
                "timestamp": datetime.datetime.now(),  # ✅ FIXED: Using user's current local time
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

    VERSION = "v1.1.0"

    # Main window
    dash = tk.Tk()
    dash.title(f"Record Management System - {branch} ({VERSION})")
    dash.geometry("700x900")
    dash.configure(bg="#f8f9fa")
    dash.resizable(False, False)

    # Configure global styles
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground="white",
                    background="white",
                    foreground="#374151",
                    font=("Segoe UI", 11),
                    relief="solid",
                    borderwidth=1)

    # Header
    header = tk.Frame(dash, bg="#1e293b", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    header_left = tk.Frame(header, bg="#1e293b")
    header_left.pack(side="left", fill="both", expand=True, padx=30, pady=20)

    tk.Label(header_left, text="Record Management System",
             font=("Segoe UI", 20, "bold"), bg="#1e293b", fg="white").pack(anchor="w")
    tk.Label(header_left, text="Professional Record Management Solution",
             font=("Segoe UI", 11), bg="#1e293b", fg="#94a3b8").pack(anchor="w", pady=(2, 0))

    header_right = tk.Frame(header, bg="#1e293b")
    header_right.pack(side="right", padx=30, pady=20)

    tk.Label(header_right, text=f"Branch: {branch}",
             font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="#e2e8f0").pack(anchor="e")
    tk.Label(header_right, text=f"Corporation: {corporation}",
             font=("Segoe UI", 10), bg="#1e293b", fg="#94a3b8").pack(anchor="e")

    # Main content area
    main_content = tk.Frame(dash, bg="#f8f9fa")
    main_content.pack(expand=True, fill="both", padx=30, pady=30)

    # Upload form card
    form_card = tk.Frame(main_content, bg="white", relief="solid", bd=1)
    form_card.pack(fill="both", expand=True)

    # Form header
    form_header = tk.Frame(form_card, bg="#f1f5f9")
    form_header.pack(fill="x")

    tk.Label(form_header, text="Upload Documents", font=("Segoe UI", 16, "bold"),
             bg="#f1f5f9", fg="#1f2937").pack(side="left", padx=30, pady=15)

    # Form body
    form_body = tk.Frame(form_card, bg="white")
    form_body.pack(fill="both", expand=True, padx=30, pady=30)

    # Form fields container
    fields_frame = tk.Frame(form_body, bg="white")
    fields_frame.pack(fill="x")

    # Transaction type field
    transaction_frame = tk.Frame(fields_frame, bg="white")
    transaction_frame.pack(fill="x", pady=(0, 20))

    tk.Label(transaction_frame, text="Transaction Type", font=("Segoe UI", 12, "bold"),
             bg="white", fg="#374151").pack(anchor="w")
    tk.Label(transaction_frame, text="Select the type of transaction for these documents",
             font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w", pady=(2, 8))

    transaction_types = ["Palawan Payout", "Palawan Sendout", "Money Changer Buy", "Money Changer Sell",
                         "Cars & Motors", "Auction Sales", "KYC Individual Records", "KYC Corporate Records",
                         "RIA In", "RIA Out",
                         "Gcash In", "Gcash Out", "i2i In", "i2i Out", "Palawan Pay In", "Palawan Pay Out",
                         "Jewelry New", "Jewelry Renew", "Jewelry Redeem", "Storage New", "Storage Renew",
                         "Storage Redeem", "Cars & Motors New", "Cars & Motors Renew", "Cars & Motors Redeem"
                         ]
    transaction_var = tk.StringVar(value=transaction_types[0])
    transaction_dropdown = ttk.Combobox(transaction_frame, textvariable=transaction_var,
                                        values=transaction_types, state="readonly",
                                        font=("Segoe UI", 11), height=10)
    transaction_dropdown.current(0)
    transaction_dropdown.pack(fill="x")

    # Date field
    date_frame = tk.Frame(fields_frame, bg="white")
    date_frame.pack(fill="x", pady=(0, 20))

    tk.Label(date_frame, text="Transaction Date", font=("Segoe UI", 12, "bold"),
             bg="white", fg="#374151").pack(anchor="w")
    tk.Label(date_frame, text="Date when the transaction occurred",
             font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w", pady=(2, 8))

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_var = tk.StringVar(value=today_str)
    date_picker = DateEntry(date_frame, textvariable=date_var, date_pattern="yyyy-mm-dd",
                            font=("Segoe UI", 11), state="readonly",
                            background="#10b981", foreground="white",
                            borderwidth=1, relief="solid")
    date_picker.set_date(datetime.date.today())
    date_picker.pack(fill="x")

    # Name field
    name_frame = tk.Frame(fields_frame, bg="white")
    name_frame.pack(fill="x", pady=(0, 30))

    tk.Label(name_frame, text="Uploaded By", font=("Segoe UI", 12, "bold"),
             bg="white", fg="#374151").pack(anchor="w")
    tk.Label(name_frame, text="Enter your full name for record keeping",
             font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w", pady=(2, 8))

    name_var = tk.StringVar()
    name_entry = tk.Entry(name_frame, textvariable=name_var, font=("Segoe UI", 11),
                          relief="solid", bd=1, bg="#f9fafb", fg="#374151")
    name_entry.pack(fill="x", ipady=8)

    # Progress section
    progress_frame = tk.Frame(form_body, bg="white")
    progress_frame.pack(fill="x", pady=(10, 0))

    progress_label = tk.Label(progress_frame, text="", font=("Segoe UI", 11, "bold"),
                              fg="#10b981", bg="white")
    progress_label.pack(pady=(0, 5))

    # Progress bar (initially hidden)
    progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)

    # Action buttons
    buttons_frame = tk.Frame(form_body, bg="white")
    buttons_frame.pack(fill="x", pady=(20, 0))

    upload_btn = tk.Button(buttons_frame, text="📤  Select & Upload Images",
                           font=("Segoe UI", 12, "bold"), bg="#10b981", fg="white",
                           activebackground="#059669", relief="flat", cursor="hand2",
                           padx=30, pady=12, command=upload_images)
    upload_btn.pack(fill="x", pady=(0, 10))

    camera_btn = tk.Button(buttons_frame, text="📸  Capture from Camera",
                           font=("Segoe UI", 12, "bold"), bg="#3b82f6", fg="white",
                           activebackground="#2563eb", relief="flat", cursor="hand2",
                           padx=30, pady=12, command=capture_and_upload)
    camera_btn.pack(fill="x", pady=(0, 10))


    # Footer
    footer = tk.Frame(dash, bg="#f8f9fa", height=40)
    footer.pack(fill="x")
    footer.pack_propagate(False)

    tk.Label(footer, text="© 2025 Developed by Paolo Somido ",
             font=("Segoe UI", 9), bg="#f8f9fa", fg="#6b7280").pack(pady=10)

    dash.mainloop()