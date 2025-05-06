# Spotify Playlist Extractor - Usage Guide

## Basic Commands

### Process a Single Playlist

```bash
python src/spotify_playlist_extractor.py https://open.spotify.com/playlist/your_playlist_id
```

This will:
- Extract all tracks from the specified playlist
- Create a folder with the playlist name in the `output` directory
- Generate track list and links files
- Generate an analytics report

### Process Multiple Playlists

```bash
python src/spotify_playlist_extractor.py https://open.spotify.com/playlist/id1 https://open.spotify.com/playlist/id2
```

This will process each playlist sequentially and create separate folders for each.

### Process Playlists from a File

```bash
python src/spotify_playlist_extractor.py --file playlists.txt
```

Where `playlists.txt` contains one playlist URL per line:

```
https://open.spotify.com/playlist/id1
https://open.spotify.com/playlist/id2
https://open.spotify.com/playlist/id3
```

## Output Options

### Custom Output Directory

```bash
python src/spotify_playlist_extractor.py URL --output-dir custom_folder
```

### Include Artist Name in Filenames

```bash
python src/spotify_playlist_extractor.py URL --include-artist
```

### Disable Playlist-specific Folders

```bash
python src/spotify_playlist_extractor.py URL --no-playlist-folders
```

All files will be saved directly to the output directory instead of creating playlist-specific folders.

## Hidden Gems Analysis

### Basic Hidden Gems Report

```bash
python src/spotify_playlist_extractor.py URL --hidden-gems
```

This will generate a hidden gems report that:
- Scores tracks on a 0-50 point scale
- Lists tracks by their gem scores
- Creates a file with track URLs for easy playlist creation

### Customize Hidden Gems Criteria

```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --min-pop=5 --max-pop=35 --min-score=25 --top-gems=20
```

Parameters:
- `--min-pop`: Minimum popularity score to consider (default: 0)
- `--max-pop`: Maximum popularity score to consider (default: 40)
- `--min-score`: Minimum gem score to include in the report (default: 20)
- `--top-gems`: Number of top gems to include in the playlist section (default: 30)

## Multi-Playlist Analysis

### Combined Analysis Report

```bash
python src/spotify_playlist_extractor.py --file playlists.txt --combined-analysis
```

This will:
- Process all playlists in the file
- Create a combined analysis report with all tracks
- Generate analytics comparing tracks across playlists
- Identify common patterns and promising artists

Hidden gems analysis is automatically included with combined analysis.

## Playlist Creation

### Create a Spotify Playlist from Hidden Gems

```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --create-playlist
```

This will:
- Analyze the playlist to find hidden gems
- Connect to Spotify with your account (requires authorization)
- Create a new playlist called "Hidden Gems" with the top gems

### Customize the Created Playlist

```bash
python src/spotify_playlist_extractor.py URL --hidden-gems --create-playlist --playlist-name "Amazing Underground Tracks" --playlist-description "My favorite undiscovered songs" --playlist-public
```

Parameters:
- `--playlist-name`: Custom name for the playlist (default: "Hidden Gems")
- `--playlist-description`: Custom description (default: "Discovered gems from playlists analyzed by Spotify Playlist Extractor")
- `--playlist-public`: Make the playlist public (default: private)

### Create a Playlist from a Specific URLs File

```bash
python src/spotify_playlist_extractor.py --create-playlist --urls-file path/to/playlist_urls.txt
```

Use this if you've already generated a hidden gems report and want to create a playlist from it later.

## Processing Options

### Skip Already Processed Playlists

```bash
python src/spotify_playlist_extractor.py --file playlists.txt --skip-existing
```

This will skip playlists that have been processed before based on cached data.

### Retry Failed Playlists

```bash
python src/spotify_playlist_extractor.py --file playlists.txt --retry-failed --retry-limit 5
```

This will attempt to reprocess any failed playlists up to the specified retry limit.

## Complete Example

```bash
python src/spotify_playlist_extractor.py --file playlists.txt --output-dir my_playlists --combined-analysis --hidden-gems --min-pop=0 --max-pop=35 --min-score=25 --create-playlist --playlist-name "Best Underground Tracks" --skip-existing --retry-failed
```

This will:
1. Process all playlists in `playlists.txt`
2. Save results to `my_playlists` directory
3. Generate a combined analysis
4. Find hidden gems with popularity between 0-35 and score at least 25
5. Create a Spotify playlist called "Best Underground Tracks"
6. Skip any playlists that were already processed
7. Retry any playlists that fail during processing

## Understanding the Output

### Playlist Folder Structure

Each playlist gets its own folder with:

- `playlist_name_tracks.txt`: Detailed track information
- `playlist_name_links.txt`: Track links for easy sharing/playing
- `playlist_name_analytics.txt`: Analytics report with detailed metrics
- `playlist_name_hidden_gems_*.txt`: Hidden gems report (if requested)
- `playlist_name_hidden_gems_playlist_urls_*.txt`: URLs for playlist creation
- `Downloads/`: Directory for downloaded tracks (future feature)

### Hidden Gems Report

The hidden gems report contains:

1. **Analysis Statistics**: Overview of all analyzed tracks
2. **Top Hidden Gems**: List of the highest-scoring gems with detailed information
3. **Gems by Score Category**:
   - Elite Gems (40+ points)
   - Quality Gems (30-39 points)
   - Standard Gems (20-29 points)
4. **Gems by Popularity Bracket**:
   - Ultra Underground (0-10 popularity)
   - Deep Underground (11-20 popularity)
   - Rising Underground (21-40 popularity)
5. **Playlist Creation**: List of recommended tracks for playlist creation

### Combined Analysis Report

The combined analysis report includes:

1. **Playlist Overview**: Summary of all processed playlists
2. **All Tracks Sorted by Popularity**: Complete list of all tracks
3. **Popularity Distribution**: Visual representation of track popularity
4. **Potential Hidden Gems**: Tracks with low popularity scores
5. **Promising Underground Artists**: Artists with multiple low-popularity tracks 