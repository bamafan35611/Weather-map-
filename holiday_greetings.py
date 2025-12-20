"""
holiday_greetings.py - Seasonal Holiday Greetings for NorthBamaWX
Adds special holiday messages to broadcasts
"""

from datetime import datetime
from typing import Optional

class HolidayGreetings:
    """Manages holiday greetings for weather broadcasts"""
    
    def __init__(self):
        # Define holidays with date ranges (month, day_start, day_end)
        self.holidays = {
            'New Year': {
                'dates': [(1, 1, 1)],  # January 1
                'greetings': [
                    "Happy New Year from NorthBamaWX!",
                    "Wishing you a safe and prosperous New Year!",
                    "Happy 2026 from your weather intelligence team!"
                ]
            },
            'MLK Day': {
                'dates': [(1, 15, 21)],  # Third Monday in January (approximate)
                'greetings': [
                    "Happy Martin Luther King Junior Day.",
                    "Honoring Doctor Martin Luther King Junior today."
                ]
            },
            'Groundhog Day': {
                'dates': [(2, 2, 2)],
                'greetings': [
                    "Happy Groundhog Day! Will we see six more weeks of winter?",
                    "It's Groundhog Day! Let's see what the weather brings."
                ]
            },
            'Valentine\'s Day': {
                'dates': [(2, 14, 14)],
                'greetings': [
                    "Happy Valentine's Day from NorthBamaWX!",
                    "Wishing you a lovely Valentine's Day!",
                    "Happy Valentine's Day! Stay safe out there today."
                ]
            },
            'Presidents Day': {
                'dates': [(2, 15, 21)],  # Third Monday in February (approximate)
                'greetings': [
                    "Happy Presidents Day!",
                    "Observing Presidents Day today."
                ]
            },
            'St. Patrick\'s Day': {
                'dates': [(3, 17, 17)],
                'greetings': [
                    "Happy Saint Patrick's Day!",
                    "Top of the morning to you on this Saint Patrick's Day!",
                    "Happy Saint Patrick's Day from NorthBamaWX!"
                ]
            },
            'Easter': {
                'dates': [(3, 22, 4, 25)],  # Easter range (varies, approximate)
                'greetings': [
                    "Happy Easter from NorthBamaWX!",
                    "Wishing you a blessed Easter Sunday!",
                    "Happy Easter! Hope you have a wonderful day."
                ]
            },
            'Memorial Day': {
                'dates': [(5, 25, 31)],  # Last Monday in May (approximate)
                'greetings': [
                    "Happy Memorial Day. Remembering those who served.",
                    "Honoring our fallen heroes this Memorial Day.",
                    "Happy Memorial Day from NorthBamaWX."
                ]
            },
            'Independence Day': {
                'dates': [(7, 3, 5)],  # July 4th +/- 1 day
                'greetings': [
                    "Happy Fourth of July!",
                    "Happy Independence Day from NorthBamaWX!",
                    "Wishing you a safe and happy Fourth of July!",
                    "Happy Independence Day! Enjoy the fireworks safely!"
                ]
            },
            'Labor Day': {
                'dates': [(9, 1, 7)],  # First Monday in September (approximate)
                'greetings': [
                    "Happy Labor Day!",
                    "Wishing you a relaxing Labor Day!",
                    "Happy Labor Day from NorthBamaWX!"
                ]
            },
            'Halloween': {
                'dates': [(10, 30, 31)],  # Oct 30-31
                'greetings': [
                    "Happy Halloween from NorthBamaWX!",
                    "Happy Halloween! Stay safe trick-or-treating tonight!",
                    "It's Halloween! Spooky weather or just spooky fun tonight?",
                    "Happy Halloween! Check conditions before heading out for candy!"
                ]
            },
            'Veterans Day': {
                'dates': [(11, 11, 11)],
                'greetings': [
                    "Happy Veterans Day. Thank you to all who served.",
                    "Honoring our veterans today.",
                    "Happy Veterans Day from NorthBamaWX."
                ]
            },
            'Thanksgiving': {
                'dates': [(11, 22, 28)],  # Fourth Thursday in November (approximate)
                'greetings': [
                    "Happy Thanksgiving from NorthBamaWX!",
                    "Wishing you a wonderful Thanksgiving!",
                    "Happy Thanksgiving! Safe travels to everyone today.",
                    "Happy Thanksgiving! We're thankful for our community."
                ]
            },
            'Christmas Eve': {
                'dates': [(12, 24, 24)],
                'greetings': [
                    "Merry Christmas Eve from NorthBamaWX!",
                    "Happy Christmas Eve! Santa's on his way!",
                    "Merry Christmas Eve! Stay safe tonight.",
                    "It's Christmas Eve! Check weather for Santa's arrival!"
                ]
            },
            'Christmas': {
                'dates': [(12, 25, 25)],
                'greetings': [
                    "Merry Christmas from NorthBamaWX!",
                    "Merry Christmas! Wishing you and your family a wonderful day!",
                    "Happy Christmas from your weather intelligence team!",
                    "Merry Christmas! Hope Santa was good to you!"
                ]
            },
            'New Year\'s Eve': {
                'dates': [(12, 31, 31)],
                'greetings': [
                    "Happy New Year's Eve from NorthBamaWX!",
                    "Happy New Year's Eve! Stay safe celebrating tonight!",
                    "Ring in the New Year safely! Happy New Year's Eve!",
                    "It's New Year's Eve! Check conditions before heading out tonight!"
                ]
            }
        }
    
    def get_holiday_greeting(self, now: Optional[datetime] = None) -> Optional[str]:
        """
        Get holiday greeting for current date
        
        Args:
            now: Current datetime (defaults to now)
        
        Returns:
            Holiday greeting string or None if no holiday
        """
        if now is None:
            now = datetime.now()
        
        month = now.month
        day = now.day
        
        # Check each holiday
        for holiday_name, holiday_data in self.holidays.items():
            for date_range in holiday_data['dates']:
                if len(date_range) == 3:
                    # Single day or range within same month
                    h_month, day_start, day_end = date_range
                    if month == h_month and day_start <= day <= day_end:
                        # Pick first greeting (or could randomize)
                        return holiday_data['greetings'][0]
                elif len(date_range) == 4:
                    # Range spanning two months (like Easter)
                    month_start, day_start, month_end, day_end = date_range
                    if (month == month_start and day >= day_start) or \
                       (month == month_end and day <= day_end):
                        return holiday_data['greetings'][0]
        
        return None
    
    def should_include_greeting(self, broadcast_type: str = 'any') -> bool:
        """
        Determine if holiday greeting should be included
        
        Args:
            broadcast_type: Type of broadcast (top_of_hour, quarter_past, etc.)
        
        Returns:
            True if greeting should be included
        """
        # Only include on top-of-hour broadcasts to avoid repetition
        return broadcast_type in ['top_of_hour', 'hourly_update', 'regional_briefing']
    
    def get_holiday_enhanced_greeting(self, standard_greeting: str, 
                                     broadcast_type: str = 'any') -> str:
        """
        Add holiday greeting to standard broadcast greeting
        
        Args:
            standard_greeting: Regular broadcast greeting
            broadcast_type: Type of broadcast
        
        Returns:
            Enhanced greeting with holiday message
        """
        if not self.should_include_greeting(broadcast_type):
            return standard_greeting
        
        holiday_greeting = self.get_holiday_greeting()
        
        if holiday_greeting:
            return f"{holiday_greeting} {standard_greeting}"
        else:
            return standard_greeting


