import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import time
import datetime
import webbrowser
from threading import Thread
from firebase_config import storage, db
from firebase_admin import firestore
from Colors import COLORS
from corporations import CORPORATIONS, DEPARTMENT_CONFIG

# Version information
VERSION = "1.1.3"
VERSION_DATE = "2025-12-03"

ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".jfif")
MAX_FILE_SIZE = 100 * 1024 * 1024

# Pagination constants
DOCUMENTS_PER_PAGE = 10

# Cash Management specific transaction types
CASH_MANAGEMENT_TRANSACTIONS = [
    "Daily Bank Statement",

]

# Cash Management sub-categories
CASH_MANAGEMENT_SUB_CATEGORIES = {

    "Daily Bank Statement": [
        "BDO",
        "BPI",
        "UNION BANK",

    ]

}


class CashManagementTransactionManager:
    """Cash Management specific transaction manager"""

    @staticmethod
    def get_transactions():
        """Get list of cash management transaction types"""
        return CASH_MANAGEMENT_TRANSACTIONS

    @staticmethod
    def get_sub_categories(transaction):
        """Get sub-categories for a specific transaction type"""
        return CASH_MANAGEMENT_SUB_CATEGORIES.get(transaction, [])

    @staticmethod
    def has_sub_categories(transaction):
        """Check if a transaction type has sub-categories"""
        return len(CashManagementTransactionManager.get_sub_categories(transaction)) > 0

    @staticmethod
    def validate_transaction(transaction, sub_category=None):
        """Validate if a transaction is valid"""
        if transaction not in CASH_MANAGEMENT_TRANSACTIONS:
            return False

        if sub_category:
            valid_subs = CashManagementTransactionManager.get_sub_categories(transaction)
            return sub_category in valid_subs

        return True

    @staticmethod
    def get_corporations():
        """Get list of all corporations"""
        return CORPORATIONS


