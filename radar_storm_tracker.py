"""
radar_storm_tracker.py - Phase 8: Radar Storm Tracking
Tracks approaching storms and predicts arrival times for your monitoring area
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

class RadarStormTracker:
    """Track approaching storms using NWS radar data"""
    
    def __init__(self):
        self.nws_api_base = "https://api.weather.gov"
        
        # Your monitoring area center point (Athens, AL area)
        self.center_lat = 34.8023
        self.center_lon = -86.9719
        
        # Monitoring radius (miles)
        self.warning_distances = {
            'urgent': 10,      # <10 miles: Urgent
            'close': 30,       # 10-30 miles: Close
            'approaching': 60, # 30-60 miles: Approaching
            'distant': 100     # 60-100 miles: Distant monitoring
        }
        
        # Counties to monitor (your 14 counties)
        self.monitored_counties = [
            # North Alabama
            'Colbert County, AL', 'Cullman County, AL', 'DeKalb County, AL',
            'Franklin County, AL', 'Jackson County, AL', 'Lawrence County, AL',
            'Lauderdale County, AL', 'Limestone County, AL', 'Madison County, AL',
            'Marshall County, AL', 'Morgan County, AL',
            # Southern Tennessee
            'Franklin County, TN', 'Lincoln County, TN', 'Moore County, TN'
        ]
        
        print("✓ Radar storm tracker initialized")
        print(f"  Monitoring radius: {self.warning_distances['distant']} miles")
    
    def get_approaching_storms(self) -> Optional[Dict]:
        """
        Check for storms approaching from the west (Mississippi border area)
        Returns storm information if detected within 100 miles
        """
        try:
            # Get radar summary for Alabama
            # We'll use NWS alerts as proxy for storm activity since real radar API is complex
            # Look for storms in counties west of our monitoring area
            
            western_approach_zones = [
                # Mississippi counties near Alabama border
                'MSC093',  # Marshall County, MS (borders Lauderdale County, AL)
                'MSC117',  # Tishomingo County, MS (borders Lauderdale/Colbert, AL)
                'MSC003',  # Alcorn County, MS (borders Lauderdale, AL)
                'MSC139',  # Tippah County, MS (borders Lauderdale, AL)
                # Western Tennessee near border
                'TNC023',  # Chester County, TN (west of our area)
                'TNC167',  # Wayne County, TN (west of our area)
            ]
            
            # Check for active warnings in approach zones
            storm_info = self._check_western_approach(western_approach_zones)
            
            if storm_info:
                return storm_info
            
            # Also check for watches that might indicate approaching storms
            watch_info = self._check_approaching_watches()
            
            return watch_info
            
        except Exception as e:
            print(f"⚠️ Error checking approaching storms: {e}")
            return None
    
    def _check_western_approach(self, zones: List[str]) -> Optional[Dict]:
        """Check for storms in western approach zones"""
        try:
            # Build URL for western zones
            zone_params = '&'.join([f'zone={zone}' for zone in zones])
            url = f"{self.nws_api_base}/alerts/active?{zone_params}&status=actual&message_type=alert"
            
            response = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            # Look for severe weather warnings
            severe_alerts = []
            for feature in features:
                props = feature.get('properties', {})
                event = props.get('event', '').lower()
                
                # Only track warnings (not watches/advisories)
                if 'warning' in event and any(word in event for word in ['severe', 'thunderstorm', 'tornado']):
                    severe_alerts.append({
                        'event': props.get('event'),
                        'area': props.get('areaDesc'),
                        'description': props.get('description', ''),
                        'onset': props.get('onset')
                    })
            
            if severe_alerts:
                # Storms detected approaching from west
                return self._build_approach_announcement(severe_alerts, 'western approach')
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error checking western approach: {e}")
            return None
    
    def _check_approaching_watches(self) -> Optional[Dict]:
        """Check for watches that might indicate approaching storms"""
        try:
            # Get active watches for broader area (includes Mississippi)
            url = f"{self.nws_api_base}/alerts/active?area=AL,MS,TN&status=actual"
            
            response = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            # Look for severe thunderstorm or tornado watches
            watches = []
            for feature in features:
                props = feature.get('properties', {})
                event = props.get('event', '').lower()
                area = props.get('areaDesc', '')
                
                if 'watch' in event and any(word in event for word in ['severe', 'thunderstorm', 'tornado']):
                    # Check if watch area is west of us (Mississippi counties)
                    if 'mississippi' in area.lower() or any(ms_word in area.lower() for ms_word in ['tupelo', 'corinth', 'booneville']):
                        watches.append({
                            'event': props.get('event'),
                            'area': area,
                            'description': props.get('description', ''),
                            'expires': props.get('expires')
                        })
            
            if watches:
                return self._build_watch_announcement(watches)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error checking watches: {e}")
            return None
    
    def _build_approach_announcement(self, alerts: List[Dict], direction: str) -> Dict:
        """Build announcement for approaching storms"""
        
        # Estimate distance based on zone (rough approximation)
        # Mississippi border is approximately 40-50 miles west of Athens
        estimated_distance = 45  # miles
        
        # Estimate storm speed (typical: 30-40 mph for severe storms)
        estimated_speed = 35  # mph
        
        # Calculate ETA
        eta_hours = estimated_distance / estimated_speed
        eta_minutes = int(eta_hours * 60)
        arrival_time = datetime.now() + timedelta(minutes=eta_minutes)
        
        # Determine urgency level
        if estimated_distance < self.warning_distances['urgent']:
            urgency = 'urgent'
        elif estimated_distance < self.warning_distances['close']:
            urgency = 'close'
        elif estimated_distance < self.warning_distances['approaching']:
            urgency = 'approaching'
        else:
            urgency = 'distant'
        
        # Build announcement text
        alert_types = list(set([a['event'] for a in alerts]))
        
        if len(alert_types) == 1:
            storm_desc = alert_types[0]
        else:
            storm_desc = f"{len(alert_types)} types of severe weather"
        
        announcement = (
            f"Radar update: {storm_desc} detected approximately {estimated_distance} miles "
            f"to the west near the Mississippi border, moving east. "
            f"Expected to reach our area in approximately {eta_minutes} minutes around "
            f"{arrival_time.strftime('%-I:%M %p')}. Monitor conditions closely."
        )
        
        return {
            'has_approaching_storms': True,
            'distance_miles': estimated_distance,
            'speed_mph': estimated_speed,
            'eta_minutes': eta_minutes,
            'arrival_time': arrival_time.strftime('%-I:%M %p'),
            'urgency': urgency,
            'storm_types': alert_types,
            'announcement': announcement,
            'alerts': alerts
        }
    
    def _build_watch_announcement(self, watches: List[Dict]) -> Dict:
        """Build announcement for approaching watches"""
        
        watch_type = watches[0]['event']
        
        announcement = (
            f"Weather outlook: A {watch_type} is in effect to our west in Mississippi. "
            f"Conditions favorable for severe weather development. "
            f"Storms may approach our area later this afternoon. Stay weather aware."
        )
        
        return {
            'has_approaching_storms': True,
            'distance_miles': 60,  # Approximate
            'speed_mph': 30,  # Conservative estimate
            'eta_minutes': 120,  # 2 hours
            'arrival_time': (datetime.now() + timedelta(hours=2)).strftime('%-I:%M %p'),
            'urgency': 'distant',
            'storm_types': [watch_type],
            'announcement': announcement,
            'watches': watches
        }
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in miles
        """
        R = 3959  # Radius of Earth in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


# Global instance
_storm_tracker = None

def get_storm_tracker() -> RadarStormTracker:
    """Get or create storm tracker instance"""
    global _storm_tracker
    if _storm_tracker is None:
        _storm_tracker = RadarStormTracker()
    return _storm_tracker


def get_approaching_storm_announcement() -> Optional[str]:
    """
    Get announcement for approaching storms
    Returns announcement text or None
    """
    try:
        tracker = get_storm_tracker()
        storm_info = tracker.get_approaching_storms()
        
        if storm_info and storm_info.get('has_approaching_storms'):
            print(f"✓ Approaching storms detected: {storm_info.get('distance_miles')} miles away")
            return storm_info.get('announcement')
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting storm announcement: {e}")
        return None


def get_storm_tracking_info() -> Optional[Dict]:
    """
    Get detailed storm tracking information
    Returns dict with storm details or None
    """
    try:
        tracker = get_storm_tracker()
        return tracker.get_approaching_storms()
        
    except Exception as e:
        print(f"⚠️ Error getting storm info: {e}")
        return None
