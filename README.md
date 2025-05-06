# Spotify Playlist Extractor

A powerful tool for extracting and analyzing track information from Spotify playlists, with a focus on discovering "hidden gems" - tracks with high potential but low popularity.

## Features

- **Extract Track Information**: Get detailed information about all tracks in a Spotify playlist
- **Multiple Playlist Processing**: Analyze multiple playlists in one go
- **Hidden Gems Analysis**: Discover lesser-known but high-quality tracks using a sophisticated scoring system
- **Spotify Playlist Creation**: Create new Spotify playlists from discovered hidden gems
- **Comprehensive Analytics**: Generate detailed analytics about tracks, artists, and popularity distribution
- **Multi-Market Support**: Handle playlists from different Spotify markets
- **Batch Processing**: Process playlists in batches with retry capability
- **Modern UI**: Graphical user interface for easy interaction with all features
- **Audio Download**: Download tracks from Spotify playlists using YouTube as a source
- **Format Options**: Download audio in multiple formats (MP3, M4A, OPUS, WAV)
- **Metadata Tagging**: Automatically tag downloaded files with correct metadata (artist, title, album)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/aljereau/Spotify-Downloader.git
   cd Spotify-Downloader
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

   For the UI, install the additional dependencies:
   ```
   pip install -r ui_requirements.txt
   ```

3. Create a `.env` file in the project root with your Spotify API credentials:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_USERNAME=your_username
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

4. Install external dependencies for downloading:
   - **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or install via package manager
     - Windows: `choco install ffmpeg`
     - macOS: `brew install ffmpeg`
     - Ubuntu: `sudo apt install ffmpeg`
   - **yt-dlp**: Should be automatically installed via requirements.txt

## Usage

### Command-Line Interface

Process a single playlist:
```bash
python src/spotify_playlist_extractor.py https://open.spotify.com/playlist/your_playlist_id
```

Process multiple playlists:
```bash
python src/spotify_playlist_extractor.py https://open.spotify.com/playlist/id1 https://open.spotify.com/playlist/id2
```

Process playlists from a file:
```bash
python src/spotify_playlist_extractor.py --file playlists.txt
```

Download tracks from a playlist:
```bash
python src/spotify_downloader.py https://open.spotify.com/playlist/your_playlist_id
```

Download tracks with custom options:
```bash
python src/spotify_downloader.py --format mp3 --max-workers 8 --skip-existing -o "Music/Downloads" https://open.spotify.com/playlist/your_playlist_id
```

### Graphical User Interface

Launch the UI application:
```bash
python -m spotify_downloader_ui.main
```

The UI provides a user-friendly way to:
- Input and validate Spotify playlist URLs
- Configure extraction settings
- Monitor extraction progress
- View and explore results
- Manage Spotify API credentials
- Download tracks with custom settings
- Monitor download progress in real-time

### Hidden Gems Analysis

Generate a hidden gems report:
```bash
python src/spotify_playlist_extractor.py URL --hidden-gems
```

Customize hidden gems criteria:
```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --min-pop=5 --max-pop=35 --min-score=25 --top-gems=20
```

### Playlist Creation

Create a Spotify playlist from hidden gems:
```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --create-playlist
```

Customize the created playlist:
```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --create-playlist --playlist-name "Amazing Underground Tracks" --playlist-description "My favorite undiscovered songs" --playlist-public
```

## How Hidden Gems Scoring Works

Tracks are scored on a 0-50 point scale based on several factors:

- **Popularity**: Lower popularity tracks get higher scores (0-20 points)
- **Artist Collaboration**: Tracks with multiple artists get a bonus (0-10 points)
- **Track Duration**: Extended tracks (5-9 minutes) get a bonus (0-10 points)
- **Release Type**: Focused releases (singles/EPs with fewer tracks) get a bonus (0-10 points)

## Output Structure

Each playlist gets its own folder with:
- `playlist_name_tracks.txt`: Detailed track information
- `playlist_name_links.txt`: Track links for easy sharing/playing
- `playlist_name_analytics.txt`: Analytics report with detailed metrics
- `playlist_name_hidden_gems_*.txt`: Hidden gems report (if requested)
- `Downloads/`: Directory for downloaded tracks

