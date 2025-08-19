import urllib.request
import requests
import os
import tempfile
import subprocess
import json
import hashlib
from tkinter import messagebox, Tk
import msvcrt
import sys
import time
import ssl
from packaging import version
import logging

# Configuration
CONFIG = {
    'app_name': 'RMS',
    'current_version': '1.0.9',
    'github_user': 'food2g0',
    'github_repo': 'Centralized-Image-Uploader',
    'version_file': 'version.txt',
    'release_tag': 'V.1.0.1',
    'installer_name': 'installer.exe',
    'timeout': 30,
    'max_retries': 3,
    'debug_mode': True
}

# Setup logging
log_level = logging.DEBUG if CONFIG['debug_mode'] else logging.INFO
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdaterError(Exception):
    """Custom exception for updater errors"""
    pass

class SingleInstanceManager:
    def __init__(self, app_name):
        self.lock_file_path = os.path.join(os.environ.get('TEMP', '/tmp'), f'{app_name}.lock')
        self.lock_file = None
    
    def __enter__(self):
        try:
            self.lock_file = open(self.lock_file_path, 'w')
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            logger.info("✅ Single instance lock acquired")
            return self
        except (OSError, IOError) as e:
            logger.warning(f"Another instance is running: {e}")
            self._show_already_running_message()
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            try:
                self.lock_file.close()
                os.unlink(self.lock_file_path)
            except:
                pass
    
    def _show_already_running_message(self):
        root = Tk()
        root.withdraw()
        try:
            if os.path.exists("Logo.ico"):
                root.iconbitmap("Logo.ico")
        except:
            pass
        messagebox.showinfo("Already Running", f"{CONFIG['app_name']} is already running.")
        root.destroy()

