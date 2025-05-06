@echo off
echo Starting Spotify Downloader GUI...
echo.
echo Using PySide6 GUI framework
echo.
set PATH=C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin;%PATH%

echo Checking dependencies...
python -m src.spotify_downloader --check-deps

echo.
echo Attempting to launch GUI...
python -m spotify_downloader_ui.main

if %ERRORLEVEL% neq 0 (
    echo.
    echo GUI launch failed. Using command-line interface instead.
    echo.
    python -m spotify_downloader_ui.cli gui
)

echo.
echo Spotify Downloader finished.
pause 