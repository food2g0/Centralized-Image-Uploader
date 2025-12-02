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
import json
from datetime import datetime


def get_current_version():
    """Get current version from version file or fallback to hardcoded"""
    version_file = 'version.txt'

    try:
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                version_content = f.read().strip()
                if version_content:
                    print(f"Version read from {version_file}: {version_content}")
                    return version_content
    except Exception as e:
        print(f"Could not read version file: {e}")


    fallback_version = '1.1.2'
    print(f"Using fallback version: {fallback_version}")
    return fallback_version


# Configuration - can be overridden by updater.ini
CONFIG = {
    'app_name': 'RMS',
    'current_version': get_current_version(),
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
        'version.txt',
        'file_checksums.json',
        'last_update_check.txt',
        'user_settings.json',
        'config',
        'logs',
        'data'
    ]
}


def setup_logging():
    """Setup logging with file rotation"""
    log_file = CONFIG.get('log_file', 'updater.log')
    log_level = logging.INFO

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
    """Load configuration from file if exists, otherwise create and use defaults"""
    config_file = CONFIG.get('config_file', 'updater.ini')

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

                for key in CONFIG:
                    if key in section:
                        value = section[key]
                        if key in ['timeout', 'max_retries']:
                            CONFIG[key] = int(value)
                        elif key in ['use_latest_release']:
                            CONFIG[key] = value.lower() in ('true', '1', 'yes', 'on')
                        elif key == 'preserve_files':
                            CONFIG[key] = [f.strip() for f in value.split(',') if f.strip()]
                        else:
                            CONFIG[key] = value

                log_message('info', f"Configuration loaded from {config_file}")

                if 'current_version' in section:
                    CONFIG['current_version'] = section['current_version']
                    log_message('info', f"Version from config: {CONFIG['current_version']}")

            else:
                log_message('warning', f"No [updater] section in {config_file}, using defaults")
                save_default_config(config_file)

        except Exception as e:
            log_message('error', f"Error reading config file: {e}, using defaults")
            save_default_config(config_file)
    else:
        log_message('info', f"Config file {config_file} not found, creating defaults")
        save_default_config(config_file)


