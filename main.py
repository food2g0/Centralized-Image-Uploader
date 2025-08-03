import urllib.request
import requests
import os
import tempfile
import subprocess
from tkinter import messagebox, Tk

# 🔁 Use GitHub version and installer links
VERSION_URL = "https://raw.githubusercontent.com/food2g0/Centralized-Image-Uploader/main/version.txt?cachebuster=1"
INSTALLER_URL = "https://github.com/food2g0/Centralized-Image-Uploader/releases/download/V.1.0.1/installer.exe"

APP_VERSION = "1.0.7"  

def get_current_version():
    version_file = "version.txt"
    if not os.path.exists(version_file):
        with open(version_file, "w") as f:
            f.write(APP_VERSION)
        return APP_VERSION
    try:
        with open(version_file) as f:
            return f.read().strip()
    except:
        return APP_VERSION

def check_for_updates():
    try:
        print("🔍 Checking for updates...")
        with urllib.request.urlopen(VERSION_URL) as response:
            latest_version = response.read().decode('utf-8').strip()
        current_version = get_current_version()
        print(f"📄 Latest version on server: {latest_version}")
        print(f"💻 Current version: {current_version}")
        if latest_version != current_version:
            print("⬆️ Update available!")
            return latest_version
        else:
            print("✅ App is up to date.")
    except Exception as e:
        print("❌ Could not check for updates:", e)
    return None

def download_and_run_installer():
    try:
        print("⬇️ Downloading installer.exe from GitHub release...")
        with requests.get(INSTALLER_URL, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                installer_path = tmp_file.name

        print(f"🚀 Running installer: {installer_path}")
        subprocess.Popen(installer_path, shell=True)  # Launch installer
        return True
    except Exception as e:
        print("❌ Failed to download or run installer:", e)
        return False


def run_updater():
    latest = check_for_updates()
    if latest:
        root = Tk()
        root.withdraw()
        answer = messagebox.askyesno("Update Available", f"A new version ({latest}) is available.\nDo you want to install it now?")
        if answer:
            if download_and_run_installer():
                messagebox.showinfo("Installer Launched", "Installer is running.\nPlease follow the prompts to update.")
                root.destroy()
                os._exit(0)  
            else:
                messagebox.showerror("Update Failed", "Failed to download or launch the installer.")
                root.destroy()
                os._exit(1)  
        root.destroy()
# 🟢 Run updater first
run_updater()

# 🟢 Then continue to launch app
try:
    import login_gui
    if hasattr(login_gui, 'open_login_gui'):
        login_gui.open_login_gui()
    elif hasattr(login_gui, 'main'):
        login_gui.main()
    else:
        raise Exception("No valid entry point found in login_gui.py")
except Exception as err:
    root = Tk()
    root.withdraw()
    messagebox.showerror("Error", f"Could not open login: {err}")
    root.destroy()
