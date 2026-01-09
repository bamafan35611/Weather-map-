"""
current_conditions_monitor.py - Real-Time Weather Conditions Monitoring
Announces rain, storms, and current weather even when there are no NWS alerts
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz

class CurrentConditionsMonitor:
    """Monitor and announce current weather conditions including rain and non-severe storms"""
    
    def __init__(self):
        self.nws_api_base = "https://api.weather.gov"
        
        # Your monitoring stations (METAR/ASOS codes for North Alabama)
        self.observation_stations = {
            'Huntsville': 'KHSV',      # Huntsville International Airport
            'Decatur': 'KDCU',          # Pryor Field Regional Airport
            'Athens': 'KMDQ',           # Madison County Executive Airport (Limestone County)
            'Muscle Shoals': 'KMSL',    # Northwest Alabama Regional Airport
            'Cullman': 'KCRX',          # Cullman Regional Airport
        }
        
        # Your monitoring area center (Athens, AL)
        self.center_lat = 34.8026
        self.center_lon = -86.9719
        
        # Central time zone
        self.central_tz = pytz.timezone('America/Chicago')
        
        print("✓ Current conditions monitor initialized")
        print(f"  Monitoring {len(self.observation_stations)} weather stations")
    
    def get_regional_conditions_summary(self) -> Optional[str]:
        """
        Get a summary of current weather conditions across your monitoring area.
        Returns announcement text if there's notable weather to report.
        """
        try:
            # Gather observations from all stations
            station_reports = []
            
            for city, station_id in self.observation_stations.items():
                obs = self._fetch_station_observation(station_id)
                if obs:
                    station_reports.append({
                        'city': city,
                        'station': station_id,
                        'data': obs
                    })
            
            if not station_reports:
                return None
            
            # Analyze conditions
            analysis = self._analyze_conditions(station_reports)
            
            # Generate announcement if there's something to report
            if analysis['has_precipitation'] or analysis['has_storms'] or analysis['significant_weather']:
                return self._generate_conditions_announcement(analysis, station_reports)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting regional conditions: {e}")
            return None
    
    def _fetch_station_observation(self, station_id: str) -> Optional[Dict]:
        """Fetch latest observation from a METAR/ASOS station"""
        try:
            url = f"{self.nws_api_base}/stations/{station_id}/observations/latest"
            
            response = requests.get(url, timeout=10, headers={
                'User-Agent': '(NorthBamaWX Weather Bot, michael@northbamawx.com)'
            })
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            props = data.get('properties', {})
            
            # Extract key weather parameters
            observation = {
                'timestamp': props.get('timestamp'),
                'temperature': self._celsius_to_fahrenheit(props.get('temperature', {}).get('value')),
                'dewpoint': self._celsius_to_fahrenheit(props.get('dewpoint', {}).get('value')),
                'wind_speed': self._ms_to_mph(props.get('windSpeed', {}).get('value')),
                'wind_gust': self._ms_to_mph(props.get('windGust', {}).get('value')),
                'wind_direction': props.get('windDirection', {}).get('value'),
                'pressure': props.get('barometricPressure', {}).get('value'),
                'visibility': props.get('visibility', {}).get('value'),
                'weather': props.get('textDescription', ''),
                'raw_text': props.get('rawMessage', ''),
                'present_weather': props.get('presentWeather', []),
            }
            
            return observation
            
        except Exception as e:
            print(f"⚠️ Error fetching {station_id}: {e}")
            return None
    
    def _analyze_conditions(self, station_reports: List[Dict]) -> Dict:
        """Analyze weather conditions across all stations"""
        
        analysis = {
            'has_precipitation': False,
            'has_storms': False,
            'significant_weather': False,
            'rain_locations': [],
            'storm_locations': [],
            'weather_types': set(),
            'max_wind_gust': 0,
            'max_wind_location': None,
            'visibility_issues': [],
            'summary_type': None  # 'rain', 'storms', 'mixed', 'weather'
        }
        
        for report in station_reports:
            city = report['city']
            obs = report['data']
            weather = (obs.get('weather', '') or '').lower()
            present = obs.get('present_weather', [])
            
            # Check for precipitation
            precip_keywords = ['rain', 'drizzle', 'showers', 'precipitation']
            if any(kw in weather for kw in precip_keywords):
                analysis['has_precipitation'] = True
                analysis['rain_locations'].append(city)
                analysis['weather_types'].add('rain')
            
            # Check for thunderstorms
            storm_keywords = ['thunder', 'lightning', 'tstm']
            raw_text = (obs.get('raw_text', '') or '').lower()
            if any(kw in weather for kw in storm_keywords) or any(kw in raw_text for kw in storm_keywords):
                analysis['has_storms'] = True
                analysis['storm_locations'].append(city)
                analysis['weather_types'].add('storms')
            
            # Check for other significant weather
            sig_keywords = ['fog', 'mist', 'haze', 'smoke', 'snow', 'sleet', 'freezing']
            if any(kw in weather for kw in sig_keywords):
                analysis['significant_weather'] = True
                analysis['weather_types'].add(weather.split()[0])
            
            # Track wind gusts
            wind_gust = obs.get('wind_gust')
            if wind_gust and wind_gust > analysis['max_wind_gust']:
                analysis['max_wind_gust'] = wind_gust
                analysis['max_wind_location'] = city
            
            # Check visibility
            visibility = obs.get('visibility')
            if visibility and visibility < 5000:  # Less than ~3 miles
                analysis['visibility_issues'].append(city)
        
        # Determine summary type
        if analysis['has_storms']:
            analysis['summary_type'] = 'storms'
        elif analysis['has_precipitation']:
            analysis['summary_type'] = 'rain'
        elif analysis['significant_weather']:
            analysis['summary_type'] = 'weather'
        
        return analysis
    
    def _generate_conditions_announcement(self, analysis: Dict, station_reports: List[Dict]) -> str:
        """Generate natural language announcement about current conditions"""
        
        parts = []
        
        # Opening
        if analysis['summary_type'] == 'storms':
            if len(analysis['storm_locations']) == 1:
                parts.append(f"Thunderstorms are currently active near {analysis['storm_locations'][0]}.")
            elif len(analysis['storm_locations']) == 2:
                parts.append(f"Thunderstorms reported near {analysis['storm_locations'][0]} and {analysis['storm_locations'][1]}.")
            else:
                parts.append(f"Scattered thunderstorms across the region with activity near {', '.join(analysis['storm_locations'][:2])}.")
        
        elif analysis['summary_type'] == 'rain':
            if len(analysis['rain_locations']) == 1:
                parts.append(f"Rain is falling across {analysis['rain_locations'][0]} at this hour.")
            elif len(analysis['rain_locations']) == 2:
                parts.append(f"Rain showers moving through {analysis['rain_locations'][0]} and {analysis['rain_locations'][1]}.")
            elif len(analysis['rain_locations']) >= 3:
                parts.append(f"Widespread rain across the region including {', '.join(analysis['rain_locations'][:3])}.")
            else:
                parts.append(f"Light rain reported in parts of North Alabama.")
        
        # Add storm details if present (but not severe)
        if analysis['has_storms']:
            if analysis['max_wind_gust'] > 0 and analysis['max_wind_gust'] < 58:
                # Non-severe but notable winds
                if analysis['max_wind_gust'] >= 30:
                    parts.append(f"Gusty winds up to {int(analysis['max_wind_gust'])} miles per hour near {analysis['max_wind_location']}.")
            
            # Remind about lightning safety
            parts.append("Remember, when thunder roars, go indoors.")
        
        # Visibility issues
        if analysis['visibility_issues']:
            if len(analysis['visibility_issues']) == 1:
                parts.append(f"Reduced visibility near {analysis['visibility_issues'][0]}.")
            else:
                parts.append(f"Reduced visibility in multiple locations including {analysis['visibility_issues'][0]}.")
        
        # Status message - no warnings
        parts.append("No severe weather warnings are in effect at this time.")
        
        return " ".join(parts)
    
    def get_current_radar_summary(self) -> Optional[str]:
        """
        Get a summary of current radar activity (requires NWS radar API)
        This is a simplified version - full radar integration would require more setup
        """
        # This would integrate with NWS radar mosaic or local radar data
        # For now, we'll return None and rely on station observations
        return None
    
    def should_announce_conditions(self) -> bool:
        """
        Determine if current conditions are significant enough to announce.
        Returns True if there's rain, storms, or other notable weather.
        """
        summary = self.get_regional_conditions_summary()
        return summary is not None
    
    def _celsius_to_fahrenheit(self, celsius: Optional[float]) -> Optional[float]:
        """Convert Celsius to Fahrenheit"""
        if celsius is None:
            return None
        return round((celsius * 9/5) + 32)
    
    def _ms_to_mph(self, ms: Optional[float]) -> Optional[float]:
        """Convert meters per second to miles per hour"""
        if ms is None:
            return None
        return round(ms * 2.237)


def get_current_conditions_announcement() -> Optional[str]:
    """
    Get current conditions announcement for broadcast.
    Returns announcement text if there's weather to report, None otherwise.
    """
    try:
        monitor = CurrentConditionsMonitor()
        return monitor.get_regional_conditions_summary()
    except Exception as e:
        print(f"⚠️ Error in current conditions: {e}")
        return None


def should_announce_current_conditions() -> bool:
    """Check if current conditions are significant enough to announce"""
    try:
        monitor = CurrentConditionsMonitor()
        return monitor.should_announce_conditions()
    except Exception as e:
        print(f"⚠️ Error checking conditions: {e}")
        return False


# Singleton instance for efficiency
_monitor_instance = None

def get_conditions_monitor() -> CurrentConditionsMonitor:
    """Get or create monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = CurrentConditionsMonitor()
    return _monitor_instance


if __name__ == '__main__':
    """Test the current conditions monitor"""
    print("=" * 60)
    print("CURRENT CONDITIONS MONITOR TEST")
    print("=" * 60)
    
    monitor = CurrentConditionsMonitor()
    
    print("\n1. Testing station observations...")
    for city, station_id in monitor.observation_stations.items():
        print(f"\nFetching {city} ({station_id})...")
        obs = monitor._fetch_station_observation(station_id)
        if obs:
            print(f"  ✓ Temperature: {obs['temperature']}°F")
            print(f"  ✓ Weather: {obs['weather']}")
            if obs['wind_gust']:
                print(f"  ✓ Wind Gust: {obs['wind_gust']} mph")
        else:
            print(f"  ✗ No data")
    
    print("\n2. Testing regional summary...")
    summary = monitor.get_regional_conditions_summary()
    if summary:
        print(f"\n📢 ANNOUNCEMENT:")
        print(f"{summary}")
    else:
        print("\n✓ No significant weather to announce")
    
    print("\n" + "=" * 60)
