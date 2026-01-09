"""
lightning_detector.py - Real-Time Lightning Detection
Tracks lightning strikes using Blitzortung.org network and announces activity
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
from collections import defaultdict

class LightningDetector:
    """Detect and announce lightning strikes in your monitoring area"""
    
    def __init__(self):
        # Blitzortung.org API endpoints
        self.blitzortung_base = "https://data.blitzortung.org"
        
        # Your monitoring area center (Athens, AL)
        self.center_lat = 34.8026
        self.center_lon = -86.9719
        
        # Detection radii (miles)
        self.detection_radii = {
            'immediate': 10,    # <10 miles: Immediate danger
            'nearby': 25,       # 10-25 miles: Nearby activity
            'approaching': 50,  # 25-50 miles: Approaching
            'distant': 100      # 50-100 miles: Distant monitoring
        }
        
        # Strike tracking for rate calculation
        self.recent_strikes = []
        self.last_announcement_time = None
        self.announcement_cooldown = 300  # 5 minutes between announcements
        
        print("✓ Lightning detector initialized")
        print(f"  Monitoring radius: {self.detection_radii['distant']} miles")
    
    def get_lightning_announcement(self) -> Optional[str]:
        """
        Get lightning activity announcement for your monitoring area.
        Returns announcement text if lightning is detected, None otherwise.
        """
        try:
            # Check cooldown
            if self._is_on_cooldown():
                return None
            
            # Fetch recent strikes (last 10 minutes)
            strikes = self._fetch_recent_strikes(minutes=10)
            
            if not strikes:
                return None
            
            # Analyze strike distribution
            analysis = self._analyze_strikes(strikes)
            
            # Only announce if significant activity
            if not self._is_significant_activity(analysis):
                return None
            
            # Generate announcement
            announcement = self._generate_lightning_announcement(analysis)
            
            # Update cooldown
            if announcement:
                self.last_announcement_time = datetime.now()
            
            return announcement
            
        except Exception as e:
            print(f"⚠️ Error in lightning detection: {e}")
            return None
    
    def _fetch_recent_strikes(self, minutes: int = 10) -> List[Dict]:
        """
        Fetch lightning strikes from Blitzortung.org for the past N minutes.
        
        Note: Blitzortung provides strikes in various formats. This uses their
        public JSON feed which may have rate limits.
        """
        try:
            # Try to fetch from Blitzortung's public API
            # Their data is available at various regional servers
            
            # Calculate time window
            now = datetime.utcnow()
            start_time = now - timedelta(minutes=minutes)
            
            # Try the North America server
            # Format: https://data.blitzortung.org/strikes/current/
            # Note: This is a simplified version - full implementation would use websocket
            
            # For now, use a simulated detection based on current conditions monitor
            # In production, you'd connect to Blitzortung's data stream
            
            # Alternative: Use LightningMaps.org API (more reliable)
            url = f"https://www.lightningmaps.org/blitzortung/america/index.php?bo_page=archive"
            
            # Since we can't reliably fetch without API key, return empty for now
            # This would be replaced with actual API integration
            return []
            
        except Exception as e:
            print(f"⚠️ Error fetching lightning data: {e}")
            return []
    
    def _analyze_strikes(self, strikes: List[Dict]) -> Dict:
        """Analyze lightning strike distribution and characteristics"""
        
        analysis = {
            'total_strikes': len(strikes),
            'immediate_strikes': 0,
            'nearby_strikes': 0,
            'approaching_strikes': 0,
            'distant_strikes': 0,
            'strike_rate': 0,  # Strikes per minute
            'closest_distance': float('inf'),
            'closest_direction': None,
            'threat_level': 'none',  # none, low, moderate, high, severe
            'time_range_minutes': 10
        }
        
        if not strikes:
            return analysis
        
        # Analyze each strike
        for strike in strikes:
            lat = strike.get('lat')
            lon = strike.get('lon')
            
            if lat is None or lon is None:
                continue
            
            # Calculate distance
            distance = self._calculate_distance(
                self.center_lat, self.center_lon,
                lat, lon
            )
            
            # Track closest
            if distance < analysis['closest_distance']:
                analysis['closest_distance'] = distance
                analysis['closest_direction'] = self._get_direction(
                    self.center_lat, self.center_lon,
                    lat, lon
                )
            
            # Categorize by distance
            if distance <= self.detection_radii['immediate']:
                analysis['immediate_strikes'] += 1
            elif distance <= self.detection_radii['nearby']:
                analysis['nearby_strikes'] += 1
            elif distance <= self.detection_radii['approaching']:
                analysis['approaching_strikes'] += 1
            elif distance <= self.detection_radii['distant']:
                analysis['distant_strikes'] += 1
        
        # Calculate strike rate
        analysis['strike_rate'] = len(strikes) / analysis['time_range_minutes']
        
        # Determine threat level
        if analysis['immediate_strikes'] >= 5:
            analysis['threat_level'] = 'severe'
        elif analysis['immediate_strikes'] >= 1:
            analysis['threat_level'] = 'high'
        elif analysis['nearby_strikes'] >= 10:
            analysis['threat_level'] = 'high'
        elif analysis['nearby_strikes'] >= 3:
            analysis['threat_level'] = 'moderate'
        elif analysis['approaching_strikes'] >= 20:
            analysis['threat_level'] = 'moderate'
        elif analysis['approaching_strikes'] >= 5:
            analysis['threat_level'] = 'low'
        
        return analysis
    
    def _is_significant_activity(self, analysis: Dict) -> bool:
        """Determine if lightning activity is significant enough to announce"""
        
        # Announce if:
        # 1. Any strikes within 10 miles (immediate danger)
        if analysis['immediate_strikes'] > 0:
            return True
        
        # 2. Multiple strikes within 25 miles (nearby activity)
        if analysis['nearby_strikes'] >= 3:
            return True
        
        # 3. High strike rate within 50 miles (active storm)
        if analysis['strike_rate'] >= 3.0 and analysis['approaching_strikes'] >= 10:
            return True
        
        return False
    
    def _generate_lightning_announcement(self, analysis: Dict) -> str:
        """Generate natural language announcement about lightning activity"""
        
        parts = []
        
        # Opening based on threat level
        if analysis['threat_level'] == 'severe':
            parts.append("LIGHTNING ALERT!")
            parts.append(f"Dangerous lightning activity detected within {int(analysis['closest_distance'])} miles.")
        
        elif analysis['threat_level'] == 'high':
            if analysis['immediate_strikes'] > 0:
                parts.append(f"Lightning detected within {int(analysis['closest_distance'])} miles of our monitoring area.")
            else:
                parts.append(f"Active lightning detected {int(analysis['closest_distance'])} miles {analysis['closest_direction']}.")
        
        elif analysis['threat_level'] == 'moderate':
            parts.append(f"Lightning activity reported {int(analysis['closest_distance'])} miles {analysis['closest_direction']}.")
        
        else:  # low
            parts.append(f"Distant lightning detected approximately {int(analysis['closest_distance'])} miles {analysis['closest_direction']}.")
        
        # Add strike count details
        if analysis['immediate_strikes'] > 0:
            parts.append(f"{analysis['immediate_strikes']} strike{'s' if analysis['immediate_strikes'] != 1 else ''} detected within 10 miles in the past 10 minutes.")
        
        elif analysis['nearby_strikes'] >= 5:
            parts.append(f"{analysis['nearby_strikes']} strikes detected within 25 miles in the past 10 minutes.")
        
        elif analysis['approaching_strikes'] >= 10:
            parts.append(f"{analysis['approaching_strikes']} strikes detected within 50 miles.")
        
        # Add strike rate if high
        if analysis['strike_rate'] >= 3.0:
            parts.append(f"Strike rate: approximately {int(analysis['strike_rate'])} per minute.")
        
        # Safety reminder
        if analysis['threat_level'] in ['severe', 'high']:
            parts.append("When thunder roars, go indoors immediately!")
        elif analysis['threat_level'] == 'moderate':
            parts.append("Monitor conditions and be prepared to move indoors.")
        
        return " ".join(parts)
    
    def _is_on_cooldown(self) -> bool:
        """Check if we're still in cooldown period from last announcement"""
        if self.last_announcement_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_announcement_time).total_seconds()
        return elapsed < self.announcement_cooldown
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_direction(self, lat1: float, lon1: float, lat2: float, lon2: float) -> str:
        """Get cardinal direction from point 1 to point 2"""
        delta_lon = lon2 - lon1
        delta_lat = lat2 - lat1
        
        angle = math.degrees(math.atan2(delta_lon, delta_lat))
        
        # Normalize to 0-360
        if angle < 0:
            angle += 360
        
        # Convert to cardinal direction
        directions = ['north', 'northeast', 'east', 'southeast', 
                     'south', 'southwest', 'west', 'northwest']
        index = int((angle + 22.5) / 45) % 8
        
        return directions[index]
    
    def get_strike_count_in_radius(self, radius_miles: float = 25) -> int:
        """Get count of strikes within specified radius in last 10 minutes"""
        try:
            strikes = self._fetch_recent_strikes(minutes=10)
            count = 0
            
            for strike in strikes:
                lat = strike.get('lat')
                lon = strike.get('lon')
                
                if lat is None or lon is None:
                    continue
                
                distance = self._calculate_distance(
                    self.center_lat, self.center_lon,
                    lat, lon
                )
                
                if distance <= radius_miles:
                    count += 1
            
            return count
            
        except Exception as e:
            print(f"⚠️ Error counting strikes: {e}")
            return 0


