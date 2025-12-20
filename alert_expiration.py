"""
alert_expiration.py - Track and Announce Alert Expirations
Monitors when warnings/watches expire and announces them
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class AlertExpirationTracker:
    """Tracks active alerts and announces when they expire"""
    
    def __init__(self):
        self.active_alerts = {}  # alert_id -> alert_data
        self.recently_expired = []  # List of recently expired alerts
        self.expiration_window = timedelta(minutes=5)  # How recent is "recently expired"
    
    def update_active_alerts(self, current_alerts: List[Dict]):
        """
        Update list of active alerts and detect expirations
        
        Args:
            current_alerts: List of currently active NWS alerts
        
        Returns:
            List of alerts that just expired
        """
        current_time = datetime.now()
        current_alert_ids = set()
        newly_expired = []
        
        # Track all current alert IDs
        for alert in current_alerts:
            alert_id = alert.get('id')
            if not alert_id:
                continue
            
            current_alert_ids.add(alert_id)
            
            # Add to active alerts if new
            if alert_id not in self.active_alerts:
                self.active_alerts[alert_id] = {
                    'id': alert_id,
                    'event': alert.get('event'),
                    'areaDesc': alert.get('areaDesc'),
                    'onset': alert.get('onset'),
                    'expires': alert.get('expires'),
                    'first_seen': current_time.isoformat()
                }
        
        # Find alerts that were active but are no longer in the list
        for alert_id, alert_data in list(self.active_alerts.items()):
            if alert_id not in current_alert_ids:
                # This alert has expired or was cancelled
                expired_alert = self.active_alerts.pop(alert_id)
                
                # Add to recently expired list
                expired_alert['expired_at'] = current_time.isoformat()
                newly_expired.append(expired_alert)
                self.recently_expired.append(expired_alert)
        
        # Clean up old expired alerts (older than expiration window)
        cutoff_time = current_time - self.expiration_window
        self.recently_expired = [
            alert for alert in self.recently_expired
            if datetime.fromisoformat(alert['expired_at']) > cutoff_time
        ]
        
        return newly_expired
    
    def get_expiration_announcements(self, expired_alerts: List[Dict]) -> List[str]:
        """
        Generate announcement text for expired alerts
        
        Args:
            expired_alerts: List of alerts that just expired
        
        Returns:
            List of announcement strings
        """
        announcements = []
        
        for alert in expired_alerts:
            event = alert.get('event', 'Alert')
            area = alert.get('areaDesc', 'the area')
            
            # Simplify area description (take first county if multiple)
            if ';' in area:
                area = area.split(';')[0].strip()
            
            # Create announcement based on alert type
            if 'warning' in event.lower():
                # Warnings - more urgent tone
                announcement = f"The {event} for {area} has expired."
            elif 'watch' in event.lower():
                # Watches - less urgent
                announcement = f"The {event} for {area} has been cancelled."
            elif 'advisory' in event.lower():
                # Advisories
                announcement = f"The {event} for {area} is no longer in effect."
            else:
                # Generic
                announcement = f"The {event} for {area} has ended."
            
            announcements.append(announcement)
        
        return announcements
    
    def get_expiration_summary(self, expired_alerts: List[Dict]) -> Optional[str]:
        """
        Get a summary of multiple expirations
        
        Args:
            expired_alerts: List of expired alerts
        
        Returns:
            Summary text or None
        """
        if not expired_alerts:
            return None
        
        if len(expired_alerts) == 1:
            # Single expiration - use full announcement
            return self.get_expiration_announcements(expired_alerts)[0]
        
        # Multiple expirations - group by type
        warnings = []
        watches = []
        advisories = []
        
        for alert in expired_alerts:
            event = alert.get('event', '')
            area = alert.get('areaDesc', '')
            
            # Simplify area
            if ';' in area:
                area = area.split(';')[0].strip()
            
            if 'warning' in event.lower():
                warnings.append(area)
            elif 'watch' in event.lower():
                watches.append(area)
            else:
                advisories.append(area)
        
        # Build summary
        parts = []
        
        if warnings:
            if len(warnings) == 1:
                parts.append(f"Warning for {warnings[0]} has expired")
            else:
                parts.append(f"{len(warnings)} warnings have expired")
        
        if watches:
            if len(watches) == 1:
                parts.append(f"Watch for {watches[0]} has been cancelled")
            else:
                parts.append(f"{len(watches)} watches have been cancelled")
        
        if advisories:
            if len(advisories) == 1:
                parts.append(f"Advisory for {advisories[0]} is no longer in effect")
            else:
                parts.append(f"{len(advisories)} advisories are no longer in effect")
        
        if parts:
            return "Update: " + ", and ".join(parts) + "."
        
        return None
    
    def should_announce_expirations(self, broadcast_type: str = 'any') -> bool:
        """
        Determine if expirations should be announced in this broadcast
        
        Args:
            broadcast_type: Type of broadcast
        
        Returns:
            True if should announce
        """
        # Announce expirations at :15 and :45 (alert-focused broadcasts)
        return broadcast_type in ['top_alerts', 'weather_story', 'quarter_past']
    
    def get_count_summary(self) -> str:
        """
        Get summary of currently tracked alerts
        
        Returns:
            Summary string
        """
        active_count = len(self.active_alerts)
        expired_count = len(self.recently_expired)
        
        return f"{active_count} active alerts, {expired_count} recently expired"


# Singleton instance
_expiration_tracker = None

def get_expiration_tracker():
    """Get singleton expiration tracker"""
    global _expiration_tracker
    if _expiration_tracker is None:
        _expiration_tracker = AlertExpirationTracker()
    return _expiration_tracker


def check_for_expirations(current_alerts: List[Dict]) -> List[Dict]:
    """
    Check for newly expired alerts
    
    Args:
        current_alerts: Current active alerts from NWS
    
    Returns:
        List of alerts that just expired
    """
    tracker = get_expiration_tracker()
    return tracker.update_active_alerts(current_alerts)


def get_expiration_announcement(expired_alerts: List[Dict]) -> Optional[str]:
    """
    Get announcement for expired alerts
    
    Args:
        expired_alerts: List of expired alerts
    
    Returns:
        Announcement text or None
    """
    tracker = get_expiration_tracker()
    return tracker.get_expiration_summary(expired_alerts)


if __name__ == '__main__':
    # Test the expiration tracker
    print("=" * 70)
    print("ALERT EXPIRATION TRACKER TEST")
    print("=" * 70)
    
    tracker = AlertExpirationTracker()
    
    # Simulate alerts at time 1
    print("\n1. Initial alerts (3 active)")
    print("-" * 70)
    
    alerts_t1 = [
        {
            'id': 'alert1',
            'event': 'Tornado Warning',
            'areaDesc': 'Madison County, AL',
            'onset': '2025-12-20T14:00:00Z',
            'expires': '2025-12-20T14:30:00Z'
        },
        {
            'id': 'alert2',
            'event': 'Severe Thunderstorm Warning',
            'areaDesc': 'Morgan County, AL',
            'onset': '2025-12-20T14:00:00Z',
            'expires': '2025-12-20T14:45:00Z'
        },
        {
            'id': 'alert3',
            'event': 'Tornado Watch',
            'areaDesc': 'North Alabama',
            'onset': '2025-12-20T13:00:00Z',
            'expires': '2025-12-20T18:00:00Z'
        }
    ]
    
    expired = tracker.update_active_alerts(alerts_t1)
    print(f"Active alerts: {len(tracker.active_alerts)}")
    print(f"Newly expired: {len(expired)}")
    
    # Simulate alerts at time 2 (one expired)
    print("\n2. Update after 30 minutes (1 expired)")
    print("-" * 70)
    
    alerts_t2 = [
        {
            'id': 'alert2',
            'event': 'Severe Thunderstorm Warning',
            'areaDesc': 'Morgan County, AL',
            'onset': '2025-12-20T14:00:00Z',
            'expires': '2025-12-20T14:45:00Z'
        },
        {
            'id': 'alert3',
            'event': 'Tornado Watch',
            'areaDesc': 'North Alabama',
            'onset': '2025-12-20T13:00:00Z',
            'expires': '2025-12-20T18:00:00Z'
        }
    ]
    
    expired = tracker.update_active_alerts(alerts_t2)
    print(f"Active alerts: {len(tracker.active_alerts)}")
    print(f"Newly expired: {len(expired)}")
    
    if expired:
        print(f"\nExpired alert: {expired[0]['event']} for {expired[0]['areaDesc']}")
        announcement = tracker.get_expiration_summary(expired)
        print(f"Announcement: {announcement}")
    
    # Simulate all alerts expiring
    print("\n3. Update after all expire")
    print("-" * 70)
    
    alerts_t3 = []
    
    expired = tracker.update_active_alerts(alerts_t3)
    print(f"Active alerts: {len(tracker.active_alerts)}")
    print(f"Newly expired: {len(expired)}")
    
    if expired:
        print(f"\nExpired {len(expired)} alerts")
        announcement = tracker.get_expiration_summary(expired)
        print(f"Announcement: {announcement}")
    
    print("\n" + "=" * 70)
    print("✓ Alert expiration tracker working!")
    print("=" * 70)
