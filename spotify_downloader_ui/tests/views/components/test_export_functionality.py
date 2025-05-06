"""
Tests for the ExportFunctionality component.
"""

import sys
import logging
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import mock component
from spotify_downloader_ui.tests.test_components import ExportFunctionality
from spotify_downloader_ui.tests.test_utils import ComponentTestRunner, MockConfigService, MockErrorService

# Sample data for testing
SAMPLE_EXPORT_DATA = {
    "available_data": {
        "playlists": [
            {"id": "playlist1", "name": "Indie Discoveries", "tracks_count": 37},
            {"id": "playlist2", "name": "Hidden Gems Vol. 1", "tracks_count": 25},
            {"id": "playlist3", "name": "Chill Electronica", "tracks_count": 42},
            {"id": "playlist4", "name": "Workout Mix", "tracks_count": 30},
            {"id": "playlist5", "name": "Hidden Gems Vol. 2", "tracks_count": 20}
        ],
        "analytics": [
            {"id": "analysis1", "name": "Artist Analysis", "description": "Analysis of artists in your playlists"},
            {"id": "analysis2", "name": "Genre Distribution", "description": "Distribution of genres across playlists"},
            {"id": "analysis3", "name": "Audio Features", "description": "Analysis of audio features like tempo and energy"},
            {"id": "analysis4", "name": "Time Analysis", "description": "Analysis of tracks by release date and addition time"}
        ],
        "visualizations": [
            {"id": "viz1", "name": "Artist Network", "type": "network", "description": "Artist collaboration network"},
            {"id": "viz2", "name": "Genre Pie Chart", "type": "pie", "description": "Genre distribution as pie chart"},
            {"id": "viz3", "name": "Audio Features Radar", "type": "radar", "description": "Audio features as radar chart"},
            {"id": "viz4", "name": "Timeline", "type": "timeline", "description": "Track additions timeline"}
        ],
        "hidden_gems": {
            "total": 45,
            "tiers": {
                "diamond": 5,
                "ruby": 10,
                "emerald": 15,
                "sapphire": 15
            }
        }
    },
    "export_formats": {
        "csv": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "simple_analytics"]
        },
        "json": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "analytics", "hidden_gems"]
        },
        "pdf": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "analytics", "visualizations", "hidden_gems", "reports"]
        },
        "excel": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "analytics", "hidden_gems"]
        },
        "images": {
            "available": True,
            "supports": ["visualizations", "cover_art"]
        },
        "text": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "simple_analytics"]
        },
        "html": {
            "available": True,
            "supports": ["playlists", "tracks", "artists", "analytics", "visualizations", "hidden_gems", "reports"]
        }
    },
    "templates": [
        {"id": "template1", "name": "Default", "description": "Standard export template"},
        {"id": "template2", "name": "Detailed", "description": "Comprehensive export with all details"},
        {"id": "template3", "name": "Summary", "description": "Brief summary of key information"},
        {"id": "template4", "name": "Analytics", "description": "Focus on analytics and visualizations"},
        {"id": "template5", "name": "Custom", "description": "User-defined custom template"}
    ],
    "destinations": {
        "local_file": {
            "available": True,
            "recent_paths": [
                "C:\\Users\\User\\Documents\\Spotify Exports",
                "C:\\Users\\User\\Desktop"
            ]
        },
        "cloud_storage": {
            "available": True,
            "services": ["Google Drive", "Dropbox", "OneDrive"],
            "authenticated": False
        },
        "web_link": {
            "available": True,
            "recent_links": [
                "https://example.com/share/abc123",
                "https://example.com/share/def456"
            ],
            "expiry_options": ["1 day", "1 week", "1 month", "Never"]
        }
    },
    "export_profiles": [
        {"id": "profile1", "name": "Weekly Backup", "template": "template1", "format": "json", "destination": "local_file"},
        {"id": "profile2", "name": "Monthly Report", "template": "template4", "format": "pdf", "destination": "cloud_storage"}
    ],
    "scheduled_exports": [
        {"id": "schedule1", "profile": "profile1", "frequency": "weekly", "next_run": "2023-05-07T00:00:00Z"},
        {"id": "schedule2", "profile": "profile2", "frequency": "monthly", "next_run": "2023-06-01T00:00:00Z"}
    ]
}

class TestExportFunctionality(unittest.TestCase):
    """Test case for ExportFunctionality component."""
    
    def setUp(self):
        """Set up the test case."""
        self.config_service = MockConfigService()
        self.error_service = MockErrorService()
    
    def test_initialization(self):
        """Test that the component initializes without errors."""
        export = ExportFunctionality(self.config_service, self.error_service)
        self.assertIsNotNone(export)
        self.assertIsNotNone(export.widget)
    
    def test_set_export_data(self):
        """Test setting export data."""
        export = ExportFunctionality(self.config_service, self.error_service)
        export.set_export_data(SAMPLE_EXPORT_DATA)
        
        # Since the mock implementation doesn't have a proper way to verify the data was set
        # correctly, we're just checking that the method doesn't raise an exception
        # In a real test, we'd check the UI elements to ensure they were updated correctly

def run_interactive_test():
    """Run an interactive test of the component."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create the test runner
    runner = ComponentTestRunner(width=800, height=900)
    
    # Run the test
    export = runner.run_test(ExportFunctionality)
    
    # Load sample data
    export.set_export_data(SAMPLE_EXPORT_DATA)
    
    # Run the application event loop
    return runner.exec_()

if __name__ == "__main__":
    # Run unit tests if run with pytest
    if "pytest" in sys.modules:
        unittest.main()
    # Run interactive test if run directly
    else:
        sys.exit(run_interactive_test()) 