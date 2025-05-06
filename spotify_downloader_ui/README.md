# Spotify Downloader UI

A modern, user-friendly graphical interface for the Spotify Playlist Extractor tool.

## Overview

This UI component provides a graphical interface to the command-line Spotify Playlist Extractor, making it easier to:

- Extract and analyze tracks from Spotify playlists
- Process multiple playlists
- Discover "hidden gems" using the built-in scoring system
- Visualize playlist data
- Create Spotify playlists from discovered tracks

## Architecture

The UI follows an MVC (Model-View-Controller) architecture with a service layer to isolate backend functionality:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                              SPOTIFY DOWNLOADER UI                            │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                                UI LAYER                                       │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Main Window    │  │  Playlist Input     │  │  Results Display       │    │
│  │  (QMainWindow)  │  │  (QWidget)          │  │  (QWidget)             │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Progress View  │  │  Settings Dialog    │  │  Hidden Gems View      │    │
│  │  (QWidget)      │  │  (QDialog)          │  │  (QWidget)             │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             CONTROLLER LAYER                                  │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  App Controller │  │  Playlist           │  │  Settings              │    │
│  │                 │  │  Controller         │  │  Controller            │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             SERVICE LAYER                                     │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Playlist       │  │  Spotify            │  │  Config                │    │
│  │  Service        │  │  Service            │  │  Service               │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐                                │
│  │                 │  │                     │                                │
│  │  Analysis       │  │  Error Handling     │                                │
│  │  Service        │  │  Service            │                                │
│  │                 │  │                     │                                │
│  └─────────────────┘  └─────────────────────┘                                │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                             MODEL LAYER                                       │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │                 │  │                     │  │                        │    │
│  │  Playlist       │  │  Track              │  │  Settings              │    │
│  │  Model          │  │  Model              │  │  Model                 │    │
│  │                 │  │                     │  │                        │    │
│  └─────────────────┘  └─────────────────────┘  └────────────────────────┘    │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                            BACKEND (EXISTING)                                 │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                         │  │
│  │                    spotify_playlist_extractor.py                        │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **UI Layer**
   - MainWindow: The main application window
   - PlaylistInputView: Input for playlist URLs
   - ProcessingView: Processing status and progress
   - ResultsView: Display of extracted tracks and analysis
   - SettingsDialog: Application configuration

2. **Service Layer**
   - PlaylistService: Interfaces with backend playlist extraction
   - SpotifyService: Handles Spotify API operations
   - ConfigService: Manages application settings
   - ErrorService: Standardized error handling

3. **Utilities**
   - Threading: Background processing for non-UI operations
   - Signals/Slots: Qt communication mechanism
   - Error handling: Consistent error display

## Features

### Core Features
- **Playlist Input**: Validate and process Spotify playlist URLs
- **Progress Tracking**: Visual feedback during extraction
- **Settings**: Configure application behavior and appearance

### Process Visualization
- **Task Queue Management**: Visualize and manage processing tasks
- **Multi-level Progress Indicators**: Track progress across various operations
- **Real-time Logging**: Advanced log viewing with filtering and search
- **Operation Control**: Throttling, pause/resume, and cancel functionality

### Results Display
- **Playlist Results View**: Comprehensive view of playlist data, metadata, and statistics
- **Hidden Gems Analysis**: Interactive scoring system with tiered gem categories and visualizations
- **Track Listing**: Detailed track information with audio previews and album art
- **Advanced Filtering**: Complex filtering options with presets and combination logic

### (Coming Soon) Advanced Features
- **Playlist Creation**: Create Spotify playlists from discovered tracks
- **Analytics**: Advanced visualization of playlist statistics
- **Export**: Save results in various formats

## Requirements

- Python 3.8+
- PyQt6
- PyQtChart
- Spotipy
- Other dependencies listed in `ui_requirements.txt`

## Usage

Run the UI application:

```bash
python -m spotify_downloader_ui.main
```

## Configuration

Configuration is stored using Qt's QSettings mechanism. On first run, default settings are created:

- Output directory: `~/SpotifyDownloader` (configurable)
- Theme: Light (configurable)
- Hidden Gems defaults:
  - Min popularity: 5
  - Max popularity: 40
  - Min score: 20

## Development

### Adding New Features

1. Service Layer: Add functionality to appropriate service classes
2. UI Layer: Create or modify view components
3. Connect with signals/slots mechanism
4. Update tests

### Project Structure

```
spotify_downloader_ui/
├── __init__.py          # Package initialization
├── app.py               # Application setup
├── main.py              # Entry point
├── architecture.md      # Architecture documentation
├── README.md            # This file
├── assets/              # UI assets and resources
├── controllers/         # UI controllers
├── models/              # Data models
├── services/            # Service layer
│   ├── __init__.py
│   ├── config_service.py
│   ├── error_service.py
│   ├── playlist_service.py
│   └── spotify_service.py
└── views/               # UI views
    ├── __init__.py
    ├── main_window.py
    ├── playlist_input_view.py
    ├── processing_view.py
    ├── results_view.py
    ├── settings_dialog.py
    └── components/      # Reusable UI components
        ├── __init__.py
        ├── multi_level_progress.py
        ├── enhanced_progress_bar.py
        ├── task_queue_manager.py
        ├── log_viewer.py
        ├── operation_control.py
        ├── playlist_results_view.py
        ├── hidden_gems_visualization.py
        ├── track_listing.py
        └── filter_panel.py
```

## License

This component is part of the Spotify Downloader project and is licensed under the MIT License.

## Acknowledgments

- Original Spotify Playlist Extractor backend code
- PyQt6 framework
- Spotipy library for Spotify API integration 