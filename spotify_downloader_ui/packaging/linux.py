"""
Linux-specific packaging utilities for Spotify Downloader UI.

This module handles Linux-specific packaging tasks including:
- Creating Linux executable using PyInstaller
- Generating Debian (.deb) packages
- Creating RPM packages
- Building AppImage files
- Setting up desktop files, file associations, etc.
"""

import os
import sys
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .common import (
    get_app_root, create_build_directory, copy_application_files,
    APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION, APP_WEBSITE,
    FILE_EXTENSIONS, run_command, collect_dependencies
)

# Configure logging
logger = logging.getLogger(__name__)

def create_linux_executable(output_dir: Union[str, Path],
                          clean: bool = True,
                          debug: bool = False) -> Path:
    """
    Create Linux executable using PyInstaller.
    
    Args:
        output_dir: Directory to store the output
        clean: Whether to clean the build directory first
        debug: Whether to build in debug mode
        
    Returns:
        Path: Path to the generated executable
    """
    logger.info("Creating Linux executable with PyInstaller")
    
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
        raise RuntimeError("Failed to create Linux executable")
    
    # Return path to executable
    exe_path = output_path / "dist" / APP_NAME / APP_NAME
    if not exe_path.exists():
        raise FileNotFoundError(f"Expected executable not found at {exe_path}")
    
    logger.info(f"Linux executable created at {exe_path}")
    return exe_path

def create_desktop_file(output_dir: Union[str, Path]) -> Path:
    """
    Create a desktop file for Linux application.
    
    Args:
        output_dir: Directory to store the output
        
    Returns:
        Path: Path to the generated desktop file
    """
    logger.info("Creating Linux desktop file")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    desktop_path = output_path / f"{APP_NAME.lower().replace(' ', '-')}.desktop"
    
    # Desktop file content
    content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment={APP_DESCRIPTION}
Exec={APP_NAME}
Icon={APP_NAME.lower().replace(' ', '-')}
Terminal=false
Categories=Audio;AudioVideo;Music;
Keywords=spotify;music;playlist;
StartupNotify=true
"""
    
    # Add file associations
    if FILE_EXTENSIONS:
        mime_types = []
        for ext in FILE_EXTENSIONS:
            # Strip leading dot if present
            ext_clean = ext[1:] if ext.startswith('.') else ext
            mime_types.append(f"application/x-{APP_NAME.lower()}-{ext_clean}")
        
        if mime_types:
            content += f"MimeType={';'.join(mime_types)};\n"
    
    # Write desktop file
    with open(desktop_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Desktop file created at {desktop_path}")
    return desktop_path

def create_mime_type_files(output_dir: Union[str, Path]) -> List[Path]:
    """
    Create MIME type files for file associations.
    
    Args:
        output_dir: Directory to store the output
        
    Returns:
        List[Path]: Paths to the generated MIME type files
    """
    if not FILE_EXTENSIONS:
        return []
    
    logger.info("Creating MIME type files")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    mime_files = []
    
    for ext in FILE_EXTENSIONS:
        # Strip leading dot if present
        ext_clean = ext[1:] if ext.startswith('.') else ext
        
        mime_type = f"application/x-{APP_NAME.lower()}-{ext_clean}"
        filename = f"{mime_type.replace('/', '-')}.xml"
        mime_path = output_path / filename
        
        # MIME type file content
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="{mime_type}">
    <comment>{APP_NAME} {ext_clean.upper()} File</comment>
    <glob pattern="*{ext}"/>
    <icon name="{APP_NAME.lower().replace(' ', '-')}"/>
  </mime-type>
</mime-info>
"""
        
        # Write MIME type file
        with open(mime_path, 'w') as f:
            f.write(content)
        
        mime_files.append(mime_path)
        logger.info(f"MIME type file created at {mime_path}")
    
    return mime_files

