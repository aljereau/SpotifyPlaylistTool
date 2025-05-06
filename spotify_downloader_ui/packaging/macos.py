"""
macOS-specific packaging utilities for Spotify Downloader UI.

This module handles macOS-specific packaging tasks including:
- Creating macOS application bundle (.app)
- Generating disk image (.dmg) for distribution
- Handling code signing and notarization
- Setting up file associations, etc.
"""

import os
import sys
import logging
import shutil
import subprocess
import plistlib
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from .common import (
    get_app_root, create_build_directory, copy_application_files,
    APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION, APP_WEBSITE,
    FILE_EXTENSIONS, run_command
)

# Configure logging
logger = logging.getLogger(__name__)

def create_macos_app_bundle(output_dir: Union[str, Path],
                           clean: bool = True,
                           debug: bool = False) -> Path:
    """
    Create macOS application bundle (.app) using PyInstaller.
    
    Args:
        output_dir: Directory to store the output
        clean: Whether to clean the build directory first
        debug: Whether to build in debug mode
        
    Returns:
        Path: Path to the generated .app bundle
    """
    logger.info("Creating macOS application bundle with PyInstaller")
    
    output_path = Path(output_dir)
    if clean and output_path.exists():
        shutil.rmtree(output_path)
    
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Get path to spec file
    spec_file = Path(__file__).parent / "spotify_downloader.spec"
    
    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--clean" if clean else "",
        "--distpath", str(output_path / "dist"),
        "--workpath", str(output_path / "build"),
        str(spec_file)
    ]
    
    if debug:
        cmd.append("--debug")
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    # Run PyInstaller
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"PyInstaller failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        raise RuntimeError("Failed to create macOS application bundle")
    
    # Return path to app bundle
    app_path = output_path / "dist" / f"{APP_NAME}.app"
    if not app_path.exists():
        raise FileNotFoundError(f"Expected app bundle not found at {app_path}")
    
    logger.info(f"macOS application bundle created at {app_path}")
    return app_path

def update_info_plist(app_bundle: Union[str, Path],
                    identifier: str = None,
                    category: str = "public.app-category.utilities") -> None:
    """
    Update Info.plist file in the app bundle with additional metadata.
    
    Args:
        app_bundle: Path to the .app bundle
        identifier: Bundle identifier (default: generated from app name)
        category: Application category (from LSApplicationCategoryType constants)
    """
    logger.info("Updating Info.plist with additional metadata")
    
    app_path = Path(app_bundle)
    plist_path = app_path / "Contents" / "Info.plist"
    
    if not plist_path.exists():
        raise FileNotFoundError(f"Info.plist not found in app bundle: {plist_path}")
    
    # Generate bundle identifier if not provided
    if identifier is None:
        identifier = f"com.{APP_NAME.lower().replace(' ', '')}.app"
    
    # Read existing plist
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)
    
    # Update with additional metadata
    updates = {
        'CFBundleIdentifier': identifier,
        'LSApplicationCategoryType': category,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHumanReadableCopyright': f"© {APP_AUTHOR}",
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Support Dark Mode
        'LSMinimumSystemVersion': '10.14',  # Minimum macOS version
    }
    
    # Add file associations if specified
    if FILE_EXTENSIONS:
        document_types = plist.get('CFBundleDocumentTypes', [])
        
        for ext in FILE_EXTENSIONS:
            # Strip leading dot if present
            ext_clean = ext[1:] if ext.startswith('.') else ext
            
            document_type = {
                'CFBundleTypeExtensions': [ext_clean],
                'CFBundleTypeIconFile': 'document.icns',  # Should be included in resources
                'CFBundleTypeName': f"{APP_NAME} {ext_clean.upper()} File",
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Owner',
            }
            
            document_types.append(document_type)
        
        updates['CFBundleDocumentTypes'] = document_types
    
    # Update plist with new values
    plist.update(updates)
    
    # Write updated plist
    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)
    
    logger.info(f"Updated Info.plist at {plist_path}")

