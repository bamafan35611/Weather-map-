"""
weather_enhancements.py - Environmental Data Commentary
Complements weather_commentary.py by adding temperature, wind, precipitation data
Does NOT replace existing commentary - adds to it!
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pytz

class WeatherEnhancements:
    """
    Adds environmental context to existing alert-based commentary
    - Temperature extremes and comparisons
    - Wind conditions
    - Precipitation reports
    - Sunrise/sunset context
    - Pattern analysis
    """
    
    def __init__(self):
        self.nws_api_base = "https://api.weather.gov"
        # 🔧 FIXED: Use only NorthBamaWX monitored cities (North Alabama + Southern Tennessee)
        self.priority_cities = [
            # North Alabama - Major cities
            {'name': 'Huntsville', 'state': 'AL', 'lat': 34.7304, 'lon': -86.5861},
            {'name': 'Decatur', 'state': 'AL', 'lat': 34.6059, 'lon': -86.9833},
            {'name': 'Athens', 'state': 'AL', 'lat': 34.8026, 'lon': -86.9719},
            {'name': 'Florence', 'state': 'AL', 'lat': 34.7998, 'lon': -87.6773},
            {'name': 'Cullman', 'state': 'AL', 'lat': 34.1748, 'lon': -86.8436},
            {'name': 'Albertville', 'state': 'AL', 'lat': 34.2676, 'lon': -86.2089},
            {'name': 'Scottsboro', 'state': 'AL', 'lat': 34.6723, 'lon': -86.0342},
            {'name': 'Russellville', 'state': 'AL', 'lat': 34.5079, 'lon': -87.7286},
            {'name': 'Guntersville', 'state': 'AL', 'lat': 34.3581, 'lon': -86.2947},
            {'name': 'Hartselle', 'state': 'AL', 'lat': 34.4426, 'lon': -86.9356},
            # Southern Tennessee
            {'name': 'Fayetteville', 'state': 'TN', 'lat': 35.1520, 'lon': -86.5705},
            {'name': 'Winchester', 'state': 'TN', 'lat': 35.1859, 'lon': -86.1122},
            {'name': 'Lynchburg', 'state': 'TN', 'lat': 35.2831, 'lon': -86.3742}
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '(NorthBamaWX Weather Bot, northbamawx@example.com)'
        })
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def _get_cached_or_fetch(self, key: str, fetch_function, *args):
        """Simple cache to avoid hammering NWS API"""
        now = datetime.now().timestamp()
        
        if key in self.cache:
            data, timestamp = self.cache[key]
            if now - timestamp < self.cache_timeout:
                return data
        
        try:
            data = fetch_function(*args)
            self.cache[key] = (data, now)
            return data
        except:
            # Return cached data even if expired, better than nothing
            if key in self.cache:
                return self.cache[key][0]
            return None
    
    def get_observation_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current observation data from NWS"""
        try:
            # Get the station
            points_url = f"{self.nws_api_base}/points/{lat:.4f},{lon:.4f}"
            response = self.session.get(points_url, timeout=5)
            
            if response.status_code != 200:
                return None
            
            points_data = response.json()
            stations_url = points_data['properties']['observationStations']
            
            # Get nearest station
            stations_response = self.session.get(stations_url, timeout=5)
            if stations_response.status_code != 200:
                return None
            
            stations = stations_response.json()
            if not stations.get('features'):
                return None
            
            station_id = stations['features'][0]['properties']['stationIdentifier']
            
            # Get latest observation
            obs_url = f"{self.nws_api_base}/stations/{station_id}/observations/latest"
            obs_response = self.session.get(obs_url, timeout=5)
            
            if obs_response.status_code != 200:
                return None
            
            return obs_response.json()['properties']
            
        except Exception as e:
            print(f"Error fetching observation for {lat},{lon}: {e}")
            return None
    
    def get_temperature_story(self) -> Optional[str]:
        """Generate temperature extremes story"""
        def fetch():
            temps = []
            
            # Sample 10 cities for temperature data
            for city in self.priority_cities[:10]:
                obs = self.get_observation_data(city['lat'], city['lon'])
                if obs and obs.get('temperature', {}).get('value'):
                    temp_c = obs['temperature']['value']
                    if temp_c is not None:
                        temp_f = round((temp_c * 9/5) + 32)
                        temps.append({
                            'city': city['name'],
                            'state': city['state'],
                            'temp': temp_f
                        })
            
            if len(temps) < 3:
                return None
            
            # Find extremes
            hottest = max(temps, key=lambda x: x['temp'])
            coldest = min(temps, key=lambda x: x['temp'])
            avg_temp = round(sum(t['temp'] for t in temps) / len(temps))
            temp_diff = hottest['temp'] - coldest['temp']
            
            # Generate story
            story = f"{hottest['city']}, {hottest['state']} is the warmest at {hottest['temp']} degrees, "
            story += f"while {coldest['city']}, {coldest['state']} is the coolest at {coldest['temp']} degrees. "
            
            if temp_diff >= 50:
                story += f"That's a {temp_diff} degree temperature spread across the nation. "
            
            # Add seasonal context
            month = datetime.now().month
            if month in [12, 1, 2]:  # Winter
                if avg_temp > 60:
                    story += "Unseasonably mild for December. "
                elif avg_temp < 35:
                    story += "Cold air gripping much of the country. "
            elif month in [6, 7, 8]:  # Summer
                if avg_temp > 85:
                    story += "Hot conditions dominating. "
            
            return story
        
        try:
            return self._get_cached_or_fetch('temperature', fetch)
        except Exception as e:
            print(f"Error in temperature story: {e}")
            return None
    
    def get_wind_story(self) -> Optional[str]:
        """Generate wind conditions story"""
        def fetch():
            windy_cities = []
            
            for city in self.priority_cities[:10]:
                obs = self.get_observation_data(city['lat'], city['lon'])
                if obs and obs.get('windSpeed', {}).get('value'):
                    wind_ms = obs['windSpeed']['value']
                    if wind_ms:
                        wind_mph = round(wind_ms * 2.237)
                        
                        # Get gusts if available
                        gust_mph = None
                        if obs.get('windGust', {}).get('value'):
                            gust_ms = obs['windGust']['value']
                            if gust_ms:
                                gust_mph = round(gust_ms * 2.237)
                        
                        if wind_mph >= 15 or (gust_mph and gust_mph >= 25):
                            windy_cities.append({
                                'city': city['name'],
                                'state': city['state'],
                                'wind': wind_mph,
                                'gust': gust_mph
                            })
            
            if not windy_cities:
                return None
            
            # Sort by highest winds
            windy_cities.sort(key=lambda x: x['gust'] if x['gust'] else x['wind'], reverse=True)
            
            w = windy_cities[0]
            if w['gust'] and w['gust'] >= 35:
                story = f"Strong winds reported in {w['city']}, {w['state']} with gusts to {w['gust']} miles per hour. "
            elif len(windy_cities) >= 3:
                story = f"Breezy conditions across several areas with winds 15 to 25 miles per hour. "
            else:
                story = f"Breezy in {w['city']} with winds at {w['wind']} miles per hour. "
            
            return story
        
        try:
            return self._get_cached_or_fetch('wind', fetch)
        except Exception as e:
            print(f"Error in wind story: {e}")
            return None
    
    def get_precipitation_story(self) -> Optional[str]:
        """Generate precipitation story"""
        def fetch():
            wet_cities = []
            
            for city in self.priority_cities[:10]:
                obs = self.get_observation_data(city['lat'], city['lon'])
                if obs:
                    # Check recent precipitation
                    precip = obs.get('precipitationLastHour', {}).get('value')
                    if precip and precip > 0:
                        precip_inches = round(precip / 25.4, 2)  # Convert mm to inches
                        wet_cities.append({
                            'city': city['name'],
                            'state': city['state'],
                            'precip': precip_inches
                        })
            
            if not wet_cities:
                return None
            
            # Sort by precipitation
            wet_cities.sort(key=lambda x: x['precip'], reverse=True)
            
            w = wet_cities[0]
            if w['precip'] >= 0.5:
                story = f"Heavy rain in {w['city']}, {w['state']} with {w['precip']} inches in the past hour. "
            else:
                story = f"Light rain reported in {w['city']}, {w['state']}. "
            
            return story
        
        try:
            return self._get_cached_or_fetch('precipitation', fetch)
        except Exception as e:
            print(f"Error in precipitation story: {e}")
            return None
    
    def get_sunrise_sunset_context(self) -> Optional[str]:
        """Generate sunrise/sunset context"""
        try:
            # Try to import astral, but don't fail if not available
            try:
                from astral import LocationInfo
                from astral.sun import sun
            except ImportError:
                return None
            
            # Use central US location for national context
            city = LocationInfo("Kansas City", "USA", "America/Chicago", 39.0997, -94.5786)
            s = sun(city.observer, date=datetime.now())
            
            now = datetime.now(pytz.timezone('America/Chicago'))
            sunrise = s['sunrise'].astimezone(pytz.timezone('America/Chicago'))
            sunset = s['sunset'].astimezone(pytz.timezone('America/Chicago'))
            
            # Time until sunrise/sunset
            if now < sunrise:
                time_until = sunrise - now
                mins_until = time_until.seconds // 60
                if mins_until <= 30:
                    return f"Sunrise in {mins_until} minutes across the central United States. "
            elif now > sunset:
                return None  # Don't mention after sunset
            else:
                time_until = sunset - now
                mins_until = time_until.seconds // 60
                if mins_until <= 60:
                    return f"Sunset approaching in about {mins_until} minutes. "
            
            return None
            
        except Exception as e:
            print(f"Error in sunrise/sunset context: {e}")
            return None
    
    def get_enhanced_context(self, broadcast_type: str = "national_briefing") -> str:
        """
        Get enhanced environmental context
        
        Args:
            broadcast_type: Type of broadcast (affects what data is included)
        
        Returns:
            String with environmental context (may be empty if no data available)
        """
        segments = []
        
        try:
            # Temperature (all broadcasts)
            temp = self.get_temperature_story()
            if temp:
                segments.append(temp)
            
            # Wind conditions (if noteworthy)
            wind = self.get_wind_story()
            if wind:
                segments.append(wind)
            
            # Precipitation (if occurring)
            precip = self.get_precipitation_story()
            if precip:
                segments.append(precip)
            
            # Sunrise/sunset (for morning/evening broadcasts)
            if broadcast_type in ["national_briefing", "hourly_update"]:
                time_context = self.get_sunrise_sunset_context()
                if time_context:
                    segments.append(time_context)
            
            return " ".join(segments)
        
        except Exception as e:
            print(f"Error generating enhanced context: {e}")
            return ""


