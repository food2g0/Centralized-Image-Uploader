def open_admin_dashboard_group1(admin_data):
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk
    from firebase_config import db, bucket
    from PIL import Image, ImageTk
    import requests
    from add_user_group1 import open_add_user_popup_group1
    from io import BytesIO
    import time
    import datetime
    from head_office_popup import open_head_office_popup
    from head_office_images import open_head_office_images
    from Colors import COLORS
    from corporations import group1_corporations
    from notification_system import NotificationSystem
    import threading
    from typing import Dict, List, Optional, Tuple, Any

    VERSION = "1.1.3"
    class OptimizedFirestoreManager:


        def __init__(self, db, bucket):
            self.db = db
            self.bucket = bucket
            self.cache = {}
            self.cache_timeout = 1800  # 30 minutes cache for heavy queries
            self.page_size = 25
            self.max_branch_discovery = 100  # Strict limit for branch discovery

            # Create composite indexes programmatically (you'll need to add these in Firebase Console)
            self.required_indexes = [
                # For branch queries with filters
                ("branch", "timestamp"),
                ("branch", "transaction_type", "timestamp"),
                ("branch", "date", "timestamp"),
                ("branch", "transaction_type", "date", "timestamp"),

                # For corporation queries with filters
                ("corporations", "timestamp"),
                ("corporations", "transaction_type", "timestamp"),
                ("corporations", "date", "timestamp"),
                ("corporations", "transaction_type", "date", "timestamp"),

                # For efficient branch discovery
                ("corporations", "branch"),
            ]

        def _get_cache_key(self, query_type: str, **params) -> str:
            """Generate consistent cache key"""
            sorted_params = sorted(params.items())
            return f"{query_type}_{hash(str(sorted_params))}"

        def _is_cache_valid(self, cache_key: str) -> bool:
            """Check if cached data is still valid"""
            if cache_key not in self.cache:
                return False
            return time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout

        def _cache_result(self, cache_key: str, data: Any, custom_timeout: int = None):
            """Cache query result with custom timeout"""
            timeout = custom_timeout or self.cache_timeout
            self.cache[cache_key] = {
                'data': data,
                'timestamp': time.time(),
                'timeout': timeout
            }

        def load_branches_ultra_optimized(self, group_corps: List[str]) -> List[str]:
            """ULTRA-OPTIMIZED: Load unique branches with absolute minimal reads"""
            cache_key = self._get_cache_key("branches_ultra", corps=str(sorted(group_corps)))

            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']

            try:
                branches_set = set()
                total_reads = 0

                # Strategy 1: Use aggregation query if available (Firestore Count queries)
                # This is the most cost-effective approach for large datasets

                # Strategy 2: Batch corporations and use SELECT with strict limits
                corp_batches = [group_corps[i:i + 10] for i in range(0, len(group_corps), 10)]

                for batch in corp_batches:
                    # CRITICAL: Only select 'branch' field to minimize data transfer cost
                    query = (self.db.collection("Uploaded_Images")
                             .where("corporations", "in", batch)
                             .select(["branch"])  # Only read branch field - MASSIVE cost reduction
                             .limit(self.max_branch_discovery))  # Strict limit

                    docs = query.stream()
                    batch_count = 0

                    for doc in docs:
                        total_reads += 1
                        batch_count += 1

                        data = doc.to_dict()
                        if data and "branch" in data:
                            branch = data.get("branch", "").strip()
                            if branch:
                                branches_set.add(branch)

                        # Early termination to control costs
                        if len(branches_set) >= 50 or total_reads >= self.max_branch_discovery:
                            break

                    if len(branches_set) >= 50 or total_reads >= self.max_branch_discovery:
                        break

                branches_list = sorted(list(branches_set))

                # Cache for longer time since branches don't change often
                self._cache_result(cache_key, branches_list, custom_timeout=3600)  # 1 hour cache

                print(f"Branch discovery - Total reads: {total_reads}, Found branches: {len(branches_list)}")
                return branches_list

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load branches: {e}")
                return []

        def load_branch_data_cursor_paginated(self, branch_name: str, page_size: int = 25,
                                              cursor_doc=None, filters: Dict = None) -> Tuple[
            List[dict], Optional[Any], bool]:
            """CURSOR-BASED PAGINATION: Most efficient for large datasets"""

            cache_key = self._get_cache_key("branch_cursor",
                                            branch=branch_name,
                                            cursor=str(cursor_doc.id if cursor_doc else None),
                                            filters=str(filters))

            if self._is_cache_valid(cache_key):
                cached = self.cache[cache_key]['data']
                return cached['data'], cached['last_doc'], cached['has_more']

            try:
                # Build optimized query with composite indexes
                query = (self.db.collection("Uploaded_Images")
                         .where("branch", "==", branch_name)
                         .order_by("timestamp", direction="DESCENDING")
                         .limit(page_size + 1))  # +1 to check if there are more pages

                # Apply filters with proper indexing
                if filters:
                    if filters.get('transaction_type') and filters['transaction_type'] != 'All':
                        query = query.where("transaction_type", "==", filters['transaction_type'])

                    if filters.get('start_date'):
                        query = query.where("date", ">=", filters['start_date'])

                    if filters.get('end_date'):
                        query = query.where("date", "<=", filters['end_date'])

                # Apply cursor for pagination
                if cursor_doc:
                    query = query.start_after(cursor_doc)

                docs = list(query.stream())

                # Check if there are more pages
                has_more = len(docs) > page_size
                if has_more:
                    docs = docs[:-1]  # Remove the extra document

                branch_data = []
                last_doc = None

                for doc in docs:
                    data = doc.to_dict()
                    if data:
                        data["doc_id"] = doc.id
                        branch_data.append(data)
                        last_doc = doc

                result = {
                    'data': branch_data,
                    'last_doc': last_doc,
                    'has_more': has_more
                }

                # Cache for shorter time for dynamic data
                self._cache_result(cache_key, result, custom_timeout=300)  # 5 minutes

                return branch_data, last_doc, has_more

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load branch data: {e}")
                return [], None, False

        def get_document_count_estimate(self, branch_name: str = None, corp_name: str = None,
                                        filters: Dict = None) -> int:
            """Get approximate document count using efficient aggregation"""

            cache_key = self._get_cache_key("count_estimate",
                                            branch=branch_name,
                                            corp=corp_name,
                                            filters=str(filters))

            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']

            try:
                # Strategy 1: Use Firestore Count aggregation query (if available)
                # This is the most cost-effective for large collections

                # Strategy 2: Sample-based estimation for very large datasets
                base_query = self.db.collection("Uploaded_Images")

                if branch_name:
                    base_query = base_query.where("branch", "==", branch_name)
                elif corp_name:
                    base_query = base_query.where("corporations", "==", corp_name)

                # Apply filters
                if filters:
                    if filters.get('transaction_type') and filters['transaction_type'] != 'All':
                        base_query = base_query.where("transaction_type", "==", filters['transaction_type'])
                    if filters.get('start_date'):
                        base_query = base_query.where("date", ">=", filters['start_date'])
                    if filters.get('end_date'):
                        base_query = base_query.where("date", "<=", filters['end_date'])

                # For large datasets, use sampling approach
                sample_query = base_query.select([]).limit(1000)  # Empty select for counting
                sample_docs = list(sample_query.stream())

                # If we got exactly 1000, there are likely more - estimate
                if len(sample_docs) == 1000:
                    # This is a rough estimate - you might want to implement more sophisticated sampling
                    estimated_count = 1000  # Conservative estimate
                else:
                    estimated_count = len(sample_docs)

                # Cache count estimates for longer
                self._cache_result(cache_key, estimated_count, custom_timeout=1800)  # 30 minutes

                return estimated_count

            except Exception:
                return 0

        def bulk_operation_optimized(self, operations: List[Dict], batch_size: int = 500):


            try:
                # Split operations into batches (Firestore batch limit is 500)
                for i in range(0, len(operations), batch_size):
                    batch = self.db.batch()
                    batch_ops = operations[i:i + batch_size]

                    for op in batch_ops:
                        if op['type'] == 'delete':
                            doc_ref = self.db.collection("Uploaded_Images").document(op['doc_id'])
                            batch.delete(doc_ref)
                        elif op['type'] == 'update':
                            doc_ref = self.db.collection("Uploaded_Images").document(op['doc_id'])
                            batch.update(doc_ref, op['data'])

                    # Commit batch
                    batch.commit()

                return True

            except Exception as e:
                messagebox.showerror("Error", f"Bulk operation failed: {e}")
                return False

        def search_documents_optimized(self, search_term: str, context: Dict,
                                       page_size: int = 25) -> List[dict]:
            """Optimized document search with proper indexing"""

            cache_key = self._get_cache_key("search",
                                            term=search_term.lower(),
                                            context=str(context))

            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']

            try:
                # For filename search, we need to implement proper text search
                # Firestore doesn't have full-text search, so we use array-contains for keywords

                base_query = self.db.collection("Uploaded_Images")

                # Apply context filters first
                if context.get('type') == 'branch':
                    base_query = base_query.where("branch", "==", context['value'])
                elif context.get('type') == 'corporation':
                    base_query = base_query.where("corporations", "==", context['value'])

                # For better search, you should store filename keywords in an array field
                # and use array-contains-any for efficient searching
                query = (base_query
                         .order_by("timestamp", direction="DESCENDING")
                         .limit(page_size * 5))  # Get more to filter client-side

                docs = list(query.stream())

                # Client-side filtering (not ideal for large datasets)
                search_results = []
                search_lower = search_term.lower()

                for doc in docs:
                    data = doc.to_dict()
                    if data:
                        filename = data.get("filename", "").lower()
                        if search_lower in filename:
                            data["doc_id"] = doc.id
                            search_results.append(data)

                            if len(search_results) >= page_size:
                                break

                # Cache search results briefly
                self._cache_result(cache_key, search_results, custom_timeout=300)

                return search_results

            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {e}")
                return []

        def clear_cache_smart(self):
            """Smart cache clearing - only clear expired entries"""
            current_time = time.time()
            expired_keys = []

            for key, cached_data in self.cache.items():
                timeout = cached_data.get('timeout', self.cache_timeout)
                if current_time - cached_data['timestamp'] > timeout:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            print(f"Cleared {len(expired_keys)} expired cache entries")

    # Usage in your main application
    def create_optimized_admin_dashboard(admin_data):
        """Modified version of your admin dashboard with optimized operations"""

        # Initialize optimized manager
        optimizer = OptimizedFirestoreManager(db, bucket)

        # Global state management
        class AppState:
            def __init__(self):
                self.current_data = []
                self.current_context = {"type": None, "value": None}
                self.current_cursor = None
                self.has_more_pages = True
                self.page_number = 0

            def reset(self):
                self.current_data.clear()
                self.current_cursor = None
                self.has_more_pages = True
                self.page_number = 0

        app_state = AppState()

        def load_page_data(context, page_size=25, reset_pagination=False):
            """Load data with proper cursor-based pagination"""

            if reset_pagination:
                app_state.reset()

            try:
                if context["type"] == "branch":
                    data, cursor, has_more = optimizer.load_branch_data_cursor_paginated(
                        context["value"],
                        page_size=page_size,
                        cursor_doc=app_state.current_cursor if not reset_pagination else None
                    )
                elif context["type"] == "corporation":
                    data, cursor, has_more = optimizer.load_corporation_data_cursor_paginated(
                        context["value"],
                        page_size=page_size,
                        cursor_doc=app_state.current_cursor if not reset_pagination else None
                    )
                else:
                    return [], None, False

                if reset_pagination:
                    app_state.current_data = data
                else:
                    app_state.current_data.extend(data)

                app_state.current_cursor = cursor
                app_state.has_more_pages = has_more
                app_state.current_context = context

                if not reset_pagination:
                    app_state.page_number += 1

                return data, cursor, has_more

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {e}")
                return [], None, False

        def optimized_search(search_term, context):

            if not search_term.strip():
                return app_state.current_data

            return optimizer.search_documents_optimized(search_term, context)

        def bulk_delete_optimized(selected_doc_ids):

            operations = [{"type": "delete", "doc_id": doc_id} for doc_id in selected_doc_ids]

            return optimizer.bulk_operation_optimized(operations)


        def schedule_cache_cleanup():

            optimizer.clear_cache_smart()

            admin.after(600000, schedule_cache_cleanup)


        admin.after(600000, schedule_cache_cleanup)

        return optimizer, app_state, load_page_data, optimized_search, bulk_delete_optimized

    admin = tk.Tk()

    admin.title(f"Admin Dashboard - Record Management System v{VERSION}")
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


    notification_system = NotificationSystem(admin, admin_data)


    current_loaded_data = []
    current_context = {"type": None, "value": None}
    image_refs = []
    branches = set()


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


    def get_file_icon(filename):

        if not filename:
            return "📄", "Unknown File"

        filename_lower = filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.jfif' )):
            return "🖼️", "Image File"
        elif filename_lower.endswith('.pdf'):
            return "📄", "PDF Document"
        elif filename_lower.endswith(('.doc', '.docx')):
            return "📝", "Word Document"
        elif filename_lower.endswith(('.xls', '.xlsx')):
            return "📊", "Excel File"
        elif filename_lower.endswith('.txt'):
            return "📃", "Text File"
        else:
            return "📄", "Document"


    def create_default_image(icon, file_type, size=(200, 200)):
        """Create a default image with icon and file type text"""
        # Create a simple colored background image
        img = Image.new('RGB', size, color='#f1f5f9')
        return img


    sidebar = tk.Frame(admin, width=sidebar_width, bg=COLORS['sidebar'], relief="flat")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)


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


    header_frame = tk.Frame(main_frame, bg=COLORS['surface'], relief="flat", bd=1)
    header_frame.pack(fill="x", pady=(0, responsive_padding), ipady=int(15 * font_scale))


    title_frame = tk.Frame(header_frame, bg=COLORS['surface'])
    title_frame.pack(side="left", fill="both", expand=True)

    tk.Label(
        title_frame,
        text="Record Management System",
        font=("Segoe UI", get_font_size(20), "bold"),
        bg=COLORS['surface'],
        fg=COLORS['text']
    ).pack(pady=int(10 * font_scale))


    buttons_frame = tk.Frame(header_frame, bg=COLORS['surface'])
    buttons_frame.pack(side="right", padx=int(20 * font_scale), pady=int(10 * font_scale))

    content_frame = tk.Frame(main_frame, bg=COLORS['background'])
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Responsive image viewer
    viewer_frame = tk.Frame(content_frame, bg=COLORS['surface'], relief="flat", bd=1)
    viewer_frame.pack(side="left", fill=tk.BOTH, expand=True, padx=(0, int(10 * font_scale)))
    viewer_frame.pack_propagate(False)


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


    scroll_frame.bind("<MouseWheel>", _on_mousewheel)
    main_frame.bind("<MouseWheel>", _on_mousewheel)


    canvas.focus_set()

    def bind_mousewheel_to_main_widgets(widget, visited=None, depth=0):
        """Safe recursive binding with cycle detection and depth limit"""
        if visited is None:
            visited = set()


        if depth > 50:  #
            return

        # Prevent cycles
        widget_id = id(widget)
        if widget_id in visited:
            return
        visited.add(widget_id)

        try:

            if widget.winfo_exists():
                widget.bind("<MouseWheel>", _on_mousewheel)
                widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
                widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        except (tk.TclError, RuntimeError, AttributeError):

            return


        try:
            children = widget.winfo_children()
            for child in children:
                bind_mousewheel_to_main_widgets(child, visited, depth + 1)
        except (tk.TclError, RuntimeError):
            # Widget or children are destroyed, skip
            pass



    def load_branches_only():

        try:

            docs = db.collection("Uploaded_Images").where("corporations", "in", group1_corporations).stream()

            branches_set = set()
            doc_count = 0

            for doc in docs:
                doc_count += 1
                if doc_count > 50000:
                    break

                data = doc.to_dict()
                if data and "branch" in data:
                    branch = data.get("branch", "").strip()
                    if branch:
                        branches_set.add(branch)

            return sorted(list(branches_set))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load branches: {e}")
            return []

    def load_branch_data(branch_name):
        try:

            docs = db.collection("Uploaded_Images").where("branch", "==", branch_name).stream()

            branch_data = []
            doc_count = 0

            for doc in docs:
                doc_count += 1

                data = doc.to_dict()
                if data:
                    data["doc_id"] = doc.id
                    branch_data.append(data)

            return branch_data

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load branch data for '{branch_name}': {e}")
            return []

    def load_corporation_data(corporation_name):

        try:

            docs = db.collection("Uploaded_Images").where("corporations", "==", corporation_name).stream()

            corp_data = []
            doc_count = 0

            for doc in docs:
                doc_count += 1

                data = doc.to_dict()
                if data:
                    data["doc_id"] = doc.id
                    corp_data.append(data)

            return corp_data

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load corporation data for '{corporation_name}': {e}")
            return []

    # Initialize with lightweight branch loading
    available_branches = load_branches_only()
    branches.update(available_branches)


    def refresh_data():

        current_time = time.time()

        # Prevent rapid successive calls
        if hasattr(refresh_data, '_last_refresh'):
            if current_time - refresh_data._last_refresh < 2.0:
                return

        # Prevent concurrent refreshes
        if hasattr(refresh_data, '_refreshing') and refresh_data._refreshing:
            return

        def do_refresh():
            try:
                refresh_data._refreshing = True
                refresh_data._last_refresh = current_time

                # Force reload current data
                if current_context.get("type") == "branch":
                    show_images(branch=current_context["value"], force_reload=True)
                elif current_context.get("type") == "corporation":
                    show_images(corporation=current_context["value"], force_reload=True)
                else:
                    # Refresh branch list if no specific context
                    nonlocal available_branches
                    available_branches = load_branches_only()
                    branches.clear()
                    branches.update(available_branches)
                    show_branch_buttons()

            except Exception as e:
                messagebox.showerror("Refresh Error", f"Failed to refresh data: {str(e)}")
            finally:
                refresh_data._refreshing = False

        # Run refresh in separate thread
        threading.Thread(target=do_refresh, daemon=True).start()

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

    def show_images(branch=None, corporation=None, force_reload=False):
        global current_loaded_data, current_context

        # Ensure variables are properly initialized
        try:
            _ = current_context.get("type")
            len(current_loaded_data)
        except (NameError, AttributeError):
            current_loaded_data = []
            current_context = {"type": None, "value": None}

        # Determine what data we need
        if corporation:
            context_key = ("corporation", corporation)
        elif branch:
            context_key = ("branch", branch)
        else:
            return

        # Check if we need to reload data
        need_reload = (force_reload or
                       current_context.get("type") != context_key[0] or
                       current_context.get("value") != context_key[1] or
                       len(current_loaded_data) == 0)

        if need_reload:
            # Clear existing UI
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            image_refs.clear()

            # Show loading indicator
            loading_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
            loading_frame.pack(pady=50, padx=20, fill="x", ipady=30)

            loading_label = tk.Label(
                loading_frame,
                text=f"🔄 Loading {context_key[0]}: {context_key[1]}...",
                font=("Segoe UI", get_font_size(16), "bold"),
                bg=COLORS['surface'],
                fg=COLORS['secondary']
            )
            loading_label.pack()

            # Update UI to show loading
            admin.update_idletasks()

            # Load data based on selection
            if corporation:
                current_loaded_data = load_corporation_data(corporation)
            elif branch:
                current_loaded_data = load_branch_data(branch)

            # Update current context
            current_context = {"type": context_key[0], "value": context_key[1]}

            # Remove loading indicator
            loading_frame.destroy()

        # Clear UI for fresh display
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        # Use current_loaded_data instead of images_by_branch
        all_images = current_loaded_data

        # Responsive filter frame
        filter_padding = max(12, int(15 * font_scale))
        filter_frame = tk.Frame(scroll_frame, bg=COLORS['surface'], relief="flat", bd=1)
        filter_frame.pack(pady=(filter_padding, int(10 * font_scale)), fill="x",
                          padx=int(20 * font_scale), ipady=int(12 * font_scale))

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
                        # Handle both image_url (legacy) and file_url (new)
                        url = img.get("file_url") or img.get("image_url")
                        fname = img.get("filename", "document")

                        if url:
                            response = requests.get(url, timeout=10)
                            if response.status_code == 200:
                                with open(f"{folder}/{fname}", "wb") as f:
                                    f.write(response.content)
                                success += 1
                            else:
                                failed += 1
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
                                          f"Are you sure you want to delete {len(selected_images)} selected files?")
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
                    except Exception:
                        pass

                    db.collection("Uploaded_Images").document(doc_data["doc_id"]).delete()

                    # Remove from current loaded data
                    if doc_data in current_loaded_data:
                        current_loaded_data.remove(doc_data)
                    if doc_data in filtered_images:
                        filtered_images.remove(doc_data)
                    selected_images.discard(doc_data["doc_id"])
                    success += 1
                except Exception:
                    failed += 1

            # Update filtered images
            filtered_images[:] = [img for img in current_loaded_data if matches(img)]
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

        # IMPROVED FILTER APPLICATION WITH DEBOUNCING
        def create_debounced_filter():
            """Create a debounced filter function to prevent excessive calls"""
            filter_timer = [None]

            def debounced_apply_filters(*args):
                # Cancel previous timer if exists
                if filter_timer[0]:
                    admin.after_cancel(filter_timer[0])

                # Set new timer for delayed execution
                filter_timer[0] = admin.after(300, actual_apply_filters)  # 300ms delay

            def actual_apply_filters():
                """The actual filter function that does the work"""
                try:
                    filter_timer[0] = None  # Clear timer reference

                    ttype = trans_type_var.get().strip().lower()
                    start_val = clean_date(start_date_var.get().strip())
                    end_val = clean_date(end_date_var.get().strip())

                    # Validate dates
                    start_date = None
                    end_date = None

                    if start_val:
                        try:
                            start_date = datetime.datetime.strptime(start_val, "%Y-%m-%d")
                        except ValueError:
                            pass

                    if end_val:
                        try:
                            end_date = datetime.datetime.strptime(end_val, "%Y-%m-%d")
                        except ValueError:
                            pass

                    # Apply filters
                    filtered = []
                    total_images = len(all_images)

                    for i, img in enumerate(all_images):
                        if matches(img):
                            filtered.append(img)

                    # Update UI
                    filtered_images.clear()
                    filtered_images.extend(filtered)
                    current_page[0] = 0
                    display_images_page()

                except Exception as e:
                    messagebox.showerror("Filter Error", f"Failed to apply filters: {str(e)}")

            return debounced_apply_filters

        apply_filters = create_debounced_filter()

        def on_filename_search_change(*args):
            current_search = filename_search_var.get().strip()
            if current_search and current_search.lower() != "type filename here...":
                apply_filters()
            elif not current_search:
                apply_filters()

        filename_search_var.trace_add("write", on_filename_search_change)

        def download_all_images():
            if not filtered_images:
                messagebox.showinfo("No Files", "No filtered files to download.")
                return

            folder = filedialog.askdirectory(title="Select Download Folder")
            if not folder:
                return

            success, failed = 0, 0
            for img in filtered_images:
                try:
                    # Handle both image_url (legacy) and file_url (new)
                    url = img.get("file_url") or img.get("image_url")
                    fname = img.get("filename", "document")

                    if url:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            with open(f"{folder}/{fname}", "wb") as f:
                                f.write(response.content)
                            success += 1
                        else:
                            failed += 1
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
                    text=f"Search results for '{search_query}': {results_count} files found",
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
                text="Select All (this page & filter)",
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
                        text="No files match your search",
                        font=("Segoe UI", get_font_size(16), "bold"),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack()
                    tk.Label(
                        no_images_frame,
                        text=f"No files found with filename containing: '{filename_search_var.get().strip()}'",
                        font=("Segoe UI", get_font_size(12)),
                        fg=COLORS['muted'],
                        bg=COLORS['surface']
                    ).pack(pady=(int(5 * font_scale), 0))
                else:
                    tk.Label(
                        no_images_frame,
                        text="No files found",
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

            def view_full_file(file_data):
                """Enhanced file viewer that handles different file types"""
                filename = file_data.get('filename', 'Unknown File')
                file_url = file_data.get("file_url") or file_data.get("image_url")

                if not file_url:
                    messagebox.showerror("Error", "No file URL available")
                    return

                top = tk.Toplevel(admin)
                top.title(f"{filename}")

                # Responsive popup size
                popup_width = max(800, min(1200, int(screen_width * 0.8)))
                popup_height = max(600, min(900, int(screen_height * 0.8)))
                top.geometry(f"{popup_width}x{popup_height}")
                top.configure(bg=COLORS['background'])

                # Check if it's an image file
                is_image = filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.jfif'))

                if is_image:
                    # Handle image files
                    try:
                        response = requests.get(file_url, timeout=10)
                        if response.status_code == 200:
                            image_data = BytesIO(response.content)
                            pil_image = Image.open(image_data).convert("RGB")

                            canvas_popup = tk.Canvas(top, bg=COLORS['surface'], highlightthickness=0, bd=0)
                            canvas_popup.pack(fill="both", expand=True, padx=int(20 * font_scale),
                                              pady=(int(20 * font_scale), int(10 * font_scale)))

                            zoom_factor = [1.0]
                            base_image = pil_image

                            def render_image():
                                new_size = (int(base_image.width * zoom_factor[0]),
                                            int(base_image.height * zoom_factor[0]))
                                resized_img = base_image.resize(new_size, Image.LANCZOS)
                                tk_image = ImageTk.PhotoImage(resized_img, master=top)

                                canvas_popup.delete("IMG")
                                canvas_popup.image_id = canvas_popup.create_image(canvas_popup.winfo_width() // 2,
                                                                                  canvas_popup.winfo_height() // 2,
                                                                                  anchor="center", image=tk_image,
                                                                                  tags="IMG")
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
                                text="Zoom In",
                                bg=COLORS['secondary'],
                                fg="white",
                                command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0] * 1.1), render_image()],
                                **zoom_btn_style
                            ).pack(side="left", padx=(int(10 * font_scale), int(5 * font_scale)))

                            tk.Button(
                                zoom_frame,
                                text="Zoom Out",
                                bg=COLORS['muted'],
                                fg="white",
                                command=lambda: [zoom_factor.__setitem__(0, zoom_factor[0] / 1.1), render_image()],
                                **zoom_btn_style
                            ).pack(side="left", padx=int(5 * font_scale))

                            render_image()
                        else:
                            tk.Label(top, text="Failed to load image", bg=COLORS['background'], fg=COLORS['danger'],
                                     font=("Segoe UI", get_font_size(12))).pack(pady=50)
                    except Exception as e:
                        tk.Label(top, text=f"Failed to load image: {e}", bg=COLORS['background'], fg=COLORS['danger'],
                                 font=("Segoe UI", get_font_size(12))).pack(pady=50)
                else:
                    # Handle non-image files (PDF, DOCX, etc.)
                    info_frame = tk.Frame(top, bg=COLORS['background'])
                    info_frame.pack(fill="both", expand=True, padx=int(40 * font_scale), pady=int(40 * font_scale))

                    # File icon and info
                    icon, file_type = get_file_icon(filename)

                    tk.Label(
                        info_frame,
                        text=icon,
                        font=("Segoe UI", get_font_size(48)),
                        bg=COLORS['background'],
                        fg=COLORS['secondary']
                    ).pack(pady=(0, int(20 * font_scale)))

                    tk.Label(
                        info_frame,
                        text=file_type,
                        font=("Segoe UI", get_font_size(18), "bold"),
                        bg=COLORS['background'],
                        fg=COLORS['text']
                    ).pack(pady=(0, int(10 * font_scale)))

                    tk.Label(
                        info_frame,
                        text=filename,
                        font=("Segoe UI", get_font_size(14)),
                        bg=COLORS['background'],
                        fg=COLORS['muted'],
                        wraplength=int(400 * font_scale)
                    ).pack(pady=(0, int(30 * font_scale)))

                    # Download button for non-image files
                    def download_file():
                        try:
                            file_path = filedialog.asksaveasfilename(
                                defaultextension="",
                                initialname=filename,
                                title="Save File As"
                            )
                            if file_path:
                                response = requests.get(file_url, timeout=30)
                                if response.status_code == 200:
                                    with open(file_path, 'wb') as f:
                                        f.write(response.content)
                                    messagebox.showinfo("Success", f"File downloaded successfully to:\n{file_path}")
                                else:
                                    messagebox.showerror("Error", "Failed to download file")
                        except Exception as e:
                            messagebox.showerror("Error", f"Download failed: {e}")

                    tk.Button(
                        info_frame,
                        text="Download File",
                        font=("Segoe UI", get_font_size(12), "bold"),
                        bg=COLORS['success'],
                        fg="white",
                        bd=0,
                        relief="flat",
                        cursor="hand2",
                        padx=int(30 * font_scale),
                        pady=int(12 * font_scale),
                        command=download_file
                    ).pack(pady=int(10 * font_scale))

                    # File details
                    details_frame = tk.Frame(info_frame, bg=COLORS['surface'], relief="flat", bd=1)
                    details_frame.pack(fill="x", pady=int(20 * font_scale), ipady=int(15 * font_scale))

                    tk.Label(
                        details_frame,
                        text="File Details",
                        font=("Segoe UI", get_font_size(14), "bold"),
                        bg=COLORS['surface'],
                        fg=COLORS['text']
                    ).pack(pady=(0, int(10 * font_scale)))

                    # Display file metadata
                    details_info = [
                        ("Filename", filename),
                        ("Branch", file_data.get("branch", "N/A")),
                        ("Uploaded By", file_data.get("uploaded_by", "N/A")),
                        ("Transaction Date", file_data.get("date", "N/A")),
                        ("Transaction Type", file_data.get("transaction_type", "N/A")),
                    ]

                    for label, value in details_info:
                        detail_row = tk.Frame(details_frame, bg=COLORS['surface'])
                        detail_row.pack(fill="x", padx=int(20 * font_scale), pady=int(3 * font_scale))

                        tk.Label(
                            detail_row,
                            text=f"{label}:",
                            font=("Segoe UI", get_font_size(11), "bold"),
                            bg=COLORS['surface'],
                            fg=COLORS['text'],
                            width=18,
                            anchor="w"
                        ).pack(side="left")

                        tk.Label(
                            detail_row,
                            text=str(value),
                            font=("Segoe UI", get_font_size(11)),
                            bg=COLORS['surface'],
                            fg=COLORS['muted'],
                            anchor="w",
                            wraplength=int(300 * font_scale)
                        ).pack(side="left", fill="x", expand=True)

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

            # Modified create_default_icon function - no async loading needed
            def create_default_icon(file_data, img_label):
                """Create and display default icon immediately"""
                filename = file_data.get("filename", "")
                icon, file_type = get_file_icon(filename)

                # Create a simple icon display
                img_label.config(
                    text=f"{icon}\n{file_type}",
                    font=("Segoe UI", get_font_size(12), "bold"),
                    fg=COLORS['secondary'],
                    bg=COLORS['surface'],
                    justify="center",
                    compound="top"
                )

                # Make it clickable
                img_label.bind("<Button-1>", lambda e, data=file_data: view_full_file(data))

                # Hover effects
                def on_enter(e):
                    img_label.config(bg="#f1f5f9")

                def on_leave(e):
                    img_label.config(bg=COLORS['surface'])

                img_label.bind("<Enter>", on_enter)
                img_label.bind("<Leave>", on_leave)

            # Responsive file cards
            for file_data in page_images:
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

                # Responsive file preview with default icon
                img_width = max(20, int(24 * font_scale))
                img_height = max(8, int(10 * font_scale))

                img_label = tk.Label(
                    card_frame,
                    bg=COLORS['surface'],
                    text="Loading...",
                    font=("Segoe UI", get_font_size(11)),
                    fg=COLORS['muted'],
                    width=img_width,
                    height=img_height,
                    borderwidth=0,
                    relief="flat",
                    justify="center"
                )
                img_label.grid(row=0, column=0, padx=int(15 * font_scale), pady=int(10 * font_scale), sticky="nw")

                # Immediately create default icon (no async loading)
                create_default_icon(file_data, img_label)

                # Responsive info section
                info_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                info_frame.grid(row=0, column=1, padx=int(15 * font_scale), sticky="nsew")

                # Enhanced filename display with search highlighting
                filename_text = file_data.get("filename", "")
                search_query = filename_search_var.get().strip().lower()
                if search_query and search_query != "type filename here..." and search_query in filename_text.lower():
                    filename_display = f"{filename_text}"
                    filename_color = COLORS['success']
                else:
                    filename_display = filename_text
                    filename_color = COLORS['muted']

                # Responsive info data
                info_data = [
                    ("File", filename_display, filename_color),
                    ("Branch", file_data.get("branch", ""), COLORS['muted']),
                    ("Uploaded By", file_data.get("uploaded_by", ""), COLORS['muted']),
                    ("Transaction Date", file_data.get("date", ""), COLORS['muted']),
                    ("Transaction Type", file_data.get("transaction_type", ""), COLORS['muted']),
                    ("Date Uploaded", format_timestamp(file_data.get("timestamp", "")), COLORS['muted']),
                    ("Lotes", file_data.get("palawan_reference", "N/A"), COLORS['muted']),
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
                              "bold" if label == "File" and text_color == COLORS['success'] else "normal"),
                        bg=COLORS['surface'],
                        fg=text_color,
                        anchor="w",
                        wraplength=wrap_length
                    ).pack(side="left")

                # Responsive actions frame
                actions_frame = tk.Frame(card_frame, bg=COLORS['surface'])
                actions_frame.grid(row=0, column=2, padx=int(15 * font_scale), pady=int(10 * font_scale), sticky="ne")

                # Responsive checkbox
                select_var = tk.BooleanVar(value=file_data["doc_id"] in selected_images)
                cb = tk.Checkbutton(
                    actions_frame,
                    text="Select",
                    variable=select_var,
                    command=lambda doc_id=file_data["doc_id"], var=select_var: on_select(doc_id, var),
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
                    text="View",
                    font=("Segoe UI", get_font_size(9), "bold"),
                    bg=COLORS['accent'],
                    fg="white",
                    bd=0,
                    relief="flat",
                    cursor="hand2",
                    padx=view_btn_padding_x,
                    pady=view_btn_padding_y,
                    command=lambda data=file_data: view_full_file(data)
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
                text="Previous",
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
                text="Next",
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
            text="Apply Filters",
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
            text="Download All",
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
            text="Clear",
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

        # Initialize filtered images with all loaded data
        filtered_images.clear()
        filtered_images.extend(all_images)
        display_images_page()

        # Ensure scroll wheel works on all main content widgets
        bind_mousewheel_to_main_widgets(scroll_frame)

        # Also bind to the canvas directly for better responsiveness
        canvas.bind("<Enter>", lambda e: canvas.focus_set())

        # Make sure the canvas updates its scroll region
        scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    # Responsive Sidebar Design
    group_name = admin_data.get("group", "Unknown Group")

    # Responsive sidebar header
    header_height = max(70, int(80 * font_scale))
    sidebar_header = tk.Frame(sidebar, bg=COLORS['sidebar'], height=header_height)
    sidebar_header.pack(fill="x", pady=(0, int(10 * font_scale)))
    sidebar_header.pack_propagate(False)

    tk.Label(
        sidebar_header,
        text="Welcome",
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

    # Responsive scrollable branches container
    available_height = screen_height - 200
    branches_container_height = max(150, min(300, int(available_height * 0.4)))

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
    branches_canvas.bind("<Button-4>", _on_branches_mousewheel)
    branches_canvas.bind("<Button-5>", _on_branches_mousewheel)

    # Initialize variables for the sidebar components
    search_var = tk.StringVar()
    selected_corp_var = tk.StringVar()
    selected_corp_var.set("Select Corporation")

    corp_list = sorted(group1_corporations)

    def show_corporation_selector():
        popup = tk.Toplevel(admin)
        popup.title("Select Corporation")

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
            text="Choose a Corporation",
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
                show_images(corporation=selected)
            else:
                messagebox.showwarning("Select Corporation", "Please select a corporation.")

        tk.Button(
            content_frame,
            text="Show Files",
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

    # Create a proper container for all bottom elements
    bottom_container = tk.Frame(sidebar, bg=COLORS['sidebar'])
    bottom_container.pack(fill="x", pady=(int(5 * font_scale), 0))

    # Search section - move this ABOVE the buttons
    search_section = tk.Frame(bottom_container, bg=COLORS['sidebar'])
    search_section.pack(fill="x", padx=int(15 * font_scale), pady=(0, int(8 * font_scale)))

    tk.Label(
        search_section,
        text="Search Branch:",
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
        text="Corporation:",
        font=("Segoe UI", get_font_size(11), "bold"),
        bg=COLORS['sidebar'],
        fg="white"
    ).pack(pady=(0, int(3 * font_scale)))

    def on_corp_selected(*args):
        selected_corp = selected_corp_var.get()
        if selected_corp and selected_corp != "Select Corporation":
            # Filter branches that have documents for this corporation
            # This would require a more complex query, but for now we'll show all branches
            show_branch_buttons(sorted(branches))

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
        'pady': int(6 * font_scale)
    }

    tk.Button(
        button_section,
        text="Select Corporation",
        command=show_corporation_selector,
        bg=COLORS['secondary'],
        fg="white",
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

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
        popup.title("Head Office Options")

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
            text="Head Office Options",
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
            text="Upload Documents",
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
            upload_btn.config(bg='#059669')

        def on_upload_leave(e):
            upload_btn.config(bg=COLORS['success'])

        upload_btn.bind("<Enter>", on_upload_enter)
        upload_btn.bind("<Leave>", on_upload_leave)

        # View button with hover effects
        view_btn = tk.Button(
            content_frame,
            text="View Documents",
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
            view_btn.config(bg='#2563eb')

        def on_view_leave(e):
            view_btn.config(bg=COLORS['secondary'])

        view_btn.bind("<Enter>", on_view_enter)
        view_btn.bind("<Leave>", on_view_leave)

        # Close button with subtle styling
        close_btn = tk.Button(
            content_frame,
            text="Close",
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
        text="Add User",
        bg=COLORS['success'],
        fg="white",
        command=lambda: open_add_user_popup_group1(admin),
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

    tk.Button(
        button_section,
        text="Head Office",
        bg='#8b5cf6',  # Purple color
        fg="white",
        command=head_office_menu,
        **action_btn_style
    ).pack(pady=int(3 * font_scale), fill="x")

    tk.Button(
        button_section,
        text="Logout",
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
        text="Developed by:",
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
            filtered = [branch for branch in sorted(branches) if query in branch.lower()]
        else:
            filtered = sorted(branches)
        show_branch_buttons(filtered)

    search_var.trace_add("write", update_branch_search)

    def create_branch_button_handler(branch_name):
        """Create a handler for branch button clicks with proper loading"""

        def handler():
            last_branch[0] = branch_name
            last_corporation[0] = None
            show_images(branch=branch_name)

        return handler

    def show_branch_buttons(filtered=None):
        for widget in branches_frame.winfo_children():
            widget.destroy()

        show_list = filtered if filtered is not None else sorted(branches)

        branch_btn_style = {
            'font': ("Segoe UI", get_font_size(10), "bold"),
            'bg': "#475569",
            'fg': "white",
            'bd': 0,
            'relief': "flat",
            'cursor': "hand2",
            'width': button_width,
            'pady': int(6 * font_scale)
        }

        for branch in show_list:
            btn = tk.Button(
                branches_frame,
                text=f"{branch}",
                command=create_branch_button_handler(branch),  # Use the new handler
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

    # IMPROVED WINDOW RESIZE HANDLER WITH DEBOUNCING
    def create_resize_handler():
        """Create debounced window resize handler"""
        resize_timer = [None]
        last_size = [None, None]

        def on_window_resize(event):
            if event.widget != admin:
                return

            current_width = admin.winfo_width()
            current_height = admin.winfo_height()

            # Only process significant size changes
            if (last_size[0] is None or
                    abs(current_width - last_size[0]) > 50 or
                    abs(current_height - last_size[1]) > 50):

                # Cancel previous resize timer
                if resize_timer[0]:
                    admin.after_cancel(resize_timer[0])

                # Set new timer for delayed resize handling
                resize_timer[0] = admin.after(500, lambda: handle_resize(current_width, current_height))

        def handle_resize(width, height):
            """Handle the actual resize logic"""
            try:
                resize_timer[0] = None
                last_size[0] = width
                last_size[1] = height

            except Exception as e:
                messagebox.showerror("Error", f"Resize handling failed: {e}")

        return on_window_resize

    # Initialize branch buttons
    show_branch_buttons()

    # Handle window resize events with debouncing
    admin.bind("<Configure>", create_resize_handler())

    # SAFE WIDGET CLEANUP FUNCTION
    def cleanup_widgets():

        try:
            # Clear image references
            image_refs.clear()

            # Clear data structures
            current_loaded_data.clear()
            branches.clear()

            # Reset state variables
            last_branch[0] = None
            last_corporation[0] = None
            current_context.clear()

        except Exception as e:
            messagebox.showerror("Error", f"Cleanup failed: {e}")

    # Bind cleanup to window close event
    def on_closing():
        cleanup_widgets()
        admin.destroy()

    admin.protocol("WM_DELETE_WINDOW", on_closing)

    if branches:
        show_branch_buttons()

    admin.mainloop()