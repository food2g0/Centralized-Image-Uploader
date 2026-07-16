import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import time
import datetime
from threading import Thread
from firebase_config import storage, db, update_head_office_index, get_head_office_custom_transactions
from firebase_admin import firestore
from Colors import COLORS
from corporations import CORPORATIONS, DEPARTMENT_CONFIG

ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".jfif")
MAX_FILE_SIZE = 100 * 1024 * 1024

# Professional UI Colors - Eye-friendly dark theme
PRO_COLORS = {
    'bg_dark': '#f8f9fa',          # Light background (almost white)
    'bg_medium': '#eef2f7',        # Very light blue-gray background
    'bg_light': '#e8ecf1',         # Light gray-blue
    'accent': '#2563eb',           # Professional blue
    'accent_hover': '#1d4ed8',     # Darker blue on hover
    'success': '#16a34a',          # Professional green
    'warning': '#d97706',          # Professional amber
    'danger': '#dc2626',           # Professional red
    'text_primary': '#0f172a',     # Dark text for readability
    'text_secondary': '#475569',   # Gray text for secondary info
    'card_bg': '#ffffff',          # Pure white cards
    'border': '#e2e8f0',           # Light subtle border
    'input_bg': '#f1f5f9',         # Light input background
    'gradient_start': '#2563eb',   # Professional blue
    'gradient_end': '#1d4ed8',     # Darker professional blue
}

VERSION = "1.1.6"


class DepartmentTransactionManager:
    """Centralized manager for department-specific transaction types"""

    @staticmethod
    def get_departments():
        """Get list of all departments"""
        return list(DEPARTMENT_CONFIG.keys())

    @staticmethod
    def get_transactions(department):
        """Get transaction types for a specific department (built-in + super admin custom)"""
        built_in = DEPARTMENT_CONFIG.get(department, {}).get("transactions", [])
        try:
            custom = get_head_office_custom_transactions(department)
        except Exception:
            custom = []
        # Merge, preserving order and avoiding duplicates
        merged = list(built_in)
        for t in custom:
            if t not in merged:
                merged.append(t)
        return merged

    @staticmethod
    def get_sub_categories(department, transaction):
        """Get sub-categories for a specific transaction type"""
        dept_config = DEPARTMENT_CONFIG.get(department, {})
        return dept_config.get("sub_categories", {}).get(transaction, [])

    @staticmethod
    def has_sub_categories(department, transaction):
        
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


def create_modern_button(parent, text, command, bg_color, hover_color=None, width=None, size='normal'):
    """Create a modern styled button with hover effects and shadow"""
    font_size = 11 if size == 'large' else 10 if size == 'normal' else 9
    pad_x = 25 if size == 'large' else 20 if size == 'normal' else 15
    pad_y = 12 if size == 'large' else 8 if size == 'normal' else 6
    
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg='white',
        font=('Segoe UI', font_size, 'bold'),
        relief='flat',
        cursor='hand2',
        padx=pad_x,
        pady=pad_y,
        width=width,
        activebackground=hover_color if hover_color else bg_color,
        activeforeground='white',
        bd=0,
        highlightthickness=0
    )

    if hover_color:
        def on_enter(e):
            button.config(bg=hover_color)

        def on_leave(e):
            button.config(bg=bg_color)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    return button


def create_card_frame(parent, bg_color=None, padding=15):
    """Create a modern card with subtle shadow effect"""
    bg = bg_color if bg_color else PRO_COLORS['card_bg']
    
    # Outer frame for shadow effect
    outer = tk.Frame(parent, bg=PRO_COLORS['bg_dark'], padx=2, pady=2)
    
    # Inner card
    card = tk.Frame(
        outer,
        bg=bg,
        relief='flat',
        bd=0,
        highlightbackground=PRO_COLORS['border'],
        highlightthickness=1
    )
    card.pack(fill='both', expand=True, padx=padding, pady=padding)
    
    return outer, card


