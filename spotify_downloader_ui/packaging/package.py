#!/usr/bin/env python3
"""
Main packaging script for Spotify Downloader UI.

This script provides a command-line interface for creating packages
for different platforms (Windows, macOS, Linux).
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("spotify_downloader.packaging")

# Add parent directory to path so we can import the packaging module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from spotify_downloader_ui.packaging.common import (
    get_app_root, APP_NAME, APP_VERSION, get_platform
)

def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=f"Create packages for {APP_NAME} {APP_VERSION}"
    )
    
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        default=get_platform(),
        help="Target platform for packaging (default: current platform)"
    )
    
    parser.add_argument(
        "--build-dir",
        type=str,
        default="build",
        help="Directory for intermediate build files (default: 'build')"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dist",
        help="Directory for final output (default: 'dist')"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Clean build directories before building (default: True)"
    )
    
    parser.add_argument(
        "--no-clean",
        action="store_false",
        dest="clean",
        help="Don't clean build directories before building"
    )
    
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Create portable package (Windows only)"
    )
    
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Sign the package (macOS only)"
    )
    
    parser.add_argument(
        "--sign-identity",
        type=str,
        help="Code signing identity (macOS only)"
    )
    
    parser.add_argument(
        "--notarize",
        action="store_true",
        help="Notarize the package with Apple (macOS only)"
    )
    
    parser.add_argument(
        "--apple-id",
        type=str,
        help="Apple ID for notarization (macOS only)"
    )
    
    parser.add_argument(
        "--apple-password",
        type=str,
        help="App-specific password for Apple ID (macOS only)"
    )
    
    parser.add_argument(
        "--team-id",
        type=str,
        help="Team ID for notarization (macOS only)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser

def package_windows(args: argparse.Namespace) -> Dict[str, Path]:
    """
    Create Windows packages.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Dict[str, Path]: Dictionary of package type to path
    """
    from spotify_downloader_ui.packaging.windows import (
        create_windows_installer, create_portable_package
    )
    
    packages = {}
    
    # Create installer
    packages['installer'] = create_windows_installer(
        build_dir=args.build_dir,
        output_dir=args.output_dir,
        clean=args.clean
    )
    
    # Create portable package if requested
    if args.portable:
        packages['portable'] = create_portable_package(
            build_dir=args.build_dir,
            output_dir=args.output_dir,
            clean=False  # Don't clean again if we just created the installer
        )
    
    return packages

def package_macos(args: argparse.Namespace) -> Dict[str, Path]:
    """
    Create macOS packages.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Dict[str, Path]: Dictionary of package type to path
    """
    from spotify_downloader_ui.packaging.macos import create_macos_package
    
    # Create macOS package
    app_path, dmg_path = create_macos_package(
        build_dir=args.build_dir,
        output_dir=args.output_dir,
        clean=args.clean,
        sign=args.sign,
        sign_identity=args.sign_identity,
        notarize=args.notarize,
        apple_id=args.apple_id,
        apple_password=args.apple_password,
        team_id=args.team_id
    )
    
    packages = {
        'app': app_path,
        'dmg': dmg_path
    }
    
    return packages

def package_linux(args: argparse.Namespace) -> Dict[str, Path]:
    """
    Create Linux packages.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Dict[str, Path]: Dictionary of package type to path
    """
    from spotify_downloader_ui.packaging.linux import create_linux_packages
    
    # Create Linux packages
    packages = create_linux_packages(
        build_dir=args.build_dir,
        output_dir=args.output_dir,
        clean=args.clean
    )
    
    return packages

def main():
    """Main entry point for the packaging script."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Creating packages for {APP_NAME} {APP_VERSION}")
    logger.info(f"Platform: {args.platform}")
    logger.info(f"Build directory: {args.build_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create packages for the specified platform
    try:
        if args.platform == "windows" or args.platform == "all":
            logger.info("Creating Windows packages")
            try:
                windows_packages = package_windows(args)
                logger.info(f"Windows packages created: {', '.join(windows_packages.keys())}")
            except Exception as e:
                logger.error(f"Failed to create Windows packages: {e}")
                if args.platform != "all":
                    raise
        
        if args.platform == "macos" or args.platform == "all":
            logger.info("Creating macOS packages")
            try:
                macos_packages = package_macos(args)
                logger.info(f"macOS packages created: {', '.join(macos_packages.keys())}")
            except Exception as e:
                logger.error(f"Failed to create macOS packages: {e}")
                if args.platform != "all":
                    raise
        
        if args.platform == "linux" or args.platform == "all":
            logger.info("Creating Linux packages")
            try:
                linux_packages = package_linux(args)
                logger.info(f"Linux packages created: {', '.join(linux_packages.keys())}")
            except Exception as e:
                logger.error(f"Failed to create Linux packages: {e}")
                if args.platform != "all":
                    raise
        
        logger.info(f"All packages created successfully in {output_dir}")
    
    except Exception as e:
        logger.error(f"Package creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 