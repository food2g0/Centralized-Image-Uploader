import urllib.request
import requests
import os
import tempfile
import subprocess
from tkinter import messagebox, Tk
import msvcrt
import sys
import time
import ssl

lock_file_path = os.path.join(os.environ['TEMP'], 'RMS.lock')

VERSION_URL = "https://raw.githubusercontent.com/food2g0/Centralized-Image-Uploader/main/version.txt"
INSTALLER_URL = "https://github.com/food2g0/Centralized-Image-Uploader/releases/download/V.1.0.1/installer.exe"

APP_VERSION = "1.0.9"

def check_single_instance():
    try:
        global lock_file
        lock_file = open(lock_file_path, 'w')
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        print("✅ Single instance check passed")
    except OSError:
        root = Tk()
        root.withdraw()
        messagebox.showinfo("Already Running", "The application is already running.")
        sys.exit()

check_single_instance()

def check_for_updates():
    try:
        print("🔍 Checking for updates...")
        print(f"📡 Connecting to: {VERSION_URL}")
        
        # Create SSL context that doesn't verify certificates (for debugging)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Create request with headers
        req = urllib.request.Request(VERSION_URL, headers=headers)
        
        # Set timeout
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            print(f"📊 HTTP Status: {response.getcode()}")
            print(f"📋 Response headers: {dict(response.headers)}")
            
            latest_version = response.read().decode('utf-8').strip()
            print(f"📄 Raw response: '{latest_version}'")
            
        print(f"📄 Latest version on server: '{latest_version}'")
        print(f"💻 Current version: '{APP_VERSION}'")
        
        # Clean versions for comparison (remove extra whitespace/newlines)
        latest_clean = latest_version.strip()
        current_clean = APP_VERSION.strip()
        
        print(f"🔍 Comparing: '{latest_clean}' vs '{current_clean}'")
        
        if latest_clean != current_clean:
            print("⬆️ Update available!")
            return latest_clean
        else:
            print("✅ App is up to date.")
            return None
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print(f"🌐 URL: {VERSION_URL}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        print("🌐 Check your internet connection")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during update check: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_url_manually():
    """Test URL accessibility manually"""
    try:
        print("🧪 Testing URL accessibility...")
        
        # Test with requests library
        response = requests.get(VERSION_URL, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"✅ Requests method - Status: {response.status_code}")
        print(f"📄 Content: '{response.text.strip()}'")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Requests method failed: {e}")

def download_and_run_installer():
    try:
        print("⬇️ Downloading installer.exe from GitHub release...")
        print(f"🔗 Download URL: {INSTALLER_URL}")
        
        # Use requests with better error handling
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with requests.get(INSTALLER_URL, stream=True, headers=headers, timeout=30) as response:
            response.raise_for_status()
            print(f"📊 Download status: {response.status_code}")
            
            # Get file size if available
            file_size = response.headers.get('content-length')
            if file_size:
                print(f"📁 File size: {int(file_size) / (1024*1024):.2f} MB")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp_file:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                    downloaded += len(chunk)
                installer_path = tmp_file.name
                
                print(f"💾 Downloaded: {downloaded / (1024*1024):.2f} MB")

        print(f"🚀 Running installer: {installer_path}")
        subprocess.Popen(installer_path, shell=True)
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to download or run installer: {e}")
        return False

def run_updater():
    print("=" * 50)
    print("🚀 UPDATE CHECKER STARTING")
    print("=" * 50)
    
    # Test URL first
    test_url_manually()
    
    print("\n" + "=" * 30)
    print("🔍 CHECKING FOR UPDATES")
    print("=" * 30)
    
    latest = check_for_updates()
    
    if latest:
        print(f"\n✨ UPDATE FOUND: {latest}")
        root = Tk()
        root.withdraw()
        
        # Add app icon if it exists
        try:
            if os.path.exists("Logo.ico"):
                root.iconbitmap("Logo.ico")
        except:
            pass
            
        answer = messagebox.askyesno(
            "Update Available", 
            f"A new version ({latest}) is available.\nCurrent version: {APP_VERSION}\n\nDo you want to install it now?"
        )
        
        if answer:
            print("👤 User chose to update")
            if download_and_run_installer():
                messagebox.showinfo("Installer Launched", "Installer is running.\nPlease follow the prompts to update.")
                try:
                    root.destroy()
                except:
                    pass
                print("🔄 Exiting for update...")
                os._exit(0)
            else:
                messagebox.showerror("Update Failed", "Failed to download or launch the installer.")
                try:
                    root.destroy()
                except:
                    pass
                print("❌ Update failed, exiting...")
                os._exit(1)
        else:
            print("👤 User chose to skip update")
            
        try:
            root.destroy()
        except:
            pass
    else:
        print("✅ No update needed")

# Run the updater
run_updater()

# ✅ Launch main app if no update or after check
print("\n" + "=" * 30)
print("🎯 LAUNCHING MAIN APP")
print("=" * 30)

try:
    import login_gui
    if hasattr(login_gui, 'open_login_gui'):
        print("📱 Calling login_gui.open_login_gui()")
        login_gui.open_login_gui()
    elif hasattr(login_gui, 'main'):
        print("📱 Calling login_gui.main()")
        login_gui.main()
    else:
        raise Exception("No valid entry point found in login_gui.py")
except Exception as err:
    print(f"❌ Error launching main app: {err}")
    root = Tk()
    root.withdraw()
    try:
        root.iconbitmap("Logo.ico")
    except:
        pass
    messagebox.showerror("Error", f"Could not open login: {err}")
    root.destroy()