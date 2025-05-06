"""
Hidden Gems Visualization component for displaying and interacting with hidden gems analysis.
"""

import logging
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QTabWidget, QToolBar, QToolButton,
    QSplitter, QMenu, QSlider, QCheckBox,
    QGroupBox, QGridLayout, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QRectF
from PySide6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QFont, QAction, QAction, QAction

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class GemCategory(Enum):
    """Categories of hidden gems based on score."""
    DIAMOND = 4
    RUBY = 3
    EMERALD = 2
    SAPPHIRE = 1
    QUARTZ = 0

class HiddenGemsScoreView(QWidget):
    """Widget for visualizing hidden gem scores."""
    
    def __init__(self, parent=None):
        """Initialize the score visualization.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Data
        self.score_data = {}
        self.track_scores = []
        
        # Settings
        self.threshold = 50  # Score threshold (0-100)
        self.current_track_index = -1
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Score distribution chart
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(QLabel("<b>Score Distribution</b>"))
        
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(200)
        chart_layout.addWidget(self.chart_view)
        
        main_layout.addLayout(chart_layout)
        
        # Threshold slider
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Gem Threshold:"))
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(self.threshold)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel(f"{self.threshold}%")
        threshold_layout.addWidget(self.threshold_label)
        
        main_layout.addLayout(threshold_layout)
        
        # Category counts
        categories_layout = QHBoxLayout()
        
        # Create category indicators
        self.category_counts = {}
        for category in GemCategory:
            color = self._get_category_color(category)
            style = f"background-color: {color.name()}; border-radius: 4px; padding: 4px; color: white;"
            
            category_frame = QFrame()
            category_frame.setStyleSheet(style)
            
            category_layout = QVBoxLayout(category_frame)
            category_layout.setContentsMargins(6, 4, 6, 4)
            
            name_label = QLabel(category.name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            category_layout.addWidget(name_label)
            
            count_label = QLabel("0")
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            category_layout.addWidget(count_label)
            
            self.category_counts[category] = count_label
            categories_layout.addWidget(category_frame)
        
        main_layout.addLayout(categories_layout)
        
        # Component weights
        weights_group = QGroupBox("Score Component Weights")
        weights_layout = QGridLayout()
        
        # Default weight components
        weight_components = [
            ("Obscurity", 30),
            ("Uniqueness", 25),
            ("Freshness", 15),
            ("Artist Potential", 20),
            ("Popularity Inverse", 10)
        ]
        
        self.weight_sliders = {}
        row = 0
        for name, default_value in weight_components:
            weights_layout.addWidget(QLabel(f"{name}:"), row, 0)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(default_value)
            slider.valueChanged.connect(self._on_weights_changed)
            weights_layout.addWidget(slider, row, 1)
            
            value_label = QLabel(f"{default_value}%")
            weights_layout.addWidget(value_label, row, 2)
            
            self.weight_sliders[name] = (slider, value_label)
            row += 1
        
        weights_group.setLayout(weights_layout)
        main_layout.addWidget(weights_group)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        self.create_playlist_button = QPushButton("Create Playlist from Gems")
        self.create_playlist_button.clicked.connect(self._on_create_playlist)
        actions_layout.addWidget(self.create_playlist_button)
        
        self.export_button = QPushButton("Export Gems Data")
        self.export_button.clicked.connect(self._on_export)
        actions_layout.addWidget(self.export_button)
        
        main_layout.addLayout(actions_layout)
        
        # Create initial empty chart
        self._update_chart([])
    
    def set_scores(self, scores: List[Dict[str, Any]]):
        """Set the hidden gem scores data.
        
        Args:
            scores: List of track score data
        """
        if not scores:
            return
            
        self.track_scores = scores
        
        # Update chart
        self._update_chart(scores)
        
        # Update category counts
        self._update_categories()
        
        logger.info(f"Loaded {len(scores)} hidden gem scores")
    
    def set_current_track(self, track_index: int):
        """Set the currently selected track.
        
        Args:
            track_index: Index of selected track
        """
        if 0 <= track_index < len(self.track_scores):
            self.current_track_index = track_index
            # Highlight in chart if implemented
    
    def _update_chart(self, scores: List[Dict[str, Any]]):
        """Update the score distribution chart.
        
        Args:
            scores: List of track score data
        """
        # Create chart
        chart = QChart()
        chart.setTitle("Hidden Gem Score Distribution")
        
        if not scores:
            # No data yet
            self.chart_view.setChart(chart)
            return
        
        # Extract scores
        values = [score.get('total_score', 0) for score in scores]
        
        # Create histogram data (10 bins)
        bin_count = 10
        bin_width = 10
        bins = [0] * bin_count
        
        for value in values:
            bin_index = min(int(value / bin_width), bin_count - 1)
            bins[bin_index] += 1
        
        # Create bar series
        bar_set = QBarSet("Tracks")
        for count in bins:
            bar_set.append(count)
        
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        chart.addSeries(bar_series)
        
        # Set up axes
        axis_x = QBarCategoryAxis()
        labels = [f"{i*10}-{(i+1)*10-1}" for i in range(bin_count)]
        axis_x.append(labels)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(bins) + 1)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        # Add vertical line for threshold
        self._add_threshold_line(chart, axis_x, axis_y)
        
        # Set the new chart
        self.chart_view.setChart(chart)
    
    def _add_threshold_line(self, chart, axis_x, axis_y):
        """Add a vertical line to indicate threshold.
        
        Args:
            chart: Chart to add line to
            axis_x: X-axis
            axis_y: Y-axis
        """
        threshold_series = QLineSeries()
        
        # Convert threshold to x-coordinate
        threshold_bin = min(int(self.threshold / 10), 9)
        threshold_x = threshold_bin + 0.5  # Center of the bin
        
        # Add points for vertical line
        y_range = axis_y.max()
        threshold_series.append(threshold_x, 0)
        threshold_series.append(threshold_x, y_range)
        
        # Style the line
        pen = QPen(QColor("red"))
        pen.setWidth(2)
        threshold_series.setPen(pen)
        
        chart.addSeries(threshold_series)
        threshold_series.attachAxis(axis_x)
        threshold_series.attachAxis(axis_y)
    
    def _update_categories(self):
        """Update category counts based on current threshold."""
        # Count tracks in each category
        counts = {category: 0 for category in GemCategory}
        
        for score_data in self.track_scores:
            score = score_data.get('total_score', 0)
            
            # Skip scores below threshold
            if score < self.threshold:
                continue
                
            # Determine category
            category = self._get_category_for_score(score)
            counts[category] += 1
        
        # Update labels
        for category, count_label in self.category_counts.items():
            count_label.setText(str(counts[category]))
    
    def _get_category_for_score(self, score: float) -> GemCategory:
        """Determine gem category for a score.
        
        Args:
            score: Hidden gem score
            
        Returns:
            Gem category
        """
        if score >= 90:
            return GemCategory.DIAMOND
        elif score >= 80:
            return GemCategory.RUBY
        elif score >= 70:
            return GemCategory.EMERALD
        elif score >= 60:
            return GemCategory.SAPPHIRE
        else:
            return GemCategory.QUARTZ
    
    def _get_category_color(self, category: GemCategory) -> QColor:
        """Get the color for a gem category.
        
        Args:
            category: Gem category
            
        Returns:
            Color for the category
        """
        if category == GemCategory.DIAMOND:
            return QColor(0, 191, 255)  # Light blue for diamond
        elif category == GemCategory.RUBY:
            return QColor(220, 20, 60)  # Crimson for ruby
        elif category == GemCategory.EMERALD:
            return QColor(46, 139, 87)  # Sea green for emerald
        elif category == GemCategory.SAPPHIRE:
            return QColor(70, 130, 180)  # Steel blue for sapphire
        else:
            return QColor(153, 153, 153)  # Gray for quartz
    
    @Slot(int)
    def _on_threshold_changed(self, value: int):
        """Handle threshold slider change.
        
        Args:
            value: New threshold value
        """
        self.threshold = value
        self.threshold_label.setText(f"{value}%")
        
        # Update chart and categories
        self._update_chart(self.track_scores)
        self._update_categories()
    
    @Slot()
    def _on_weights_changed(self):
        """Handle weight slider changes."""
        # Update labels
        for name, (slider, label) in self.weight_sliders.items():
            label.setText(f"{slider.value()}%")
        
        # In a real implementation, this would recalculate scores
        # For now, just log the changed weights
        weights = {name: slider.value() for name, (slider, _) in self.weight_sliders.items()}
        logger.info(f"Score weights updated: {weights}")
    
    @Slot()
    def _on_create_playlist(self):
        """Handle create playlist button click."""
        # In a real implementation, this would create a playlist from gems
        # For now, just log the action
        logger.info(f"Create playlist from gems requested (threshold: {self.threshold}%)")
    
    @Slot()
    def _on_export(self):
        """Handle export button click."""
        # In a real implementation, this would export gem data
        # For now, just log the action
        logger.info("Export gems data requested")

class ArtistClusterView(QWidget):
    """Widget for visualizing artist clustering by hidden potential."""
    
    def __init__(self, parent=None):
        """Initialize the artist cluster view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Data
        self.artist_data = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.chart_view)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("View:"))
        
        self.view_combo = QComboBox()
        self.view_combo.addItem("Scatter Plot", "scatter")
        self.view_combo.addItem("Bubble Chart", "bubble")
        self.view_combo.addItem("Heat Map", "heatmap")
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        controls_layout.addWidget(self.view_combo)
        
        controls_layout.addSpacing(20)
        
        self.show_names_check = QCheckBox("Show Artist Names")
        self.show_names_check.setChecked(True)
        self.show_names_check.stateChanged.connect(self._on_show_names_changed)
        controls_layout.addWidget(self.show_names_check)
        
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)
        
        # Create empty chart
        self._create_empty_chart()
    
    def set_artist_data(self, data: List[Dict[str, Any]]):
        """Set artist data for clustering.
        
        Args:
            data: List of artist data
        """
        self.artist_data = data
        self._update_chart()
        
        logger.info(f"Artist cluster view updated with {len(data)} artists")
    
    def _create_empty_chart(self):
        """Create an empty chart with instructions."""
        chart = QChart()
        chart.setTitle("Artist Clustering by Hidden Potential")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        self.chart_view.setChart(chart)
    
    def _update_chart(self):
        """Update the chart based on current data and view type."""
        if not self.artist_data:
            self._create_empty_chart()
            return
            
        # Get current view type
        view_type = self.view_combo.currentData()
        
        # Create appropriate chart
        if view_type == "scatter":
            self._create_scatter_chart()
        elif view_type == "bubble":
            self._create_bubble_chart()
        elif view_type == "heatmap":
            self._create_heatmap_chart()
    
    def _create_scatter_chart(self):
        """Create a scatter plot chart of artists."""
        # This is just a placeholder implementation
        chart = QChart()
        chart.setTitle("Artist Clustering by Hidden Potential")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # In a real implementation, this would create an actual scatter plot
        # of artists based on potential and popularity
        
        self.chart_view.setChart(chart)
    
    def _create_bubble_chart(self):
        """Create a bubble chart of artists."""
        # This is just a placeholder implementation
        chart = QChart()
        chart.setTitle("Artist Potential Bubble Chart")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # In a real implementation, this would create an actual bubble chart
        
        self.chart_view.setChart(chart)
    
    def _create_heatmap_chart(self):
        """Create a heatmap chart of artists."""
        # This is just a placeholder implementation
        chart = QChart()
        chart.setTitle("Artist Potential Heat Map")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # In a real implementation, this would create an actual heat map
        
        self.chart_view.setChart(chart)
    
    @Slot(int)
    def _on_view_changed(self, index: int):
        """Handle view type change.
        
        Args:
            index: Selected index
        """
        self._update_chart()
    
    @Slot(int)
    def _on_show_names_changed(self, state: int):
        """Handle show names checkbox change.
        
        Args:
            state: Checkbox state
        """
        self._update_chart()