def save_default_config(config_file):
    """Save default configuration to file"""
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

        config_dir = os.path.dirname(config_file) if os.path.dirname(config_file) else '.'
        os.makedirs(config_dir, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            parser.write(f)

        log_message('info', f"Default configuration saved to {config_file}")

    except Exception as e:
        log_message('error', f"Error saving config file: {e}")


def update_config_version(new_version):
    """Update the version in the config file"""
    config_file = CONFIG.get('config_file', 'updater.ini')

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

        if os.path.exists(config_file):
            parser.read(config_file, encoding='utf-8')

        if 'updater' not in parser:
            parser['updater'] = {}

        parser['updater']['current_version'] = new_version
        CONFIG['current_version'] = new_version

        with open(config_file, 'w', encoding='utf-8') as f:
            parser.write(f)

        log_message('info', f"Updated config version to: {new_version}")
        return True

    except Exception as e:
        log_message('error', f"Failed to update config version: {e}")
        return False


setup_logging()
logger = logging.getLogger(__name__)
load_config()


class VersionTracker:
    """Manages version tracking and post-update fixes"""

    @staticmethod
    def save_pending_version(version):
        """Save version that we expect after update"""
        try:
            pending_file = 'pending_update.json'
            data = {
                'expected_version': version,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }

            with open(pending_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            logger.info(f"Saved pending version: {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to save pending version: {e}")
            return False

    @staticmethod
    def check_pending_update():
        """Check if we have a pending update to process"""
        try:
            pending_file = 'pending_update.json'
            if not os.path.exists(pending_file):
                return None

            with open(pending_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('status') == 'pending':
                logger.info(f"Found pending update to version: {data.get('expected_version')}")
                return data

            return None

        except Exception as e:
            logger.error(f"Error checking pending update: {e}")
            return None

    @staticmethod
    def complete_pending_update(expected_version):
        """Complete a pending update by fixing version if needed"""
        try:
            version_file = 'version.txt'
            current_version = None

            # Read current version file
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    current_version = f.read().strip()

            logger.info(f"Expected version: {expected_version}, Current version: {current_version}")

            # If version is wrong, fix it
            if current_version != expected_version:
                logger.warning(f"Version mismatch detected! Fixing {current_version} -> {expected_version}")

                # Force correct version
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(expected_version)

                # Update config too
                update_config_version(expected_version)

                logger.info(f"Version corrected to: {expected_version}")

            # Mark update as completed
            pending_file = 'pending_update.json'
            if os.path.exists(pending_file):
                with open(pending_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                data['status'] = 'completed'
                data['completed_at'] = datetime.now().isoformat()

                with open(pending_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)

                logger.info("Pending update marked as completed")

            return True

        except Exception as e:
            logger.error(f"Error completing pending update: {e}")
            return False

    @staticmethod
    def cleanup_completed_updates():
        """Clean up old completed update files"""
        try:
            pending_file = 'pending_update.json'
            if os.path.exists(pending_file):
                with open(pending_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # If update was completed more than 24 hours ago, clean it up
                if data.get('status') == 'completed' and data.get('completed_at'):
                    completed_time = datetime.fromisoformat(data['completed_at'])
                    if (datetime.now() - completed_time).total_seconds() > 86400:  # 24 hours
                        os.remove(pending_file)
                        logger.info("Cleaned up old completed update file")

        except Exception as e:
            logger.error(f"Error cleaning up updates: {e}")


class VersionFileManager:
    """Manages version file updates"""

    @staticmethod
    def update_version_file(new_version):
        """Update the version file with new version"""
        version_file = 'version.txt'
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(new_version)
            logger.info(f"Updated version file to: {new_version}")

            update_config_version(new_version)
            return True
        except Exception as e:
            logger.error(f"Failed to update version file: {e}")
            return False

    @staticmethod
    def create_version_file_if_missing():
        """Create version file if it doesn't exist"""
        version_file = 'version.txt'
        if not os.path.exists(version_file):
            current_version = CONFIG['current_version']
            try:
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(current_version)
                logger.info(f"Created initial version file with: {current_version}")
                return True
            except Exception as e:
                logger.error(f"Failed to create version file: {e}")
                return False
        return True

    @staticmethod
    def ensure_version_consistency():
        """Ensure version file and config file are consistent"""
        version_file = 'version.txt'
        config_version = CONFIG.get('current_version')

        file_version = None
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    file_version = f.read().strip()
            except Exception as e:
                logger.warning(f"Could not read version file: {e}")

        if file_version and file_version != config_version:
            logger.info(f"Version mismatch detected: file={file_version}, config={config_version}")
            CONFIG['current_version'] = file_version
            update_config_version(file_version)
            logger.info(f"Version synchronized to: {file_version}")
        elif not file_version:
            VersionFileManager.update_version_file(config_version)


class FilePreservationManager:
    """Manages preservation of important files during updates"""

    @staticmethod
    def get_preserve_list():
        """Get list of files/folders to preserve"""
        return CONFIG.get('preserve_files', [
            'updater.ini',
            'updater.log',
            'version.txt',
            'pending_update.json',
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
                        logger.info(f"Backed up file: {item}")
                    elif os.path.isdir(item):
                        import shutil
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        shutil.copytree(item, backup_path)
                        preserved_files.append(item)
                        logger.info(f"Backed up folder: {item}")

            logger.info(f"Backed up {len(preserved_files)} items to {backup_dir}")
            return backup_dir, preserved_files

        except Exception as e:
            logger.error(f"Error backing up files: {e}")
            return None, []


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
# 5. DO NOT overwrite version.txt - let the app handle it
"""

            instruction_file = "update_instructions.txt"
            with open(instruction_file, 'w', encoding='utf-8') as f:
                f.write(script_content)

            logger.info(f"Created preservation instructions: {instruction_file}")
            return instruction_file

        except Exception as e:
            logger.error(f"Error creating preservation script: {e}")
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
            logger.info("Single instance lock acquired")
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
                logger.info(f"Attempting to connect to {url} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(
                    url,
                    headers=NetworkManager.get_headers(),
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True
                )
                response.raise_for_status()
                logger.info(f"Request successful (Status: {response.status_code})")
                return response

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"SSL certificate verification failed. Please check your internet connection.")
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"Connection timed out after {timeout} seconds")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError("Cannot connect to update server. Check your internet connection.")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if e.response.status_code == 404:
                    raise UpdaterError("Update file not found on server")
                elif e.response.status_code == 403:
                    raise UpdaterError("Access denied to update server")
                else:
                    raise UpdaterError(f"Server error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise UpdaterError(f"Unexpected error: {str(e)}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)


class LatestReleaseManager:
    @staticmethod
    def get_latest_release_info():
        """Get information about the latest release from GitHub API"""
        api_url = f"https://api.github.com/repos/{CONFIG['github_user']}/{CONFIG['github_repo']}/releases/latest"

        try:
            logger.info("Fetching latest release information from GitHub...")
            logger.info(f"API URL: {api_url}")

            response = NetworkManager.make_request_with_retry(
                api_url,
                CONFIG['max_retries'],
                CONFIG['timeout']
            )

            release_data = response.json()

            latest_version = release_data['tag_name'].lstrip('vV')
            release_name = release_data.get('name', f"Release {latest_version}")
            release_notes = release_data.get('body', 'No release notes available.')
            published_at = release_data.get('published_at', '')

            installer_download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'] == CONFIG['installer_name']:
                    installer_download_url = asset['browser_download_url']
                    break

            if not installer_download_url:
                if release_data.get('assets'):
                    installer_download_url = release_data['assets'][0]['browser_download_url']
                else:
                    installer_download_url = f"https://github.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/releases/download/{release_data['tag_name']}/{CONFIG['installer_name']}"

            logger.info(f"Latest release: {latest_version}")
            logger.info(f"Release name: {release_name}")
            logger.info(f"Published: {published_at}")
            logger.info(f"Download URL: {installer_download_url}")

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
            logger.error(f"Failed to fetch latest release info: {e}")
            raise UpdaterError(f"Failed to get latest release information: {str(e)}")

    @staticmethod
    def compare_versions(current_version, latest_version):
        """Compare version strings to determine if update is needed"""
        try:
            current_clean = current_version.strip().replace('v', '').replace('V', '')
            latest_clean = latest_version.strip().replace('v', '').replace('V', '')

            logger.info(f"Comparing versions: '{current_clean}' vs '{latest_clean}'")

            try:
                current_ver = version.parse(current_clean)
                latest_ver = version.parse(latest_clean)

                if latest_ver > current_ver:
                    logger.info("Semantic version comparison: Update available")
                    return True
                elif latest_ver == current_ver:
                    logger.info("Semantic version comparison: Versions are equal")
                    return False
                else:
                    logger.info("Semantic version comparison: Current version is newer")
                    return False

            except Exception as e:
                logger.warning(f"Semantic version parsing failed, using string comparison: {e}")

                if latest_clean != current_clean:
                    logger.info("String comparison: Versions differ, assuming update available")
                    return True
                else:
                    logger.info("String comparison: Versions are identical")
                    return False

        except Exception as e:
            logger.error(f"Version comparison failed: {e}")
            return False


class VersionManager:
    @staticmethod
    def check_for_updates():
        """Check if updates are available using latest release"""
        try:
            logger.info("Checking for updates using latest release...")

            release_info = LatestReleaseManager.get_latest_release_info()

            current_version = CONFIG['current_version']
            latest_version = release_info['version']

            logger.info(f"Current version: {current_version}")
            logger.info(f"Latest version: {latest_version}")

            update_available = LatestReleaseManager.compare_versions(current_version, latest_version)

            if update_available:
                logger.info("Update available!")
                return {
                    'version': latest_version,
                    'download_url': release_info['download_url'],
                    'release_name': release_info['name'],
                    'release_notes': release_info['notes'],
                    'published_at': release_info['published_at'],
                    'tag_name': release_info['tag_name']
                }
            else:
                logger.info("App is up to date")
                return None

        except UpdaterError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking updates: {e}")
            raise UpdaterError(f"Failed to check for updates: {str(e)}")


class InstallerManager:
    @staticmethod
    def download_installer(installer_url, show_progress=True):
        """Download installer with progress feedback"""
        try:
            logger.info(f"Downloading installer from: {installer_url}")

            response = NetworkManager.make_request_with_retry(
                installer_url,
                CONFIG['max_retries'],
                CONFIG['timeout']
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", prefix="updater_") as tmp_file:
                file_size = int(response.headers.get('content-length', 0))
                if file_size > 0:
                    logger.info(f"Installer size: {file_size / (1024 * 1024):.2f} MB")

                downloaded = 0
                chunk_size = 8192

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        tmp_file.write(chunk)
                        downloaded += len(chunk)

                        if file_size > 0 and show_progress:
                            progress = (downloaded / file_size) * 100
                            if downloaded % (chunk_size * 100) == 0:
                                logger.info(f"Download progress: {progress:.1f}%")

                installer_path = tmp_file.name
                logger.info(f"Installer saved to: {installer_path}")

                if not os.path.exists(installer_path) or os.path.getsize(installer_path) == 0:
                    raise UpdaterError("Downloaded installer is empty or corrupted")

                return installer_path

        except UpdaterError:
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise UpdaterError(f"Failed to download installer: {str(e)}")

    @staticmethod
    def run_installer(installer_path):
        """Run the downloaded installer"""
        try:
            if not os.path.exists(installer_path):
                raise UpdaterError("Installer file not found")

            logger.info(f"Launching installer: {installer_path}")

            if sys.platform == "win32":
                try:
                    subprocess.run(['powershell', 'Start-Process', installer_path, '-Verb', 'RunAs'], check=False)
                except Exception:
                    subprocess.Popen(installer_path, shell=True)

            return True

        except Exception as e:
            logger.error(f"Failed to run installer: {e}")
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

        message = (
            f"A new version is available!\n\n"
            f"Current version: {CONFIG['current_version']}\n"
            f"Latest version: {update_info['version']}\n"
            f"Release: {update_info['release_name']}\n\n"
        )

        if update_info.get('published_at'):
            try:
                from datetime import datetime
                pub_date = datetime.fromisoformat(update_info['published_at'].replace('Z', '+00:00'))
                message += f"Published: {pub_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
            except Exception:
                pass

        if update_info.get('release_notes'):
            notes = update_info['release_notes']
            if len(notes) > 200:
                notes = notes[:200] + "..."
            message += f"\nRelease Notes:\n{notes}\n"

        message += (
            f"\nWould you like to download and install the update now?\n\n"
            f"The application will close during the update process.\n"
            f"Your settings and data will be preserved."
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
    """Main updater function using latest release with version tracking"""
    logger.info("=" * 60)
    logger.info(f"{CONFIG['app_name']} LATEST RELEASE UPDATER STARTING")
    logger.info("=" * 60)

    try:
        VersionFileManager.create_version_file_if_missing()
        VersionFileManager.ensure_version_consistency()

        update_info = VersionManager.check_for_updates()

        if not update_info:
            logger.info("No updates needed")
            return True

        UpdateInstructions.create_preservation_script()
        backup_dir, preserved_files = FilePreservationManager.backup_important_files()

        logger.info(f"Showing update dialog for latest release: {update_info['version']}")

        if not UpdaterUI.show_update_dialog(update_info):
            logger.info("User declined update")
            return True

        logger.info("User accepted update")

        # Save the expected version BEFORE running installer
        VersionTracker.save_pending_version(update_info['version'])

        installer_path = InstallerManager.download_installer(update_info['download_url'])

        UpdaterUI.show_info(
            "Update Ready",
            f"Update to version {update_info['version']} downloaded successfully!\n"
            f"The installer will now start.\n\n"
            f"Your settings and logs will be preserved.\n"
            f"{len(preserved_files) if preserved_files else 0} files backed up.\n"
            f"Version will be verified after installation.\n\n"
            f"Please follow the installation prompts."
        )

        InstallerManager.run_installer(installer_path)

        logger.info("Exiting for update...")
        return False

    except UpdaterError as e:
        logger.error(f"Update error: {e}")
        UpdaterUI.show_error("Update Failed", str(e))
        return True

    except Exception as e:
        logger.error(f"Unexpected updater error: {e}")
        UpdaterUI.show_error("Update Error", f"An unexpected error occurred:\n{str(e)}")
        return True


def launch_main_app():
    """Launch the main application"""
    logger.info("=" * 40)
    logger.info("LAUNCHING MAIN APPLICATION")
    logger.info("=" * 40)

    try:
        import login_gui

        if hasattr(login_gui, 'open_login_gui'):
            logger.info("Calling login_gui.open_login_gui()")
            login_gui.open_login_gui()
        elif hasattr(login_gui, 'main'):
            logger.info("Calling login_gui.main()")
            login_gui.main()
        else:
            raise Exception("No valid entry point found in login_gui.py")

    except Exception as e:
        logger.error(f"Failed to launch main app: {e}")
        UpdaterUI.show_error("Application Error", f"Could not start {CONFIG['app_name']}:\n{str(e)}")
        sys.exit(1)


def initialize_app_files():
    """Initialize application files on first run or after update"""
    logger.info("Initializing application files...")

    try:
        # Check for pending updates first
        pending_update = VersionTracker.check_pending_update()
        if pending_update:
            expected_version = pending_update.get('expected_version')
            logger.info(f"Processing pending update to version: {expected_version}")

            # Complete the pending update (this will fix version.txt if needed)
            VersionTracker.complete_pending_update(expected_version)

            # Reload CONFIG with corrected version
            CONFIG['current_version'] = expected_version

            logger.info(f"Pending update completed successfully to version: {expected_version}")

        # Ensure version file exists
        VersionFileManager.create_version_file_if_missing()

        # Ensure config file exists with current settings
        config_file = CONFIG.get('config_file', 'updater.ini')
        if not os.path.exists(config_file):
            save_default_config(config_file)

        # Ensure version consistency between files
        VersionFileManager.ensure_version_consistency()

        # Clean up old completed updates
        VersionTracker.cleanup_completed_updates()

        logger.info("Application files initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application files: {e}")


def debug_version_status():
    """Debug function to log current version status"""
    logger.info("=" * 50)
    logger.info("VERSION STATUS DEBUG")
    logger.info("=" * 50)

    # Check version.txt
    version_file = 'version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            file_version = f.read().strip()
        logger.info(f"version.txt contains: '{file_version}'")
    else:
        logger.info("version.txt does not exist")

    # Check CONFIG version
    logger.info(f"CONFIG current_version: '{CONFIG['current_version']}'")

    # Check config file
    config_file = CONFIG.get('config_file', 'updater.ini')
    if os.path.exists(config_file):
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file, encoding='utf-8')
            if 'updater' in parser and 'current_version' in parser['updater']:
                config_version = parser['updater']['current_version']
                logger.info(f"updater.ini contains version: '{config_version}'")
        except Exception as e:
            logger.error(f"Error reading config: {e}")
    else:
        logger.info("updater.ini does not exist")

    # Check pending updates
    pending_update = VersionTracker.check_pending_update()
    if pending_update:
        logger.info(f"Pending update found: {pending_update}")
    else:
        logger.info("No pending updates")

    logger.info("=" * 50)


def main():
    """Main entry point"""
    try:
        with SingleInstanceManager(CONFIG['app_name']):
            # Debug version status for troubleshooting
            debug_version_status()

            # Initialize application files first (this handles pending updates)
            initialize_app_files()

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
        logger.error(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()