# Singleton instance for easy access
_enhancer_instance = None

def get_weather_enhancer() -> WeatherEnhancements:
    """Get or create weather enhancer instance"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = WeatherEnhancements()
    return _enhancer_instance


def add_environmental_context(base_commentary: str, broadcast_type: str = "national_briefing") -> str:
    """
    Add environmental context to existing commentary
    
    This is the main integration function - call this to enhance any commentary!
    
    Args:
        base_commentary: Your existing alert-based commentary
        broadcast_type: Type of broadcast
    
    Returns:
        Enhanced commentary with environmental data added
    
    Example:
        base = get_national_briefing(alerts, scored)
        enhanced = add_environmental_context(base, "national_briefing")
    """
    try:
        enhancer = get_weather_enhancer()
        context = enhancer.get_enhanced_context(broadcast_type)
        
        if context:
            # Add context after main commentary
            return f"{base_commentary} {context}"
        else:
            # No enhancement available, return original
            return base_commentary
    
    except Exception as e:
        print(f"Enhancement failed gracefully: {e}")
        # Always return original commentary if enhancement fails
        return base_commentary


# For backward compatibility and easy testing
def get_enhanced_commentary(alerts: List[Dict], broadcast_type: str = "top_alerts") -> str:
    """
    Legacy function name - just returns environmental context
    Use add_environmental_context() instead for full integration
    """
    try:
        enhancer = get_weather_enhancer()
        return enhancer.get_enhanced_context(broadcast_type)
    except Exception as e:
        print(f"Enhancement failed: {e}")
        return ""
