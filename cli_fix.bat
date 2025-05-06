@echo off
echo ===============================================
echo Spotify Downloader CLI Helper
echo ===============================================
echo.
echo The GUI version isn't working properly due to compatibility issues 
echo with Python 3.13 and PyQt6 6.9.0. 
echo.
echo However, the command-line interface works perfectly!
echo.
echo Here's how to use it:
echo.
echo 1. To download a playlist:
echo    .\run_spotify_downloader.bat https://open.spotify.com/playlist/YOUR_PLAYLIST_ID
echo.
echo 2. To specify the audio format:
echo    .\run_spotify_downloader.bat --format mp3 https://open.spotify.com/playlist/YOUR_PLAYLIST_ID
echo.
echo 3. To specify the output directory:
echo    .\run_spotify_downloader.bat -o "output" https://open.spotify.com/playlist/YOUR_PLAYLIST_ID
echo.
echo 4. For more help:
echo    .\run_spotify_downloader.bat --help
echo.
echo ===============================================
echo.
echo Press any key to exit or CTRL+C to cancel
pause > nul 