import tkinter as tk
from tkinter import messagebox, filedialog
from firebase_config import db
from PIL import Image, ImageTk
import requests
from add_user_group2 import open_add_user_popup_group2
from io import BytesIO

def open_admin_dashboard_group2(admin_data):
    admin = tk.Tk()  
    admin.title("Admin Dashboard")
    admin.geometry("1024x720")
   

    # Sidebar frame
    sidebar = tk.Frame(admin, width=220, bg="#2c3e50", height=800, relief="raised")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False) 

    # Hamburger button 
    hamburger_btn = tk.Button(admin, text="☰", font=("Arial", 18), bg="#34495e", fg="white", bd=0, state="disabled")
    hamburger_btn.place(x=5, y=5, width=40, height=40)

    # Main content frame
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
        # Resize the window width to match canvas
        canvas.itemconfig(scroll_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    image_refs = []

    group2_corporations = {
        "ASIAPHIL STAR", "MAJOREVIM", "MEGAWORLD DOMESTIC", "NORTHERN SUNSTAR",
        "SAINT BARBARA PRIME", "SAN RAMON PLATINUM", "SILVERSTAR (J)"
        }

# Fetch all uploaded images
    docs = db.collection("Uploaded_Images").stream()
    branches = set()
    images_by_branch = {}

    for doc in docs:
        data = doc.to_dict()
        corp = data.get("corporations", "").strip().upper()
    if corp in group2_corporations:
        branch = data.get("branch", "Unknown")
        data["doc_id"] = doc.id
        branches.add(branch)
        images_by_branch.setdefault(branch, []).append(data)

    branches = sorted(branches)

    def show_images(branch):
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        image_refs.clear()
        # --- Filtering UI ---
        filter_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
        filter_frame.pack(pady=(10, 0), fill="x")

        # Transaction type dropdown
        all_images = images_by_branch.get(branch, [])
        transaction_types = sorted(set(img.get("transaction_type", "") for img in all_images if img.get("transaction_type")))
        transaction_types = ["All"] + transaction_types
        trans_type_var = tk.StringVar(value="All")
        tk.Label(filter_frame, text="Transaction Type:", font=("Arial", 10), bg="#ecf0f1").pack(side="left", padx=(0, 2))
        trans_type_menu = tk.OptionMenu(filter_frame, trans_type_var, *transaction_types)
        trans_type_menu.config(font=("Arial", 10))
        trans_type_menu.pack(side="left", padx=(0, 10))

        # Date of transaction picker (using tkcalendar)
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

        def apply_filters(*args):
            ttype = trans_type_var.get()
            # Always get the value from the widget if using DateEntry
            if 'date_picker' in locals():
                date_val = date_picker.get().strip()
            else:
                date_val = date_var.get().strip()
            print(f"[DEBUG] Filter values: transaction_type='{ttype}', date='{date_val}'")
            print(f"[DEBUG] All image dates: {[img.get('date','') for img in all_images]}")
            filtered = all_images
            # Apply both filters together
            if ttype != "All" and date_val:
                filtered = [img for img in all_images if img.get("transaction_type", "") == ttype and img.get("date", "") == date_val]
            elif ttype != "All":
                filtered = [img for img in all_images if img.get("transaction_type", "") == ttype]
            elif date_val:
                filtered = [img for img in all_images if img.get("date", "") == date_val]
            print(f"[DEBUG] Filtered images count: {len(filtered)}")
            if filtered:
                print(f"[DEBUG] First filtered image: {filtered[0]}")
            display_images(filtered)

        filter_btn = tk.Button(filter_frame, text="Apply Filters", font=("Arial", 10), bg="#2980b9", fg="white", command=apply_filters)
        filter_btn.pack(side="left", padx=(0, 2))
        # Trigger filter on date picker selection for better UX
        if 'date_picker' in locals():
            date_picker.bind("<<DateEntrySelected>>", apply_filters)
        trans_type_var.trace_add('write', lambda *a: apply_filters())

        # Loading indicator
        loading_label = tk.Label(scroll_frame, text="Loading images...", font=("Arial", 12), fg="#2980b9", bg="#ecf0f1")
        loading_label.pack(pady=20)
        scroll_frame.update_idletasks()

        def display_images(images):
            for widget in scroll_frame.winfo_children():
                # Don't destroy filter_frame
                if widget != filter_frame:
                    widget.destroy()
            image_refs.clear()
            if not images:
                tk.Label(scroll_frame, text="No images found.", font=("Arial", 12), fg="#c0392b", bg="#ecf0f1").pack(pady=20)
                return
            for img in images:
                frame = tk.Frame(scroll_frame, bg="white", relief="raised", bd=2)
                frame.pack(padx=10, pady=10, fill="x")
                photo = None
                img_label = tk.Label(frame, bg="white")
                try:
                    response = requests.get(img["image_url"], timeout=10)
                    # print(f"Fetching image from: {img['image_url']}")
                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        image_data = BytesIO(response.content)
                        pil_img = Image.open(image_data).convert("RGB")
                        pil_img.thumbnail((180, 180))
                        photo = ImageTk.PhotoImage(pil_img, master=admin)
                        img_label.config(image=photo)
                        img_label.image = photo  
                        image_refs.append(photo)  # Also keep in list
                    else:
                        img_label.config(text="❌ Failed to load image", fg="red")
                except Exception as e:
                    print("Image load error:", e)
                    img_label.config(text="❌ Failed to load image", fg="red")
                img_label.pack(side="left", padx=10)

                # --- Info section ---
                info_frame = tk.Frame(frame, bg="white")
                info_frame.pack(side="left", padx=10, fill="x", expand=True)
                filename = img.get("filename", "")
                branchname = img.get("branch", "")
                timestamp = img.get("timestamp", "")
                selected_date = img.get("date", "")
                transaction_type = img.get("transaction_type", "")
                image_url = img.get("image_url", "")
                tk.Label(info_frame, text=f"📁 File: {filename}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")
                tk.Label(info_frame, text=f"📁 Branch: {branchname}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")
                tk.Label(info_frame, text=f"📁 Timestamp: {timestamp}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")
                tk.Label(info_frame, text=f"📁 Date of Transaction: {selected_date}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")
                tk.Label(info_frame, text=f"📁 Transaction type: {transaction_type}", justify="left", font=("Arial", 10), bg="#fff").pack(anchor="w")

                def download_image(url=image_url, fname=filename):
                    try:
                        save_path = filedialog.asksaveasfilename(initialfile=fname, defaultextension=".jpg",
                            filetypes=[("JPEG Image", "*.jpg;*.jpeg"), ("PNG Image", "*.png"), ("All Files", "*.*")])
                        if not save_path:
                            return
                        img_data = requests.get(url).content
                        with open(save_path, "wb") as f:
                            f.write(img_data)
                        messagebox.showinfo("Download", f"Downloaded to {save_path}")
                    except Exception as err:
                        messagebox.showerror("Download Error", f"Could not download {fname}: {err}")

                dl_btn = tk.Button(info_frame, text="Download", font=("Arial", 9), bg="#27ae60", fg="white",
                                  command=download_image)
                dl_btn.pack(side="left", padx=4, pady=4)

                def delete_image(doc_data=img, cont=frame):
                    try:
                        docs = db.collection("Uploaded_Images").where("filename", "==", doc_data.get("filename")).where("image_url", "==", doc_data.get("image_url")).where("branch", "==", doc_data.get("branch")).stream()
                        for d in docs:
                            d.reference.delete()
                        cont.destroy()
                        messagebox.showinfo("Delete", f"Deleted {doc_data.get('filename')}")
                    except Exception as err:
                        messagebox.showerror("Delete Error", f"Could not delete {doc_data.get('filename')}: {err}")

                del_btn = tk.Button(info_frame, text="Delete", font=("Arial", 9), bg="#c0392b", fg="white",
                                  command=lambda d=img, c=frame: delete_image(d, c))
                del_btn.pack(side="left", padx=4, pady=4)

        loading_label.destroy()
        display_images(all_images)

        # Sidebar: Select Branches button, then show all branches as buttons
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
                btn = tk.Button(branches_frame, text=branch, font=("Arial", 11), bg="#34495e", fg="white", width=18,
                command=lambda b=branch: show_images(b))
                btn.pack(pady=2)
            branches_frame.pack(pady=5)

    branches_visible = [False]


    def toggle_branch_buttons():
            if branches_visible[0]:
                branches_frame.pack_forget()
                search_frame.pack_forget()
                branches_visible[0] = False
            else:
                # Show search entry and button
                for widget in search_frame.winfo_children():
                    widget.destroy()
                search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=16)
                search_entry.pack(side="left", padx=2)
                def do_search():
                    term = search_var.get().strip().lower()
                    if term:
                        filtered = [b for b in branches if term in b.lower()]
                    else:
                        filtered = branches
                    show_branch_buttons(filtered)
                search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10), bg="#2980b9", fg="white", command=do_search)
                search_btn.pack(side="left", padx=2)
                search_frame.pack(pady=2)
                show_branch_buttons()
                branches_visible[0] = True

    btn_width = 18
    select_btn = tk.Button(sidebar, text="Select Branches", font=("Arial", 11), bg="#2980b9", fg="white", command=toggle_branch_buttons, width=btn_width)
    select_btn.pack(pady=5)

    add_user_btn = tk.Button(sidebar, text="Add User", font=("Arial", 11), bg="#27ae60", fg="white", command=lambda: open_add_user_popup_group2(admin), width=btn_width)
    add_user_btn.pack(pady=5)

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

    logout_btn = tk.Button(sidebar, text="Logout", font=("Arial", 11), bg="#c0392b", fg="white", command=logout, width=btn_width)
    logout_btn.pack(pady=5)
    tk.Label(
    sidebar, 
    text="Developed by Paolo Somido", 
    font=("Arial", 9), 
    fg="lightgray", 
    bg="#2c3e50"
).pack(side="bottom", pady=10)


    admin.mainloop()    