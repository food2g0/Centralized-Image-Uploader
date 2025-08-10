import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import os
import time
import datetime
from threading import Thread
from firebase_config import storage, db  # pyrebase storage, firebase_admin db
from firebase_admin import firestore

# Allowed file types
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".pdf", ".docx")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Color scheme
COLORS = {
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'secondary': '#64748b',
    'success': '#059669',
    'danger': '#dc2626',
    'warning': '#d97706',
    'light': '#f8fafc',
    'white': '#ffffff',
    'dark': '#1e293b',
    'border': '#e2e8f0',
    'text': '#334155',
    'text_light': '#64748b'
}

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
    
    # Add hover effects
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
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def open_head_office_popup(parent_admin):
    # Store selected files
    selected_files = []
    
    def add_files():
        file_paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[
                ("All Supported", "*.jpg;*.jpeg;*.png;*.pdf;*.docx"),
                ("Images", "*.jpg;*.jpeg;*.png"),
                ("Documents", "*.pdf;*.docx"),
                ("All Files", "*.*")
            ]
        )
        
        for file_path in file_paths:
            if file_path not in [f['path'] for f in selected_files]:
                # Validate file
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    messagebox.showwarning("Invalid File", f"File type {ext} not allowed for:\n{os.path.basename(file_path)}")
                    continue
                
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE:
                    messagebox.showwarning("File Too Large", f"File exceeds 50MB limit:\n{os.path.basename(file_path)}")
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
            # Clear any existing canvas/scrollbar
            for widget in file_list_frame.winfo_children():
                widget.destroy()
                
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

        # Clear existing widgets
        for widget in file_list_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame for file list with fixed height
        canvas = tk.Canvas(file_list_frame, bg=COLORS['light'], highlightthickness=0, height=180)
        scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Add files to scrollable frame
        for i, file_info in enumerate(selected_files):
            file_frame = create_styled_frame(scrollable_frame, COLORS['white'], relief='solid', bd=1)
            file_frame.pack(fill='x', padx=2, pady=2)
            
            # File info section
            info_frame = create_styled_frame(file_frame, COLORS['white'])
            info_frame.pack(side='left', fill='both', expand=True, padx=8, pady=4)
            
            # File name and status
            status_color = COLORS['text'] if file_info['status'] == 'pending' else \
                          COLORS['success'] if file_info['status'] == 'uploaded' else \
                          COLORS['warning'] if file_info['status'] == 'uploading' else \
                          COLORS['danger']
            
            status_icon = "📄" if file_info['status'] == 'pending' else \
                         "✅" if file_info['status'] == 'uploaded' else \
                         "⏳" if file_info['status'] == 'uploading' else \
                         "❌"
            
            # Truncate long file names
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
            
            # Remove button (only for pending files)
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
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        if len(selected_files) > 6:  # Show scrollbar only when needed
            scrollbar.pack(side="right", fill="y")
        
        # Update file count
        total_files = len(selected_files)
        total_size = sum(f['size'] for f in selected_files)
        files_info_label.config(
            text=f"{total_files} file{'s' if total_files != 1 else ''} selected | Total: {format_file_size(total_size)}"
        )

    def validate_inputs():
        """Validate all inputs before upload"""
        errors = []
        
        if not selected_files:
            errors.append("Please select at least one file")
        if not department_var.get():
            errors.append("Please select a department")
        if not transaction_type_var.get():
            errors.append("Please select a transaction type")
            
        return errors

    def upload_files():
        # Validate inputs
        errors = validate_inputs()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(f"• {error}" for error in errors))
            return

        department = department_var.get()
        transaction_type = transaction_type_var.get()
        date_val = date_entry.get_date().strftime("%Y-%m-%d")

        def do_upload():
            try:
                # Disable upload button during upload
                upload_btn.config(state='disabled', text='Uploading...', bg=COLORS['secondary'])
                clear_btn.config(state='disabled')
                
                total_files = len(selected_files)
                uploaded_files = []
                failed_files = []
                
                for i, file_info in enumerate(selected_files):
                    try:
                        # Update status
                        file_info['status'] = 'uploading'
                        progress = int((i / total_files) * 80)  # Reserve 20% for final steps
                        progress_var.set(progress)
                        status_label.config(
                            text=f"Uploading {file_info['name']} ({i+1}/{total_files})...", 
                            fg=COLORS['primary']
                        )
                        popup.update_idletasks()
                        update_file_list()
                        
                        # Firebase path
                        timestamp = int(time.time())
                        file_name = f"{date_val}_{timestamp}_{i}_{file_info['name']}"
                        storage_path = f"Head Office/{file_name}"
                        
                        # Upload to Firebase Storage
                        storage.child(storage_path).put(file_info['path'])
                        
                        # Get public URL
                        file_url = storage.child(storage_path).get_url(None)
                        
                        # Save to Firestore
                        doc_ref = db.collection("head_office_uploads").add({
                            "department": department,
                            "transaction_type": transaction_type,
                            "date": date_val,
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
                
                # Final progress
                progress_var.set(100)
                update_file_list()
                
                # Show results
                if uploaded_files and not failed_files:
                    status_label.config(
                        text=f"✅ Successfully uploaded {len(uploaded_files)} file{'s' if len(uploaded_files) != 1 else ''}!", 
                        fg=COLORS['success']
                    )
                    messagebox.showinfo("Upload Complete", f"Successfully uploaded {len(uploaded_files)} documents!")
                elif uploaded_files and failed_files:
                    status_label.config(
                        text=f"⚠️ {len(uploaded_files)} uploaded, {len(failed_files)} failed", 
                        fg=COLORS['warning']
                    )
                    messagebox.showwarning(
                        "Partial Upload", 
                        f"Uploaded: {len(uploaded_files)} files\nFailed: {len(failed_files)} files\n\nFailed files:\n" + 
                        "\n".join(failed_files[:3]) + ("..." if len(failed_files) > 3 else "")
                    )
                else:
                    status_label.config(text="❌ All uploads failed", fg=COLORS['danger'])
                    messagebox.showerror("Upload Failed", "All file uploads failed:\n" + "\n".join(failed_files[:3]))
                
                # Reset form if all successful
                if not failed_files:
                    selected_files.clear()
                    department_var.set("")
                    transaction_type_var.set("")
                    progress_var.set(0)
                    update_file_list()
                    status_label.config(text="Ready to upload", fg=COLORS['text_light'])
                
            except Exception as e:
                progress_var.set(0)
                status_label.config(text="❌ Upload failed", fg=COLORS['danger'])
                messagebox.showerror("Upload Error", f"Unexpected error: {str(e)}")
            finally:
                upload_btn.config(state='normal', text='🚀 Upload All Files', bg=COLORS['primary'])
                clear_btn.config(state='normal')

        Thread(target=do_upload).start()

    # Create popup window
    popup = tk.Toplevel(parent_admin)
    popup.title("📤 Head Office Multi-File Upload")
    popup.geometry("600x700")
    popup.configure(bg=COLORS['light'])
    popup.grab_set()
    popup.resizable(True, False)  # Allow horizontal resize, fixed height

    # Center the window
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

    # Variables
    department_var = tk.StringVar()
    transaction_type_var = tk.StringVar()
    progress_var = tk.IntVar(value=0)

    # Main container
    main_frame = create_styled_frame(popup, COLORS['white'])
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Header
    header_frame = create_styled_frame(main_frame, COLORS['primary'])
    header_frame.pack(fill='x', pady=(0, 20))
    
    header_label = tk.Label(
        header_frame,
        text="📋 Multi-Document Upload Center",
        font=('Segoe UI', 16, 'bold'),
        bg=COLORS['primary'],
        fg='white',
        pady=15
    )
    header_label.pack()

    # Form container with scrollable area
    form_container = create_styled_frame(main_frame)
    form_container.pack(fill='both', expand=True, padx=10)
    
    # Create canvas for scrollable form
    form_canvas = tk.Canvas(form_container, bg=COLORS['white'], highlightthickness=0)
    form_scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=form_canvas.yview)
    form_frame = tk.Frame(form_canvas, bg=COLORS['white'])
    
    form_frame.bind(
        "<Configure>",
        lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all"))
    )
    
    form_canvas.create_window((0, 0), window=form_frame, anchor="nw")
    form_canvas.configure(yscrollcommand=form_scrollbar.set)
    
    # Enable mouse wheel scrolling for form
    def on_form_mousewheel(event):
        form_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    form_canvas.bind("<MouseWheel>", on_form_mousewheel)
    
    # Pack canvas and scrollbar
    form_canvas.pack(side="left", fill="both", expand=True)
    form_scrollbar.pack(side="right", fill="y")

    # Department section
    dept_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    dept_section.pack(fill='x', pady=(0, 15), padx=5)
    
    tk.Label(
        dept_section,
        text="🏢 Department",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))
    
    department_dropdown = ttk.Combobox(
        dept_section,
        textvariable=department_var,
        state="readonly",
        font=('Segoe UI', 10),
        values=["Accounting", "Liaison Department", "Compliance Department"]
    )
    department_dropdown.pack(fill='x', padx=15, pady=(0, 15))

    # Transaction Type section
    trans_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    trans_section.pack(fill='x', pady=(0, 15), padx=5)
    
    tk.Label(
        trans_section,
        text="📋 Transaction Type",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))
    
    transaction_dropdown = ttk.Combobox(
        trans_section,
        textvariable=transaction_type_var,
        state="readonly",
        font=('Segoe UI', 10),
        values=["Invoice", "Purchase Order", "Delivery Receipt", "Contract", "Report", "Memo"]
    )
    transaction_dropdown.pack(fill='x', padx=15, pady=(0, 15))

    # Date section
    date_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    date_section.pack(fill='x', pady=(0, 15), padx=5)
    
    tk.Label(
        date_section,
        text="📅 Document Date",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))
    
    date_entry = DateEntry(
        date_section,
        width=18,
        background=COLORS['primary'],
        foreground='white',
        borderwidth=2,
        font=('Segoe UI', 10)
    )
    date_entry.pack(padx=15, pady=(0, 15), anchor='w')

    # File section (fixed height to prevent overflow)
    file_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    file_section.pack(fill='x', pady=(0, 15), padx=5)
    
    # File section header
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
    
    # File list container (fixed height with scrollbar)
    file_list_container = create_styled_frame(file_section, COLORS['light'])
    file_list_container.pack(fill='x', padx=15, pady=(0, 10))
    file_list_container.configure(height=200)  # Fixed height
    
    file_list_frame = create_styled_frame(file_list_container, COLORS['light'])
    file_list_frame.pack(fill='both', expand=True)
    
    # Supported formats info
    formats_label = tk.Label(
        file_section,
        text="💡 Supported: JPG, PNG, PDF, DOCX (Max 50MB each)",
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
    
    close_btn = create_modern_button(
        button_frame,
        "❌ Close",
        popup.destroy,
        COLORS['secondary'],
        COLORS['text'],
        width=12
    )
    close_btn.pack(side='left')

    # Configure ttk styles
    style = ttk.Style()
    style.configure('TProgressbar', thickness=20)

    # Initialize file list
    update_file_list()

    popup.mainloop()