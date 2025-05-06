#!/usr/bin/env python3
"""
Test script for Hidden Gems functionality using mock data
"""

import json
import os
import sys
from datetime import datetime

# Import functions from the main script
sys.path.append('src')
from spotify_playlist_extractor import generate_hidden_gems_report, save_track_analytics

def main():
    # Ensure output directory exists
    output_dir = 'output/test_results'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading mock playlist data...")
    # Load mock data
    with open('mock_playlist.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tracks = data['tracks']
    metadata = data['metadata']
    
    print(f"Loaded {len(tracks)} tracks from mock playlist: {metadata['name']}")
    
    # Save analytics report
    analytics_file = os.path.join(output_dir, f"mock_playlist_analytics.txt")
    print(f"Generating analytics report...")
    save_track_analytics(tracks, analytics_file)
    print(f"Analytics report saved to: {analytics_file}")
    
    # Generate hidden gems report
    print(f"Generating hidden gems report...")
    min_pop = 0
    max_pop = 40
    min_score = 20
    top_gems = 5
    
    gems_file, urls_file = generate_hidden_gems_report(
        output_dir, 
        tracks, 
        min_pop, 
        max_pop, 
        min_score, 
        top_gems,
        playlist_name=metadata['name']
    )
    
    print(f"Hidden gems report saved to: {gems_file}")
    print(f"Playlist URLs saved to: {urls_file}")
    
if __name__ == "__main__":
    main() 