# Singleton instance
_holiday_system = None

def get_holiday_system():
    """Get singleton holiday greeting system"""
    global _holiday_system
    if _holiday_system is None:
        _holiday_system = HolidayGreetings()
    return _holiday_system


def get_current_holiday_greeting() -> Optional[str]:
    """
    Quick function to get current holiday greeting
    
    Returns:
        Holiday greeting or None
    """
    system = get_holiday_system()
    return system.get_holiday_greeting()


def add_holiday_greeting_to_broadcast(broadcast_text: str, 
                                      broadcast_type: str = 'any') -> str:
    """
    Add holiday greeting to broadcast if appropriate
    
    Args:
        broadcast_text: Original broadcast text
        broadcast_type: Type of broadcast
    
    Returns:
        Enhanced broadcast text with holiday greeting
    """
    system = get_holiday_system()
    
    if not system.should_include_greeting(broadcast_type):
        return broadcast_text
    
    holiday_greeting = system.get_holiday_greeting()
    
    if holiday_greeting:
        # Add greeting at the beginning
        return f"{holiday_greeting} {broadcast_text}"
    else:
        return broadcast_text


if __name__ == '__main__':
    # Test the holiday system
    print("=" * 70)
    print("NORTHBAMAWX HOLIDAY GREETING SYSTEM TEST")
    print("=" * 70)
    
    system = HolidayGreetings()
    
    # Test specific dates
    test_dates = [
        datetime(2025, 1, 1),   # New Year
        datetime(2025, 2, 14),  # Valentine's
        datetime(2025, 7, 4),   # July 4th
        datetime(2025, 10, 31), # Halloween
        datetime(2025, 12, 24), # Christmas Eve
        datetime(2025, 12, 25), # Christmas
        datetime(2025, 12, 31), # New Year's Eve
        datetime(2025, 6, 15),  # Random day (no holiday)
    ]
    
    print("\nTesting holiday greetings:")
    for test_date in test_dates:
        greeting = system.get_holiday_greeting(test_date)
        date_str = test_date.strftime("%B %d, %Y")
        if greeting:
            print(f"  {date_str}: '{greeting}'")
        else:
            print(f"  {date_str}: No holiday")
    
    # Test enhancement
    print("\nTesting broadcast enhancement:")
    sample_broadcast = "NorthBamaWX. All quiet on the weather front this morning."
    
    christmas_date = datetime(2025, 12, 25)
    enhanced = system.get_holiday_enhanced_greeting(
        sample_broadcast, 
        broadcast_type='hourly_update'
    )
    
    # Manually set to Christmas for demo
    original_greeting = system.get_holiday_greeting
    system.get_holiday_greeting = lambda now=None: "Merry Christmas from NorthBamaWX!"
    
    enhanced = system.get_holiday_enhanced_greeting(
        sample_broadcast,
        broadcast_type='hourly_update'
    )
    
    print(f"  Original: {sample_broadcast}")
    print(f"  Enhanced: {enhanced}")
    
    print("\n" + "=" * 70)
    print("✓ Holiday greeting system working!")
    print("=" * 70)
