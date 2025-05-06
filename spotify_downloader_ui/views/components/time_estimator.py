"""
Time estimation utility for process operations.

This module provides a utility class to estimate remaining time based on
progress and elapsed time information.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

class TimeEstimator:
    """Utility class to estimate remaining time for operations."""
    
    def __init__(self, window_size: int = 10):
        """Initialize the time estimator.
        
        Args:
            window_size: Size of the sliding window for ETA calculations
        """
        self.start_time = None
        self.last_update_time = None
        self.progress_history = deque(maxlen=window_size)
        self.reset()
        
        logger.debug("Time estimator initialized with window size %d", window_size)
    
    def reset(self):
        """Reset the estimator."""
        self.start_time = None
        self.last_update_time = None
        self.progress_history.clear()
    
    def start(self):
        """Start or restart time measurement."""
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.progress_history.clear()
        
        logger.debug("Time estimator started")
    
    def update(self, current: int, total: int) -> Dict:
        """Update progress and calculate time estimates.
        
        Args:
            current: Current progress value
            total: Total progress value
            
        Returns:
            Dict with time estimation data:
                - elapsed_seconds: Seconds since start
                - remaining_seconds: Estimated seconds remaining
                - eta_timestamp: Estimated completion time as timestamp
                - speed: Items per second
                - percent_complete: Percentage complete (0-100)
        """
        if self.start_time is None:
            self.start()
        
        now = time.time()
        elapsed = now - self.start_time
        elapsed_since_last = now - self.last_update_time
        self.last_update_time = now
        
        # Calculate percentage complete
        percent_complete = 0
        if total > 0:
            percent_complete = min(100, (current / total) * 100)
        
        # Store progress point with timestamp
        self.progress_history.append({
            'time': now,
            'current': current,
            'total': total
        })
        
        # Calculate speed (items per second)
        speed = 0
        remaining_seconds = -1  # -1 indicates unknown
        eta_timestamp = None
        
        if len(self.progress_history) >= 2 and total > 0:
            # Get oldest and newest points in our window
            oldest = self.progress_history[0]
            newest = self.progress_history[-1]
            
            time_diff = newest['time'] - oldest['time']
            progress_diff = newest['current'] - oldest['current']
            
            # Calculate speed if we have meaningful data
            if time_diff > 0 and progress_diff > 0:
                speed = progress_diff / time_diff
                
                # Calculate remaining time
                items_remaining = total - current
                if speed > 0:
                    remaining_seconds = items_remaining / speed
                    eta_timestamp = now + remaining_seconds
        
        # Prepare result dictionary
        result = {
            'elapsed_seconds': int(elapsed),
            'remaining_seconds': int(remaining_seconds) if remaining_seconds >= 0 else -1,
            'eta_timestamp': eta_timestamp,
            'speed': speed,
            'percent_complete': percent_complete
        }
        
        logger.debug(f"Time estimate updated: {current}/{total} - ETA: {result['remaining_seconds']}s")
        
        return result
    
    def get_formatted_eta(self) -> str:
        """Get a human-readable ETA string.
        
        Returns:
            Formatted ETA string (e.g., "2m 30s" or "Unknown")
        """
        if not self.progress_history:
            return "Unknown"
        
        # Get the latest estimate
        newest = self.progress_history[-1]
        total = newest['total']
        current = newest['current']
        
        # Update to get the latest estimate
        estimate = self.update(current, total)
        
        remaining = estimate['remaining_seconds']
        if remaining < 0:
            return "Calculating..."
        
        # Format the time
        if remaining < 60:
            return f"{remaining}s"
        elif remaining < 3600:
            minutes = remaining // 60
            seconds = remaining % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_elapsed_time_str(self) -> str:
        """Get formatted elapsed time string.
        
        Returns:
            Formatted elapsed time string
        """
        if self.start_time is None:
            return "00:00"
        
        elapsed = int(time.time() - self.start_time)
        
        if elapsed < 60:
            return f"00:{elapsed:02d}"
        elif elapsed < 3600:
            minutes = elapsed // 60
            seconds = elapsed % 60
            return f"{minutes:02d}:{seconds:02d}"
        else:
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}" 