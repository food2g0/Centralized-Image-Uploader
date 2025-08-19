import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import time
import datetime
from threading import Thread
from firebase_config import storage, db  
from firebase_admin import firestore
from Colors import COLORS
from corporations import CORPORATIONS, DEPARTMENT_CONFIG



ALLOWED_EXTENSIONS = ".pdf"
MAX_FILE_SIZE = 100 * 1024 * 1024



class DepartmentTransactionManager:
    """Centralized manager for department-specific transaction types"""

    @staticmethod
    def get_departments():
        """Get list of all departments"""
        return list(DEPARTMENT_CONFIG.keys())

    @staticmethod
    def get_transactions(department):
        """Get transaction types for a specific department"""
        return DEPARTMENT_CONFIG.get(department, {}).get("transactions", [])

    @staticmethod
    def get_sub_categories(department, transaction):
        """Get sub-categories for a specific transaction type"""
        dept_config = DEPARTMENT_CONFIG.get(department, {})
        return dept_config.get("sub_categories", {}).get(transaction, [])

    @staticmethod
    def has_sub_categories(department, transaction):
        """Check if a transaction type has sub-categories"""
        return len(DepartmentTransactionManager.get_sub_categories(department, transaction)) > 0

    @staticmethod
    def get_department_icon(department):
        """Get icon for department"""
        return DEPARTMENT_CONFIG.get(department, {}).get("icon", "📁")

    @staticmethod
    def validate_transaction(department, transaction, sub_category=None):
        """Validate if a transaction is valid for the department"""
        valid_transactions = DepartmentTransactionManager.get_transactions(department)
        if transaction not in valid_transactions:
            return False

        if sub_category:
            valid_subs = DepartmentTransactionManager.get_sub_categories(department, transaction)
            return sub_category in valid_subs

        return True

    @staticmethod
    def get_corporations():
        """Get list of all corporations"""
        return CORPORATIONS


def create_modern_button(parent, text, command, bg_color, hover_color=None, width=None):
    """Create a modern styled button with hover effects"""
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg='white',
        font=('Segoe UI', 10, 'bold'),
        relief='flat',
        cursor='hand2',
        padx=20,
        pady=8,
        width=width
    )

    if hover_color:
        def on_enter(e):
            button.config(bg=hover_color)

        def on_leave(e):
            button.config(bg=bg_color)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    return button


def create_styled_frame(parent, bg_color=COLORS['white'], relief='flat', bd=1):
    """Create a styled frame with modern appearance"""
    frame = tk.Frame(parent, bg=bg_color, relief=relief, bd=bd)
    return frame


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def setup_corporation_filtering(combobox, all_corporations, corporation_var):
    """
    Setup letter-based filtering for corporation dropdown
    
    Args:
        combobox: The ttk.Combobox widget
        all_corporations: List of all corporation names
        corporation_var: The StringVar connected to the combobox
    """
    def filter_corporations(event):
        """Filter based on typed letters"""
        typed_text = combobox.get().upper()
        
        if not typed_text:
            combobox['values'] = all_corporations
            return
            
        # Filter corporations starting with typed letters
        filtered = [corp for corp in all_corporations 
                   if corp.upper().startswith(typed_text)]
        
        combobox['values'] = filtered
        
        # Show dropdown if there are matches
        if filtered:
            try:
                combobox.event_generate('<Down>')
            except:
                pass  # Ignore if dropdown can't be opened
    
    def reset_corporations(event):
        """Reset to show all corporations"""
        combobox['values'] = all_corporations
    
    def on_selection(event):
        """Handle corporation selection"""
        combobox['values'] = all_corporations
    
    # Bind the filtering events
    combobox.bind('<KeyRelease>', filter_corporations)
    combobox.bind('<FocusOut>', reset_corporations)
    combobox.bind('<<ComboboxSelected>>', on_selection)