class NetworkManager:
    @staticmethod
    def get_headers():
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/plain,application/json,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    @staticmethod
    def make_request_with_retry(url, max_retries=3, timeout=30):
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Attempting to connect to {url} (attempt {attempt + 1}/{max_retries})")
                
                response = requests.get(
                    url,
                    headers=NetworkManager.get_headers(),
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True  # Keep SSL verification enabled
                )
                response.raise_for_status()
                logger.info(f"✅ Request successful (Status: {response.status_code})")
                return response
                
            except requests.exceptions.SSLError as e:
                logger.error(f"🔒 SSL Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"SSL certificate verification failed. Please check your internet connection.")
            except requests.exceptions.Timeout as e:
                logger.error(f"⏰ Timeout on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"Connection timed out after {timeout} seconds")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"🌐 Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError("Cannot connect to update server. Check your internet connection.")
            except requests.exceptions.HTTPError as e:
                logger.error(f"📡 HTTP error on attempt {attempt + 1}: {e}")
                if e.response.status_code == 404:
                    raise UpdaterError("Update file not found on server")
                elif e.response.status_code == 403:
                    raise UpdaterError("Access denied to update server")
                else:
                    raise UpdaterError(f"Server error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"Unexpected error: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

class VersionManager:
    @staticmethod
    def get_version_url():
        return f"https://raw.githubusercontent.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/main/{CONFIG['version_file']}"
    
    @staticmethod
    def get_installer_url(version_tag=None):
        tag = version_tag or CONFIG['release_tag']
        return f"https://github.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/releases/download/{tag}/{CONFIG['installer_name']}"
    
    @staticmethod
    def parse_version(version_str):
        """Parse version string and clean it"""
        cleaned = version_str.strip().replace('v', '').replace('V', '')
        try:
            return version.parse(cleaned)
        except:
            # Fallback for simple version strings
            return cleaned
    
    @staticmethod
    def check_for_updates():
        """Check if updates are available"""
        try:
            logger.info("🔍 Checking for updates...")
            
            version_url = VersionManager.get_version_url()
            logger.info(f"📡 Version URL: {version_url}")
            
            response = NetworkManager.make_request_with_retry(
                version_url, 
                CONFIG['max_retries'], 
                CONFIG['timeout']
            )
            
            latest_version_str = response.text.strip()
            current_version_str = CONFIG['current_version']
            
            logger.info(f"📄 Latest version: '{latest_version_str}'")
            logger.info(f"💻 Current version: '{current_version_str}'")
            
            # Parse versions for comparison
            try:
                latest_ver = VersionManager.parse_version(latest_version_str)
                current_ver = VersionManager.parse_version(current_version_str)
                
                if isinstance(latest_ver, str) or isinstance(current_ver, str):
                    # Fallback to string comparison
                    update_available = latest_version_str != current_version_str
                else:
                    update_available = latest_ver > current_ver
                    
            except Exception as e:
                logger.warning(f"Version parsing failed, using string comparison: {e}")
                update_available = latest_version_str != current_version_str
            
            if update_available:
                logger.info("⬆️ Update available!")
                return latest_version_str
            else:
                logger.info("✅ App is up to date")
                return None
                
        except UpdaterError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error checking updates: {e}")
            raise UpdaterError(f"Failed to check for updates: {str(e)}")

class InstallerManager:
    @staticmethod
    def download_installer(installer_url, show_progress=True):
        """Download installer with progress feedback"""
        try:
            logger.info(f"⬇️ Downloading installer from: {installer_url}")
            
            response = NetworkManager.make_request_with_retry(
                installer_url,
                CONFIG['max_retries'],
                CONFIG['timeout']
            )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", prefix="updater_") as tmp_file:
                file_size = int(response.headers.get('content-length', 0))
                if file_size > 0:
                    logger.info(f"📁 Installer size: {file_size / (1024*1024):.2f} MB")
                
                downloaded = 0
                chunk_size = 8192
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if file_size > 0 and show_progress:
                            progress = (downloaded / file_size) * 100
                            if downloaded % (chunk_size * 100) == 0:  # Log every ~800KB
                                logger.info(f"📥 Download progress: {progress:.1f}%")
                
                installer_path = tmp_file.name
                logger.info(f"💾 Installer saved to: {installer_path}")
                
                # Verify file was downloaded
                if not os.path.exists(installer_path) or os.path.getsize(installer_path) == 0:
                    raise UpdaterError("Downloaded installer is empty or corrupted")
                
                return installer_path
                
        except UpdaterError:
            raise
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            raise UpdaterError(f"Failed to download installer: {str(e)}")
    
    @staticmethod
    def run_installer(installer_path):
        """Run the downloaded installer"""
        try:
            if not os.path.exists(installer_path):
                raise UpdaterError("Installer file not found")
            
            logger.info(f"🚀 Launching installer: {installer_path}")
            
            # Run installer with elevated privileges if possible
            if sys.platform == "win32":
                try:
                    # Request elevation for current user, not switch to Administrator
                    subprocess.run(['powershell', 'Start-Process', installer_path, '-Verb', 'RunAs'], check=False)
                except:
                    subprocess.Popen(installer_path, shell=True)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to run installer: {e}")
            raise UpdaterError(f"Failed to run installer: {str(e)}")

class UpdaterUI:
    @staticmethod
    def create_root():
        root = Tk()
        root.withdraw()
        try:
            if os.path.exists("Logo.ico"):
                root.iconbitmap("Logo.ico")
        except:
            pass
        return root
    
    @staticmethod
    def show_update_dialog(current_version, latest_version):
        """Show update confirmation dialog"""
        root = UpdaterUI.create_root()
        
        message = (
            f"🎉 A new version is available!\n\n"
            f"Current version: {current_version}\n"
            f"Latest version: {latest_version}\n\n"
            f"Would you like to download and install the update now?\n\n"
            f"The application will close during the update process."
        )
        
        result = messagebox.askyesno(
            "Update Available",
            message,
            icon='question'
        )
        
        root.destroy()
        return result
    
    @staticmethod
    def show_error(title, message):
        """Show error dialog"""
        root = UpdaterUI.create_root()
        messagebox.showerror(title, message)
        root.destroy()
    
    @staticmethod
    def show_info(title, message):
        """Show info dialog"""
        root = UpdaterUI.create_root()
        messagebox.showinfo(title, message)
        root.destroy()

def run_updater():
    """Main updater function"""
    logger.info("=" * 60)
    logger.info(f"🚀 {CONFIG['app_name']} UPDATER STARTING")
    logger.info("=" * 60)
    
    try:
        # Check for updates
        latest_version = VersionManager.check_for_updates()
        
        if not latest_version:
            logger.info("✅ No updates needed")
            return True
        
        # Show update dialog
        logger.info(f"📱 Showing update dialog for version {latest_version}")
        
        if not UpdaterUI.show_update_dialog(CONFIG['current_version'], latest_version):
            logger.info("👤 User declined update")
            return True
        
        logger.info("👤 User accepted update")
        
        # Download and run installer
        installer_url = VersionManager.get_installer_url()
        installer_path = InstallerManager.download_installer(installer_url)
        
        UpdaterUI.show_info(
            "Update Ready",
            "Update downloaded successfully!\nThe installer will now start.\n\nPlease follow the installation prompts."
        )
        
        InstallerManager.run_installer(installer_path)
        
        logger.info("🔄 Exiting for update...")
        return False  # Signal to exit app
        
    except UpdaterError as e:
        logger.error(f"⚠️ Update error: {e}")
        UpdaterUI.show_error("Update Failed", str(e))
        return True  # Continue with app
        
    except Exception as e:
        logger.error(f"❌ Unexpected updater error: {e}")
        if CONFIG['debug_mode']:
            import traceback
            traceback.print_exc()
        UpdaterUI.show_error("Update Error", f"An unexpected error occurred:\n{str(e)}")
        return True  # Continue with app

def launch_main_app():
    """Launch the main application"""
    logger.info("=" * 40)
    logger.info("🎯 LAUNCHING MAIN APPLICATION")
    logger.info("=" * 40)
    
    try:
        import login_gui
        
        if hasattr(login_gui, 'open_login_gui'):
            logger.info("📱 Calling login_gui.open_login_gui()")
            login_gui.open_login_gui()
        elif hasattr(login_gui, 'main'):
            logger.info("📱 Calling login_gui.main()")
            login_gui.main()
        else:
            raise Exception("No valid entry point found in login_gui.py")
            
    except Exception as e:
        logger.error(f"❌ Failed to launch main app: {e}")
        UpdaterUI.show_error("Application Error", f"Could not start {CONFIG['app_name']}:\n{str(e)}")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        # Ensure single instance
        with SingleInstanceManager(CONFIG['app_name']):
            # Run updater
            should_continue = run_updater()
            
            if should_continue:
                # Launch main app
                launch_main_app()
            else:
                # Exit for update
                sys.exit(0)
                
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        if CONFIG['debug_mode']:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()