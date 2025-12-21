"""
weather_history.py - Historical Weather Comparisons
Compares current conditions to historical records
"""

import requests
from datetime import datetime
from typing import Dict, Optional

class WeatherHistoryComparer:
    """Compares current weather to historical records"""
    
    def __init__(self):
        # NOAA Climate Data API
        self.climate_api_base = "https://www.ncdc.noaa.gov/cdo-web/api/v2"
        
        # Historical records for North Alabama cities (manually compiled)
        # Format: {city: {month_day: {'record_high': temp, 'record_high_year': year, ...}}}
        self.local_records = {
            'Huntsville': {
                '12-21': {'record_high': 77, 'record_high_year': 1967, 'record_low': 5, 'record_low_year': 1989},
                '12-22': {'record_high': 75, 'record_high_year': 2015, 'record_low': 3, 'record_low_year': 1989},
                '12-25': {'record_high': 79, 'record_high_year': 2015, 'record_low': 1, 'record_low_year': 1983},
                '01-01': {'record_high': 79, 'record_high_year': 2022, 'record_low': -11, 'record_low_year': 2018},
                '07-04': {'record_high': 105, 'record_high_year': 2012, 'record_low': 56, 'record_low_year': 1933},
                # Add more dates as needed
            },
            'Athens': {
                '12-21': {'record_high': 76, 'record_high_year': 1967, 'record_low': 6, 'record_low_year': 1989},
                '12-25': {'record_high': 78, 'record_high_year': 2015, 'record_low': 2, 'record_low_year': 1983},
                # Add more dates as needed
            }
        }
        
        # Normal temperatures by month for North Alabama
        self.monthly_normals = {
            1: {'high': 50, 'low': 31},   # January
            2: {'high': 55, 'low': 34},   # February
            3: {'high': 64, 'low': 42},   # March
            4: {'high': 73, 'low': 50},   # April
            5: {'high': 81, 'low': 59},   # May
            6: {'high': 88, 'low': 67},   # June
            7: {'high': 91, 'low': 71},   # July
            8: {'high': 91, 'low': 70},   # August
            9: {'high': 85, 'low': 63},   # September
            10: {'high': 74, 'low': 51},  # October
            11: {'high': 63, 'low': 41},  # November
            12: {'high': 52, 'low': 33}   # December
        }
    
    def get_date_key(self, date: datetime = None) -> str:
        """Get date key in MM-DD format"""
        if date is None:
            date = datetime.now()
        return date.strftime('%m-%d')
    
    def get_record_for_date(self, city: str, date: datetime = None) -> Optional[Dict]:
        """
        Get historical records for a specific date
        
        Args:
            city: City name
            date: Date to check (default: today)
        
        Returns:
            Dict with record data or None
        """
        date_key = self.get_date_key(date)
        
        if city in self.local_records and date_key in self.local_records[city]:
            return self.local_records[city][date_key]
        
        return None
    
    def compare_to_record(self, city: str, current_temp: float, is_high: bool = True, date: datetime = None) -> Optional[str]:
        """
        Compare current temperature to record
        
        Args:
            city: City name
            current_temp: Current temperature
            is_high: True for high temp, False for low temp
            date: Date to compare (default: today)
        
        Returns:
            Comparison text or None
        """
        records = self.get_record_for_date(city, date)
        
        if not records:
            return None
        
        if is_high:
            record = records.get('record_high')
            record_year = records.get('record_high_year')
            record_type = "high"
        else:
            record = records.get('record_low')
            record_year = records.get('record_low_year')
            record_type = "low"
        
        if record is None:
            return None
        
        # Check if tying or breaking record
        if abs(current_temp - record) < 0.5:  # Tying record
            return f"That ties the record {record_type} set in {record_year}."
        elif (is_high and current_temp > record) or (not is_high and current_temp < record):
            # Breaking record
            diff = abs(current_temp - record)
            return f"That breaks the record {record_type} of {record:.0f} degrees set in {record_year} by {diff:.0f} degrees!"
        elif abs(current_temp - record) <= 5:
            # Within 5 degrees of record
            diff = abs(current_temp - record)
            return f"That's within {diff:.0f} degrees of the record {record_type} of {record:.0f} set in {record_year}."
        
        return None
    
    def compare_to_normal(self, current_temp: float, month: int = None) -> Optional[str]:
        """
        Compare current temperature to monthly normal
        
        Args:
            current_temp: Current temperature
            month: Month number (default: current month)
        
        Returns:
            Comparison text or None
        """
        if month is None:
            month = datetime.now().month
        
        normals = self.monthly_normals.get(month)
        if not normals:
            return None
        
        avg_normal = (normals['high'] + normals['low']) / 2
        diff = current_temp - avg_normal
        
        if abs(diff) >= 10:
            if diff > 0:
                return f"That's {abs(diff):.0f} degrees above normal for this time of year."
            else:
                return f"That's {abs(diff):.0f} degrees below normal for this time of year."
        
        return None
    
    def get_temperature_context(self, city: str, current_temp: float, is_high: bool = True) -> Optional[str]:
        """
        Get full temperature context (record + normal comparison)
        
        Args:
            city: City name
            current_temp: Current temperature
            is_high: True for high temp, False for low temp
        
        Returns:
            Context text or None
        """
        record_comparison = self.compare_to_record(city, current_temp, is_high)
        normal_comparison = self.compare_to_normal(current_temp)
        
        if record_comparison:
            return record_comparison
        elif normal_comparison:
            return normal_comparison
        
        return None


# Singleton instance
_history_comparer = None

def get_history_comparer():
    """Get singleton history comparer"""
    global _history_comparer
    if _history_comparer is None:
        _history_comparer = WeatherHistoryComparer()
    return _history_comparer


def get_temperature_context(city: str, temp: float, is_high: bool = True) -> Optional[str]:
    """Get historical context for temperature"""
    comparer = get_history_comparer()
    return comparer.get_temperature_context(city, temp, is_high)


if __name__ == '__main__':
    # Test the history comparer
    print("=" * 70)
    print("WEATHER HISTORY COMPARER TEST")
    print("=" * 70)
    
    comparer = WeatherHistoryComparer()
    
    print("\n1. Test record comparison (today):")
    print("-" * 70)
    
    # Test tying record
    test_cases = [
        ('Huntsville', 77, True, "Tying record high"),
        ('Huntsville', 80, True, "Breaking record high"),
        ('Huntsville', 73, True, "Near record high"),
        ('Huntsville', 60, True, "Normal temperature"),
    ]
    
    for city, temp, is_high, description in test_cases:
        result = comparer.compare_to_record(city, temp, is_high)
        print(f"\n{description}: {temp}°F in {city}")
        if result:
            print(f"  Context: {result}")
        else:
            print(f"  No record context")
    
    print("\n2. Test normal comparison:")
    print("-" * 70)
    
    # December normal is ~42°F average
    test_temps = [25, 40, 55, 70]
    for temp in test_temps:
        result = comparer.compare_to_normal(temp, month=12)
        print(f"\n{temp}°F in December:")
        if result:
            print(f"  {result}")
        else:
            print(f"  Near normal")
    
    print("\n" + "=" * 70)
    print("✓ Weather history comparer working!")
    print("=" * 70)
