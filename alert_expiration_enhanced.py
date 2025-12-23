"""
alert_expiration_enhanced.py - NorthBamaWX Enhanced Alert Expiration System
Improved expiration tracking with countdown warnings and all-clear announcements
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EnhancedAlertExpiration:
    """Enhanced alert expiration tracking with countdowns and all-clear announcements"""
    
    def __init__(self):
        # Thresholds for different announcement types
        self.countdown_thresholds = [30, 15, 5]  # Minutes before expiration
        self.recently_expired_window = 10  # Minutes to track after expiration
        
    def analyze_expirations(self, active_alerts: List[Dict]) -> Dict:
        """
        Analyze alert expirations and generate announcements
        
        Args:
            active_alerts: List of currently active alerts
            
        Returns:
            Dictionary with expiration analysis
        """
        try:
            now = datetime.utcnow()
            
            analysis = {
                'expiring_soon': [],      # Alerts expiring in <30 min
                'expiring_imminent': [],  # Alerts expiring in <5 min
                'should_announce_countdown': False,
                'countdown_alerts': [],
                'expires_text': None
            }
            
            for alert in active_alerts:
                expires = self._parse_expiration(alert)
                if not expires:
                    continue
                
                time_until_expiry = expires - now
                minutes_remaining = time_until_expiry.total_seconds() / 60
                
                # Categorize by time remaining
                if 0 < minutes_remaining <= 30:
                    analysis['expiring_soon'].append({
                        'alert': alert,
                        'minutes': int(minutes_remaining),
                        'expires': expires
                    })
                    
                    # Check if we should announce countdown
                    if self._should_announce_countdown(minutes_remaining):
                        analysis['countdown_alerts'].append({
                            'event': alert.get('event', 'Weather Alert'),
                            'area': alert.get('areaDesc', 'the area'),
                            'minutes': int(minutes_remaining)
                        })
                        analysis['should_announce_countdown'] = True
                
                if 0 < minutes_remaining <= 5:
                    analysis['expiring_imminent'].append({
                        'alert': alert,
                        'minutes': int(minutes_remaining)
                    })
            
            # Generate announcement text
            if analysis['countdown_alerts']:
                analysis['expires_text'] = self._format_expiration_announcement(
                    analysis['countdown_alerts']
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing alert expirations: {e}")
            return {
                'expiring_soon': [],
                'expiring_imminent': [],
                'should_announce_countdown': False,
                'countdown_alerts': [],
                'expires_text': None
            }
    
    def _parse_expiration(self, alert: Dict) -> Optional[datetime]:
        """Parse alert expiration time"""
        try:
            # Check for 'expires' field
            expires_str = alert.get('expires')
            if expires_str:
                # Handle ISO format
                return datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
            
            # Check for 'ends' field (some alerts use this)
            ends_str = alert.get('ends')
            if ends_str:
                return datetime.fromisoformat(ends_str.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.error(f"Error parsing expiration time: {e}")
        
        return None
    
    def _should_announce_countdown(self, minutes_remaining: float) -> bool:
        """Determine if we should announce countdown for this alert"""
        # Announce at specific thresholds: 30, 15, 5 minutes
        for threshold in self.countdown_thresholds:
            # Within 1 minute of threshold (accounts for 15-min broadcast cycle)
            if threshold - 1 <= minutes_remaining <= threshold + 1:
                return True
        
        return False
    
    def _format_expiration_announcement(self, countdown_alerts: List[Dict]) -> str:
        """Format expiration countdown announcement"""
        if not countdown_alerts:
            return ""
        
        parts = []
        
        # Group by time remaining
        by_time = {}
        for alert in countdown_alerts:
            minutes = alert['minutes']
            if minutes not in by_time:
                by_time[minutes] = []
            by_time[minutes].append(alert)
        
        # Format each time group
        for minutes in sorted(by_time.keys()):
            alerts = by_time[minutes]
            
            if len(alerts) == 1:
                alert = alerts[0]
                event = alert['event']
                area = self._simplify_area(alert['area'])
                
                if minutes <= 5:
                    parts.append(f"The {event} for {area} expires in {minutes} minutes.")
                elif minutes <= 15:
                    parts.append(f"The {event} for {area} expires in {minutes} minutes.")
                else:
                    parts.append(f"The {event} for {area} expires in {minutes} minutes.")
            
            else:
                # Multiple alerts expiring at same time
                event_types = [a['event'] for a in alerts]
                unique_events = list(set(event_types))
                
                if len(unique_events) == 1:
                    parts.append(f"Multiple {unique_events[0]}s expire in {minutes} minutes.")
                else:
                    parts.append(f"Several weather alerts expire in {minutes} minutes.")
        
        return " ".join(parts)
    
    def _simplify_area(self, area_desc: str) -> str:
        """Simplify area description for natural speech"""
        if not area_desc:
            return "the area"
        
        # If very long, just use first county
        if ';' in area_desc and len(area_desc) > 50:
            first_area = area_desc.split(';')[0].strip()
            return f"{first_area} and surrounding areas"
        
        # Replace semicolons with "and"
        simplified = area_desc.replace(';', ' and')
        
        return simplified
    
    def get_all_clear_announcement(self, recently_expired: List[Dict]) -> Optional[str]:
        """
        Generate all-clear announcement for recently expired alerts
        
        Args:
            recently_expired: List of alerts that expired in last few minutes
            
        Returns:
            All-clear announcement or None
        """
        if not recently_expired:
            return None
        
        try:
            # Check for severe warnings that just expired
            severe_expired = [
                alert for alert in recently_expired
                if 'warning' in alert.get('event', '').lower()
            ]
            
            if not severe_expired:
                return None
            
            # Group by type
            tornado_warnings = [a for a in severe_expired if 'tornado' in a.get('event', '').lower()]
            severe_warnings = [a for a in severe_expired if 'severe' in a.get('event', '').lower()]
            flood_warnings = [a for a in severe_expired if 'flood' in a.get('event', '').lower()]
            
            parts = []
            
            # Announce tornado warnings ending first (most important)
            if tornado_warnings:
                if len(tornado_warnings) == 1:
                    area = self._simplify_area(tornado_warnings[0].get('areaDesc', 'the area'))
                    parts.append(f"The Tornado Warning for {area} has expired.")
                else:
                    parts.append(f"{len(tornado_warnings)} Tornado Warnings have expired.")
            
            # Then severe thunderstorm warnings
            if severe_warnings:
                if len(severe_warnings) == 1:
                    area = self._simplify_area(severe_warnings[0].get('areaDesc', 'the area'))
                    parts.append(f"The Severe Thunderstorm Warning for {area} has expired.")
                else:
                    parts.append(f"{len(severe_warnings)} Severe Thunderstorm Warnings have expired.")
            
            # Then flood warnings
            if flood_warnings:
                if len(flood_warnings) == 1:
                    parts.append(f"The Flood Warning has expired.")
                else:
                    parts.append(f"{len(flood_warnings)} Flood Warnings have expired.")
            
            # Add closing
            if parts:
                announcement = " ".join(parts)
                announcement += " Continue to monitor conditions."
                return announcement
            
        except Exception as e:
            logger.error(f"Error generating all-clear announcement: {e}")
        
        return None


# Singleton instance
_expiration_tracker = None

def get_expiration_tracker() -> EnhancedAlertExpiration:
    """Get singleton EnhancedAlertExpiration instance"""
    global _expiration_tracker
    if _expiration_tracker is None:
        _expiration_tracker = EnhancedAlertExpiration()
    return _expiration_tracker


def get_expiration_announcement(active_alerts: List[Dict]) -> Optional[str]:
    """
    Convenience function to get expiration announcement
    
    Args:
        active_alerts: List of currently active alerts
        
    Returns:
        Formatted expiration announcement or None
    """
    tracker = get_expiration_tracker()
    analysis = tracker.analyze_expirations(active_alerts)
    return analysis.get('expires_text')
