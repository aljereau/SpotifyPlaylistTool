"""
Update checker for Spotify Downloader UI.

This module handles checking for updates against a remote source
and determining if an update is available.
"""

import os
import sys
import json
import logging
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import urllib.request
import urllib.error

from spotify_downloader_ui.packaging.common import APP_VERSION

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/aljereau/Spotify-Downloader/main/updates.json"
LAST_CHECK_FILE = "last_update_check.json"

class VersionInfo:
    """Class to represent version information."""
    
    def __init__(self, version_str: str):
        """
        Initialize from a version string like "1.2.3".
        
        Args:
            version_str: Version string in the format "X.Y.Z[-suffix]"
        """
        self.version_str = version_str
        
        # Split into parts
        parts = version_str.split('-', 1)
        version_parts = parts[0].split('.')
        
        # Convert to integers (padding with 0 if necessary)
        padding = [0] * (3 - len(version_parts))
        self.major, self.minor, self.patch = [int(p) for p in version_parts] + padding
        
        # Extract suffix if present
        self.suffix = parts[1] if len(parts) > 1 else ""
        
        # Channel (stable, beta, alpha, etc.)
        self.channel = "stable"
        if self.suffix:
            if "beta" in self.suffix:
                self.channel = "beta"
            elif "alpha" in self.suffix:
                self.channel = "alpha"
            elif "dev" in self.suffix:
                self.channel = "dev"
    
    def __str__(self) -> str:
        """Return the version string."""
        return self.version_str
    
    def __eq__(self, other) -> bool:
        """Check if versions are equal."""
        if not isinstance(other, VersionInfo):
            return False
        
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch and 
                self.suffix == other.suffix)
    
    def __lt__(self, other) -> bool:
        """Check if this version is less than the other version."""
        if not isinstance(other, VersionInfo):
            return NotImplemented
        
        # Compare major, minor, patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # If everything else is equal, versions with no suffix are "greater"
        # than versions with a suffix (e.g., 1.0.0 > 1.0.0-beta)
        if not self.suffix and other.suffix:
            return False
        if self.suffix and not other.suffix:
            return True
        
        # If both have suffixes, compare them
        return self.suffix < other.suffix

