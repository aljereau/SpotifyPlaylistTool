# Spotify Downloader UI Testing

This document describes the testing approach for the Spotify Downloader UI components.

## Test Structure

The test framework is organized as follows:

```
spotify_downloader_ui/tests/
├── __init__.py
├── test_utils.py                 # Test utilities and mock services
├── test_components.py            # Mock component implementations for testing
├── run_phase4_tests.py           # Test runner for Phase 4 components
├── run_phase5_tests.py           # Test runner for Phase 5 components
├── test_component.py             # CLI for testing individual components
├── TESTING.md                    # This documentation file
├── README.md                     # General test documentation
└── views/
    └── components/               # Tests for individual components
        ├── test_playlist_results_view.py         # Phase 4 component test
        ├── test_hidden_gems_visualization.py     # Phase 4 component test
        ├── test_track_listing.py                 # Phase 4 component test 
        ├── test_filter_panel.py                  # Phase 4 component test
        ├── test_spotify_playlist_creation.py     # Phase 5 component test
        ├── test_multi_playlist_management.py     # Phase 5 component test
        ├── test_advanced_analytics.py            # Phase 5 component test
        └── test_export_functionality.py          # Phase 5 component test
```

## Testing Approach

The testing framework uses a combination of unit tests and interactive visual tests:

1. **Unit Tests**: Basic tests to verify component initialization and functionality
2. **Interactive Tests**: Visual tests that display the UI components with sample data
3. **Integration Tests**: Combined views of all components from a particular phase

## Mock Components

Instead of using the actual UI components, which may have dependencies that are difficult to satisfy in a test environment, we use mock implementations in `test_components.py`. These mock components provide the same interface but simplified functionality.

The mock components include:

1. **Phase 4 Components**:
   - `PlaylistResultsView`: Shows playlist metadata and results
   - `HiddenGemsVisualization`: Displays hidden gems with visualization
   - `TrackListing`: Shows a list of tracks with details
   - `FilterSidebar`: Provides filtering options

2. **Phase 5 Components**:
   - `SpotifyPlaylistCreation`: Interface for creating Spotify playlists
   - `MultiPlaylistManagement`: Management of multiple playlists
   - `AdvancedAnalytics`: Advanced analytics visualizations
   - `ExportFunctionality`: Export options and functionality

## Mock Services

To avoid dependencies on the backend and other services, we use mock implementations of:

- `MockConfigService`: Provides configuration settings
- `MockErrorService`: Handles error display

## Sample Data

Each component test file includes sample data structures that mimic real data:

- `SAMPLE_PLAYLIST`: Sample playlist data for testing
- `SAMPLE_GEMS_DATA`: Sample hidden gems data
- `SAMPLE_TRACKS`: Sample track data
- `SAMPLE_CREATION_DATA`: Sample playlist creation data
- `SAMPLE_PLAYLISTS`: Sample collection of playlists
- `SAMPLE_ANALYTICS_DATA`: Sample analytics data
- `SAMPLE_EXPORT_DATA`: Sample export configuration data

## Running Tests

### Unit Tests

Run unit tests for each phase:

```bash
# Run Phase 4 unit tests
python -m spotify_downloader_ui.tests.run_phase4_tests --unit

# Run Phase 5 unit tests
python -m spotify_downloader_ui.tests.run_phase5_tests --unit
```

### Integration Tests

Run integration tests that show all components of a phase together:

```bash
# Run Phase 4 integration test
python -m spotify_downloader_ui.tests.run_phase4_tests --integration

# Run Phase 5 integration test
python -m spotify_downloader_ui.tests.run_phase5_tests --integration
```

### Individual Component Tests

Test individual components:

```bash
# Test individual Phase 4 component
python -m spotify_downloader_ui.tests.test_component playlist_results_view
python -m spotify_downloader_ui.tests.test_component hidden_gems_visualization
python -m spotify_downloader_ui.tests.test_component track_listing
python -m spotify_downloader_ui.tests.test_component filter_sidebar

# Test individual Phase 5 component
python -m spotify_downloader_ui.tests.test_component spotify_playlist_creation
python -m spotify_downloader_ui.tests.test_component multi_playlist_management
python -m spotify_downloader_ui.tests.test_component advanced_analytics
python -m spotify_downloader_ui.tests.test_component export_functionality
```

## Testing Guidelines

1. **Always Write Tests First**: Follow a test-driven development approach
2. **Visual Verification**: All UI components should have visual tests
3. **Integration Testing**: Ensure components work together
4. **Edge Cases**: Test boundary conditions (empty data, large datasets)
5. **Error Handling**: Verify that components handle errors gracefully

## Known Limitations

1. Mock components don't implement all functionality of real components
2. Visual testing requires manual validation
3. Backend integration tests are not included in this framework
4. Some component interactions may not be fully tested

## Future Improvements

1. Add automated screenshot comparison for visual tests
2. Implement more comprehensive edge case testing
3. Add performance testing for large datasets
4. Implement accessibility testing
5. Add integration tests with the actual backend using a mock server

## Validation Evidence

After running tests, capture screenshots and test results to document in the corresponding Phase Progress document as evidence of validation. 