def code_sign_app(app_bundle: Union[str, Path],
                 identity: str = None,
                 entitlements: Union[str, Path] = None) -> bool:
    """
    Code sign the macOS application bundle.
    
    Args:
        app_bundle: Path to the .app bundle
        identity: Code signing identity (e.g., "Developer ID Application: Your Name")
        entitlements: Path to entitlements file
        
    Returns:
        bool: True if signing was successful
    """
    if identity is None:
        logger.warning("No code signing identity provided, skipping code signing")
        return False
    
    logger.info(f"Code signing macOS application with identity: {identity}")
    
    app_path = Path(app_bundle)
    
    # Check if the app bundle exists
    if not app_path.exists():
        raise FileNotFoundError(f"App bundle not found: {app_path}")
    
    # Build codesign command
    cmd = ["codesign", "--force", "--verbose", "--timestamp"]
    
    if entitlements:
        entitlements_path = Path(entitlements)
        if not entitlements_path.exists():
            raise FileNotFoundError(f"Entitlements file not found: {entitlements_path}")
        
        cmd.extend(["--entitlements", str(entitlements_path)])
    
    cmd.extend(["--sign", identity, str(app_path)])
    
    # Run codesign
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Code signing failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False
    
    logger.info(f"Successfully signed {app_path}")
    
    # Verify signature
    verify_cmd = ["codesign", "--verify", "--verbose", str(app_path)]
    return_code, stdout, stderr = run_command(verify_cmd)
    
    if return_code != 0:
        logger.error(f"Code signature verification failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False
    
    logger.info(f"Signature verification successful for {app_path}")
    return True

def create_dmg_file(app_bundle: Union[str, Path],
                  output_dir: Union[str, Path],
                  background_image: Union[str, Path] = None,
                  volume_name: str = None) -> Path:
    """
    Create a DMG disk image for distribution.
    
    Args:
        app_bundle: Path to the .app bundle
        output_dir: Directory to store the output DMG file
        background_image: Path to background image for the DMG
        volume_name: Name of the mounted volume (default: app name)
        
    Returns:
        Path: Path to the generated DMG file
    """
    logger.info("Creating DMG disk image")
    
    app_path = Path(app_bundle)
    output_path = Path(output_dir)
    
    # Check if the app bundle exists
    if not app_path.exists():
        raise FileNotFoundError(f"App bundle not found: {app_path}")
    
    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Set default volume name if not provided
    if volume_name is None:
        volume_name = f"{APP_NAME} {APP_VERSION}"
    
    # Set DMG filename
    dmg_filename = f"{APP_NAME.replace(' ', '')}-{APP_VERSION}.dmg"
    dmg_path = output_path / dmg_filename
    
    # If background image is specified, check if it exists
    if background_image is not None:
        background_path = Path(background_image)
        if not background_path.exists():
            logger.warning(f"Background image not found: {background_path}")
            background_image = None
    
    # Create a temporary directory for DMG contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy .app bundle to temporary directory
        shutil.copytree(app_path, temp_path / app_path.name)
        
        # Create a symbolic link to /Applications
        applications_link = temp_path / "Applications"
        os.symlink("/Applications", applications_link)
        
        # If background image is specified, create .background directory
        if background_image:
            background_dir = temp_path / ".background"
            background_dir.mkdir(exist_ok=True)
            
            # Copy background image
            shutil.copy2(background_image, background_dir / Path(background_image).name)
            
            # Create DS_Store file (requires additional tools, simplified here)
            # In a real implementation, you would use a tool like DMGCanvas or create_dmg
        
        # Create DMG file using hdiutil
        cmd = [
            "hdiutil", "create",
            "-volname", volume_name,
            "-srcfolder", str(temp_path),
            "-ov",  # Overwrite existing file
            "-format", "UDZO",  # Compressed disk image
            str(dmg_path)
        ]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"DMG creation failed with code {return_code}")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            raise RuntimeError("Failed to create DMG file")
    
    logger.info(f"DMG file created at {dmg_path}")
    return dmg_path