def create_debian_package(build_dir: Union[str, Path],
                        output_dir: Union[str, Path],
                        clean: bool = True) -> Path:
    """
    Create a Debian package (.deb) for distribution.
    
    Args:
        build_dir: Directory for intermediate build files
        output_dir: Directory for final output
        clean: Whether to clean the build directories first
        
    Returns:
        Path: Path to the generated .deb package
    """
    logger.info("Creating Debian package")
    
    build_path = Path(build_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Create a temporary directory for Debian package structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create package directory structure
        package_name = APP_NAME.lower().replace(' ', '-')
        version = APP_VERSION.replace('-', '~')  # Debian version format
        
        # Create directories
        debian_root = temp_path / package_name
        debian_root.mkdir()
        
        # Create DEBIAN control directory
        control_dir = debian_root / "DEBIAN"
        control_dir.mkdir()
        
        # Create control file
        control_content = f"""Package: {package_name}
Version: {version}
Section: sound
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8)
Maintainer: {APP_AUTHOR}
Description: {APP_DESCRIPTION}
 A powerful tool for extracting and analyzing Spotify playlists.
 .
 Features include:
 * Extract track information from Spotify playlists
 * Discover "hidden gems" using sophisticated scoring
 * Create new playlists from discovered tracks
 * Comprehensive analytics about tracks and artists
 * Modern graphical user interface
"""
        with open(control_dir / "control", 'w') as f:
            f.write(control_content)
        
        # Create post-install script
        postinst_content = """#!/bin/sh
set -e

# Register MIME types and update desktop database
if [ "$1" = "configure" ] || [ "$1" = "abort-upgrade" ]; then
    if command -v update-mime-database >/dev/null; then
        update-mime-database /usr/share/mime
    fi
    if command -v update-desktop-database >/dev/null; then
        update-desktop-database -q
    fi
fi

exit 0
"""
        postinst_path = control_dir / "postinst"
        with open(postinst_path, 'w') as f:
            f.write(postinst_content)
        os.chmod(postinst_path, 0o755)  # Make executable
        
        # Create pre-remove script
        prerm_content = """#!/bin/sh
set -e

exit 0
"""
        prerm_path = control_dir / "prerm"
        with open(prerm_path, 'w') as f:
            f.write(prerm_content)
        os.chmod(prerm_path, 0o755)  # Make executable
        
        # Create directories for files
        bin_dir = debian_root / "usr" / "bin"
        bin_dir.mkdir(parents=True)
        
        app_dir = debian_root / "opt" / package_name
        app_dir.mkdir(parents=True)
        
        share_dir = debian_root / "usr" / "share"
        icons_dir = share_dir / "icons" / "hicolor" / "128x128" / "apps"
        icons_dir.mkdir(parents=True)
        
        desktop_dir = share_dir / "applications"
        desktop_dir.mkdir(parents=True)
        
        mime_dir = share_dir / "mime" / "packages"
        mime_dir.mkdir(parents=True)
        
        doc_dir = share_dir / "doc" / package_name
        doc_dir.mkdir(parents=True)
        
        # Copy application files
        app_path = build_path / "pyinstaller" / "dist" / APP_NAME
        if not app_path.exists():
            # Create the executable if it doesn't exist
            create_linux_executable(build_path / "pyinstaller", clean=clean)
        
        # Check again if it exists
        if not app_path.exists():
            raise FileNotFoundError(f"Expected executable directory not found at {app_path}")
        
        # Copy application files to package
        shutil.copytree(app_path, app_dir, dirs_exist_ok=True)
        
        # Create symlink in /usr/bin
        bin_link = bin_dir / package_name
        bin_link.write_text(f"""#!/bin/sh
exec /opt/{package_name}/{APP_NAME} "$@"
""")
        os.chmod(bin_link, 0o755)  # Make executable
        
        # Copy icon
        icon_path = app_path / "spotify_downloader_ui" / "assets" / "icons" / "app_icon.png"
        if icon_path.exists():
            shutil.copy2(icon_path, icons_dir / f"{package_name}.png")
        
        # Create desktop file
        desktop_file = create_desktop_file(temp_path)
        shutil.copy2(desktop_file, desktop_dir)
        
        # Create MIME type files
        mime_files = create_mime_type_files(temp_path)
        for mime_file in mime_files:
            shutil.copy2(mime_file, mime_dir)
        
        # Copy documentation
        doc_files = ["README.md", "LICENSE"]
        for doc_file in doc_files:
            doc_path = get_app_root() / doc_file
            if doc_path.exists():
                shutil.copy2(doc_path, doc_dir)
        
        # Build Debian package
        arch = "amd64"  # Default architecture
        deb_filename = f"{package_name}_{version}_{arch}.deb"
        deb_path = output_path / deb_filename
        
        cmd = ["dpkg-deb", "--build", "--root-owner-group", str(debian_root), str(deb_path)]
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"dpkg-deb failed with code {return_code}")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            raise RuntimeError("Failed to create Debian package")
    
    logger.info(f"Debian package created at {deb_path}")
    return deb_path

