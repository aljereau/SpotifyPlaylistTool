# Spotify Downloader

A powerful tool for downloading tracks from Spotify playlists. This tool first extracts track information from your Spotify playlists and then downloads audio files using YouTube as a source.

## Features

- Extract complete track information from Spotify playlists
- Download audio files for all tracks in a playlist
- Choose from multiple audio formats (MP3, M4A, OPUS, WAV)
- Configure concurrent downloads to optimize performance
- Track download progress in real-time
- Add proper metadata to downloaded files (artist, title, album, etc.)
- Built-in track analysis for discovering hidden gems
- Modern, user-friendly GUI

## Requirements

- Python 3.7 or higher
- [Spotify Developer Account](https://developer.spotify.com/dashboard/) for API credentials
- External tools:
  - [yt-dlp](https://github.com/yt-dlp/yt-dlp) - For downloading audio from YouTube
  - [FFmpeg](https://ffmpeg.org/) - For audio processing

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/spotify-downloader.git
   cd spotify-downloader
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install external dependencies:
   - **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or install via package manager
     - Windows: `choco install ffmpeg`
     - macOS: `brew install ffmpeg`
     - Ubuntu: `sudo apt install ffmpeg`
   - **yt-dlp**: Should be automatically installed via requirements.txt

4. Create a `.env` file in the project root with your Spotify API credentials:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

## Usage

### GUI (Recommended)

1. Launch the application:
   ```
   python -m spotify_downloader_ui.main
   ```

2. Input a Spotify playlist URL in the "Playlist Input" tab and click "Process Playlist"

3. Navigate to the "Download Tracks" tab 

4. Configure download settings:
   - Select audio format (MP3, M4A, OPUS, WAV)
   - Set number of concurrent downloads (higher = faster, but more resource-intensive)
   - Choose whether to skip existing files
   - Optionally change the output directory

5. Click "Download All Tracks" to start downloading

6. Monitor progress in the table and progress bar

7. Find your downloaded files in the output directory under the playlist folder's "Downloads" subfolder

### Command Line Interface

For advanced users who prefer the command line:

```bash
# Basic usage - process a playlist and download tracks
python -m src.spotify_downloader "https://open.spotify.com/playlist/37i9dQZEVXcQ9...?si=..."

# Specify output format
python -m src.spotify_downloader --format mp3 "https://open.spotify.com/playlist/..."

# Download multiple playlists
python -m src.spotify_downloader "playlist_url_1" "playlist_url_2" "playlist_url_3"

# Process playlists from a text file (one URL per line)
python -m src.spotify_downloader -f playlists.txt

# Specify output directory
python -m src.spotify_downloader -o "Music/Spotify" "playlist_url"

# Set concurrent downloads
python -m src.spotify_downloader --max-workers 8 "playlist_url"
```

For full command line options:
```
python -m src.spotify_downloader --help
```

## Legal Disclaimer

This tool is for personal use only. Please respect copyright laws and the terms of service of Spotify and YouTube. The developers of this tool do not encourage or condone using it for copyright infringement or any illegal purposes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [spotipy](https://spotipy.readthedocs.io/) - Python client for the Spotify Web API 

## Usage with Batch File

To download tracks from a Spotify playlist using the batch file, run:

```
run_spotify_downloader.bat https://open.spotify.com/playlist/your_playlist_id
```