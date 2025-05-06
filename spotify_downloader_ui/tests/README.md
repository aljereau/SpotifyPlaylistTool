# Spotify Downloader UI Test Framework

This directory contains the test framework for the Spotify Downloader UI components.

## Overview

The test framework provides:

1. **Unit Tests**: Automated tests to verify component functionality
2. **Interactive Visual Tests**: Manual tests to verify component appearance
3. **Integration Tests**: Tests to verify components working together
4. **Mock Components**: Simplified implementations of UI components for testing

## Test Organization

- `run_phase4_tests.py`: Test runner for Phase 4 components
- `run_phase5_tests.py`: Test runner for Phase 5 components
- `test_component.py`: CLI tool for testing individual components
- `test_components.py`: Mock implementations of UI components
- `test_utils.py`: Utility functions and mock services
- `views/components/`: Test modules for individual components

## Running Tests

### Phase 4 Components (Results Display)

```bash
# Run all tests
python -m spotify_downloader_ui.tests.run_phase4_tests

# Run only unit tests
python -m spotify_downloader_ui.tests.run_phase4_tests --unit

# Run only integration test
python -m spotify_downloader_ui.tests.run_phase4_tests --integration
```

### Phase 5 Components (Advanced Features)

```bash
# Run all tests
python -m spotify_downloader_ui.tests.run_phase5_tests

# Run only unit tests
python -m spotify_downloader_ui.tests.run_phase5_tests --unit

# Run only integration test
python -m spotify_downloader_ui.tests.run_phase5_tests --integration
```

### Testing Individual Components

```bash
# Test a specific component
python -m spotify_downloader_ui.tests.test_component COMPONENT_NAME
```

Available components:

#### Phase 4 Components:
- `playlist_results_view`
- `hidden_gems_visualization`
- `track_listing`
- `filter_sidebar`

#### Phase 5 Components:
- `spotify_playlist_creation`
- `multi_playlist_management`
- `advanced_analytics`
- `export_functionality`

## Mock Services

The test framework provides mock implementations of services:

- `MockConfigService`: Configuration service
- `MockErrorService`: Error handling service

## Sample Data

Each component test module includes sample data:

```python
# Example from test_playlist_results_view.py
SAMPLE_PLAYLIST = {
    "name": "My Playlist",
    "description": "A sample playlist for testing",
    "tracks": [
        {
            "id": "track1",
            "name": "Song 1",
            "artist": "Artist 1",
            # ...
        },
        # ...
    ]
}
```

## Visual Testing

When you run visual tests, a window will appear showing the component with sample data. You can interact with the component to verify its functionality.

## Creating New Tests

To add a new component test:

1. Create a new test module in `views/components/`
2. Define sample data
3. Create unit tests
4. Add an interactive test function
5. Update `test_component.py` to include the new component

## Documentation

See the following files for more information:

- [TESTING.md](TESTING.md): Detailed testing documentation
- [README.md](../README.md): Project overview 