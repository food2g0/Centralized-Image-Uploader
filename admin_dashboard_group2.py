def open_admin_dashboard_group2(admin_data):
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk
    from firebase_config import db, bucket
    from PIL import Image, ImageTk
    import requests
    from add_user_group2 import open_add_user_popup_group2
    from io import BytesIO
    from threading import Thread
    import datetime
    from itertools import islice
    from head_office_popup import open_head_office_popup
    from head_office_images import open_head_office_images
    from Colors import COLORS
    from corporations import group2_corporations
    from notification_system import NotificationSystem  # Import the notification system

    admin = tk.Tk()
    admin.title("Admin Dashboard - Record Management System")
    admin.state('zoomed')  
    admin.configure(bg="#f8fafc")

    screen_width = admin.winfo_screenwidth()
    screen_height = admin.winfo_screenheight()

    min_width = max(1024, int(screen_width * 0.8))
    min_height = max(768, int(screen_height * 0.8))

    admin.minsize(min_width, min_height)
    admin.geometry(f"{min_width}x{min_height}")

    # Responsive scaling factors
    scale_factor = min(screen_width / 1920, screen_height / 1080)
    font_scale = max(0.8, min(1.2, scale_factor))

    sidebar_width = max(250, min(350, int(screen_width * 0.2)))

    # Responsive font sizes
    def get_font_size(base_size):
        return max(8, int(base_size * font_scale))

    # Initialize notification system
    notification_system = NotificationSystem(admin, admin_data)

    # Responsive ttk styles
    style = ttk.Style()
    style.theme_use('clam')

    style.configure('Modern.TButton',
                    background=COLORS['secondary'],
                    foreground='white',
                    borderwidth=0,
                    focuscolor='none',
                    relief='flat',
                    padding=(int(20 * font_scale), int(10 * font_scale)))

    style.map('Modern.TButton',
              background=[('active', '#2563eb'), ('pressed', '#1d4ed8')])

    # Responsive sidebar
    sidebar = tk.Frame(admin, width=sidebar_width, bg=COLORS['sidebar'], relief="flat")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    # Responsive hamburger button
    hamburger_btn = tk.Button(
        admin,
        text="☰",
        font=("Segoe UI", get_font_size(16), "bold"),
        bg=COLORS['sidebar'],
        fg="white",
        bd=0,
        relief="flat",
        width=3,
        height=2,
        state="disabled"
    )
    hamburger_btn.place(x=8, y=8)

    # Main content area with responsive padding
    responsive_padding = max(10, int(20 * font_scale))
    main_frame = tk.Frame(admin, bg=COLORS['background'])
    main_frame.pack(side="left", fill=tk.BOTH, expand=True, padx=responsive_padding, pady=responsive_padding)

    # Responsive header with refresh and notification buttons
    header_frame = tk.Frame(main_frame, bg=COLORS['surface'], relief="flat", bd=1)
    header_frame.pack(fill="x", pady=(0, responsive_padding), ipady=int(15 * font_scale))

    # Title section
    title_frame = tk.Frame(header_frame, bg=COLORS['surface'])
    title_frame.pack(side="left", fill="both", expand=True)

    tk.Label(
        title_frame,
        text="Record Management System",
        font=("Segoe UI", get_font_size(20), "bold"),
        bg=COLORS['surface'],
        fg=COLORS['text']
    ).pack(pady=int(10 * font_scale))

    # Buttons frame in top right (now contains both refresh and notification buttons)
    buttons_frame = tk.Frame(header_frame, bg=COLORS['surface'])
    buttons_frame.pack(side="right", padx=int(20 * font_scale), pady=int(10 * font_scale))

    content_frame = tk.Frame(main_frame, bg=COLORS['background'])
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Responsive image viewer
    viewer_frame = tk.Frame(content_frame, bg=COLORS['surface'], relief="flat", bd=1)
    viewer_frame.pack(side="left", fill=tk.BOTH, expand=True, padx=(0, int(10 * font_scale)))
    viewer_frame.pack_propagate(False)

    # Responsive canvas with scrollbar
    canvas = tk.Canvas(viewer_frame, bg=COLORS['surface'], highlightthickness=0, bd=0)

    scrollbar_width = max(12, int(16 * font_scale))
    scrollbar = tk.Scrollbar(viewer_frame, orient="vertical", command=canvas.yview,
                             bg=COLORS['border'], troughcolor=COLORS['background'],
                             activebackground=COLORS['secondary'], width=scrollbar_width)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y", padx=(2, 0))
    canvas.pack(side="left", fill="both", expand=True)

    last_branch = [None]
    last_corporation = [None]

    scroll_frame = tk.Frame(canvas, bg=COLORS['surface'])
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(scroll_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    def _on_mousewheel(event):
        # Handle mouse wheel scrolling for the main canvas
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Bind mouse wheel events to the canvas and related widgets
    canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux wheel up
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux wheel down

    # Also bind to the scroll_frame and main elements for better coverage
    scroll_frame.bind("<MouseWheel>", _on_mousewheel)
    main_frame.bind("<MouseWheel>", _on_mousewheel)

    # Make sure the canvas can receive focus for mouse events
    canvas.focus_set()

    def bind_mousewheel_to_main_widgets(widget):
        try:
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        except:
            pass

        for child in widget.winfo_children():
            bind_mousewheel_to_main_widgets(child)

        # Add this at the end of your show_images function, after all widgets are created:

        # Ensure scroll wheel works on all main content widgets
        bind_mousewheel_to_main_widgets(scroll_frame)

        # Also bind to the canvas directly for better responsiveness
        canvas.bind("<Enter>", lambda e: canvas.focus_set())

        # Make sure the canvas updates its scroll region
        scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    image_refs = []

    def chunks(iterable, size=10):
        it = iter(iterable)
        return iter(lambda: list(islice(it, size)), [])

    images_by_branch = {}
    branches = set()

    for corp_chunk in chunks(group2_corporations, 10):
        docs = db.collection("Uploaded_Images").where("corporations", "in", corp_chunk).stream()

        for doc in docs:
            data = doc.to_dict()
            branch = data.get("branch", "Unknown")
            data["doc_id"] = doc.id
            branches.add(branch)
            images_by_branch.setdefault(branch, []).append(data)

    branches = sorted(branches)

    def refresh_data():
        """Refresh the current view"""
        show_images(branch=last_branch[0], corporation=last_corporation[0])

    def show_notifications():
        """Show notifications - placeholder function"""
        notification_system.open_notifications()

    # Create notification button (beside refresh button)
    notification_btn = tk.Button(
        buttons_frame,
        text="🔔 Notifications",
        font=("Segoe UI", get_font_size(11), "bold"),
        bg=COLORS['accent'],
        fg="white",
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=int(20 * font_scale),
        pady=int(8 * font_scale),
        command=show_notifications
    )
    notification_btn.pack(side="left", padx=(0, int(10 * font_scale)))

    # Create refresh button
    refresh_btn = tk.Button(
        buttons_frame,
        text="🔄 Refresh",
        font=("Segoe UI", get_font_size(11), "bold"),
        bg=COLORS['secondary'],
        fg="white",
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=int(20 * font_scale),
        pady=int(8 * font_scale),
        command=refresh_data
    )
    refresh_btn.pack(side="left")

    # Rest of your existing code remains the same...
    # [Continue with all the existing functions like show_images, etc.]

    def show_images(branch=None, corporation=None):
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        # Responsive filter frame
        filter_padding = max(12, int(15 * font_scale))
        filter_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
        filter_frame.pack(pady=(filter_padding, int(10 * font_scale)), fill="x",
                          padx=int(20 * font_scale), ipady=int(12 * font_scale))

        if corporation:
            all_images = []
            for imgs in images_by_branch.values():
                all_images.extend([img for img in imgs if img.get("corporations", "").strip().upper() == corporation])
        else:
            all_images = images_by_branch.get(branch, [])

        transaction_types = sorted(
            set(img.get("transaction_type", "") for img in all_images if img.get("transaction_type")))
        transaction_types = ["All"] + transaction_types
        trans_type_var = tk.StringVar(value="All")

        filename_search_var = tk.StringVar()

        # Responsive filter rows
        filter_row1 = tk.Frame(filter_frame, bg=COLORS['surface'])
        filter_row1.pack(fill="x", pady=(0, int(8 * font_scale)))

        # Responsive labels and controls
        tk.Label(
            filter_row1,
            text="Transaction Type:",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(int(10 * font_scale), int(5 * font_scale)))

        trans_type_menu = tk.OptionMenu(filter_row1, trans_type_var, *transaction_types)
        trans_type_menu.config(
            font=("Segoe UI", get_font_size(10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary'],
            activeforeground='white',
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        trans_type_menu["menu"].config(
            font=("Segoe UI", get_font_size(10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary']
        )
        trans_type_menu.pack(side="left", padx=(0, int(20 * font_scale)))

        # Responsive filename search
        tk.Label(
            filter_row1,
            text="🔍 Search Filename:",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(0, int(5 * font_scale)))

        # Responsive search entry width
        search_width = max(20, min(35, int(25 * (screen_width / 1920))))
        filename_search_entry = tk.Entry(
            filter_row1,
            textvariable=filename_search_var,
            font=("Segoe UI", get_font_size(10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            bd=1,
            relief="solid",
            width=search_width,
            insertbackground=COLORS['secondary']
        )
        filename_search_entry.pack(side="left", padx=(0, int(10 * font_scale)))

        # Placeholder text behavior
        def on_filename_focus_in(event):
            if filename_search_entry.get() == "Type filename here...":
                filename_search_entry.delete(0, tk.END)
                filename_search_entry.config(fg=COLORS['text'])

        def on_filename_focus_out(event):
            if not filename_search_entry.get():
                filename_search_entry.insert(0, "Type filename here...")
                filename_search_entry.config(fg=COLORS['muted'])

        filename_search_entry.insert(0, "Type filename here...")
        filename_search_entry.config(fg=COLORS['muted'])
        filename_search_entry.bind("<FocusIn>", on_filename_focus_in)
        filename_search_entry.bind("<FocusOut>", on_filename_focus_out)

        # Second row for date filters
        filter_row2 = tk.Frame(filter_frame, bg=COLORS['surface'])
        filter_row2.pack(fill="x")

        try:
            from tkcalendar import DateEntry
        except ImportError:
            tk.Label(
                filter_row2,
                text="[tkcalendar not installed]",
                font=("Segoe UI", get_font_size(10)),
                fg=COLORS['danger'],
                bg=COLORS['surface']
            ).pack(side="left", padx=(0, int(5 * font_scale)))
            DateEntry = None

        tk.Label(
            filter_row2,
            text="From:",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(int(10 * font_scale), int(5 * font_scale)))

        start_date_var = tk.StringVar()
        end_date_var = tk.StringVar()

        # Responsive date entry width
        date_width = max(10, int(12 * font_scale))

        if 'DateEntry' in locals() and DateEntry:
            start_date_picker = DateEntry(
                filter_row2,
                textvariable=start_date_var,
                font=("Segoe UI", get_font_size(10)),
                width=date_width,
                date_pattern='yyyy-mm-dd',
                background=COLORS['secondary'],
                foreground='white',
                borderwidth=1,
                relief="solid"
            )
            start_date_picker.pack(side="left", padx=(0, int(10 * font_scale)))

            tk.Label(
                filter_row2,
                text="To:",
                font=("Segoe UI", get_font_size(11), "bold"),
                bg=COLORS['surface'],
                fg=COLORS['text']
            ).pack(side="left", padx=(0, int(5 * font_scale)))

            end_date_picker = DateEntry(
                filter_row2,
                textvariable=end_date_var,
                font=("Segoe UI", get_font_size(10)),
                width=date_width,
                date_pattern='yyyy-mm-dd',
                background=COLORS['secondary'],
                foreground='white',
                borderwidth=1,
                relief="solid"
            )
            end_date_picker.pack(side="left", padx=(0, int(15 * font_scale)))
        else:
            date_entry_style = {
                'font': ("Segoe UI", get_font_size(10)),
                'bg': COLORS['surface'],
                'fg': COLORS['text'],
                'bd': 1,
                'relief': "solid",
                'insertbackground': COLORS['secondary']
            }
            tk.Entry(filter_row2, textvariable=start_date_var, width=date_width, **date_entry_style).pack(
                side="left", padx=(0, int(10 * font_scale)))
            tk.Label(filter_row2, text="To:", font=("Segoe UI", get_font_size(11), "bold"),
                     bg=COLORS['surface'], fg=COLORS['text']).pack(side="left", padx=(0, int(5 * font_scale)))
            tk.Entry(filter_row2, textvariable=end_date_var, width=date_width, **date_entry_style).pack(
                side="left", padx=(0, int(15 * font_scale)))

        # Responsive pagination - adjust per screen size
        if screen_width >= 1920:
            images_per_page = 15
        elif screen_width >= 1600:
            images_per_page = 12
        elif screen_width >= 1366:
            images_per_page = 10
        else:
            images_per_page = 8

        current_page = [0]
        filtered_images = []
        selected_images = set()

        # Responsive button styling
        button_padding_x = max(12, int(15 * font_scale))
        button_padding_y = max(6, int(8 * font_scale))

        button_style = {
            'font': ("Segoe UI", get_font_size(10), "bold"),
            'bd': 0,
            'relief': "flat",
            'cursor': "hand2",
            'padx': button_padding_x,
            'pady': button_padding_y
        }

        download_selected_btn = tk.Button(
            filter_row2,
            text="📥 Download Selected",
            bg=COLORS['success'],
            fg="white",
            **button_style
        )
        delete_selected_btn = tk.Button(
            filter_row2,
            text="🗑️ Delete Selected",
            bg=COLORS['danger'],
            fg="white",
            **button_style
        )
        download_selected_btn.pack_forget()
        delete_selected_btn.pack_forget()

        def update_selected_buttons():
            if selected_images:
                download_selected_btn.pack(side="left", padx=5)
                delete_selected_btn.pack(side="left", padx=5)
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

            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete {len(selected_images)} selected images?")
            if not confirm:
                return

            success, failed = 0, 0
            to_delete = [img for img in filtered_images if img["doc_id"] in selected_images]

            for doc_data in to_delete:
                filename = doc_data.get("filename", "this file")
                try:
                    date = doc_data.get("date", "")
                    branch_folder = doc_data.get("branch", "Unknown_Branch")
                    storage_path = doc_data.get("storage_path", f"{branch_folder}/{date}/{filename}")

                    try:
                        blob = bucket.blob(storage_path)
                        blob.delete()
                    except Exception as e:
                        print(f"⚠️ Failed to delete storage file {filename}: {e}")

                    db.collection("Uploaded_Images").document(doc_data["doc_id"]).delete()

                    if branch in images_by_branch:
                        images_by_branch[branch] = [i for i in images_by_branch[branch] if
                                                    i["doc_id"] != doc_data["doc_id"]]
                    if doc_data in filtered_images:
                        filtered_images.remove(doc_data)
                    selected_images.discard(doc_data["doc_id"])
                    success += 1
                except Exception as err:
                    print(f"🔥 Failed to delete {filename}: {err}")
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

            filename_query = filename_search_var.get().strip().lower()
            if filename_query and filename_query != "type filename here...":
                img_filename = img.get("filename", "").strip().lower()
                if filename_query not in img_filename:
                    return False

            start_date = datetime.datetime.strptime(start_val, "%Y-%m-%d") if start_val else None
            end_date = datetime.datetime.strptime(end_val, "%Y-%m-%d") if end_val else None
            img_date_str = clean_date(img.get("date", ""))
            try:
                img_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d")
            except:
                return False

            img_type = img.get("transaction_type", "").strip().lower()

            if ttype != "all" and img_type != ttype:
                return False

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

            def get_img_timestamp(img):
                ts = img.get("timestamp", "")
                try:
                    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            return datetime.datetime.strptime(ts, fmt)
                        except:
                            continue
                date_str = clean_date(img.get("date", ""))
                try:
                    return datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    return datetime.datetime.min

            filtered.sort(key=get_img_timestamp)
            print(f"[DEBUG] {len(filtered)} matched images")

            filtered_images.clear()
            filtered_images.extend(filtered)
            current_page[0] = 0
            display_images_page()

        def on_filename_search_change(*args):
            current_search = filename_search_var.get().strip()
            if current_search and current_search.lower() != "type filename here...":
                apply_filters()
            elif not current_search:
                apply_filters()

        filename_search_var.trace_add("write", on_filename_search_change)

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

            # Responsive search results info
            if filename_search_var.get().strip() and filename_search_var.get().strip().lower() != "type filename here...":
                search_info_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
                search_info_frame.pack(fill="x", padx=int(20 * font_scale),
                                       pady=(int(5 * font_scale), int(8 * font_scale)),
                                       ipady=int(8 * font_scale))

                search_query = filename_search_var.get().strip()
                results_count = len(filtered_images)

                tk.Label(
                    search_info_frame,
                    text=f"🔍 Search results for '{search_query}': {results_count} images found",
                    font=("Segoe UI", get_font_size(11), "bold"),
                    bg=COLORS['surface'],
                    fg=COLORS['secondary']
                ).pack(padx=int(10 * font_scale), pady=int(5 * font_scale))

            # Responsive select all
            select_all_var = tk.BooleanVar(
                value=all(img["doc_id"] in selected_images for img in page_images) and len(page_images) > 0)

            def on_select_all():
                if select_all_var.get():
                    for img in page_images:
                        selected_images.add(img["doc_id"])
                else:
                    for img in page_images:
                        selected_images.discard(img["doc_id"])
                update_selected_buttons()
                display_images_page()

            select_all_frame = tk.Frame(scroll_frame, bg=COLORS['surface'])
            select_all_frame.pack(fill="x", padx=int(20 * font_scale), pady=(int(5 * font_scale), int(8 * font_scale)))

            select_all_cb = tk.Checkbutton(
                select_all_frame,
                text="✓ Select All (this page & filter)",
                variable=select_all_var,
                command=on_select_all,
                bg=COLORS['surface'],
                fg=COLORS['text'],
                font=("Segoe UI", get_font_size(11), "bold"),
                activebackground=COLORS['surface'],
                activeforeground=COLORS['secondary'],
                selectcolor=COLORS['secondary'],
                bd=0,
                highlightthickness=0
            )
            select_all_cb.pack(anchor="w", padx=int(10 * font_scale), pady=int(5 * font_scale))

            if not page_images:
                no_images_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
                no_images_frame.pack(pady=int(30 * font_scale), padx=int(20 * font_scale), fill="x",
                                     ipady=int(30 * font_scale))

                if filename_search_var.get().strip() and filename_search_var.get().strip().lower() != "type filename here...":
                    tk.Label(
                        no_images_frame,
                        text="🔍 No files match your search",
                        font=("Segoe UI", get_font_size(16), "bold"),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack()
                    tk.Label(
                        no_images_frame,
                        text=f"No images found with filename containing: '{filename_search_var.get().strip()}'",
                        font=("Segoe UI", get_font_size(12)),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack(pady=(int(5 * font_scale), 0))
                else:
                    tk.Label(
                        no_images_frame,
                        text="📁 No images found",
                        font=("Segoe UI", get_font_size(16), "bold"),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack()
                    tk.Label(
                        no_images_frame,
                        text="Try adjusting your filters or select a different branch",
                        font=("Segoe UI", get_font_size(12)),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack(pady=(int(5 * font_scale), 0))
                return

            def view_full_image(img_data):
                top = tk.Toplevel(admin)
                top.title(f"📷 {img_data.get('filename', 'Image')}")

                # Responsive popup size
                popup_width = max(800, min(1200, int(screen_width * 0.8)))
                popup_height = max(600, min(900, int(screen_height * 0.8)))
                top.geometry(f"{popup_width}x{popup_height}")
                top.configure(bg=COLORS['background'])

                try:
                    response = requests.get(img_data["image_url"], timeout=10)
                    image_data = BytesIO(response.content)
                    pil_image = Image.open(image_data).convert("RGB")
                except Exception as e:
                    tk.Label(top, text=f"❌ Failed to load image: {e}", bg=COLORS['background'], fg=COLORS['danger'],
                             font=("Segoe UI", get_font_size(12))).pack(pady=50)
                    return

                canvas_popup = tk.Canvas(top, bg=COLORS['surface'], highlightthickness=0, bd=0)
                canvas_popup.pack(fill="both", expand=True, padx=int(20 * font_scale),
                            pady=(int(20 * font_scale), int(10 * font_scale)))

                zoom_factor = [1.0]
                base_image = pil_image

                def render_image():
                    new_size = (int(base_image.width * zoom_factor[0]), int(base_image.height * zoom_factor[0]))
                    resized_img = base_image.resize(new_size, Image.LANCZOS)
                    tk_image = ImageTk.PhotoImage(resized_img, master=top)

                    canvas_popup.delete("IMG")
                    canvas_popup.image_id = canvas_popup.create_image(canvas_popup.winfo_width() // 2, canvas_popup.winfo_height() // 2,
                                                          anchor="center", image=tk_image, tags="IMG")
                    canvas_popup.image = tk_image

                def zoom(event):
                    if event.delta > 0 or event.num == 4:
                        zoom_factor[0] *= 1.1
                    elif event.delta < 0 or event.num == 5:
                        zoom_factor[0] /= 1.1
                    render_image()

                drag_data = {"x": 0, "y": 0}

                def start_drag(event):
                    drag_data["x"] = event.x
                    drag_data["y"] = event.y

                def do_drag(event):
                    dx = event.x - drag_data["x"]
                    dy = event.y - drag_data["y"]
                    canvas_popup.move("IMG", dx, dy)
                    drag_data["x"] = event.x
                    drag_data["y"] = event.y

                canvas_popup.bind("<MouseWheel>", zoom)
                canvas_popup.bind("<Button-4>", zoom)
                canvas_popup.bind("<Button-5>", zoom)
                canvas_popup.bind("<ButtonPress-1>", start_drag)
                canvas_popup.bind("<B1-Motion>", do_drag)

                # Responsive zoom controls
                zoom_frame = tk.Frame(top, bg=COLORS['surface'], relief="flat", bd=1)
                zoom_frame.pack(fill="x", side="bottom", pady=(0, int(20 * font_scale)),
                                padx=int(20 * font_scale), ipady=int(8 * font_scale))

                zoom_btn_style = {
                    'font': ("Segoe UI", get_font_size(10), "bold"),
                    'bd': 0,
                    'relief': "flat",
                    'cursor': "hand2",
                    'padx': int(20 * font_scale),
                    'pady': int(8 * font_scale)
                }

                tk.Button(
                    zoom_frame,
                    text="🔍+ Zoom In",
                    bg=COLORS['secondary'],
                    fg="white",
                    command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0] * 1.1), render_image()],
                    **zoom_btn_style
                ).pack(side="left", padx=(int(10 * font_scale), int(5 * font_scale)))

                tk.Button(
                    zoom_frame,
                    text="🔍- Zoom Out",
                    bg=COLORS['muted'],
                    fg="white",
                    command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0] / 1.1), render_image()],
                    **zoom_btn_style
                ).pack(side="left", padx=int(5 * font_scale))

                render_image()

            def format_timestamp(ts):
                import datetime
                if not isinstance(ts, str):
                    ts = str(ts) if ts is not None else ""
                ts = ts.replace("Z", "+00:00")
                try:
                    dt = datetime.datetime.fromisoformat(ts)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            dt = datetime.datetime.strptime(ts, fmt)
                            return dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            continue
                return ts

            def load_image_async(img_data, img_label):
                try:
                    url = img_data["image_url"]
                    response = requests.get(url, timeout=10)

                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        image_data = BytesIO(response.content)
                        pil_img = Image.open(image_data).convert("RGB")

                        # Responsive thumbnail size
                        thumb_size = max(150, min(250, int(200 * font_scale)))
                        pil_img.thumbnail((thumb_size, thumb_size))
                        photo = ImageTk.PhotoImage(pil_img, master=admin)

                        def update_ui():
                            img_label.config(image=photo, text="", bg=COLORS['surface'])
                            img_label.image = photo
                            image_refs.append(photo)
                            img_label.bind("<Button-1>", lambda e, data=img_data: view_full_image(data))

                        admin.after(0, update_ui)
                    else:
                        admin.after(0, lambda: img_label.config(text="❌ Not an image", fg=COLORS['danger'],
                                                                bg=COLORS['surface']))
                except Exception as e:
                    admin.after(0, lambda: img_label.config(text="❌ Failed to load", fg=COLORS['danger'],
                                                            bg=COLORS['surface']))

            # Responsive image cards
            for img in page_images:
                card_padding = max(15, int(20 * font_scale))
                card_frame = tk.Frame(
                    scroll_frame,
                    bg=COLORS['surface'],
                    relief="flat",
                    bd=1,
                    highlightbackground=COLORS['border'],
                    highlightthickness=1
                )
                card_frame.pack(padx=int(20 * font_scale), pady=int(8 * font_scale), fill="x",
                                ipadx=card_padding, ipady=card_padding)
                card_frame.grid_columnconfigure(1, weight=1)

                # Responsive image preview
                img_width = max(20, int(24 * font_scale))
                img_height = max(8, int(10 * font_scale))

                img_label = tk.Label(
                    card_frame,
                    bg=COLORS['surface'],
                    text="📷 Loading...",
                    font=("Segoe UI", get_font_size(11), "italic"),
                    fg=COLORS['muted'],
                    width=img_width,
                    height=img_height,
                    borderwidth=0,
                    relief="flat"
                )
                img_label.grid(row=0, column=0, padx=int(15 * font_scale), pady=int(10 * font_scale), sticky="nw")

                def on_enter(e, lbl=img_label):
                    lbl.config(bg="#f1f5f9")

                def on_leave(e, lbl=img_label):
                    lbl.config(bg=COLORS['surface'])

                img_label.bind("<Enter>", on_enter)
                img_label.bind("<Leave>", on_leave)

                Thread(target=load_image_async, args=(img, img_label), daemon=True).start()

                # Responsive info section
                info_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                info_frame.grid(row=0, column=1, padx=int(15 * font_scale), sticky="nsew")

                # Enhanced filename display with search highlighting
                filename_text = img.get("filename", "")
                search_query = filename_search_var.get().strip().lower()
                if search_query and search_query != "type filename here..." and search_query in filename_text.lower():
                    filename_display = f"📄 {filename_text} ⭐"
                    filename_color = COLORS['success']
                else:
                    filename_display = filename_text
                    filename_color = COLORS['muted']

                # Responsive info data
                info_data = [
                    ("📄 File", filename_display, filename_color),
                    ("🏢 Branch", img.get("branch", ""), COLORS['muted']),
                    ("👤 Uploaded By", img.get("uploaded_by", ""), COLORS['muted']),
                    ("📅 Transaction Date", img.get("date", ""), COLORS['muted']),
                    ("💼 Transaction Type", img.get("transaction_type", ""), COLORS['muted']),
                    ("⏰ Date Uploaded", format_timestamp(img.get("timestamp", "")), COLORS['muted']),
                ]

                for label, val, text_color in info_data:
                    row = tk.Frame(info_frame, bg=COLORS['surface'])
                    row.pack(anchor="w", pady=int(3 * font_scale), fill="x")

                    label_width = max(15, int(18 * font_scale))
                    tk.Label(
                        row,
                        text=f"{label}:",
                        font=("Segoe UI", get_font_size(10), "bold"),
                        bg=COLORS['surface'],
                        fg=COLORS['text'],
                        width=label_width,
                        anchor="w"
                    ).pack(side="left")

                    # Responsive text wrapping
                    wrap_length = max(300, min(600, int(400 * (screen_width / 1920))))
                    tk.Label(
                        row,
                        text=val,
                        font=("Segoe UI", get_font_size(10),
                              "bold" if label == "📄 File" and "⭐" in str(val) else "normal"),
                        bg=COLORS['surface'],
                        fg=text_color,
                        anchor="w",
                        wraplength=wrap_length
                    ).pack(side="left")

                # Responsive actions frame
                actions_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                actions_frame.grid(row=0, column=2, padx=int(15 * font_scale), pady=int(10 * font_scale), sticky="ne")

                # Responsive checkbox
                select_var = tk.BooleanVar(value=img["doc_id"] in selected_images)
                cb = tk.Checkbutton(
                    actions_frame,
                    text="Select",
                    variable=select_var,
                    command=lambda doc_id=img["doc_id"], var=select_var: on_select(doc_id, var),
                    bg=COLORS['surface'],
                    fg=COLORS['text'],
                    font=("Segoe UI", get_font_size(10), "bold"),
                    activebackground=COLORS['surface'],
                    activeforeground=COLORS['secondary'],
                    selectcolor=COLORS['secondary'],
                    bd=0,
                    highlightthickness=0
                )
                cb.pack(pady=(0, int(5 * font_scale)))

                # Responsive view button
                view_btn_padding_x = max(10, int(12 * font_scale))
                view_btn_padding_y = max(4, int(6 * font_scale))

                view_btn = tk.Button(
                    actions_frame,
                    text="👁️ View",
                    font=("Segoe UI", get_font_size(9), "bold"),
                    bg=COLORS['accent'],
                    fg="white",
                    bd=0,
                    relief="flat",
                    cursor="hand2",
                    padx=view_btn_padding_x,
                    pady=view_btn_padding_y,
                    command=lambda data=img: view_full_image(data)
                )
                view_btn.pack()

            # Responsive navigation
            nav_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
            nav_frame.pack(pady=int(15 * font_scale), padx=int(20 * font_scale), fill="x",
                           ipady=int(10 * font_scale))

            nav_btn_style = {
                'font': ("Segoe UI", get_font_size(10), "bold"),
                'bd': 0,
                'relief': "flat",
                'cursor': "hand2",
                'padx': int(20 * font_scale),
                'pady': int(8 * font_scale)
            }

            # Previous button
            prev_btn = tk.Button(
                nav_frame,
                text="⬅️ Previous",
                state="normal" if current_page[0] > 0 else "disabled",
                bg=COLORS['secondary'] if current_page[0] > 0 else COLORS['muted'],
                fg="white",
                command=lambda: go_page(-1),
                **nav_btn_style
            )
            prev_btn.pack(side="left", padx=(int(10 * font_scale), int(5 * font_scale)))

            # Page info
            tk.Label(
                nav_frame,
                text=f"Page {current_page[0] + 1} of {max(1, (len(filtered_images) - 1) // images_per_page + 1)}",
                bg=COLORS['surface'],
                fg=COLORS['text'],
                font=("Segoe UI", get_font_size(11), "bold")
            ).pack(side="left", padx=int(20 * font_scale))

            # Next button
            next_btn = tk.Button(
                nav_frame,
                text="Next ➡️",
                state="normal" if end < len(filtered_images) else "disabled",
                bg=COLORS['secondary'] if end < len(filtered_images) else COLORS['sidebar'],
                fg="white",
                command=lambda: go_page(1),
                **nav_btn_style
            )
            next_btn.pack(side="left", padx=(int(5 * font_scale), int(10 * font_scale)))

        def go_page(direction):
            current_page[0] += direction
            display_images_page()

        if 'start_date_picker' in locals():
            start_date_picker.bind("<<DateEntrySelected>>", apply_filters)
            end_date_picker.bind("<<DateEntrySelected>>", apply_filters)

        # Responsive filter buttons
        tk.Button(
            filter_row2,
            text="🔍 Apply Filters",
            font=("Segoe UI", get_font_size(10), "bold"),
            bg=COLORS['secondary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=button_padding_x,
            pady=button_padding_y,
            command=apply_filters
        ).pack(side="left", padx=(0, int(5 * font_scale)))

        tk.Button(
            filter_row2,
            text="📥 Download All",
            font=("Segoe UI", get_font_size(10), "bold"),
            bg=COLORS['warning'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=button_padding_x,
            pady=button_padding_y,
            command=download_all_images
        ).pack(side="left", padx=int(5 * font_scale))

        # Clear search button
        def clear_filename_search():
            filename_search_var.set("")
            filename_search_entry.config(fg=COLORS['muted'])
            filename_search_entry.insert(0, "Type filename here...")
            apply_filters()

        tk.Button(
            filter_row1,
            text="❌ Clear",
            font=("Segoe UI", get_font_size(9), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(10 * font_scale),
            pady=int(6 * font_scale),
            command=clear_filename_search
        ).pack(side="left", padx=int(5 * font_scale))

        filtered_images.clear()
        filtered_images.extend(all_images)
        display_images_page()

    # Responsive Sidebar Design
    group_name = admin_data.get("group", "Unknown Group")

    # Responsive sidebar header
    header_height = max(70, int(80 * font_scale))
    sidebar_header = tk.Frame(sidebar, bg=COLORS['sidebar'], height=header_height)
    sidebar_header.pack(fill="x", pady=(0, int(10 * font_scale)))
    sidebar_header.pack_propagate(False)

    tk.Label(
        sidebar_header,
        text=f"👋 Welcome",
        font=("Segoe UI", get_font_size(14), "bold"),
        bg=COLORS['sidebar'],
        fg="white"
    ).pack(pady=(int(20 * font_scale), int(2 * font_scale)))

    tk.Label(
        sidebar_header,
        text=group_name,
        font=("Segoe UI", get_font_size(16), "bold"),
        bg=COLORS['sidebar'],
        fg=COLORS['accent']
    ).pack()

    # Responsive scrollable branches container - REDUCED HEIGHT
    available_height = screen_height - 200  # Account for header, search, buttons, footer
    branches_container_height = max(150, min(300, int(available_height * 0.4)))  # More conservative

    branches_main_frame = tk.Frame(sidebar, bg=COLORS['sidebar'])
    branches_main_frame.pack(fill="both", expand=True, padx=int(5 * font_scale), pady=(0, int(5 * font_scale)))

    branches_canvas = tk.Canvas(branches_main_frame, bg=COLORS['sidebar'], highlightthickness=0, bd=0)
    scrollbar_width = max(10, int(12 * font_scale))
    branches_scrollbar = tk.Scrollbar(branches_main_frame, orient="vertical", command=branches_canvas.yview,
                                      bg=COLORS['border'], troughcolor=COLORS['sidebar'],
                                      activebackground=COLORS['secondary'], width=scrollbar_width)
    branches_canvas.configure(yscrollcommand=branches_scrollbar.set)

    branches_scrollbar.pack(side="right", fill="y")
    branches_canvas.pack(side="left", fill="both", expand=True)

    branches_frame = tk.Frame(branches_canvas, bg=COLORS['sidebar'])
    branches_canvas_window = branches_canvas.create_window((0, 0), window=branches_frame, anchor="nw")

    def on_branches_configure(event):
        branches_canvas.configure(scrollregion=branches_canvas.bbox("all"))
        canvas_width = branches_canvas.winfo_width()
        branches_canvas.itemconfig(branches_canvas_window, width=canvas_width)

    def on_canvas_configure(event):
        canvas_width = branches_canvas.winfo_width()
        branches_canvas.itemconfig(branches_canvas_window, width=canvas_width)

    branches_frame.bind("<Configure>", on_branches_configure)
    branches_canvas.bind("<Configure>", on_canvas_configure)

    def _on_branches_mousewheel(event):
        branches_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    branches_canvas.bind("<MouseWheel>", _on_branches_mousewheel)
    branches_canvas.bind("<Button-4>", _on_branches_mousewheel)  # Linux wheel up
    branches_canvas.bind("<Button-5>", _on_branches_mousewheel)  # Linux wheel down

    def bind_mousewheel_recursive(widget):
        widget.bind("<MouseWheel>", _on_branches_mousewheel)
        for child in widget.winfo_children():
            bind_mousewheel_recursive(child)

    # Initialize variables for the sidebar components
    search_var = tk.StringVar()
    selected_corp_var = tk.StringVar()
    selected_corp_var.set("Select Corporation")

    corp_list = sorted(group2_corporations)

    def show_corporation_selector():
        popup = tk.Toplevel(admin)
        popup.title("🏢 Select Corporation")

        # Responsive popup size
        popup_width = max(350, min(500, int(400 * font_scale)))
        popup_height = max(140, int(160 * font_scale))
        popup.geometry(f"{popup_width}x{popup_height}")
        popup.configure(bg=COLORS['surface'])
        popup.resizable(False, False)

        popup.transient(admin)
        popup.grab_set()

        header_height = max(40, int(50 * font_scale))
        header_frame = tk.Frame(popup, bg=COLORS['secondary'], height=header_height)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🏢 Choose a Corporation",
            font=("Segoe UI", get_font_size(14), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(pady=int(15 * font_scale))

        content_frame = tk.Frame(popup, bg=COLORS['surface'])
        content_frame.pack(fill="both", expand=True, padx=int(20 * font_scale), pady=int(20 * font_scale))

        corp_var = tk.StringVar(value="Select Corporation")

        corp_dropdown = tk.OptionMenu(content_frame, corp_var, *corp_list)
        dropdown_width = max(20, int(25 * font_scale))
        corp_dropdown.config(
            font=("Segoe UI", get_font_size(11)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary'],
            activeforeground='white',
            bd=1,
            relief="solid",
            width=dropdown_width
        )
        corp_dropdown["menu"].config(
            font=("Segoe UI", get_font_size(11)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary']
        )
        corp_dropdown.pack(pady=(0, int(15 * font_scale)))

        def on_confirm():
            selected = corp_var.get()
            if selected and selected != "Select Corporation":
                popup.destroy()
                last_branch[0] = None
                last_corporation[0] = selected
                show_images(branch=None, corporation=selected)
            else:
                messagebox.showwarning("Select Corporation", "Please select a corporation.")

        tk.Button(
            content_frame,
            text="📊 Show Images",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=COLORS['success'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(20 * font_scale),
            pady=int(10 * font_scale),
            command=on_confirm
        ).pack()

    # FIXED SIDEBAR LAYOUT - Replace the old search_section and button_frame with this:

    # Create a proper container for all bottom elements
    bottom_container = tk.Frame(sidebar, bg=COLORS['sidebar'])
    bottom_container.pack(fill="x", pady=(int(5 * font_scale), 0))

    # Search section - move this ABOVE the buttons
    search_section = tk.Frame(bottom_container, bg=COLORS['sidebar'])
    search_section.pack(fill="x", padx=int(15 * font_scale), pady=(0, int(8 * font_scale)))

    tk.Label(
        search_section,
        text="🔍 Search Branch:",
        font=("Segoe UI", get_font_size(11), "bold"),
        bg=COLORS['sidebar'],
        fg="white"
    ).pack(pady=(0, int(3 * font_scale)))

    search_width = max(20, int(25 * font_scale))
    search_entry = tk.Entry(
        search_section,
        textvariable=search_var,
        font=("Segoe UI", get_font_size(11)),
        bg=COLORS['surface'],
        fg=COLORS['text'],
        bd=1,
        relief="solid",
        width=search_width,
        insertbackground=COLORS['secondary']
    )
    search_entry.pack(pady=(0, int(3 * font_scale)))

    # Corporation dropdown section
    corp_section = tk.Frame(bottom_container, bg=COLORS['sidebar'])
    corp_section.pack(fill="x", padx=int(15 * font_scale), pady=(0, int(8 * font_scale)))

    tk.Label(
        corp_section,
        text="🏢 Corporation:",
        font=("Segoe UI", get_font_size(11), "bold"),
        bg=COLORS['sidebar'],
        fg="white"
    ).pack(pady=(0, int(3 * font_scale)))

    def on_corp_selected(*args):
        selected_corp = selected_corp_var.get()
        if selected_corp and selected_corp != "Select Corporation":
            filtered_branches = sorted([
                branch for branch, imgs in images_by_branch.items()
                if any(img.get("corporations", "").strip().upper() == selected_corp for img in imgs)
            ])
            show_branch_buttons(filtered_branches)

    corp_dropdown = tk.OptionMenu(corp_section, selected_corp_var, *corp_list, command=lambda _: on_corp_selected())
    dropdown_width = max(16, int(20 * font_scale))
    corp_dropdown.config(
        font=("Segoe UI", get_font_size(10)),
        bg=COLORS['surface'],
        fg=COLORS['text'],
        activebackground=COLORS['secondary'],
        activeforeground='white',
        bd=1,
        relief="solid",
        width=dropdown_width
    )
    corp_dropdown["menu"].config(
        font=("Segoe UI", get_font_size(10)),
        bg=COLORS['surface'],
        fg=COLORS['text'],
        activebackground=COLORS['secondary']
    )
    corp_dropdown.pack(pady=(0, int(3 * font_scale)))

    # Action buttons section
    button_section = tk.Frame(bottom_container, bg=COLORS['sidebar'])
    button_section.pack(fill="x", padx=int(15 * font_scale), pady=(int(3 * font_scale), 0))

    # Responsive action buttons
    button_width = max(18, int(22 * font_scale))
    action_btn_style = {
        'font': ("Segoe UI", get_font_size(11), "bold"),
        'bd': 0,
        'relief': "flat",
        'cursor': "hand2",
        'width': button_width,
        'pady': int(6 * font_scale)  # Reduced padding
    }

    tk.Button(
        button_section,
        text="🏢 Select Corporation",
        command=show_corporation_selector,
        bg=COLORS['secondary'],
        fg="white",
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")  # Reduced pady

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

    def head_office_menu():
        """Create a popup menu for head office options"""
        popup = tk.Toplevel(admin)
        popup.title("🏢 Head Office Options")

        # Responsive popup size
        popup_width = max(320, min(450, int(380 * font_scale)))
        popup_height = max(200, int(240 * font_scale))
        popup.geometry(f"{popup_width}x{popup_height}")
        popup.configure(bg=COLORS['surface'])
        popup.resizable(False, False)

        # Center the popup on the parent window
        popup.transient(admin)
        popup.grab_set()

        # Calculate position to center on parent
        x = admin.winfo_x() + (admin.winfo_width() // 2) - (popup_width // 2)
        y = admin.winfo_y() + (admin.winfo_height() // 2) - (popup_height // 2)
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        # Header with gradient effect
        header_frame = tk.Frame(popup, bg=COLORS['sidebar'], height=max(50, int(60 * font_scale)))
        header_frame.pack(fill="x", pady=(0, int(20 * font_scale)))
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🏢 Head Office Options",
            font=("Segoe UI", get_font_size(16), "bold"),
            bg=COLORS['sidebar'],
            fg="white"
        ).pack(expand=True)

        # Buttons container with better spacing
        content_frame = tk.Frame(popup, bg=COLORS['surface'])
        content_frame.pack(fill="both", expand=True, padx=int(25 * font_scale), pady=int(10 * font_scale))

        # Upload button with hover effects
        upload_btn = tk.Button(
            content_frame,
            text="📤 Upload Documents",
            font=("Segoe UI", get_font_size(12), "bold"),
            bg=COLORS['success'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(25 * font_scale),
            pady=int(12 * font_scale),
            command=lambda: [popup.destroy(), open_head_office_popup(admin)]
        )
        upload_btn.pack(pady=int(8 * font_scale), fill="x")

        # Hover effects for upload button
        def on_upload_enter(e):
            upload_btn.config(bg='#059669')  # Darker green

        def on_upload_leave(e):
            upload_btn.config(bg=COLORS['success'])

        upload_btn.bind("<Enter>", on_upload_enter)
        upload_btn.bind("<Leave>", on_upload_leave)

        # View button with hover effects
        view_btn = tk.Button(
            content_frame,
            text="👁️ View Documents",
            font=("Segoe UI", get_font_size(12), "bold"),
            bg=COLORS['secondary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(25 * font_scale),
            pady=int(12 * font_scale),
            command=lambda: [popup.destroy(), open_head_office_images(admin)]
        )
        view_btn.pack(pady=int(8 * font_scale), fill="x")

        # Hover effects for view button
        def on_view_enter(e):
            view_btn.config(bg='#2563eb')  # Darker blue

        def on_view_leave(e):
            view_btn.config(bg=COLORS['secondary'])

        view_btn.bind("<Enter>", on_view_enter)
        view_btn.bind("<Leave>", on_view_leave)

        # Close button with subtle styling
        close_btn = tk.Button(
            content_frame,
            text="✕ Close",
            font=("Segoe UI", get_font_size(10), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(20 * font_scale),
            pady=int(8 * font_scale),
            command=popup.destroy
        )
        close_btn.pack(pady=(int(15 * font_scale), 0))

        # Hover effect for close button
        def on_close_enter(e):
            close_btn.config(bg=COLORS['danger'])

        def on_close_leave(e):
            close_btn.config(bg=COLORS['muted'])

        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)

        # ESC key to close popup
        popup.bind('<Escape>', lambda e: popup.destroy())
        popup.focus_set()

    tk.Button(
        button_section,
        text="➕ Add User",
        bg=COLORS['success'],
        fg="white",
        command=lambda: open_add_user_popup_group2(admin),
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

    tk.Button(
        button_section,
        text="🏢 Head Office ▼",
        bg='#8b5cf6',  # Purple color
        fg="white",
        command=head_office_menu,
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

    tk.Button(
        button_section,
        text="🚪 Logout",
        bg=COLORS['danger'],
        fg="white",
        command=logout,
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

    # Footer section
    footer_section = tk.Frame(bottom_container, bg=COLORS['sidebar'])
    footer_section.pack(fill="x", pady=(int(8 * font_scale), int(5 * font_scale)))

    tk.Label(
        footer_section,
        text="💻 Developed by:",
        font=("Segoe UI", get_font_size(9), "bold"),
        fg="#94a3b8",
        bg=COLORS['sidebar']
    ).pack()

    tk.Label(
        footer_section,
        text="Paolo Somido",
        font=("Segoe UI", get_font_size(10), "bold"),
        fg=COLORS['accent'],
        bg=COLORS['sidebar']
    ).pack()

    def update_branch_search(*args):
        query = search_var.get().strip().lower()
        if query:
            filtered = [branch for branch in branches if query in branch.lower()]
        else:
            filtered = branches
        show_branch_buttons(filtered)

    search_var.trace_add("write", update_branch_search)

    def show_branch_buttons(filtered=None):
        for widget in branches_frame.winfo_children():
            widget.destroy()

        show_list = filtered if filtered is not None else branches

        branch_btn_style = {
            'font': ("Segoe UI", get_font_size(10), "bold"),
            'bg': "#475569",
            'fg': "white",
            'bd': 0,
            'relief': "flat",
            'cursor': "hand2",
            'width': button_width,
            'pady': int(6 * font_scale)  # Reduced padding
        }

        for branch in show_list:
            btn = tk.Button(
                branches_frame,
                text=f"📂 {branch}",
                command=lambda b=branch: [last_branch.__setitem__(0, b), last_corporation.__setitem__(0, None),
                                          show_images(branch=b)],
                **branch_btn_style
            )
            btn.pack(pady=2, padx=int(15 * font_scale), fill="x")

            def on_enter(e, button=btn):
                button.config(bg=COLORS['accent'])

            def on_leave(e, button=btn):
                button.config(bg="#475569")

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            btn.bind("<MouseWheel>", _on_branches_mousewheel)

        branches_frame.update_idletasks()
        branches_canvas.configure(scrollregion=branches_canvas.bbox("all"))
        bind_mousewheel_recursive(branches_frame)

    # Initialize branch buttons
    show_branch_buttons()

    # Handle window resize events
    def on_window_resize(event):
        if event.widget == admin:
            # Update responsive elements when window is resized
            current_width = admin.winfo_width()
            current_height = admin.winfo_height()

            # Recalculate scaling if needed
            new_scale = min(current_width / 1920, current_height / 1080)
            if abs(new_scale - scale_factor) > 0.1:  # Significant change
                # Could trigger a refresh of responsive elements here
                pass

    admin.bind("<Configure>", on_window_resize)

    admin.mainloop()