"""
nws_forecast_fetcher.py - Fetch actual NWS forecast data for specific locations
IMPROVED VERSION with better error handling and debugging
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import pytz

class NWSForecastFetcher:
    """Fetches NWS forecast data for specific locations"""
    
    def __init__(self):
        self.nws_api_base = "https://api.weather.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '(NorthBamaWX Weather Bot, michael@northbamawx.com)',
            'Accept': 'application/geo+json'
        })
        
        # Your primary location
        self.home_location = {
            'name': 'Athens',
            'state': 'AL',
            'lat': 34.80,
            'lon': -86.97
        }
        
        # Cache for grid point data (changes rarely)
        self.grid_cache = {}
    
    def get_forecast_for_location(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get the actual NWS forecast for a location
        
        Returns:
            Dictionary with forecast periods, or None if error
        """
        try:
            # Step 1: Get the grid point for this location
            points_url = f"{self.nws_api_base}/points/{lat:.4f},{lon:.4f}"
            print(f"📍 Fetching grid point: {points_url}")
            
            response = self.session.get(points_url, timeout=15)
            
            # Debug response
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 404:
                print(f"❌ Location not found in NWS grid (possibly outside US)")
                return None
            
            if response.status_code == 500:
                print(f"❌ NWS API server error (500) - try again later")
                return None
            
            response.raise_for_status()
            points_data = response.json()
            
            # Step 2: Get the forecast URL from the points data
            if 'properties' not in points_data:
                print(f"❌ Invalid response from NWS points API")
                print(f"   Response: {str(points_data)[:200]}")
                return None
            
            forecast_url = points_data['properties'].get('forecast')
            
            if not forecast_url:
                print(f"❌ No forecast URL in points response")
                return None
            
            print(f"📡 Fetching forecast: {forecast_url}")
            
            forecast_response = self.session.get(forecast_url, timeout=15)
            print(f"   Status: {forecast_response.status_code}")
            
            if forecast_response.status_code == 500:
                print(f"❌ NWS forecast server error (500) - try again later")
                return None
            
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Extract the periods
            if 'properties' not in forecast_data or 'periods' not in forecast_data['properties']:
                print(f"❌ Invalid forecast response structure")
                return None
            
            periods = forecast_data['properties']['periods']
            
            if not periods:
                print(f"❌ No forecast periods returned")
                return None
            
            print(f"✅ Successfully fetched {len(periods)} forecast periods")
            
            return {
                'location': f"{lat:.2f},{lon:.2f}",
                'updated': forecast_data['properties'].get('updated'),
                'periods': periods
            }
            
        except requests.exceptions.Timeout:
            print(f"⏱️ NWS API timeout after 15 seconds - network may be slow")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection error to NWS API: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP error from NWS API: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching forecast for {lat},{lon}: {type(e).__name__}: {e}")
            return None
    
    def get_home_forecast(self) -> Optional[Dict]:
        """Get forecast for Athens, AL (your home location)"""
        return self.get_forecast_for_location(
            self.home_location['lat'],
            self.home_location['lon']
        )
    
    def get_current_conditions_summary(self, forecast_data: Dict) -> str:
        """
        Generate a summary of current/upcoming conditions from forecast
        
        Args:
            forecast_data: Result from get_forecast_for_location()
        
        Returns:
            Human-readable summary
        """
        if not forecast_data or not forecast_data.get('periods'):
            return "Forecast data unavailable"
        
        periods = forecast_data['periods']
        
        # Get current/next period
        current_period = periods[0]
        next_period = periods[1] if len(periods) > 1 else None
        
        # Build summary
        summary = f"{current_period['name']}: {current_period['detailedForecast']}"
        
        if next_period:
            summary += f" {next_period['name']}: {next_period['detailedForecast']}"
        
        return summary
    
    def is_severe_weather_expected(self, forecast_data: Dict) -> bool:
        """
        Check if severe weather is in the forecast
        
        Args:
            forecast_data: Result from get_forecast_for_location()
        
        Returns:
            True if severe weather keywords found in forecast
        """
        if not forecast_data or not forecast_data.get('periods'):
            return False
        
        severe_keywords = [
            'severe', 'thunderstorm', 'tornado', 'damaging', 
            'flooding', 'flood', 'heavy rain', 'strong winds',
            'hazardous', 'dangerous'
        ]
        
        # Check first 3 periods (today + tonight + tomorrow)
        for period in forecast_data['periods'][:3]:
            forecast_text = period.get('detailedForecast', '').lower()
            short_text = period.get('shortForecast', '').lower()
            
            if any(keyword in forecast_text or keyword in short_text for keyword in severe_keywords):
                return True
        
        return False
    
    def get_short_forecast_summary(self, forecast_data: Dict, num_periods: int = 2) -> str:
        """
        Get a short, broadcast-ready forecast summary
        
        Args:
            forecast_data: Result from get_forecast_for_location()
            num_periods: Number of forecast periods to include
        
        Returns:
            Short summary suitable for voice broadcast
        """
        if not forecast_data or not forecast_data.get('periods'):
            return "Forecast currently unavailable."
        
        periods = forecast_data['periods'][:num_periods]
        
        summaries = []
        for period in periods:
            name = period['name']
            short = period['shortForecast']
            temp = period['temperature']
            temp_unit = period['temperatureUnit']
            
            summaries.append(f"{name}: {short}, {temp} degrees {temp_unit}")
        
        return ". ".join(summaries) + "."
    
    def get_current_observation(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get current weather observation data for a location
        
        Returns:
            Dictionary with temperature, wind speed, etc. or None if error
        """
        try:
            # Get the grid point first
            points_url = f"{self.nws_api_base}/points/{lat:.4f},{lon:.4f}"
            response = self.session.get(points_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            points_data = response.json()
            
            # Get observation stations
            stations_url = points_data['properties'].get('observationStations')
            if not stations_url:
                return None
            
            stations_response = self.session.get(stations_url, timeout=10)
            if stations_response.status_code != 200:
                return None
            
            stations = stations_response.json()
            if not stations.get('features') or len(stations['features']) == 0:
                return None
            
            # Get the nearest station
            station_id = stations['features'][0]['properties']['stationIdentifier']
            
            # Get latest observation
            obs_url = f"{self.nws_api_base}/stations/{station_id}/observations/latest"
            obs_response = self.session.get(obs_url, timeout=10)
            
            if obs_response.status_code != 200:
                return None
            
            obs_data = obs_response.json()
            return obs_data.get('properties', {})
            
        except Exception as e:
            print(f"⚠️ Error fetching observation for {lat},{lon}: {e}")
            return None
    
    def get_athens_current_conditions(self) -> Optional[Dict]:
        """Get current conditions for Athens, AL"""
        obs = self.get_current_observation(
            self.home_location['lat'],
            self.home_location['lon']
        )
        
        if not obs:
            return None
        
        # Extract and convert the data we need
        result = {}
        
        # Temperature
        temp_c = obs.get('temperature', {}).get('value')
        if temp_c is not None:
            result['temperature'] = round((temp_c * 9/5) + 32)
        
        # Wind speed
        wind_ms = obs.get('windSpeed', {}).get('value')
        if wind_ms is not None:
            result['wind_speed'] = round(wind_ms * 2.237)  # Convert m/s to mph
        
        # Wind gust
        gust_ms = obs.get('windGust', {}).get('value')
        if gust_ms is not None:
            result['wind_gust'] = round(gust_ms * 2.237)
        
        # Wind direction
        wind_dir = obs.get('windDirection', {}).get('value')
        if wind_dir is not None:
            result['wind_direction'] = self._degrees_to_cardinal(wind_dir)
        
        return result if result else None
    
    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert wind direction degrees to cardinal direction"""
        directions = ['North', 'Northeast', 'East', 'Southeast', 
                     'South', 'Southwest', 'West', 'Northwest']
        index = round(degrees / 45) % 8
        return directions[index]
    
    def _expand_wind_direction(self, direction_str: str) -> str:
        """Expand wind direction abbreviations to full words for speech"""
        # Map of abbreviations to full words
        direction_map = {
            'N': 'North',
            'NNE': 'North-Northeast',
            'NE': 'Northeast',
            'ENE': 'East-Northeast',
            'E': 'East',
            'ESE': 'East-Southeast',
            'SE': 'Southeast',
            'SSE': 'South-Southeast',
            'S': 'South',
            'SSW': 'South-Southwest',
            'SW': 'Southwest',
            'WSW': 'West-Southwest',
            'W': 'West',
            'WNW': 'West-Northwest',
            'NW': 'Northwest',
            'NNW': 'North-Northwest'
        }
        
        # Return expanded version if found, otherwise return original
        return direction_map.get(direction_str, direction_str)
    
    def get_athens_forecast_specifically(self) -> str:
        """
        Get a broadcast-ready forecast specifically for Athens, AL
        This is what should be announced instead of just alerts
        """
        forecast = self.get_home_forecast()
        
        if not forecast:
            return "Athens, Alabama forecast is temporarily unavailable. We'll update you when data is restored."
        
        # Get the first 2 periods (current + next)
        periods = forecast['periods'][:2]
        
        if not periods:
            return "Athens, Alabama forecast data is incomplete. Checking back shortly."
        
        # Build Athens-specific summary
        current = periods[0]
        
        summary = f"Athens, Alabama: {current['name']}, {current['shortForecast']}. "
        summary += f"High of {current['temperature']} degrees. "
        
        # Check if severe weather mentioned
        if self.is_severe_weather_expected(forecast):
            summary += "Potential for severe weather. Monitor conditions closely. "
        
        return summary


# Singleton instance
_forecast_fetcher = None

def get_forecast_fetcher() -> NWSForecastFetcher:
    """Get or create forecast fetcher instance"""
    global _forecast_fetcher
    if _forecast_fetcher is None:
        _forecast_fetcher = NWSForecastFetcher()
    return _forecast_fetcher


def get_athens_forecast() -> str:
    """
    Quick function to get Athens, AL forecast
    Use this in your weather_commentary.py
    """
    fetcher = get_forecast_fetcher()
    return fetcher.get_athens_forecast_specifically()


def get_athens_current_conditions() -> Optional[Dict]:
    """
    Get current temperature and wind conditions for Athens, AL
    Returns dict with 'temperature', 'wind_speed', 'wind_gust', 'wind_direction'
    """
    fetcher = get_forecast_fetcher()
    return fetcher.get_athens_current_conditions()


def get_athens_briefing_with_conditions() -> str:
    """
    Get Athens forecast with current temperature and wind speed included
    This is the complete briefing for Athens
    """
    fetcher = get_forecast_fetcher()
    
    # Get forecast
    forecast_text = fetcher.get_athens_forecast_specifically()
    
    # Get current conditions
    conditions = fetcher.get_athens_current_conditions()
    
    if not conditions:
        # If we can't get current conditions, just return the forecast
        return forecast_text
    
    # Build conditions text
    conditions_parts = []
    
    if 'temperature' in conditions:
        conditions_parts.append(f"Current temperature is {conditions['temperature']} degrees")
    
    # WIND DISABLED - NWS observation stations have unreliable wind sensors
    # if 'wind_speed' in conditions and conditions['wind_speed'] > 0:
    #     wind_dir = conditions.get('wind_direction', '')
    #     wind_text = f"winds from the {wind_dir} at {conditions['wind_speed']} miles per hour"
    #     if 'wind_gust' in conditions and conditions['wind_gust'] > conditions['wind_speed'] + 5:
    #         wind_text += f" gusting to {conditions['wind_gust']}"
    #     conditions_parts.append(wind_text)
    
    if conditions_parts:
        # Add current conditions before the forecast
        conditions_text = ", ".join(conditions_parts) + ". "
        return f"Athens, Alabama: {conditions_text}{forecast_text}"
    
    return forecast_text


def get_city_briefing_with_conditions(city_name: str, lat: float, lon: float, state: str, max_retries: int = 3) -> str:
    """
    Get localized forecast for any city in the monitored area
    ENHANCED with retry logic
    
    Args:
        city_name: Name of the city
        lat: Latitude
        lon: Longitude  
        state: State abbreviation (AL or TN)
        max_retries: Maximum number of retry attempts
    
    Returns:
        Broadcast-ready city briefing with current conditions and forecast
    """
    fetcher = get_forecast_fetcher()
    
    import time
    
    for attempt in range(max_retries):
        try:
            # Get forecast data
            forecast_data = fetcher.get_forecast_for_location(lat, lon)
            
            if not forecast_data or not forecast_data.get('periods'):
                if attempt < max_retries - 1:
                    print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed for {city_name}, retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                return f"{city_name}, {state} forecast is temporarily unavailable."
            
            # Get current observation (don't retry if this fails, it's optional)
            current_obs = None
            try:
                current_obs = fetcher.get_current_observation(lat, lon)
            except:
                pass  # Observations are optional
            
            # Build the briefing
            briefing_parts = []
            briefing_parts.append(f"{city_name}, {state}:")
            
            # Add current conditions if available
            if current_obs:
                conditions_parts = []
                
                # Temperature from observation (this is accurate)
                temp_c = current_obs.get('temperature', {}).get('value')
                if temp_c is not None:
                    temp_f = round((temp_c * 9/5) + 32)
                    conditions_parts.append(f"Currently {temp_f} degrees")
                
                # WIND FROM FORECAST (more reliable than observation)
                # Get wind from the current forecast period instead of observation
                current_period = forecast_data['periods'][0]
                wind_speed_str = current_period.get('windSpeed', '')
                wind_direction_str = current_period.get('windDirection', '')
                
                # Parse wind speed (comes as "10 mph" or "5 to 10 mph")
                if wind_speed_str:
                    # Extract number from string like "10 mph" or "5 to 10 mph"
                    import re
                    # Try to find "X to Y mph" pattern first
                    range_match = re.search(r'(\d+)\s+to\s+(\d+)', wind_speed_str)
                    if range_match:
                        # Use the higher number from range
                        wind_mph = int(range_match.group(2))
                    else:
                        # Try to find single number
                        single_match = re.search(r'(\d+)', wind_speed_str)
                        if single_match:
                            wind_mph = int(single_match.group(1))
                        else:
                            wind_mph = 0
                    
                    print(f"🌬️ DEBUG {city_name} - Wind from FORECAST (not observation):")
                    print(f"   Forecast windSpeed: '{wind_speed_str}'")
                    print(f"   Parsed to: {wind_mph} mph")
                    print(f"   Forecast windDirection: '{wind_direction_str}'")
                    
                    # Only announce if wind speed is significant (>= 5 mph)
                    if wind_mph >= 5:
                        if wind_direction_str:
                            # Expand abbreviations like SSW to South-Southwest
                            expanded_direction = self._expand_wind_direction(wind_direction_str)
                            wind_text = f"winds {expanded_direction} at {wind_mph} miles per hour"
                        else:
                            wind_text = f"winds at {wind_mph} miles per hour"
                        
                        conditions_parts.append(wind_text)
                    # If wind < 5 mph, skip wind announcement (calm conditions)
                
                if conditions_parts:
                    briefing_parts.append(", ".join(conditions_parts) + ".")
            
            # Add forecast (current period)
            current_period = forecast_data['periods'][0]
            briefing_parts.append(f"{current_period['name']}, {current_period['shortForecast']}.")
            
            # Add high/low temperature
            temp = current_period['temperature']
            temp_unit = current_period['temperatureUnit']
            temp_trend = "High" if current_period['isDaytime'] else "Low"
            briefing_parts.append(f"{temp_trend} of {temp} degrees.")
            
            print(f"✅ Successfully fetched forecast for {city_name}")
            return " ".join(briefing_parts)
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1}/{max_retries} error for {city_name}: {e}, retrying in 2 seconds...")
                time.sleep(2)
                continue
            else:
                print(f"❌ All retries failed for {city_name}: {e}")
                return f"{city_name}, {state} forecast is temporarily unavailable."
    
    return f"{city_name}, {state} forecast is temporarily unavailable."


