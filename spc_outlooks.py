"""
spc_outlooks.py - Storm Prediction Center Multi-Day Outlooks
Fetches and announces Day 2 and Day 3 severe weather outlooks
*** LOCAL ONLY - Only announces if North Alabama/Southern Tennessee is in the risk area ***
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import json
import pytz

# Central Time Zone for accurate date calculations
CENTRAL_TZ = pytz.timezone('America/Chicago')

class SPCOutlookFetcher:
    """Fetches Storm Prediction Center outlooks - LOCAL ONLY"""
    
    def __init__(self):
        self.base_url = "https://www.spc.noaa.gov/products/outlook"
        
        # Risk categories and their severity
        self.risk_categories = {
            'TSTM': {'level': 1, 'name': 'Thunderstorm', 'color': 'green'},
            'MRGL': {'level': 2, 'name': 'Marginal', 'color': 'dark green'},
            'SLGT': {'level': 3, 'name': 'Slight', 'color': 'yellow'},
            'ENH': {'level': 4, 'name': 'Enhanced', 'color': 'orange'},
            'MDT': {'level': 5, 'name': 'Moderate', 'color': 'red'},
            'HIGH': {'level': 6, 'name': 'High', 'color': 'magenta'}
        }
        
        # *** NORTH ALABAMA & SOUTHERN TENNESSEE ONLY ***
        # Our specific monitoring area
        self.monitoring_region = {
            'lat_min': 34.0,   # Southern boundary (North AL)
            'lat_max': 35.5,   # Northern boundary (South TN)
            'lon_min': -88.0,  # Western boundary
            'lon_max': -85.5   # Eastern boundary
        }
        
        # Key cities we monitor (for text-based checking)
        self.local_cities = [
            'Huntsville', 'Athens', 'Decatur', 'Florence',
            'Muscle Shoals', 'Scottsboro', 'Cullman',
            'Madison County', 'Limestone County', 'Lauderdale County',
            'Morgan County', 'Jackson County', 'Marshall County',
            'Franklin County', 'Lincoln County'  # TN counties
        ]
    
    def fetch_outlook(self, day: int = 2) -> Optional[Dict]:
        """
        Fetch SPC outlook for specified day
        
        Args:
            day: Day number (1=today, 2=tomorrow, 3=day after tomorrow)
        
        Returns:
            Dict with outlook information or None
        """
        if day not in [1, 2, 3]:
            print(f"Invalid day: {day}. Must be 1, 2, or 3")
            return None
        
        try:
            # Fetch the GeoJSON outlook data (more accurate than HTML parsing)
            geojson_url = f"{self.base_url}/day{day}otlk_cat.lyr.geojson"
            response = requests.get(geojson_url, timeout=10)
            
            if response.status_code == 200:
                # We got GeoJSON data - most accurate!
                outlook = self._parse_geojson_outlook(response.json(), day)
                print(f"✓ Fetched Day {day} outlook from GeoJSON")
                return outlook
            else:
                # Fallback to HTML parsing
                print(f"GeoJSON not available, falling back to HTML for Day {day}")
                html_url = f"{self.base_url}/day{day}otlk.html"
                response = requests.get(html_url, timeout=10)
                
                if response.status_code != 200:
                    print(f"Failed to fetch Day {day} outlook: HTTP {response.status_code}")
                    return None
                
                outlook = self._parse_html_outlook(response.text, day)
                return outlook
        
        except Exception as e:
            print(f"Error fetching Day {day} outlook: {e}")
            return None
    
    def _parse_geojson_outlook(self, geojson_data: Dict, day: int) -> Dict:
        """
        Parse GeoJSON outlook data (most accurate method!)
        
        Args:
            geojson_data: GeoJSON from SPC
            day: Day number
        
        Returns:
            Parsed outlook dict
        """
        outlook = {
            'day': day,
            'valid_date': self._get_valid_date(day),
            'risk_level': None,
            'risk_name': None,
            'affecting_area': False,
            'hazards': [],
            'confidence': 'high'  # GeoJSON = high confidence
        }
        
        # Check if any polygons overlap our region
        if 'features' in geojson_data:
            for feature in geojson_data['features']:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                # Get risk level for this polygon
                risk_label = properties.get('LABEL', '')
                risk_code = properties.get('DN', 0)
                
                # Check if this polygon overlaps our region
                if self._polygon_overlaps_region(geometry):
                    print(f"  ✓ Found {risk_label} risk affecting our area")
                    outlook['affecting_area'] = True
                    
                    # Update highest risk level
                    for code, info in self.risk_categories.items():
                        if code in risk_label.upper():
                            if outlook['risk_level'] is None or info['level'] > outlook['risk_level']:
                                outlook['risk_level'] = info['level']
                                outlook['risk_name'] = info['name']
                
                # Extract hazards from label
                if 'TORNADO' in risk_label.upper():
                    if 'tornadoes' not in outlook['hazards']:
                        outlook['hazards'].append('tornadoes')
                if 'HAIL' in risk_label.upper():
                    if 'large hail' not in outlook['hazards']:
                        outlook['hazards'].append('large hail')
                if 'WIND' in risk_label.upper():
                    if 'damaging winds' not in outlook['hazards']:
                        outlook['hazards'].append('damaging winds')
        
        return outlook
    
    def _polygon_overlaps_region(self, geometry: Dict) -> bool:
        """
        Check if a polygon overlaps our monitoring region
        
        Args:
            geometry: GeoJSON geometry object
        
        Returns:
            True if overlaps, False otherwise
        """
        if not geometry or geometry.get('type') not in ['Polygon', 'MultiPolygon']:
            return False
        
        try:
            coordinates = geometry.get('coordinates', [])
            
            # Handle both Polygon and MultiPolygon
            if geometry['type'] == 'Polygon':
                polygons = [coordinates]
            else:  # MultiPolygon
                polygons = coordinates
            
            # Check each polygon
            for polygon in polygons:
                # polygon[0] is the outer ring
                for ring in polygon:
                    for point in ring:
                        lon, lat = point[0], point[1]
                        
                        # Check if this point is in our region
                        if (self.monitoring_region['lat_min'] <= lat <= self.monitoring_region['lat_max'] and
                            self.monitoring_region['lon_min'] <= lon <= self.monitoring_region['lon_max']):
                            return True
            
            return False
        
        except Exception as e:
            print(f"  Error checking polygon overlap: {e}")
            return False
    
    def _parse_html_outlook(self, html_content: str, day: int) -> Dict:
        """
        Parse HTML outlook (fallback method, less accurate)
        
        Args:
            html_content: HTML content from SPC
            day: Day number
        
        Returns:
            Parsed outlook dict
        """
        outlook = {
            'day': day,
            'valid_date': self._get_valid_date(day),
            'risk_level': None,
            'risk_name': None,
            'affecting_area': False,
            'hazards': [],
            'confidence': 'medium'  # HTML = medium confidence
        }
        
        # Look for risk categories in the text
        for risk_code, risk_info in self.risk_categories.items():
            if risk_code in html_content.upper():
                if outlook['risk_level'] is None or risk_info['level'] > outlook['risk_level']:
                    outlook['risk_level'] = risk_info['level']
                    outlook['risk_name'] = risk_info['name']
        
        # *** IMPROVED: Check for specific cities/counties we monitor ***
        # Only mark as affecting area if our specific cities are mentioned
        for city in self.local_cities:
            if city in html_content:
                outlook['affecting_area'] = True
                print(f"  ✓ Found mention of {city} in outlook")
                break
        
        # If no specific cities found, do NOT announce
        # This prevents announcing nationwide outlooks
        
        # Look for specific hazards
        hazard_keywords = {
            'tornado': 'tornadoes',
            'hail': 'large hail',
            'wind': 'damaging winds',
            'flooding': 'flooding'
        }
        
        for keyword, hazard_name in hazard_keywords.items():
            if keyword in html_content.lower():
                outlook['hazards'].append(hazard_name)
        
        return outlook
    
    def _get_valid_date(self, day: int) -> str:
        """Get valid date for outlook - uses Central Time"""
        # Use Central Time for accurate date calculations
        now_central = datetime.now(CENTRAL_TZ)
        target_date = now_central + timedelta(days=day-1)
        return target_date.strftime('%A, %B %d')
    
    def get_outlook_announcement(self, day: int = 2) -> Optional[str]:
        """
        Get announcement for specified day outlook
        *** ONLY announces if North Alabama/Southern Tennessee is affected ***
        
        Args:
            day: Day number (2 or 3)
        
        Returns:
            Announcement text or None
        """
        outlook = self.fetch_outlook(day)
        
        if not outlook:
            return None
        
        # *** CRITICAL: Only announce if it affects OUR area ***
        if not outlook['affecting_area']:
            print(f"  → Day {day} outlook does NOT affect our area - not announcing")
            return None
        
        # Only announce if there's a Marginal risk or higher
        if not outlook['risk_level'] or outlook['risk_level'] < 2:
            print(f"  → Day {day} outlook has no significant risk - not announcing")
            return None
        
        # Build announcement
        day_name = "tomorrow" if day == 2 else "the day after tomorrow"
        risk_name = outlook['risk_name']
        valid_date = outlook['valid_date']
        
        announcement = f"Storm Prediction Center has issued a {risk_name} risk for severe weather {day_name}, {valid_date}"
        
        # Add hazards if available
        if outlook['hazards']:
            if len(outlook['hazards']) == 1:
                announcement += f". Primary threat: {outlook['hazards'][0]}"
            elif len(outlook['hazards']) == 2:
                announcement += f". Threats include: {outlook['hazards'][0]} and {outlook['hazards'][1]}"
            else:
                hazards_text = ", ".join(outlook['hazards'][:-1]) + f" and {outlook['hazards'][-1]}"
                announcement += f". Threats include: {hazards_text}"
        
        announcement += "."
        
        print(f"  ✓ Announcing Day {day} outlook (affects our area)")
        
        return announcement
    
    def get_multi_day_summary(self) -> Optional[str]:
        """
        Get summary of Day 2 and Day 3 outlooks
        *** ONLY for North Alabama/Southern Tennessee ***
        
        Returns:
            Combined announcement or None
        """
        day2 = self.get_outlook_announcement(2)
        day3 = self.get_outlook_announcement(3)
        
        if day2 and day3:
            return f"{day2} {day3}"
        elif day2:
            return day2
        elif day3:
            return day3
        else:
            return None


# Singleton instance
_outlook_fetcher = None

def get_outlook_fetcher():
    """Get singleton outlook fetcher"""
    global _outlook_fetcher
    if _outlook_fetcher is None:
        _outlook_fetcher = SPCOutlookFetcher()
    return _outlook_fetcher


def get_day2_outlook() -> Optional[str]:
    """Get Day 2 outlook announcement - LOCAL ONLY"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_outlook_announcement(2)


