"""
Tests for the TrackListing component.
"""

import sys
import logging
import unittest
import random
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import TrackListing
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample track data for testing
def generate_sample_tracks(count=50):
    """Generate sample track data for testing.
    
    Args:
        count: Number of tracks to generate
        
    Returns:
        List of track dictionaries
    """
    tracks = []
    
    albums = [
        {"name": "Album 1", "release_date": "2022-01-01", "images": [{"url": "https://example.com/album1.jpg"}]},
        {"name": "Album 2", "release_date": "2021-05-15", "images": [{"url": "https://example.com/album2.jpg"}]},
        {"name": "Album 3", "release_date": "2020-11-30", "images": [{"url": "https://example.com/album3.jpg"}]},
    ]
    
    artists = [
        {"name": "Artist 1"},
        {"name": "Artist 2"},
        {"name": "Artist 3"},
        {"name": "Artist 4"},
    ]
    
    for i in range(count):
        # Select a random album
        album = random.choice(albums)
        
        # Select 1-2 random artists
        track_artists = random.sample(artists, random.randint(1, 2))
        
        # Generate a random duration (2-5 minutes)
        duration_ms = random.randint(120, 300) * 1000
        
        # Generate a random popularity (0-100)
        popularity = random.randint(0, 100)
        
        # Generate a random gem score (0-100)
        gem_score = random.randint(0, 100)
        
        # Create track
        track = {
            "id": f"track_{i}",
            "name": f"Test Track {i}",
            "album": album,
            "artists": track_artists,
            "duration_ms": duration_ms,
            "popularity": popularity,
            "gem_score": gem_score,
            "preview_url": f"https://example.com/preview/{i}.mp3" if random.random() > 0.3 else None,
            "added_at": "2023-01-01T12:00:00Z",
        }
        
        tracks.append(track)
    
    return tracks

SAMPLE_TRACKS = generate_sample_tracks()

class TestTrackListing(unittest.TestCase):
    """Test case for TrackListing component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        view = TrackListing(self.config_service, self.error_service)
        self.assertIsNotNone(view)
        self.assertIsNotNone(view.widget)
    
    def test_set_tracks(self):
        """Test setting track data."""
        view = TrackListing(self.config_service, self.error_service)
        view.set_tracks(SAMPLE_TRACKS)
        
        # Since the model doesn't expose the track count directly, we're just
        # testing that the method completes without errors

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=1000, height=800)
    
    # Run the test
    view = runner.run_test(TrackListing)
    
    # Load sample data
    view.set_tracks(SAMPLE_TRACKS)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 