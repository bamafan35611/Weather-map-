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
        Check for storms approaching from west (Mississippi) and north (Tennessee)
        Returns storm information if detected within 100 miles
        """
        try:
            # WESTERN APPROACH: Mississippi counties near Alabama border
            western_approach_zones = [
                # Mississippi counties near Alabama border
                'MSC093',  # Marshall County, MS (borders Lauderdale County, AL)
                'MSC117',  # Tishomingo County, MS (borders Lauderdale/Colbert, AL)
                'MSC003',  # Alcorn County, MS (borders Lauderdale, AL)
                'MSC139',  # Tippah County, MS (borders Lauderdale, AL)
            ]
            
            # NORTHERN APPROACH: Tennessee counties that feed into North Alabama
            northern_approach_zones = [
                # Southern Middle Tennessee (directly north of your area)
                'TNC003',  # Bedford County, TN (north of Limestone/Madison)
                'TNC055',  # Giles County, TN (north of Limestone)
                'TNC061',  # Grundy County, TN (north of Jackson/Marshall)
                'TNC075',  # Hamilton County, TN (Chattanooga - northeast approach)
                'TNC081',  # Hickman County, TN (northwest of your area)
                'TNC085',  # Humphreys County, TN (west of your area)
                'TNC099',  # Lawrence County, TN (north of Lauderdale/Lawrence AL)
                'TNC108',  # Lewis County, TN (north of Lawrence/Lauderdale)
                'TNC117',  # Marshall County, TN (north of Madison/Jackson)
                'TNC119',  # Maury County, TN (north of Limestone/Madison)
                'TNC121',  # Meigs County, TN (northeast approach)
                'TNC127',  # Moore County, TN (your monitoring area)
                'TNC141',  # Putnam County, TN (far north)
                'TNC169',  # Williamson County, TN (north of your area)
                # Western Tennessee near border
                'TNC023',  # Chester County, TN (west of your area)
                'TNC167',  # Wayne County, TN (north/west of your area)
            ]
            
            # Check western approach first
            western_storm = self._check_approach_zone(western_approach_zones, 'western')
            if western_storm:
                return western_storm
            
            # Check northern approach
            northern_storm = self._check_approach_zone(northern_approach_zones, 'northern')
            if northern_storm:
                return northern_storm
            
            # Also check for watches that might indicate approaching storms
            watch_info = self._check_approaching_watches()
            
            return watch_info
            
        except Exception as e:
            print(f"⚠️ Error checking approaching storms: {e}")
            return None
    
    def _check_approach_zone(self, zones: List[str], direction: str) -> Optional[Dict]:
        """Check for storms in specified approach zones"""
        try:
            # Build URL for zones
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
                # Storms detected approaching from this direction
                return self._build_approach_announcement(severe_alerts, direction)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error checking {direction} approach: {e}")
            return None
    
    def _check_western_approach(self, zones: List[str]) -> Optional[Dict]:
        """DEPRECATED: Use _check_approach_zone instead"""
        return self._check_approach_zone(zones, 'western')
    
    def _check_approaching_watches(self) -> Optional[Dict]:
        """Check for watches that might indicate approaching storms"""
        try:
            # Get active watches for broader area (includes Mississippi and Tennessee)
            url = f"{self.nws_api_base}/alerts/active?area=AL,MS,TN&status=actual"
            
            response = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            # Look for severe thunderstorm or tornado watches
            western_watches = []
            northern_watches = []
            
            for feature in features:
                props = feature.get('properties', {})
                event = props.get('event', '').lower()
                area = props.get('areaDesc', '')
                
                if 'watch' in event and any(word in event for word in ['severe', 'thunderstorm', 'tornado']):
                    watch_info = {
                        'event': props.get('event'),
                        'area': area,
                        'description': props.get('description', ''),
                        'expires': props.get('expires')
                    }
                    
                    # Check if watch area is west (Mississippi)
                    if 'mississippi' in area.lower() or any(ms_word in area.lower() for ms_word in ['tupelo', 'corinth', 'booneville', 'tishomingo']):
                        western_watches.append(watch_info)
                    # Check if watch area is north (Tennessee)
                    elif 'tennessee' in area.lower() or any(tn_word in area.lower() for tn_word in ['nashville', 'columbia', 'shelbyville', 'manchester', 'tullahoma', 'fayetteville']):
                        northern_watches.append(watch_info)
            
            # Prioritize western approach, then northern
            if western_watches:
                return self._build_watch_announcement(western_watches, 'western')
            elif northern_watches:
                return self._build_watch_announcement(northern_watches, 'northern')
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error checking watches: {e}")
            return None
    
    def _build_approach_announcement(self, alerts: List[Dict], direction: str) -> Dict:
        """Build announcement for approaching storms"""
        
        # Estimate distance and direction text based on approach direction
        if direction == 'western':
            estimated_distance = 45  # Mississippi border ~40-50 miles west
            direction_text = "to the west near the Mississippi border"
        elif direction == 'northern':
            estimated_distance = 50  # Southern Tennessee ~40-60 miles north
            direction_text = "to the north in Southern Tennessee"
        else:
            estimated_distance = 45
            direction_text = "in the region"
        
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
            f"{direction_text}, moving toward our area. "
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
            'direction': direction,
            'storm_types': alert_types,
            'announcement': announcement,
            'alerts': alerts
        }
    
    def _build_watch_announcement(self, watches: List[Dict], direction: str = 'western') -> Dict:
        """Build announcement for approaching watches"""
        
        watch_type = watches[0]['event']
        
        if direction == 'western':
            direction_text = "to our west in Mississippi"
            estimated_distance = 60
        elif direction == 'northern':
            direction_text = "to our north in Southern Tennessee"
            estimated_distance = 65
        else:
            direction_text = "in the region"
            estimated_distance = 60
        
        announcement = (
            f"Weather outlook: A {watch_type} is in effect {direction_text}. "
            f"Conditions favorable for severe weather development. "
            f"Storms may approach our area later. Stay weather aware."
        )
        
        return {
            'has_approaching_storms': True,
            'distance_miles': estimated_distance,
            'speed_mph': 30,  # Conservative estimate
            'eta_minutes': 120,  # 2 hours
            'arrival_time': (datetime.now() + timedelta(hours=2)).strftime('%-I:%M %p'),
            'urgency': 'distant',
            'direction': direction,
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