class DocumentPaginator:
    """Handles document pagination and Firebase query optimization"""

    def __init__(self, page_size=DOCUMENTS_PER_PAGE):
        self.page_size = page_size
        self.current_page = 1
        self.total_documents = 0
        self.total_pages = 0
        self.cached_documents = {}  # Cache documents by page
        self.cache_timestamp = {}  # Track cache freshness
        self.cache_duration = 300  # Cache for 5 minutes

    def clear_cache(self):
        """Clear document cache"""
        self.cached_documents.clear()
        self.cache_timestamp.clear()

    def is_cache_valid(self, page):
        """Check if cached data is still valid"""
        if page not in self.cache_timestamp:
            return False
        return time.time() - self.cache_timestamp[page] < self.cache_duration

    def get_total_count(self, filters=None):
        """Get total document count with optimized query"""
        try:
            query = db.collection("cash_management_uploads")

            # Apply filters
            if filters:
                corp_filter = filters.get('corporation')
                trans_filter = filters.get('transaction_type')
                date_filter = filters.get('date_filter')

                if corp_filter and corp_filter != "All":
                    query = query.where("corporation", "==", corp_filter)

                if trans_filter and trans_filter != "All":
                    query = query.where("transaction_type", ">=", trans_filter).where("transaction_type", "<",
                                                                                      trans_filter + "\uf8ff")

                if date_filter:
                    query = query.where("upload_date", ">=", date_filter)

            # Use a lightweight query to count documents
            docs = query.select(["upload_date"]).stream()  # Only fetch upload_date field for counting
            self.total_documents = len(list(docs))
            self.total_pages = max(1, (self.total_documents + self.page_size - 1) // self.page_size)

            return self.total_documents

        except Exception as e:
            print(f"Error getting total count: {e}")
            return 0

    def get_page_documents(self, page, filters=None):
        """Get documents for specific page with optimized Firebase query"""
        try:
            # Check cache first
            cache_key = f"{page}_{str(filters)}"
            if cache_key in self.cached_documents and self.is_cache_valid(cache_key):
                return self.cached_documents[cache_key]

            query = db.collection("cash_management_uploads")

            # Apply filters
            if filters:
                corp_filter = filters.get('corporation')
                trans_filter = filters.get('transaction_type')
                date_filter = filters.get('date_filter')

                if corp_filter and corp_filter != "All":
                    query = query.where("corporation", "==", corp_filter)

                if trans_filter and trans_filter != "All":
                    # For transaction type, we need to handle sub-categories
                    query = query.where("transaction_type", ">=", trans_filter).where("transaction_type", "<",
                                                                                      trans_filter + "\uf8ff")

                if date_filter:
                    query = query.where("upload_date", ">=", date_filter)

            # Order by upload_date descending and apply pagination
            query = query.order_by("upload_date", direction=firestore.Query.DESCENDING)

            # Calculate offset
            offset = (page - 1) * self.page_size

            # Get documents with limit and offset
            docs = query.offset(offset).limit(self.page_size).stream()

            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['doc_id'] = doc.id
                documents.append(doc_data)

            # Cache the results
            self.cached_documents[cache_key] = documents
            self.cache_timestamp[cache_key] = time.time()

            return documents

        except Exception as e:
            print(f"Error getting page documents: {e}")
            return []

    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            return True
        return False

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            return True
        return False

    def go_to_page(self, page):
        """Go to specific page"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            return True
        return False


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


def create_corporation_section_alternative(form_frame, corporation_var, all_corporations):
    """Alternative corporation section with simpler, more reliable filtering"""

    corp_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    corp_section.pack(fill='x', pady=(0, 15), padx=5)

    corp_label = tk.Label(
        corp_section,
        text="Corporation (Type to search)",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    )
    corp_label.pack(fill='x', padx=15, pady=(15, 5))

    # Create frame for entry and listbox
    search_frame = create_styled_frame(corp_section, COLORS['white'])
    search_frame.pack(fill='x', padx=15, pady=(0, 10))

    # Search entry
    search_var = tk.StringVar()
    search_entry = tk.Entry(
        search_frame,
        textvariable=search_var,
        font=('Segoe UI', 10),
        relief='solid',
        bd=1
    )
    search_entry.pack(fill='x', pady=(0, 5))

    # Results listbox
    results_frame = tk.Frame(search_frame, bg=COLORS['white'])
    results_listbox = tk.Listbox(
        results_frame,
        font=('Segoe UI', 9),
        height=6,
        relief='solid',
        bd=1
    )
    scrollbar = tk.Scrollbar(results_frame, orient='vertical', command=results_listbox.yview)
    results_listbox.configure(yscrollcommand=scrollbar.set)

    # Selected corporation display
    selected_frame = create_styled_frame(corp_section, COLORS['success'], relief='solid', bd=1)
    selected_label = tk.Label(
        selected_frame,
        text="No corporation selected",
        font=('Segoe UI', 10, 'bold'),
        bg=COLORS['success'],
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
        """Handle corporation selection"""
        selection = results_listbox.curselection()
        if selection:
            selected_corp = results_listbox.get(selection[0])
            if selected_corp in all_corporations:
                corporation_var.set(selected_corp)
                search_var.set(selected_corp)
                selected_label.config(text=f"Selected: {selected_corp}")
                selected_frame.pack(fill='x', padx=15, pady=(0, 10))
                results_frame.pack_forget()

    def clear_selection():
        """Clear current selection"""
        corporation_var.set("")
        search_var.set("")
        selected_label.config(text="No corporation selected")
        selected_frame.pack_forget()
        results_frame.pack_forget()

    # Clear button
    clear_btn = tk.Button(
        corp_section,
        text="Clear Selection",
        command=clear_selection,
        bg=COLORS['warning'],
        fg='white',
        font=('Segoe UI', 8),
        relief='flat',
        cursor='hand2'
    )
    clear_btn.pack(padx=15, pady=(0, 15))

    # Bind events
    search_var.trace('w', update_search)
    results_listbox.bind('<Double-Button-1>', on_select)
    results_listbox.bind('<Return>', on_select)

    # Initialize
    update_search()

    return corp_section


def delete_document(doc_id, file_url, file_name, callback, paginator=None):
    """Delete a document from both storage and database with optimized operations"""

    def confirm_delete():
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete this document?\n\nFile: {file_name}\n\nThis action cannot be undone."
        )
        return result

    def do_delete():
        try:
            # Show progress
            progress_window = tk.Toplevel()
            progress_window.title("Deleting Document")
            progress_window.geometry("300x100")
            progress_window.configure(bg=COLORS['light'])
            progress_window.resizable(False, False)

            # Center the progress window
            progress_window.update_idletasks()
            screen_width = progress_window.winfo_screenwidth()
            screen_height = progress_window.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 100) // 2
            progress_window.geometry(f"300x100+{x}+{y}")

            progress_label = tk.Label(
                progress_window,
                text=f"Deleting {file_name[:30]}...",
                font=('Segoe UI', 10),
                bg=COLORS['light'],
                fg=COLORS['text']
            )
            progress_label.pack(pady=20)

            progress_bar = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                style='TProgressbar'
            )
            progress_bar.pack(fill='x', padx=20, pady=(0, 20))
            progress_bar.start()

            progress_window.update()

            # Extract storage path from URL
            storage_path = None
            try:
                # Parse the storage path from Firebase URL
                if "firebase" in file_url and "Cash%20Management" in file_url:
                    # Extract path between 'o/' and '?'
                    start_idx = file_url.find("o/") + 2
                    end_idx = file_url.find("?", start_idx)
                    if start_idx > 1 and end_idx > start_idx:
                        storage_path = file_url[start_idx:end_idx].replace("%20", " ").replace("%2F", "/")
            except Exception as e:
                print(f"Error parsing storage path: {e}")

            # Delete from database first (more critical operation)
            db.collection("cash_management_uploads").document(doc_id).delete()

            # Try to delete from storage if we have the path
            if storage_path:
                try:
                    storage.child(storage_path).delete()
                except Exception as storage_error:
                    print(f"Storage deletion warning: {storage_error}")
                    # Continue even if storage deletion fails

            # Clear cache after deletion
            if paginator:
                paginator.clear_cache()

            progress_window.destroy()

            messagebox.showinfo("Success", f"Document '{file_name}' has been deleted successfully.")

            # Call the callback to refresh the document list
            if callback:
                callback()

        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Delete Error", f"Failed to delete document: {str(e)}")

    # Confirm before deleting
    if confirm_delete():
        Thread(target=do_delete).start()


def create_pagination_controls(parent, paginator, load_callback):
    """Create modern pagination controls"""

    pagination_frame = create_styled_frame(parent, COLORS['white'], relief='solid', bd=1)
    pagination_frame.pack(fill='x', pady=(10, 0), padx=20)

    # Left side - Page info
    info_frame = tk.Frame(pagination_frame, bg=COLORS['white'])
    info_frame.pack(side='left', padx=15, pady=10)

    page_info_label = tk.Label(
        info_frame,
        text="",
        font=('Segoe UI', 10),
        bg=COLORS['white'],
        fg=COLORS['text']
    )
    page_info_label.pack()

    # Right side - Navigation controls
    nav_frame = tk.Frame(pagination_frame, bg=COLORS['white'])
    nav_frame.pack(side='right', padx=15, pady=10)

    def update_page_info():
        """Update page information display"""
        if paginator.total_documents == 0:
            page_info_label.config(text="No documents found")
            return

        start_doc = (paginator.current_page - 1) * paginator.page_size + 1
        end_doc = min(paginator.current_page * paginator.page_size, paginator.total_documents)

        page_info_label.config(
            text=f"Showing {start_doc}-{end_doc} of {paginator.total_documents} documents"
        )

    def go_first():
        if paginator.go_to_page(1):
            load_callback()
            update_controls()

    def go_prev():
        if paginator.prev_page():
            load_callback()
            update_controls()

    def go_next():
        if paginator.next_page():
            load_callback()
            update_controls()

    def go_last():
        if paginator.go_to_page(paginator.total_pages):
            load_callback()
            update_controls()

    def on_page_entry(event):
        try:
            page = int(page_entry.get())
            if paginator.go_to_page(page):
                load_callback()
                update_controls()
            else:
                page_entry.delete(0, tk.END)
                page_entry.insert(0, str(paginator.current_page))
        except ValueError:
            page_entry.delete(0, tk.END)
            page_entry.insert(0, str(paginator.current_page))

    # Navigation buttons
    first_btn = create_modern_button(
        nav_frame, "<<", go_first, COLORS['secondary'], width=3
    )
    first_btn.pack(side='left', padx=2)

    prev_btn = create_modern_button(
        nav_frame, "<", go_prev, COLORS['secondary'], width=3
    )
    prev_btn.pack(side='left', padx=2)

    # Page entry
    page_frame = tk.Frame(nav_frame, bg=COLORS['white'])
    page_frame.pack(side='left', padx=10)

    tk.Label(
        page_frame, text="Page", font=('Segoe UI', 9),
        bg=COLORS['white'], fg=COLORS['text']
    ).pack(side='left')

    page_entry = tk.Entry(
        page_frame, width=4, font=('Segoe UI', 9),
        relief='solid', bd=1, justify='center'
    )
    page_entry.pack(side='left', padx=(5, 0))
    page_entry.bind('<Return>', on_page_entry)

    page_total_label = tk.Label(
        page_frame, text="", font=('Segoe UI', 9),
        bg=COLORS['white'], fg=COLORS['text']
    )
    page_total_label.pack(side='left', padx=(5, 0))

    next_btn = create_modern_button(
        nav_frame, ">", go_next, COLORS['secondary'], width=3
    )
    next_btn.pack(side='left', padx=2)

    last_btn = create_modern_button(
        nav_frame, ">>", go_last, COLORS['secondary'], width=3
    )
    last_btn.pack(side='left', padx=2)

    def update_controls():
        """Update pagination controls state"""
        # Update page info
        update_page_info()

        # Update page entry
        page_entry.delete(0, tk.END)
        page_entry.insert(0, str(paginator.current_page))

        # Update total pages label
        page_total_label.config(text=f"of {paginator.total_pages}")

        # Update button states
        first_btn.config(state='normal' if paginator.current_page > 1 else 'disabled')
        prev_btn.config(state='normal' if paginator.current_page > 1 else 'disabled')
        next_btn.config(state='normal' if paginator.current_page < paginator.total_pages else 'disabled')
        last_btn.config(state='normal' if paginator.current_page < paginator.total_pages else 'disabled')
        page_entry.config(state='normal' if paginator.total_pages > 1 else 'disabled')

    return pagination_frame, update_controls


def view_uploaded_documents():
    """View uploaded cash management documents with pagination and optimized Firebase operations"""

    # Initialize paginator
    paginator = DocumentPaginator(DOCUMENTS_PER_PAGE)

    view_window = tk.Toplevel()
    view_window.title(f"Cash Management - View Documents v{VERSION}")
    view_window.geometry("1200x800")
    view_window.configure(bg=COLORS['light'])

    # Center the window
    view_window.update_idletasks()
    screen_width = view_window.winfo_screenwidth()
    screen_height = view_window.winfo_screenheight()
    window_width = view_window.winfo_width()
    window_height = view_window.winfo_height()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    view_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Header
    header_frame = create_styled_frame(view_window, COLORS['primary'])
    header_frame.pack(fill='x', pady=(0, 20), padx=20)

    header_label = tk.Label(
        header_frame,
        text=f"Cash Management - Document Browser v{VERSION} (Optimized)",
        font=('Segoe UI', 16, 'bold'),
        bg=COLORS['primary'],
        fg='white',
        pady=15
    )
    header_label.pack()

    # Filter section with improved layout
    filter_frame = create_styled_frame(view_window, COLORS['white'], relief='solid', bd=1)
    filter_frame.pack(fill='x', pady=(0, 10), padx=20)

    tk.Label(
        filter_frame,
        text="🔍 Filters & Search",
        font=('Segoe UI', 12, 'bold'),
        bg=COLORS['white'],
        fg=COLORS['text']
    ).pack(anchor='w', padx=15, pady=(15, 10))

    filters_container = tk.Frame(filter_frame, bg=COLORS['white'])
    filters_container.pack(fill='x', padx=15, pady=(0, 15))

    # Corporation filter
    corp_frame = tk.Frame(filters_container, bg=COLORS['white'])
    corp_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))

    tk.Label(corp_frame, text="Corporation:", font=('Segoe UI', 9, 'bold'), bg=COLORS['white']).pack(anchor='w')
    corp_filter_var = tk.StringVar()
    corp_filter_dropdown = ttk.Combobox(
        corp_frame,
        textvariable=corp_filter_var,
        font=('Segoe UI', 9),
        state="readonly",
        values=["All"] + CashManagementTransactionManager.get_corporations()
    )
    corp_filter_dropdown.set("All")
    corp_filter_dropdown.pack(fill='x')

    # Transaction type filter
    trans_frame = tk.Frame(filters_container, bg=COLORS['white'])
    trans_frame.pack(side='left', fill='x', expand=True, padx=(5, 10))

    tk.Label(trans_frame, text="Transaction Type:", font=('Segoe UI', 9, 'bold'), bg=COLORS['white']).pack(anchor='w')
    trans_filter_var = tk.StringVar()
    trans_filter_dropdown = ttk.Combobox(
        trans_frame,
        textvariable=trans_filter_var,
        font=('Segoe UI', 9),
        state="readonly",
        values=["All"] + CashManagementTransactionManager.get_transactions()
    )
    trans_filter_dropdown.set("All")
    trans_filter_dropdown.pack(fill='x')

    # Date range filter
    date_frame = tk.Frame(filters_container, bg=COLORS['white'])
    date_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))

    tk.Label(date_frame, text="Date Range:", font=('Segoe UI', 9, 'bold'), bg=COLORS['white']).pack(anchor='w')
    date_filter_var = tk.StringVar()
    date_filter_dropdown = ttk.Combobox(
        date_frame,
        textvariable=date_filter_var,
        font=('Segoe UI', 9),
        state="readonly",
        values=["All", "Today", "Last 7 Days", "Last 30 Days", "This Month"]
    )
    date_filter_dropdown.set("All")
    date_filter_dropdown.pack(fill='x')

    # Filter actions
    filter_actions_frame = tk.Frame(filter_frame, bg=COLORS['white'])
    filter_actions_frame.pack(fill='x', padx=15, pady=(0, 15))

    filter_btn = create_modern_button(
        filter_actions_frame,
        "🔍 Apply Filters",
        lambda: load_documents(),
        COLORS['primary'],
        width=15
    )
    filter_btn.pack(side='left')

    refresh_btn = create_modern_button(
        filter_actions_frame,
        "🔄 Refresh",
        lambda: refresh_documents(),
        COLORS['success'],
        width=12
    )
    refresh_btn.pack(side='left', padx=(10, 0))

    # Documents display section with improved header
    docs_frame = create_styled_frame(view_window, COLORS['white'], relief='solid', bd=1)
    docs_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

    # Enhanced headers
    headers_frame = create_styled_frame(docs_frame, COLORS['primary'])
    headers_frame.pack(fill='x', padx=0, pady=0)

    headers = [
        ("📄 File Name", 25),
        ("🏢 Corporation", 20),
        ("📊 Transaction Type", 20),
        ("📅 Date", 10),
        ("👤 Uploader", 12),
        ("⚙️ Actions", 15)
    ]

    for header, width in headers:
        tk.Label(
            headers_frame,
            text=header,
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['primary'],
            fg='white',
            anchor='w',
            width=width
        ).pack(side='left', padx=3, pady=8)

    # Scrollable documents list
    list_container = tk.Frame(docs_frame, bg=COLORS['white'])
    list_container.pack(fill='both', expand=True, padx=5, pady=5)

    docs_canvas = tk.Canvas(list_container, bg=COLORS['white'], highlightthickness=0)
    docs_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=docs_canvas.yview)
    docs_list_frame = tk.Frame(docs_canvas, bg=COLORS['white'])

    docs_list_frame.bind(
        "<Configure>",
        lambda e: docs_canvas.configure(scrollregion=docs_canvas.bbox("all"))
    )

    docs_canvas.create_window((0, 0), window=docs_list_frame, anchor="nw")
    docs_canvas.configure(yscrollcommand=docs_scrollbar.set)

    def on_docs_mousewheel(event):
        docs_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    docs_canvas.bind("<MouseWheel>", on_docs_mousewheel)

    docs_canvas.pack(side="left", fill="both", expand=True)
    docs_scrollbar.pack(side="right", fill="y")

    # Status section
    status_frame = create_styled_frame(docs_frame, COLORS['light'])
    status_frame.pack(fill='x', pady=5)

    status_label = tk.Label(
        status_frame,
        text="Loading documents...",
        font=('Segoe UI', 10),
        bg=COLORS['light'],
        fg=COLORS['text']
    )
    status_label.pack(pady=10)

    def get_current_filters():
        """Get current filter settings"""
        filters = {}

        corp_filter = corp_filter_var.get()
        if corp_filter and corp_filter != "All":
            filters['corporation'] = corp_filter

        trans_filter = trans_filter_var.get()
        if trans_filter and trans_filter != "All":
            filters['transaction_type'] = trans_filter

        date_filter = get_date_filter()
        if date_filter:
            filters['date_filter'] = date_filter

        return filters if filters else None

    def get_date_filter():
        """Get date filter based on selection"""
        filter_type = date_filter_var.get()
        today = datetime.datetime.now()

        if filter_type == "Today":
            return today.strftime("%Y-%m-%d")
        elif filter_type == "Last 7 Days":
            week_ago = today - datetime.timedelta(days=7)
            return week_ago.strftime("%Y-%m-%d")
        elif filter_type == "Last 30 Days":
            month_ago = today - datetime.timedelta(days=30)
            return month_ago.strftime("%Y-%m-%d")
        elif filter_type == "This Month":
            return today.strftime("%Y-%m-01")
        else:
            return None

    def open_document(file_url, file_name):
        """Open document in browser"""
        try:
            webbrowser.open(file_url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open document: {str(e)}")

    def download_document(file_url, file_name):
        """Download document"""
        try:
            import requests
            response = requests.get(file_url)

            if response.status_code == 200:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    initialname=file_name
                )

                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    messagebox.showinfo("Success", f"Document downloaded successfully to:\n{save_path}")
            else:
                messagebox.showerror("Error", "Failed to download document")

        except ImportError:
            messagebox.showwarning("Download",
                                   "Download feature requires 'requests' library.\nOpening in browser instead...")
            open_document(file_url, file_name)
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    def refresh_documents():
        """Refresh documents by clearing cache and reloading"""
        paginator.clear_cache()
        paginator.current_page = 1
        load_documents()

    def load_documents():
        """Load and display documents for current page with optimized Firebase queries"""
        try:
            # Clear existing documents
            for widget in docs_list_frame.winfo_children():
                widget.destroy()

            status_label.config(text="Loading documents...", fg=COLORS['text'])
            view_window.update_idletasks()

            # Get current filters
            filters = get_current_filters()

            # Get total count first (optimized query)
            total_count = paginator.get_total_count(filters)

            if total_count == 0:
                no_docs_label = tk.Label(
                    docs_list_frame,
                    text="No documents found matching the current filters.\nTry adjusting your search criteria or check if documents have been uploaded.",
                    font=('Segoe UI', 12),
                    bg=COLORS['white'],
                    fg=COLORS['text_light'],
                    justify='center'
                )
                no_docs_label.pack(pady=50)
                status_label.config(text="No documents found", fg=COLORS['warning'])

                # Hide pagination if no documents
                if 'pagination_controls' in locals():
                    pagination_frame.pack_forget()
                return

            # Get documents for current page
            documents = paginator.get_page_documents(paginator.current_page, filters)

            if not documents:
                no_docs_label = tk.Label(
                    docs_list_frame,
                    text="Error loading documents for this page.\nPlease try refreshing or contact support.",
                    font=('Segoe UI', 12),
                    bg=COLORS['white'],
                    fg=COLORS['danger'],
                    justify='center'
                )
                no_docs_label.pack(pady=50)
                status_label.config(text="Error loading page", fg=COLORS['danger'])
                return

            # Display documents with improved styling
            for i, doc_data in enumerate(documents):
                doc_frame = create_styled_frame(
                    docs_list_frame,
                    COLORS['light'] if i % 2 == 0 else COLORS['white'],
                    relief='solid',
                    bd=1
                )
                doc_frame.pack(fill='x', pady=1, padx=2)

                # Add hover effect
                def on_enter(e, frame=doc_frame):
                    frame.config(bg=COLORS['primary_light'] if frame.cget('bg') == COLORS['light'] else COLORS['light'])

                def on_leave(e, frame=doc_frame, original_bg=doc_frame.cget('bg')):
                    frame.config(bg=original_bg)

                doc_frame.bind("<Enter>", on_enter)
                doc_frame.bind("<Leave>", on_leave)

                # File name with file type icon
                file_name = doc_data.get('file_name', 'Unknown')
                display_name = file_name[:35] + "..." if len(file_name) > 35 else file_name

                name_label = tk.Label(
                    doc_frame,
                    text=f"📄 {display_name}",
                    font=('Segoe UI', 9),
                    bg=doc_frame['bg'],
                    fg=COLORS['text'],
                    anchor='w',
                    width=25
                )
                name_label.pack(side='left', padx=3, pady=4)
                name_label.bind("<Enter>", on_enter)
                name_label.bind("<Leave>", on_leave)

                # Corporation
                corp = doc_data.get('corporation', 'Unknown')
                display_corp = corp[:18] + "..." if len(corp) > 18 else corp
                corp_label = tk.Label(
                    doc_frame,
                    text=display_corp,
                    font=('Segoe UI', 9),
                    bg=doc_frame['bg'],
                    fg=COLORS['text'],
                    anchor='w',
                    width=20
                )
                corp_label.pack(side='left', padx=3, pady=4)
                corp_label.bind("<Enter>", on_enter)
                corp_label.bind("<Leave>", on_leave)

                # Transaction type
                trans_type = doc_data.get('transaction_type', 'Unknown')
                display_trans = trans_type[:18] + "..." if len(trans_type) > 18 else trans_type
                trans_label = tk.Label(
                    doc_frame,
                    text=display_trans,
                    font=('Segoe UI', 9),
                    bg=doc_frame['bg'],
                    fg=COLORS['text'],
                    anchor='w',
                    width=20
                )
                trans_label.pack(side='left', padx=3, pady=4)
                trans_label.bind("<Enter>", on_enter)
                trans_label.bind("<Leave>", on_leave)

                # Upload date
                upload_date = doc_data.get('upload_date', 'Unknown')
                date_label = tk.Label(
                    doc_frame,
                    text=upload_date,
                    font=('Segoe UI', 9),
                    bg=doc_frame['bg'],
                    fg=COLORS['text'],
                    anchor='w',
                    width=10
                )
                date_label.pack(side='left', padx=3, pady=4)
                date_label.bind("<Enter>", on_enter)
                date_label.bind("<Leave>", on_leave)

                # Uploaded by
                uploaded_by = doc_data.get('uploaded_by', 'Unknown')
                display_uploader = uploaded_by[:10] + "..." if len(uploaded_by) > 10 else uploaded_by
                uploader_label = tk.Label(
                    doc_frame,
                    text=display_uploader,
                    font=('Segoe UI', 9),
                    bg=doc_frame['bg'],
                    fg=COLORS['text'],
                    anchor='w',
                    width=12
                )
                uploader_label.pack(side='left', padx=3, pady=4)
                uploader_label.bind("<Enter>", on_enter)
                uploader_label.bind("<Leave>", on_leave)

                # Actions with improved buttons
                actions_frame = tk.Frame(doc_frame, bg=doc_frame['bg'])
                actions_frame.pack(side='left', padx=3, pady=4)
                actions_frame.bind("<Enter>", on_enter)
                actions_frame.bind("<Leave>", on_leave)

                file_url = doc_data.get('file_url', '')
                doc_id = doc_data.get('doc_id', '')

                # View button
                view_btn = tk.Button(
                    actions_frame,
                    text="👁 View",
                    command=lambda url=file_url, name=file_name: open_document(url, name),
                    bg=COLORS['primary'],
                    fg='white',
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    cursor='hand2',
                    width=6,
                    height=1
                )
                view_btn.pack(side='left', padx=1)

                # Download button
                download_btn = tk.Button(
                    actions_frame,
                    text="⬇ Get",
                    command=lambda url=file_url, name=file_name: download_document(url, name),
                    bg=COLORS['success'],
                    fg='white',
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    cursor='hand2',
                    width=5,
                    height=1
                )
                download_btn.pack(side='left', padx=1)

                # Delete button
                delete_btn = tk.Button(
                    actions_frame,
                    text="🗑 Del",
                    command=lambda doc_id=doc_id, url=file_url, name=file_name: delete_document(
                        doc_id, url, name, load_documents, paginator
                    ),
                    bg=COLORS['danger'],
                    fg='white',
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    cursor='hand2',
                    width=5,
                    height=1
                )
                delete_btn.pack(side='left', padx=1)

            # Update status
            start_doc = (paginator.current_page - 1) * paginator.page_size + 1
            end_doc = min(paginator.current_page * paginator.page_size, paginator.total_documents)

            status_label.config(
                text=f"Showing {start_doc}-{end_doc} of {paginator.total_documents} documents (Page {paginator.current_page} of {paginator.total_pages})",
                fg=COLORS['success']
            )

            # Update pagination controls
            if 'update_pagination' in locals():
                update_pagination()

        except Exception as e:
            status_label.config(text=f"Error loading documents: {str(e)}", fg=COLORS['danger'])
            messagebox.showerror("Error", f"Failed to load documents: {str(e)}")

    # Create pagination controls
    pagination_frame, update_pagination = create_pagination_controls(view_window, paginator, load_documents)

    # Bind filter changes to reload with pagination reset
    def on_filter_change(*args):
        paginator.current_page = 1
        paginator.clear_cache()
        load_documents()

    corp_filter_dropdown.bind('<<ComboboxSelected>>', on_filter_change)
    trans_filter_dropdown.bind('<<ComboboxSelected>>', on_filter_change)
    date_filter_dropdown.bind('<<ComboboxSelected>>', on_filter_change)

    # Load documents initially
    load_documents()

    # Update pagination controls
    update_pagination()

    print(f"[cash_management] Document viewer with pagination opened (Page size: {DOCUMENTS_PER_PAGE})")


def open_cash_management(next_user_data):
    """
    Cash Management dashboard for NDA users - Version 1.2.0 with optimized Firebase operations
    """
    # Initialize cash management transaction manager
    cash_manager = CashManagementTransactionManager()

    # Get user info
    username = next_user_data.get('username', 'Unknown User')
    user_role = next_user_data.get('role', 'NDA')

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
                text="No files selected\nClick 'Add Files' to select documents",
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

            display_name = file_info['name']
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."

            name_label = tk.Label(
                info_frame,
                text=f"{display_name}",
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

        if selected_transaction:
            # Check if this transaction has sub-categories
            if cash_manager.has_sub_categories(selected_transaction):
                # Get sub-categories and show the section
                sub_categories = cash_manager.get_sub_categories(selected_transaction)
                sub_category_dropdown['values'] = sub_categories

                # Update label to be more specific
                sub_category_label.config(text=f"{selected_transaction} Type")

                # Show the sub-category section
                sub_category_section.pack(fill='x', pady=(0, 15), padx=5, after=trans_section)
            else:
                # Hide the sub-category section
                sub_category_section.pack_forget()
        else:
            sub_category_section.pack_forget()

    def validate_inputs():
        """Enhanced validation for cash management"""
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
            all_corps = cash_manager.get_corporations()

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
                    # Auto-correct the case and update the variable
                    corporation_var.set(exact_match)
                    selected_corp = exact_match
                else:
                    # No valid match found
                    errors.append(f"Corporation '{selected_corp}' not found. Please select from the list.")

        # Transaction type validation
        if not selected_transaction:
            errors.append("Please select a transaction type")
        elif not cash_manager.validate_transaction(selected_transaction):
            errors.append(f"Invalid transaction type '{selected_transaction}'")
        elif cash_manager.has_sub_categories(selected_transaction) and not selected_sub:
            errors.append(f"Please select a {selected_transaction} type")
        elif selected_sub and not cash_manager.validate_transaction(selected_transaction, selected_sub):
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

                # Use batch operations for better Firebase performance
                batch_timestamp = int(time.time())

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

                        # Create unique file name to prevent conflicts
                        file_name = f"{current_date}_{batch_timestamp}_{i}_{file_info['name']}"
                        storage_path = f"Cash Management/{file_name}"

                        # Upload to Firebase Storage
                        storage.child(storage_path).put(file_info['path'])
                        file_url = storage.child(storage_path).get_url(None)

                        # Optimized database write with batch operations
                        doc_data = {
                            "corporation": corporation,
                            "department": "Cash Management",
                            "transaction_type": final_transaction_type,
                            "uploaded_by": uploaded_by,
                            "upload_date": current_date,
                            "file_name": file_info['name'],
                            "file_url": file_url,
                            "file_size": file_info['size'],
                            "upload_batch": batch_timestamp,
                            "user_role": user_role,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        }

                        # Add document to Firestore
                        doc_ref = db.collection("cash_management_uploads").add(doc_data)

                        file_info['status'] = 'uploaded'
                        uploaded_files.append(file_info['name'])

                    except Exception as e:
                        file_info['status'] = 'failed'
                        failed_files.append(f"{file_info['name']}: {str(e)}")
                        print(f"Upload error for {file_info['name']}: {e}")

                progress_var.set(100)
                update_file_list()

                # Show results based on upload success
                if uploaded_files and not failed_files:
                    status_label.config(
                        text=f"Successfully uploaded {len(uploaded_files)} file{'s' if len(uploaded_files) != 1 else ''}!",
                        fg=COLORS['success']
                    )
                    messagebox.showinfo("Upload Complete",
                                        f"Successfully uploaded {len(uploaded_files)} documents!\n\nOptimized Firebase operations used for better performance.")

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
                        text=f"{len(uploaded_files)} uploaded, {len(failed_files)} failed",
                        fg=COLORS['warning']
                    )
                    messagebox.showwarning(
                        "Partial Upload",
                        f"Uploaded: {len(uploaded_files)} files\nFailed: {len(failed_files)} files\n\nCheck the failed files and try uploading them again."
                    )
                else:
                    status_label.config(text="All uploads failed", fg=COLORS['danger'])
                    messagebox.showerror("Upload Failed",
                                         "All file uploads failed. Please check your connection and try again.")

            except Exception as e:
                progress_var.set(0)
                status_label.config(text="Upload failed", fg=COLORS['danger'])
                messagebox.showerror("Upload Error", f"Unexpected error during upload: {str(e)}")
                print(f"Upload error: {e}")
            finally:
                upload_btn.config(state='normal', text='Upload All Files', bg=COLORS['primary'])
                clear_btn.config(state='normal')

        Thread(target=do_upload).start()

    # Create main window
    popup = tk.Tk()
    popup.title(f"Cash Management - Document Upload v{VERSION}")
    popup.geometry("600x750")
    popup.configure(bg=COLORS['light'])
    popup.resizable(False, True)

    popup.update_idletasks()

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    window_width = popup.winfo_width()
    window_height = popup.winfo_height()

    x = (screen_width - window_width) // 2
    y = max(10, (screen_height - window_height - 80) // 2)  # 80px buffer for taskbar

    if y + window_height > screen_height - 60:
        y = screen_height - window_height - 60

    popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

    max_height = screen_height - 100  # 100px buffer for taskbar and title bar
    if window_height > max_height:
        popup.geometry(f"500x{max_height}")
        popup.resizable(False, True)  # Allow vertical resize if needed

    # Variables
    corporation_var = tk.StringVar()
    transaction_type_var = tk.StringVar()
    sub_category_var = tk.StringVar()
    uploaded_by_var = tk.StringVar()
    progress_var = tk.IntVar(value=0)

    # Main container
    main_frame = create_styled_frame(popup, COLORS['white'])
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Header with version
    header_frame = create_styled_frame(main_frame, COLORS['primary'])
    header_frame.pack(fill='x', pady=(0, 20))

    header_label = tk.Label(
        header_frame,
        text=f"Cash Management - Document Upload v{VERSION}",
        font=('Segoe UI', 16, 'bold'),
        bg=COLORS['primary'],
        fg='white',
        pady=15
    )
    header_label.pack()

    # Version info display
    version_info_frame = create_styled_frame(main_frame, COLORS['light'], relief='solid', bd=1)
    version_info_frame.pack(fill='x', pady=(0, 15), padx=5)

    version_label = tk.Label(
        version_info_frame,
        text=f"Version {VERSION} - {VERSION_DATE} | User: {username} ({user_role}) | Features: Upload, View (Paginated), Delete, Optimized Firebase",
        font=('Segoe UI', 9),
        bg=COLORS['light'],
        fg=COLORS['text'],
        pady=8
    )
    version_label.pack()

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

    # Corporation section
    all_corporations = cash_manager.get_corporations()
    corp_section = create_corporation_section_alternative(form_frame, corporation_var, all_corporations)

    # Transaction Type section
    trans_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)
    trans_section.pack(fill='x', pady=(0, 15), padx=5)

    trans_label = tk.Label(
        trans_section,
        text="Cash Management Transaction Type",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['light'],
        fg=COLORS['text'],
        anchor='w'
    )
    trans_label.pack(fill='x', padx=15, pady=(15, 5))

    # Set transaction types for cash management
    cash_transactions = cash_manager.get_transactions()
    transaction_dropdown = ttk.Combobox(
        trans_section,
        textvariable=transaction_type_var,
        state="readonly",
        font=('Segoe UI', 10),
        values=cash_transactions
    )
    transaction_dropdown.pack(fill='x', padx=15, pady=(0, 15))
    transaction_dropdown.bind('<<ComboboxSelected>>', on_transaction_change)

    # Sub-category section (initially hidden)
    sub_category_section = create_styled_frame(form_frame, COLORS['light'], relief='solid', bd=1)

    sub_category_label = tk.Label(
        sub_category_section,
        text="Sub-Category",
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
        text="Uploaded By",
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
        text="Enter the name of the person uploading these documents",
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
        text="Document Files",
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
        "Add Files",
        add_files,
        COLORS['success'],
        COLORS['success'],
        width=12
    )
    add_files_btn.pack(side='left')

    clear_btn = create_modern_button(
        file_btn_frame,
        "Clear All",
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
        text="Supported: PDF, JPG, PNG, GIF, BMP, WebP, JPEG (Max 100MB per file)",
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
        text="Upload Progress",
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
        "Upload All Files",
        upload_files,
        COLORS['primary'],
        COLORS['primary_hover'],
        width=18
    )
    upload_btn.pack(side='left', padx=(0, 10))

    view_btn = create_modern_button(
        button_frame,
        "View Documents",
        view_uploaded_documents,
        COLORS['secondary'],
        width=15
    )
    view_btn.pack(side='left', padx=(0, 10))

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
        "Logout",
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

    print(
        f"[cash_management] Cash management dashboard v{VERSION} opened for {username} - {user_role} with optimized Firebase operations")

    popup.mainloop()


# Main function to be called from login
def main(next_user_data):
    try:
        # Validate user data
        if not next_user_data:
            messagebox.showerror("Error", "No user data provided")
            return

        if 'username' not in next_user_data:
            messagebox.showerror("Error", "Username not specified")
            return

        # Open the cash management dashboard
        open_cash_management(next_user_data)

    except Exception as e:
        print(f"[cash_management] Error opening cash management dashboard v{VERSION}: {e}")
        messagebox.showerror("Dashboard Error", f"Failed to open cash management dashboard: {e}")