class GemIndicator(QWidget):
    """Widget for displaying a visual indicator for gem classification."""
    
    clicked = Signal()
    
    def __init__(self, category: GemCategory, parent=None):
        """Initialize the gem indicator.
        
        Args:
            category: Gem category to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.category = category
        self.color = self._get_category_color(category)
        self.highlight = False
        
        self.setMinimumSize(24, 24)
        self.setMaximumSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def paintEvent(self, event):
        """Paint the gem indicator.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get gem shape based on category
        path = QPainterPath()
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        
        if self.category == GemCategory.DIAMOND:
            # Diamond shape
            path.moveTo(rect.center().position().position().x(), rect.top())
            path.lineTo(rect.right(), rect.center().position().position().y())
            path.lineTo(rect.center().position().position().x(), rect.bottom())
            path.lineTo(rect.left(), rect.center().position().position().y())
            path.closeSubpath()
        elif self.category == GemCategory.RUBY:
            # Ruby shape (octagon)
            third = rect.width() / 3
            path.moveTo(rect.left() + third, rect.top())
            path.lineTo(rect.right() - third, rect.top())
            path.lineTo(rect.right(), rect.top() + third)
            path.lineTo(rect.right(), rect.bottom() - third)
            path.lineTo(rect.right() - third, rect.bottom())
            path.lineTo(rect.left() + third, rect.bottom())
            path.lineTo(rect.left(), rect.bottom() - third)
            path.lineTo(rect.left(), rect.top() + third)
            path.closeSubpath()
        elif self.category == GemCategory.EMERALD:
            # Emerald shape (rectangle)
            path.addRect(rect)
        elif self.category == GemCategory.SAPPHIRE:
            # Sapphire shape (rounded rectangle)
            path.addRoundedRect(rect, 5, 5)
        else:
            # Quartz shape (circle)
            path.addEllipse(rect)
        
        # Fill with gradient
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color)
        
        # Border
        border_color = self.color.darker(120)
        if self.highlight:
            border_color = Qt.GlobalColor.white
        
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)
        
        painter.end()
    
    def _get_category_color(self, category: GemCategory) -> QColor:
        """Get the color for a gem category.
        
        Args:
            category: Gem category
            
        Returns:
            Color for the category
        """
        if category == GemCategory.DIAMOND:
            return QColor(0, 191, 255)  # Light blue for diamond
        elif category == GemCategory.RUBY:
            return QColor(220, 20, 60)  # Crimson for ruby
        elif category == GemCategory.EMERALD:
            return QColor(46, 139, 87)  # Sea green for emerald
        elif category == GemCategory.SAPPHIRE:
            return QColor(70, 130, 180)  # Steel blue for sapphire
        else:
            return QColor(153, 153, 153)  # Gray for quartz
    
    def set_highlight(self, highlight: bool):
        """Set highlight state.
        
        Args:
            highlight: Whether to highlight the gem
        """
        self.highlight = highlight
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        self.clicked.emit()
        super().mousePressEvent(event)

