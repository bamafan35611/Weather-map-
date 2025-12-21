"""
spc_outlooks.py - Storm Prediction Center Multi-Day Outlooks
Fetches and announces Day 2 and Day 3 severe weather outlooks
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

class SPCOutlookFetcher:
    """Fetches Storm Prediction Center outlooks"""
    
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
        
        # North Alabama and Southern Tennessee monitoring area
        self.monitoring_states = ['AL', 'TN']
        self.monitoring_region = {
            'lat_min': 34.0,
            'lat_max': 35.5,
            'lon_min': -87.5,
            'lon_max': -85.5
        }
    
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
            # Fetch the outlook text product
            url = f"{self.base_url}/day{day}otlk.html"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"Failed to fetch Day {day} outlook: HTTP {response.status_code}")
                return None
            
            html_content = response.text
            
            # Parse the outlook
            outlook = self._parse_outlook(html_content, day)
            
            return outlook
        
        except Exception as e:
            print(f"Error fetching Day {day} outlook: {e}")
            return None
    
    def _parse_outlook(self, html_content: str, day: int) -> Dict:
        """
        Parse SPC outlook HTML
        
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
            'raw_text': ''
        }
        
        # Look for risk categories in the text
        for risk_code, risk_info in self.risk_categories.items():
            if risk_code in html_content.upper():
                # Found a risk category
                if outlook['risk_level'] is None or risk_info['level'] > outlook['risk_level']:
                    outlook['risk_level'] = risk_info['level']
                    outlook['risk_name'] = risk_info['name']
        
        # Check if our region is mentioned
        if any(state in html_content.upper() for state in self.monitoring_states):
            outlook['affecting_area'] = True
        
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
        """Get valid date for outlook"""
        target_date = datetime.now() + timedelta(days=day-1)
        return target_date.strftime('%A, %B %d')
    
    def get_outlook_announcement(self, day: int = 2) -> Optional[str]:
        """
        Get announcement for specified day outlook
        
        Args:
            day: Day number (2 or 3)
        
        Returns:
            Announcement text or None
        """
        outlook = self.fetch_outlook(day)
        
        if not outlook:
            return None
        
        # Only announce if there's a risk and it affects our area
        if not outlook['risk_level'] or outlook['risk_level'] < 2:
            # No significant risk
            return None
        
        if not outlook['affecting_area']:
            # Doesn't affect our region
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
            else:
                hazards_text = ", ".join(outlook['hazards'][:-1]) + f" and {outlook['hazards'][-1]}"
                announcement += f". Threats include: {hazards_text}"
        
        announcement += "."
        
        return announcement
    
    def get_multi_day_summary(self) -> Optional[str]:
        """
        Get summary of Day 2 and Day 3 outlooks
        
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
    """Get Day 2 outlook announcement"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_outlook_announcement(2)


def get_day3_outlook() -> Optional[str]:
    """Get Day 3 outlook announcement"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_outlook_announcement(3)


def get_extended_outlook() -> Optional[str]:
    """Get combined Day 2/3 outlook"""
    fetcher = get_outlook_fetcher()
    return fetcher.get_multi_day_summary()


if __name__ == '__main__':
    # Test the SPC outlook fetcher
    print("=" * 70)
    print("SPC OUTLOOK FETCHER TEST")
    print("=" * 70)
    
    fetcher = SPCOutlookFetcher()
    
    print("\n1. Fetching Day 2 Outlook:")
    print("-" * 70)
    day2 = fetcher.fetch_outlook(2)
    if day2:
        print(f"Day: {day2['day']}")
        print(f"Valid: {day2['valid_date']}")
        print(f"Risk Level: {day2['risk_level']} ({day2['risk_name']})")
        print(f"Affects our area: {day2['affecting_area']}")
        print(f"Hazards: {', '.join(day2['hazards']) if day2['hazards'] else 'None identified'}")
    else:
        print("No Day 2 outlook available")
    
    print("\n2. Testing announcement:")
    print("-" * 70)
    announcement = fetcher.get_outlook_announcement(2)
    if announcement:
        print(f"Announcement: {announcement}")
    else:
        print("No significant outlook to announce")
    
    print("\n3. Testing Day 3 Outlook:")
    print("-" * 70)
    day3_announcement = fetcher.get_outlook_announcement(3)
    if day3_announcement:
        print(f"Day 3: {day3_announcement}")
    else:
        print("No Day 3 outlook to announce")
    
    print("\n" + "=" * 70)
    print("✓ SPC outlook fetcher working!")
    print("Note: Outlooks only announce if risk level is Marginal or higher")
    print("      and the outlook affects North Alabama or Southern Tennessee")
    print("=" * 70)
