import tkinter as tk
from tkinter import messagebox, ttk
import calendar  # Add this line
from Colors import COLORS
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import firestore
from collections import defaultdict, Counter
import threading
import time

try:
    from tkcalendar import DateEntry
    HAS_DATE_PICKER = True
except ImportError:
    HAS_DATE_PICKER = False


class CustomCalendar:
    def __init__(self, parent, textvariable, **kwargs):
        self.textvariable = textvariable
        self.parent = parent
        self.callback = kwargs.get('callback', None)

        # Initial date
        initial_date = kwargs.get('initial_date', datetime.now())
        self.current_month = initial_date.month
        self.current_year = initial_date.year
        self.selected_date = initial_date

        # Main frame
        self.cal_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        self.setup_calendar()

    def setup_calendar(self):
        # Clear existing widgets
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        # Header with navigation
        header_frame = tk.Frame(self.cal_frame, bg='#2196F3')
        header_frame.pack(fill='x')

        # Previous month button
        tk.Button(
            header_frame,
            text='<',
            font=('Arial', 12, 'bold'),
            bg='#2196F3',
            fg='white',
            bd=0,
            cursor='hand2',
            command=self.prev_month
        ).pack(side='left', padx=5, pady=5)

        # Month/Year display
        month_year_text = f"{calendar.month_name[self.current_month]} {self.current_year}"
        tk.Label(
            header_frame,
            text=month_year_text,
            font=('Arial', 12, 'bold'),
            bg='#2196F3',
            fg='white'
        ).pack(side='left', expand=True)

        # Next month button
        tk.Button(
            header_frame,
            text='>',
            font=('Arial', 12, 'bold'),
            bg='#2196F3',
            fg='white',
            bd=0,
            cursor='hand2',
            command=self.next_month
        ).pack(side='right', padx=5, pady=5)

        # Days header
        days_frame = tk.Frame(self.cal_frame, bg='white')
        days_frame.pack(fill='x')

        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            tk.Label(
                days_frame,
                text=day,
                font=('Arial', 10, 'bold'),
                bg='#E3F2FD',
                fg='#1976D2',
                width=4
            ).pack(side='left', padx=1, pady=1)

        # Calendar grid
        cal_grid = tk.Frame(self.cal_frame, bg='white')
        cal_grid.pack(fill='both', expand=True, padx=5, pady=5)

        # Get calendar data
        cal_data = calendar.monthcalendar(self.current_year, self.current_month)

        for week_num, week in enumerate(cal_data):
            week_frame = tk.Frame(cal_grid, bg='white')
            week_frame.pack(fill='x')

            for day in week:
                if day == 0:
                    # Empty day
                    tk.Label(
                        week_frame,
                        text='',
                        width=4,
                        height=2,
                        bg='white'
                    ).pack(side='left', padx=1, pady=1)
                else:
                    # Regular day
                    day_btn = tk.Button(
                        week_frame,
                        text=str(day),
                        width=4,
                        height=1,
                        font=('Arial', 10),
                        cursor='hand2',
                        command=lambda d=day: self.select_date(d)
                    )

                    # Highlight today
                    today = datetime.now()
                    if (day == today.day and self.current_month == today.month
                            and self.current_year == today.year):
                        day_btn.config(bg='#FFC107', fg='black', font=('Arial', 10, 'bold'))
                    else:
                        day_btn.config(bg='white', fg='black', relief='flat', bd=1)
                        day_btn.bind('<Enter>', lambda e, btn=day_btn: btn.config(bg='#E3F2FD'))
                        day_btn.bind('<Leave>', lambda e, btn=day_btn: btn.config(bg='white'))

                    day_btn.pack(side='left', padx=1, pady=1)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.setup_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.setup_calendar()

    def select_date(self, day):
        selected_date = datetime(self.current_year, self.current_month, day)
        date_str = selected_date.strftime('%Y-%m-%d')
        self.textvariable.set(date_str)
        if self.callback:
            self.callback()

    def pack(self, **kwargs):
        self.cal_frame.pack(**kwargs)


