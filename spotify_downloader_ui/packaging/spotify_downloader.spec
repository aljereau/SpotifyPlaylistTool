# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Spotify Downloader.

This file defines how PyInstaller should bundle the application.
"""

import sys
import os
from pathlib import Path

# Application name and metadata
block_cipher = None
app_name = "Spotify Downloader"
app_version = "1.0.0"
app_icon = "spotify_downloader_ui/assets/icons/app_icon"
main_script = "spotify_downloader_ui/main.py"

# Platform-specific settings
if sys.platform.startswith('win'):
    app_icon += ".ico"
    exe_extension = ".exe"
    separator = ";"
elif sys.platform.startswith('darwin'):
    app_icon += ".icns"
    exe_extension = ""
    separator = ":"
else:  # Linux
    app_icon += ".png"
    exe_extension = ""
    separator = ":"

# Make sure the icon file exists
if not os.path.exists(app_icon):
    app_icon = None

# Additional data files to include
additional_data = [
    # Assets directory
    ('spotify_downloader_ui/assets', 'spotify_downloader_ui/assets'),
    
    # Documentation
    ('README.md', '.'),
    ('LICENSE', '.'),
    
    # Configuration files
    ('ui_requirements.txt', '.'),
    ('requirements.txt', '.'),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'PyQt6.QtSvg',
    'matplotlib',
    'numpy',
    'pandas',
    'spotipy',
    'requests',
    'pkg_resources',
]

a = Analysis(
    [main_script],
    pathex=[os.path.abspath(os.getcwd())],
    binaries=[],
    datas=additional_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Create macOS application bundle if on Mac
if sys.platform.startswith('darwin'):
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon=app_icon,
        bundle_identifier='com.spotifydownloader.app',
        info_plist={
            'CFBundleShortVersionString': app_version,
            'CFBundleVersion': app_version,
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Support Dark Mode
            'LSMinimumSystemVersion': '10.14',  # Minimum macOS version
            'CFBundleDisplayName': app_name,
            'CFBundleName': app_name,
            'CFBundleExecutable': app_name,
            'LSUIElement': False,  # Not a background app
            'NSHumanReadableCopyright': '© 2023 Spotify Downloader Team',
        },
    ) 