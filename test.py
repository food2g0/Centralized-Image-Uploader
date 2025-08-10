def open_head_office_popup(parent_admin):
    import tkinter as tk
    from tkinter import messagebox, ttk
    from firebase_config import db
    
    # Get screen dimensions for responsive design
    screen_width = parent_admin.winfo_screenwidth()
    screen_height = parent_admin.winfo_screenheight()
    scale_factor = min(screen_width / 1920, screen_height / 1080)
    font_scale = max(0.8, min(1.2, scale_factor))
    
    def get_font_size(base_size):
        return max(8, int(base_size * font_scale))
    
    # Modern color scheme
    colors = {
        'primary': '#1e293b',
        'secondary': '#3b82f6',
        'accent': '#06b6d4',
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'surface': '#ffffff',
        'background': '#f8fafc',
        'muted': '#64748b',
        'text': '#0f172a',
        'border': '#e2e8f0'
    }
    
    # Create popup window
    popup = tk.Toplevel(parent_admin)
    popup.title("🏢 Head Office Management")
    
    # Responsive popup size
    popup_width = max(800, min(1200, int(screen_width * 0.7)))
    popup_height = max(600, min(900, int(screen_height * 0.7)))
    popup.geometry(f"{popup_width}x{popup_height}")
    popup.configure(bg=colors['background'])
    popup.resizable(True, True)
    
    # Center the popup
    x = (screen_width - popup_width) // 2
    y = (screen_height - popup_height) // 2
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    
    popup.transient(parent_admin)
    popup.grab_set()
    
    # Header
    header_frame = tk.Frame(popup, bg=colors['primary'])
    header_frame.pack(fill="x", pady=0)
    
    header_height = max(60, int(70 * font_scale))
    header_inner = tk.Frame(header_frame, bg=colors['primary'], height=header_height)
    header_inner.pack(fill="x", padx=int(20 * font_scale), pady=int(10 * font_scale))
    header_inner.pack_propagate(False)
    
    tk.Label(
        header_inner,
        text="🏢 Head Office Dashboard",
        font=("Segoe UI", get_font_size(18), "bold"),
        bg=colors['primary'],
        fg="white"
    ).pack(side="left", pady=int(15 * font_scale))
    
    # Close button
    close_btn = tk.Button(
        header_inner,
        text="✕",
        font=("Segoe UI", get_font_size(16), "bold"),
        bg=colors['danger'],
        fg="white",
        bd=0,
        relief="flat",
        cursor="hand2",
        width=3,
        height=1,
        command=popup.destroy
    )
    close_btn.pack(side="right", pady=int(15 * font_scale))
    
    # Main content frame
    main_content = tk.Frame(popup, bg=colors['background'])
    main_content.pack(fill="both", expand=True, padx=int(20 * font_scale), pady=int(20 * font_scale))
    
    # Create notebook for tabs
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure tab styles
    style.configure('Custom.TNotebook', background=colors['surface'], borderwidth=1)
    style.configure('Custom.TNotebook.Tab', 
                    background=colors['muted'], 
                    foreground="white", 
                    padding=[int(12 * font_scale), int(8 * font_scale)],
                    font=("Segoe UI", get_font_size(11), "bold"))
    style.map('Custom.TNotebook.Tab',
              background=[('selected', colors['secondary']), ('active', colors['accent'])],
              foreground=[('selected', 'white'), ('active', 'white')])
    
    notebook = ttk.Notebook(main_content, style='Custom.TNotebook')
    notebook.pack(fill="both", expand=True)
    
    # Tab 1: User Management
    users_frame = tk.Frame(notebook, bg=colors['surface'])
    notebook.add(users_frame, text="👥 User Management")
    
    # Tab 2: System Statistics
    stats_frame = tk.Frame(notebook, bg=colors['surface'])
    notebook.add(stats_frame, text="📊 System Statistics")
    
    # Tab 3: Branch Overview
    branches_frame = tk.Frame(notebook, bg=colors['surface'])
    notebook.add(branches_frame, text="🏢 Branch Overview")
    
    # Tab 4: Settings
    settings_frame = tk.Frame(notebook, bg=colors['surface'])
    notebook.add(settings_frame, text="⚙️ Settings")
    
    # === USER MANAGEMENT TAB ===
    def setup_user_management_tab():
        # Header for user management
        user_header = tk.Frame(users_frame, bg=colors['secondary'], height=max(50, int(60 * font_scale)))
        user_header.pack(fill="x", pady=(0, int(15 * font_scale)))
        user_header.pack_propagate(False)
        
        tk.Label(
            user_header,
            text="👥 Manage System Users",
            font=("Segoe UI", get_font_size(14), "bold"),
            bg=colors['secondary'],
            fg="white"
        ).pack(pady=int(15 * font_scale))
        
        # User list frame with scrollbar
        user_list_frame = tk.Frame(users_frame, bg=colors['surface'])
        user_list_frame.pack(fill="both", expand=True, padx=int(15 * font_scale), pady=(0, int(15 * font_scale)))
        
        # Canvas for scrollable user list
        user_canvas = tk.Canvas(user_list_frame, bg=colors['surface'], highlightthickness=0, bd=0)
        user_scrollbar = tk.Scrollbar(user_list_frame, orient="vertical", command=user_canvas.yview,
                                     bg=colors['border'], troughcolor=colors['background'],
                                     activebackground=colors['secondary'], width=max(12, int(16 * font_scale)))
        user_canvas.configure(yscrollcommand=user_scrollbar.set)
        
        user_scrollbar.pack(side="right", fill="y")
        user_canvas.pack(side="left", fill="both", expand=True)
        
        user_scroll_frame = tk.Frame(user_canvas, bg=colors['surface'])
        user_canvas_window = user_canvas.create_window((0, 0), window=user_scroll_frame, anchor="nw")
        
        def on_user_frame_configure(event):
            user_canvas.configure(scrollregion=user_canvas.bbox("all"))
            user_canvas.itemconfig(user_canvas_window, width=user_canvas.winfo_width())
        
        user_scroll_frame.bind("<Configure>", on_user_frame_configure)
        
        def load_users():
            # Clear existing user widgets
            for widget in user_scroll_frame.winfo_children():
                widget.destroy()
            
            try:
                # Fetch users from Firebase
                users_ref = db.collection("users")
                users = users_ref.stream()
                
                user_count = 0
                for user_doc in users:
                    user_data = user_doc.to_dict()
                    user_id = user_doc.id
                    
                    # Create user card
                    user_card = tk.Frame(user_scroll_frame, bg=colors['surface'], relief="solid", bd=1)
                    user_card.pack(fill="x", padx=int(10 * font_scale), pady=int(8 * font_scale), 
                                  ipady=int(15 * font_scale))
                    
                    # User info
                    info_frame = tk.Frame(user_card, bg=colors['surface'])
                    info_frame.pack(side="left", fill="both", expand=True, padx=int(15 * font_scale))
                    
                    # Username
                    tk.Label(
                        info_frame,
                        text=f"👤 {user_data.get('username', 'Unknown')}",
                        font=("Segoe UI", get_font_size(12), "bold"),
                        bg=colors['surface'],
                        fg=colors['text']
                    ).pack(anchor="w")
                    
                    # Group
                    tk.Label(
                        info_frame,
                        text=f"🏢 Group: {user_data.get('group', 'Unknown')}",
                        font=("Segoe UI", get_font_size(10)),
                        bg=colors['surface'],
                        fg=colors['muted']
                    ).pack(anchor="w")
                    
                    # Branch
                    tk.Label(
                        info_frame,
                        text=f"📍 Branch: {user_data.get('branch', 'Unknown')}",
                        font=("Segoe UI", get_font_size(10)),
                        bg=colors['surface'],
                        fg=colors['muted']
                    ).pack(anchor="w")
                    
                    # Actions
                    actions_frame = tk.Frame(user_card, bg=colors['surface'])
                    actions_frame.pack(side="right", padx=int(15 * font_scale))
                    
                    def delete_user(uid=user_id, username=user_data.get('username', 'Unknown')):
                        confirm = messagebox.askyesno(
                            "Confirm Delete", 
                            f"Are you sure you want to delete user '{username}'?"
                        )
                        if confirm:
                            try:
                                db.collection("users").document(uid).delete()
                                messagebox.showinfo("Success", f"User '{username}' deleted successfully!")
                                load_users()  # Refresh the list
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
                    
                    tk.Button(
                        actions_frame,
                        text="🗑️ Delete",
                        font=("Segoe UI", get_font_size(9), "bold"),
                        bg=colors['danger'],
                        fg="white",
                        bd=0,
                        relief="flat",
                        cursor="hand2",
                        padx=int(12 * font_scale),
                        pady=int(6 * font_scale),
                        command=delete_user
                    ).pack()
                    
                    user_count += 1
                
                if user_count == 0:
                    tk.Label(
                        user_scroll_frame,
                        text="👤 No users found",
                        font=("Segoe UI", get_font_size(14), "bold"),
                        bg=colors['surface'],
                        fg=colors['muted']
                    ).pack(pady=int(50 * font_scale))
                
            except Exception as e:
                tk.Label(
                    user_scroll_frame,
                    text=f"❌ Error loading users: {str(e)}",
                    font=("Segoe UI", get_font_size(12)),
                    bg=colors['surface'],
                    fg=colors['danger']
                ).pack(pady=int(50 * font_scale))
        
        # Action buttons
        action_frame = tk.Frame(users_frame, bg=colors['surface'])
        action_frame.pack(fill="x", padx=int(15 * font_scale), pady=int(10 * font_scale))
        
        tk.Button(
            action_frame,
            text="🔄 Refresh Users",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=colors['secondary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(20 * font_scale),
            pady=int(10 * font_scale),
            command=load_users
        ).pack(side="left", padx=(0, int(10 * font_scale)))
        
        # Load users initially
        load_users()
    
    # === SYSTEM STATISTICS TAB ===
    def setup_statistics_tab():
        # Header
        stats_header = tk.Frame(stats_frame, bg=colors['accent'], height=max(50, int(60 * font_scale)))
        stats_header.pack(fill="x", pady=(0, int(15 * font_scale)))
        stats_header.pack_propagate(False)
        
        tk.Label(
            stats_header,
            text="📊 System Overview & Statistics",
            font=("Segoe UI", get_font_size(14), "bold"),
            bg=colors['accent'],
            fg="white"
        ).pack(pady=int(15 * font_scale))
        
        # Stats content
        stats_content = tk.Frame(stats_frame, bg=colors['surface'])
        stats_content.pack(fill="both", expand=True, padx=int(15 * font_scale), pady=(0, int(15 * font_scale)))
        
        # Create statistics cards
        def create_stat_card(parent, title, value, icon, color):
            card = tk.Frame(parent, bg=color, relief="flat", bd=0)
            card.pack(side="left", fill="both", expand=True, padx=int(10 * font_scale), 
                     pady=int(10 * font_scale), ipady=int(20 * font_scale))
            
            tk.Label(
                card,
                text=icon,
                font=("Segoe UI", get_font_size(24)),
                bg=color,
                fg="white"
            ).pack(pady=(int(10 * font_scale), int(5 * font_scale)))
            
            tk.Label(
                card,
                text=str(value),
                font=("Segoe UI", get_font_size(20), "bold"),
                bg=color,
                fg="white"
            ).pack()
            
            tk.Label(
                card,
                text=title,
                font=("Segoe UI", get_font_size(12), "bold"),
                bg=color,
                fg="white"
            ).pack(pady=(int(5 * font_scale), int(10 * font_scale)))
        
        def load_statistics():
            # Clear existing stats
            for widget in stats_content.winfo_children():
                widget.destroy()
            
            try:
                # Get user count
                users_count = len(list(db.collection("users").stream()))
                
                # Get images count
                images_count = len(list(db.collection("Uploaded_Images").stream()))
                
                # Get unique branches count
                branches = set()
                for doc in db.collection("Uploaded_Images").stream():
                    data = doc.to_dict()
                    branch = data.get("branch", "Unknown")
                    branches.add(branch)
                branches_count = len(branches)
                
                # Create statistics row
                stats_row = tk.Frame(stats_content, bg=colors['surface'])
                stats_row.pack(fill="x", pady=int(20 * font_scale))
                
                create_stat_card(stats_row, "Total Users", users_count, "👥", colors['success'])
                create_stat_card(stats_row, "Total Images", images_count, "📸", colors['secondary'])
                create_stat_card(stats_row, "Active Branches", branches_count, "🏢", colors['warning'])
                
                # Additional info
                info_frame = tk.Frame(stats_content, bg=colors['surface'], relief="solid", bd=1)
                info_frame.pack(fill="x", padx=int(20 * font_scale), pady=int(20 * font_scale), 
                               ipady=int(15 * font_scale))
                
                tk.Label(
                    info_frame,
                    text="📋 System Information",
                    font=("Segoe UI", get_font_size(14), "bold"),
                    bg=colors['surface'],
                    fg=colors['text']
                ).pack(pady=(int(10 * font_scale), int(15 * font_scale)))
                
                import datetime
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                tk.Label(
                    info_frame,
                    text=f"🕒 Last Updated: {current_time}",
                    font=("Segoe UI", get_font_size(11)),
                    bg=colors['surface'],
                    fg=colors['muted']
                ).pack()
                
            except Exception as e:
                tk.Label(
                    stats_content,
                    text=f"❌ Error loading statistics: {str(e)}",
                    font=("Segoe UI", get_font_size(12)),
                    bg=colors['surface'],
                    fg=colors['danger']
                ).pack(pady=int(50 * font_scale))
        
        # Load statistics initially
        load_statistics()
        
        # Refresh button
        tk.Button(
            stats_frame,
            text="🔄 Refresh Statistics",
            font=("Segoe UI", get_font_size(11), "bold"),
            bg=colors['accent'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=int(20 * font_scale),
            pady=int(10 * font_scale),
            command=load_statistics
        ).pack(pady=int(15 * font_scale))
    
    # === BRANCH OVERVIEW TAB ===
    def setup_branch_overview_tab():
        # Header
        branch_header = tk.Frame(branches_frame, bg=colors['warning'], height=max(50, int(60 * font_scale)))
        branch_header.pack(fill="x", pady=(0, int(15 * font_scale)))
        branch_header.pack_propagate(False)
        
        tk.Label(
            branch_header,
            text="🏢 Branch Activity Overview",
            font=("Segoe UI", get_font_size(14), "bold"),
            bg=colors['warning'],
            fg="white"
        ).pack(pady=int(15 * font_scale))
        
        # Branch content
        branch_content = tk.Frame(branches_frame, bg=colors['surface'])
        branch_content.pack(fill="both", expand=True, padx=int(15 * font_scale), pady=(0, int(15 * font_scale)))
        
        tk.Label(
            branch_content,
            text="🚧 Branch overview functionality coming soon...",
            font=("Segoe UI", get_font_size(16), "bold"),
            bg=colors['surface'],
            fg=colors['muted']
        ).pack(pady=int(100 * font_scale))
    
    # === SETTINGS TAB ===
    def setup_settings_tab():
        # Header
        settings_header = tk.Frame(settings_frame, bg=colors['muted'], height=max(50, int(60 * font_scale)))
        settings_header.pack(fill="x", pady=(0, int(15 * font_scale)))
        settings_header.pack_propagate(False)
        
        tk.Label(
            settings_header,
            text="⚙️ System Settings",
            font=("Segoe UI", get_font_size(14), "bold"),
            bg=colors['muted'],
            fg="white"
        ).pack(pady=int(15 * font_scale))
        
        # Settings content
        settings_content = tk.Frame(settings_frame, bg=colors['surface'])
        settings_content.pack(fill="both", expand=True, padx=int(15 * font_scale), pady=(0, int(15 * font_scale)))
        
        tk.Label(
            settings_content,
            text="⚙️ System settings will be available here...",
            font=("Segoe UI", get_font_size(16), "bold"),
            bg=colors['surface'],
            fg=colors['muted']
        ).pack(pady=int(100 * font_scale))
    
    # Setup all tabs
    setup_user_management_tab()
    setup_statistics_tab()
    setup_branch_overview_tab()
    setup_settings_tab()
    
    # Set default tab
    notebook.select(0)
    
    # Handle window close event
    def on_closing():
        popup.grab_release()
        popup.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_closing)