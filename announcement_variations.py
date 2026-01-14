"""
announcement_variations.py - Natural Language Variations for Weather Bot
Provides multiple ways to say the same thing for more natural broadcasts
"""

import random
from datetime import datetime
from typing import List, Dict, Optional
import pytz

class AnnouncementVariations:
    """Manages natural language variations for weather announcements"""
    
    def __init__(self):
        # Time-of-day greetings
        self.greetings = {
            'early_morning': [  # 12am-6am
                "Good early morning",
                "This is NorthBamaWX with your overnight weather update",
                "NorthBamaWX here with conditions overnight"
            ],
            'morning': [  # 6am-12pm
                "Good morning",
                "Good morning from NorthBamaWX",
                "NorthBamaWX with your morning update"
            ],
            'afternoon': [  # 12pm-5pm
                "Good afternoon",
                "Good afternoon from NorthBamaWX",
                "NorthBamaWX with your afternoon update"
            ],
            'evening': [  # 5pm-9pm
                "Good evening",
                "Good evening from NorthBamaWX",
                "NorthBamaWX with your evening update"
            ],
            'night': [  # 9pm-12am
                "Good evening",
                "NorthBamaWX with your late evening update",
                "This is NorthBamaWX with tonight's weather"
            ]
        }
        
        # All clear variations
        self.all_clear = [
            "NorthBamaWX. All quiet at this time.",
            "NorthBamaWX. Weather conditions calm across the region.",
            "NorthBamaWX. No active alerts this hour.",
            "NorthBamaWX. Conditions remain quiet.",
            "NorthBamaWX. All clear across North Alabama and Southern Tennessee.",
            "NorthBamaWX. Weather quiet across our monitoring area.",
            "NorthBamaWX. No weather alerts in effect.",
            "NorthBamaWX. All quiet on the weather front."
        ]
        
        # Regional briefing intros
        self.regional_briefing_intros = [
            "Here's what's happening weather-wise across North Alabama and Southern Tennessee.",
            "Let's check conditions across our monitoring area.",
            "Here's your regional weather intelligence update.",
            "Checking in on weather across North Alabama and Southern Tennessee.",
            "Here's the latest from across our region."
        ]
        
        # Alert intros (when alerts exist)
        self.alert_intros = [
            "NorthBamaWX with current weather alerts.",
            "NorthBamaWX. We're tracking active weather alerts.",
            "NorthBamaWX with important weather information.",
            "NorthBamaWX. Active weather alerts in effect.",
            "NorthBamaWX monitoring active weather alerts."
        ]
        
        # Multiple alerts intro
        self.multiple_alerts_intros = [
            "Multiple weather alerts remain in effect.",
            "Several alerts are active across the region.",
            "We're tracking multiple weather alerts.",
            "Multiple warnings and watches in effect.",
            "Numerous alerts active across our monitoring area."
        ]
        
        # Watch callout variations
        self.watch_callouts = [
            "Also, a {watch_type} remains in effect for {area}.",
            "Additionally, a {watch_type} is active for {area}.",
            "A {watch_type} is also in effect for {area}.",
            "We're also tracking a {watch_type} for {area}.",
            "Note that a {watch_type} continues for {area}."
        ]
        
        # Expiration variations
        self.single_expiration = [
            "Update: The {event} for {area} has expired.",
            "The {event} for {area} is no longer in effect.",
            "Update: {event} for {area} has ended.",
            "{event} for {area} has now expired.",
            "The {event} affecting {area} is no longer in effect."
        ]
        
        self.multiple_expirations = [
            "Update: {count} weather alerts have expired.",
            "{count} alerts are no longer in effect.",
            "Update: {count} warnings and watches have ended.",
            "{count} weather alerts have now expired.",
            "Conditions improving as {count} alerts have expired."
        ]
        
        # Forecast intro variations
        self.forecast_intros = [
            "Here's the forecast for {location}.",
            "The forecast for {location}.",
            "Looking ahead for {location}.",
            "{location} forecast.",
            "Checking the forecast for {location}."
        ]
        
        # City briefing intros
        self.city_briefing_intros = [
            "Now checking conditions in {city}.",
            "A look at {city}.",
            "Conditions in {city}.",
            "Over in {city}.",
            "Checking in on {city}."
        ]
        
        # Storm motion variations (used in storm_motion.py integration)
        self.storm_motion_phrases = [
            "Storm moving {direction} at {speed} miles per hour.",
            "This storm is moving {direction} at {speed} miles per hour.",
            "Movement: {direction} at {speed} miles per hour.",
            "Tracking {direction} at {speed} miles per hour.",
            "Storm heading {direction} at {speed} miles per hour."
        ]
        
        # Transition phrases
        self.transitions = [
            "Now,",
            "Meanwhile,",
            "Additionally,",
            "Also,",
            "In other weather news,",
            "Turning our attention to,",
            "Looking at,"
        ]
        
        # Closing phrases
        self.closings = [
            "Stay weather aware.",
            "We'll keep you updated.",
            "Stay safe out there.",
            "More updates ahead.",
            "Stay informed.",
            "We're monitoring conditions.",
            "Check back for updates."
        ]
    
    def get_time_of_day(self) -> str:
        """Get current time of day category using Central Time"""
        central = pytz.timezone('America/Chicago')
        hour = datetime.now(central).hour
        
        if 0 <= hour < 6:
            return 'early_morning'
        elif 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def get_greeting(self, time_specific: bool = True) -> str:
        """
        Get time-appropriate greeting
        
        Args:
            time_specific: If True, use time-specific greeting. If False, generic.
        
        Returns:
            Greeting string
        """
        if time_specific:
            time_of_day = self.get_time_of_day()
            return random.choice(self.greetings[time_of_day])
        else:
            return "NorthBamaWX"
    
    def get_all_clear(self) -> str:
        """Get variation for all clear announcement"""
        return random.choice(self.all_clear)
    
    def get_regional_briefing_intro(self) -> str:
        """Get variation for regional briefing intro"""
        return random.choice(self.regional_briefing_intros)
    
    def get_alert_intro(self, alert_count: int = 1) -> str:
        """
        Get variation for alert intro
        
        Args:
            alert_count: Number of alerts
        
        Returns:
            Alert intro string
        """
        if alert_count > 1:
            return random.choice(self.multiple_alerts_intros)
        else:
            return random.choice(self.alert_intros)
    
    def get_watch_callout(self, watch_type: str, area: str) -> str:
        """
        Get variation for watch callout
        
        Args:
            watch_type: Type of watch (e.g., "Tornado Watch")
            area: Affected area
        
        Returns:
            Watch callout string
        """
        template = random.choice(self.watch_callouts)
        return template.format(watch_type=watch_type, area=area)
    
    def get_expiration_announcement(self, event: str, area: str, count: int = 1) -> str:
        """
        Get variation for expiration announcement
        
        Args:
            event: Event type (e.g., "Tornado Warning")
            area: Affected area
            count: Number of expirations
        
        Returns:
            Expiration announcement string
        """
        if count == 1:
            template = random.choice(self.single_expiration)
            return template.format(event=event, area=area)
        else:
            template = random.choice(self.multiple_expirations)
            return template.format(count=count)
    
    def get_forecast_intro(self, location: str) -> str:
        """Get variation for forecast intro"""
        template = random.choice(self.forecast_intros)
        return template.format(location=location)
    
    def get_city_briefing_intro(self, city: str) -> str:
        """Get variation for city briefing intro"""
        template = random.choice(self.city_briefing_intros)
        return template.format(city=city)
    
    def get_storm_motion_phrase(self, direction: str, speed: int) -> str:
        """Get variation for storm motion announcement"""
        template = random.choice(self.storm_motion_phrases)
        return template.format(direction=direction, speed=speed)
    
    def get_transition(self) -> str:
        """Get transition phrase"""
        return random.choice(self.transitions)
    
    def get_closing(self) -> str:
        """Get closing phrase"""
        return random.choice(self.closings)


