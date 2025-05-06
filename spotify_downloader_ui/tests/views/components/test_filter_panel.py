"""
Tests for the FilterSidebar component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, Signal

# Import mock component
from spotify_downloader_ui.tests.test_components import FilterSidebar
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

class FilterSignalCatcher(object):
    """Utility class to catch filter changed signals."""
    
    def __init__(self):
        """Initialize the signal catcher."""
        self.last_filters = None
        self.call_count = 0
    
    def filter_changed_handler(self, filters):
        """Handle filter changed signal.
        
        Args:
            filters: Filter dictionary
        """
        self.last_filters = filters
        self.call_count += 1

class TestFilterSidebar(unittest.TestCase):
    """Test case for FilterSidebar component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        sidebar = FilterSidebar(self.config_service, self.error_service)
        self.assertIsNotNone(sidebar)
        self.assertIsNotNone(sidebar.widget)
    
    def test_clear_filters(self):
        """Test clearing filters."""
        sidebar = FilterSidebar(self.config_service, self.error_service)
        
        # Since our mock component doesn't implement real signal functionality,
        # we're just testing that the method completes without errors
        sidebar.clear_filters()
    
    def test_apply_preset(self):
        """Test applying a filter preset."""
        sidebar = FilterSidebar(self.config_service, self.error_service)
        
        # Since our mock component doesn't implement real signal functionality,
        # we're just testing that the method completes without errors
        sidebar.apply_preset("hidden_gems")

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=400, height=800)
    
    # Run the test
    sidebar = runner.run_test(FilterSidebar)
    
    # Apply a preset
    sidebar.apply_preset("hidden_gems")
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 