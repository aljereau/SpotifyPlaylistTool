import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
username = os.getenv('SPOTIFY_USERNAME')

def test_client_credentials():
    """Test accessing playlists with client credentials."""
    print("Testing with Client Credentials Flow...")
    
    # Initialize Spotify client with client credentials
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id, 
        client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Test playlists
    test_playlists = [
        # Spotify-created playlists
        "37i9dQZF1DWXjs5HmaJqaY",  # Boris Brejcha's track IDs
        "37i9dQZEVXbMDoHDwVN2tF",  # Top 50 Global
        "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
        
        # User playlists from playlists.txt
        "0tsWcawuGdHoEd1ZwEdaLY",  # User playlist from playlists.txt
    ]
    
    for playlist_id in test_playlists:
        print(f"\nTesting playlist: {playlist_id}")
        is_spotify_playlist = playlist_id.startswith('37i9dQ')
        playlist_type = "Spotify-created" if is_spotify_playlist else "User"
        print(f"Playlist type: {playlist_type}")
        
        # Try different markets for Spotify playlists
        markets = ['US', 'GB', 'DE', None] if is_spotify_playlist else [None]
        
        for market in markets:
            try:
                print(f"  Trying with market: {market or 'default'}")
                playlist = sp.playlist(playlist_id, fields='name,owner.display_name,tracks.total', market=market)
                print(f"  ✅ Success! Name: {playlist['name']}, Owner: {playlist['owner']['display_name']}, Tracks: {playlist['tracks']['total']}")
                
                # Try getting tracks
                try:
                    tracks = sp.playlist_tracks(playlist_id, limit=1, market=market)
                    if tracks['items']:
                        track = tracks['items'][0]['track']
                        print(f"  ✅ First track: {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")
                    else:
                        print("  ❌ No tracks found")
                except Exception as e:
                    print(f"  ❌ Error getting tracks: {str(e)}")
                
                # We found a working market, no need to try others
                break
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

def test_oauth():
    """Test accessing playlists with OAuth."""
    print("\n\nTesting with OAuth Flow...")
    
    # Set up OAuth for authorization
    scope = "playlist-read-private playlist-read-collaborative"
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
    
    sp_oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        username=username
    )
    
    # Check if we have a token cached
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        print("No token found in cache. Please authorize:")
        auth_url = sp_oauth.get_authorize_url()
        print(f"Please visit this URL: {auth_url}")
        response = input("Enter the URL you were redirected to: ")
        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    
    # Create Spotify client
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # Test the same playlists
    test_playlists = [
        # Spotify-created playlists
        "37i9dQZF1DWXjs5HmaJqaY",  # Boris Brejcha's track IDs
        "37i9dQZEVXbMDoHDwVN2tF",  # Top 50 Global
        "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
        
        # User playlists from playlists.txt
        "0tsWcawuGdHoEd1ZwEdaLY",  # User playlist from playlists.txt
    ]
    
    for playlist_id in test_playlists:
        print(f"\nTesting playlist with OAuth: {playlist_id}")
        is_spotify_playlist = playlist_id.startswith('37i9dQ')
        playlist_type = "Spotify-created" if is_spotify_playlist else "User"
        print(f"Playlist type: {playlist_type}")
        
        # Try different markets for Spotify playlists
        markets = ['US', 'GB', 'DE', None] if is_spotify_playlist else [None]
        
        for market in markets:
            try:
                print(f"  Trying with market: {market or 'default'}")
                playlist = sp.playlist(playlist_id, fields='name,owner.display_name,tracks.total', market=market)
                print(f"  ✅ Success! Name: {playlist['name']}, Owner: {playlist['owner']['display_name']}, Tracks: {playlist['tracks']['total']}")
                
                # Try getting tracks
                try:
                    tracks = sp.playlist_tracks(playlist_id, limit=1, market=market)
                    if tracks['items']:
                        track = tracks['items'][0]['track']
                        print(f"  ✅ First track: {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")
                    else:
                        print("  ❌ No tracks found")
                except Exception as e:
                    print(f"  ❌ Error getting tracks: {str(e)}")
                
                # We found a working market, no need to try others
                break
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

if __name__ == "__main__":
    # Run tests
    print("Testing Spotify API access to playlists...")
    print(f"Client ID: {client_id[:5]}...")
    
    # Test client credentials flow first
    test_client_credentials()
    
    # Uncomment to test OAuth flow
    test_oauth() 