def notarize_app(dmg_path: Union[str, Path],
               username: str,
               password: str,
               team_id: str = None) -> bool:
    """
    Notarize a DMG file with Apple.
    
    Args:
        dmg_path: Path to the DMG file
        username: Apple ID username
        password: Apple ID app-specific password
        team_id: Team ID (if part of multiple teams)
        
    Returns:
        bool: True if notarization was successful
    """
    if not (username and password):
        logger.warning("Missing username or password, skipping notarization")
        return False
    
    logger.info("Submitting app for notarization")
    
    dmg_file = Path(dmg_path)
    
    # Check if the DMG file exists
    if not dmg_file.exists():
        raise FileNotFoundError(f"DMG file not found: {dmg_file}")
    
    # Submit for notarization
    cmd = [
        "xcrun", "altool", "--notarize-app",
        "--primary-bundle-id", f"com.{APP_NAME.lower().replace(' ', '')}.app",
        "--username", username,
        "--password", password,
        "--file", str(dmg_file)
    ]
    
    if team_id:
        cmd.extend(["--asc-provider", team_id])
    
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Notarization submission failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False
    
    # Extract request UUID from output
    request_uuid = None
    for line in stdout.splitlines():
        if "RequestUUID" in line:
            request_uuid = line.split("=")[1].strip()
            break
    
    if not request_uuid:
        logger.error("Failed to extract RequestUUID from notarization submission")
        return False
    
    logger.info(f"Notarization request submitted with UUID: {request_uuid}")
    logger.info("Waiting for notarization to complete (this may take several minutes)...")
    
    # Check notarization status (polling)
    success = False
    max_attempts = 30
    for attempt in range(max_attempts):
        logger.info(f"Checking notarization status (attempt {attempt + 1}/{max_attempts})...")
        
        # Wait before checking
        import time
        time.sleep(30)  # Wait 30 seconds between checks
        
        # Check status
        cmd = [
            "xcrun", "altool", "--notarization-info", request_uuid,
            "--username", username,
            "--password", password
        ]
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.warning(f"Failed to check notarization status: {stderr}")
            continue
        
        # Check if notarization is complete
        if "Status: success" in stdout:
            success = True
            logger.info("Notarization successful!")
            break
        elif "Status: in progress" in stdout:
            logger.info("Notarization still in progress...")
            continue
        else:
            logger.error(f"Notarization failed: {stdout}")
            return False
    
    if not success:
        logger.error("Notarization timed out")
        return False
    
    # Staple the notarization to the DMG
    logger.info("Stapling notarization ticket to DMG...")
    cmd = ["xcrun", "stapler", "staple", str(dmg_file)]
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Stapling failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False
    
    logger.info("Notarization ticket successfully stapled to DMG")
    return True

def create_macos_package(build_dir: Union[str, Path] = "build",
                        output_dir: Union[str, Path] = "dist",
                        clean: bool = True,
                        sign: bool = False,
                        sign_identity: str = None,
                        notarize: bool = False,
                        apple_id: str = None,
                        apple_password: str = None,
                        team_id: str = None) -> Tuple[Path, Optional[Path]]:
    """
    Create macOS application bundle and DMG for distribution.
    
    Args:
        build_dir: Directory for intermediate build files
        output_dir: Directory for final output
        clean: Whether to clean the build directories first
        sign: Whether to sign the application bundle
        sign_identity: Code signing identity
        notarize: Whether to notarize the application
        apple_id: Apple ID username for notarization
        apple_password: App-specific password for notarization
        team_id: Team ID (if part of multiple teams)
        
    Returns:
        Tuple[Path, Optional[Path]]: Paths to the app bundle and DMG file (if created)
    """
    logger.info(f"Creating macOS package for {APP_NAME} {APP_VERSION}")
    
    # Validate that we're running on macOS
    if not sys.platform.startswith('darwin'):
        raise RuntimeError("macOS packaging must be run on macOS")
    
    build_path = create_build_directory(build_dir) if clean else Path(build_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Create application bundle
    app_path = create_macos_app_bundle(build_path / "pyinstaller", clean=clean)
    
    # Update Info.plist with additional metadata
    update_info_plist(app_path)
    
    # Copy app bundle to output directory
    output_app_path = output_path / app_path.name
    if output_app_path.exists():
        shutil.rmtree(output_app_path)
    shutil.copytree(app_path, output_app_path)
    
    # Sign the application if requested
    if sign:
        if not sign_identity:
            logger.warning("Code signing requested, but no identity provided")
        else:
            code_sign_app(output_app_path, identity=sign_identity)
    
    # Create DMG file
    dmg_path = create_dmg_file(output_app_path, output_path)
    
    # Notarize the DMG if requested
    if notarize:
        if not (apple_id and apple_password):
            logger.warning("Notarization requested, but missing Apple ID or password")
        else:
            notarize_app(dmg_path, apple_id, apple_password, team_id)
    
    logger.info(f"macOS package created: {output_app_path} and {dmg_path}")
    return output_app_path, dmg_path

def main():
    """Main function for testing the module."""
    logging.basicConfig(level=logging.INFO)
    create_macos_package()

if __name__ == "__main__":
    main() 