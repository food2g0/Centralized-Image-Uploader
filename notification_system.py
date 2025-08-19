import tkinter as tk
from tkinter import messagebox, ttk
from Colors import COLORS
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import firestore
from collections import defaultdict, Counter
import threading
import time


class NotificationSystem:
    def __init__(self, parent_window, admin_data):
        self.parent_window = parent_window
        self.admin_data = admin_data
        self.notifications = []
        self.notification_window = None
        self.db = firestore.client()  # Firebase Firestore client
        self.upload_stats = {}
        self.last_check_time = datetime.now()
        
        # Start background monitoring
        self.start_upload_monitoring()
        
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
    
    def open_notifications(self):
        """Open the notifications window"""
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.lift()
            return
            
        self.notification_window = tk.Toplevel(self.parent_window)
        self.notification_window.title("🔔 Notifications")
        
        # Responsive window size
        screen_width = self.parent_window.winfo_screenwidth()
        screen_height = self.parent_window.winfo_screenheight()
        font_scale = max(0.8, min(1.2, min(screen_width / 1920, screen_height / 1080)))
        
        window_width = max(500, min(800, int(700 * font_scale)))
        window_height = max(400, min(800, int(600 * font_scale)))
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.notification_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.notification_window.configure(bg=COLORS['background'])
        self.notification_window.transient(self.parent_window)
        
        # Refresh data before showing
        threading.Thread(target=self.check_new_uploads, daemon=True).start()
        
        self.create_notification_ui()
        
    def create_notification_ui(self):
        """Create the notification interface"""
        # Header
        header_frame = tk.Frame(self.notification_window, bg=COLORS['secondary'], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=COLORS['secondary'])
        header_content.pack(expand=True, fill="both")
        
        tk.Label(
            header_content,
            text="🔔 Upload Notifications",
            font=("Segoe UI", self.get_font_size(16), "bold"),
            bg=COLORS['secondary'],
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Summary button
        summary_btn = tk.Button(
            header_content,
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
        summary_btn.pack(side="right", padx=(0, 10), pady=15)
        
        # Refresh button
        refresh_btn = tk.Button(
            header_content,
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
        refresh_btn.pack(side="right", padx=20, pady=15)
        
        # Main content area with scrollbar
        main_frame = tk.Frame(self.notification_window, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
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
        
        # Store reference for refreshing
        self.scrollable_frame = scrollable_frame
        
        # Load and display notifications
        self.display_notifications()
        
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
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
    
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
    
    def refresh_notifications(self):
        """Refresh notifications manually"""
        def refresh_in_background():
            self.check_new_uploads()
            # Update UI in main thread
            self.notification_window.after(0, self.display_notifications)
        
        threading.Thread(target=refresh_in_background, daemon=True).start()
    
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
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