class PopularityComparisonView(QWidget):
    """Widget for comparing hidden gem scores with Spotify popularity."""
    
    def __init__(self, parent=None):
        """Initialize the comparison view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Data
        self.track_data = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Chart title
        main_layout.addWidget(QLabel("<b>Hidden Gems vs. Spotify Popularity</b>"))
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.chart_view)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.invert_check = QCheckBox("Invert Correlation")
        self.invert_check.stateChanged.connect(self._on_invert_changed)
        controls_layout.addWidget(self.invert_check)
        
        controls_layout.addStretch()
        
        self.top_percent_combo = QComboBox()
        self.top_percent_combo.addItem("Show All Tracks", 100)
        self.top_percent_combo.addItem("Top 50%", 50)
        self.top_percent_combo.addItem("Top 25%", 25)
        self.top_percent_combo.addItem("Top 10%", 10)
        self.top_percent_combo.currentIndexChanged.connect(self._on_top_percent_changed)
        controls_layout.addWidget(self.top_percent_combo)
        
        main_layout.addLayout(controls_layout)
        
        # Create empty chart
        self._create_empty_chart()
    
    def set_track_data(self, data: List[Dict[str, Any]]):
        """Set track data for comparison.
        
        Args:
            data: List of track data with scores and popularity
        """
        self.track_data = data
        self._update_chart()
        
        logger.info(f"Popularity comparison updated with {len(data)} tracks")
    
    def _create_empty_chart(self):
        """Create an empty chart with instructions."""
        chart = QChart()
        chart.setTitle("Hidden Gems vs. Spotify Popularity")
        
        self.chart_view.setChart(chart)
    
    def _update_chart(self):
        """Update the chart based on current data."""
        if not self.track_data:
            self._create_empty_chart()
            return
            
        # Create a scatter chart
        chart = QChart()
        chart.setTitle("Hidden Gems vs. Spotify Popularity")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # In a real implementation, this would create an actual scatter chart
        # plotting gem score against Spotify popularity
        
        self.chart_view.setChart(chart)
    
    @Slot(int)
    def _on_invert_changed(self, state: int):
        """Handle invert checkbox change.
        
        Args:
            state: Checkbox state
        """
        self._update_chart()
    
    @Slot(int)
    def _on_top_percent_changed(self, index: int):
        """Handle top percent combo change.
        
        Args:
            index: Selected index
        """
        self._update_chart()

class HiddenGemsVisualization:
    """Main component for visualizing hidden gems analysis."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the hidden gems visualization.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self.config_service = config_service
        self.error_service = error_service
        
        # Create main container widget
        self.container = QTabWidget()
        
        # Score visualization
        self.score_view = HiddenGemsScoreView()
        self.container.addTab(self.score_view, "Gem Scores")
        
        # Artist clustering
        self.artist_view = ArtistClusterView()
        self.container.addTab(self.artist_view, "Artist Clusters")
        
        # Popularity comparison
        self.comparison_view = PopularityComparisonView()
        self.container.addTab(self.comparison_view, "Popularity Comparison")
        
        logger.info("Hidden gems visualization initialized")
    
    @property
    def widget(self) -> QWidget:
        """Get the main widget.
        
        Returns:
            The hidden gems visualization widget
        """
        return self.container
    
    def set_gems_data(self, data: Dict[str, Any]):
        """Set hidden gems data for visualization.
        
        Args:
            data: Dictionary containing hidden gems analysis
        """
        # Update score view
        self.score_view.set_scores(data.get('track_scores', []))
        
        # Update artist view
        self.artist_view.set_artist_data(data.get('artist_data', []))
        
        # Update comparison view
        self.comparison_view.set_track_data(data.get('track_scores', []))
        
        logger.info("Hidden gems data loaded")
    
    def set_current_track(self, track_index: int):
        """Set the currently selected track.
        
        Args:
            track_index: Index of selected track
        """
        self.score_view.set_current_track(track_index) 