"""
weekend_outlook.py - NorthBamaWX Weekend Weather Outlook
Special Friday/Saturday briefings with weekend forecast
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import requests

class WeekendOutlook:
    """Generates weekend weather outlook briefings"""
    
    def __init__(self):
        # Athens, AL coordinates (home location)
        self.HOME_LOCATION = {
            'name': 'Athens',
            'state': 'AL',
            'lat': 34.8023,
            'lon': -86.9717
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NorthBamaWX/2.0 (Weekend Outlook)',
            'Accept': 'application/geo+json'
        })
    
    def should_announce_weekend_outlook(self) -> bool:
        """
        Determine if we should announce weekend outlook
        
        Returns:
            True if it's Friday afternoon/evening or Saturday
        """
        now = datetime.now()
        day_of_week = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
        hour = now.hour
        
        # Friday after 2 PM (14:00)
        if day_of_week == 4 and hour >= 14:
            return True
        
        # All day Saturday
        if day_of_week == 5:
            return True
        
        return False
    
    def get_weekend_forecast(self) -> Optional[Dict]:
        """
        Get weekend forecast data from NWS
        
        Returns:
            Dictionary with Saturday and Sunday forecasts
        """
        try:
            # Get grid point
            points_url = f"https://api.weather.gov/points/{self.HOME_LOCATION['lat']},{self.HOME_LOCATION['lon']}"
            
            print(f"📅 Fetching weekend forecast for {self.HOME_LOCATION['name']}")
            
            points_response = self.session.get(points_url, timeout=15)
            
            if points_response.status_code != 200:
                print(f"⚠️ Points API returned {points_response.status_code}")
                return None
            
            points_data = points_response.json()
            forecast_url = points_data['properties'].get('forecast')
            
            if not forecast_url:
                print(f"❌ No forecast URL in points response")
                return None
            
            # Get forecast
            forecast_response = self.session.get(forecast_url, timeout=15)
            
            if forecast_response.status_code != 200:
                print(f"⚠️ Forecast API returned {forecast_response.status_code}")
                return None
            
            forecast_data = forecast_response.json()
            periods = forecast_data.get('properties', {}).get('periods', [])
            
            if not periods:
                print(f"❌ No forecast periods returned")
                return None
            
            # Find Saturday and Sunday periods
            now = datetime.now()
            current_day = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
            
            saturday_period = None
            sunday_period = None
            
            for period in periods:
                name = period.get('name', '').lower()
                
                # Look for Saturday
                if 'saturday' in name and not saturday_period:
                    # Prefer daytime period
                    if period.get('isDaytime', False) or not saturday_period:
                        saturday_period = period
                
                # Look for Sunday
                if 'sunday' in name and not sunday_period:
                    # Prefer daytime period
                    if period.get('isDaytime', False) or not sunday_period:
                        sunday_period = period
            
            if not saturday_period and not sunday_period:
                print(f"⚠️ Could not find Saturday or Sunday in forecast periods")
                return None
            
            result = {
                'saturday': saturday_period,
                'sunday': sunday_period,
                'current_day': current_day
            }
            
            print(f"✅ Weekend forecast retrieved")
            if saturday_period:
                print(f"   Saturday: {saturday_period.get('shortForecast', 'N/A')}, {saturday_period.get('temperature', 'N/A')}°F")
            if sunday_period:
                print(f"   Sunday: {sunday_period.get('shortForecast', 'N/A')}, {sunday_period.get('temperature', 'N/A')}°F")
            
            return result
            
        except Exception as e:
            print(f"❌ Error fetching weekend forecast: {e}")
            return None
    
    def format_weekend_outlook(self, forecast_data: Optional[Dict]) -> Optional[str]:
        """
        Format weekend forecast into broadcast-ready announcement
        
        Args:
            forecast_data: Dictionary from get_weekend_forecast()
            
        Returns:
            Formatted announcement string or None if unavailable
        """
        if not forecast_data:
            return None
        
        saturday = forecast_data.get('saturday')
        sunday = forecast_data.get('sunday')
        current_day = forecast_data.get('current_day', 0)
        
        if not saturday and not sunday:
            return None
        
        parts = []
        
        # Determine intro based on current day
        if current_day == 4:  # Friday
            parts.append("Looking ahead to the weekend:")
        elif current_day == 5:  # Saturday
            parts.append("Weekend weather update:")
        else:
            return None  # Shouldn't happen, but safety check
        
        # Saturday forecast
        if saturday:
            sat_short = saturday.get('shortForecast', 'conditions expected')
            sat_temp = saturday.get('temperature', 'Unknown')
            sat_name = saturday.get('name', 'Saturday')
            
            # Simplify the name
            if current_day == 5:  # If it's Saturday, say "Today"
                sat_name = "Today"
            elif 'night' in saturday.get('name', '').lower():
                sat_name = "Saturday night"
            else:
                sat_name = "Saturday"
            
            # Build Saturday sentence
            if 'high' in saturday.get('name', '').lower() or saturday.get('isDaytime', False):
                parts.append(f"{sat_name} will be {sat_short.lower()} with a high of {sat_temp}.")
            else:
                parts.append(f"{sat_name} will be {sat_short.lower()} with a low of {sat_temp}.")
        
        # Sunday forecast
        if sunday:
            sun_short = sunday.get('shortForecast', 'conditions expected')
            sun_temp = sunday.get('temperature', 'Unknown')
            sun_name = sunday.get('name', 'Sunday')
            
            # Simplify the name
            if current_day == 6:  # If it's Sunday, say "Today" (rare, but handle it)
                sun_name = "Today"
            elif 'night' in sunday.get('name', '').lower():
                sun_name = "Sunday night"
            else:
                sun_name = "Sunday"
            
            # Build Sunday sentence
            if 'high' in sunday.get('name', '').lower() or sunday.get('isDaytime', False):
                if current_day == 5 and saturday:
                    # On Saturday, use "expects" or "looks" for Sunday
                    parts.append(f"{sun_name} expects {sun_short.lower()} with temperatures near {sun_temp}.")
                else:
                    parts.append(f"{sun_name} will be {sun_short.lower()} with a high of {sun_temp}.")
            else:
                parts.append(f"{sun_name} will be {sun_short.lower()} with a low of {sun_temp}.")
        
        announcement = " ".join(parts)
        print(f"📢 Weekend outlook prepared: {len(announcement)} chars")
        
        return announcement


# Singleton instance
_weekend_outlook_instance = None

def get_weekend_outlook() -> WeekendOutlook:
    """Get the singleton WeekendOutlook instance"""
    global _weekend_outlook_instance
    if _weekend_outlook_instance is None:
        _weekend_outlook_instance = WeekendOutlook()
    return _weekend_outlook_instance


def get_weekend_announcement() -> Optional[str]:
    """
    Convenience function to get broadcast-ready weekend outlook
    
    Returns:
        Formatted announcement or None if not weekend or unavailable
    """
    outlook = get_weekend_outlook()
    
    # Check if we should announce
    if not outlook.should_announce_weekend_outlook():
        return None
    
    # Get forecast data
    forecast_data = outlook.get_weekend_forecast()
    
    if not forecast_data:
        return None
    
    # Format announcement
    return outlook.format_weekend_outlook(forecast_data)


# For testing
if __name__ == "__main__":
    print("Testing Weekend Outlook System...")
    print("-" * 50)
    
    outlook = WeekendOutlook()
    
    # Check if we should announce
    should_announce = outlook.should_announce_weekend_outlook()
    now = datetime.now()
    
    print(f"\n📅 Current Day: {now.strftime('%A, %B %d, %Y')}")
    print(f"   Time: {now.strftime('%I:%M %p')}")
    print(f"   Should announce weekend outlook: {should_announce}")
    
    if should_announce:
        print(f"\n✅ It's time for a weekend outlook!")
        
        forecast_data = outlook.get_weekend_forecast()
        
        if forecast_data:
            announcement = outlook.format_weekend_outlook(forecast_data)
            
            if announcement:
                print(f"\n📢 BROADCAST ANNOUNCEMENT:")
                print(f"   {announcement}")
            else:
                print(f"\n⚠️ Could not format weekend announcement")
        else:
            print(f"\n⚠️ Could not fetch weekend forecast")
    else:
        print(f"\n✓ Not the right time for weekend outlook")
        print(f"   (Only announces Friday after 2 PM and Saturday)")