class BetterDateEntry:
    def __init__(self, parent, textvariable, **kwargs):
        self.textvariable = textvariable
        self.parent = parent
        self.callback = kwargs.get('callback', None)

        # Get parent background color safely
        try:
            parent_bg = parent.cget('bg')
        except:
            parent_bg = 'white'

        self.main_frame = tk.Frame(parent, bg=parent_bg)

        # Date entry field
        self.date_entry = tk.Entry(
            self.main_frame,
            textvariable=textvariable,
            font=('Segoe UI', 11),
            width=12,
            relief='solid',
            bd=1,
            bg='white',
            fg='black'
        )
        self.date_entry.pack(side='left', padx=(0, 5))

        # Calendar button
        self.cal_button = tk.Button(
            self.main_frame,
            text='📅',
            font=('Arial', 12),
            cursor='hand2',
            relief='flat',
            bd=1,
            bg='#f0f0f0',
            command=self.show_calendar
        )
        self.cal_button.pack(side='left')

        # Popup calendar window
        self.cal_window = None

        # Bind Enter key to entry
        self.date_entry.bind('<Return>', self.on_date_entered)

    def on_date_entered(self, event=None):
        try:
            date_str = self.textvariable.get()
            datetime.strptime(date_str, '%Y-%m-%d')  # Validate format
            if self.callback:
                self.callback()
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format")

    def show_calendar(self):
        if self.cal_window and self.cal_window.winfo_exists():
            self.cal_window.destroy()

        self.cal_window = tk.Toplevel(self.parent)
        self.cal_window.title("Select Date")
        self.cal_window.resizable(False, False)

        # Position near the entry
        try:
            x = self.main_frame.winfo_rootx()
            y = self.main_frame.winfo_rooty() + self.main_frame.winfo_height()
            self.cal_window.geometry(f"+{x}+{y}")
        except:
            # Fallback positioning
            self.cal_window.geometry("300x250+300+300")

        # Get current date from entry or use today
        try:
            current_date = datetime.strptime(self.textvariable.get(), '%Y-%m-%d')
        except ValueError:
            current_date = datetime.now()

        # Calendar widget
        calendar_widget = CustomCalendar(
            self.cal_window,
            self.textvariable,
            callback=self.close_calendar,
            initial_date=current_date
        )
        calendar_widget.pack(padx=5, pady=5)

        # Close button
        tk.Button(
            self.cal_window,
            text="Close",
            command=self.close_calendar,
            bg='#f0f0f0',
            relief='flat',
            bd=1,
            cursor='hand2'
        ).pack(pady=5)

        # Make window modal
        self.cal_window.transient(self.parent)
        self.cal_window.grab_set()
        self.cal_window.focus_set()

    def close_calendar(self):
        if self.cal_window:
            self.cal_window.destroy()
            self.cal_window = None
        if self.callback:
            self.callback()

    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.main_frame.grid(**kwargs)