def create_rpm_package(build_dir: Union[str, Path],
                      output_dir: Union[str, Path],
                      clean: bool = True) -> Path:
    """
    Create an RPM package for distribution.
    
    Args:
        build_dir: Directory for intermediate build files
        output_dir: Directory for final output
        clean: Whether to clean the build directories first
        
    Returns:
        Path: Path to the generated .rpm package
    """
    logger.info("Creating RPM package")
    
    build_path = Path(build_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    package_name = APP_NAME.lower().replace(' ', '-')
    version = APP_VERSION
    
    # Create directory structure for RPM package
    rpm_build_dir = build_path / "rpm"
    if clean and rpm_build_dir.exists():
        shutil.rmtree(rpm_build_dir)
    
    rpm_build_dir.mkdir(exist_ok=True, parents=True)
    
    for subdir in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpm_build_dir / subdir).mkdir(exist_ok=True)
    
    # Create source tarball
    source_dir = rpm_build_dir / "SOURCES"
    tarball_name = f"{package_name}-{version}.tar.gz"
    tarball_path = source_dir / tarball_name
    
    # Create application files for the tarball
    app_path = build_path / "pyinstaller" / "dist" / APP_NAME
    if not app_path.exists():
        # Create the executable if it doesn't exist
        create_linux_executable(build_path / "pyinstaller", clean=clean)
    
    # Create tarball directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / f"{package_name}-{version}"
        package_dir.mkdir()
        
        # Copy application files
        shutil.copytree(app_path, package_dir / APP_NAME, dirs_exist_ok=True)
        
        # Create desktop file
        desktop_file = create_desktop_file(temp_path)
        shutil.copy2(desktop_file, package_dir)
        
        # Create MIME type files
        mime_files = create_mime_type_files(temp_path)
        for mime_file in mime_files:
            shutil.copy2(mime_file, package_dir)
        
        # Create tarball
        import tarfile
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(package_dir, arcname=f"{package_name}-{version}")
    
    # Create spec file
    spec_file = rpm_build_dir / "SPECS" / f"{package_name}.spec"
    
    spec_content = f"""Name:           {package_name}
Version:        {version}
Release:        1%{{?dist}}
Summary:        A tool for extracting and analyzing Spotify playlists

License:        MIT
URL:            {APP_WEBSITE}
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      x86_64
Requires:       python3 >= 3.8

%description
{APP_DESCRIPTION}

A powerful tool for extracting and analyzing Spotify playlists.

Features include:
* Extract track information from Spotify playlists
* Discover "hidden gems" using sophisticated scoring
* Create new playlists from discovered tracks
* Comprehensive analytics about tracks and artists
* Modern graphical user interface

%prep
%setup -q

%build
# Nothing to build

%install
mkdir -p %{{buildroot}}/opt/%{{name}}
mkdir -p %{{buildroot}}%{{_bindir}}
mkdir -p %{{buildroot}}%{{_datadir}}/applications
mkdir -p %{{buildroot}}%{{_datadir}}/mime/packages
mkdir -p %{{buildroot}}%{{_datadir}}/icons/hicolor/128x128/apps

# Copy application files
cp -r %{{name}}-%{{version}}/{APP_NAME}/* %{{buildroot}}/opt/%{{name}}/

# Create executable launcher
cat > %{{buildroot}}%{{_bindir}}/%{{name}} << 'EOF'
#!/bin/sh
exec /opt/%{{name}}/{APP_NAME} "$@"
EOF
chmod 755 %{{buildroot}}%{{_bindir}}/%{{name}}

# Install desktop file
install -m 644 %{{name}}-%{{version}}/*.desktop %{{buildroot}}%{{_datadir}}/applications/

# Install MIME type files
if ls %{{name}}-%{{version}}/*.xml 1> /dev/null 2>&1; then
    install -m 644 %{{name}}-%{{version}}/*.xml %{{buildroot}}%{{_datadir}}/mime/packages/
fi

# Install icon
if [ -f %{{name}}-%{{version}}/{APP_NAME}/spotify_downloader_ui/assets/icons/app_icon.png ]; then
    install -m 644 %{{name}}-%{{version}}/{APP_NAME}/spotify_downloader_ui/assets/icons/app_icon.png %{{buildroot}}%{{_datadir}}/icons/hicolor/128x128/apps/%{{name}}.png
fi

%files
%license %{{name}}-%{{version}}/{APP_NAME}/LICENSE
%doc %{{name}}-%{{version}}/{APP_NAME}/README.md
%{{_bindir}}/%{{name}}
%{{_datadir}}/applications/*.desktop
%{{_datadir}}/mime/packages/*.xml
%{{_datadir}}/icons/hicolor/128x128/apps/%{{name}}.png
/opt/%{{name}}/

%post
if [ $1 -eq 1 ]; then
    # Update MIME and desktop database on first install
    update-mime-database %{{_datadir}}/mime &> /dev/null || :
    update-desktop-database &> /dev/null || :
fi

%postun
if [ $1 -eq 0 ]; then
    # Update MIME and desktop database on removal
    update-mime-database %{{_datadir}}/mime &> /dev/null || :
    update-desktop-database &> /dev/null || :
fi

%changelog
* {subprocess.check_output(['date', '+%a %b %d %Y']).decode().strip()} {APP_AUTHOR} <maintainer@example.com> - {version}-1
- Initial package
"""
    
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Build RPM package
    cmd = [
        "rpmbuild", "-ba",
        "--define", f"_topdir {rpm_build_dir.absolute()}",
        str(spec_file)
    ]
    
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"rpmbuild failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        raise RuntimeError("Failed to create RPM package")
    
    # Find the built RPM package
    rpm_files = list((rpm_build_dir / "RPMS" / "x86_64").glob(f"{package_name}-{version}*.rpm"))
    
    if not rpm_files:
        raise FileNotFoundError("No RPM package found after build")
    
    rpm_path = rpm_files[0]
    final_rpm_path = output_path / rpm_path.name
    shutil.copy2(rpm_path, final_rpm_path)
    
    logger.info(f"RPM package created at {final_rpm_path}")
    return final_rpm_path