def create_styled_frame(parent, bg_color=COLORS['white'], relief='flat', bd=1):

    frame = tk.Frame(parent, bg=bg_color, relief=relief, bd=bd)
    return frame


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def create_corporation_section_alternative(form_frame, corporation_var, all_corporations):

    corp_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    corp_section.pack(fill='x', pady=(0, 15), padx=5)

    corp_label = tk.Label(
        corp_section,
        text="🏢 Corporation (Type to search)",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
        anchor='w'
    )
    corp_label.pack(fill='x', padx=15, pady=(15, 5))

    # Create frame for entry and listbox
    search_frame = tk.Frame(corp_section, bg=PRO_COLORS['card_bg'])
    search_frame.pack(fill='x', padx=15, pady=(0, 10))

    # Search entry
    search_var = tk.StringVar()
    search_entry = tk.Entry(
        search_frame,
        textvariable=search_var,
        font=('Segoe UI', 10),
        relief='flat',
        bd=0,
        bg=PRO_COLORS['input_bg'],
        fg=PRO_COLORS['text_primary'],
        insertbackground=PRO_COLORS['text_primary']
    )
    search_entry.pack(fill='x', pady=(0, 5), ipady=8)

    # Results listbox
    results_frame = tk.Frame(search_frame, bg=PRO_COLORS['input_bg'])
    results_listbox = tk.Listbox(
        results_frame,
        font=('Segoe UI', 9),
        height=6,
        relief='flat',
        bd=0,
        bg=PRO_COLORS['input_bg'],
        fg=PRO_COLORS['text_primary'],
        selectbackground=PRO_COLORS['accent'],
        selectforeground='white',
        highlightthickness=0
    )
    scrollbar = tk.Scrollbar(results_frame, orient='vertical', command=results_listbox.yview)
    results_listbox.configure(yscrollcommand=scrollbar.set)

    # Selected corporation display
    selected_frame = tk.Frame(corp_section, bg=PRO_COLORS['success'])
    selected_label = tk.Label(
        selected_frame,
        text="No corporation selected",
        font=('Segoe UI', 10, 'bold'),
        bg=PRO_COLORS['success'],
        fg='white',
        pady=8
    )

    def update_search(*args):
        """Update search results"""
        query = search_var.get().strip().upper()

        # Clear current results
        results_listbox.delete(0, tk.END)

        if not query:
            # Show all if empty
            filtered = all_corporations[:20]  # Limit to first 20
            if len(all_corporations) > 20:
                results_listbox.insert(tk.END, f"... and {len(all_corporations) - 20} more (type to filter)")
        else:
            # Filter based on query
            filtered = [corp for corp in all_corporations if query in corp.upper()][:20]
            if len(filtered) == 0:
                results_listbox.insert(tk.END, "No matches found")
                results_frame.pack_forget()
                return

        # Add filtered results
        for corp in filtered:
            results_listbox.insert(tk.END, corp)

        # Show results
        if filtered:
            results_frame.pack(fill='x', pady=(0, 10))
            results_listbox.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

    def on_select(event):

        selection = results_listbox.curselection()
        if selection:
            selected_corp = results_listbox.get(selection[0])
            if selected_corp in all_corporations:
                corporation_var.set(selected_corp)
                search_var.set(selected_corp)
                selected_label.config(text=f"✓ Selected: {selected_corp}")
                selected_frame.pack(fill='x', padx=15, pady=(0, 10))
                results_frame.pack_forget()

    def clear_selection():
        """Clear current selection"""
        corporation_var.set("")
        search_var.set("")
        selected_label.config(text="No corporation selected")
        selected_frame.pack_forget()
        results_frame.pack_forget()

    # Clear button (dark theme)
    clear_btn = tk.Button(
        corp_section,
        text="🗑️ Clear Selection",
        command=clear_selection,
        bg=PRO_COLORS['warning'],
        fg='#000000',
        font=('Segoe UI', 8, 'bold'),
        relief='flat',
        cursor='hand2',
        padx=10,
        pady=5
    )
    clear_btn.pack(padx=15, pady=(0, 15))

    # Bind events
    search_var.trace('w', update_search)
    results_listbox.bind('<Double-Button-1>', on_select)
    results_listbox.bind('<Return>', on_select)

    # Initialize
    update_search()

    return corp_section


