# Spotify Playlist Extractor - New Features

## Overview of Enhancements

We've significantly upgraded the Spotify Playlist Extractor with several new features and improvements:

### 1. Multi-Playlist Processing Framework

- **Batch Processing**: Process multiple playlists in a single run, either from command-line arguments or a text file
- **Cache Management**: Skip already processed playlists with `--skip-existing` option
- **Error Handling**: Retry failed playlists with configurable retry limits
- **Progress Tracking**: Detailed progress reporting for multiple playlist processing

### 2. Organized Output Structure

- **Playlist-Specific Folders**: Each playlist gets its own directory for better organization
- **Downloads Folder**: Dedicated "Downloads" folder inside each playlist directory for future downloads
- **Reference Files**: Metadata reference files to quickly find processed playlists
- **Combined Reports**: Optional combined analysis for multiple playlists

### 3. Hidden Gems Analysis

- **Advanced Scoring System**: Tracks are scored on a 0-50 point scale based on:
  - Popularity (0-20 points): Lower popularity = higher score
  - Artist Collaboration (0-10 points): Multiple artists = higher score
  - Track Duration (0-10 points): Extended tracks = higher score
  - Release Type (0-10 points): Singles and EPs = higher score

- **Detailed Reports**: Comprehensive reports with:
  - Overall statistics
  - Top gems with score breakdown
  - Categorization by score tiers (Elite, Quality, Standard)
  - Categorization by popularity brackets (Ultra, Deep, Rising Underground)
  - First-class playlist creation support

### 4. Spotify Playlist Creation

- **OAuth Authentication**: Secure authentication for Spotify API write access
- **Automated Creation**: Create playlists directly from hidden gems with one command
- **Customization Options**: Configure playlist name, description, and privacy settings
- **Browser-Based Auth Flow**: Complete OAuth flow for user authorization

### 5. Enhanced Analytics

- **Popularity Analysis**: Tracks sorted by popularity with detailed information
- **Popularity Distribution**: Visual representation of popularity distribution
- **Artist Analysis**: Identify promising underground artists with multiple tracks
- **Categorized Results**: Tracks categorized by popularity ranges for easier discovery

## Implementation Details

### New Command-Line Options

```
# Hidden Gems Options
--hidden-gems               Generate a hidden gems report
--min-pop INT               Minimum popularity score (default: 0)
--max-pop INT               Maximum popularity score (default: 40)
--min-score INT             Minimum gem score (default: 20)
--top-gems INT              Number of top gems for playlist (default: 30)

# Spotify Integration
--create-playlist           Create a Spotify playlist from hidden gems
--playlist-name TEXT        Custom name for the created playlist
--playlist-description TEXT Custom description for the playlist
--playlist-public           Make the playlist public (default: private)
--urls-file TEXT            Use specific URLs file for playlist creation

# Multi-Playlist Options
--file TEXT                 File containing playlist URLs
--combined-analysis         Generate combined analysis for all playlists
--skip-existing             Skip already processed playlists
--retry-failed              Retry failed playlist downloads
--retry-limit INT           Maximum number of retries (default: 3)
--no-playlist-folders       Disable playlist-specific folders
```

### Folder Structure

The new output structure is more organized and scalable:

```
output/
├── playlist1/
│   ├── playlist1_tracks.txt
│   ├── playlist1_links.txt
│   ├── playlist1_analytics.txt
│   ├── playlist1_hidden_gems_*.txt
│   ├── playlist1_hidden_gems_playlist_urls_*.txt
│   └── Downloads/
├── playlist2/
│   ├── ...
│   └── Downloads/
├── combined_analysis_*.txt
├── playlist1_ref.json
└── playlist2_ref.json
```

### Hidden Gems Scoring Example

A track could receive points as follows:
- Popularity of 12/100: +20 points (Low popularity)
- 3 collaborating artists: +10 points (Artist collaboration)
- 6.5 minute duration: +10 points (Extended track)
- Single with 2 tracks: +10 points (Focus release)
- **Total score**: 50/50 points (Elite gem)

## Future Directions

Potential future enhancements to consider:
- Audio feature analysis (danceability, energy, etc.)
- Track download functionality
- Playlist comparison tools
- Recommendation engines
- Machine learning for custom gem scoring 