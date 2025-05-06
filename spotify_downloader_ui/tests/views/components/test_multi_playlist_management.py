"""
Tests for the MultiPlaylistManagement component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import MultiPlaylistManagement
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample data for testing
SAMPLE_PLAYLISTS = [
    {
        "id": "playlist1",
        "name": "Indie Discoveries",
        "description": "A collection of indie tracks I've discovered",
        "is_public": True,
        "owner": "User123",
        "followers": 45,
        "image_url": "https://example.com/playlist1.jpg",
        "tracks_count": 37,
        "track_ids": ["track1", "track2", "track3", "track17", "track21"],
        "date_created": "2023-02-15T10:30:00Z",
        "date_modified": "2023-04-28T14:22:00Z",
        "category": "Discoveries"
    },
    {
        "id": "playlist2",
        "name": "Hidden Gems Vol. 1",
        "description": "Underrated tracks with low popularity but high quality",
        "is_public": False,
        "owner": "User123",
        "followers": 12,
        "image_url": "https://example.com/playlist2.jpg",
        "tracks_count": 25,
        "track_ids": ["track5", "track8", "track11", "track14", "track23"],
        "date_created": "2023-03-10T16:45:00Z",
        "date_modified": "2023-04-30T09:15:00Z",
        "category": "Hidden Gems"
    },
    {
        "id": "playlist3",
        "name": "Chill Electronica",
        "description": "Relaxing electronic music for focus and study",
        "is_public": True,
        "owner": "User123",
        "followers": 89,
        "image_url": "https://example.com/playlist3.jpg",
        "tracks_count": 42,
        "track_ids": ["track7", "track9", "track15", "track22", "track30"],
        "date_created": "2023-01-05T08:20:00Z",
        "date_modified": "2023-05-01T17:40:00Z",
        "category": "Mood"
    },
    {
        "id": "playlist4",
        "name": "Workout Mix",
        "description": "High energy tracks for exercising",
        "is_public": True,
        "owner": "User123",
        "followers": 73,
        "image_url": "https://example.com/playlist4.jpg",
        "tracks_count": 30,
        "track_ids": ["track4", "track12", "track19", "track26", "track33"],
        "date_created": "2023-02-20T11:10:00Z",
        "date_modified": "2023-04-25T15:30:00Z",
        "category": "Activity"
    },
    {
        "id": "playlist5",
        "name": "Hidden Gems Vol. 2",
        "description": "More underrated tracks with amazing potential",
        "is_public": False,
        "owner": "User123",
        "followers": 8,
        "image_url": "https://example.com/playlist5.jpg",
        "tracks_count": 20,
        "track_ids": ["track6", "track13", "track18", "track25", "track31"],
        "date_created": "2023-04-05T13:50:00Z",
        "date_modified": "2023-05-02T10:25:00Z",
        "category": "Hidden Gems"
    }
]

class TestMultiPlaylistManagement(unittest.TestCase):
    """Test case for MultiPlaylistManagement component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        management = MultiPlaylistManagement(self.config_service, self.error_service)
        self.assertIsNotNone(management)
        self.assertIsNotNone(management.widget)
    
    def test_set_playlists(self):
        """Test setting playlists data."""
        management = MultiPlaylistManagement(self.config_service, self.error_service)
        management.set_playlists(SAMPLE_PLAYLISTS)
        
        # Since the mock implementation doesn't have a proper way to verify the data was set
        # correctly, we're just checking that the method doesn't raise an exception
        # In a real test, we'd check the UI elements to ensure they were updated correctly

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=900, height=700)
    
    # Run the test
    management = runner.run_test(MultiPlaylistManagement)
    
    # Load sample data
    management.set_playlists(SAMPLE_PLAYLISTS)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 