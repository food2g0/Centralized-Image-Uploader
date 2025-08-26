import urllib.request
import requests
import os
import tempfile
import subprocess
from tkinter import messagebox, Tk
import msvcrt
import sys
import time
from packaging import version
import configparser
import logging

# Configuration - can be overridden by updater.ini
CONFIG = {
    'app_name': 'RMS',
    'current_version': '1.1.0',
    'github_user': 'food2g0',
    'github_repo': 'Centralized-Image-Uploader',
    'installer_name': 'installer.exe',
    'timeout': 30,
    'max_retries': 3,
    'use_latest_release': True,
    'config_file': 'updater.ini',
    'log_file': 'updater.log',
    'preserve_files': [
        'updater.ini',
        'updater.log',
        'file_checksums.json',
        'last_update_check.txt',
        'user_settings.json',
        'config',
        'logs',
        'data'
    ]  # Files/folders to preserve during updates
}


# Setup logging
def setup_logging():
    """Setup logging with file rotation"""
    log_file = CONFIG.get('log_file', 'updater.log')
    log_level = logging.INFO

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else '.'
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )


def load_config():
    """Load configuration from file if exists, otherwise use defaults"""
    config_file = CONFIG.get('config_file', 'updater.ini')

    # Get logger if available, otherwise use print
    try:
        current_logger = logging.getLogger(__name__)
    except:
        current_logger = None

    def log_message(level, message):
        if current_logger:
            getattr(current_logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")

    if os.path.exists(config_file):
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file, encoding='utf-8')

            if 'updater' in parser:
                section = parser['updater']

                # Update CONFIG with values from file
                for key in CONFIG:
                    if key in section:
                        value = section[key]
                        # Convert string values to appropriate types
                        if key in ['timeout', 'max_retries']:
                            CONFIG[key] = int(value)
                        elif key in ['use_latest_release']:
                            CONFIG[key] = value.lower() in ('true', '1', 'yes', 'on')
                        elif key == 'preserve_files':
                            CONFIG[key] = [f.strip() for f in value.split(',') if f.strip()]
                        else:
                            CONFIG[key] = value

                log_message('info', f"✅ Configuration loaded from {config_file}")
            else:
                log_message('warning', f"⚠️ No [updater] section in {config_file}, using defaults")

        except Exception as e:
            log_message('error', f"❌ Error reading config file: {e}, using defaults")
    else:
        log_message('info', f"ℹ️ Config file {config_file} not found, using defaults")
        # Create default config file
        save_default_config(config_file)


