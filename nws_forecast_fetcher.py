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
