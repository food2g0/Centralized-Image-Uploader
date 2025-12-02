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

            # ✅ NEW: Get Palawan reference number if applicable
            palawan_ref = ""
            if hasattr(palawan_field_frame, 'palawan_entry'):
                palawan_ref = palawan_field_frame.palawan_entry.get().strip()

            # Show progress bar and initialize
            progress_bar.pack(pady=(0, 10))
            progress_bar['maximum'] = len(valid_files)
            progress_bar['value'] = 0
            progress_label.config(text=f"Uploading 0/{len(valid_files)} images...")
            canvas.update_idletasks()

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

                    # ✅ UPDATED: Add palawan_reference to doc_data
                    doc_data = {
                        "branch": branch,
                        "transaction_type": confirmed_transaction,
                        "date": confirmed_date,
                        "uploaded_by": uploaded_by,
                        "image_url": url,
                        "storage_path": storage_path,
                        "filename": filename,
                        "timestamp": datetime.datetime.now(),
                        "corporations": corporation,
                    }

                    # Only add palawan_reference if it's not empty
                    if palawan_ref:
                        doc_data["palawan_reference"] = palawan_ref

                    db.collection("Uploaded_Images").add(doc_data)
                    uploaded += 1
                    progress_label.config(text=f"Uploading {uploaded}/{len(valid_files)} images...")
                    canvas.update_idletasks()
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
            
            # Responsive image preview sizing
            preview_width = max(600, min(int(dash.winfo_width() * 0.6), 900))
            preview_height = max(500, min(int(dash.winfo_height() * 0.7), 750))
            
            # Center preview window
            x_offset = dash.winfo_rootx() + (dash.winfo_width() - preview_width) // 2
            y_offset = dash.winfo_rooty() + (dash.winfo_height() - preview_height) // 2
            
            img_win.geometry(f"{preview_width}x{preview_height}+{x_offset}+{y_offset}")
            img_win.configure(bg="#f8f9fa")
            img_win.grab_set()
            img_win.minsize(400, 350)

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
                # Scale image based on available container size
                max_img_width = preview_width - 100
                max_img_height = preview_height - 200
                img.thumbnail((max_img_width, max_img_height))
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
        
        # Responsive popup sizing
        popup_width = max(600, min(int(dash.winfo_width() * 0.7), 800))
        popup_height = max(500, min(int(dash.winfo_height() * 0.75), 700))
        
        # Center popup relative to main window
        x_offset = dash.winfo_rootx() + (dash.winfo_width() - popup_width) // 2
        y_offset = dash.winfo_rooty() + (dash.winfo_height() - popup_height) // 2
        
        confirm_win.geometry(f"{popup_width}x{popup_height}+{x_offset}+{y_offset}")
        confirm_win.configure(bg="#f8f9fa")
        confirm_win.grab_set()
        confirm_win.minsize(500, 400)

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
                
                # Responsive filename prompt
                prompt_width = max(350, min(int(dash.winfo_width() * 0.4), 500))
                prompt_height = 200
                
                x_offset = dash.winfo_rootx() + (dash.winfo_width() - prompt_width) // 2
                y_offset = dash.winfo_rooty() + (dash.winfo_height() - prompt_height) // 2
                
                prompt.geometry(f"{prompt_width}x{prompt_height}+{x_offset}+{y_offset}")
                prompt.configure(bg="#f8f9fa")
                prompt.grab_set()
                prompt.minsize(300, 180)

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

        # ✅ NEW: Get Palawan reference number if applicable
        palawan_ref = ""
        if hasattr(palawan_field_frame, 'palawan_entry'):
            palawan_ref = palawan_field_frame.palawan_entry.get().strip()

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

            # ✅ UPDATED: Add palawan_reference to doc_data
            doc_data = {
                "branch": branch,
                "transaction_type": confirmed_transaction,
                "date": confirmed_date,
                "uploaded_by": uploaded_by,
                "image_url": url,
                "filename": filename,
                "timestamp": datetime.datetime.now(),
                "storage_path": storage_path,
                "corporations": corporation,
            }

            # Only add palawan_reference if it's not empty
            if palawan_ref:
                doc_data["palawan_reference"] = palawan_ref

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

    VERSION = "v1.1.3"

    dash = tk.Tk()
    dash.title(f"Record Management System - {branch} ({VERSION})") 
    screen_width = dash.winfo_screenwidth() 
    screen_height = dash.winfo_screenheight() 
    window_width = max(900, min(int(screen_width * 0.8), 1400))
    window_height = max(700, min(int(screen_height * 0.85), 900)) 
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    dash.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    dash.configure(bg="#f8f9fa")
    dash.resizable(True, True)
    dash.minsize(800, 600)  # Set minimum window size

    
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

    # ✅ SCROLLABLE MAIN CONTENT AREA
    main_container = tk.Frame(dash, bg="#f8f9fa")
    main_container.pack(expand=True, fill="both", padx=0, pady=0)

    # Create canvas with scrollbar
    canvas = tk.Canvas(main_container, bg="#f8f9fa", highlightthickness=0, relief="flat")
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

 
    scrollable_frame = tk.Frame(canvas, bg="#f8f9fa")
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_linux_scroll(event):                              
        if event.num == 5:
            canvas.yview_scroll(3, "units")
        elif event.num == 4:
            canvas.yview_scroll(-3, "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)
    canvas.bind_all("<Button-4>", on_linux_scroll)
    canvas.bind_all("<Button-5>", on_linux_scroll)

  
    def on_frame_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        canvas_width = canvas.winfo_width()
        if canvas_width > 1:
            canvas.itemconfig(canvas_window, width=canvas_width)

    scrollable_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_frame_configure)

    # Upload form card (inside scrollable frame)
    form_card = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    form_card.pack(fill="both", expand=True, padx=30, pady=30)

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

    transaction_types = ["Money Changer Buy", "Palawan Sendout","Palawan Payout",  "Money Changer Sell",
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
    
    palawan_field_frame = tk.Frame(fields_frame, bg="white")
    palawan_field_frame.pack(fill="x", pady=(0, 20))

    def on_transaction_change(*args):
        # Clear previous widgets in palawan frame
        for widget in palawan_field_frame.winfo_children():
            widget.destroy()

        selected_transaction = transaction_var.get()
        
        # Show field only if Palawan Payout or Palawan Sendout is selected
        if selected_transaction in ["Palawan Payout", "Palawan Sendout"]:
            tk.Label(palawan_field_frame, text="Lotes", font=("Segoe UI", 12, "bold"),
                     bg="white", fg="#374151").pack(anchor="w")
           

            palawan_entry = tk.Entry(palawan_field_frame, font=("Segoe UI", 11),
                                     relief="solid", bd=1)
            palawan_entry.pack(fill="x", ipady=8)

            # Store reference to entry for later use
            palawan_field_frame.palawan_entry = palawan_entry

    # Bind the transaction dropdown to trigger the function
    transaction_var.trace("w", on_transaction_change)

    # Date field - COMPLETE REWRITE: Custom solution to avoid DateEntry issues
    date_frame = tk.Frame(fields_frame, bg="white")
    date_frame.pack(fill="x", pady=(0, 20))

    tk.Label(date_frame, text="Transaction Date", font=("Segoe UI", 12, "bold"),
             bg="white", fg="#374151").pack(anchor="w")
    tk.Label(date_frame, text="Date when the transaction occurred",
             font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w", pady=(2, 8))

    # Create container for date input and button
    date_input_frame = tk.Frame(date_frame, bg="white")
    date_input_frame.pack(fill="x")

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_var = tk.StringVar(value=today_str)

    # ✅ BULLETPROOF SOLUTION: Custom date entry with separate calendar popup
    date_entry = tk.Entry(date_input_frame,
                          textvariable=date_var,
                          font=("Segoe UI", 11),
                          state="readonly",
                          relief="solid",
                          bd=1,
                          bg="#f9fafb",
                          fg="#374151",
                          cursor="hand2")
    date_entry.pack(side="left", fill="x", expand=True, ipady=8)

    # Calendar button
    calendar_btn = tk.Button(date_input_frame,
                             text="📅",
                             font=("Segoe UI", 12),
                             bg="#10b981",
                             fg="white",
                             relief="flat",
                             bd=1,
                             padx=8,
                             pady=8,
                             cursor="hand2",
                             activebackground="#059669")
    calendar_btn.pack(side="right", padx=(5, 0))

    def open_calendar_popup():
        """Open a reliable calendar popup window"""
        # Create popup window
        cal_popup = tk.Toplevel(dash)
        cal_popup.title("Select Date")
        cal_popup.geometry("300x300")
        cal_popup.configure(bg="#f8f9fa")
        cal_popup.resizable(False, False)
        cal_popup.grab_set()  # Make it modal

        # Center the popup
        cal_popup.geometry(f"+{dash.winfo_rootx() + 200}+{dash.winfo_rooty() + 200}")

        # Header
        header_frame = tk.Frame(cal_popup, bg="#1e293b", height=40)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="Select Transaction Date",
                 font=("Segoe UI", 12, "bold"),
                 bg="#1e293b", fg="white").pack(pady=10)

        # Calendar widget (this time without readonly issues)
        from tkcalendar import Calendar

        # Parse current date
        try:
            current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d").date()
        except:
            current_date = datetime.date.today()

        cal = Calendar(cal_popup,
                       selectmode='day',
                       date_pattern='yyyy-mm-dd',
                       font=("Segoe UI", 10),
                       selectbackground="#10b981",
                       selectforeground="white",
                       normalbackground="white",
                       normalforeground="black",
                       weekendbackground="#f1f5f9",
                       weekendforeground="black",
                       othermonthforeground="#6b7280",
                       othermonthbackground="white",
                       bordercolor="#e5e7eb",
                       headersbackground="#10b981",
                       headersforeground="white",
                       showweeknumbers=False)

        cal.selection_set(current_date)
        cal.pack(expand=True, fill="both", padx=20, pady=20)

        # Buttons frame
        btn_frame = tk.Frame(cal_popup, bg="#f8f9fa")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def select_date():
            selected_date = cal.selection_get()
            date_var.set(selected_date.strftime("%Y-%m-%d"))
            cal_popup.destroy()

        def cancel_selection():
            cal_popup.destroy()

        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                               font=("Segoe UI", 10, "bold"),
                               bg="#6b7280", fg="white",
                               relief="flat", padx=20, pady=8,
                               cursor="hand2",
                               command=cancel_selection)
        cancel_btn.pack(side="left")

        # Select button
        select_btn = tk.Button(btn_frame, text="Select Date",
                               font=("Segoe UI", 10, "bold"),
                               bg="#10b981", fg="white",
                               relief="flat", padx=20, pady=8,
                               cursor="hand2",
                               command=select_date)
        select_btn.pack(side="right")

        # Double-click to select
        cal.bind("<<CalendarSelected>>", lambda e: select_date())

    # Bind calendar opening to both entry and button
    calendar_btn.configure(command=open_calendar_popup)
    date_entry.bind('<Button-1>', lambda e: open_calendar_popup())
    date_entry.bind('<Double-Button-1>', lambda e: open_calendar_popup())
    date_entry.bind('<Return>', lambda e: open_calendar_popup())
    date_entry.bind('<space>', lambda e: open_calendar_popup())

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