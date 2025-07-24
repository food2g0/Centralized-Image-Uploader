
try:
    import login_gui
    if hasattr(login_gui, 'open_login_gui'):
        login_gui.open_login_gui()
    elif hasattr(login_gui, 'main'):
        login_gui.main()
    else:
        raise Exception("No valid entry point found in login_gui.py")
except Exception as err:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"Could not open login: {err}")
    root.destroy()
