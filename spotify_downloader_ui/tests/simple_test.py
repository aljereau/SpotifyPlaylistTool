"""
Simple test UI for Spotify Downloader components.

This script provides a simplified test environment for the Spotify Downloader UI components,
creating basic mockups of the four main Phase 4 components:
- PlaylistResultsView
- HiddenGemsVisualization
- TrackListing
- FilterSidebar

Run this script directly:
python -m spotify_downloader_ui.tests.simple_test
"""

import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QCheckBox, QComboBox, QPushButton, QGroupBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette

class MockPlaylistResultsView(QWidget):
    """Mock implementation of PlaylistResultsView."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Playlist header
        header = QLabel("Test Playlist")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Playlist info
        info = QLabel("Created by: Test User | 123 followers | 45 tracks")
        layout.addWidget(info)
        
        # Playlist description
        desc = QLabel("This is a test playlist for the Spotify Downloader UI.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Statistics section
        stats_box = QGroupBox("Playlist Statistics")
        stats_layout = QVBoxLayout()
        
        stats_layout.addWidget(QLabel("Average popularity: 65"))
        stats_layout.addWidget(QLabel("Average track duration: 3:45"))
        stats_layout.addWidget(QLabel("Most common artist: Test Artist (10 tracks)"))
        stats_layout.addWidget(QLabel("Genres: Pop (15), Rock (12), Electronic (8), Other (10)"))
        
        stats_box.setLayout(stats_layout)
        layout.addWidget(stats_box)
        
        # Add some spacing
        layout.addStretch()

class MockHiddenGemsVisualization(QWidget):
    """Mock implementation of HiddenGemsVisualization."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Hidden Gems Visualization")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Simple bar chart representation using colored frames
        chart_frame = QFrame()
        chart_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        chart_layout = QHBoxLayout(chart_frame)
        
        # Create 10 bars with different heights
        for i in range(10):
            bar = QFrame()
            bar.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
            
            # Calculate height based on "score"
            height = 20 + (i * 15)
            if i % 3 == 0:
                height = 150 - height  # Mix it up a bit
                
            # Set color based on "popularity"
            palette = QPalette()
            if i < 3:
                palette.setColor(QPalette.ColorRole.Window, QColor(150, 200, 150))  # Green for low popularity
            elif i < 7:
                palette.setColor(QPalette.ColorRole.Window, QColor(200, 200, 150))  # Yellow for medium
            else:
                palette.setColor(QPalette.ColorRole.Window, QColor(200, 150, 150))  # Red for high popularity
                
            bar.setAutoFillBackground(True)
            bar.setPalette(palette)
            bar.setMinimumSize(30, height)
            
            chart_layout.addWidget(bar)
        
        layout.addWidget(chart_frame)
        
        # Legend
        legend_box = QGroupBox("Legend")
        legend_layout = QHBoxLayout()
        
        # Low popularity
        low_frame = QFrame()
        low_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        low_frame.setMinimumSize(20, 20)
        low_frame.setMaximumSize(20, 20)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(150, 200, 150))
        low_frame.setAutoFillBackground(True)
        low_frame.setPalette(palette)
        legend_layout.addWidget(low_frame)
        legend_layout.addWidget(QLabel("Low Popularity"))
        
        legend_layout.addSpacing(20)
        
        # Medium popularity
        med_frame = QFrame()
        med_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        med_frame.setMinimumSize(20, 20)
        med_frame.setMaximumSize(20, 20)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(200, 200, 150))
        med_frame.setAutoFillBackground(True)
        med_frame.setPalette(palette)
        legend_layout.addWidget(med_frame)
        legend_layout.addWidget(QLabel("Medium Popularity"))
        
        legend_layout.addSpacing(20)
        
        # High popularity
        high_frame = QFrame()
        high_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        high_frame.setMinimumSize(20, 20)
        high_frame.setMaximumSize(20, 20)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(200, 150, 150))
        high_frame.setAutoFillBackground(True)
        high_frame.setPalette(palette)
        legend_layout.addWidget(high_frame)
        legend_layout.addWidget(QLabel("High Popularity"))
        
        legend_layout.addStretch()
        legend_box.setLayout(legend_layout)
        layout.addWidget(legend_box)
        
        # Add some spacing
        layout.addStretch()

