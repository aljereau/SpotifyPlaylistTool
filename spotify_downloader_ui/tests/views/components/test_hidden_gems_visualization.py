"""
Tests for the HiddenGemsVisualization component.
"""

import sys
import logging
import unittest
import random
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import HiddenGemsVisualization
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample hidden gems data for testing
def generate_sample_data(track_count=50):
    """Generate sample hidden gems data for testing.
    
    Args:
        track_count: Number of tracks to generate
        
    Returns:
        Dictionary of hidden gems data
    """
    track_scores = []
    
    for i in range(track_count):
        # Generate a random score from 0-100
        score = random.randint(0, 100)
        
        # Create score components
        obscurity = random.randint(0, 100)
        uniqueness = random.randint(0, 100)
        freshness = random.randint(0, 100)
        artist_potential = random.randint(0, 100)
        popularity_inverse = random.randint(0, 100)
        
        track_scores.append({
            "track_id": f"track_{i}",
            "track_name": f"Test Track {i}",
            "total_score": score,
            "components": {
                "obscurity": obscurity,
                "uniqueness": uniqueness,
                "freshness": freshness,
                "artist_potential": artist_potential,
                "popularity_inverse": popularity_inverse
            }
        })
    
    # Generate artist data
    artist_data = []
    for i in range(track_count // 5):  # Fewer artists than tracks
        artist_data.append({
            "id": f"artist_{i}",
            "name": f"Test Artist {i}",
            "popularity": random.randint(0, 100),
            "potential": random.randint(0, 100),
            "track_count": random.randint(1, 5)
        })
    
    return {
        "track_scores": track_scores,
        "artist_data": artist_data
    }

SAMPLE_GEMS_DATA = generate_sample_data()

class TestHiddenGemsVisualization(unittest.TestCase):
    """Test case for HiddenGemsVisualization component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        view = HiddenGemsVisualization(self.config_service, self.error_service)
        self.assertIsNotNone(view)
        self.assertIsNotNone(view.widget)
    
    def test_set_gems_data(self):
        """Test setting gems data."""
        view = HiddenGemsVisualization(self.config_service, self.error_service)
        view.set_gems_data(SAMPLE_GEMS_DATA)
        
        # Since we can't easily check internal state, this test just verifies
        # that the method completes without errors

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=1000, height=800)
    
    # Run the test
    view = runner.run_test(HiddenGemsVisualization)
    
    # Load sample data
    view.set_gems_data(SAMPLE_GEMS_DATA)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 