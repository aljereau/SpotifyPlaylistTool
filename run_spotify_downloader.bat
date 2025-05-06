@echo off
echo Starting Spotify Downloader...
echo.
echo Using PySide6 GUI framework
echo.
set PATH=C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin;%PATH%
python -m src.spotify_downloader %*
echo.
echo Spotify Downloader finished.
pause 