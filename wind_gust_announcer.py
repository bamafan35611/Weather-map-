"""
wind_gust_announcer.py - Wind Gust Announcements
Announces dangerous wind gusts in severe weather
"""

from typing import Optional, Dict
import re

class WindGustAnnouncer:
    """Announces wind gusts in severe warnings"""
    
    def __init__(self):
        # Wind speed thresholds and descriptions
        self.wind_categories = [
            (75, "catastrophic", "Catastrophic damage possible. Widespread destruction."),
            (65, "extreme", "Extreme damage likely. Structural damage to buildings."),
            (58, "damaging", "Damaging winds. Can uproot trees and damage roofs."),
            (50, "strong", "Strong winds. Secure loose objects."),
            (40, "gusty", "Gusty winds possible."),
        ]
    
    def extract_wind_speed(self, text: str) -> Optional[int]:
        """Extract wind speed from alert text"""
        patterns = [
            r'(\d+)\s*mph\s+(?:wind|gust)',
            r'winds?\s+(?:up\s+to\s+)?(\d+)\s*mph',
            r'gusts?\s+(?:up\s+to\s+)?(\d+)\s*mph',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def get_wind_category(self, wind_speed: int) -> Dict:
        """Get category and description for wind speed"""
        for threshold, category, description in self.wind_categories:
            if wind_speed >= threshold:
                return {
                    'category': category,
                    'description': description,
                    'threshold': threshold
                }
        
        return None
    
    def get_wind_announcement(self, alert_text: str) -> Optional[str]:
        """Generate wind gust announcement"""
        wind_speed = self.extract_wind_speed(alert_text)
        
        if not wind_speed or wind_speed < 40:
            return None
        
        category_info = self.get_wind_category(wind_speed)
        
        if category_info:
            return f"Winds up to {wind_speed} miles per hour. {category_info['description']}"
        
        return f"Winds up to {wind_speed} miles per hour possible."

_announcer = None

def get_wind_announcement(text: str) -> Optional[str]:
    global _announcer
    if _announcer is None:
        _announcer = WindGustAnnouncer()
    return _announcer.get_wind_announcement(text)

if __name__ == '__main__':
    announcer = WindGustAnnouncer()
    
    test_cases = [
        "Severe thunderstorm with 70 mph winds",
        "Wind gusts up to 55 mph possible",
        "Winds to 45 mph",
    ]
    
    for test in test_cases:
        result = announcer.get_wind_announcement(test)
        print(f"{test}\n  → {result}\n")
