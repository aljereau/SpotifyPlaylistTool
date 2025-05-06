"""
Spotify Downloader package initialization.
This file initializes the Spotify Downloader package and applies any necessary patches.
"""

# Apply patches to ensure compatibility
try:
    from .spotify_api_patch import apply_spotify_patches
    apply_spotify_patches()
except ImportError:
    # If the patch file isn't available, we can continue without it
    pass 