def save_default_config(config_file):
    """Save default configuration to file"""
    # Get logger if available, otherwise use print
    try:
        current_logger = logging.getLogger(__name__)
    except:
        current_logger = None

    def log_message(level, message):
        if current_logger:
            getattr(current_logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")

    try:
        parser = configparser.ConfigParser()
        parser['updater'] = {
            'app_name': CONFIG['app_name'],
            'current_version': CONFIG['current_version'],
            'github_user': CONFIG['github_user'],
            'github_repo': CONFIG['github_repo'],
            'installer_name': CONFIG['installer_name'],
            'timeout': str(CONFIG['timeout']),
            'max_retries': str(CONFIG['max_retries']),
            'use_latest_release': str(CONFIG['use_latest_release']).lower(),
            'log_file': CONFIG['log_file'],
            'preserve_files': ', '.join(CONFIG['preserve_files'])
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            parser.write(f)

        log_message('info', f"✅ Default configuration saved to {config_file}")

    except Exception as e:
        log_message('error', f"❌ Error saving config file: {e}")


# Setup logging first, then load configuration
setup_logging()
logger = logging.getLogger(__name__)
load_config()


class FilePreservationManager:
    """Manages preservation of important files during updates"""

    @staticmethod
    def get_preserve_list():
        """Get list of files/folders to preserve"""
        return CONFIG.get('preserve_files', [
            'updater.ini',
            'updater.log',
            'config',
            'logs',
            'data'
        ])

    @staticmethod
    def backup_important_files():
        """Create backup of important files before update"""
        try:
            backup_dir = os.path.join(tempfile.gettempdir(), f"{CONFIG['app_name']}_backup")
            os.makedirs(backup_dir, exist_ok=True)

            preserved_files = []
            for item in FilePreservationManager.get_preserve_list():
                if os.path.exists(item):
                    backup_path = os.path.join(backup_dir, os.path.basename(item))

                    if os.path.isfile(item):
                        import shutil
                        shutil.copy2(item, backup_path)
                        preserved_files.append(item)
                        logger.info(f"📋 Backed up file: {item}")
                    elif os.path.isdir(item):
                        import shutil
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        shutil.copytree(item, backup_path)
                        preserved_files.append(item)
                        logger.info(f"📋 Backed up folder: {item}")

            logger.info(f"✅ Backed up {len(preserved_files)} items to {backup_dir}")
            return backup_dir, preserved_files

        except Exception as e:
            logger.error(f"❌ Error backing up files: {e}")
            return None, []

    @staticmethod
    def restore_important_files(backup_dir):
        """Restore important files after update"""
        if not backup_dir or not os.path.exists(backup_dir):
            logger.warning("⚠️ No backup directory found, skipping restore")
            return

        try:
            restored_files = []
            for item in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, item)
                restore_path = item

                if os.path.isfile(backup_path):
                    import shutil
                    shutil.copy2(backup_path, restore_path)
                    restored_files.append(item)
                    logger.info(f"📋 Restored file: {item}")
                elif os.path.isdir(backup_path):
                    import shutil
                    if os.path.exists(restore_path):
                        shutil.rmtree(restore_path)
                    shutil.copytree(backup_path, restore_path)
                    restored_files.append(item)
                    logger.info(f"📋 Restored folder: {item}")

            logger.info(f"✅ Restored {len(restored_files)} items")

            # Clean up backup
            import shutil
            shutil.rmtree(backup_dir)
            logger.info("🧹 Cleaned up backup directory")

        except Exception as e:
            logger.error(f"❌ Error restoring files: {e}")


class UpdateInstructions:
    """Creates instructions for installer to preserve files"""

    @staticmethod
    def create_preservation_script():
        """Create script with preservation instructions for installer"""
        try:
            script_content = f"""
# {CONFIG['app_name']} Update Preservation Instructions
# This file tells the installer which files to preserve

[PRESERVE_FILES]
"""
            for item in FilePreservationManager.get_preserve_list():
                script_content += f"{item}\n"

            script_content += f"""
[SETTINGS]
app_name={CONFIG['app_name']}
preserve_user_data=true
backup_before_install=true

[INSTRUCTIONS]
# Instructions for installer:
# 1. Backup files listed in PRESERVE_FILES section
# 2. Install new version
# 3. Restore backed up files
# 4. Keep existing configuration files
"""

            instruction_file = "update_instructions.txt"
            with open(instruction_file, 'w', encoding='utf-8') as f:
                f.write(script_content)

            logger.info(f"📋 Created preservation instructions: {instruction_file}")
            return instruction_file

        except Exception as e:
            logger.error(f"❌ Error creating preservation script: {e}")
            return None


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
            except Exception:
                pass

    def _show_already_running_message(self):
        root = Tk()
        root.withdraw()
        try:
            if os.path.exists("Logo.ico"):
                root.iconbitmap("Logo.ico")
        except Exception:
            pass
        messagebox.showinfo("Already Running", f"{CONFIG['app_name']} is already running.")
        root.destroy()


class NetworkManager:
    @staticmethod
    def get_headers():
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/vnd.github.v3+json',
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
                    verify=True
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


class LatestReleaseManager:
    @staticmethod
    def get_latest_release_info():
        """Get information about the latest release from GitHub API"""
        api_url = f"https://api.github.com/repos/{CONFIG['github_user']}/{CONFIG['github_repo']}/releases/latest"

        try:
            logger.info("🔍 Fetching latest release information from GitHub...")
            logger.info(f"📡 API URL: {api_url}")

            response = NetworkManager.make_request_with_retry(
                api_url,
                CONFIG['max_retries'],
                CONFIG['timeout']
            )

            release_data = response.json()

            # Extract relevant information
            latest_version = release_data['tag_name'].lstrip('vV')  # Remove v or V prefix
            release_name = release_data.get('name', f"Release {latest_version}")
            release_notes = release_data.get('body', 'No release notes available.')
            published_at = release_data.get('published_at', '')

            # Find the installer asset
            installer_download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'] == CONFIG['installer_name']:
                    installer_download_url = asset['browser_download_url']
                    break

            if not installer_download_url:
                # Fallback: use the first asset or construct URL
                if release_data.get('assets'):
                    installer_download_url = release_data['assets'][0]['browser_download_url']
                else:
                    # Construct URL based on tag
                    installer_download_url = f"https://github.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/releases/download/{release_data['tag_name']}/{CONFIG['installer_name']}"

            logger.info(f"📄 Latest release: {latest_version}")
            logger.info(f"📝 Release name: {release_name}")
            logger.info(f"📅 Published: {published_at}")
            logger.info(f"⬇️ Download URL: {installer_download_url}")

            return {
                'version': latest_version,
                'name': release_name,
                'notes': release_notes,
                'published_at': published_at,
                'download_url': installer_download_url,
                'tag_name': release_data['tag_name']
            }

        except UpdaterError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to fetch latest release info: {e}")
            raise UpdaterError(f"Failed to get latest release information: {str(e)}")

    @staticmethod
    def compare_versions(current_version, latest_version):
        """Compare version strings to determine if update is needed"""
        try:
            # Clean version strings
            current_clean = current_version.strip().replace('v', '').replace('V', '')
            latest_clean = latest_version.strip().replace('v', '').replace('V', '')

            logger.info(f"🔍 Comparing versions: '{current_clean}' vs '{latest_clean}'")

            # Try semantic version comparison first
            try:
                current_ver = version.parse(current_clean)
                latest_ver = version.parse(latest_clean)

                if latest_ver > current_ver:
                    logger.info("⬆️ Semantic version comparison: Update available")
                    return True
                elif latest_ver == current_ver:
                    logger.info("✅ Semantic version comparison: Versions are equal")
                    return False
                else:
                    logger.info("✅ Semantic version comparison: Current version is newer")
                    return False

            except Exception as e:
                logger.warning(f"Semantic version parsing failed, using string comparison: {e}")

                # Fallback to string comparison
                if latest_clean != current_clean:
                    logger.info("⬆️ String comparison: Versions differ, assuming update available")
                    return True
                else:
                    logger.info("✅ String comparison: Versions are identical")
                    return False

        except Exception as e:
            logger.error(f"❌ Version comparison failed: {e}")
            # If comparison fails, assume no update to be safe
            return False


class VersionManager:
    @staticmethod
    def check_for_updates():
        """Check if updates are available using latest release"""
        try:
            logger.info("🔍 Checking for updates using latest release...")

            # Get latest release information
            release_info = LatestReleaseManager.get_latest_release_info()

            current_version = CONFIG['current_version']
            latest_version = release_info['version']

            logger.info(f"💻 Current version: {current_version}")
            logger.info(f"📄 Latest version: {latest_version}")

            # Compare versions
            update_available = LatestReleaseManager.compare_versions(current_version, latest_version)

            if update_available:
                logger.info("⬆️ Update available!")
                return {
                    'version': latest_version,
                    'download_url': release_info['download_url'],
                    'release_name': release_info['name'],
                    'release_notes': release_info['notes'],
                    'published_at': release_info['published_at'],
                    'tag_name': release_info['tag_name']
                }
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
                    logger.info(f"📁 Installer size: {file_size / (1024 * 1024):.2f} MB")

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
                    subprocess.run(['powershell', 'Start-Process', installer_path, '-Verb', 'RunAs'], check=False)
                except Exception:
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
        except Exception:
            pass
        return root

    @staticmethod
    def show_update_dialog(update_info):
        """Show update confirmation dialog with release information"""
        root = UpdaterUI.create_root()

        # Create a more detailed message with release info
        message = (
            f"🎉 A new version is available!\n\n"
            f"Current version: {CONFIG['current_version']}\n"
            f"Latest version: {update_info['version']}\n"
            f"Release: {update_info['release_name']}\n\n"
        )

        # Add release date if available
        if update_info.get('published_at'):
            try:
                from datetime import datetime
                pub_date = datetime.fromisoformat(update_info['published_at'].replace('Z', '+00:00'))
                message += f"Published: {pub_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
            except Exception:
                pass

        # Add truncated release notes if available
        if update_info.get('release_notes'):
            notes = update_info['release_notes']
            if len(notes) > 200:
                notes = notes[:200] + "..."
            message += f"\nRelease Notes:\n{notes}\n"

        message += (
            f"\nWould you like to download and install the update now?\n\n"
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
    """Main updater function using latest release"""
    logger.info("=" * 60)
    logger.info(f"🚀 {CONFIG['app_name']} LATEST RELEASE UPDATER STARTING")
    logger.info("=" * 60)

    try:
        # Check for updates using latest release
        update_info = VersionManager.check_for_updates()

        if not update_info:
            logger.info("✅ No updates needed")
            return True

        # Create preservation instructions
        UpdateInstructions.create_preservation_script()

        # Backup important files before showing update dialog
        backup_dir, preserved_files = FilePreservationManager.backup_important_files()

        # Show update dialog
        logger.info(f"📱 Showing update dialog for latest release: {update_info['version']}")

        if not UpdaterUI.show_update_dialog(update_info):
            logger.info("👤 User declined update")
            return True

        logger.info("👤 User accepted update")

        # Download and run installer
        installer_path = InstallerManager.download_installer(update_info['download_url'])

        UpdaterUI.show_info(
            "Update Ready",
            f"Update to version {update_info['version']} downloaded successfully!\n"
            f"The installer will now start.\n\n"
            f"✅ Your settings and logs will be preserved.\n"
            f"📋 {len(preserved_files) if preserved_files else 0} files backed up.\n\n"
            f"Please follow the installation prompts."
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
        sys.exit(1)


if __name__ == "__main__":
    main()