class UpdateInfo:
    """Class to represent update information."""
    
    def __init__(self, 
                 version: str, 
                 url: str, 
                 date: str,
                 channel: str = "stable",
                 min_version: Optional[str] = None,
                 requires_restart: bool = True,
                 changelog: Optional[List[str]] = None,
                 platforms: Optional[List[str]] = None,
                 size: Optional[int] = None):
        """
        Initialize update information.
        
        Args:
            version: Version string
            url: URL to download the update
            date: Release date string
            channel: Update channel (stable, beta, etc.)
            min_version: Minimum version required to update from
            requires_restart: Whether the update requires a restart
            changelog: List of changes in this update
            platforms: List of supported platforms
            size: Size of the update in bytes
        """
        self.version = VersionInfo(version)
        self.url = url
        self.date = date
        self.channel = channel
        self.min_version = VersionInfo(min_version) if min_version else None
        self.requires_restart = requires_restart
        self.changelog = changelog or []
        self.platforms = platforms or ["windows", "macos", "linux"]
        self.size = size
    
    def is_compatible(self, current_version: VersionInfo) -> bool:
        """
        Check if the update is compatible with the current version.
        
        Args:
            current_version: Current version to check against
            
        Returns:
            bool: True if compatible, False otherwise
        """
        # If no minimum version is specified, assume it's compatible
        if self.min_version is None:
            return True
        
        # Check if current version meets minimum requirement
        return current_version >= self.min_version
    
    def supports_platform(self, platform: str) -> bool:
        """
        Check if the update supports the given platform.
        
        Args:
            platform: Platform to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return platform in self.platforms

class UpdateChecker:
    """Class for checking for updates."""
    
    def __init__(self, 
                 update_url: str = DEFAULT_UPDATE_URL,
                 check_interval: int = DEFAULT_CHECK_INTERVAL,
                 app_data_dir: Optional[Union[str, Path]] = None,
                 current_version: Optional[str] = None):
        """
        Initialize update checker.
        
        Args:
            update_url: URL to check for updates
            check_interval: Interval between checks in seconds
            app_data_dir: Directory to store update check information
            current_version: Current version (default: APP_VERSION)
        """
        self.update_url = update_url
        self.check_interval = check_interval
        
        # Set app data directory
        if app_data_dir is None:
            if sys.platform.startswith('win'):
                app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), "SpotifyDownloader")
            elif sys.platform.startswith('darwin'):
                app_data_dir = os.path.expanduser("~/Library/Application Support/SpotifyDownloader")
            else:  # Linux and other platforms
                app_data_dir = os.path.expanduser("~/.local/share/spotifydownloader")
        
        self.app_data_dir = Path(app_data_dir)
        self.app_data_dir.mkdir(exist_ok=True, parents=True)
        
        # Set current version
        self.current_version = VersionInfo(current_version or APP_VERSION)
        
        # Last check information
        self.last_check_file = self.app_data_dir / LAST_CHECK_FILE
        self.last_check_time = 0
        self.last_check_version = None
        self._load_last_check()
    
    def _load_last_check(self) -> None:
        """Load information about the last update check."""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    
                self.last_check_time = data.get('timestamp', 0)
                self.last_check_version = data.get('version')
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load last update check: {e}")
    
    def _save_last_check(self) -> None:
        """Save information about the last update check."""
        data = {
            'timestamp': time.time(),
            'version': str(self.current_version)
        }
        
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            logger.warning(f"Failed to save last update check: {e}")
    
    def should_check(self) -> bool:
        """
        Check if it's time to check for updates.
        
        Returns:
            bool: True if an update check is needed, False otherwise
        """
        # If never checked before, should check
        if self.last_check_time == 0:
            return True
        
        # If version changed since last check, should check
        if self.last_check_version != str(self.current_version):
            return True
        
        # Check based on time interval
        time_since_last_check = time.time() - self.last_check_time
        return time_since_last_check >= self.check_interval
    
    def check_for_updates(self, force: bool = False) -> Tuple[bool, Optional[UpdateInfo]]:
        """
        Check for updates.
        
        Args:
            force: Force an update check regardless of interval
            
        Returns:
            tuple: (update_available, update_info)
        """
        # Check if it's time to check for updates
        if not force and not self.should_check():
            logger.info("Skipping update check (already checked recently)")
            return False, None
        
        logger.info(f"Checking for updates at {self.update_url}")
        
        try:
            # Fetch update information
            with urllib.request.urlopen(self.update_url) as response:
                update_data = json.loads(response.read().decode('utf-8'))
            
            # Parse update information
            latest_version = update_data.get('latest_version')
            updates = update_data.get('updates', [])
            
            if not latest_version or not updates:
                raise ValueError("Invalid update data format")
            
            # Find the latest update info
            platform = "windows" if sys.platform.startswith('win') else (
                "macos" if sys.platform.startswith('darwin') else "linux"
            )
            
            latest_update = None
            for update in updates:
                version = update.get('version')
                if version != latest_version:
                    continue
                
                # Create update info
                update_info = UpdateInfo(
                    version=version,
                    url=update.get('url'),
                    date=update.get('date'),
                    channel=update.get('channel', 'stable'),
                    min_version=update.get('min_version'),
                    requires_restart=update.get('requires_restart', True),
                    changelog=update.get('changelog', []),
                    platforms=update.get('platforms'),
                    size=update.get('size')
                )
                
                # Check platform support
                if not update_info.supports_platform(platform):
                    continue
                
                latest_update = update_info
                break
            
            # Update last check info
            self._save_last_check()
            
            # Check if an update is available
            if latest_update and VersionInfo(latest_version) > self.current_version:
                logger.info(f"Update available: {latest_version}")
                return True, latest_update
            
            logger.info("No updates available")
            return False, None
            
        except (urllib.error.URLError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to check for updates: {e}")
            return False, None

def get_update_checker(app_data_dir: Optional[Union[str, Path]] = None) -> UpdateChecker:
    """
    Get the update checker instance.
    
    Args:
        app_data_dir: Directory to store update check information
        
    Returns:
        UpdateChecker: Update checker instance
    """
    return UpdateChecker(app_data_dir=app_data_dir)

def check_for_updates(force: bool = False) -> Tuple[bool, Optional[UpdateInfo]]:
    """
    Check for updates.
    
    Args:
        force: Force an update check regardless of interval
        
    Returns:
        tuple: (update_available, update_info)
    """
    checker = get_update_checker()
    return checker.check_for_updates(force=force) 