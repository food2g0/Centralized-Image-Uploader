import tkinter as tk
from tkinter import messagebox, filedialog
from firebase_config import db
from PIL import Image, ImageTk
import requests
from add_user_group1 import open_add_user_popup_group1
from io import BytesIO

# ... [Keep your imports and firebase_config, etc.]

def open_admin_dashboard_group1(admin_data):
    import tkinter as tk
    from tkinter import messagebox, filedialog
    from firebase_config import db
    from PIL import Image, ImageTk
    import requests
    from add_user_group1 import open_add_user_popup_group1
    from io import BytesIO

    admin = tk.Tk()  
    admin.title("Admin Dashboard")
    admin.geometry("1024x720")

    sidebar = tk.Frame(admin, width=220, bg="#2c3e50", height=800, relief="raised")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False) 

    hamburger_btn = tk.Button(admin, text="☰", font=("Arial", 18), bg="#34495e", fg="white", bd=0, state="disabled")
    hamburger_btn.place(x=5, y=5, width=40, height=40)

    main_frame = tk.Frame(admin, bg="#ecf0f1")
    main_frame.pack(side="left", fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="Record Management System", font=("Arial", 16), bg="#f1ecec").pack(pady=10)

    frame = tk.Frame(main_frame, bg="#ecf0f1")
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, bg="#ecf0f1", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scroll_frame = tk.Frame(canvas, bg="#ecf0f1")
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(scroll_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    image_refs = []

    group1_corporations = {
        "ATLANTIC STARGEM", "GALLIUM GRANITE", "GOLD BARS", "GREEN AMBER (J)",
        "KING-ASIA GROUP", "KRYPTON KNIGHT", "MAXI-WEALTH", "METROGOLD STAR",
        "NORTH-WESTERN PACIFIC", "PACIFIC METROSTAR", "PUREGOLD KARAT",
        "SAN SEBASTIAN SILVER", "WORLDCREST", "WORLDGEM"
    }

    docs = db.collection("Uploaded_Images").stream()
    branches = set()
    images_by_branch = {}

    for doc in docs:
        data = doc.to_dict()
        corp = data.get("corporations", "").strip().upper()
        if corp in group1_corporations:
            branch = data.get("branch", "Unknown")
            data["doc_id"] = doc.id
            branches.add(branch)
            images_by_branch.setdefault(branch, []).append(data)

    branches = sorted(branches)

    def show_images(branch):
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()

        filter_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
        filter_frame.pack(pady=(10, 0), fill="x")

        all_images = images_by_branch.get(branch, [])
        transaction_types = sorted(set(img.get("transaction_type", "") for img in all_images if img.get("transaction_type")))
        transaction_types = ["All"] + transaction_types
        trans_type_var = tk.StringVar(value="All")

        tk.Label(filter_frame, text="Transaction Type:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
        trans_type_menu = tk.OptionMenu(filter_frame, trans_type_var, *transaction_types)
        trans_type_menu.config(font=("Arial", 10))
        trans_type_menu.pack(side="left", padx=(0, 10))

        try:
            from tkcalendar import DateEntry
        except ImportError:
            tk.Label(filter_frame, text="[tkcalendar not installed]", font=("Arial", 10), fg="red", bg="#ecf0f1").pack(side="left", padx=(0, 2))
            DateEntry = None

        tk.Label(filter_frame, text="Date:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
        date_var = tk.StringVar()

        if 'DateEntry' in locals() and DateEntry:
            date_picker = DateEntry(filter_frame, textvariable=date_var, font=("Arial", 10), width=12, date_pattern='yyyy-mm-dd')
            date_picker.pack(side="left", padx=(0, 10))
        else:
            date_entry = tk.Entry(filter_frame, textvariable=date_var, font=("Arial", 10), width=12)
            date_entry.pack(side="left", padx=(0, 10))

        # Pagination variables
        images_per_page = 10
        current_page = [0]  # list so it is mutable in nested functions
        filtered_images = []

        def apply_filters(*args):
            ttype = trans_type_var.get()
            date_val = date_picker.get().strip() if 'date_picker' in locals() else date_var.get().strip()
            filtered = all_images
            if ttype != "All" and date_val:
                filtered = [img for img in all_images if img.get("transaction_type", "") == ttype and img.get("date", "") == date_val]
            elif ttype != "All":
                filtered = [img for img in all_images if img.get("transaction_type", "") == ttype]
            elif date_val:
                filtered = [img for img in all_images if img.get("date", "") == date_val]
            filtered_images.clear()
            filtered_images.extend(filtered)
            current_page[0] = 0
            display_images_page()

        def display_images_page():
            for widget in scroll_frame.winfo_children():
                if widget != filter_frame:
                    widget.destroy()
            image_refs.clear()

            start = current_page[0] * images_per_page
            end = start + images_per_page
            page_images = filtered_images[start:end]

            if not page_images:
                tk.Label(scroll_frame, text="No images found.", font=("Arial", 12), fg="#c0392b", bg="#ecf0f1").pack(pady=20)
                return

            for img in page_images:
                frame = tk.Frame(scroll_frame, bg="white", relief="raised", bd=2)
                frame.pack(padx=10, pady=10, fill="x")
                img_label = tk.Label(frame, bg="white")
                try:
                    response = requests.get(img["image_url"], timeout=10)
                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        image_data = BytesIO(response.content)
                        pil_img = Image.open(image_data).convert("RGB")
                        pil_img.thumbnail((180, 180))
                        photo = ImageTk.PhotoImage(pil_img, master=admin)
                        img_label.config(image=photo)
                        img_label.image = photo
                        image_refs.append(photo)
                    else:
                        img_label.config(text="❌ Failed to load image", fg="red")
                except Exception:
                    img_label.config(text="❌ Failed to load image", fg="red")
                img_label.pack(side="left", padx=10)

                info_frame = tk.Frame(frame, bg="white")
                info_frame.pack(side="left", padx=10, fill="x", expand=True)
                for label, val in [
                    ("File", img.get("filename", "")),
                    ("Branch", img.get("branch", "")),
                    ("Timestamp", img.get("timestamp", "")),
                    ("Date of Transaction", img.get("date", "")),
                    ("Transaction type", img.get("transaction_type", ""))
                ]:
                    tk.Label(info_frame, text=f"📁 {label}: {val}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")

                def download_image(url=img["image_url"], fname=img.get("filename", "download")):
                    try:
                        save_path = filedialog.asksaveasfilename(initialfile=fname, defaultextension=".jpg")
                        if save_path:
                            with open(save_path, "wb") as f:
                                f.write(requests.get(url).content)
                            messagebox.showinfo("Download", f"Downloaded to {save_path}")
                    except Exception as err:
                        messagebox.showerror("Download Error", f"Could not download {fname}: {err}")

                tk.Button(info_frame, text="Download", font=("Arial", 9), bg="#27ae60", fg="white", command=download_image).pack(side="left", padx=4, pady=4)

                def delete_image(doc_data=img, cont=frame):
                    try:
                        db.collection("Uploaded_Images").document(doc_data["doc_id"]).delete()
                        cont.destroy()
                        messagebox.showinfo("Delete", f"Deleted {doc_data.get('filename')}")
                        if branch in images_by_branch:
                            images_by_branch[branch] = [i for i in images_by_branch[branch] if i["doc_id"] != doc_data["doc_id"]]
                            apply_filters()
                    except Exception as err:
                        messagebox.showerror("Delete Error", f"Could not delete {doc_data.get('filename')}: {err}")

                tk.Button(info_frame, text="Delete", font=("Arial", 9), bg="#c0392b", fg="white", command=delete_image).pack(side="left", padx=4, pady=4)

            # Pagination buttons
            nav_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
            nav_frame.pack(pady=5)
            tk.Button(nav_frame, text="⬅ Prev", state="normal" if current_page[0] > 0 else "disabled",
                      command=lambda: go_page(-1)).pack(side="left", padx=5)
            tk.Label(nav_frame, text=f"Page {current_page[0]+1} of {max(1, (len(filtered_images)-1)//images_per_page+1)}",
                     bg="#ecf0f1", font=("Arial", 10)).pack(side="left")
            tk.Button(nav_frame, text="Next ➡", state="normal" if end < len(filtered_images) else "disabled",
                      command=lambda: go_page(1)).pack(side="left", padx=5)

        def go_page(direction):
            current_page[0] += direction
            display_images_page()

        if 'date_picker' in locals():
            date_picker.bind("<<DateEntrySelected>>", apply_filters)
        trans_type_var.trace_add('write', lambda *a: apply_filters())

        filter_btn = tk.Button(filter_frame, text="Apply Filters", font=("Arial", 10), bg="#2980b9", fg="white", command=apply_filters)
        filter_btn.pack(side="left", padx=(0, 2))

        # Initial load
        filtered_images.clear()
        filtered_images.extend(all_images)
        display_images_page()

    # Sidebar layout
    group_name = admin_data.get("group", "Unknown Group")
    tk.Label(sidebar, text=f"Welcome Admin of {group_name}", font=("Poppins", 12), bg="#2c3e50", fg="white").pack(pady=(60,10))

    branches_frame = tk.Frame(sidebar, bg="#2c3e50")
    search_frame = tk.Frame(sidebar, bg="#2c3e50")
    search_var = tk.StringVar()

    def show_branch_buttons(filtered=None):
        for widget in branches_frame.winfo_children():
            widget.destroy()
        show_list = filtered if filtered is not None else branches
        for branch in show_list:
            tk.Button(branches_frame, text=branch, font=("Arial", 11), bg="#34495e", fg="white", width=18, command=lambda b=branch: show_images(b)).pack(pady=2)
        branches_frame.pack(pady=5)

    branches_visible = [False]

    def toggle_branch_buttons():
        if branches_visible[0]:
            branches_frame.pack_forget()
            search_frame.pack_forget()
            branches_visible[0] = False
        else:
            for widget in search_frame.winfo_children():
                widget.destroy()
            tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=16).pack(side="left", padx=2)
            tk.Button(search_frame, text="Search", font=("Arial", 10), bg="#2980b9", fg="white", command=lambda: show_branch_buttons([b for b in branches if search_var.get().strip().lower() in b.lower()])).pack(side="left", padx=2)
            search_frame.pack(pady=2)
            show_branch_buttons()
            branches_visible[0] = True

    tk.Button(sidebar, text="Select Branches", font=("Arial", 11), bg="#2980b9", fg="white", command=toggle_branch_buttons, width=18).pack(pady=5)
    tk.Button(sidebar, text="Add User", font=("Arial", 11), bg="#27ae60", fg="white", command=lambda: open_add_user_popup_group1(admin), width=18).pack(pady=5)

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

    tk.Button(sidebar, text="Logout", font=("Arial", 11), bg="#c0392b", fg="white", command=logout, width=18).pack(pady=5)
    tk.Label(sidebar, text="Developed by Paolo Somido", font=("Arial", 9), fg="lightgray", bg="#2c3e50").pack(side="bottom", pady=10)

    admin.mainloop()