def open_head_office_dashboard(next_user_data):


    dept_manager = DepartmentTransactionManager()


    user_department = next_user_data.get('department', '')
    user_role = next_user_data.get('role', '').lower()
    username = next_user_data.get('username', 'Unknown User')

    # Debug: Print user info
    print(f"[HEAD OFFICE] Username: {username}, Role: '{user_role}', Department: '{user_department}'")

    # Check if user is Liaison-Compliance Department (restricted access)
    # Support multiple variations: 'liaison-compliance department', 'liaison', or department containing 'Liaison'
    is_liaison_compliance = (
        user_role == 'liaison-compliance department' or
        'liaison' in user_role or
        user_department == 'Liaison-Compliance Department' or
        'liaison' in user_department.lower()
    )
    print(f"[HEAD OFFICE] is_liaison_compliance: {is_liaison_compliance}")

    # Store selected files
    selected_files = []

    def add_files():
        file_paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[
                ("All Supported", "*.jpeg;*.jpg;*.png;*.pdf;"),
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
                bg=PRO_COLORS['input_bg'],
                fg=PRO_COLORS['text_secondary'],
                justify='center'
            )
            no_files_label.pack(expand=True, fill='both', pady=20)
            files_info_label.config(text="0 files selected")
            return

        # Create scrollable frame for file list
        for widget in file_list_frame.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(file_list_frame, bg=PRO_COLORS['input_bg'], highlightthickness=0, height=180)
        scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=PRO_COLORS['input_bg'])

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
            file_frame = tk.Frame(scrollable_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
            file_frame.pack(fill='x', padx=2, pady=2)

            info_frame = tk.Frame(file_frame, bg=PRO_COLORS['card_bg'])
            info_frame.pack(side='left', fill='both', expand=True, padx=8, pady=4)

            status_color = PRO_COLORS['text_secondary'] if file_info['status'] == 'pending' else \
                PRO_COLORS['success'] if file_info['status'] == 'uploaded' else \
                    PRO_COLORS['warning'] if file_info['status'] == 'uploading' else \
                        PRO_COLORS['danger']

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
                bg=PRO_COLORS['card_bg'],
                fg=status_color,
                anchor='w'
            )
            name_label.pack(fill='x')

            size_label = tk.Label(
                info_frame,
                text=f"{format_file_size(file_info['size'])} • {file_info['status'].title()}",
                font=('Segoe UI', 8),
                bg=PRO_COLORS['card_bg'],
                fg=PRO_COLORS['text_secondary'],
                anchor='w'
            )
            size_label.pack(fill='x')

            if file_info['status'] == 'pending':
                remove_btn = tk.Button(
                    file_frame,
                    text="×",
                    command=lambda idx=i: remove_file(idx),
                    bg=PRO_COLORS['danger'],
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
        """Enhanced validation with better corporation filtering support"""
        errors = []

        if not selected_files:
            errors.append("Please select at least one file")

        # Clean and validate corporation
        selected_corp = corporation_var.get().strip()
        selected_transaction = transaction_type_var.get()
        selected_sub = sub_category_var.get()
        uploaded_by = uploaded_by_var.get().strip()

        # Corporation validation
        if not selected_corp:
            errors.append("Please select a corporation")
        else:
            all_corps = dept_manager.get_corporations()

            # Check for exact match first
            if selected_corp in all_corps:
                # Valid selection, no issues
                pass
            else:
                # Check for case-insensitive exact match
                exact_match = None
                for corp in all_corps:
                    if corp.upper() == selected_corp.upper():
                        exact_match = corp
                        break

                if exact_match:

                    corporation_var.set(exact_match)
                    selected_corp = exact_match
                else:
                    # No valid match found
                    errors.append(f"Corporation '{selected_corp}' not found. Please select from the list.")

        # Transaction type validation
        if not selected_transaction:
            errors.append("Please select a transaction type")
        elif not dept_manager.validate_transaction(user_department, selected_transaction):
            errors.append(f"Invalid transaction type '{selected_transaction}' for {user_department}")
        elif dept_manager.has_sub_categories(user_department, selected_transaction) and not selected_sub:
            errors.append(f"Please select a {selected_transaction} type")
        elif selected_sub and not dept_manager.validate_transaction(user_department, selected_transaction,
                                                                    selected_sub):
            errors.append(f"Invalid sub-category '{selected_sub}' for {selected_transaction}")

        # Uploaded by validation (excluding placeholder text)
        if not uploaded_by or uploaded_by == "Enter your name":
            errors.append("Please enter who is uploading the documents")
        elif len(uploaded_by) < 2:
            errors.append("Uploaded by name must be at least 2 characters")
        elif uploaded_by.isspace():
            errors.append("Uploaded by cannot be only whitespace")

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
                            "uploaded_by": uploaded_by,  
                            "upload_date": current_date,
                            "file_name": file_info['name'],
                            "file_url": file_url,
                            "file_size": file_info['size'],
                            "upload_batch": timestamp,
                            "timestamp": firestore.SERVER_TIMESTAMP,
                         
                        })
                        
                        # Update index for fast lookups
                        update_head_office_index(user_department, final_transaction_type)

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

    # Create main window with professional styling
    popup = tk.Tk()
    popup.title(f"📤 {user_department} - Document Upload | Head Office Portal v{VERSION}")
    popup.configure(bg=PRO_COLORS['bg_dark'])
    
    # Enable resizing and fullscreen
    popup.resizable(True, True)
    popup.minsize(700, 600)
    
    # Get screen dimensions
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    
    # Set initial size (80% of screen)
    window_width = min(1000, int(screen_width * 0.8))
    window_height = min(900, int(screen_height * 0.9))
    
    # Center window
    x = (screen_width - window_width) // 2
    y = max(20, (screen_height - window_height) // 2 - 30)
    
    popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Fullscreen toggle variables
    is_fullscreen = [False]
    
    def toggle_fullscreen(event=None):
        """Toggle fullscreen mode with F11"""
        is_fullscreen[0] = not is_fullscreen[0]
        popup.attributes('-fullscreen', is_fullscreen[0])
        if is_fullscreen[0]:
            fullscreen_btn.config(text="⬜ Exit Fullscreen")
        else:
            fullscreen_btn.config(text="⬛ Fullscreen")
        return "break"
    
    def exit_fullscreen(event=None):
        """Exit fullscreen with Escape"""
        if is_fullscreen[0]:
            is_fullscreen[0] = False
            popup.attributes('-fullscreen', False)
            fullscreen_btn.config(text="⬛ Fullscreen")
        return "break"
    
    def maximize_window(event=None):
        """Maximize/restore window"""
        if popup.state() == 'zoomed':
            popup.state('normal')
        else:
            popup.state('zoomed')
    
    # Bind keyboard shortcuts
    popup.bind('<F11>', toggle_fullscreen)
    popup.bind('<Escape>', exit_fullscreen)
    popup.bind('<F10>', maximize_window)

    # Variables
    corporation_var = tk.StringVar()
    transaction_type_var = tk.StringVar()
    sub_category_var = tk.StringVar()
    uploaded_by_var = tk.StringVar()
    progress_var = tk.IntVar(value=0)

    # Main container with dark theme
    main_frame = tk.Frame(popup, bg=PRO_COLORS['bg_dark'])
    main_frame.pack(fill='both', expand=True)

    # Top toolbar with controls
    toolbar_frame = tk.Frame(main_frame, bg=PRO_COLORS['bg_medium'], height=45)
    toolbar_frame.pack(fill='x', side='top')
    toolbar_frame.pack_propagate(False)
    
    # Left side - App title
    title_frame = tk.Frame(toolbar_frame, bg=PRO_COLORS['bg_medium'])
    title_frame.pack(side='left', padx=15, pady=8)
    
    tk.Label(
        title_frame,
        text=f"📤 HEAD OFFICE PORTAL",
        font=('Segoe UI', 12, 'bold'),
        bg=PRO_COLORS['bg_medium'],
        fg=PRO_COLORS['text_primary']
    ).pack(side='left')
    
    tk.Label(
        title_frame,
        text=f"  v{VERSION}",
        font=('Segoe UI', 9),
        bg=PRO_COLORS['bg_medium'],
        fg=PRO_COLORS['text_secondary']
    ).pack(side='left')
    
    # Right side - Window controls
    controls_frame = tk.Frame(toolbar_frame, bg=PRO_COLORS['bg_medium'])
    controls_frame.pack(side='right', padx=10, pady=8)
    
    fullscreen_btn = tk.Button(
        controls_frame,
        text="⬛ Fullscreen",
        command=toggle_fullscreen,
        bg=PRO_COLORS['bg_light'],
        fg=PRO_COLORS['text_primary'],
        font=('Segoe UI', 9),
        relief='flat',
        cursor='hand2',
        padx=10,
        pady=3,
        bd=0
    )
    fullscreen_btn.pack(side='left', padx=5)
    
    # Help tooltip
    tk.Label(
        controls_frame,
        text="F11: Fullscreen | ESC: Exit",
        font=('Segoe UI', 8),
        bg=PRO_COLORS['bg_medium'],
        fg=PRO_COLORS['text_secondary']
    ).pack(side='left', padx=(10, 0))

    # Content area with responsive padding
    content_area = tk.Frame(main_frame, bg=PRO_COLORS['bg_dark'])
    content_area.pack(fill='both', expand=True, padx=25, pady=20)
    
    # Inner content wrapper with max-width for large screens
    content_wrapper = tk.Frame(content_area, bg=PRO_COLORS['bg_dark'])
    content_wrapper.pack(fill='both', expand=True)
    
    # Update padding dynamically based on window size
    def update_content_padding(event=None):
        current_width = popup.winfo_width()
        if current_width > 1600:
            side_padding = int((current_width - 1200) / 2)
        elif current_width > 1200:
            side_padding = int((current_width - 900) / 2)
        else:
            side_padding = 25
        content_area.pack_configure(padx=max(25, side_padding))
    
    # Bind to window resize
    popup.bind('<Configure>', update_content_padding)

    # Header card
    header_frame = tk.Frame(content_wrapper, bg=PRO_COLORS['accent'])
    header_frame.pack(fill='x', pady=(0, 20))
    
    # Gradient-like header with department info
    header_inner = tk.Frame(header_frame, bg=PRO_COLORS['accent'])
    header_inner.pack(fill='x', padx=3, pady=3)

    dept_icon = dept_manager.get_department_icon(user_department)
    header_label = tk.Label(
        header_inner,
        text=f"{dept_icon} {user_department} - Document Upload",
        font=('Segoe UI', 18, 'bold'),
        bg=PRO_COLORS['accent'],
        fg='white',
        pady=18
    )
    header_label.pack()

    # User info display card
    user_info_frame = tk.Frame(content_wrapper, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    user_info_frame.pack(fill='x', pady=(0, 15))

    user_info_inner = tk.Frame(user_info_frame, bg=PRO_COLORS['card_bg'])
    user_info_inner.pack(fill='x', padx=15, pady=12)
    
    tk.Label(
        user_info_inner,
        text=f"👤 {username}",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary']
    ).pack(side='left')
    
    tk.Label(
        user_info_inner,
        text="  |  ",
        font=('Segoe UI', 11),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_secondary']
    ).pack(side='left')
    
    tk.Label(
        user_info_inner,
        text=f"🏢 {user_department}",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['success']
    ).pack(side='left')
    
    # Online status indicator
    tk.Label(
        user_info_inner,
        text="● Online",
        font=('Segoe UI', 9),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['success']
    ).pack(side='right')

    # Form container with scrollable area (dark theme)
    form_container = tk.Frame(content_wrapper, bg=PRO_COLORS['bg_dark'])
    form_container.pack(fill='both', expand=True)

    form_canvas = tk.Canvas(form_container, bg=PRO_COLORS['bg_dark'], highlightthickness=0)
    form_scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=form_canvas.yview)
    form_frame = tk.Frame(form_canvas, bg=PRO_COLORS['bg_dark'])

    # Create window and store ID for resizing
    canvas_window = form_canvas.create_window((0, 0), window=form_frame, anchor="nw")

    def on_frame_configure(event):
        form_canvas.configure(scrollregion=form_canvas.bbox("all"))

    def on_canvas_configure(event):
        # Make form_frame expand to fill canvas width
        canvas_width = event.width
        form_canvas.itemconfig(canvas_window, width=canvas_width)

    form_frame.bind("<Configure>", on_frame_configure)
    form_canvas.bind("<Configure>", on_canvas_configure)

    form_canvas.configure(yscrollcommand=form_scrollbar.set)

    def on_form_mousewheel(event):
        form_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    form_canvas.bind("<MouseWheel>", on_form_mousewheel)
    form_frame.bind("<MouseWheel>", on_form_mousewheel)

    form_canvas.pack(side="left", fill="both", expand=True)
    form_scrollbar.pack(side="right", fill="y")

    # Corporation section
    all_corporations = dept_manager.get_corporations()
    corp_section = create_corporation_section_alternative(form_frame, corporation_var, all_corporations)

    # Transaction Type section (dark theme)
    trans_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    trans_section.pack(fill='x', pady=(0, 15), padx=5)

    trans_label = tk.Label(
        trans_section,
        text=f"📋 {user_department.replace(' Department', '')} Transaction Type",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
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

    # Sub-category section (initially hidden, dark theme)
    sub_category_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)

    sub_category_label = tk.Label(
        sub_category_section,
        text="📚 Sub-Category",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
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

    # Uploaded By section (dark theme)
    uploaded_by_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    uploaded_by_section.pack(fill='x', pady=(0, 15), padx=5)

    tk.Label(
        uploaded_by_section,
        text="👤 Uploaded By",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))

    uploaded_by_entry = tk.Entry(
        uploaded_by_section,
        textvariable=uploaded_by_var,
        font=('Segoe UI', 10),
        relief='flat',
        bd=0,
        bg=PRO_COLORS['input_bg'],
        fg=PRO_COLORS['text_primary'],
        insertbackground=PRO_COLORS['text_primary']
    )
    uploaded_by_entry.pack(fill='x', padx=15, pady=(0, 10), ipady=8)

    # Add placeholder text functionality
    def on_focus_in(event):
        if uploaded_by_entry.get() == "Enter your name":
            uploaded_by_entry.delete(0, tk.END)
            uploaded_by_entry.config(fg=PRO_COLORS['text_primary'])

    def on_focus_out(event):
        if uploaded_by_entry.get() == "":
            uploaded_by_entry.insert(0, "Enter your name")
            uploaded_by_entry.config(fg=PRO_COLORS['text_secondary'])

    # Set initial placeholder
    uploaded_by_entry.insert(0, "Enter your name")
    uploaded_by_entry.config(fg=PRO_COLORS['text_secondary'])
    uploaded_by_entry.bind('<FocusIn>', on_focus_in)
    uploaded_by_entry.bind('<FocusOut>', on_focus_out)

    # Helper text
    helper_label = tk.Label(
        uploaded_by_section,
        text="💡 Enter the name of the person uploading these documents",
        font=('Segoe UI', 8),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_secondary'],
        anchor='w'
    )
    helper_label.pack(fill='x', padx=15, pady=(0, 15))

    # File section (dark theme)
    file_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    file_section.pack(fill='x', pady=(0, 15), padx=5)

    file_header_frame = tk.Frame(file_section, bg=PRO_COLORS['card_bg'])
    file_header_frame.pack(fill='x', padx=15, pady=(15, 5))

    tk.Label(
        file_header_frame,
        text="📎 Document Files",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
        anchor='w'
    ).pack(side='left')

    files_info_label = tk.Label(
        file_header_frame,
        text="0 files selected",
        font=('Segoe UI', 9),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_secondary'],
        anchor='e'
    )
    files_info_label.pack(side='right')

    # File management buttons (dark theme)
    file_btn_frame = tk.Frame(file_section, bg=PRO_COLORS['card_bg'])
    file_btn_frame.pack(fill='x', padx=15, pady=(0, 10))

    add_files_btn = create_modern_button(
        file_btn_frame,
        "📁 Add Files",
        add_files,
        PRO_COLORS['success'],
        '#00f0b5',
        width=12
    )
    add_files_btn.pack(side='left')

    clear_btn = create_modern_button(
        file_btn_frame,
        "🗑️ Clear All",
        clear_all_files,
        PRO_COLORS['warning'],
        '#ffd700',
        width=10
    )
    clear_btn.pack(side='left', padx=(10, 0))

    # File list container (dark theme)
    file_list_container = tk.Frame(file_section, bg=PRO_COLORS['input_bg'])
    file_list_container.pack(fill='x', padx=15, pady=(0, 10))
    file_list_container.configure(height=200)

    file_list_frame = tk.Frame(file_list_container, bg=PRO_COLORS['input_bg'])
    file_list_frame.pack(fill='both', expand=True)

    # Supported formats info
    formats_label = tk.Label(
        file_section,
        text="💡 Supported: PDF, JPG, PNG, GIF, BMP, WebP (Max 100MB per file)",
        font=('Segoe UI', 8),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_secondary'],
        anchor='w'
    )
    formats_label.pack(fill='x', padx=15, pady=(0, 15))

    # Progress section (dark theme)
    progress_section = tk.Frame(form_frame, bg=PRO_COLORS['card_bg'], highlightbackground=PRO_COLORS['border'], highlightthickness=1)
    progress_section.pack(fill='x', pady=(0, 15), padx=5)

    tk.Label(
        progress_section,
        text="📊 Upload Progress",
        font=('Segoe UI', 11, 'bold'),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['text_primary'],
        anchor='w'
    ).pack(fill='x', padx=15, pady=(15, 5))

    progress_bar = ttk.Progressbar(
        progress_section,
        variable=progress_var,
        maximum=100,
        style='custom.Horizontal.TProgressbar'
    )
    progress_bar.pack(fill='x', padx=15, pady=(0, 10))

    status_label = tk.Label(
        progress_section,
        text="● Ready to upload",
        font=('Segoe UI', 9),
        bg=PRO_COLORS['card_bg'],
        fg=PRO_COLORS['success'],
        anchor='w'
    )
    status_label.pack(fill='x', padx=15, pady=(0, 15))

    # Button section (dark theme)
    button_frame = tk.Frame(content_wrapper, bg=PRO_COLORS['bg_dark'])
    button_frame.pack(fill='x', pady=(20, 0))

    upload_btn = create_modern_button(
        button_frame,
        "🚀 Upload All Files",
        upload_files,
        PRO_COLORS['accent'],
        PRO_COLORS['accent_hover'],
        width=20,
        size='large'
    )
    upload_btn.pack(side='left', padx=(0, 15))

    def view_branch_kyc():
        """View KYC uploads from branches (Liaison-Compliance feature)"""
        try:
            # Create a modified admin_data for viewing branches
            branch_view_data = {
                'username': username,
                'department': user_department,
                'role': 'liaison-compliance',
                'view_mode': 'kyc_only'  # Flag to filter for KYC only
            }

            # Show group selection to view branches from specific group
            show_branch_selection_for_liaison(branch_view_data, popup)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open branch KYC uploads: {e}")

    def show_branch_selection_for_liaison(liaison_data, parent_window):
        """Show group selection for Liaison-Compliance to view branch KYC"""
        from corporations import group1_corporations, group2_corporations, group3_corporations

        selection_window = tk.Toplevel(parent_window)
        selection_window.title("Select Group - View Branch KYC")
        selection_window.geometry("500x400")
        selection_window.resizable(False, False)

        # Header
        header_frame = tk.Frame(selection_window, bg="#0f172a", height=120)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="View Branch KYC Forms",
            font=("Arial", 20, "bold"),
            bg="#0f172a",
            fg="white"
        ).pack(pady=(15, 5))

        tk.Label(
            header_frame,
            text="Select a group to view KYC forms from branches",
            font=("Arial", 10),
            bg="#0f172a",
            fg="#cbd5e1"
        ).pack(pady=(0, 15))

        # Content
        content_frame = tk.Frame(selection_window, bg="#f8fafc")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        groups_data = [
            ("Group 1", "group 1", group1_corporations, "📊"),
            ("Group 2", "group 2", group2_corporations, "📈"),
            ("Group 3", "group 3", group3_corporations, "📉")
        ]

        def select_group_for_kyc(group_name, corporations):
            selection_window.destroy()
            try:
                from shared_admin_dashboard import create_admin_dashboard

                # Create admin data with KYC filter flag
                modified_data = liaison_data.copy()
                modified_data['group'] = group_name

                create_admin_dashboard(
                    admin_data=modified_data,
                    group_corporations=corporations,
                    add_user_popup_func=lambda x: None,  # Liaison can't add users
                    group_name_display=f"{group_name} - Liaison View",
                    filter_transaction_type=['KYC Individual Records', 'Palawan Payout', 'Palawan Pay In', 'Palawan Sendout', 'Money Changer Buy', 'Money Changer Sell', 'Jewelry Renew', 'Jewelry New', 'Jewelry Redeem'],
                    switch_group_callback=None
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open group dashboard: {e}")

        for display_name, group_value, corporations, icon in groups_data:
            btn_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=1)
            btn_frame.pack(fill="x", pady=10)

            btn = tk.Button(
                btn_frame,
                text=f"{icon}  {display_name}",
                font=("Arial", 12, "bold"),
                bg="#2563eb",
                fg="white",
                height=2,
                relief="flat",
                cursor="hand2",
                command=lambda g=group_value, c=corporations: select_group_for_kyc(g, c),
                activebackground="#1d4ed8",
                activeforeground="white"
            )
            btn.pack(fill="both", expand=True, padx=0, pady=0)

    # Add "View Branch KYC" button for Liaison-Compliance Department users
    if is_liaison_compliance:
        view_btn = create_modern_button(
            button_frame,
            "👁️ View Branch KYC",
            view_branch_kyc,
            PRO_COLORS['success'],
            '#34d399',
            width=15,
            size='normal'
        )
        view_btn.pack(side='left', padx=(0, 15))

    def logout_and_exit():
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
        PRO_COLORS['danger'],
        '#ff4757',
        width=12,
        size='normal'
    )
    logout_btn.pack(side='right')

    # Configure ttk styles for dark theme
    style = ttk.Style()
    style.theme_use('clam')
    
    # Custom progress bar style
    style.configure(
        'custom.Horizontal.TProgressbar',
        troughcolor=PRO_COLORS['input_bg'],
        background=PRO_COLORS['accent'],
        thickness=25,
        borderwidth=0
    )
    
    # Custom scrollbar style
    style.configure(
        'TScrollbar',
        background=PRO_COLORS['bg_light'],
        troughcolor=PRO_COLORS['bg_dark'],
        borderwidth=0
    )
    
    # Custom combobox style
    style.configure(
        'TCombobox',
        fieldbackground=PRO_COLORS['input_bg'],
        background=PRO_COLORS['bg_light'],
        foreground=PRO_COLORS['text_primary'],
        arrowcolor=PRO_COLORS['text_primary']
    )

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


