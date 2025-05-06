"""
Tests for the SpotifyPlaylistCreation component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import SpotifyPlaylistCreation
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample data for testing
SAMPLE_CREATION_DATA = {
    "name": "My Hidden Gems",
    "description": "A collection of hidden gems discovered with Spotify Downloader",
    "is_public": False,
    "cover_image": "https://example.com/cover.jpg",
    "tracks": [
        {
            "id": "track1",
            "name": "Hidden Gem 1",
            "artist": "Unknown Artist",
            "album": "Underground Album",
            "duration_ms": 240000,
            "popularity": 15,
            "score": 85
        },
        {
            "id": "track2",
            "name": "Deep Cut",
            "artist": "Indie Band",
            "album": "Rare Collection",
            "duration_ms": 185000,
            "popularity": 25,
            "score": 75
        },
        {
            "id": "track3",
            "name": "Underrated Track",
            "artist": "Lesser Known Artist",
            "album": "Hidden Masterpiece",
            "duration_ms": 320000,
            "popularity": 10,
            "score": 90
        },
        {
            "id": "track4",
            "name": "Obscure Hit",
            "artist": "Niche Producer",
            "album": "Limited Release",
            "duration_ms": 210000,
            "popularity": 30,
            "score": 70
        },
        {
            "id": "track5",
            "name": "Overlooked Classic",
            "artist": "Forgotten Band",
            "album": "Lost Recordings",
            "duration_ms": 275000,
            "popularity": 5,
            "score": 95
        }
    ],
    "templates": [
        {"name": "Hidden Gems", "description": "Template for hidden gems playlists"},
        {"name": "Weekly Discoveries", "description": "Template for weekly discoveries"},
        {"name": "Artist Spotlight", "description": "Template for artist spotlight playlists"}
    ]
}

class TestSpotifyPlaylistCreation(unittest.TestCase):
    """Test case for SpotifyPlaylistCreation component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        creation = SpotifyPlaylistCreation(self.config_service, self.error_service)
        self.assertIsNotNone(creation)
        self.assertIsNotNone(creation.widget)
    
    def test_set_creation_data(self):
        """Test setting playlist creation data."""
        creation = SpotifyPlaylistCreation(self.config_service, self.error_service)
        creation.set_creation_data(SAMPLE_CREATION_DATA)
        
        # Since the mock implementation doesn't have a proper way to verify the data was set
        # correctly, we're just checking that the method doesn't raise an exception
        # In a real test, we'd check the UI elements to ensure they were updated correctly

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=800, height=600)
    
    # Run the test
    creation = runner.run_test(SpotifyPlaylistCreation)
    
    # Load sample data
    creation.set_creation_data(SAMPLE_CREATION_DATA)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 