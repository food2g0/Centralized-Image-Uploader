def open_head_office_images(admin):
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk
    from firebase_config import db, bucket
    from PIL import Image, ImageTk
    import requests
    from io import BytesIO
    from threading import Thread
    import datetime
    from itertools import islice
    import webbrowser
    import tempfile
    import os
    from Colors import COLORS


    popup = tk.Toplevel(admin)
    popup.title("🏢 Head Office - Record Management System")
    popup.configure(bg="#f8fafc")


    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()


    if screen_width < 1024:

        window_width = screen_width - 100
        window_height = screen_height - 100
        popup.geometry(f"{window_width}x{window_height}+50+50")
        popup.minsize(800, 600)
    elif screen_width < 1366:

        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.85)
        popup.geometry(f"{window_width}x{window_height}")
        popup.minsize(900, 650)
    else:
  
        window_width = max(1024, int(screen_width * 0.8))
        window_height = max(768, int(screen_height * 0.8))
        popup.geometry(f"{window_width}x{window_height}")
        popup.minsize(1024, 768)
        popup.state('zoomed')


    base_scale = min(screen_width / 1366, screen_height / 768) 
    scale_factor = max(0.7, min(1.3, base_scale))
    font_scale = max(0.8, min(1.2, scale_factor))

    def get_font_size(base_size):
        return max(8, int(base_size * font_scale))

   
    is_small_screen = screen_width < 1366 or screen_height < 768


    padding = 10 if is_small_screen else 20
    main_frame = tk.Frame(popup, bg=COLORS['background'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)


    current_department = [None]
    current_filter_function = [None]


    header_frame = tk.Frame(main_frame, bg=COLORS['surface'], relief="flat", bd=1)
    header_frame.pack(fill="x", pady=(0, padding), ipady=10 if is_small_screen else 15)

    header_content = tk.Frame(header_frame, bg=COLORS['surface'])
    header_content.pack(fill="x", padx=15 if is_small_screen else 20, pady=5 if is_small_screen else 10)


    title_frame = tk.Frame(header_content, bg=COLORS['surface'])
    title_frame.pack(side="left", fill="both", expand=True)

    header_text = "🏢 Record Management System" if is_small_screen else "🏢 Records Management System"
    tk.Label(
        title_frame,
        text=header_text,
        font=("Segoe UI", get_font_size(16 if is_small_screen else 20), "bold"),
        bg=COLORS['surface'],
        fg=COLORS['text']
    ).pack(anchor="w")


    refresh_frame = tk.Frame(header_content, bg=COLORS['surface'])
    refresh_frame.pack(side="right")

    def refresh_current_view():
        """Refresh the current view"""
        if current_department[0]:
        
            load_documents_for_department(current_department[0])
        else:
           
            show_head_office_images()

    refresh_btn = tk.Button(
        refresh_frame,
        text="🔄 Refresh" if is_small_screen else "🔄 Refresh",
        font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold"),
        bg=COLORS['secondary'],
        fg="white",
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=15 if is_small_screen else 20,
        pady=6 if is_small_screen else 8,
        command=refresh_current_view
    )
    refresh_btn.pack()


    def on_refresh_enter(e):
        refresh_btn.config(bg='#2563eb')

    def on_refresh_leave(e):
        refresh_btn.config(bg=COLORS['secondary'])

    refresh_btn.bind("<Enter>", on_refresh_enter)
    refresh_btn.bind("<Leave>", on_refresh_leave)

    # Content frame
    content_frame = tk.Frame(main_frame, bg=COLORS['background'])
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Viewer frame with scrollbar
    viewer_frame = tk.Frame(content_frame, bg=COLORS['surface'], relief="flat", bd=1)
    viewer_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(viewer_frame, bg=COLORS['surface'], highlightthickness=0, bd=0)
    scrollbar_width = 12 if is_small_screen else 16
    scrollbar = tk.Scrollbar(viewer_frame, orient="vertical", command=canvas.yview,
                             bg=COLORS['border'], troughcolor=COLORS['background'],
                             activebackground=COLORS['secondary'], width=scrollbar_width)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y", padx=(2, 0))
    canvas.pack(side="left", fill="both", expand=True)

    scroll_frame = tk.Frame(canvas, bg=COLORS['surface'])
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(scroll_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    canvas.focus_set()

    image_refs = []

    def get_departments_from_db():
        """Fetch unique departments from database"""
        try:
            docs = db.collection("head_office_uploads").stream()
            departments = set()
            for doc in docs:
                data = doc.to_dict()
                dept = data.get("department", "").strip()
                if dept:
                    departments.add(dept)
            return sorted(list(departments))
        except Exception as e:
            print(f"Error fetching departments: {e}")
            return []

    def get_transaction_types_from_db(selected_dept=None):
        """Fetch unique transaction types from database, optionally filtered by department"""
        try:
            docs = db.collection("head_office_uploads").stream()
            transaction_types = set()
            for doc in docs:
                data = doc.to_dict()
                dept = data.get("department", "").strip()

                # If department is specified, only get transaction types for that department
                if selected_dept and dept != selected_dept:
                    continue

                trans_type = data.get("transaction_type", "").strip()
                if trans_type:
                    transaction_types.add(trans_type)
            return sorted(list(transaction_types))
        except Exception as e:
            print(f"Error fetching transaction types: {e}")
            return []

    def show_head_office_images():
        # Clear current department tracking
        current_department[0] = None
        current_filter_function[0] = None

        # Clear previous content
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        # Department selection frame with responsive padding
        frame_padding = 10 if is_small_screen else 15
        dept_selection_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
        dept_selection_frame.pack(pady=frame_padding, fill="x", padx=frame_padding, ipady=8 if is_small_screen else 12)

        instruction_text = "🏢 Select department:" if is_small_screen else "🏢 Please select a department to view documents:"
        tk.Label(
            dept_selection_frame,
            text=instruction_text,
            font=("Segoe UI", get_font_size(12 if is_small_screen else 14), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(pady=8 if is_small_screen else 10)

        # Get departments from database
        departments = get_departments_from_db()
        if not departments:
            tk.Label(
                scroll_frame,
                text="❌ No departments found in database",
                font=("Segoe UI", get_font_size(14)),
                fg=COLORS['danger'],
                bg=COLORS['surface']
            ).pack(pady=50)
            return

        dept_var = tk.StringVar(value="Select Department")

        # Department dropdown with responsive sizing
        dept_menu = tk.OptionMenu(dept_selection_frame, dept_var, *departments)
        dropdown_width = 15 if is_small_screen else 20
        dept_menu.config(
            font=("Segoe UI", get_font_size(10 if is_small_screen else 12)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary'],
            activeforeground='white',
            bd=1,
            relief="solid",
            width=dropdown_width
        )
        dept_menu["menu"].config(
            font=("Segoe UI", get_font_size(10 if is_small_screen else 11)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary']
        )
        dept_menu.pack(pady=8 if is_small_screen else 10)

        def on_department_selected():
            selected_dept = dept_var.get()
            if selected_dept == "Select Department":
                messagebox.showwarning("Department Required", "Please select a department first.")
                return
            load_documents_for_department(selected_dept)

        button_text = "📂 Load Docs" if is_small_screen else "📂 Load Documents"
        button_padx = 15 if is_small_screen else 20
        button_pady = 8 if is_small_screen else 10

        tk.Button(
            dept_selection_frame,
            text=button_text,
            font=("Segoe UI", get_font_size(10 if is_small_screen else 12), "bold"),
            bg=COLORS['secondary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=button_padx,
            pady=button_pady,
            command=on_department_selected
        ).pack(pady=8 if is_small_screen else 10)

    def view_pdf(pdf_data):
        """Open PDF in browser or default PDF viewer"""
        try:
            pdf_url = pdf_data.get("file_url", "")
            if not pdf_url:
                messagebox.showerror("Error", "PDF URL not found")
                return

            # Try to download and open PDF
            response = requests.get(pdf_url, timeout=30)
            if response.status_code == 200:
                # Create temporary file
                temp_dir = tempfile.mkdtemp()
                filename = pdf_data.get("filename", "document.pdf")
                if not filename.endswith('.pdf'):
                    filename += '.pdf'

                temp_path = os.path.join(temp_dir, filename)

                with open(temp_path, 'wb') as f:
                    f.write(response.content)

                # Open with default PDF viewer
                webbrowser.open(f'file://{temp_path}')
            else:
                messagebox.showerror("Error", f"Failed to download PDF: {response.status_code}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")

    def load_documents_for_department(selected_dept):
        # Track current department for refresh functionality
        current_department[0] = selected_dept

        # Clear previous content except header
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        # Get all documents for selected department
        try:
            docs = db.collection("head_office_uploads").where("department", "==", selected_dept).stream()
            all_documents = []
            for doc in docs:
                data = doc.to_dict()
                data["doc_id"] = doc.id
                all_documents.append(data)
        except Exception as e:
            tk.Label(
                scroll_frame,
                text=f"❌ Error loading documents: {e}",
                font=("Segoe UI", get_font_size(14)),
                fg=COLORS['danger'],
                bg=COLORS['surface']
            ).pack(pady=50)
            return

        if not all_documents:
            tk.Label(
                scroll_frame,
                text=f"📁 No documents found for {selected_dept}",
                font=("Segoe UI", get_font_size(14)),
                fg=COLORS['muted'],
                bg=COLORS['surface']
            ).pack(pady=50)
            return

        # NEW 2-ROW FILTER LAYOUT - ALWAYS AT TOP
        filter_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
        filter_frame.pack(side="top", anchor="n", pady=10 if is_small_screen else 15, fill="x",
                          padx=10 if is_small_screen else 20,
                          ipady=8 if is_small_screen else 12)

        # ROW 1: Back button, Department label, Transaction Type dropdown, Search field, Clear button
        row1_frame = tk.Frame(filter_frame, bg=COLORS['surface'])
        row1_frame.pack(fill="x", pady=(5, 8))

        # Back button
        back_text = "⬅️ Back" if is_small_screen else "⬅️ Back to Departments"
        tk.Button(
            row1_frame,
            text=back_text,
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=10 if is_small_screen else 15,
            pady=6 if is_small_screen else 8,
            command=show_head_office_images
        ).pack(side="left", padx=(5, 10))

        # Department label
        dept_text = f"🏢 {selected_dept}" if len(selected_dept) < 20 else f"🏢 {selected_dept[:17]}..."
        tk.Label(
            row1_frame,
            text=dept_text,
            font=("Segoe UI", get_font_size(10 if is_small_screen else 12), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(0, 15 if is_small_screen else 20))

        # Transaction type filter
        transaction_types = get_transaction_types_from_db(selected_dept)
        transaction_types = ["All"] + transaction_types
        trans_type_var = tk.StringVar(value="All")

        tk.Label(
            row1_frame,
            text="📋 Type:",
            font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(0, 5))

        trans_type_menu = tk.OptionMenu(row1_frame, trans_type_var, *transaction_types)
        menu_width = 12 if is_small_screen else 15
        trans_type_menu.config(
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary'],
            activeforeground='white',
            bd=1,
            relief="solid",
            width=menu_width
        )
        trans_type_menu["menu"].config(
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            activebackground=COLORS['secondary']
        )
        trans_type_menu.pack(side="left", padx=(0, 15 if is_small_screen else 20))

        # Search label and entry in same row
        tk.Label(
            row1_frame,
            text="🔍 Search:",
            font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(0, 5))

        # Search entry
        filename_search_var = tk.StringVar()
        search_width = 25 if is_small_screen else 30
        filename_search_entry = tk.Entry(
            row1_frame,
            textvariable=filename_search_var,
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            bd=1,
            relief="solid",
            width=search_width,
            insertbackground=COLORS['secondary']
        )
        filename_search_entry.pack(side="left", padx=(0, 5))

        # Placeholder text behavior
        placeholder_text = "Type filename to search..." if is_small_screen else "Type filename here to search..."

        def on_filename_focus_in(event):
            if filename_search_entry.get() == placeholder_text:
                filename_search_entry.delete(0, tk.END)
                filename_search_entry.config(fg=COLORS['text'])

        def on_filename_focus_out(event):
            if not filename_search_entry.get():
                filename_search_entry.insert(0, placeholder_text)
                filename_search_entry.config(fg=COLORS['muted'])

        filename_search_entry.insert(0, placeholder_text)
        filename_search_entry.config(fg=COLORS['muted'])
        filename_search_entry.bind("<FocusIn>", on_filename_focus_in)
        filename_search_entry.bind("<FocusOut>", on_filename_focus_out)

        # Clear button
        def clear_filename_search():
            filename_search_var.set("")
            filename_search_entry.config(fg=COLORS['muted'])
            filename_search_entry.delete(0, tk.END)
            filename_search_entry.insert(0, placeholder_text)
            apply_filters()

        clear_text = "❌ Clear" if is_small_screen else "❌ Clear Search"
        tk.Button(
            row1_frame,
            text=clear_text,
            font=("Segoe UI", get_font_size(8 if is_small_screen else 9), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=8 if is_small_screen else 12,
            pady=4 if is_small_screen else 6,
            command=clear_filename_search
        ).pack(side="left", padx=(3, 10))

        # ROW 2: Selection action buttons (Download Selected, Delete Selected) - Initially hidden
        row2_frame = tk.Frame(filter_frame, bg=COLORS['surface'])
        # Don't pack initially - will be shown when documents are selected

        # Pagination and selection variables
        documents_per_page = 8 if is_small_screen else 12
        current_page = [0]
        filtered_documents = []
        selected_documents = set()

        # Selection buttons (will be in row2_frame)
        download_text = "📥 Download Selected" if is_small_screen else "📥 Download Selected Documents"
        delete_text = "🗑️ Delete Selected" if is_small_screen else "🗑️ Delete Selected Documents"

        download_selected_btn = tk.Button(
            row2_frame,
            text=download_text,
            bg=COLORS['success'],
            fg="white",
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10), "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=12 if is_small_screen else 15,
            pady=6 if is_small_screen else 8
        )
        delete_selected_btn = tk.Button(
            row2_frame,
            text=delete_text,
            bg=COLORS['danger'],
            fg="white",
            font=("Segoe UI", get_font_size(9 if is_small_screen else 10), "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=12 if is_small_screen else 15,
            pady=6 if is_small_screen else 8
        )

        def update_selected_buttons():
            if selected_documents:
                # Show row2 with selection buttons
                row2_frame.pack(fill="x", pady=(0, 5))
                download_selected_btn.pack(side="left", padx=(10, 5))
                delete_selected_btn.pack(side="left", padx=5)

                # Update button text with count
                count = len(selected_documents)
                download_selected_btn.config(text=f"📥 Download ({count})")
                delete_selected_btn.config(text=f"🗑️ Delete ({count})")
            else:
                # Hide row2 when no documents selected
                row2_frame.pack_forget()

        def on_select(doc_id, var):
            if var.get():
                selected_documents.add(doc_id)
            else:
                selected_documents.discard(doc_id)
            update_selected_buttons()

        def download_selected_documents():
            if not selected_documents:
                messagebox.showinfo("No Selection", "No documents selected for download.")
                return
            folder = filedialog.askdirectory(title="Select Download Folder")
            if not folder:
                return
            success, failed = 0, 0
            for doc in filtered_documents:
                if doc["doc_id"] in selected_documents:
                    try:
                        url = doc.get("file_url")
                        fname = doc.get("file_name", "document.pdf")
                        if not fname.endswith('.pdf'):
                            fname += '.pdf'
                        response = requests.get(url, timeout=30)
                        if response.status_code == 200:
                            with open(f"{folder}/{fname}", "wb") as f:
                                f.write(response.content)
                            success += 1
                        else:
                            failed += 1
                    except:
                        failed += 1
            messagebox.showinfo("Download Complete", f"Downloaded: {success}, Failed: {failed}")

        def delete_selected_documents():
            if not selected_documents:
                messagebox.showinfo("No Selection", "No documents selected for deletion.")
                return

            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Delete {len(selected_documents)} documents?")
            if not confirm:
                return

            success, failed = 0, 0
            to_delete = [doc for doc in filtered_documents if doc["doc_id"] in selected_documents]

            for doc_data in to_delete:
                try:
                    # Delete from Firebase Storage
                    storage_path = doc_data.get("storage_path", "")
                    if storage_path:
                        try:
                            blob = bucket.blob(storage_path)
                            blob.delete()
                        except Exception as e:
                            print(f"⚠️ Failed to delete storage file: {e}")

                    # Delete from Firestore
                    db.collection("head_office_uploads").document(doc_data["doc_id"]).delete()
                    selected_documents.discard(doc_data["doc_id"])
                    success += 1
                except Exception as err:
                    print(f"🔥 Failed to delete: {err}")
                    failed += 1

            # Refresh the display
            apply_filters()
            messagebox.showinfo("Delete Complete", f"Deleted: {success}, Failed: {failed}")

        download_selected_btn.config(command=download_selected_documents)
        delete_selected_btn.config(command=delete_selected_documents)

        def matches(doc):
            # Transaction type filter
            ttype = trans_type_var.get().strip()
            if ttype != "All" and doc.get("transaction_type", "").strip() != ttype:
                return False

            # Filename search
            filename_query = filename_search_var.get().strip().lower()
            if filename_query and filename_query.lower() != placeholder_text.lower():
                doc_filename = doc.get("file_name", "").strip().lower()
                if filename_query not in doc_filename:
                    return False

            return True

        def apply_filters(*args):
            # Store current filter function for refresh
            current_filter_function[0] = apply_filters

            filtered = list(filter(matches, all_documents))

            # Sort by timestamp
            def get_doc_timestamp(doc):
                ts = doc.get("timestamp", "")
                try:
                    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except:
                    return datetime.datetime.min

            filtered.sort(key=get_doc_timestamp, reverse=True)

            filtered_documents.clear()
            filtered_documents.extend(filtered)
            current_page[0] = 0
            display_documents_page()

        def on_filename_search_change(*args):
            apply_filters()

        # Auto-apply filters when search or dropdown changes
        filename_search_var.trace_add("write", on_filename_search_change)
        trans_type_var.trace_add("write", on_filename_search_change)

        def display_documents_page():
            # Clear existing documents but keep filter frame
            for widget in scroll_frame.winfo_children():
                if widget != filter_frame:
                    widget.destroy()

            start = current_page[0] * documents_per_page
            end = start + documents_per_page
            page_documents = filtered_documents[start:end]

            # Search results info - always after filter frame
            search_query = filename_search_var.get().strip()
            if search_query and search_query.lower() != placeholder_text.lower():
                search_info_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
                search_info_frame.pack(side="top", anchor="n", fill="x", padx=10 if is_small_screen else 20,
                                       pady=(5, 8), ipady=6 if is_small_screen else 8)

                results_count = len(filtered_documents)
                search_text = f"🔍 '{search_query}': {results_count} found" if is_small_screen else f"🔍 Search results for '{search_query}': {results_count} documents found"

                tk.Label(
                    search_info_frame,
                    text=search_text,
                    font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold"),
                    bg=COLORS['surface'],
                    fg=COLORS['secondary']
                ).pack(padx=8 if is_small_screen else 10, pady=4 if is_small_screen else 5)

            # Select all checkbox - always after search info
            if page_documents:
                select_all_var = tk.BooleanVar(
                    value=all(doc["doc_id"] in selected_documents for doc in page_documents))

                def on_select_all():
                    if select_all_var.get():
                        for doc in page_documents:
                            selected_documents.add(doc["doc_id"])
                    else:
                        for doc in page_documents:
                            selected_documents.discard(doc["doc_id"])
                    update_selected_buttons()
                    display_documents_page()

                select_all_frame = tk.Frame(scroll_frame, bg=COLORS['surface'])
                select_all_frame.pack(side="top", anchor="n", fill="x", padx=10 if is_small_screen else 20,
                                      pady=(5, 8))

                select_all_text = "✓ Select All" if is_small_screen else "✓ Select All (this page)"
                tk.Checkbutton(
                    select_all_frame,
                    text=select_all_text,
                    variable=select_all_var,
                    command=on_select_all,
                    bg=COLORS['surface'],
                    fg=COLORS['text'],
                    font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold"),
                    activebackground=COLORS['surface'],
                    activeforeground=COLORS['secondary'],
                    selectcolor=COLORS['secondary'],
                    bd=0,
                    highlightthickness=0
                ).pack(anchor="w", padx=8 if is_small_screen else 10, pady=4 if is_small_screen else 5)

            # No documents message - centered only when no documents
            if not page_documents:
                # Create a container that will center the no documents message
                no_docs_container = tk.Frame(scroll_frame, bg=COLORS['surface'])
                no_docs_container.pack(fill="both", expand=True, padx=10 if is_small_screen else 20,
                                       pady=20 if is_small_screen else 30)

                no_docs_frame = tk.Frame(no_docs_container, bg=COLORS['surface'], relief="flat", bd=1)
                no_docs_frame.pack(expand=True, ipady=20 if is_small_screen else 30)

                tk.Label(
                    no_docs_frame,
                    text="📁 No documents found",
                    font=("Segoe UI", get_font_size(14 if is_small_screen else 16), "bold"),
                    fg=COLORS['muted'],
                    bg=COLORS['surface']
                ).pack()
                tk.Label(
                    no_docs_frame,
                    text="Try adjusting your filters",
                    font=("Segoe UI", get_font_size(10 if is_small_screen else 12)),
                    fg=COLORS['muted'],
                    bg=COLORS['surface']
                ).pack(pady=(5, 0))
                return

            def format_timestamp(ts):
                if not isinstance(ts, str):
                    ts = str(ts) if ts is not None else ""
                try:
                    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if is_small_screen:
                        return dt.strftime("%m/%d %H:%M")
                    else:
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    return ts

            # Display documents with responsive layout
            card_padding = 10 if is_small_screen else 20
            card_margin = 6 if is_small_screen else 8

            for doc in page_documents:
                card_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1,
                                      highlightbackground=COLORS['border'], highlightthickness=1)
                card_frame.pack(padx=card_padding, pady=card_margin, fill="x",
                                ipadx=10 if is_small_screen else 20,
                                ipady=10 if is_small_screen else 20)

                if is_small_screen:
                    # Vertical layout for small screens
                    card_frame.grid_columnconfigure(0, weight=1)

                    # Top section: PDF icon and basic info
                    top_section = tk.Frame(card_frame, bg=COLORS['surface'])
                    top_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
                    top_section.grid_columnconfigure(1, weight=1)

                    # PDF icon (smaller for mobile)
                    pdf_icon_label = tk.Label(
                        top_section,
                        text="📄",
                        font=("Segoe UI", get_font_size(20), "bold"),
                        bg=COLORS['surface'],
                        fg=COLORS['danger'],
                        width=4,
                        height=2
                    )
                    pdf_icon_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

                    # Basic info
                    basic_info_frame = tk.Frame(top_section, bg=COLORS['surface'])
                    basic_info_frame.grid(row=0, column=1, sticky="ew")

                    # Filename (truncated if too long)
                    filename_text = doc.get("file_name", "")
                    if len(filename_text) > 25:
                        filename_display = filename_text[:22] + "..."
                    else:
                        filename_display = filename_text

                    tk.Label(basic_info_frame, text=filename_display,
                             font=("Segoe UI", get_font_size(11), "bold"),
                             bg=COLORS['surface'], fg=COLORS['text'],
                             anchor="w").pack(anchor="w", fill="x")

                    # Department and type
                    dept_text = doc.get("department", "")[:15] + "..." if len(
                        doc.get("department", "")) > 15 else doc.get("department", "")
                    tk.Label(basic_info_frame, text=f"🏢 {dept_text}",
                             font=("Segoe UI", get_font_size(9)),
                             bg=COLORS['surface'], fg=COLORS['muted'],
                             anchor="w").pack(anchor="w", fill="x")

                    trans_type = doc.get("transaction_type", "")[:20] + "..." if len(
                        doc.get("transaction_type", "")) > 20 else doc.get("transaction_type", "")
                    tk.Label(basic_info_frame, text=f"💼 {trans_type}",
                             font=("Segoe UI", get_font_size(9)),
                             bg=COLORS['surface'], fg=COLORS['muted'],
                             anchor="w").pack(anchor="w", fill="x")

                    # Actions section
                    actions_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                    actions_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

                    # Checkbox on left
                    select_var = tk.BooleanVar(value=doc["doc_id"] in selected_documents)
                    tk.Checkbutton(actions_frame, text="Select", variable=select_var,
                                   command=lambda doc_id=doc["doc_id"], var=select_var: on_select(doc_id, var),
                                   bg=COLORS['surface'], fg=COLORS['text'],
                                   font=("Segoe UI", get_font_size(9), "bold"),
                                   activebackground=COLORS['surface'], selectcolor=COLORS['secondary'],
                                   bd=0, highlightthickness=0).pack(side="left")

                    # View button on right
                    tk.Button(actions_frame,
                              text="👁️ View", font=("Segoe UI", get_font_size(9), "bold"),
                              bg=COLORS['accent'], fg="white",
                              bd=0, relief="flat", cursor="hand2", padx=10, pady=4,
                              command=lambda data=doc: view_pdf(data)).pack(side="right")

                    # Upload info (smaller text)
                    uploaded_by = doc.get("uploaded_by", "")[:15] + "..." if len(
                        doc.get("uploaded_by", "")) > 15 else doc.get("uploaded_by", "")
                    upload_info = f"👤 {uploaded_by} • ⏰ {format_timestamp(doc.get('timestamp', ''))}"
                    tk.Label(actions_frame, text=upload_info,
                             font=("Segoe UI", get_font_size(8)),
                             bg=COLORS['surface'], fg=COLORS['muted']).pack(side="left", padx=(20, 0))

                else:
                    # Horizontal layout for larger screens (original design)
                    card_frame.grid_columnconfigure(1, weight=1)

                    # PDF icon
                    pdf_icon_label = tk.Label(
                        card_frame,
                        text="📄\nPDF",
                        font=("Segoe UI", get_font_size(16), "bold"),
                        bg=COLORS['surface'],
                        fg=COLORS['danger'],
                        width=10,
                        height=4,
                        borderwidth=2,
                        relief="solid"
                    )
                    pdf_icon_label.grid(row=0, column=0, padx=15, pady=10, sticky="nw")

                    # Info section
                    info_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                    info_frame.grid(row=0, column=1, padx=15, sticky="nsew")

                    # File info
                    filename_text = doc.get("file_name", "")
                    search_query = filename_search_var.get().strip().lower()
                    if search_query and search_query.lower() != placeholder_text.lower() and search_query in filename_text.lower():
                        filename_display = f"📄 {filename_text} ⭐"
                        filename_color = COLORS['success']
                    else:
                        filename_display = filename_text
                        filename_color = COLORS['muted']

                    info_data = [
                        ("📄 File", filename_display, filename_color),
                        ("🏢 Department", doc.get("department", ""), COLORS['muted']),
                        ("👤 Uploaded By", doc.get("uploaded_by", ""), COLORS['muted']),
                        ("💼 Transaction Type", doc.get("transaction_type", ""), COLORS['muted']),
                        ("⏰ Date Uploaded", format_timestamp(doc.get("timestamp", "")), COLORS['muted']),
                    ]

                    for label, val, text_color in info_data:
                        row = tk.Frame(info_frame, bg=COLORS['surface'])
                        row.pack(anchor="w", pady=3, fill="x")

                        tk.Label(row, text=f"{label}:", font=("Segoe UI", 10, "bold"),
                                 bg=COLORS['surface'], fg=COLORS['text'], width=18, anchor="w").pack(side="left")
                        tk.Label(row, text=val, font=("Segoe UI", 10, "bold" if "⭐" in str(val) else "normal"),
                                 bg=COLORS['surface'], fg=text_color, anchor="w", wraplength=400).pack(side="left")

                    # Actions
                    actions_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                    actions_frame.grid(row=0, column=2, padx=15, pady=10, sticky="ne")

                    select_var = tk.BooleanVar(value=doc["doc_id"] in selected_documents)
                    tk.Checkbutton(actions_frame, text="Select", variable=select_var,
                                   command=lambda doc_id=doc["doc_id"], var=select_var: on_select(doc_id, var),
                                   bg=COLORS['surface'], fg=COLORS['text'], font=("Segoe UI", 10, "bold"),
                                   activebackground=COLORS['surface'], selectcolor=COLORS['secondary'],
                                   bd=0, highlightthickness=0).pack(pady=(0, 5))

                    tk.Button(actions_frame,
                              text="👁️ View PDF", font=("Segoe UI", 9, "bold"), bg=COLORS['accent'], fg="white",
                              bd=0, relief="flat", cursor="hand2", padx=12, pady=6,
                              command=lambda data=doc: view_pdf(data)).pack()

           
            nav_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
            nav_frame.pack(pady=10 if is_small_screen else 15,
                           padx=10 if is_small_screen else 20, fill="x",
                           ipady=8 if is_small_screen else 10)

            def go_page(direction):
                current_page[0] += direction
                display_documents_page()


            prev_text = "⬅️" if is_small_screen else "⬅️ Previous"
            prev_btn = tk.Button(nav_frame, text=prev_text,
                                 state="normal" if current_page[0] > 0 else "disabled",
                                 bg=COLORS['secondary'] if current_page[0] > 0 else COLORS['primary'],
                                 fg="white", font=("Segoe UI", get_font_size(9 if is_small_screen else 10), "bold"),
                                 bd=0, relief="flat",
                                 cursor="hand2", padx=12 if is_small_screen else 20,
                                 pady=6 if is_small_screen else 8,
                                 command=lambda: go_page(-1))
            prev_btn.pack(side="left", padx=(5 if is_small_screen else 10, 3 if is_small_screen else 5))

     
            total_pages = max(1, (len(filtered_documents) - 1) // documents_per_page + 1)
            page_text = f"{current_page[0] + 1}/{total_pages}" if is_small_screen else f"Page {current_page[0] + 1} of {total_pages}"
            tk.Label(nav_frame,
                     text=page_text,
                     bg=COLORS['surface'], fg=COLORS['text'],
                     font=("Segoe UI", get_font_size(10 if is_small_screen else 11), "bold")).pack(side="left",
                                                                                                   padx=10 if is_small_screen else 20)

      
            next_text = "➡️" if is_small_screen else "Next ➡️"
            next_btn = tk.Button(nav_frame, text=next_text,
                                 state="normal" if end < len(filtered_documents) else "disabled",
                                 bg=COLORS['secondary'] if end < len(filtered_documents) else COLORS['primary'],
                                 fg="white", font=("Segoe UI", get_font_size(9 if is_small_screen else 10), "bold"),
                                 bd=0, relief="flat",
                                 cursor="hand2", padx=12 if is_small_screen else 20,
                                 pady=6 if is_small_screen else 8,
                                 command=lambda: go_page(1))
            next_btn.pack(side="left", padx=(3 if is_small_screen else 5, 5 if is_small_screen else 10))


        apply_filters()


    show_head_office_images()


    def close_popup():
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", close_popup)