# Singleton instance
_variations = None

def get_variations():
    """Get singleton variations instance"""
    global _variations
    if _variations is None:
        _variations = AnnouncementVariations()
    return _variations


# Convenience functions
def get_greeting(time_specific: bool = True) -> str:
    """Get time-appropriate greeting"""
    return get_variations().get_greeting(time_specific)

def get_all_clear() -> str:
    """Get all clear variation"""
    return get_variations().get_all_clear()

def get_regional_briefing_intro() -> str:
    """Get regional briefing intro"""
    return get_variations().get_regional_briefing_intro()

def get_alert_intro(alert_count: int = 1) -> str:
    """Get alert intro"""
    return get_variations().get_alert_intro(alert_count)

def get_watch_callout(watch_type: str, area: str) -> str:
    """Get watch callout"""
    return get_variations().get_watch_callout(watch_type, area)

def get_expiration_announcement(event: str, area: str, count: int = 1) -> str:
    """Get expiration announcement"""
    return get_variations().get_expiration_announcement(event, area, count)

def get_forecast_intro(location: str) -> str:
    """Get forecast intro"""
    return get_variations().get_forecast_intro(location)

def get_city_briefing_intro(city: str) -> str:
    """Get city briefing intro"""
    return get_variations().get_city_briefing_intro(city)

def get_transition() -> str:
    """Get transition phrase"""
    return get_variations().get_transition()

def get_closing() -> str:
    """Get closing phrase"""
    return get_variations().get_closing()


if __name__ == '__main__':
    # Test the variations
    print("=" * 70)
    print("ANNOUNCEMENT VARIATIONS TEST")
    print("=" * 70)
    
    variations = AnnouncementVariations()
    
    print("\n1. Greetings (5 samples)")
    print("-" * 70)
    for i in range(5):
        print(f"  {variations.get_greeting()}")
    
    print("\n2. All Clear (5 samples)")
    print("-" * 70)
    for i in range(5):
        print(f"  {variations.get_all_clear()}")
    
    print("\n3. Alert Intros (5 samples)")
    print("-" * 70)
    for i in range(5):
        print(f"  {variations.get_alert_intro()}")
    
    print("\n4. Watch Callouts (3 samples)")
    print("-" * 70)
    for i in range(3):
        print(f"  {variations.get_watch_callout('Tornado Watch', 'Madison County')}")
    
    print("\n5. Expiration Announcements (3 samples)")
    print("-" * 70)
    for i in range(3):
        print(f"  {variations.get_expiration_announcement('Severe Thunderstorm Warning', 'Morgan County')}")
    
    print("\n6. City Briefings (3 samples)")
    print("-" * 70)
    for i in range(3):
        print(f"  {variations.get_city_briefing_intro('Huntsville')}")
    
    print("\n7. Storm Motion (3 samples)")
    print("-" * 70)
    for i in range(3):
        print(f"  {variations.get_storm_motion_phrase('northeast', 45)}")
    
    print("\n" + "=" * 70)
    print("✓ Variations system working! Bot will sound more natural!")
    print("=" * 70)
