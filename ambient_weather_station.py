"""
ambient_weather_station.py - Personal Weather Station Integration
Pulls real-time data from Michael's Ambient Weather station in Athens, AL
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

class AmbientWeatherStation:
    """Integrates with Ambient Weather personal weather station"""
    
    def __init__(self):
        # API credentials (from environment variables or hardcoded)
        self.api_key = os.getenv('AMBIENT_API_KEY', '4823807035fa4c35ba67395c7c8f51eab50a1a48c146469fb7c4b142fe5d4915')
        self.app_key = os.getenv('AMBIENT_APP_KEY', '0d5cd6639fe145f1a12f4729241b0d5886152a2b513b48f59b581eaff00f0552')
        self.mac_address = os.getenv('AMBIENT_MAC_ADDRESS', '40:F5:20:0B:78:99')
        
        # API endpoint
        self.base_url = 'https://api.ambientweather.net/v1'
        
        # Cache to avoid hitting API too frequently
        self._last_fetch = None
        self._cached_data = None
        self._cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    def get_current_conditions(self) -> Optional[Dict]:
        """
        Get current conditions from personal weather station
        
        Returns:
            Dict with weather data or None if unavailable
        """
        try:
            # Check cache first
            if self._cached_data and self._last_fetch:
                if datetime.now() - self._last_fetch < self._cache_duration:
                    print("✓ Using cached Ambient Weather data")
                    return self._cached_data
            
            # Fetch from API
            url = f"{self.base_url}/devices/{self.mac_address}"
            params = {
                'apiKey': self.api_key,
                'applicationKey': self.app_key,
                'limit': 1  # Only get most recent reading
            }
            
            print(f"🌡️ Fetching data from Ambient Weather station {self.mac_address}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) == 0:
                print("⚠️ No data returned from Ambient Weather API")
                return None
            
            # Get most recent reading
            latest = data[0]
            
            # Parse and convert data
            conditions = self._parse_conditions(latest)
            
            # Update cache
            self._cached_data = conditions
            self._last_fetch = datetime.now()
            
            # 🆕 PHASE 7: Record for ML predictions
            try:
                from personal_station_ml import record_station_observation
                record_station_observation(conditions)
            except ImportError:
                pass  # ML module not available
            except Exception as e:
                print(f"⚠️ Error recording for ML: {e}")
            
            print(f"✓ Ambient Weather data retrieved successfully")
            print(f"   Temp: {conditions.get('temperature')}°F, Wind: {conditions.get('wind_speed')} mph")
            
            return conditions
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching Ambient Weather data: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Error parsing Ambient Weather data: {e}")
            return None
    
    def _parse_conditions(self, data: Dict) -> Dict:
        """Parse raw API data into usable format"""
        conditions = {}
        
        # Temperature (convert if needed, usually already in F)
        if 'tempf' in data:
            conditions['temperature'] = round(data['tempf'])
        
        # Wind speed (mph)
        if 'windspeedmph' in data:
            conditions['wind_speed'] = round(data['windspeedmph'])
        else:
            conditions['wind_speed'] = 0
        
        # Wind gust (mph)
        if 'windgustmph' in data:
            conditions['wind_gust'] = round(data['windgustmph'])
        
        # Wind direction (degrees)
        if 'winddir' in data:
            conditions['wind_direction_degrees'] = data['winddir']
            conditions['wind_direction'] = self._degrees_to_cardinal(data['winddir'])
        
        # Humidity (%)
        if 'humidity' in data:
            conditions['humidity'] = round(data['humidity'])
        
        # Pressure (inHg)
        if 'baromabsin' in data:
            conditions['pressure'] = round(data['baromabsin'], 2)
        
        # Rain (inches)
        if 'dailyrainin' in data:
            conditions['daily_rain'] = round(data['dailyrainin'], 2)
        
        # Feels like temperature
        if 'feelsLike' in data:
            conditions['feels_like'] = round(data['feelsLike'])
        
        # Last update time
        if 'dateutc' in data:
            conditions['observation_time'] = data['dateutc']
        
        return conditions
    
    def _degrees_to_cardinal(self, degrees: int) -> str:
        """Convert wind direction degrees to cardinal direction"""
        directions = [
            'North', 'North-Northeast', 'Northeast', 'East-Northeast',
            'East', 'East-Southeast', 'Southeast', 'South-Southeast',
            'South', 'South-Southwest', 'Southwest', 'West-Southwest',
            'West', 'West-Northwest', 'Northwest', 'North-Northwest'
        ]
        
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def get_athens_announcement(self) -> Optional[str]:
        """
        Generate Athens weather announcement from personal station
        
        Returns:
            Formatted announcement string or None
        """
        conditions = self.get_current_conditions()
        
        if not conditions:
            return None
        
        # Build announcement
        parts = []
        
        # Temperature (always include)
        if 'temperature' in conditions:
            parts.append(f"Current temperature is {conditions['temperature']} degrees")
        
        # Wind (only if significant)
        if 'wind_speed' in conditions and conditions['wind_speed'] >= 5:
            wind_dir = conditions.get('wind_direction', '')
            wind_speed = conditions['wind_speed']
            
            wind_text = f"winds from the {wind_dir} at {wind_speed} miles per hour"
            
            # Add gusts if significant
            if 'wind_gust' in conditions and conditions['wind_gust'] > wind_speed + 5:
                wind_text += f" gusting to {conditions['wind_gust']}"
            
            parts.append(wind_text)
        elif 'wind_speed' in conditions and conditions['wind_speed'] < 5:
            parts.append("winds calm")
        
        # Humidity (if extreme)
        if 'humidity' in conditions:
            humidity = conditions['humidity']
            if humidity >= 80:
                parts.append(f"humidity {humidity}%")
            elif humidity <= 30:
                parts.append(f"very dry, humidity {humidity}%")
        
        if parts:
            announcement = "Conditions from our local weather station: " + ", ".join(parts)
            return announcement
        
        return None


# Singleton instance
_station = None

def get_ambient_station() -> AmbientWeatherStation:
    """Get or create station instance"""
    global _station
    if _station is None:
        _station = AmbientWeatherStation()
    return _station


def get_personal_station_conditions() -> Optional[Dict]:
    """Get current conditions from personal weather station"""
    station = get_ambient_station()
    return station.get_current_conditions()


def get_personal_station_announcement() -> Optional[str]:
    """Get formatted announcement from personal weather station"""
    station = get_ambient_station()
    return station.get_athens_announcement()


if __name__ == '__main__':
    # Test the integration
    print("=" * 70)
    print("AMBIENT WEATHER STATION TEST")
    print("=" * 70)
    
    station = AmbientWeatherStation()
    
    print("\n1. Testing get_current_conditions()...")
    conditions = station.get_current_conditions()
    
    if conditions:
        print("\n✅ SUCCESS! Current conditions:")
        for key, value in conditions.items():
            print(f"   {key}: {value}")
    else:
        print("\n❌ FAILED to get conditions")
    
    print("\n2. Testing get_athens_announcement()...")
    announcement = station.get_athens_announcement()
    
    if announcement:
        print("\n✅ SUCCESS! Announcement:")
        print(f"   {announcement}")
    else:
        print("\n❌ FAILED to generate announcement")
    
    print("\n" + "=" * 70)
