"""
Run tests for Phase 5 components.
"""

import sys
import os
import logging
import unittest
from PySide6.QtWidgets import QApplication

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import test components
from spotify_downloader_ui.tests.views.components.test_spotify_playlist_creation import TestSpotifyPlaylistCreation
from spotify_downloader_ui.tests.views.components.test_multi_playlist_management import TestMultiPlaylistManagement
from spotify_downloader_ui.tests.views.components.test_advanced_analytics import TestAdvancedAnalytics
from spotify_downloader_ui.tests.views.components.test_export_functionality import TestExportFunctionality

# Import mock components for visual tests
from spotify_downloader_ui.tests.test_components import (
    SpotifyPlaylistCreation, 
    MultiPlaylistManagement,
    AdvancedAnalytics,
    ExportFunctionality
)
from spotify_downloader_ui.tests.test_utils import (
    ComponentTestRunner, 
    MockConfigService, 
    MockErrorService
)

# Sample data for testing
from spotify_downloader_ui.tests.views.components.test_advanced_analytics import SAMPLE_ANALYTICS_DATA
from spotify_downloader_ui.tests.views.components.test_export_functionality import SAMPLE_EXPORT_DATA

def run_unit_tests():
    """Run unit tests for Phase 5 components."""
    test_suite = unittest.TestSuite()
    
    # Add tests for each component
    test_suite.addTest(unittest.makeSuite(TestSpotifyPlaylistCreation))
    test_suite.addTest(unittest.makeSuite(TestMultiPlaylistManagement))
    test_suite.addTest(unittest.makeSuite(TestAdvancedAnalytics))
    test_suite.addTest(unittest.makeSuite(TestExportFunctionality))
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_visual_tests():
    """Run visual tests for Phase 5 components."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Check if component name was specified
    if len(sys.argv) > 1:
        component_name = sys.argv[1]
        
        # Create services
        config_service = MockConfigService()
        error_service = MockErrorService()
        
        # Create runner
        runner = ComponentTestRunner(width=800, height=600)
        
        # Run specific component test
        if component_name == "playlist_creation":
            component = SpotifyPlaylistCreation(config_service, error_service)
            sample_data = {
                "tracks": [
                    {"id": "track1", "name": "Track 1", "artist": "Artist 1"},
                    {"id": "track2", "name": "Track 2", "artist": "Artist 2"},
                    {"id": "track3", "name": "Track 3", "artist": "Artist 3"}
                ]
            }
            component.set_creation_data(sample_data)
            return runner.run_component_in_window(component, "Spotify Playlist Creation")
        
        elif component_name == "multi_playlist":
            component = MultiPlaylistManagement(config_service, error_service)
            sample_playlists = []
            for i in range(1, 6):
                playlist = {
                    "id": f"playlist{i}",
                    "name": f"Sample Playlist {i}",
                    "description": f"Description for playlist {i}",
                    "is_public": i % 2 == 0,
                    "tracks_count": 20 + i * 5
                }
                sample_playlists.append(playlist)
            component.set_playlists(sample_playlists)
            return runner.run_component_in_window(component, "Multi-Playlist Management")
        
        elif component_name == "analytics":
            component = AdvancedAnalytics(config_service, error_service)
            component.set_analytics_data(SAMPLE_ANALYTICS_DATA)
            return runner.run_component_in_window(component, "Advanced Analytics")
        
        elif component_name == "export":
            component = ExportFunctionality(config_service, error_service)
            component.set_export_data(SAMPLE_EXPORT_DATA)
            return runner.run_component_in_window(component, "Export Functionality")
        
        else:
            print(f"Unknown component: {component_name}")
            print("Available components: playlist_creation, multi_playlist, analytics, export")
            return 1
    
    else:
        # Run all components in tabs
        app = QApplication([])
        
        # Create services
        config_service = MockConfigService()
        error_service = MockErrorService()
        
        # Create runner for all components
        runner = ComponentTestRunner(width=1000, height=800)
        
        # Add components to tabs
        runner.add_component_tab("Playlist Creation", SpotifyPlaylistCreation(config_service, error_service))
        runner.add_component_tab("Multi-Playlist", MultiPlaylistManagement(config_service, error_service))
        runner.add_component_tab("Analytics", AdvancedAnalytics(config_service, error_service))
        runner.add_component_tab("Export", ExportFunctionality(config_service, error_service))
        
        # Set sample data
        runner.get_component(0).set_creation_data({
            "tracks": [
                {"id": "track1", "name": "Track 1", "artist": "Artist 1"},
                {"id": "track2", "name": "Track 2", "artist": "Artist 2"},
                {"id": "track3", "name": "Track 3", "artist": "Artist 3"}
            ]
        })
        
        sample_playlists = []
        for i in range(1, 6):
            playlist = {
                "id": f"playlist{i}",
                "name": f"Sample Playlist {i}",
                "description": f"Description for playlist {i}",
                "is_public": i % 2 == 0,
                "tracks_count": 20 + i * 5
            }
            sample_playlists.append(playlist)
        runner.get_component(1).set_playlists(sample_playlists)
        
        runner.get_component(2).set_analytics_data(SAMPLE_ANALYTICS_DATA)
        runner.get_component(3).set_export_data(SAMPLE_EXPORT_DATA)
        
        return runner.exec_()

if __name__ == "__main__":
    # Check if integration or unit test mode is specified
    if len(sys.argv) > 1 and sys.argv[1] == "--unit":
        # Run only unit tests
        success = run_unit_tests()
        sys.exit(0 if success else 1)
    else:
        # Run visual tests
        sys.exit(run_visual_tests()) 