def get_day3_outlook() -> Optional[str]:
    """Get Day 3 outlook announcement - LOCAL ONLY"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_outlook_announcement(3)


def get_extended_outlook() -> Optional[str]:
    """Get combined Day 2/3 outlook - LOCAL ONLY"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_multi_day_summary()


if __name__ == '__main__':
    # Test the SPC outlook fetcher
    print("=" * 70)
    print("SPC OUTLOOK FETCHER TEST - LOCAL ONLY")
    print("=" * 70)
    
    fetcher = SPCOutlookFetcher()
    
    print("\n📍 Monitoring Region:")
    print(f"Latitude: {fetcher.monitoring_region['lat_min']}° to {fetcher.monitoring_region['lat_max']}°")
    print(f"Longitude: {fetcher.monitoring_region['lon_min']}° to {fetcher.monitoring_region['lon_max']}°")
    print(f"Cities: {', '.join(fetcher.local_cities[:5])}...")
    
    print("\n1. Fetching Day 2 Outlook:")
    print("-" * 70)
    day2 = fetcher.fetch_outlook(2)
    if day2:
        print(f"Day: {day2['day']}")
        print(f"Valid: {day2['valid_date']}")
        print(f"Risk Level: {day2['risk_level']} ({day2['risk_name']})")
        print(f"Affects our area: {day2['affecting_area']} *** CRITICAL CHECK ***")
        print(f"Hazards: {', '.join(day2['hazards']) if day2['hazards'] else 'None identified'}")
        print(f"Confidence: {day2['confidence']}")
    else:
        print("No Day 2 outlook available")
    
    print("\n2. Testing announcement (LOCAL ONLY):")
    print("-" * 70)
    announcement = fetcher.get_outlook_announcement(2)
    if announcement:
        print(f"✓ WILL ANNOUNCE: {announcement}")
    else:
        print("✗ NO ANNOUNCEMENT (outlook doesn't affect our area or no significant risk)")
    
    print("\n3. Testing Day 3 Outlook:")
    print("-" * 70)
    day3_announcement = fetcher.get_outlook_announcement(3)
    if day3_announcement:
        print(f"✓ WILL ANNOUNCE: {day3_announcement}")
    else:
        print("✗ NO ANNOUNCEMENT")
    
    print("\n" + "=" * 70)
    print("✓ SPC outlook fetcher working - LOCAL ONLY MODE!")
    print("=" * 70)
    print("Will ONLY announce if:")
    print("  1. Risk level is Marginal or higher")
    print("  2. Outlook polygon overlaps North Alabama/Southern Tennessee")
    print("  3. OR specific local cities/counties are mentioned")
    print("=" * 70)
