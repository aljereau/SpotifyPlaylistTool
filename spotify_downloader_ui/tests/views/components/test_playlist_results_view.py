"""
Tests for the PlaylistResultsView component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import PlaylistResultsView
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample playlist data for testing
SAMPLE_PLAYLIST = {
    "collaborative": False,
    "description": "Test playlist description",
    "external_urls": {
        "spotify": "https://open.spotify.com/playlist/test"
    },
    "followers": {
        "href": None,
        "total": 123
    },
    "id": "test_playlist_id",
    "images": [
        {
            "height": 640,
            "url": "https://example.com/image.jpg",
            "width": 640
        }
    ],
    "name": "Test Playlist",
    "owner": {
        "display_name": "Test User",
        "id": "test_user_id"
    },
    "public": True,
    "tracks": {
        "href": "https://api.spotify.com/v1/playlists/test/tracks",
        "items": [
            {
                "added_at": "2023-01-01T12:00:00Z",
                "track": {
                    "album": {
                        "name": "Test Album",
                        "release_date": "2022-01-01",
                        "images": [
                            {
                                "height": 640,
                                "url": "https://example.com/album.jpg",
                                "width": 640
                            }
                        ]
                    },
                    "artists": [
                        {
                            "name": "Test Artist"
                        }
                    ],
                    "duration_ms": 180000,
                    "id": "test_track_id",
                    "name": "Test Track",
                    "popularity": 75
                }
            }
        ],
        "total": 1
    }
}

class TestPlaylistResultsView(unittest.TestCase):
    """Test case for PlaylistResultsView component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        view = PlaylistResultsView(self.config_service, self.error_service)
        self.assertIsNotNone(view)
        self.assertIsNotNone(view.widget)
    
    def test_load_playlist(self):
        """Test loading a playlist."""
        view = PlaylistResultsView(self.config_service, self.error_service)
        view.load_playlist("test_playlist_id", SAMPLE_PLAYLIST)
        
        # Verify that the playlist is loaded
        current_id = view.get_current_playlist_id()
        self.assertEqual(current_id, "test_playlist_id")

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=1000, height=800)
    
    # Run the test
    view = runner.run_test(PlaylistResultsView)
    
    # Load sample data
    view.load_playlist("test_playlist_id", SAMPLE_PLAYLIST)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 