def create_appimage(build_dir: Union[str, Path],
                   output_dir: Union[str, Path],
                   clean: bool = True) -> Path:
    """
    Create an AppImage file for distribution.
    
    Args:
        build_dir: Directory for intermediate build files
        output_dir: Directory for final output
        clean: Whether to clean the build directories first
        
    Returns:
        Path: Path to the generated AppImage file
    """
    logger.info("Creating AppImage")
    
    build_path = Path(build_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Create AppDir structure
    appdir_path = build_path / "appdir"
    if clean and appdir_path.exists():
        shutil.rmtree(appdir_path)
    
    appdir_path.mkdir(exist_ok=True, parents=True)
    
    # Copy application files from PyInstaller build
    app_path = build_path / "pyinstaller" / "dist" / APP_NAME
    if not app_path.exists():
        # Create the executable if it doesn't exist
        create_linux_executable(build_path / "pyinstaller", clean=clean)
    
    # Copy all files to AppDir
    shutil.copytree(app_path, appdir_path / "usr", dirs_exist_ok=True)
    
    # Create AppRun executable
    apprun_path = appdir_path / "AppRun"
    apprun_content = f"""#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${HERE}/usr/sbin:${HERE}/usr/games:${HERE}/bin:${HERE}/sbin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu:${HERE}/usr/lib/i386-linux-gnu:${HERE}/lib:${HERE}/lib/x86_64-linux-gnu:${HERE}/lib/i386-linux-gnu:$LD_LIBRARY_PATH"
export PYTHONPATH="${HERE}/usr/lib/python3.8/site-packages:${PYTHONPATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
exec "${HERE}/usr/{APP_NAME}" "$@"
"""
    
    with open(apprun_path, 'w') as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)  # Make executable
    
    # Create desktop file
    desktop_path = appdir_path / f"{APP_NAME.lower().replace(' ', '-')}.desktop"
    create_desktop_file(appdir_path)
    
    # Copy icon
    icon_path = app_path / "spotify_downloader_ui" / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        shutil.copy2(icon_path, appdir_path / f"{APP_NAME.lower().replace(' ', '-')}.png")
    
    # Download AppImage tool
    appimage_tool_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    appimage_tool_path = build_path / "appimagetool"
    
    if not appimage_tool_path.exists():
        logger.info(f"Downloading AppImage tool from {appimage_tool_url}")
        import urllib.request
        urllib.request.urlretrieve(appimage_tool_url, appimage_tool_path)
        os.chmod(appimage_tool_path, 0o755)  # Make executable
    
    # Build AppImage
    appimage_filename = f"{APP_NAME.replace(' ', '_')}-{APP_VERSION}-x86_64.AppImage"
    appimage_path = output_path / appimage_filename
    
    # Run AppImage tool
    cmd = [str(appimage_tool_path), str(appdir_path), str(appimage_path)]
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"AppImage tool failed with code {return_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        raise RuntimeError("Failed to create AppImage")
    
    logger.info(f"AppImage created at {appimage_path}")
    return appimage_path

