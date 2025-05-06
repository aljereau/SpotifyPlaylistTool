"""
Test individual components from the command line.

This script allows users to test individual components by name.
Usage: python -m spotify_downloader_ui.tests.test_component <component_name>

Available components:
- playlist_results_view
- hidden_gems_visualization
- track_listing
- filter_sidebar
"""

import sys
import logging
import importlib
from PySide6.QtWidgets import QApplication
import argparse

from spotify_downloader_ui.tests.test_utils import get_application

def main():
    """Run the test for the specified component."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Get component name from command line
    if len(sys.argv) < 2:
        print("Usage: python -m spotify_downloader_ui.tests.test_component <component_name>")
        print("\nAvailable components:")
        print("- playlist_results_view")
        print("- hidden_gems_visualization")
        print("- track_listing")
        print("- filter_sidebar")
        return 1
    
    component_name = sys.argv[1].lower()
    
    # Map component name to module
    component_modules = {
        "playlist_results_view": "test_playlist_results_view",
        "hidden_gems_visualization": "test_hidden_gems_visualization",
        "track_listing": "test_track_listing",
        "filter_sidebar": "test_filter_panel",
    }
    
    # Check if component is valid
    if component_name not in component_modules:
        print(f"Error: Unknown component '{component_name}'")
        print("\nAvailable components:")
        print("- playlist_results_view")
        print("- hidden_gems_visualization")
        print("- track_listing")
        print("- filter_sidebar")
        return 1
    
    # Import the module
    module_name = f"spotify_downloader_ui.tests.views.components.{component_modules[component_name]}"
    try:
        module = importlib.import_module(module_name)
        
        # Run the interactive test
        if hasattr(module, "run_interactive_test"):
            # Initialize QApplication
            app = get_application()
            
            # Run the test
            print(f"Running interactive test for {component_name}...")
            return module.run_interactive_test()
        else:
            print(f"Error: Module {module_name} does not have a run_interactive_test function")
            return 1
    except ImportError as e:
        print(f"Error importing module {module_name}: {e}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an interactive test for a UI component")
    parser.add_argument("component", choices=[
        # Phase 4 components
        "playlist_results_view", 
        "hidden_gems_visualization", 
        "track_listing", 
        "filter_sidebar",
        # Phase 5 components
        "spotify_playlist_creation",
        "multi_playlist_management",
        "advanced_analytics",
        "export_functionality",
    ], help="The component to test")
    parser.add_argument("--width", type=int, default=800, help="Window width")
    parser.add_argument("--height", type=int, default=600, help="Window height")
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the component test
    exit_code = 0
    
    try:
        if args.component == "playlist_results_view":
            from spotify_downloader_ui.tests.views.components.test_playlist_results_view import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "hidden_gems_visualization":
            from spotify_downloader_ui.tests.views.components.test_hidden_gems_visualization import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "track_listing":
            from spotify_downloader_ui.tests.views.components.test_track_listing import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "filter_sidebar":
            from spotify_downloader_ui.tests.views.components.test_filter_panel import run_interactive_test
            exit_code = run_interactive_test()
        # Phase 5 components
        elif args.component == "spotify_playlist_creation":
            from spotify_downloader_ui.tests.views.components.test_spotify_playlist_creation import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "multi_playlist_management":
            from spotify_downloader_ui.tests.views.components.test_multi_playlist_management import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "advanced_analytics":
            from spotify_downloader_ui.tests.views.components.test_advanced_analytics import run_interactive_test
            exit_code = run_interactive_test()
        elif args.component == "export_functionality":
            from spotify_downloader_ui.tests.views.components.test_export_functionality import run_interactive_test
            exit_code = run_interactive_test()
        else:
            print(f"Error: Unknown component '{args.component}'")
            exit_code = 1
    except Exception as e:
        print(f"Error running test for {args.component}: {e}")
        exit_code = 1
    
    sys.exit(exit_code) 