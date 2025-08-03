def open_admin_dashboard_group3(admin_data):
    import tkinter as tk
    from tkinter import messagebox, filedialog
    from firebase_config import db, bucket
    from PIL import Image, ImageTk
    import requests
    from add_user import open_add_user_popup_group3
    from io import BytesIO
    from threading import Thread
    import datetime
    from itertools import islice

    admin = tk.Tk()  
    admin.title("Admin Dashboard")
    admin.geometry("1024x720")

    sidebar = tk.Frame(admin, width=220, bg="#2c3e50", height=800, relief="raised")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    hamburger_btn = tk.Button(admin, text="☰", font=("Arial", 18), bg="#34495e", fg="white", bd=0, state="disabled")
    hamburger_btn.place(x=5, y=5, width=40, height=40)

    main_frame = tk.Frame(admin, bg="#ecf0f1")
    main_frame.pack(side="left", fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="Record Management System", font=("Arial", 16), bg="#f1ecec").pack(pady=10)

    content_frame = tk.Frame(main_frame, bg="#ecf0f1")
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Left - Image Viewer
    viewer_frame = tk.Frame(content_frame, bg="#ecf0f1", width=600)
    viewer_frame.pack(side="left", fill=tk.BOTH, expand=True)
    viewer_frame.pack_propagate(False)

    # Right - Report Viewer
    report_frame = tk.Frame(content_frame, bg="#f9f9f9", width=400, relief="sunken", bd=1)
    report_frame.pack(side="right", fill=tk.Y)
    report_frame.pack_propagate(False)

    canvas = tk.Canvas(viewer_frame, bg="#ecf0f1", highlightthickness=0)
    scrollbar = tk.Scrollbar(viewer_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scroll_frame = tk.Frame(canvas, bg="#ecf0f1")
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(scroll_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)
    


    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    image_refs = []

    group3_corporations = {
        "ALEXITE (J)", "GOLDSTAR ATLANTIC", "GOOD QUALITY ASSURANCE", "HOMENEEDS",
        "INTER WORLD GEM", "KRISTAL CLEAR DIAMOND (J)", "MONEYMAX", "MULTIGAINED",
        "PRIMARY MAX", "PRINCESS CUT (J)", "SAFELOCK",
        "SUREPLEDGE", "UNIWORLD-ASIA", "YELLOW ENDURANCE"
    }


    def chunks(iterable, size=10):
        it = iter(iterable)
        return iter(lambda: list(islice(it, size)), [])

    images_by_branch = {}
    branches = set()

    for corp_chunk in chunks(group3_corporations, 10):
        docs = db.collection("Uploaded_Images").where("corporations", "in", corp_chunk).stream()

        for doc in docs:
            data = doc.to_dict()
            branch = data.get("branch", "Unknown")
            data["doc_id"] = doc.id
            branches.add(branch)
            images_by_branch.setdefault(branch, []).append(data)

    branches = sorted(branches)

    def show_images(branch=None, corporation=None):
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        filter_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
        filter_frame.pack(pady=(10, 0), fill="x")
        if corporation:
            all_images = []
            for imgs in images_by_branch.values():
                all_images.extend([img for img in imgs if img.get("corporations", "").strip().upper() == corporation])
        else:
        
            all_images = images_by_branch.get(branch, [])
        transaction_types = sorted(set(img.get("transaction_type", "") for img in all_images if img.get("transaction_type")))
        transaction_types = ["All"] + transaction_types
        trans_type_var = tk.StringVar(value="All")

        tk.Label(filter_frame, text="Transaction Type:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
        trans_type_menu = tk.OptionMenu(filter_frame, trans_type_var, *transaction_types)
        trans_type_menu.config(font=("Arial", 10))
        trans_type_menu.pack(side="left", padx=(0, 10))

        try:
            from tkcalendar import DateEntry
        except ImportError:
            tk.Label(filter_frame, text="[tkcalendar not installed]", font=("Arial", 10), fg="red", bg="#ecf0f1").pack(side="left", padx=(0, 2))
            DateEntry = None

        tk.Label(filter_frame, text="From:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
        start_date_var = tk.StringVar()
        end_date_var = tk.StringVar()

        if 'DateEntry' in locals() and DateEntry:
            start_date_picker = DateEntry(filter_frame, textvariable=start_date_var, font=("Arial", 10), width=12, date_pattern='yyyy-mm-dd')
            start_date_picker.pack(side="left", padx=(0, 5))

            tk.Label(filter_frame, text="To:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
            end_date_picker = DateEntry(filter_frame, textvariable=end_date_var, font=("Arial", 10), width=12, date_pattern='yyyy-mm-dd')
            end_date_picker.pack(side="left", padx=(0, 10))
        else:
            tk.Entry(filter_frame, textvariable=start_date_var, font=("Arial", 10), width=12).pack(side="left", padx=(0, 5))
            tk.Label(filter_frame, text="To:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
            tk.Entry(filter_frame, textvariable=end_date_var, font=("Arial", 10), width=12).pack(side="left", padx=(0, 10))


        images_per_page = 10
        current_page = [0]
        filtered_images = []
        
        selected_images = set()

        download_selected_btn = tk.Button(filter_frame, text="Download Selected", font=("Arial", 10), bg="#066e18", fg="white")
        delete_selected_btn = tk.Button(filter_frame, text="Delete Selected", font=("Arial", 10), bg="#c0392b", fg="white")
        download_selected_btn.pack_forget()
        delete_selected_btn.pack_forget()

        def update_selected_buttons():
            if selected_images:
                download_selected_btn.pack(side="left", padx=2)
                delete_selected_btn.pack(side="left", padx=2)
            else:
                download_selected_btn.pack_forget()
                delete_selected_btn.pack_forget()

        def on_select(doc_id, var):
            if var.get():
                selected_images.add(doc_id)
            else:
                selected_images.discard(doc_id)
            update_selected_buttons()

        def download_selected_images():
            if not selected_images:
                messagebox.showinfo("No Selection", "No images selected for download.")
                return
            folder = filedialog.askdirectory(title="Select Download Folder")
            if not folder:
                return
            success, failed = 0, 0
            for img in filtered_images:
                if img["doc_id"] in selected_images:
                    try:
                        url = img.get("image_url")
                        fname = img.get("filename", "image.jpg")
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            with open(f"{folder}/{fname}", "wb") as f:
                                f.write(response.content)
                            success += 1
                        else:
                            failed += 1
                    except:
                        failed += 1
            messagebox.showinfo("Download Complete", f"Downloaded: {success}, Failed: {failed}")

        def delete_selected_images():
            if not selected_images:
                messagebox.showinfo("No Selection", "No images selected for deletion.")
                return
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_images)} selected images?")
            if not confirm:
                return
            success, failed = 0, 0
            to_delete = [img for img in filtered_images if img["doc_id"] in selected_images]
            for doc_data in to_delete:
                filename = doc_data.get("filename", "this file")
                try:
                    db.collection("Uploaded_Images").document(doc_data["doc_id"]).delete()
                    date = doc_data.get("date", "")
                    branch_folder = doc_data.get("branch", "Unknown_Branch")
                    storage_path = doc_data.get("storage_path", f"{branch_folder}/{date}/{filename}")
                    blob = bucket.blob(storage_path)
                    blob.delete()
                    if branch in images_by_branch:
                        images_by_branch[branch] = [i for i in images_by_branch[branch] if i["doc_id"] != doc_data["doc_id"]]
                    if doc_data in filtered_images:
                        filtered_images.remove(doc_data)
                    selected_images.discard(doc_data["doc_id"])
                    success += 1
                except Exception as err:
                    failed += 1
            filtered_images[:] = [img for img in images_by_branch.get(branch, []) if matches(img)]
            current_page[0] = 0
            display_images_page()
            messagebox.showinfo("Delete Complete", f"Deleted: {success}, Failed: {failed}")

        download_selected_btn.config(command=download_selected_images)
        delete_selected_btn.config(command=delete_selected_images)

        def clean_date(date_str):
            return date_str.strip().replace("–", "-").replace("—", "-")
        def matches(img):
            ttype = trans_type_var.get().strip().lower()
            start_val = clean_date(start_date_var.get().strip())
            end_val = clean_date(end_date_var.get().strip())
            start_date = datetime.datetime.strptime(start_val, "%Y-%m-%d") if start_val else None
            end_date = datetime.datetime.strptime(end_val, "%Y-%m-%d") if end_val else None
            img_date_str = clean_date(img.get("date", ""))
            try:
                img_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d")
            except:
                return False

            img_type = img.get("transaction_type", "").strip().lower()

                # Type filter
            if ttype != "all" and img_type != ttype:
                return False

                # Date range filter
            if start_date and img_date < start_date:
                return False
            if end_date and img_date > end_date:
                return False

            return True

        def apply_filters(*args):
            ttype = trans_type_var.get().strip().lower()
            start_val = clean_date(start_date_var.get().strip())
            end_val = clean_date(end_date_var.get().strip())

            start_date = datetime.datetime.strptime(start_val, "%Y-%m-%d") if start_val else None
            end_date = datetime.datetime.strptime(end_val, "%Y-%m-%d") if end_val else None

            filtered = list(filter(matches, all_images))

    

            


            filtered = list(filter(matches, all_images))
            print(f"[DEBUG] {len(filtered)} matched images")

            filtered_images.clear()
            filtered_images.extend(filtered)
            current_page[0] = 0
            display_images_page()
            



        def download_all_images():
            if not filtered_images:
                messagebox.showinfo("No Images", "No filtered images to download.")
                return

            folder = filedialog.askdirectory(title="Select Download Folder")
            if not folder:
                return

            success, failed = 0, 0
            for img in filtered_images:
                try:
                    url = img.get("image_url")
                    fname = img.get("filename", "image.jpg")
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        with open(f"{folder}/{fname}", "wb") as f:
                            f.write(response.content)
                        success += 1
                    else:
                        failed += 1
                except:
                    failed += 1

            messagebox.showinfo("Download Complete", f"Downloaded: {success}, Failed: {failed}")

        def display_images_page():
            for widget in scroll_frame.winfo_children():
                if widget != filter_frame:
                    widget.destroy()
            image_refs.clear()

            start = current_page[0] * images_per_page
            end = start + images_per_page
            page_images = filtered_images[start:end]

            # --- Select All Checkbox ---
            select_all_var = tk.BooleanVar(value=all(img["doc_id"] in selected_images for img in page_images) and len(page_images) > 0)
            def on_select_all():
                if select_all_var.get():
                    for img in page_images:
                        selected_images.add(img["doc_id"])
                else:
                    for img in page_images:
                        selected_images.discard(img["doc_id"])
                update_selected_buttons()
                display_images_page()  # Refresh checkboxes

            select_all_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
            select_all_frame.pack(fill="x", padx=18, pady=(0, 4))
            tk.Checkbutton(
                select_all_frame,
                text="Select All (this page & filter)",
                variable=select_all_var,
                command=on_select_all,
                bg="#ecf0f1",
                font=("Segoe UI", 10)
            ).pack(anchor="w")

            if not page_images:
                tk.Label(scroll_frame, text="No images found.", font=("Arial", 12), fg="#c0392b", bg="#ecf0f1").pack(pady=20)
                return
            def view_full_image(img_data):
                top = tk.Toplevel(admin)
                top.title(img_data.get("filename", "Image"))
                top.geometry("900x700")
                top.configure(bg="white")

                try:
                    response = requests.get(img_data["image_url"], timeout=10)
                    image_data = BytesIO(response.content)
                    pil_image = Image.open(image_data).convert("RGB")
                except Exception as e:
                    tk.Label(top, text=f"Failed to load image: {e}", bg="white", fg="red").pack()
                    return

                canvas = tk.Canvas(top, bg="white", highlightthickness=0)
                canvas.pack(fill="both", expand=True)

                zoom_factor = [1.0]  # List so it's mutable in nested functions
                base_image = pil_image

                def render_image():
                    # Resize image based on zoom factor
                    new_size = (int(base_image.width * zoom_factor[0]), int(base_image.height * zoom_factor[0]))
                    resized_img = base_image.resize(new_size, Image.LANCZOS)
                    tk_image = ImageTk.PhotoImage(resized_img, master=top)
                    canvas.delete("IMG")
                    canvas.create_image(top.winfo_width()//2, top.winfo_height()//2, anchor="center", image=tk_image, tags="IMG")
                    canvas.image = tk_image  # prevent garbage collection

                def zoom(event):
                    if event.delta > 0 or event.num == 4:  # Zoom in
                        zoom_factor[0] *= 1.1
                    elif event.delta < 0 or event.num == 5:  # Zoom out
                        zoom_factor[0] /= 1.1
                    render_image()

                # Bind mouse wheel zoom
                canvas.bind("<MouseWheel>", zoom)  # Windows and Mac
                canvas.bind("<Button-4>", zoom)    # Linux scroll up
                canvas.bind("<Button-5>", zoom)    # Linux scroll down

                # Optional: Zoom buttons
                zoom_frame = tk.Frame(top, bg="white")
                zoom_frame.pack(fill="x", side="bottom", pady=5)

                tk.Button(zoom_frame, text="➕ Zoom In", command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0]*1.1), render_image()]).pack(side="left", padx=10)
                tk.Button(zoom_frame, text="➖ Zoom Out", command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0]/1.1), render_image()]).pack(side="left")

                render_image()




            def load_image_async(img_data, img_label):
                try:
                    url = img_data["image_url"]
                    print(f"Loading image from: {url}")
                    response = requests.get(url, timeout=10)
                    print("Status Code:", response.status_code)
                    print("Content-Type:", response.headers.get('Content-Type'))

                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        image_data = BytesIO(response.content)
                        pil_img = Image.open(image_data).convert("RGB")
                        pil_img.thumbnail((180, 180))
                        photo = ImageTk.PhotoImage(pil_img, master=admin)

                        def update_ui():
                            img_label.config(image=photo, text="")  # remove text
                            img_label.image = photo
                            image_refs.append(photo)  # Keep reference
                            img_label.bind("<Button-1>", lambda e, data=img_data: view_full_image(data))
                        admin.after(0, update_ui)
                    else:
                        admin.after(0, lambda: img_label.config(text="❌ Not an image", fg="red"))
                except Exception as e:
                    print(f"Image load failed: {e}")
                    admin.after(0, lambda: img_label.config(text="❌ Failed to load image", fg="red"))

            # Inside your loop
            for img in page_images:
                frame = tk.Frame(
                    scroll_frame, 
                    bg="#f7f7fa", 
                    relief="groove", 
                    bd=2, 
                    highlightbackground="#d1d5db", 
                    highlightthickness=1
                )
                frame.pack(padx=18, pady=12, fill="x", ipadx=4, ipady=4)
                img_label = tk.Label(
                    frame, 
                    bg="#f7f7fa", 
                    text="Loading...", 
                    font=("Segoe UI", 10, "italic"), 
                    width=24, 
                    height=10, 
                    borderwidth=0
                )
                img_label.pack(side="left", padx=14, pady=8)
                img_label.bind("<Enter>", lambda e: img_label.config(bg="#e0e7ef"))
                img_label.bind("<Leave>", lambda e: img_label.config(bg="#f7f7fa"))

                Thread(target=load_image_async, args=(img, img_label), daemon=True).start()

                info_frame = tk.Frame(frame, bg="#f7f7fa")
                info_frame.pack(side="left", padx=12, fill="x", expand=True)
                for label, val in [
                    ("File", img.get("filename", "")),
                    ("Branch", img.get("branch", "")),
                    ("Uploaded By", img.get("uploaded_by", "")),
                    ("Date of Transaction", img.get("date", "")),
                    ("Transaction type", img.get("transaction_type", ""))
                ]:
                    row = tk.Frame(info_frame, bg="#f7f7fa")
                    row.pack(anchor="w", pady=2, fill="x")
                    tk.Label(
                        row, 
                        text=f"{label}:", 
                        font=("Segoe UI", 10, "bold"), 
                        bg="#f7f7fa", 
                        fg="#34495e", 
                        width=16, 
                        anchor="w"
                    ).pack(side="left")
                    tk.Label(
                        row, 
                        text=f"{val}", 
                        font=("Segoe UI", 10), 
                        bg="#f7f7fa", 
                        fg="#222", 
                        anchor="w"
                    ).pack(side="left")



                # Add selection checkbox
                select_var = tk.BooleanVar(value=img["doc_id"] in selected_images)
                cb_frame = tk.Frame(frame, bg="#f7f7fa")
                cb_frame.pack(side="right", padx=10, pady=10)
                cb = tk.Checkbutton(
                    cb_frame, 
                    text="Select", 
                    variable=select_var,
                    command=lambda doc_id=img["doc_id"], var=select_var: on_select(doc_id, var), 
                    bg="#f7f7fa", 
                    font=("Segoe UI", 10)
                )
                cb.pack()
            def show_corporation_images(corporation):
                for widget in scroll_frame.winfo_children():
                    widget.destroy()
                image_refs.clear()

                # Gather all images for the selected corporation
                corp_images = []
                for imgs in images_by_branch.values():
                    corp_images.extend([img for img in imgs if img.get("corporations", "").strip().upper() == corporation])

                if not corp_images:
                    tk.Label(scroll_frame, text="No images found for this corporation.", font=("Arial", 12), fg="#c0392b", bg="#ecf0f1").pack(pady=20)
                    return

                for img in page_images:
                    frame = tk.Frame(
                        scroll_frame, 
                        bg="#f7f7fa", 
                        relief="groove", 
                        bd=2, 
                        highlightbackground="#d1d5db", 
                        highlightthickness=1
                    )
                    frame.pack(padx=18, pady=12, fill="x", ipadx=4, ipady=4)

                    if not corporation:
                        # Show thumbnail
                        img_label = tk.Label(
                            frame, 
                            bg="#f7f7fa", 
                            text="Loading...", 
                            font=("Segoe UI", 10, "italic"), 
                            width=24, 
                            height=10, 
                            borderwidth=0
                        )
                        img_label.pack(side="left", padx=14, pady=8)
                        img_label.bind("<Enter>", lambda e: img_label.config(bg="#e0e7ef"))
                        img_label.bind("<Leave>", lambda e: img_label.config(bg="#f7f7fa"))
                        Thread(target=load_image_async, args=(img, img_label), daemon=True).start()

                    # Show details and view button (always)
                    info_frame = tk.Frame(frame, bg="#f7f7fa")
                    info_frame.pack(side="left", padx=12, fill="x", expand=True)
                    for label, val in [
                        ("File", img.get("filename", "")),
                        ("Branch", img.get("branch", "")),
                        ("Uploaded By", img.get("uploaded_by", "")),
                        ("Date of Transaction", img.get("date", "")),
                        ("Transaction type", img.get("transaction_type", ""))
                    ]:
                        row = tk.Frame(info_frame, bg="#f7f7fa")
                        row.pack(anchor="w", pady=2, fill="x")
                        tk.Label(
                            row, 
                            text=f"{label}:", 
                            font=("Segoe UI", 10, "bold"), 
                            bg="#f7f7fa", 
                            fg="#34495e", 
                            width=16, 
                            anchor="w"
                        ).pack(side="left")
                        tk.Label(
                            row, 
                            text=f"{val}", 
                            font=("Segoe UI", 10), 
                            bg="#f7f7fa", 
                            fg="#222", 
                            anchor="w"
                        ).pack(side="left")

                    def view_image(img_data=img):
                        top = tk.Toplevel(admin)
                        top.title(img_data.get("filename", "Image"))
                        top.geometry("900x700")
                        top.configure(bg="white")
                        try:
                            response = requests.get(img_data["image_url"], timeout=10)
                            image_data = BytesIO(response.content)
                            pil_image = Image.open(image_data).convert("RGB")
                        except Exception as e:
                            tk.Label(top, text=f"Failed to load image: {e}", bg="white", fg="red").pack()
                            return
                        canvas = tk.Canvas(top, bg="white", highlightthickness=0)
                        canvas.pack(fill="both", expand=True)
                        tk_image = ImageTk.PhotoImage(pil_image, master=top)
                        canvas.create_image(top.winfo_width()//2, top.winfo_height()//2, anchor="center", image=tk_image)
                        canvas.image = tk_image  # prevent garbage collection

                    tk.Button(frame, text="View", font=("Segoe UI", 10), bg="#2980b9", fg="white", command=view_image).pack(side="right", padx=10, pady=10)      
                            # Load image asynchronously          
            nav_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
            nav_frame.pack(pady=5)
            tk.Button(nav_frame, text="⬅ Prev", state="normal" if current_page[0] > 0 else "disabled",
                    command=lambda: go_page(-1)).pack(side="left", padx=5)
            tk.Label(nav_frame, text=f"Page {current_page[0]+1} of {max(1, (len(filtered_images)-1)//images_per_page+1)}",
                    bg="#ecf0f1", font=("Arial", 10)).pack(side="left")
            tk.Button(nav_frame, text="Next ➡", state="normal" if end < len(filtered_images) else "disabled",
                    command=lambda: go_page(1)).pack(side="left", padx=5)
        def go_page(direction):
            current_page[0] += direction
            display_images_page()

        if 'start_date_picker' in locals():
            start_date_picker.bind("<<DateEntrySelected>>", apply_filters)
            end_date_picker.bind("<<DateEntrySelected>>", apply_filters)


        tk.Button(filter_frame, text="Apply Filters", font=("Arial", 10), bg="#2980b9", fg="white", command=apply_filters).pack(side="left", padx=(0, 2))
        tk.Button(filter_frame, text="Download All", font=("Arial", 10), bg="#8e44ad", fg="white", command=download_all_images).pack(side="left", padx=2)

        filtered_images.clear()
        filtered_images.extend(all_images)
        display_images_page()

    # Sidebar layout
    group_name = admin_data.get("group", "Unknown Group")
    tk.Label(sidebar, text=f"Welcome {group_name}", font=("Poppins", 12), bg="#2c3e50", fg="white").pack(pady=(60,10))

    branches_frame = tk.Frame(sidebar, bg="#2c3e50")
    search_frame = tk.Frame(sidebar, bg="#2c3e50")
    search_var = tk.StringVar()
    
    selected_corp_var = tk.StringVar()
    selected_corp_var.set("Select Branch")
 

    corp_list = sorted(group3_corporations)
    def show_corporation_selector():
        popup = tk.Toplevel(admin)
        popup.title("Select Corporation")
        popup.geometry("350x120")
        popup.configure(bg="#ecf0f1")

        tk.Label(popup, text="Choose a corporation:", font=("Arial", 11), bg="#ecf0f1").pack(pady=(15, 5))
        corp_var = tk.StringVar(value="Select Corporation")
        corp_list = sorted(group3_corporations)
        corp_dropdown = tk.OptionMenu(popup, corp_var, *corp_list)
        corp_dropdown.config(font=("Arial", 10), bg="#34495e", fg="white", width=22)
        corp_dropdown["menu"].config(font=("Arial", 10))
        corp_dropdown.pack(pady=(0, 10))

        def on_confirm():
            selected = corp_var.get()
            if selected and selected != "Select Corporation":
                popup.destroy()
                show_images(branch=None, corporation=selected)
            else:
                messagebox.showwarning("Select Corporation", "Please select a corporation.")

        tk.Button(popup, text="Show Images", font=("Arial", 10), bg="#2980b9", fg="white", width=14, command=on_confirm).pack(pady=(0, 10))

# Now place the button after the function definition:
    tk.Button(
        sidebar,
        text="Select Corporation",
        font=("Arial", 10),
        bg="#2980b9",
        fg="white",
        width= 20,
        command=show_corporation_selector
    ).pack(pady=(20, 12))


    def on_corp_selected(*args):
        selected_corp = selected_corp_var.get()
        if selected_corp and selected_corp != "Select Corporation":
            filtered_branches = sorted([
                branch for branch, imgs in images_by_branch.items()
                if any(img.get("corporations", "").strip().upper() == selected_corp for img in imgs)
            ])
            show_branch_buttons(filtered_branches)


    corp_dropdown = tk.OptionMenu(sidebar, selected_corp_var, *corp_list, command=lambda _: on_corp_selected())
    corp_dropdown.config(font=("Arial", 10), bg="#34495e", fg="white", width=18)
    corp_dropdown["menu"].config(font=("Arial", 10))
    corp_dropdown.pack(pady=(0, 10))
    
    def show_branch_buttons(filtered=None):
        for widget in branches_frame.winfo_children():
            widget.destroy()
        show_list = filtered if filtered is not None else branches
        for branch in show_list:
            tk.Button(branches_frame, text=branch, font=("Arial", 11), bg="#34495e", fg="white", width=18, command=lambda b=branch: show_images(b)).pack(pady=2)
        branches_frame.pack(pady=5)

    branches_visible = [False]


    tk.Button(sidebar, text="Add User", font=("Arial", 11), bg="#27ae60", fg="white", command=lambda: open_add_user_popup_group3(admin), width=18).pack(pady=5)





    def logout():
        admin.destroy()
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

    tk.Button(sidebar, text="Logout", font=("Arial", 11), bg="#c0392b", fg="white", command=logout, width=18).pack(pady=5)
    tk.Label(sidebar, text="Developed by: Paolo Somido", font=("Arial", 9), fg="lightgray", bg="#2c3e50").pack(side="bottom", pady=10)

    admin.mainloop()