## Project Structure

The project is organized into two main components:

1. **Backend (Command-Line Tool)**
   - Located in the `src/` directory
   - Core playlist extraction and analysis logic
   - Track downloading functionality

2. **UI (Graphical Interface)**
   - Located in the `spotify_downloader_ui/` directory
   - Modern PyQt6-based graphical interface
   - Follows MVC architecture pattern
   - See [UI Documentation](spotify_downloader_ui/README.md) for details

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Spotipy](https://github.com/plamere/spotipy) - The Python library for the Spotify Web API
- [PySide6](https://doc.qt.io/qtforpython-6/) - The Python binding for Qt application framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The command-line utility for downloading YouTube videos
- [FFmpeg](https://ffmpeg.org/) - The complete solution for audio/video processing
- Spotify Web API for providing the data access

# Spotify Downloader UI

A modern UI for Spotify Playlist analysis, extraction, and downloading.

## Features

- Extract playlist data from Spotify
- Analyze playlist contents for hidden gems and trends
- Visualize playlist data and track information
- Filter and search playlist tracks
- Create new playlists directly in Spotify
- Compare and manage multiple playlists
- Generate advanced analytics visualizations
- Export data in multiple formats
- Download tracks with configurable settings
- Track download progress in real-time
- Choose from multiple audio formats

## Project Status

This project is in active development. Current status by phase:

1. **Phase 1: Foundation** ✅ (Complete)
2. **Phase 2: Core UI** ✅ (Complete)
3. **Phase 3: Process Visualization** ✅ (Complete)
4. **Phase 4: Results Display** ✅ (Complete)
5. **Phase 5: Advanced Features** ✅ (Complete)
6. **Phase 6: Packaging** ✅ (Complete)

## Advanced Features

Phase 5 components have been successfully implemented, providing advanced functionality for the Spotify Downloader:

1. **Spotify Playlist Creation**: Create new playlists on Spotify with custom metadata, track selection, and templates.
   
2. **Multi-Playlist Management**: Compare, merge, and manage multiple playlists with grouping, categorization, and batch operations.
   
3. **Advanced Analytics**: Visualize comprehensive analytics including artist analysis, audio features, genre distribution, time-based analysis, diversity metrics, and user preference modeling.
   
4. **Export Functionality**: Export playlist data in multiple formats (CSV, JSON, PDF, Excel, images, text) with customizable templates, scheduling, and cloud storage integration.

5. **Track Downloads**: Download tracks from playlists with configurable settings, format options, and metadata tagging.

These advanced features transform the application from a simple downloader into a complete playlist management solution.

## Installation

1. Ensure Python 3.8+ is installed
2. Clone the repository
3. Install dependencies:
   ```
   pip install -r ui_requirements.txt
   ```
4. Install FFmpeg (required for audio processing)

## Usage

Run the application:
```
python -m spotify_downloader_ui.app
```

## Testing

The application includes a comprehensive testing framework for validating UI components:

```bash
# Run Phase 4 tests (Results Display)
python -m spotify_downloader_ui.tests.run_phase4_tests

# Run Phase 5 tests (Advanced Features)
python -m spotify_downloader_ui.tests.run_phase5_tests

# Test a specific component
python -m spotify_downloader_ui.tests.test_component spotify_playlist_creation
```

See the [testing documentation](spotify_downloader_ui/tests/TESTING.md) for more information.

## Project Structure

```
spotify_downloader_ui/
├── app.py                # Main application entry point
├── main.py               # Main window implementation
├── architecture.md       # Architecture overview
├── services/             # Service layer
├── utils/                # Utility functions
├── views/                # UI components
│   ├── phase1/           # Foundation components
│   ├── phase2/           # Core UI components
│   ├── phase3/           # Process visualization
│   ├── phase4/           # Results display
│   ├── phase5/           # Advanced features
│   └── components/       # Shared components
└── tests/                # Test framework
```

## Dependencies

- PyQt6: UI framework
- Matplotlib: Data visualization
- pandas: Data handling
- requests: HTTP requests
- spotipy: Spotify API client
- yt-dlp: YouTube download utility
- FFmpeg: Audio processing

## License

MIT License 