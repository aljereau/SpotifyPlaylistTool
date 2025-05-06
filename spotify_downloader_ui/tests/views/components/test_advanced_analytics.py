"""
Tests for the AdvancedAnalytics component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import AdvancedAnalytics
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample data for testing
SAMPLE_ANALYTICS_DATA = {
    "artist_analysis": {
        "artist_frequency": [
            {"artist": "Indie Artist 1", "count": 12, "percentage": 5.2},
            {"artist": "Famous Band", "count": 8, "percentage": 3.5},
            {"artist": "Niche Producer", "count": 7, "percentage": 3.0},
            {"artist": "Unknown Artist", "count": 6, "percentage": 2.6},
            {"artist": "Local Talent", "count": 5, "percentage": 2.2}
        ],
        "collaborations": [
            {"source": "Indie Artist 1", "target": "Famous Band", "count": 3},
            {"source": "Niche Producer", "target": "Unknown Artist", "count": 2},
            {"source": "Famous Band", "target": "Local Talent", "count": 1},
            {"source": "Indie Artist 1", "target": "Niche Producer", "count": 1},
            {"source": "Unknown Artist", "target": "Local Talent", "count": 1}
        ],
        "popularity_distribution": {
            "bins": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "counts": [15, 25, 35, 45, 30, 25, 20, 15, 10, 5]
        }
    },
    "audio_features": {
        "tempo": {
            "bins": [60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160],
            "counts": [5, 10, 25, 40, 50, 45, 35, 20, 10, 5]
        },
        "danceability_energy": [
            {"danceability": 0.65, "energy": 0.72, "count": 5, "name": "Track 1"},
            {"danceability": 0.45, "energy": 0.38, "count": 3, "name": "Track 2"},
            {"danceability": 0.82, "energy": 0.91, "count": 4, "name": "Track 3"},
            {"danceability": 0.25, "energy": 0.20, "count": 2, "name": "Track 4"},
            {"danceability": 0.70, "energy": 0.65, "count": 6, "name": "Track 5"}
        ],
        "feature_averages": {
            "danceability": 0.68,
            "energy": 0.72,
            "speechiness": 0.08,
            "acousticness": 0.25,
            "instrumentalness": 0.15,
            "liveness": 0.18,
            "valence": 0.65
        }
    },
    "genre_distribution": {
        "genres": ["Pop", "Rock", "Electronic", "Hip-Hop", "Jazz", "Other"],
        "counts": [75, 50, 40, 30, 15, 20],
        "percentages": [32.6, 21.7, 17.4, 13.0, 6.5, 8.7]
    },
    "time_analysis": {
        "release_dates": {
            "bins": ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"],
            "counts": [5, 8, 10, 15, 20, 25, 30, 35, 28, 22, 18, 25, 30, 12]
        },
        "addition_timeline": {
            "dates": ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05"],
            "counts": [15, 25, 50, 35, 20]
        }
    },
    "diversity_metrics": {
        "artist_diversity": 0.85,
        "genre_diversity": 0.72,
        "audio_feature_diversity": 0.68,
        "release_year_spread": 0.75
    },
    "user_preferences": {
        "top_artists": ["Indie Artist 1", "Famous Band", "Niche Producer"],
        "top_genres": ["Electronic", "Pop", "Rock"],
        "mood_preference": {
            "energetic": 0.65,
            "calm": 0.35,
            "happy": 0.70,
            "sad": 0.30
        },
        "listening_patterns": {
            "morning": 0.25,
            "afternoon": 0.35,
            "evening": 0.40
        }
    }
}

class TestAdvancedAnalytics(unittest.TestCase):
    """Test case for AdvancedAnalytics component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        analytics = AdvancedAnalytics(self.config_service, self.error_service)
        self.assertIsNotNone(analytics)
        self.assertIsNotNone(analytics.widget)
    
    def test_set_analytics_data(self):
        """Test setting analytics data."""
        analytics = AdvancedAnalytics(self.config_service, self.error_service)
        analytics.set_analytics_data(SAMPLE_ANALYTICS_DATA)
        
        # Since the mock implementation doesn't have a proper way to verify the data was set
        # correctly, we're just checking that the method doesn't raise an exception
        # In a real test, we'd check the UI elements to ensure they were updated correctly

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=1000, height=800)
    
    # Run the test
    analytics = runner.run_test(AdvancedAnalytics)
    
    # Load sample data
    analytics.set_analytics_data(SAMPLE_ANALYTICS_DATA)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 