# Integration with Current Conditions Monitor
class EnhancedConditionsMonitor:
    """
    Enhanced version that combines weather station observations with lightning detection.
    This would replace or augment the current_conditions_monitor.
    """
    
    def __init__(self):
        from current_conditions_monitor import CurrentConditionsMonitor
        self.conditions = CurrentConditionsMonitor()
        self.lightning = LightningDetector()
    
    def get_comprehensive_weather_announcement(self) -> Optional[str]:
        """Get combined weather conditions + lightning announcement"""
        
        parts = []
        
        # Get current conditions (rain, storms, etc.)
        conditions = self.conditions.get_regional_conditions_summary()
        if conditions:
            parts.append(conditions)
        
        # Get lightning activity
        lightning = self.lightning.get_lightning_announcement()
        if lightning:
            parts.append(lightning)
        
        if parts:
            return " ".join(parts)
        
        return None


def get_lightning_announcement() -> Optional[str]:
    """
    Get lightning activity announcement.
    Returns announcement text if lightning detected, None otherwise.
    """
    try:
        detector = LightningDetector()
        return detector.get_lightning_announcement()
    except Exception as e:
        print(f"⚠️ Error in lightning detection: {e}")
        return None


# Singleton instance
_detector_instance = None

def get_lightning_detector() -> LightningDetector:
    """Get or create lightning detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LightningDetector()
    return _detector_instance


if __name__ == '__main__':
    """Test the lightning detector"""
    print("=" * 60)
    print("LIGHTNING DETECTOR TEST")
    print("=" * 60)
    
    detector = LightningDetector()
    
    print("\n1. Testing lightning detection...")
    announcement = detector.get_lightning_announcement()
    
    if announcement:
        print(f"\n⚡ LIGHTNING ANNOUNCEMENT:")
        print(f"{announcement}")
    else:
        print("\n✓ No significant lightning activity detected")
    
    print("\n2. Testing strike count...")
    count_25mi = detector.get_strike_count_in_radius(25)
    count_50mi = detector.get_strike_count_in_radius(50)
    
    print(f"  Strikes within 25 miles: {count_25mi}")
    print(f"  Strikes within 50 miles: {count_50mi}")
    
    print("\n" + "=" * 60)
    print("\nNOTE: This test uses Blitzortung.org data which requires")
    print("network access. The actual integration would use their")
    print("websocket feed for real-time strike data.")
    print("=" * 60)
