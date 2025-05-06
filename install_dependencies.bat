@echo off
echo Spotify Downloader - Installing Dependencies
echo ============================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking for FFmpeg...
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo FFmpeg not found in PATH. Attempting to download and install...
    
    echo Downloading FFmpeg...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z' -OutFile 'ffmpeg.7z'"
    
    echo Extracting FFmpeg...
    if exist "C:\Program Files\7-Zip\7z.exe" (
        "C:\Program Files\7-Zip\7z.exe" x ffmpeg.7z -oC:\ffmpeg
    ) else (
        echo 7-Zip not found. Please extract ffmpeg.7z manually to C:\ffmpeg.
        echo Then restart this script.
        pause
        exit /b 1
    )
    
    echo Adding FFmpeg to PATH for this session...
    set "PATH=C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin;%PATH%"
    
    echo.
    echo IMPORTANT: To make FFmpeg available for all applications, 
    echo please add the following directory to your system PATH:
    echo C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin
    echo.
) else (
    echo FFmpeg already installed.
)

echo.
echo Running dependency check...
python -m src.spotify_downloader --check-deps

echo.
echo Installation complete! You can now run Spotify Downloader using:
echo   run_spotify_downloader.bat     - Command-line interface
echo   run_spotify_downloader_gui.bat - Graphical interface
echo.
pause 