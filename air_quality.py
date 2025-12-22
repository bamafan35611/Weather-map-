"""
air_quality.py - NorthBamaWX Air Quality Index System
Fetches and announces current air quality data from EPA AirNow API
"""

import requests
from typing import Optional, Dict
from datetime import datetime

class AirQuality:
    """Fetches and formats air quality data from EPA AirNow"""
    
    def __init__(self):
        # Primary monitoring location (Huntsville, AL - covers North Alabama)
        self.PRIMARY_LOCATION = {
            'name': 'Huntsville',
            'state': 'AL',
            'lat': 34.7304,
            'lon': -86.5861,
            'zip': '35801'
        }
        
        # AQI Categories with health messages
        self.AQI_CATEGORIES = {
            'Good': {
                'range': (0, 50),
                'color': 'Green',
                'announce': False,
                'message': None  # Don't announce when air is good
            },
            'Moderate': {
                'range': (51, 100),
                'color': 'Yellow',
                'announce': True,
                'message': "Unusually sensitive people should consider limiting prolonged outdoor activity."
            },
            'Unhealthy for Sensitive Groups': {
                'range': (101, 150),
                'color': 'Orange',
                'announce': True,
                'message': "People with respiratory or heart conditions, children, and older adults should limit prolonged outdoor activity."
            },
            'Unhealthy': {
                'range': (151, 200),
                'color': 'Red',
                'announce': True,
                'message': "Everyone should limit prolonged outdoor activity."
            },
            'Very Unhealthy': {
                'range': (201, 300),
                'color': 'Purple',
                'announce': True,
                'message': "Everyone should avoid prolonged outdoor activity. People with respiratory or heart conditions should remain indoors."
            },
            'Hazardous': {
                'range': (301, 500),
                'color': 'Maroon',
                'announce': True,
                'message': "Everyone should avoid all outdoor activity. This is an emergency condition."
            }
        }
        
        # Pollutant descriptions
        self.POLLUTANTS = {
            'PM2.5': 'fine particulate matter',
            'PM10': 'particulate matter',
            'O3': 'ozone',
            'NO2': 'nitrogen dioxide',
            'SO2': 'sulfur dioxide',
            'CO': 'carbon monoxide'
        }
    
    def get_current_aqi(self, zip_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get current air quality index for location
        
        Args:
            zip_code: ZIP code to check (defaults to Huntsville)
            
        Returns:
            Dictionary with AQI data or None if unavailable
        """
        if zip_code is None:
            zip_code = self.PRIMARY_LOCATION['zip']
        
        try:
            # AirNow API endpoint (observation by ZIP code)
            # Note: This is a simplified implementation
            # Production should use registered AirNow API key
            url = f"https://www.airnowapi.org/aq/observation/zipCode/current/"
            
            params = {
                'format': 'application/json',
                'zipCode': zip_code,
                'distance': 25,  # Search within 25 miles
                'API_KEY': 'GUEST'  # Use guest key for testing (limited)
            }
            
            print(f"🌫️ Fetching air quality for ZIP {zip_code}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    print(f"⚠️ No AQI data available for {zip_code}")
                    return None
                
                # Get the highest AQI reading (worst pollutant)
                highest_aqi = max(data, key=lambda x: x.get('AQI', 0))
                
                aqi_value = highest_aqi.get('AQI', 0)
                category = highest_aqi.get('Category', {}).get('Name', 'Unknown')
                pollutant = highest_aqi.get('ParameterName', 'Unknown')
                reporting_area = highest_aqi.get('ReportingArea', zip_code)
                
                result = {
                    'aqi': aqi_value,
                    'category': category,
                    'pollutant': pollutant,
                    'location': reporting_area,
                    'timestamp': highest_aqi.get('DateObserved', ''),
                    'raw_data': highest_aqi
                }
                
                print(f"✅ AQI for {reporting_area}: {aqi_value} ({category})")
                print(f"   Dominant pollutant: {pollutant}")
                
                return result
            else:
                print(f"⚠️ AirNow API returned {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching air quality: {e}")
            return None
    
    def _get_category_from_aqi(self, aqi_value: int) -> str:
        """Determine category name from AQI value"""
        for category, info in self.AQI_CATEGORIES.items():
            min_val, max_val = info['range']
            if min_val <= aqi_value <= max_val:
                return category
        return 'Unknown'
    
    def _should_announce(self, aqi_value: int) -> bool:
        """Determine if this AQI level should be announced"""
        category = self._get_category_from_aqi(aqi_value)
        return self.AQI_CATEGORIES.get(category, {}).get('announce', False)
    
    def format_aqi_announcement(self, aqi_data: Optional[Dict]) -> Optional[str]:
        """
        Format AQI data into a broadcast-ready announcement
        
        Args:
            aqi_data: Dictionary from get_current_aqi()
            
        Returns:
            Formatted announcement string or None if shouldn't announce
        """
        if not aqi_data:
            return None
        
        aqi_value = aqi_data.get('aqi', 0)
        category = aqi_data.get('category', 'Unknown')
        pollutant = aqi_data.get('pollutant', 'Unknown')
        location = aqi_data.get('location', 'our area')
        
        # Check if we should announce this AQI level
        if not self._should_announce(aqi_value):
            print(f"✓ AQI is {category} ({aqi_value}) - no announcement needed")
            return None
        
        # Build announcement
        parts = []
        
        # Lead with AQI value and category
        if category == 'Moderate':
            parts.append(f"Air quality is currently moderate with an index of {aqi_value}.")
        elif category == 'Unhealthy for Sensitive Groups':
            parts.append(f"Air quality is unhealthy for sensitive groups with an index of {aqi_value}.")
        elif category == 'Unhealthy':
            parts.append(f"Air quality is unhealthy with an index of {aqi_value}.")
        elif category == 'Very Unhealthy':
            parts.append(f"Air quality is very unhealthy with an index of {aqi_value}.")
        elif category == 'Hazardous':
            parts.append(f"Air quality has reached hazardous levels with an index of {aqi_value}.")
        else:
            parts.append(f"Air quality index is {aqi_value}.")
        
        # Add dominant pollutant if we recognize it
        pollutant_name = self.POLLUTANTS.get(pollutant, pollutant.lower())
        if pollutant != 'Unknown':
            parts.append(f"The primary pollutant is {pollutant_name}.")
        
        # Add health message
        category_info = self.AQI_CATEGORIES.get(category, {})
        health_message = category_info.get('message')
        if health_message:
            parts.append(health_message)
        
        announcement = " ".join(parts)
        print(f"📢 AQI announcement prepared: {len(announcement)} chars")
        
        return announcement
    
    def get_aqi_voice_style(self, aqi_value: int) -> str:
        """
        Determine appropriate voice style based on AQI severity
        
        Args:
            aqi_value: AQI value (0-500)
            
        Returns:
            Voice style name for TTS
        """
        if aqi_value <= 50:
            return 'calm'
        elif aqi_value <= 100:
            return 'professional'
        elif aqi_value <= 150:
            return 'concerned'
        elif aqi_value <= 200:
            return 'urgent'
        else:
            return 'emergency'


# Singleton instance
_air_quality_instance = None

def get_air_quality() -> AirQuality:
    """Get the singleton AirQuality instance"""
    global _air_quality_instance
    if _air_quality_instance is None:
        _air_quality_instance = AirQuality()
    return _air_quality_instance


def get_aqi_announcement(zip_code: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to get broadcast-ready AQI announcement
    
    Args:
        zip_code: ZIP code to check (defaults to Huntsville)
        
    Returns:
        Dictionary with 'text' and 'voice_style' or None if shouldn't announce
    """
    aq = get_air_quality()
    aqi_data = aq.get_current_aqi(zip_code)
    
    if not aqi_data:
        return None
    
    announcement = aq.format_aqi_announcement(aqi_data)
    
    if not announcement:
        return None
    
    return {
        'text': announcement,
        'voice_style': aq.get_aqi_voice_style(aqi_data.get('aqi', 0)),
        'aqi_value': aqi_data.get('aqi'),
        'category': aqi_data.get('category')
    }


# For testing
if __name__ == "__main__":
    print("Testing Air Quality System...")
    print("-" * 50)
    
    aq = AirQuality()
    
    # Test with Huntsville ZIP
    print("\n📍 Checking Huntsville, AL (35801)...")
    aqi_data = aq.get_current_aqi('35801')
    
    if aqi_data:
        print(f"\n✅ Current AQI Data:")
        print(f"   AQI: {aqi_data['aqi']}")
        print(f"   Category: {aqi_data['category']}")
        print(f"   Pollutant: {aqi_data['pollutant']}")
        print(f"   Location: {aqi_data['location']}")
        
        announcement = aq.format_aqi_announcement(aqi_data)
        
        if announcement:
            print(f"\n📢 BROADCAST ANNOUNCEMENT:")
            print(f"   {announcement}")
            print(f"\n🎙️ Voice Style: {aq.get_aqi_voice_style(aqi_data['aqi'])}")
        else:
            print(f"\n✓ AQI is good - no announcement needed")
    else:
        print("\n⚠️ Could not fetch AQI data")
        print("   (May need API key for production use)")
