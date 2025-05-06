"""
Mock components for tests.

This module provides simple mock implementations of components
that may have import issues in the actual codebase.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, 
    QComboBox, QPushButton, QListWidget, QTabWidget, QFrame, 
    QGroupBox, QCheckBox, QRadioButton, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette

# Mock versions of problem components

class PlaylistResultsView:
    """Mock PlaylistResultsView for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the view."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._playlist_id = None
        self._loaded_data = None
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def load_playlist(self, playlist_id, playlist_data):
        """Load a playlist."""
        self._playlist_id = playlist_id
        self._loaded_data = playlist_data
        label = QLabel(f"Playlist: {playlist_data.get('name', 'Unknown')}")
        self._layout.addWidget(label)
    
    def get_current_playlist_id(self):
        """Get the current playlist ID."""
        return self._playlist_id

class HiddenGemsVisualization:
    """Mock HiddenGemsVisualization for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the view."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._data = None
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_gems_data(self, data):
        """Set hidden gems data."""
        self._data = data
        label = QLabel(f"Hidden Gems: {len(data.get('track_scores', []))} tracks")
        self._layout.addWidget(label)
    
    def set_current_track(self, track_index):
        """Set the current track."""
        pass

class TrackListing:
    """Mock TrackListing for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the view."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._tracks = []
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_tracks(self, tracks):
        """Set track data."""
        self._tracks = tracks
        label = QLabel(f"Tracks: {len(tracks)}")
        self._layout.addWidget(label)
    
    def get_selected_tracks(self):
        """Get selected tracks."""
        return []

class FilterSignal:
    """Mock signal for filter changes."""
    
    def __init__(self):
        """Initialize the signal."""
        self._slots = []
    
    def connect(self, slot):
        """Connect to slot."""
        self._slots.append(slot)
    
    def emit(self, *args):
        """Emit signal."""
        for slot in self._slots:
            slot(*args)