def open_head_office_dashboard(next_user_data):
    """
    Simplified Head Office upload dashboard
    Automatically sets department based on user's department field
    """
    # Initialize department manager
    dept_manager = DepartmentTransactionManager()

    # Get user's department from the database
    user_department = next_user_data.get('department', '')
    username = next_user_data.get('username', 'Unknown User')

    # Store selected files
    selected_files = []

    def add_files():
        file_paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[
                ("All Supported", "*.pdf"),
                ("Documents", "*.pdf;"),
            ]
        )

        for file_path in file_paths:
            if file_path not in [f['path'] for f in selected_files]:
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    messagebox.showwarning("Invalid File",
                                           f"File type {ext} not allowed for:\n{os.path.basename(file_path)}")
                    continue

                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE:
                    messagebox.showwarning("File Too Large",
                                           f"File exceeds 100MB limit:\n{os.path.basename(file_path)}")
                    continue

                selected_files.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size': file_size,
                    'status': 'pending'
                })

        update_file_list()

    def remove_file(index):
        if 0 <= index < len(selected_files):
            selected_files.pop(index)
            update_file_list()

    def clear_all_files():
        selected_files.clear()
        update_file_list()

    def update_file_list():
        # Clear existing file widgets
        for widget in file_list_frame.winfo_children():
            widget.destroy()

        if not selected_files:
            no_files_label = tk.Label(
                file_list_frame,
                text="📂 No files selected\nClick 'Add Files' to select documents",
                font=('Segoe UI', 10),
                bg=COLORS['light'],
                fg=COLORS['text_light'],
                justify='center'
            )
            no_files_label.pack(expand=True, fill='both', pady=20)
            files_info_label.config(text="0 files selected")
            return

        # Create scrollable frame for file list
        for widget in file_list_frame.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(file_list_frame, bg=COLORS['light'], highlightthickness=0, height=180)
        scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

        # Add files to scrollable frame
        for i, file_info in enumerate(selected_files):
            file_frame = create_styled_frame(scrollable_frame, COLORS['white'], relief='solid', bd=1)
            file_frame.pack(fill='x', padx=2, pady=2)

            info_frame = create_styled_frame(file_frame, COLORS['white'])
            info_frame.pack(side='left', fill='both', expand=True, padx=8, pady=4)

            status_color = COLORS['text'] if file_info['status'] == 'pending' else \
                COLORS['success'] if file_info['status'] == 'uploaded' else \
                    COLORS['warning'] if file_info['status'] == 'uploading' else \
                        COLORS['danger']

            status_icon = "📄" if file_info['status'] == 'pending' else \
                "✅" if file_info['status'] == 'uploaded' else \
                    "⏳" if file_info['status'] == 'uploading' else \
                        "❌"

            display_name = file_info['name']
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."

            name_label = tk.Label(
                info_frame,
                text=f"{status_icon} {display_name}",
                font=('Segoe UI', 9, 'bold'),
                bg=COLORS['white'],
                fg=status_color,
                anchor='w'
            )
            name_label.pack(fill='x')

            size_label = tk.Label(
                info_frame,
                text=f"{format_file_size(file_info['size'])} • {file_info['status'].title()}",
                font=('Segoe UI', 8),
                bg=COLORS['white'],
                fg=COLORS['text_light'],
                anchor='w'
            )
            size_label.pack(fill='x')

            if file_info['status'] == 'pending':
                remove_btn = tk.Button(
                    file_frame,
                    text="×",
                    command=lambda idx=i: remove_file(idx),
                    bg=COLORS['danger'],
                    fg='white',
                    font=('Segoe UI', 10, 'bold'),
                    relief='flat',
                    cursor='hand2',
                    width=2,
                    height=1
                )
                remove_btn.pack(side='right', padx=4, pady=4)

        canvas.pack(side="left", fill="both", expand=True)
        if len(selected_files) > 6:
            scrollbar.pack(side="right", fill="y")

        total_files = len(selected_files)
        total_size = sum(f['size'] for f in selected_files)
        files_info_label.config(
            text=f"{total_files} file{'s' if total_files != 1 else ''} selected | Total: {format_file_size(total_size)}"
        )

    def on_transaction_change(event=None):
        """Handle transaction type selection change"""
        selected_transaction = transaction_type_var.get()

        # Clear sub-category
        sub_category_var.set("")

        if user_department and selected_transaction:
            # Check if this transaction has sub-categories
            if dept_manager.has_sub_categories(user_department, selected_transaction):
                # Get sub-categories and show the section
                sub_categories = dept_manager.get_sub_categories(user_department, selected_transaction)
                sub_category_dropdown['values'] = sub_categories

                # Update label to be more specific
                sub_category_label.config(text=f"📚 {selected_transaction} Type")

                # Show the sub-category section
                sub_category_section.pack(fill='x', pady=(0, 15), padx=5, after=trans_section)
            else:
                # Hide the sub-category section
                sub_category_section.pack_forget()
        else:
            sub_category_section.pack_forget()

    def validate_inputs():
        """Enhanced validation with corporation filtering support"""
        errors = []

        if not selected_files:
            errors.append("Please select at least one file")

        selected_corp = corporation_var.get().strip()  # Add strip() to handle spaces
        selected_transaction = transaction_type_var.get()
        selected_sub = sub_category_var.get()
        uploaded_by = uploaded_by_var.get().strip()

        if not selected_corp:
            errors.append("Please select a corporation")
        elif selected_corp not in dept_manager.get_corporations():
            # Check if it's a partial match or invalid
            matching_corps = [corp for corp in dept_manager.get_corporations() 
                             if corp.upper().startswith(selected_corp.upper())]
            if matching_corps:
                errors.append(f"Please select a complete corporation name from the dropdown")
            else:
                errors.append("Invalid corporation selected")

        if not selected_transaction:
            errors.append("Please select a transaction type")
        elif not dept_manager.validate_transaction(user_department, selected_transaction):
            errors.append(f"Invalid transaction type for {user_department}")
        elif dept_manager.has_sub_categories(user_department, selected_transaction) and not selected_sub:
            errors.append(f"Please select a {selected_transaction} type")
        elif selected_sub and not dept_manager.validate_transaction(user_department, selected_transaction,
                                                                    selected_sub):
            errors.append(f"Invalid sub-category for {selected_transaction}")

        if not uploaded_by:
            errors.append("Please enter who is uploading the documents")
        elif len(uploaded_by) < 2:
            errors.append("Uploaded by name must be at least 2 characters")

        return errors

    def upload_files():
        # Validate inputs
        errors = validate_inputs()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(f"• {error}" for error in errors))
            return

        corporation = corporation_var.get().strip()
        transaction_type = transaction_type_var.get()
        sub_category = sub_category_var.get()
        uploaded_by = uploaded_by_var.get().strip()
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Combine transaction type with sub-category if applicable
        final_transaction_type = f"{transaction_type} - {sub_category}" if sub_category else transaction_type

        def do_upload():
            try:
                upload_btn.config(state='disabled', text='Uploading...', bg=COLORS['secondary'])
                clear_btn.config(state='disabled')

                total_files = len(selected_files)
                uploaded_files = []
                failed_files = []

                for i, file_info in enumerate(selected_files):
                    try:
                        file_info['status'] = 'uploading'
                        progress = int((i / total_files) * 80)
                        progress_var.set(progress)
                        status_label.config(
                            text=f"Uploading {file_info['name']} ({i + 1}/{total_files})...",
                            fg=COLORS['primary']
                        )
                        popup.update_idletasks()
                        update_file_list()

                        timestamp = int(time.time())
                        file_name = f"{current_date}_{timestamp}_{i}_{file_info['name']}"
                        storage_path = f"Head Office/{file_name}"

                        storage.child(storage_path).put(file_info['path'])
                        file_url = storage.child(storage_path).get_url(None)

                        doc_ref = db.collection("head_office_uploads").add({
                            "corporation": corporation,
                            "department": user_department,  # Automatically use user's department
                            "transaction_type": final_transaction_type,
                            "uploaded_by": uploaded_by,  # User-entered name
                            "upload_date": current_date,
                            "file_name": file_info['name'],
                            "file_url": file_url,
                            "file_size": file_info['size'],
                            "upload_batch": timestamp,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })

                        file_info['status'] = 'uploaded'
                        uploaded_files.append(file_info['name'])

                    except Exception as e:
                        file_info['status'] = 'failed'
                        failed_files.append(f"{file_info['name']}: {str(e)}")

                progress_var.set(100)
                update_file_list()

                # Show results based on upload success
                if uploaded_files and not failed_files:
                    status_label.config(
                        text=f"✅ Successfully uploaded {len(uploaded_files)} file{'s' if len(uploaded_files) != 1 else ''}!",
                        fg=COLORS['success']
                    )
                    messagebox.showinfo("Upload Complete", f"Successfully uploaded {len(uploaded_files)} documents!")

                    # Reset form on complete success
                    selected_files.clear()
                    corporation_var.set("")
                    transaction_type_var.set("")
                    sub_category_var.set("")
                    uploaded_by_var.set("")
                    progress_var.set(0)
                    update_file_list()
                    status_label.config(text="Ready to upload", fg=COLORS['text_light'])
                    sub_category_section.pack_forget()

                elif uploaded_files and failed_files:
                    status_label.config(
                        text=f"⚠️ {len(uploaded_files)} uploaded, {len(failed_files)} failed",
                        fg=COLORS['warning']
                    )
                    messagebox.showwarning(
                        "Partial Upload",
                        f"Uploaded: {len(uploaded_files)} files\nFailed: {len(failed_files)} files"
                    )
                else:
                    status_label.config(text="❌ All uploads failed", fg=COLORS['danger'])
                    messagebox.showerror("Upload Failed", "All file uploads failed")

            except Exception as e:
                progress_var.set(0)
                status_label.config(text="❌ Upload failed", fg=COLORS['danger'])
                messagebox.showerror("Upload Error", f"Unexpected error: {str(e)}")
            finally:
                upload_btn.config(state='normal', text='🚀 Upload All Files', bg=COLORS['primary'])
                clear_btn.config(state='normal')

        Thread(target=do_upload).start()

    # Create main window
    popup = tk.Tk()
    popup.title(f"📤 {user_department} - Document Upload")
    popup.geometry("600x750")
    popup.configure(bg=COLORS['light'])
    popup.resizable(True, False)

    # Center the window
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

    # Variables
    corporation_var = tk.StringVar()
    transaction_type_var = tk.StringVar()
    sub_category_var = tk.StringVar()
    uploaded_by_var = tk.StringVar()
    progress_var = tk.IntVar(value=0)

    # Main container
    main_frame = create_styled_frame(popup, COLORS['white'])
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Header
    header_frame = create_styled_frame(main_frame, COLORS['primary'])
    header_frame.pack(fill='x', pady=(0, 20))

    dept_icon = dept_manager.get_department_icon(user_department)
    header_label = tk.Label(
        header_frame,
        text=f"{dept_icon} {user_department} - Document Upload",
        font=('Segoe UI', 16, 'bold'),
        bg=COLORS['primary'],
        fg='white',
        pady=15
    )
    header_label.pack()

    # User info display
    user_info_frame = create_styled_frame(main_frame, COLORS['light'], relief='solid', bd=1)
    user_info_frame.pack(fill='x', pady=(0, 15), padx=5)

    tk.Label(
        user_info_frame,
        text=f"👤 User: {username} | 🏢 Department: {user_department}",
        font=('Segoe UI', 10, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        pady=10
    ).pack()

    # Form container with scrollable area
    form_container = create_styled_frame(main_frame)
    form_container.pack(fill='both', expand=True, padx=10)

    form_canvas = tk.Canvas(form_container, bg=COLORS['white'], highlightthickness=0)
    form_scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=form_canvas.yview)
    form_frame = tk.Frame(form_canvas, bg=COLORS['white'])

    form_frame.bind(
        "<Configure>",
        lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all"))
    )

    form_canvas.create_window((0, 0), window=form_frame, anchor="nw")
    form_canvas.configure(yscrollcommand=form_scrollbar.set)

    def on_form_mousewheel(event):
        form_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    form_canvas.bind("<MouseWheel>", on_form_mousewheel)

    form_canvas.pack(side="left", fill="both", expand=True)
    form_scrollbar.pack(side="right", fill="y")

    # Corporation section with filtering
    corp_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    corp_section.pack(fill='x', pady=(0, 15), padx=5)

    corp_label = tk.Label(
        corp_section,
        text="🏢 Corporation (Type letters to filter)",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    )
    corp_label.pack(fill='x', padx=15, pady=(15, 5))

    # Get all corporations
    all_corporations = dept_manager.get_corporations()
    
    corporation_dropdown = ttk.Combobox(
        corp_section,
        textvariable=corporation_var,
        font=('Segoe UI', 10),
        values=all_corporations,
        state="normal"  # Changed from readonly to normal to allow typing
    )
    corporation_dropdown.pack(fill='x', padx=15, pady=(0, 10))
    
    # Setup filtering functionality
    setup_corporation_filtering(corporation_dropdown, all_corporations, corporation_var)
    
    # Helper text for corporation
    corp_helper_label = tk.Label(
        corp_section,
        text="💡 Start typing to filter corporations by first letters (e.g., type 'A' to show all corps starting with 'A')",
        font=('Segoe UI', 8),
        bg=COLORS['light'],
        fg=COLORS['text_light'],
        anchor='w'
    )
    corp_helper_label.pack(fill='x', padx=15, pady=(0, 15))

    # Transaction Type section
    trans_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    trans_section.pack(fill='x', pady=(0, 15), padx=5)

    trans_label = tk.Label(
        trans_section,
        text=f"📋 {user_department.replace(' Department', '')} Transaction Type",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    )
    trans_label.pack(fill='x', padx=15, pady=(15, 5))

    # Set transaction types based on user's department
    dept_transactions = dept_manager.get_transactions(user_department)
    transaction_dropdown = ttk.Combobox(
        trans_section,
        textvariable=transaction_type_var,
        state="readonly",
        font=('Segoe UI', 10),
        values=dept_transactions
    )
    transaction_dropdown.pack(fill='x', padx=15, pady=(0, 15))
    transaction_dropdown.bind('<<ComboboxSelected>>', on_transaction_change)

    # Sub-category section (initially hidden)
    sub_category_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)

    sub_category_label = tk.Label(
        sub_category_section,
        text="📚 Sub-Category",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    )
    sub_category_label.pack(fill='x', padx=15, pady=(15, 5))

    sub_category_dropdown = ttk.Combobox(
        sub_category_section,
        textvariable=sub_category_var,
        state="readonly",
        font=('Segoe UI', 10),
        values=[]
    )
    sub_category_dropdown.pack(fill='x', padx=15, pady=(0, 15))

    # Uploaded By section
    uploaded_by_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    uploaded_by_section.pack(fill='x', pady=(0, 15), padx=5)

    tk.Label(
        uploaded_by_section,
        text="👤 Uploaded By",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))

    uploaded_by_entry = tk.Entry(
        uploaded_by_section,
        textvariable=uploaded_by_var,
        font=('Segoe UI', 10),
        relief='solid',
        bd=1,
        bg=COLORS['white'],
        fg=COLORS['text']
    )
    uploaded_by_entry.pack(fill='x', padx=15, pady=(0, 10))

    # Add placeholder text functionality
    def on_focus_in(event):
        if uploaded_by_entry.get() == "Enter your name":
            uploaded_by_entry.delete(0, tk.END)
            uploaded_by_entry.config(fg=COLORS['text'])

    def on_focus_out(event):
        if uploaded_by_entry.get() == "":
            uploaded_by_entry.insert(0, "Enter your name")
            uploaded_by_entry.config(fg=COLORS['text_light'])

    # Set initial placeholder
    uploaded_by_entry.insert(0, "Enter your name")
    uploaded_by_entry.config(fg=COLORS['text_light'])
    uploaded_by_entry.bind('<FocusIn>', on_focus_in)
    uploaded_by_entry.bind('<FocusOut>', on_focus_out)

    # Helper text
    helper_label = tk.Label(
        uploaded_by_section,
        text="💡 Enter the name of the person uploading these documents",
        font=('Segoe UI', 8),
        bg=COLORS['light'],
        fg=COLORS['text_light'],
        anchor='w'
    )
    helper_label.pack(fill='x', padx=15, pady=(0, 15))

    # File section
    file_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    file_section.pack(fill='x', pady=(0, 15), padx=5)

    file_header_frame = create_styled_frame(file_section, COLORS['light'])
    file_header_frame.pack(fill='x', padx=15, pady=(15, 5))

    tk.Label(
        file_header_frame,
        text="📎 Document Files",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(side='left')

    files_info_label = tk.Label(
        file_header_frame,
        text="0 files selected",
        font=('Segoe UI', 9),
        bg=COLORS['light'],
        fg=COLORS['text_light'],
        anchor='e'
    )
    files_info_label.pack(side='right')

    # File management buttons
    file_btn_frame = create_styled_frame(file_section, COLORS['light'])
    file_btn_frame.pack(fill='x', padx=15, pady=(0, 10))

    add_files_btn = create_modern_button(
        file_btn_frame,
        "📁 Add Files",
        add_files,
        COLORS['success'],
        COLORS['success'],
        width=12
    )
    add_files_btn.pack(side='left')

    clear_btn = create_modern_button(
        file_btn_frame,
        "🗑️ Clear All",
        clear_all_files,
        COLORS['warning'],
        width=10
    )
    clear_btn.pack(side='left', padx=(10, 0))

    # File list container
    file_list_container = create_styled_frame(file_section, COLORS['light'])
    file_list_container.pack(fill='x', padx=15, pady=(0, 10))
    file_list_container.configure(height=200)

    file_list_frame = create_styled_frame(file_list_container, COLORS['light'])
    file_list_frame.pack(fill='both', expand=True)

    # Supported formats info
    formats_label = tk.Label(
        file_section,
        text="💡 Supported: PDF (Max 100MB per file)",
        font=('Segoe UI', 8),
        bg=COLORS['light'],
        fg=COLORS['text_light'],
        anchor='w'
    )
    formats_label.pack(fill='x', padx=15, pady=(0, 15))

    # Progress section
    progress_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    progress_section.pack(fill='x', pady=(0, 15), padx=5)

    tk.Label(
        progress_section,
        text="📊 Upload Progress",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))

    progress_bar = ttk.Progressbar(
        progress_section,
        variable=progress_var,
        maximum=100,
        style='TProgressbar'
    )
    progress_bar.pack(fill='x', padx=15, pady=(0, 10))

    status_label = tk.Label(
        progress_section,
        text="Ready to upload",
        font=('Segoe UI', 9),
        bg=COLORS['light'],
        fg=COLORS['text_light'],
        anchor='w'
    )
    status_label.pack(fill='x', padx=15, pady=(0, 15))

    # Button section
    button_frame = create_styled_frame(main_frame)
    button_frame.pack(fill='x', pady=(20, 0))

    upload_btn = create_modern_button(
        button_frame,
        "🚀 Upload All Files",
        upload_files,
        COLORS['primary'],
        COLORS['primary_hover'],
        width=18
    )
    upload_btn.pack(side='left', padx=(0, 10))

    def logout_and_exit():
        """Logout and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            popup.destroy()
            try:
                import login_gui
                login_gui.main()
            except Exception as e:
                print(f"Error restarting login: {e}")

    logout_btn = create_modern_button(
        button_frame,
        "🚪 Logout",
        logout_and_exit,
        COLORS['danger'],
        width=12
    )
    logout_btn.pack(side='right')

    # Configure ttk styles
    style = ttk.Style()
    style.configure('TProgressbar', thickness=20)

    # Initialize file list
    update_file_list()

    # Show validation message if user department is not configured
    if user_department not in DEPARTMENT_CONFIG:
        messagebox.showwarning(
            "Department Not Configured",
            f"The department '{user_department}' is not configured in the system.\n"
            "Please contact the administrator to add transaction types for your department."
        )

    print(f"[head_office_upload] Upload dashboard opened for {username} - {user_department}")

    popup.mainloop()


# Main function to be called from login
def main(next_user_data):
 
    try:
        # Validate user data
        if not next_user_data:
            messagebox.showerror("Error", "No user data provided")
            return

        if 'department' not in next_user_data:
            messagebox.showerror("Error", "User department not specified")
            return

        if 'username' not in next_user_data:
            messagebox.showerror("Error", "Username not specified")
            return

        # Open the upload dashboard
        open_head_office_dashboard(next_user_data)

    except Exception as e:
        print(f"[head_office_upload] Error opening upload dashboard: {e}")
        messagebox.showerror("Dashboard Error", f"Failed to open upload dashboard: {e}")


if __name__ == "__main__":
    # Test data - remove this in production
    test_next_user_data = {
        "username": "IT DEPT",
        "department": "IT Department",
        "password": "123456"
    }
    main(test_next_user_data)