class NotificationSystem:
    def __init__(self, parent_window, admin_data):
        self.parent_window = parent_window
        self.admin_data = admin_data
        self.notifications = []
        self.notification_window = None
        self.db = firestore.client()
        self.upload_stats = {}
        self.last_check_time = datetime.now()

        # Initialize with admin's default group but allow selection
        self.admin_default_group = admin_data.get("group", "group1")
        self.selected_group = self.admin_default_group  # Current selected group
        self.available_groups = self._get_available_groups()
        self.group_corporations = self._get_group_corporations(self.selected_group)

        # Start background monitoring
        self.start_upload_monitoring()

    def _get_available_groups(self):
        """Get list of available groups"""
        available = []

        # Check which group modules are available
        for group_name in ["group1", "group2", "group3"]:
            try:
                module_name = f"{group_name}_corporations"
                exec(f"from corporations import {module_name}")
                available.append(group_name)
            except ImportError:
                continue

        return available if available else ["group1"]  # Fallback

    def _get_group_corporations(self, group_name=None):
        """Get corporations based on the specified group"""
        if group_name is None:
            group_name = self.selected_group

        group_name = group_name.lower()

        if "group1" in group_name or group_name == "group1":
            try:
                from corporations import group1_corporations
                return group1_corporations
            except ImportError:
                return []
        elif "group2" in group_name or group_name == "group2":
            try:
                from corporations import group2_corporations
                return group2_corporations
            except ImportError:
                return []
        elif "group3" in group_name or group_name == "group3":
            try:
                from corporations import group3_corporations
                return group3_corporations
            except ImportError:
                return []
        else:
            # Default fallback
            try:
                from corporations import group1_corporations
                return group1_corporations
            except ImportError:
                return []

    def change_group(self, new_group):
        """Change the selected group and update corporations"""
        if new_group in self.available_groups:
            self.selected_group = new_group
            self.group_corporations = self._get_group_corporations(new_group)

            # Refresh notifications and data for new group
            self.refresh_notifications()

            # Update window title if notification window is open
            if self.notification_window and self.notification_window.winfo_exists():
                self.notification_window.title(f"🔔 Monitoring Dashboard - {self.selected_group.upper()}")

            return True
        return False

    def get_font_size(self, base_size):
        """Get responsive font size"""
        screen_width = self.parent_window.winfo_screenwidth()
        screen_height = self.parent_window.winfo_screenheight()
        scale_factor = min(screen_width / 1920, screen_height / 1080)
        font_scale = max(0.8, min(1.2, scale_factor))
        return max(8, int(base_size * font_scale))

    def start_upload_monitoring(self):
        """Start monitoring uploads in background thread"""

        def monitor_uploads():
            while True:
                try:
                    self.check_new_uploads()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    print(f"Error monitoring uploads: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

        monitor_thread = threading.Thread(target=monitor_uploads, daemon=True)
        monitor_thread.start()

    def check_new_uploads(self):
        """Check for new uploads and calculate daily department totals"""
        try:
            # Get uploads from the last 7 days for better tracking
            week_ago = datetime.now() - timedelta(days=7)
            today = datetime.now().strftime("%Y-%m-%d")

            uploads_ref = self.db.collection('head_office_uploads')
            query = uploads_ref.where('timestamp', '>=', week_ago)

            docs = query.get()

            # Group uploads by date and department for aggregation
            daily_department_stats = defaultdict(lambda: defaultdict(lambda: {
                'files': [],
                'total_count': 0,
                'total_size': 0,
                'uploaders': set(),
                'transaction_types': set()
            }))

            for doc in docs:
                data = doc.to_dict()
                department = data.get('department', 'Unknown Department')
                upload_date = data.get('upload_date', 'Unknown Date')
                file_name = data.get('file_name', 'Unknown File')
                file_size = data.get('file_size', 0)
                uploaded_by = data.get('uploaded_by', 'Unknown User')
                transaction_type = data.get('transaction_type', 'Unknown Type')

                # Add to daily stats
                stats = daily_department_stats[upload_date][department]
                stats['files'].append({
                    'file_name': file_name,
                    'file_size': file_size,
                    'uploaded_by': uploaded_by,
                    'transaction_type': transaction_type,
                    'timestamp': data.get('timestamp')
                })
                stats['total_count'] += 1
                stats['total_size'] += file_size
                stats['uploaders'].add(uploaded_by)
                stats['transaction_types'].add(transaction_type)

            # Update notifications with aggregated data
            self.update_notifications_from_aggregated_stats(daily_department_stats)

        except Exception as e:
            print(f"Error checking uploads: {e}")

    def get_branches_without_upload_for_date(self, target_date):
        """Get branches that haven't uploaded for a specific date, filtered by group corporations"""
        try:
            # Get all branches that uploaded on target_date from group corporations
            branches_with_upload = set()

            # Convert group_corporations to list and normalize case
            if isinstance(self.group_corporations, set):
                group_corps_list = list(self.group_corporations)
            else:
                group_corps_list = self.group_corporations

            # Normalize group corporations to uppercase for comparison
            normalized_group_corps = {corp.strip().upper() for corp in group_corps_list}

            print(f"Debug - Target date: {target_date}")
            print(f"Debug - Group corporations: {normalized_group_corps}")

            # Query uploads for target date using date field only
            docs = self.db.collection("Uploaded_Images").where("date", "==", target_date).stream()

            upload_found = False
            azalea_uploads = []  # Special tracking for AZALEA

            for doc in docs:
                upload_found = True
                data = doc.to_dict()
                corporation = data.get("corporations", "").strip().upper()
                branch = data.get("branch", "").strip().upper()  # Normalize branch name too

                # Special tracking for AZALEA branch
                if branch == "AZALEA":
                    azalea_uploads.append({
                        'corporation': corporation,
                        'branch': branch,
                        'doc_id': doc.id,
                        'date': data.get("date"),
                        'in_group': corporation in normalized_group_corps
                    })
                    print(
                        f"DEBUG AZALEA - Found AZALEA upload: Corp='{corporation}', Date='{data.get('date')}', InGroup={corporation in normalized_group_corps}")

                print(f"Debug - Found upload: Corporation='{corporation}', Branch='{branch}'")

                # Check if corporation belongs to this group (exact match)
                if corporation in normalized_group_corps:
                    if branch:
                        branches_with_upload.add(branch)
                        print(f"Debug - Added branch with upload: {branch}")
                else:
                    print(f"Debug - Corporation '{corporation}' not in group")

            # Special debug output for AZALEA
            if azalea_uploads:
                print(f"DEBUG AZALEA - Total AZALEA uploads found: {len(azalea_uploads)}")
                for upload in azalea_uploads:
                    print(f"DEBUG AZALEA - Upload details: {upload}")
            else:
                print(f"DEBUG AZALEA - No AZALEA uploads found for date {target_date}")

            # Also check if AZALEA appears with different case variations
            print(f"DEBUG AZALEA - Checking for case variations...")
            docs_recheck = self.db.collection("Uploaded_Images").where("date", "==", target_date).stream()
            for doc in docs_recheck:
                data = doc.to_dict()
                branch_raw = data.get("branch", "").strip()
                if "azalea" in branch_raw.lower():
                    print(f"DEBUG AZALEA - Found case variation: '{branch_raw}' (Corp: {data.get('corporations')})")

            if not upload_found:
                print(f"Debug - No uploads found for date {target_date}")

            print(f"Debug - Branches with uploads on {target_date}: {branches_with_upload}")

            # Get all possible branches from this group's historical data
            all_branches_in_group = set()

            # Query historical data in chunks due to Firestore limitations
            for i in range(0, len(group_corps_list), 10):
                chunk = group_corps_list[i:i + 10]

                # Use exact corporation names from the list (no case normalization in query)
                historical_docs = self.db.collection("Uploaded_Images").where(
                    "corporations", "in", chunk
                ).limit(1000).stream()

                for doc in historical_docs:
                    data = doc.to_dict()
                    corporation = data.get("corporations", "").strip().upper()
                    branch = data.get("branch", "").strip().upper()  # Normalize branch name

                    # Double-check corporation matches (normalized comparison)
                    if corporation in normalized_group_corps and branch:
                        all_branches_in_group.add(branch)

            print(f"Debug - All branches in group: {all_branches_in_group}")

            # Return branches that exist in the group but haven't uploaded on target date
            branches_without_upload = all_branches_in_group - branches_with_upload

            print(f"Debug - Branches without upload: {branches_without_upload}")

            return sorted(list(branches_without_upload))

        except Exception as e:
            print(f"Error getting branches without upload for {target_date}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def open_notifications(self):
        """Open the notifications window with group selection and tabs"""
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.lift()
            return

        self.notification_window = tk.Toplevel(self.parent_window)
        self.notification_window.title(f"🔔 Monitoring Dashboard - {self.selected_group.upper()}")

        # Responsive window size
        screen_width = self.parent_window.winfo_screenwidth()
        screen_height = self.parent_window.winfo_screenheight()
        font_scale = max(0.8, min(1.2, min(screen_width / 1920, screen_height / 1080)))

        window_width = max(600, min(900, int(800 * font_scale)))
        window_height = max(500, min(800, int(700 * font_scale)))

        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.notification_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.notification_window.configure(bg=COLORS['background'])
        self.notification_window.transient(self.parent_window)
        self.notification_window.grab_set()

        # Header with group selection
        header_frame = tk.Frame(self.notification_window, bg=COLORS['secondary'], height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        header_content = tk.Frame(header_frame, bg=COLORS['secondary'])
        header_content.pack(expand=True, fill="both")

        # Title
        tk.Label(
            header_content,
            text="📊 Monitoring Dashboard",
            font=("Segoe UI", self.get_font_size(16), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(pady=(10, 5))

        # Group selection frame
        group_frame = tk.Frame(header_content, bg=COLORS['secondary'])
        group_frame.pack(pady=(0, 5))

        tk.Label(
            group_frame,
            text="Group:",
            font=("Segoe UI", self.get_font_size(11), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(side="left", padx=(0, 5))

        # Group selection dropdown
        self.group_var = tk.StringVar(value=self.selected_group)
        group_dropdown = ttk.Combobox(
            group_frame,
            textvariable=self.group_var,
            values=[g.upper() for g in self.available_groups],
            state="readonly",
            width=10,
            font=("Segoe UI", self.get_font_size(10))
        )
        group_dropdown.pack(side="left", padx=(0, 10))
        group_dropdown.bind("<<ComboboxSelected>>", self.on_group_change)

        # Date info
        today_str = datetime.now().strftime("%B %d, %Y")
        tk.Label(
            header_content,
            text=f"{today_str}",
            font=("Segoe UI", self.get_font_size(11)),
            bg=COLORS['secondary'],
            fg=COLORS['accent']
        ).pack()

        # Create notebook for tabs
        main_frame = tk.Frame(self.notification_window, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.theme_use('clam')

        # Configure tab styles
        style.configure('Custom.TNotebook', background=COLORS['background'])
        style.configure('Custom.TNotebook.Tab',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        padding=[20, 10])
        style.map('Custom.TNotebook.Tab',
                  background=[('selected', COLORS['secondary']),
                              ('active', COLORS['accent'])],
                  foreground=[('selected', 'white')])

        notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        notebook.pack(fill="both", expand=True)

        # Create frames for each tab
        departments_frame = tk.Frame(notebook, bg=COLORS['background'])
        branches_frame = tk.Frame(notebook, bg=COLORS['background'])

        notebook.add(departments_frame, text="🏭 Departments")
        notebook.add(branches_frame, text="🏢 Branches")

        # Initialize tabs
        self.create_departments_tab(departments_frame)
        self.create_branches_tab(branches_frame)

        # Close button
        close_frame = tk.Frame(self.notification_window, bg=COLORS['background'])
        close_frame.pack(fill="x", padx=20, pady=(0, 20))

        close_btn = tk.Button(
            close_frame,
            text="✕ Close",
            font=("Segoe UI", self.get_font_size(11), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.notification_window.destroy
        )
        close_btn.pack()

        # ESC key to close
        self.notification_window.bind('<Escape>', lambda e: self.notification_window.destroy())
        self.notification_window.focus_set()

    def on_group_change(self, event):
        """Handle group selection change"""
        new_group = self.group_var.get().lower()

        if self.change_group(new_group):
            # Show loading message
            messagebox.showinfo(
                "Group Changed",
                f"Switched to {new_group.upper()}. Refreshing data..."
            )

            # Refresh the branches tab if it exists
            if hasattr(self, 'branches_content_frame'):
                self.load_branches_data()

    # Keep all existing methods but update references to self.group to use self.selected_group
    def create_departments_tab(self, parent_frame):
        """Create the departments tab with existing functionality"""
        # Header with refresh button
        header_frame = tk.Frame(parent_frame, bg=COLORS['surface'], relief="flat", bd=1)
        header_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(
            header_frame,
            text="🏭 Department Upload Activities",
            font=("Segoe UI", self.get_font_size(14), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=15, pady=10)

        # Summary and Refresh buttons
        btn_frame = tk.Frame(header_frame, bg=COLORS['surface'])
        btn_frame.pack(side="right", padx=15, pady=10)

        summary_btn = tk.Button(
            btn_frame,
            text="📊 Daily Summary",
            font=("Segoe UI", self.get_font_size(10), "bold"),
            bg=COLORS['success'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.show_daily_summary
        )
        summary_btn.pack(side="left", padx=(0, 5))

        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            font=("Segoe UI", self.get_font_size(10), "bold"),
            bg=COLORS['primary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.refresh_notifications
        )
        refresh_btn.pack(side="left")

        # Scrollable content area for notifications
        content_frame = tk.Frame(parent_frame, bg=COLORS['background'])
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create scrollable frame
        canvas = tk.Canvas(content_frame, bg=COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['background'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store reference for refreshing
        self.scrollable_frame = scrollable_frame

        # Load and display notifications
        self.display_notifications()

        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

    # Updated create_branches_tab method for your NotificationSystem class

    def create_branches_tab(self, parent_frame):
        """Create the branches monitoring tab with improved date picker"""
        # Header with date picker
        header_frame = tk.Frame(parent_frame, bg=COLORS['surface'], relief="flat", bd=1)
        header_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(
            header_frame,
            text="🏢 Branch Upload Monitoring",
            font=("Segoe UI", self.get_font_size(14), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=15, pady=10)

        # Date selection frame
        date_frame = tk.Frame(header_frame, bg=COLORS['surface'])
        date_frame.pack(side="right", padx=15, pady=10)

        tk.Label(
            date_frame,
            text="Select Date:",
            font=("Segoe UI", self.get_font_size(11), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left", padx=(0, 5))

        # Initialize date variable
        self.selected_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        # Use BetterDateEntry instead of DateEntry
        self.date_picker = BetterDateEntry(
            date_frame,
            textvariable=self.selected_date,
            callback=self.load_branches_data
        )
        self.date_picker.pack(side="left", padx=(0, 10))

        # Check button
        check_btn = tk.Button(
            date_frame,
            text="🔍 Check",
            font=("Segoe UI", self.get_font_size(10), "bold"),
            bg=COLORS['primary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.load_branches_data
        )
        check_btn.pack(side="left")

        # Content area for branches
        self.branches_content_frame = tk.Frame(parent_frame, bg=COLORS['background'])
        self.branches_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial load
        self.load_branches_data()

    # Also add the BetterDateEntry class to your file at the top, after imports:



    def load_branches_data(self):
        """Load branches data for selected date"""
        # Clear existing content
        for widget in self.branches_content_frame.winfo_children():
            widget.destroy()

        # Show loading message
        loading_label = tk.Label(
            self.branches_content_frame,
            text="🔄 Loading branch data...",
            font=("Segoe UI", self.get_font_size(12)),
            bg=COLORS['background'],
            fg=COLORS['muted']
        )
        loading_label.pack(pady=50)

        def load_in_background():
            try:
                target_date = self.selected_date.get()
                branches_without_upload = self.get_branches_without_upload_for_date(target_date)

                def update_ui():
                    loading_label.destroy()
                    self.display_branches_content(branches_without_upload, target_date)

                self.notification_window.after(0, update_ui)

            except Exception as e:
                def show_error():
                    loading_label.config(
                        text=f"❌ Error loading branches: {str(e)}",
                        fg=COLORS['danger']
                    )

                self.notification_window.after(0, show_error)

        # Start loading in background thread
        threading.Thread(target=load_in_background, daemon=True).start()

    def display_branches_content(self, branches_without_upload, target_date):
        """Display branches that haven't uploaded on the target date"""
        # Info section
        info_frame = tk.Frame(self.branches_content_frame, bg=COLORS['surface'], relief="flat", bd=1)
        info_frame.pack(fill="x", pady=(0, 20), ipady=15)

        count = len(branches_without_upload)

        if count == 0:
            icon = "✅"
            status_text = f"All branches uploaded on {target_date}!"
            status_color = COLORS['success']
            desc_text = f"Excellent! All branches in {self.selected_group.upper()} uploaded documents on {target_date}."
        else:
            icon = "⚠️"
            status_text = f"{count} branch{'es' if count != 1 else ''} without uploads on {target_date}"
            status_color = COLORS['warning'] if count <= 3 else COLORS['danger']
            desc_text = f"The following branches in {self.selected_group.upper()} didn't upload documents on {target_date}:"

        tk.Label(
            info_frame,
            text=f"{icon} {status_text}",
            font=("Segoe UI", self.get_font_size(16), "bold"),
            bg=COLORS['surface'],
            fg=status_color
        ).pack(pady=(0, 5))

        tk.Label(
            info_frame,
            text=desc_text,
            font=("Segoe UI", self.get_font_size(11)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            wraplength=600
        ).pack()

        if branches_without_upload:
            # Scrollable list
            list_frame = tk.Frame(self.branches_content_frame, bg=COLORS['background'])
            list_frame.pack(fill="both", expand=True)

            # Canvas for scrolling
            canvas = tk.Canvas(list_frame, bg=COLORS['surface'], highlightthickness=0)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLORS['surface'])

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

            # Pack scrollbar and canvas
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            # Add branches to scrollable frame
            for i, branch in enumerate(branches_without_upload, 1):
                branch_frame = tk.Frame(scrollable_frame, bg="white", relief="flat", bd=1)
                branch_frame.pack(fill="x", padx=10, pady=5, ipady=10)

                tk.Label(
                    branch_frame,
                    text=f"{i}. 🏢 {branch}",
                    font=("Segoe UI", self.get_font_size(12), "bold"),
                    bg="white",
                    fg=COLORS['text'],
                    anchor="w"
                ).pack(side="left", padx=15, fill="x", expand=True)

                tk.Label(
                    branch_frame,
                    text=f"No uploads on {target_date}",
                    font=("Segoe UI", self.get_font_size(10)),
                    bg="white",
                    fg=COLORS['danger']
                ).pack(side="right", padx=15)

            # Mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            canvas.bind("<MouseWheel>", _on_mousewheel)
            scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    # Add all other existing methods here (display_notifications, create_notification_item, etc.)
    # Just update any references to self.group to use self.selected_group

    def update_notifications_from_aggregated_stats(self, daily_department_stats):
        """Update notifications based on aggregated upload statistics"""
        new_notifications = []

        # Sort dates (most recent first)
        sorted_dates = sorted(daily_department_stats.keys(), reverse=True)

        for date in sorted_dates:
            departments = daily_department_stats[date]

            # Sort departments by upload count (most active first)
            sorted_departments = sorted(
                departments.items(),
                key=lambda x: x[1]['total_count'],
                reverse=True
            )

            for department, stats in sorted_departments:
                file_count = stats['total_count']
                total_size = stats['total_size']
                unique_uploaders = len(stats['uploaders'])
                unique_types = len(stats['transaction_types'])

                # Format file size
                size_str = self.format_file_size(total_size)

                # Create detailed message
                uploader_text = f"{unique_uploaders} user{'s' if unique_uploaders != 1 else ''}"
                type_text = f"{unique_types} type{'s' if unique_types != 1 else ''}"

                message = f"📊 {file_count} files ({size_str}) • {uploader_text} • {type_text}"

                # Determine priority based on upload volume
                if file_count >= 20:
                    priority = "high"
                    icon = "🔴"
                elif file_count >= 10:
                    priority = "medium"
                    icon = "🟡"
                else:
                    priority = "low"
                    icon = "🟢"

                # Create notification
                notification = {
                    'id': f"{department}_{date}_{file_count}",
                    'title': f"{icon} {department}",
                    'message': message,
                    'date': date,
                    'type': 'upload',
                    'priority': priority,
                    'details': {
                        'department': department,
                        'file_count': file_count,
                        'total_size': total_size,
                        'unique_uploaders': unique_uploaders,
                        'unique_types': unique_types,
                        'uploaders': list(stats['uploaders']),
                        'transaction_types': list(stats['transaction_types']),
                        'uploads': stats['files']
                    },
                    'timestamp': datetime.now()
                }

                new_notifications.append(notification)

        # Update notifications list (keep only recent ones)
        self.notifications = new_notifications[:100]  # Keep last 100 notifications

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"

    def display_notifications(self):
        """Display notifications in the scrollable frame"""
        # Clear existing notifications
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.notifications:
            # No notifications message
            no_notif_frame = tk.Frame(self.scrollable_frame, bg=COLORS['surface'], relief="flat", bd=1)
            no_notif_frame.pack(fill="x", pady=10, padx=10)

            tk.Label(
                no_notif_frame,
                text="🔔 No recent upload notifications",
                font=("Segoe UI", self.get_font_size(14)),
                bg=COLORS['surface'],
                fg=COLORS['muted']
            ).pack(pady=30)

            tk.Label(
                no_notif_frame,
                text="Upload notifications will appear here when departments upload files",
                font=("Segoe UI", self.get_font_size(11)),
                bg=COLORS['surface'],
                fg=COLORS['muted']
            ).pack(pady=(0, 20))
            return

        # Display notifications (most recent first)
        sorted_notifications = sorted(
            self.notifications,
            key=lambda x: x.get('timestamp', datetime.now()),
            reverse=True
        )

        for notification in sorted_notifications:
            self.create_notification_item(notification)

    def create_notification_item(self, notification):
        """Create a single notification item"""
        item_frame = tk.Frame(
            self.scrollable_frame,
            bg=COLORS['surface'],
            relief="flat",
            bd=1,
            padx=15,
            pady=12
        )
        item_frame.pack(fill="x", pady=5, padx=10)

        # Header with title and date
        header_frame = tk.Frame(item_frame, bg=COLORS['surface'])
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text=notification['title'],
            font=("Segoe UI", self.get_font_size(13), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(side="left")

        tk.Label(
            header_frame,
            text=notification['date'],
            font=("Segoe UI", self.get_font_size(10)),
            bg=COLORS['surface'],
            fg=COLORS['muted']
        ).pack(side="right")

        # Message
        tk.Label(
            item_frame,
            text=notification['message'],
            font=("Segoe UI", self.get_font_size(11)),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            anchor="w"
        ).pack(fill="x", pady=(5, 0))

        # Details button
        if 'details' in notification:
            details_btn = tk.Button(
                item_frame,
                text="📋 View Details",
                font=("Segoe UI", self.get_font_size(9)),
                bg=COLORS['primary'],
                fg="white",
                bd=0,
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=4,
                command=lambda n=notification: self.show_notification_details(n)
            )
            details_btn.pack(side="left", pady=(8, 0))

    def refresh_notifications(self):
        """Refresh notifications manually"""

        def refresh_in_background():
            self.check_new_uploads()
            # Update UI in main thread
            if self.notification_window and self.notification_window.winfo_exists():
                self.notification_window.after(0, self.display_notifications)

        threading.Thread(target=refresh_in_background, daemon=True).start()

    def show_notification_details(self, notification):
        """Show detailed information about uploads"""
        details = notification.get('details', {})
        uploads = details.get('uploads', [])

        # Create details window
        details_window = tk.Toplevel(self.notification_window)
        details_window.title(f"📋 {notification['title']} - Upload Details")
        details_window.geometry("600x500")
        details_window.configure(bg=COLORS['background'])
        details_window.transient(self.notification_window)

        # Center the window
        details_window.geometry("+{}+{}".format(
            self.notification_window.winfo_x() + 50,
            self.notification_window.winfo_y() + 50
        ))

        # Header
        header_frame = tk.Frame(details_window, bg=COLORS['secondary'], height=50)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text=f"📋 {details.get('department', 'Unknown')} - {notification['date']}",
            font=("Segoe UI", self.get_font_size(14), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(pady=12)

        # Summary with enhanced statistics
        summary_frame = tk.Frame(details_window, bg=COLORS['surface'], relief="flat", bd=1)
        summary_frame.pack(fill="x", padx=15, pady=15)

        # Main stats
        main_stats = f"📊 Total Files: {details.get('file_count', 0)} | Total Size: {self.format_file_size(details.get('total_size', 0))}"
        tk.Label(
            summary_frame,
            text=main_stats,
            font=("Segoe UI", self.get_font_size(12), "bold"),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(pady=(10, 5))

        # Additional stats
        additional_stats = f"👥 {details.get('unique_uploaders', 0)} unique uploaders | 📋 {details.get('unique_types', 0)} transaction types"
        tk.Label(
            summary_frame,
            text=additional_stats,
            font=("Segoe UI", self.get_font_size(10)),
            bg=COLORS['surface'],
            fg=COLORS['muted']
        ).pack(pady=(0, 5))

        # Show uploaders and types
        if details.get('uploaders'):
            uploaders_text = "Uploaders: " + ", ".join(details['uploaders'][:5])
            if len(details['uploaders']) > 5:
                uploaders_text += f" (and {len(details['uploaders']) - 5} more)"

            tk.Label(
                summary_frame,
                text=uploaders_text,
                font=("Segoe UI", self.get_font_size(9)),
                bg=COLORS['surface'],
                fg=COLORS['muted'],
                wraplength=500
            ).pack(pady=(0, 10))

        # Files list with scrollbar
        list_frame = tk.Frame(details_window, bg=COLORS['background'])
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        canvas = tk.Canvas(list_frame, bg=COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['background'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Display each file
        for i, upload in enumerate(uploads, 1):
            file_frame = tk.Frame(scrollable_frame, bg=COLORS['surface'], relief="flat", bd=1)
            file_frame.pack(fill="x", pady=3, padx=5)

            # File info
            info_frame = tk.Frame(file_frame, bg=COLORS['surface'])
            info_frame.pack(fill="x", padx=10, pady=8)

            tk.Label(
                info_frame,
                text=f"{i}. 📄 {upload.get('file_name', 'Unknown File')}",
                font=("Segoe UI", self.get_font_size(11), "bold"),
                bg=COLORS['surface'],
                fg=COLORS['text'],
                anchor="w"
            ).pack(fill="x")

            details_text = f"   Size: {self.format_file_size(upload.get('file_size', 0))} | Type: {upload.get('transaction_type', 'Unknown')} | By: {upload.get('uploaded_by', 'Unknown')}"
            tk.Label(
                info_frame,
                text=details_text,
                font=("Segoe UI", self.get_font_size(9)),
                bg=COLORS['surface'],
                fg=COLORS['muted'],
                anchor="w"
            ).pack(fill="x", pady=(2, 0))

        # Close button
        close_btn = tk.Button(
            details_window,
            text="✕ Close",
            font=("Segoe UI", self.get_font_size(11), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=details_window.destroy
        )
        close_btn.pack(pady=15)

        # ESC to close
        details_window.bind('<Escape>', lambda e: details_window.destroy())
        details_window.focus_set()

        # Bind mousewheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

    def get_daily_department_totals(self, target_date=None):
        """Get total uploads by department for a specific day"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")

        try:
            uploads_ref = self.db.collection('head_office_uploads')
            query = uploads_ref.where('upload_date', '==', target_date)

            docs = query.get()

            department_totals = defaultdict(lambda: {
                'total_files': 0,
                'total_size': 0,
                'uploaders': set(),
                'transaction_types': set(),
                'files': []
            })

            for doc in docs:
                data = doc.to_dict()
                department = data.get('department', 'Unknown Department')

                department_totals[department]['total_files'] += 1
                department_totals[department]['total_size'] += data.get('file_size', 0)
                department_totals[department]['uploaders'].add(data.get('uploaded_by', 'Unknown'))
                department_totals[department]['transaction_types'].add(data.get('transaction_type', 'Unknown'))
                department_totals[department]['files'].append({
                    'file_name': data.get('file_name', 'Unknown'),
                    'file_size': data.get('file_size', 0),
                    'uploaded_by': data.get('uploaded_by', 'Unknown'),
                    'transaction_type': data.get('transaction_type', 'Unknown'),
                    'timestamp': data.get('timestamp')
                })

            # Convert sets to counts and lists
            for dept in department_totals:
                department_totals[dept]['unique_uploaders'] = len(department_totals[dept]['uploaders'])
                department_totals[dept]['unique_types'] = len(department_totals[dept]['transaction_types'])
                department_totals[dept]['uploaders'] = list(department_totals[dept]['uploaders'])
                department_totals[dept]['transaction_types'] = list(department_totals[dept]['transaction_types'])

            return dict(department_totals)

        except Exception as e:
            print(f"Error getting daily totals: {e}")
            return {}

    def show_daily_summary(self):
        """Show daily summary window with all department totals"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Get today's totals
        daily_totals = self.get_daily_department_totals(today)

        if not daily_totals:
            messagebox.showinfo("Daily Summary", f"No uploads found for {today}")
            return

        # Create summary window
        summary_window = tk.Toplevel(self.parent_window)
        summary_window.title(f"📊 Daily Upload Summary - {today}")
        summary_window.geometry("700x600")
        summary_window.configure(bg=COLORS['background'])
        summary_window.transient(self.parent_window)

        # Center the window
        screen_width = summary_window.winfo_screenwidth()
        screen_height = summary_window.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 600) // 2
        summary_window.geometry(f"700x600+{x}+{y}")

        # Header
        header_frame = tk.Frame(summary_window, bg=COLORS['secondary'], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text=f"📊 Upload Summary - {today}",
            font=("Segoe UI", self.get_font_size(16), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(pady=18)

        # Overall stats
        total_files = sum(dept['total_files'] for dept in daily_totals.values())
        total_size = sum(dept['total_size'] for dept in daily_totals.values())
        total_departments = len(daily_totals)

        stats_frame = tk.Frame(summary_window, bg=COLORS['primary'], relief="flat")
        stats_frame.pack(fill="x", padx=20, pady=15)

        overall_text = f"🎯 {total_departments} departments uploaded {total_files} files ({self.format_file_size(total_size)}) today"
        tk.Label(
            stats_frame,
            text=overall_text,
            font=("Segoe UI", self.get_font_size(13), "bold"),
            bg=COLORS['primary'],
            fg="white"
        ).pack(pady=12)

        # Department breakdown with scrollbar
        main_frame = tk.Frame(summary_window, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(main_frame, bg=COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['background'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sort departments by upload count
        sorted_departments = sorted(
            daily_totals.items(),
            key=lambda x: x[1]['total_files'],
            reverse=True
        )

        # Display each department
        for rank, (department, stats) in enumerate(sorted_departments, 1):
            dept_frame = tk.Frame(scrollable_frame, bg=COLORS['surface'], relief="flat", bd=1)
            dept_frame.pack(fill="x", pady=5, padx=5)

            # Department header
            header_dept = tk.Frame(dept_frame, bg=COLORS['surface'])
            header_dept.pack(fill="x", padx=15, pady=10)

            # Rank and department name
            rank_color = COLORS['primary'] if rank <= 3 else COLORS['muted']
            tk.Label(
                header_dept,
                text=f"#{rank}",
                font=("Segoe UI", self.get_font_size(12), "bold"),
                bg=rank_color,
                fg="white",
                width=3,
                relief="flat"
            ).pack(side="left", padx=(0, 10))

            tk.Label(
                header_dept,
                text=f"📁 {department}",
                font=("Segoe UI", self.get_font_size(13), "bold"),
                bg=COLORS['surface'],
                fg=COLORS['text']
            ).pack(side="left")

            # Stats
            stats_text = f"{stats['total_files']} files • {self.format_file_size(stats['total_size'])} • {stats['unique_uploaders']} users"
            tk.Label(
                header_dept,
                text=stats_text,
                font=("Segoe UI", self.get_font_size(10)),
                bg=COLORS['surface'],
                fg=COLORS['muted']
            ).pack(side="right")

            # Progress bar (visual representation)
            progress_frame = tk.Frame(dept_frame, bg=COLORS['surface'])
            progress_frame.pack(fill="x", padx=15, pady=(0, 10))

            max_files = max(dept['total_files'] for dept in daily_totals.values())
            progress_width = int((stats['total_files'] / max_files) * 200) if max_files > 0 else 0

            progress_bg = tk.Frame(progress_frame, bg=COLORS['background'], height=8)
            progress_bg.pack(fill="x")

            if progress_width > 0:
                progress_bar = tk.Frame(progress_bg, bg=COLORS['primary'], height=8, width=progress_width)
                progress_bar.pack(side="left")

        # Close button
        close_btn = tk.Button(
            summary_window,
            text="✕ Close",
            font=("Segoe UI", self.get_font_size(11), "bold"),
            bg=COLORS['muted'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=summary_window.destroy
        )
        close_btn.pack(pady=15)

        # Bind mousewheel and ESC
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        summary_window.bind('<Escape>', lambda e: summary_window.destroy())
        summary_window.focus_set()

    def add_manual_notification(self, title, message, notification_type="info"):
        """Add a manual notification (for testing or special events)"""
        notification = {
            'id': f"manual_{int(time.time())}",
            'title': title,
            'message': message,
            'type': notification_type,
            'timestamp': datetime.now(),
            'date': datetime.now().strftime("%Y-%m-%d")
        }
        self.notifications.insert(0, notification)

        # Keep only last 50 notifications
        self.notifications = self.notifications[:50]