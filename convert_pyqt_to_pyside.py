#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert a PyQt6-based project to PySide6.
This script updates imports and performs necessary replacements for compatibility.
"""

import os
import re
import glob

# File types to process
FILE_EXTENSIONS = ['.py']

# Project directories to process, excluding venv
PROJECT_DIRS = [
    'src',
    'spotify_downloader_ui'
]

# Conversion rules for imports
IMPORT_CONVERSIONS = [
    (r'from PyQt6', 'from PySide6'),
    (r'import PyQt6', 'import PySide6'),
    (r'PyQt6\.', 'PySide6.'),
]

# Conversion rules for signals and slots
SIGNAL_SLOT_CONVERSIONS = [
    (r'pyqtSignal', 'Signal'),
    (r'pyqtSlot', 'Slot'),
]

# Conversion rules for QAction import location
QACTION_IMPORT_CONVERSIONS = [
    (r'from PySide6\.QtWidgets import (.*?)QAction(.*?)', r'from PySide6.QtWidgets import \1\2'),
    (r'from PySide6\.QtWidgets import QAction', r'from PySide6.QtGui import QAction'),
    (r'from PySide6\.QtWidgets import (.*?), QAction(.*?)', r'from PySide6.QtWidgets import \1\2\nfrom PySide6.QtGui import QAction'),
]

# Conversion for exec() method
EXEC_CONVERSIONS = [
    (r'\.exec\(\)', '.exec_()'),
]

# Conversion for mouse event methods
MOUSE_EVENT_CONVERSIONS = [
    (r'\.pos\(\)', '.position().toPoint()'),
    (r'\.globalPos\(\)', '.globalPosition().toPoint()'),
    (r'\.x\(\)', '.position().x()'),
    (r'\.y\(\)', '.position().y()'),
]

# QApplication attributes for high DPI scaling that are no longer needed/available
HIGH_DPI_CONVERSIONS = [
    (r'QApplication\.setAttribute\(Qt\.AA_EnableHighDpiScaling.*?\)', '# High DPI scaling is enabled by default in PySide6'),
    (r'QApplication\.setAttribute\(Qt\.AA_UseHighDpiPixmaps.*?\)', '# High DPI pixmaps are enabled by default in PySide6'),
    (r'QApplication\.setAttribute\(Qt\.AA_DisableHighDpiScaling.*?\)', '# High DPI scaling cannot be disabled in PySide6'),
]

def should_process_file(file_path):
    """Check if we should process this file."""
    # Check if file has a supported extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in FILE_EXTENSIONS:
        return False
    
    # Skip the conversion script itself
    if os.path.basename(file_path) == os.path.basename(__file__):
        return False
    
    # Skip files in venv or any other excluded directories
    if 'venv' in file_path or 'env' in file_path:
        return False
    
    return True

def apply_regex_replacements(content, replacements):
    """Apply regex replacements to content."""
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    return content

def convert_file(file_path):
    """Convert a single file from PyQt6 to PySide6."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply all conversions
    content = apply_regex_replacements(content, IMPORT_CONVERSIONS)
    content = apply_regex_replacements(content, SIGNAL_SLOT_CONVERSIONS)
    content = apply_regex_replacements(content, QACTION_IMPORT_CONVERSIONS)
    content = apply_regex_replacements(content, EXEC_CONVERSIONS)
    content = apply_regex_replacements(content, MOUSE_EVENT_CONVERSIONS)
    content = apply_regex_replacements(content, HIGH_DPI_CONVERSIONS)
    
    # Special handling for QAction imports
    if "QAction" in content and "from PySide6.QtGui import" in content and "from PySide6.QtGui import QAction" not in content:
        content = re.sub(
            r'from PySide6\.QtGui import (.*?)\n',
            r'from PySide6.QtGui import \1, QAction\n',
            content,
            count=1
        )
    
    # Write back the modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Converted {file_path}")

def process_directory(directory):
    """Process all Python files in a directory."""
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path) and should_process_file(path):
            convert_file(path)
        elif os.path.isdir(path) and file != 'venv' and file != '.git':
            process_directory(path)

def find_special_files():
    """Find and process special files like .ui or .qrc files."""
    # Find and report .ui files
    ui_files = glob.glob('**/*.ui', recursive=True)
    if ui_files:
        print("\nUI Files found:")
        print("Please note that with PySide6, UI files should be loaded with QUiLoader instead of PyQt6's uic module.")
        print("See: https://doc.qt.io/qtforpython-6/tutorials/basictutorial/uifiles.html")
        for ui_file in ui_files:
            print(f"  - {ui_file}")
    
    # Find and report .qrc files
    qrc_files = glob.glob('**/*.qrc', recursive=True)
    if qrc_files:
        print("\nQRC Files found:")
        print("Please note that with PySide6, resource files should be compiled with pyside6-rcc instead of pyrcc6.")
        print("See: https://doc.qt.io/qtforpython-6/tutorials/basictutorial/qrcfiles.html")
        for qrc_file in qrc_files:
            print(f"  - {qrc_file}")

def main():
    """Main function to convert the project."""
    print("Converting project from PyQt6 to PySide6...")
    
    # Process each project directory
    for dir_name in PROJECT_DIRS:
        if os.path.isdir(dir_name):
            process_directory(dir_name)
    
    # Check for .ui and .qrc files
    find_special_files()
    
    print("\nConversion completed!")
    print("Please review the changes and verify the application functionality.")
    print("Some manual changes might still be needed, especially for:")
    print("  - Complex enum usages")
    print("  - Custom class property getters/setters")
    print("  - Complex UI loading code")
    print("  - Third-party dependencies that expect PyQt6")

if __name__ == "__main__":
    main() 