class FilterSidebar:
    """Mock FilterSidebar for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the view."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._filter_changed = FilterSignal()
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    @property
    def filter_changed(self):
        """Get the filter changed signal."""
        return self._filter_changed
    
    def clear_filters(self):
        """Clear all filters."""
        self._filter_changed.emit({})
    
    def set_available_categories(self, field, categories):
        """Set available categories."""
        pass
    
    def apply_preset(self, preset_name):
        """Apply a filter preset."""
        self._filter_changed.emit({"preset": preset_name})

class SpotifyPlaylistCreation:
    """Mock SpotifyPlaylistCreation for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the component."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._creation_data = None
        
        # Create basic UI elements
        self._layout.addWidget(QLabel("Spotify Playlist Creation"))
        
        # Add playlist name field
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Playlist Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter playlist name...")
        name_layout.addWidget(self._name_edit)
        self._layout.addLayout(name_layout)
        
        # Add description field
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Enter playlist description...")
        desc_layout.addWidget(self._desc_edit)
        self._layout.addLayout(desc_layout)
        
        # Add privacy option
        privacy_layout = QHBoxLayout()
        privacy_layout.addWidget(QLabel("Privacy:"))
        self._privacy_combo = QComboBox()
        self._privacy_combo.addItems(["Public", "Private", "Unlisted"])
        privacy_layout.addWidget(self._privacy_combo)
        privacy_layout.addStretch()
        self._layout.addLayout(privacy_layout)
        
        # Add track selection placeholder
        self._layout.addWidget(QLabel("Selected Tracks:"))
        self._track_list = QListWidget()
        self._layout.addWidget(self._track_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Select Tracks"))
        button_layout.addWidget(QPushButton("Save as Template"))
        button_layout.addWidget(QPushButton("Create Playlist"))
        button_layout.addStretch()
        self._layout.addLayout(button_layout)
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_creation_data(self, data):
        """Set playlist creation data."""
        self._creation_data = data
        
        # Update UI with the data
        if "tracks" in data and isinstance(data["tracks"], list):
            self._track_list.clear()
            for track in data["tracks"]:
                self._track_list.addItem(track.get("name", "Unknown Track"))

class MultiPlaylistManagement:
    """Mock MultiPlaylistManagement for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the component."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._playlists = []
        
        # Create basic UI elements
        self._layout.addWidget(QLabel("Multi-Playlist Management"))
        
        # Add playlist collection view
        top_layout = QHBoxLayout()
        
        # Playlist list
        playlist_layout = QVBoxLayout()
        playlist_layout.addWidget(QLabel("Playlists:"))
        self._playlist_list = QListWidget()
        playlist_layout.addWidget(self._playlist_list)
        
        # Playlist action buttons
        playlist_buttons = QHBoxLayout()
        playlist_buttons.addWidget(QPushButton("Add"))
        playlist_buttons.addWidget(QPushButton("Remove"))
        playlist_buttons.addWidget(QPushButton("Group"))
        playlist_buttons.addStretch()
        playlist_layout.addLayout(playlist_buttons)
        
        top_layout.addLayout(playlist_layout)
        
        # Playlist details
        details_layout = QVBoxLayout()
        details_layout.addWidget(QLabel("Playlist Details:"))
        self._details_widget = QLabel("Select a playlist to view details")
        details_layout.addWidget(self._details_widget)
        
        # Operation buttons
        ops_buttons = QHBoxLayout()
        ops_buttons.addWidget(QPushButton("Compare"))
        ops_buttons.addWidget(QPushButton("Merge"))
        ops_buttons.addWidget(QPushButton("Find Duplicates"))
        ops_buttons.addStretch()
        details_layout.addLayout(ops_buttons)
        
        top_layout.addLayout(details_layout)
        
        self._layout.addLayout(top_layout)
        
        # Add collection statistics
        self._layout.addWidget(QLabel("Collection Statistics:"))
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("Total Playlists: 0"))
        stats_layout.addWidget(QLabel("Total Tracks: 0"))
        stats_layout.addWidget(QLabel("Unique Artists: 0"))
        stats_layout.addStretch()
        self._layout.addLayout(stats_layout)
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_playlists(self, playlists):
        """Set playlist data."""
        self._playlists = playlists
        
        # Update UI with the data
        self._playlist_list.clear()
        for playlist in playlists:
            self._playlist_list.addItem(playlist.get("name", "Unknown Playlist"))

class AdvancedAnalytics:
    """Mock AdvancedAnalytics for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the component."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._analytics_data = None
        
        # Create basic UI elements
        header = QLabel("Advanced Analytics Dashboard")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._layout.addWidget(header)
        
        # Create tabs for different analytics
        self._tabs = QTabWidget()
        
        # Artist analysis tab
        artist_tab = QWidget()
        artist_layout = QVBoxLayout(artist_tab)
        artist_layout.addWidget(QLabel("Artist Analysis"))
        
        # Placeholder for artist charts
        artist_chart = QFrame()
        artist_chart.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        artist_chart.setMinimumHeight(200)
        artist_layout.addWidget(artist_chart)
        
        self._tabs.addTab(artist_tab, "Artist Analysis")
        
        # Audio features tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        audio_layout.addWidget(QLabel("Audio Features"))
        
        # Placeholder for audio feature charts
        audio_chart = QFrame()
        audio_chart.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        audio_chart.setMinimumHeight(200)
        audio_layout.addWidget(audio_chart)
        
        self._tabs.addTab(audio_tab, "Audio Features")
        
        # Genre distribution tab
        genre_tab = QWidget()
        genre_layout = QVBoxLayout(genre_tab)
        genre_layout.addWidget(QLabel("Genre Distribution"))
        
        # Placeholder for genre chart
        genre_chart = QFrame()
        genre_chart.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        genre_chart.setMinimumHeight(200)
        genre_layout.addWidget(genre_chart)
        
        self._tabs.addTab(genre_tab, "Genre Distribution")
        
        # Time analysis tab
        time_tab = QWidget()
        time_layout = QVBoxLayout(time_tab)
        time_layout.addWidget(QLabel("Time-Based Analysis"))
        
        # Placeholder for time chart
        time_chart = QFrame()
        time_chart.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        time_chart.setMinimumHeight(200)
        time_layout.addWidget(time_chart)
        
        self._tabs.addTab(time_tab, "Time Analysis")
        
        # Add tabs to layout
        self._layout.addWidget(self._tabs)
        
        # Add export and options buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Export Analysis"))
        button_layout.addWidget(QPushButton("Save View"))
        button_layout.addStretch()
        self._layout.addLayout(button_layout)
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_analytics_data(self, data):
        """Set analytics data."""
        self._analytics_data = data

class ExportFunctionality:
    """Mock ExportFunctionality for testing."""
    
    def __init__(self, config_service, error_service):
        """Initialize the component."""
        self._config_service = config_service
        self._error_service = error_service
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._export_data = None
        
        # Create basic UI elements
        header = QLabel("Export Manager")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._layout.addWidget(header)
        
        # Data selection section
        data_group = QGroupBox("Data Selection")
        data_layout = QVBoxLayout()
        
        # Data source
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Data Source:"))
        source_combo = QComboBox()
        source_combo.addItems(["Current Playlist", "All Playlists", "Hidden Gems", "Analytics"])
        source_layout.addWidget(source_combo)
        source_layout.addStretch()
        data_layout.addLayout(source_layout)
        
        # Data type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Export Type:"))
        
        # Create a group of checkboxes
        type_layout.addWidget(QCheckBox("Track Info"))
        type_layout.addWidget(QCheckBox("Analytics"))
        type_layout.addWidget(QCheckBox("Playlists"))
        type_layout.addWidget(QCheckBox("Visualizations"))
        type_layout.addStretch()
        data_layout.addLayout(type_layout)
        
        data_group.setLayout(data_layout)
        self._layout.addWidget(data_group)
        
        # Format selection section
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout()
        
        # Format options grid
        format_grid = QGridLayout()
        format_grid.addWidget(QCheckBox("CSV"), 0, 0)
        format_grid.addWidget(QCheckBox("JSON"), 0, 1)
        format_grid.addWidget(QCheckBox("PDF"), 0, 2)
        format_grid.addWidget(QCheckBox("Excel"), 1, 0)
        format_grid.addWidget(QCheckBox("Images"), 1, 1)
        format_grid.addWidget(QCheckBox("Text"), 1, 2)
        format_layout.addLayout(format_grid)
        
        format_group.setLayout(format_layout)
        self._layout.addWidget(format_group)
        
        # Template selection
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        template_combo = QComboBox()
        template_combo.addItems(["Default", "Detailed", "Summary", "Analytics", "Custom..."])
        template_layout.addWidget(template_combo)
        template_layout.addStretch()
        self._layout.addLayout(template_layout)
        
        # Destination options
        dest_group = QGroupBox("Destination")
        dest_layout = QVBoxLayout()
        
        dest_layout.addWidget(QRadioButton("Local File"))
        dest_layout.addWidget(QRadioButton("Cloud Storage"))
        dest_layout.addWidget(QRadioButton("Generate Link"))
        
        dest_group.setLayout(dest_layout)
        self._layout.addWidget(dest_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Export Now"))
        button_layout.addWidget(QPushButton("Schedule Export"))
        button_layout.addWidget(QPushButton("Save Profile"))
        button_layout.addStretch()
        self._layout.addLayout(button_layout)
    
    @property
    def widget(self):
        """Get the widget."""
        return self._container
    
    def set_export_data(self, data):
        """Set export data."""
        self._export_data = data 