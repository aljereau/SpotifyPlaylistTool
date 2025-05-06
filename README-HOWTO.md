# Spotify Downloader - How to Run

This guide explains how to run the Spotify Downloader application.

## Prerequisites

The following dependencies must be installed:

1. **Python 3.7 or higher**
2. **FFmpeg** - Automatically included in the setup
3. **PySide6** - The Python binding for Qt application framework
4. **yt-dlp** - Automatically installed with the application

## Installation

Run the `install_dependencies.bat` script to automatically install all required dependencies:

```
install_dependencies.bat
```

This script will:
1. Install all Python dependencies using pip
2. Check for FFmpeg and download it if not found
3. Verify all dependencies are correctly installed

## Running the Application

Two batch files are provided for easy use:

### Command-Line Interface

Run `run_spotify_downloader.bat` to use the command-line interface:

```
run_spotify_downloader.bat [options]
```

Examples:

```
# Download tracks from a Spotify playlist
run_spotify_downloader.bat https://open.spotify.com/playlist/your_playlist_id

# Download tracks with specific format
run_spotify_downloader.bat --format mp3 https://open.spotify.com/playlist/your_playlist_id

# Set custom output directory
run_spotify_downloader.bat -o "C:\Music" https://open.spotify.com/playlist/your_playlist_id

# Show help
run_spotify_downloader.bat --help
```

### Graphical User Interface

Run `run_spotify_downloader_gui.bat` to use the graphical user interface:

```
run_spotify_downloader_gui.bat
```

The GUI provides a user-friendly way to:
- Enter Spotify playlist URLs
- Configure download settings
- Track download progress
- View playlist analysis

## Troubleshooting

If you encounter issues with the application, try the following steps:

1. **Run the dependency check again**:
   ```
   python -m src.spotify_downloader --check-deps
   ```

2. **Verify FFmpeg is properly installed**:
   ```
   ffmpeg -version
   ```

3. **Check your Spotify API credentials**:
   Make sure your .env file contains valid Spotify client ID and secret.

4. **Update dependencies**:
   ```
   pip install -r requirements.txt --upgrade
   ```

5. **Check the log files**:
   Log files are stored in the `logs` directory and might contain useful debugging information.

## Command-Line Options

```
Input Options:
  urls                  One or more Spotify playlist URLs
  -f, --file FILE       Text file containing Spotify playlist URLs (one per line)

Output Options:
  -o, --output-dir OUTPUT_DIR
                        Output directory for downloaded tracks (default: output)
  --format {mp3,m4a,opus,wav}
                        Audio format for downloaded tracks (default: mp3)

Download Options:
  --max-workers MAX_WORKERS
                        Maximum number of concurrent downloads (default: 4)
  --skip-existing       Skip downloading files that already exist
  --retry-count RETRY_COUNT
                        Number of retries for failed downloads (default: 3)

Utility Options:
  --check-deps          Check if required dependencies (yt-dlp, ffmpeg) are installed
```

## Spotify Authentication

If you need to authenticate with Spotify, use the following command:

```
python -m spotify_downloader_ui.cli auth
```

This will guide you through the authentication process. 