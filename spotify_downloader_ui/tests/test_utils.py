"""
Test utilities for Spotify Downloader UI tests.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Mock services
class MockConfigService:
    """Mock implementation of ConfigService for testing."""
    
    def __init__(self):
        self.config = {}
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
        return True
    
    def save(self):
        """Save configuration to disk."""
        return True

class MockErrorService:
    """Mock implementation of ErrorService for testing."""
    
    def __init__(self):
        self.last_error = None
        self.last_info = None
    
    def show_error(self, title, message, details=None):
        """Show an error message."""
        self.last_error = {
            "title": title,
            "message": message,
            "details": details
        }
        logging.error(f"ERROR - {title}: {message}")
        return True
    
    def show_info(self, title, message):
        """Show an information message."""
        self.last_info = {
            "title": title,
            "message": message
        }
        logging.info(f"INFO - {title}: {message}")
        return True

# Singleton QApplication for tests
_qapp = None

def get_application():
    """Get the QApplication singleton for tests."""
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance()
        if _qapp is None:
            _qapp = QApplication(sys.argv)
    return _qapp

class ComponentTestRunner:
    """Base class for component tests."""
    
    def __init__(self, width=800, height=600):
        """Initialize the test runner.
        
        Args:
            width: Initial window width
            height: Initial window height
        """
        self.app = get_application()
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
        self.width = width
        self.height = height
    
    def run_test(self, component_class, *args, **kwargs):
        """Run a test for a component.
        
        Args:
            component_class: The component class to test
            *args: Additional positional arguments for the component
            **kwargs: Additional keyword arguments for the component
            
        Returns:
            The component instance
        """
        # Create component with mock services
        if 'config_service' not in kwargs:
            kwargs['config_service'] = self.config_service
        if 'error_service' not in kwargs:
            kwargs['error_service'] = self.error_service
            
        component = component_class(*args, **kwargs)
        
        # Get the actual widget
        if hasattr(component, 'widget'):
            widget = component.widget
        else:
            widget = component
            
        # Set up the widget for display
        widget.resize(self.width, self.height)
        widget.setWindowTitle(f"Test: {component_class.__name__}")
        widget.show()
        
        return component
    
    def exec(self):
        """Run the application event loop."""
        return self.app.exec_() 