def create_linux_packages(build_dir: Union[str, Path] = "build",
                         output_dir: Union[str, Path] = "dist",
                         clean: bool = True) -> Dict[str, Path]:
    """
    Create all Linux packages for distribution.
    
    Args:
        build_dir: Directory for intermediate build files
        output_dir: Directory for final output
        clean: Whether to clean the build directories first
        
    Returns:
        Dict[str, Path]: Dictionary of package type to generated package path
    """
    logger.info(f"Creating Linux packages for {APP_NAME} {APP_VERSION}")
    
    # Validate that we're running on Linux
    if not sys.platform.startswith('linux'):
        raise RuntimeError("Linux packaging must be run on Linux")
    
    build_path = create_build_directory(build_dir) if clean else Path(build_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Create executable first
    create_linux_executable(build_path / "pyinstaller", clean=clean)
    
    # Create packages
    packages = {}
    
    # Try to create Debian package
    try:
        packages['deb'] = create_debian_package(build_path, output_path, clean=False)
    except Exception as e:
        logger.error(f"Failed to create Debian package: {e}")
    
    # Try to create RPM package
    try:
        packages['rpm'] = create_rpm_package(build_path, output_path, clean=False)
    except Exception as e:
        logger.error(f"Failed to create RPM package: {e}")
    
    # Try to create AppImage
    try:
        packages['appimage'] = create_appimage(build_path, output_path, clean=False)
    except Exception as e:
        logger.error(f"Failed to create AppImage: {e}")
    
    if not packages:
        raise RuntimeError("Failed to create any Linux packages")
    
    logger.info(f"Created Linux packages: {', '.join(packages.keys())}")
    return packages

def main():
    """Main function for testing the module."""
    logging.basicConfig(level=logging.INFO)
    create_linux_packages()

if __name__ == "__main__":
    main() 