if __name__ == '__main__':
    # Test the forecast fetcher
    print("=" * 70)
    print("TESTING NWS FORECAST FETCHER FOR ATHENS, AL")
    print("=" * 70)
    
    fetcher = NWSForecastFetcher()
    
    print("\n1. Fetching Athens, AL forecast...")
    forecast = fetcher.get_home_forecast()
    
    if forecast:
        print(f"✅ Forecast retrieved successfully!")
        print(f"   Updated: {forecast['updated']}")
        print(f"   Number of periods: {len(forecast['periods'])}")
        
        print("\n2. First 3 forecast periods:")
        print("-" * 70)
        for i, period in enumerate(forecast['periods'][:3], 1):
            print(f"\n{i}. {period['name']}:")
            print(f"   Temperature: {period['temperature']}°{period['temperatureUnit']}")
            print(f"   Short: {period['shortForecast']}")
            print(f"   Detailed: {period['detailedForecast'][:150]}...")
        
        print("\n3. Short summary for broadcast:")
        print("-" * 70)
        print(fetcher.get_short_forecast_summary(forecast, 2))
        
        print("\n4. Athens-specific broadcast:")
        print("-" * 70)
        print(fetcher.get_athens_forecast_specifically())
        
        print("\n5. Severe weather check:")
        print("-" * 70)
        is_severe = fetcher.is_severe_weather_expected(forecast)
        print(f"Severe weather expected: {'YES' if is_severe else 'NO'}")
    
    else:
        print("❌ Could not fetch forecast - see error messages above")
    
    print("\n" + "=" * 70)
