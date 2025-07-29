import urllib.request
import requests
import zipfile
import os
import shutil
import tempfile
from tkinter import messagebox, Tk

VERSION_URL = "https://firebasestorage.googleapis.com/v0/b/records-management-faffa.firebasestorage.app/o/version.txt?alt=media&token=eea72d84-6649-42ba-9ccb-0340e8ad5aeb"
UPDATE_ZIP_URL = "https://firebasestorage.googleapis.com/v0/b/records-management-faffa.firebasestorage.app/o/update.zip?alt=media&token=cdd772a1-e28c-4fc7-b1e6-bad2427bda53"

def get_current_version():
    try:
        with open("version.txt") as f:
            return f.read().strip()
    except:
        return "0.0.0"

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

def download_and_apply_update():
    try:
        print("⬇️ Downloading update.zip from Firebase...")
        response = requests.get(UPDATE_ZIP_URL, stream=True)
        with open("update.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("✅ Downloaded update.zip")

        print("📦 Extracting files...")
        with tempfile.TemporaryDirectory() as tmpdirname:
            with zipfile.ZipFile("update.zip", "r") as zip_ref:
                zip_ref.extractall(tmpdirname)

            # Copy files from temp to current dir
            for item in os.listdir(tmpdirname):
                src = os.path.join(tmpdirname, item)
                dst = os.path.join(".", item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        os.remove("update.zip")
        print("✅ Update applied successfully!")
        return True
    except Exception as e:
        print("❌ Update failed:", e)
        return False

def run_updater():
    latest = check_for_updates()
    if latest:
        root = Tk()
        root.withdraw()
        answer = messagebox.askyesno("Update Available", f"A new version ({latest}) is available.\nDo you want to update now?")
        if answer:
            if download_and_apply_update():
                messagebox.showinfo("Update Complete", "App has been updated.\nPlease restart the application.")
                root.destroy()
                import sys
                sys.exit()
            else:
                messagebox.showerror("Update Failed", "Something went wrong during the update.")
                root.destroy()
                import sys
                sys.exit()
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