class MockTrackListing(QWidget):
    """Mock implementation of TrackListing."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Track Listing")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Track search
        search = QLineEdit()
        search.setPlaceholderText("Search tracks...")
        layout.addWidget(search)
        
        # Track list
        self.track_list = QListWidget()
        
        # Add sample tracks
        track_names = [
            "Amazing Track - Test Artist",
            "Hidden Gem - Unknown Artist",
            "Popular Hit - Famous Band",
            "Deep Cut - Indie Group",
            "Underground Classic - Local Artist",
            "Chart Topper - Pop Star",
            "Album Filler - One Hit Wonder",
            "Fan Favorite - Rock Band",
            "Overlooked Masterpiece - Jazz Ensemble",
            "Deep Cut - Electronic Producer"
        ]
        
        for i, name in enumerate(track_names):
            item = QListWidgetItem(name)
            if i % 3 == 0:
                item.setBackground(QColor(240, 255, 240))  # Light green for "hidden gems"
            self.track_list.addItem(item)
        
        layout.addWidget(self.track_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QPushButton("Play"))
        controls_layout.addWidget(QPushButton("Add to Playlist"))
        controls_layout.addWidget(QPushButton("Download"))
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

class MockFilterSidebar(QWidget):
    """Mock implementation of FilterSidebar."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Filters")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Popularity filter
        pop_group = QGroupBox("Popularity")
        pop_layout = QVBoxLayout()
        pop_layout.addWidget(QCheckBox("Low (0-30)"))
        pop_layout.addWidget(QCheckBox("Medium (31-70)"))
        pop_layout.addWidget(QCheckBox("High (71-100)"))
        pop_group.setLayout(pop_layout)
        layout.addWidget(pop_group)
        
        # Genre filter
        genre_group = QGroupBox("Genre")
        genre_layout = QVBoxLayout()
        genre_layout.addWidget(QCheckBox("Pop"))
        genre_layout.addWidget(QCheckBox("Rock"))
        genre_layout.addWidget(QCheckBox("Hip-Hop"))
        genre_layout.addWidget(QCheckBox("Electronic"))
        genre_layout.addWidget(QCheckBox("Jazz"))
        genre_layout.addWidget(QCheckBox("Classical"))
        genre_layout.addWidget(QCheckBox("Other"))
        genre_group.setLayout(genre_layout)
        layout.addWidget(genre_group)
        
        # Release date filter
        date_group = QGroupBox("Release Date")
        date_layout = QVBoxLayout()
        date_layout.addWidget(QCheckBox("2020s"))
        date_layout.addWidget(QCheckBox("2010s"))
        date_layout.addWidget(QCheckBox("2000s"))
        date_layout.addWidget(QCheckBox("1990s"))
        date_layout.addWidget(QCheckBox("Older"))
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # Presets
        preset_group = QGroupBox("Presets")
        preset_layout = QVBoxLayout()
        preset_combo = QComboBox()
        preset_combo.addItems(["Hidden Gems", "Party Tracks", "Chill Vibes", "Workout Mix"])
        preset_layout.addWidget(preset_combo)
        preset_layout.addWidget(QPushButton("Apply Preset"))
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Add spacing and clear button at bottom
        layout.addStretch()
        layout.addWidget(QPushButton("Clear All Filters"))

class SimpleTestWindow(QMainWindow):
    """Main window for simple test of UI components."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Spotify Downloader UI - Simple Test")
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Filter sidebar on the left
        self.filter_sidebar = MockFilterSidebar()
        main_splitter.addWidget(self.filter_sidebar)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top section: Playlist results
        self.playlist_results = MockPlaylistResultsView()
        content_layout.addWidget(self.playlist_results)
        
        # Middle and bottom sections in a vertical splitter
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Middle section: Hidden gems visualization
        self.hidden_gems = MockHiddenGemsVisualization()
        vertical_splitter.addWidget(self.hidden_gems)
        
        # Bottom section: Track listing
        self.track_listing = MockTrackListing()
        vertical_splitter.addWidget(self.track_listing)
        
        # Set initial sizes for vertical splitter
        vertical_splitter.setSizes([300, 500])
        
        content_layout.addWidget(vertical_splitter)
        
        # Add content area to main splitter
        main_splitter.addWidget(content_widget)
        
        # Set initial sizes for main splitter
        main_splitter.setSizes([200, 1000])
        
        # Add main splitter to layout
        main_layout.addWidget(main_splitter)

def main():
    """Run the simple test."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create the application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create and show the main window
    window = SimpleTestWindow()
    window.show()
    
    # Run the event loop
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main()) 