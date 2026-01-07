"""
alert_trends.py - NorthBamaWX Alert Trend Analysis
Tracks alert patterns and identifies severe weather outbreaks
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class AlertTrendAnalyzer:
    """Analyzes alert trends and patterns over time"""
    
    def __init__(self):
        # Track alerts over time
        self.alert_history = []
        self.max_history_hours = 24
        
        # Alert type categories
        self.severe_types = ['tornado warning', 'severe thunderstorm warning', 'flash flood warning']
        self.watch_types = ['tornado watch', 'severe thunderstorm watch', 'flood watch']
        
    def add_alert(self, alert: Dict):
        """
        Add an alert to the history tracker
        
        Args:
            alert: Alert dictionary with event, timestamp, etc.
        """
        try:
            alert_record = {
                'event': alert.get('event', ''),
                'timestamp': datetime.now(timezone.utc),
                'id': alert.get('id', ''),
                'severity': alert.get('severity', ''),
                'urgency': alert.get('urgency', ''),
                'certainty': alert.get('certainty', '')
            }
            
            self.alert_history.append(alert_record)
            
            # Clean old history (beyond 24 hours)
            self._cleanup_old_history()
            
        except Exception as e:
            logger.error(f"Error adding alert to trend tracker: {e}")
    
    def _cleanup_old_history(self):
        """Remove alerts older than max_history_hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_history_hours)
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert['timestamp'] > cutoff
        ]
    
    def analyze_trends(self, current_alerts: List[Dict]) -> Optional[Dict]:
        """
        Analyze current alert trends and patterns
        
        Args:
            current_alerts: List of currently active alerts
            
        Returns:
            Trend analysis dictionary or None
        """
        try:
            # Update history with current alerts
            for alert in current_alerts:
                if alert.get('id') not in [a.get('id') for a in self.alert_history[-10:]]:
                    self.add_alert(alert)
            
            analysis = {
                'is_outbreak': False,
                'activity_level': 'normal',
                'trend_direction': 'stable',
                'alert_count_1h': 0,
                'alert_count_3h': 0,
                'alert_count_6h': 0,
                'severe_warning_count': 0,
                'tornado_warning_count': 0,
                'watch_count': 0,
                'notable_patterns': []
            }
            
            # Count alerts in different time windows
            now = datetime.now(timezone.utc)
            
            for alert in self.alert_history:
                age = now - alert['timestamp']
                event_lower = alert['event'].lower()
                
                # Count by time period
                if age <= timedelta(hours=1):
                    analysis['alert_count_1h'] += 1
                if age <= timedelta(hours=3):
                    analysis['alert_count_3h'] += 1
                if age <= timedelta(hours=6):
                    analysis['alert_count_6h'] += 1
                
                # Count by type (last 3 hours)
                if age <= timedelta(hours=3):
                    if 'tornado warning' in event_lower:
                        analysis['tornado_warning_count'] += 1
                    elif 'severe thunderstorm warning' in event_lower or 'flash flood warning' in event_lower:
                        analysis['severe_warning_count'] += 1
                    elif 'watch' in event_lower:
                        analysis['watch_count'] += 1
            
            # Determine activity level
            analysis['activity_level'] = self._calculate_activity_level(analysis)
            
            # Determine trend direction (comparing 1h vs 3h)
            analysis['trend_direction'] = self._calculate_trend_direction(analysis)
            
            # Check for outbreak pattern
            analysis['is_outbreak'] = self._detect_outbreak(analysis)
            
            # Identify notable patterns
            analysis['notable_patterns'] = self._identify_patterns(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing alert trends: {e}")
            return None
    
    def _calculate_activity_level(self, analysis: Dict) -> str:
        """Determine overall activity level"""
        count_1h = analysis['alert_count_1h']
        tornado_count = analysis['tornado_warning_count']
        severe_count = analysis['severe_warning_count']
        
        # High activity thresholds
        if tornado_count >= 2 or count_1h >= 5:
            return 'high'
        elif severe_count >= 3 or count_1h >= 3:
            return 'elevated'
        elif count_1h >= 1:
            return 'moderate'
        else:
            return 'normal'
    
    def _calculate_trend_direction(self, analysis: Dict) -> str:
        """Determine if alerts are increasing, decreasing, or stable"""
        count_1h = analysis['alert_count_1h']
        count_3h = analysis['alert_count_3h']
        
        # If no recent activity
        if count_3h == 0:
            return 'stable'
        
        # Calculate rate (alerts per hour)
        rate_1h = count_1h  # Already per hour
        rate_3h = count_3h / 3.0
        
        # Compare rates
        if rate_1h > rate_3h * 1.5:  # 50% increase
            return 'increasing'
        elif rate_1h < rate_3h * 0.5:  # 50% decrease
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_outbreak(self, analysis: Dict) -> bool:
        """Detect if this is a severe weather outbreak"""
        tornado_count = analysis['tornado_warning_count']
        severe_count = analysis['severe_warning_count']
        count_3h = analysis['alert_count_3h']
        
        # Outbreak criteria:
        # - Multiple tornado warnings, OR
        # - Many severe warnings in short time, OR
        # - High total alert count
        
        if tornado_count >= 2:  # Multiple tornado warnings
            return True
        elif severe_count >= 4:  # Many severe warnings
            return True
        elif count_3h >= 8:  # High total alert volume
            return True
        
        return False
    
    def _identify_patterns(self, analysis: Dict) -> List[str]:
        """Identify notable patterns in alert activity"""
        patterns = []
        
        tornado_count = analysis['tornado_warning_count']
        severe_count = analysis['severe_warning_count']
        count_1h = analysis['alert_count_1h']
        activity = analysis['activity_level']
        trend = analysis['trend_direction']
        
        # Pattern: Multiple tornado warnings
        if tornado_count >= 2:
            patterns.append('multiple_tornadoes')
        elif tornado_count == 1:
            patterns.append('tornado_warning')
        
        # Pattern: Rapid alert issuance
        if count_1h >= 3:
            patterns.append('rapid_development')
        
        # Pattern: Persistent severe weather
        if severe_count >= 3:
            patterns.append('persistent_severe')
        
        # Pattern: Escalating situation
        if trend == 'increasing' and activity in ['elevated', 'high']:
            patterns.append('escalating')
        
        # Pattern: Improving conditions
        if trend == 'decreasing' and count_1h == 0:
            patterns.append('improving')
        
        return patterns
    
    def format_trend_announcement(self, analysis: Dict) -> Optional[str]:
        """
        Format trend analysis into natural language announcement
        
        Args:
            analysis: Trend analysis dictionary
            
        Returns:
            Natural language trend description or None
        """
        if not analysis:
            return None
        
        activity = analysis['activity_level']
        trend = analysis['trend_direction']
        patterns = analysis['notable_patterns']
        tornado_count = analysis['tornado_warning_count']
        count_1h = analysis['alert_count_1h']
        count_3h = analysis['alert_count_3h']
        
        # Don't announce if activity is normal
        if activity == 'normal' and not patterns:
            return None
        
        parts = []
        
        # Outbreak announcement (highest priority)
        if analysis['is_outbreak']:
            parts.append("Severe weather outbreak in progress across our area.")
        
        # Multiple tornado warnings
        elif 'multiple_tornadoes' in patterns:
            parts.append(f"Multiple tornado warnings have been issued in the past three hours.")
        
        # Single tornado warning
        elif 'tornado_warning' in patterns:
            parts.append("A tornado warning is in effect.")
        
        # Activity level announcement
        if activity == 'high' and not analysis['is_outbreak']:
            parts.append("Alert activity is high.")
        elif activity == 'elevated':
            parts.append("Alert activity is elevated.")
        
        # Trend direction
        if trend == 'increasing' and activity in ['elevated', 'high']:
            parts.append("Alert activity has increased in the past hour.")
        elif trend == 'decreasing' and count_1h == 0 and count_3h > 0:
            parts.append("Alert activity is decreasing.")
        
        # Pattern-specific announcements
        if 'rapid_development' in patterns:
            parts.append(f"{count_1h} alerts issued in the last hour.")
        
        if 'persistent_severe' in patterns and 'multiple_tornadoes' not in patterns:
            parts.append("Severe weather has persisted across the region.")
        
        # Combine all parts
        if parts:
            return " ".join(parts)
        
        return None


# Singleton instance
_trend_analyzer = None

def get_trend_analyzer() -> AlertTrendAnalyzer:
    """Get singleton AlertTrendAnalyzer instance"""
    global _trend_analyzer
    if _trend_analyzer is None:
        _trend_analyzer = AlertTrendAnalyzer()
    return _trend_analyzer


def get_alert_trend_announcement(current_alerts: List[Dict]) -> Optional[str]:
    """
    Convenience function to get trend announcement for current alerts
    
    Args:
        current_alerts: List of currently active alerts
        
    Returns:
        Formatted trend announcement or None
    """
    analyzer = get_trend_analyzer()
    analysis = analyzer.analyze_trends(current_alerts)
    
    if analysis:
        return analyzer.format_trend_announcement(analysis)
    
    return None
