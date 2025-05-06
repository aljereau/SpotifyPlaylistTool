"""
Common packaging utilities for Spotify Downloader UI.

This module contains common utilities for packaging the application
that are shared across all platforms.
"""

import os
import sys
import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Union

# Configure logging
logger = logging.getLogger(__name__)

# Application metadata
APP_NAME = "Spotify Downloader"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Spotify Downloader Team"
APP_DESCRIPTION = "A tool for extracting and analyzing Spotify playlists"
APP_WEBSITE = "https://github.com/aljereau/Spotify-Downloader"
APP_LICENSE = "MIT"

# File extensions to associate with the application
FILE_EXTENSIONS = [".spotifylist"]

def get_app_root() -> Path:
    """
    Get the root directory of the application.
    
    Returns:
        Path: The application root directory
    """
    # When packaged with PyInstaller, _MEIPASS is defined
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    
    # Development mode - return the repository root
    return Path(__file__).parent.parent.parent

def get_platform() -> str:
    """
    Get the current platform identifier.
    
    Returns:
        str: 'windows', 'macos', or 'linux'
    """
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    else:
        return 'linux'

def collect_dependencies() -> List[str]:
    """
    Collect a list of all package dependencies.
    
    Returns:
        List[str]: List of package dependencies
    """
    # Use pipdeptree or similar to get accurate dependency list
    # This is a simplified example
    try:
        import pkg_resources
        return [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
    except ImportError:
        logger.warning("Could not import pkg_resources to collect dependencies")
        return []

def create_build_directory(build_dir: Union[str, Path]) -> Path:
    """
    Create and prepare a clean build directory.
    
    Args:
        build_dir: Path to the build directory
        
    Returns:
        Path: The path to the created build directory
    """
    build_path = Path(build_dir)
    
    # Create or clean the directory
    if build_path.exists():
        logger.info(f"Cleaning build directory: {build_path}")
        shutil.rmtree(build_path)
    
    logger.info(f"Creating build directory: {build_path}")
    build_path.mkdir(parents=True)
    
    return build_path

def copy_application_files(build_dir: Union[str, Path], include_docs: bool = True) -> None:
    """
    Copy application files to the build directory.
    
    Args:
        build_dir: Path to the build directory
        include_docs: Whether to include documentation files
    """
    build_path = Path(build_dir)
    app_root = get_app_root()
    
    # Copy main package
    logger.info("Copying application files")
    shutil.copytree(
        app_root / "spotify_downloader_ui",
        build_path / "spotify_downloader_ui",
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
    )
    
    # Copy other necessary files
    for filename in ["requirements.txt", "ui_requirements.txt", "LICENSE", "README.md"]:
        src_file = app_root / filename
        if src_file.exists():
            shutil.copy2(src_file, build_path)
    
    # Copy documentation if requested
    if include_docs:
        docs_dir = app_root / "docs"
        if docs_dir.exists():
            shutil.copytree(docs_dir, build_path / "docs")

def get_version_info() -> Dict[str, Any]:
    """
    Get detailed version information.
    
    Returns:
        Dict[str, Any]: Version information dictionary
    """
    return {
        "version": APP_VERSION,
        "full_version": APP_VERSION,
        "platform": get_platform(),
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "build_date": None,  # Will be set during actual build
    }

def run_command(cmd: List[str], cwd: Optional[Union[str, Path]] = None) -> Tuple[int, str, str]:
    """
    Run a command and return its output.
    
    Args:
        cmd: Command to run as list of arguments
        cwd: Working directory for the command
        
    Returns:
        Tuple[int, str, str]: Return code, stdout, stderr
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr 