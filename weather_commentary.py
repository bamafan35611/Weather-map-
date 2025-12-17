"""
weather_commentary.py - NorthBamaWX Weather Commentary Generator
Makes your bot talkative by generating interesting weather narration
"""

from typing import Dict, List, Optional
from datetime import datetime
import pytz
import random
import re

# Import weather enhancements (temperature, wind, precipitation data)
try:
    from weather_enhancements import add_environmental_context
    ENHANCEMENTS_AVAILABLE = True
    print("✓ Weather enhancements loaded - temperature, wind, precipitation data enabled")
except ImportError as e:
    print(f"⚠ Weather enhancements not available: {e}")
    ENHANCEMENTS_AVAILABLE = False
    # Fallback function that does nothing
    def add_environmental_context(text, broadcast_type=None):
        return text


def clean_nws_text(text: str) -> str:
    """
    Clean up awkward NWS phrasing to make it sound better when spoken
    This fixes text that comes directly from NWS alert descriptions
    """
    if not text:
        return text
    
    # Fix "packing" phrases (common NWS meteorological jargon)
    replacements = {
        'packing flooding': 'bringing flooding',
        'packing floods': 'bringing floods',
        'packing heavy flooding': 'bringing heavy flooding',
        'packing flash flooding': 'bringing flash flooding',
        'packing rainfall': 'bringing rainfall',
        'packing rain': 'bringing rain',
        'packing winds': 'bringing winds',
        'packing severe weather': 'bringing severe weather',
        'packing thunderstorms': 'bringing thunderstorms',
        'packing hail': 'bringing hail',
        'storm is packing': 'storm is bringing',
        'system is packing': 'system is bringing',
        'storms are packing': 'storms are bringing',
        'systems are packing': 'systems are bringing',
        'front is packing': 'front is bringing',
        
        # Other awkward phrases
        'dumping heavy rain': 'bringing heavy rain',
        'unloading rainfall': 'bringing rainfall',
        'producing copious': 'producing heavy',
    }
    
    # Apply replacements (case-insensitive)
    for bad_phrase, good_phrase in replacements.items():
        # Use regex for case-insensitive replacement
        pattern = re.compile(re.escape(bad_phrase), re.IGNORECASE)
        text = pattern.sub(good_phrase, text)
    
    return text

class WeatherCommentary:
    """Generates engaging weather commentary for broadcasting"""
    
    def __init__(self):
        self.regions = {
            'Plains': ['Kansas', 'Oklahoma', 'Nebraska', 'Texas', 'Missouri'],
            'Southeast': ['Alabama', 'Georgia', 'Tennessee', 'Mississippi', 'Louisiana'],
            'Northeast': ['New York', 'Massachusetts', 'Pennsylvania', 'Maine'],
            'Midwest': ['Illinois', 'Ohio', 'Indiana', 'Michigan', 'Wisconsin'],
            'West': ['California', 'Washington', 'Oregon', 'Nevada', 'Arizona'],
            'Southwest': ['New Mexico', 'Arizona', 'Nevada', 'Utah'],
            'Mountain': ['Colorado', 'Wyoming', 'Montana', 'Idaho'],
            'Gulf Coast': ['Florida', 'Louisiana', 'Texas', 'Mississippi', 'Alabama']
        }
    
    def _clean_text(self, text: str) -> str:
        """Internal method to clean all generated text"""
        return clean_nws_text(text)
    
    def generate_national_briefing(self, alerts: List[Dict], scored_alerts: List[Dict]) -> str:
        """Generate a comprehensive national weather briefing"""
        
        if not alerts:
            return self._clean_text(self._generate_quiet_weather_commentary())
        
        lines = []
        
        # Opening
        lines.append(self._get_opening())
        
        # Alert count and overview
        total = len(alerts)
        lines.append(f"Currently monitoring {total} active weather alerts across the nation.")
        
        # Break down by severity
        severity_breakdown = self._analyze_severity(scored_alerts)
        if severity_breakdown:
            lines.append(severity_breakdown)
        
        # Regional breakdown
        regional = self._analyze_by_region(alerts)
        if regional:
            lines.extend(regional)
        
        # Highlight top threats
        top_threats = self._highlight_top_threats(scored_alerts[:3])
        if top_threats:
            lines.extend(top_threats)
        
        # Alert type summary
        type_summary = self._summarize_alert_types(alerts)
        if type_summary:
            lines.append(type_summary)
        
        # Closing
        lines.append(self._get_closing())
        
        # Clean all the joined text
        return self._clean_text(" ".join(lines))
    
    def generate_regional_update(self, alerts: List[Dict], region: str = 'Southeast') -> str:
        """Generate regional weather update"""
        
        # Filter alerts for region
        region_alerts = self._filter_by_region(alerts, region)
        
        if not region_alerts:
            return f"Quiet weather across the {region} at this hour. All clear for now."
        
        lines = []
        lines.append(f"Let's check in on the {region}.")
        lines.append(f"We're tracking {len(region_alerts)} active alerts in this region.")
        
        # Describe the situation
        for alert in region_alerts[:3]:  # Top 3
            location = alert.get('areaDesc', 'the area')
            event = alert.get('event', 'Weather Alert')
            lines.append(f"{event} in effect for {location}.")
        
        return " ".join(lines)
    
    def generate_interesting_facts(self, alerts: List[Dict]) -> Optional[str]:
        """Generate interesting facts about current weather"""
        
        if not alerts:
            return None
        
        facts = []
        
        # Count tornado warnings
        tornado_count = sum(1 for a in alerts if 'tornado' in a.get('event', '').lower())
        if tornado_count > 0:
            facts.append(f"We're currently tracking {tornado_count} tornado warning{'s' if tornado_count > 1 else ''} nationwide.")
        
        # Find unusual weather
        unusual = self._find_unusual_weather(alerts)
        if unusual:
            facts.append(unusual)
        
        # Geographic spread
        states = set()
        for alert in alerts:
            location = alert.get('areaDesc', '')
            for state in ['Alabama', 'Oklahoma', 'Texas', 'California', 'Florida', 'Kansas']:
                if state in location:
                    states.add(state)
        
        if len(states) >= 5:
            facts.append(f"Active weather is affecting {len(states)} states from coast to coast.")
        
        return " ".join(facts) if facts else None
    
    def generate_comparison_commentary(self, alerts: List[Dict]) -> Optional[str]:
        """Generate comparative commentary about different weather systems"""
        
        if len(alerts) < 2:
            return None
        
        lines = []
        
        # Compare different types of weather
        tornado_alerts = [a for a in alerts if 'tornado' in a.get('event', '').lower()]
        flood_alerts = [a for a in alerts if 'flood' in a.get('event', '').lower()]
        wind_alerts = [a for a in alerts if 'wind' in a.get('event', '').lower()]
        
        if tornado_alerts and flood_alerts:
            lines.append(f"We're dealing with a complex weather pattern today.")
            lines.append(f"Severe weather in the Plains with {len(tornado_alerts)} tornado warning{'s' if len(tornado_alerts) > 1 else ''},")
            lines.append(f"while the Pacific Northwest is handling {len(flood_alerts)} flood alert{'s' if len(flood_alerts) > 1 else ''}.")
        
        if wind_alerts and len(wind_alerts) >= 5:
            lines.append(f"High winds are a major story today, with {len(wind_alerts)} wind alerts active.")
        
        return " ".join(lines) if lines else None
    
    def generate_weather_story(self, alerts: List[Dict], scored_alerts: List[Dict]) -> str:
        """Generate a narrative story about current weather"""
        
        if not alerts:
            return self._clean_text(self._generate_quiet_weather_commentary())
        
        lines = []
        
        # Start with the headline
        highest_threat = scored_alerts[0] if scored_alerts else None
        if highest_threat:
            score = highest_threat.get('threat_score', {}).get('score', 0)
            event = highest_threat.get('event', 'Weather Alert')
            location = highest_threat.get('areaDesc', 'the area')
            
            if score >= 85:
                lines.append("Breaking weather situation developing right now.")
                lines.append(f"A {event} is the top concern, affecting {location}.")
                lines.append(f"Our AI rates this as a {score} out of 100 threat level.")
            elif score >= 70:
                lines.append("Significant weather activity across multiple regions.")
                lines.append(f"The leading story is a {event} for {location}.")
            else:
                lines.append("Active weather pattern continues.")
        
        # Add the big picture
        lines.append(self._describe_weather_pattern(alerts))
        
        # Regional highlights
        regions_affected = self._count_regions_affected(alerts)
        if regions_affected >= 3:
            lines.append(f"This is truly a coast to coast weather event, with {regions_affected} regions experiencing active conditions.")
        
        # What's coming
        lines.append("We'll continue monitoring these systems and keep you updated.")
        
        return self._clean_text(" ".join(lines))
    
    def generate_hourly_update(self, alerts: List[Dict], scored_alerts: List[Dict], 
                               hour: int, local_area: str = "North Alabama") -> str:
        """Generate hourly weather update"""
        
        lines = []
        
        # Time-specific greeting
        if 6 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 17:
            greeting = "Good afternoon"
        elif 17 <= hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Good night"
        
        lines.append(f"{greeting}, this is NorthBamaWX with your weather intelligence update.")
        
        # National overview
        if alerts:
            lines.append(f"Across the nation, we're monitoring {len(alerts)} active weather alerts.")
            
            # Severity breakdown
            severe_count = sum(1 for a in scored_alerts if a.get('threat_score', {}).get('score', 0) >= 70)
            if severe_count > 0:
                lines.append(f"{severe_count} of these are high severity warnings requiring immediate attention.")
        else:
            lines.append("Quiet weather across the country at this hour.")
        
        # Local check
        local_alerts = self._filter_by_location(alerts, local_area)
        if local_alerts:
            lines.append(f"Here in {local_area}, we have {len(local_alerts)} active alert{'s' if len(local_alerts) > 1 else ''}.")
        else:
            lines.append(f"All clear here in {local_area}.")
        
        # Interesting tidbit
        fact = self.generate_interesting_facts(alerts)
        if fact:
            lines.append(fact)
        
        lines.append("Stay weather aware.")
        
        return self._clean_text(" ".join(lines))
    
    def _generate_quiet_weather_commentary(self) -> str:
        """Generate commentary when weather is quiet"""
        
        options = [
            "Quiet weather across the nation right now. No significant alerts to report. We're keeping an eye on conditions and will update you if anything develops.",
            
            "All quiet on the weather front at this hour. The National Weather Service has no major alerts active. Enjoying the calm before the next weather system arrives.",
            
            "Calm conditions nationwide. Our AI monitoring system is active but finding nothing to worry about. This is the kind of weather everyone can appreciate.",
            
            "Weather conditions are tranquil across the country. No watches or warnings in effect. We'll stay vigilant and keep you updated.",
            
            "Taking advantage of the quiet weather today. Our automated systems are monitoring all 50 states, ready to alert you the moment conditions change."
        ]
        
        return random.choice(options)
    
    def _analyze_severity(self, scored_alerts: List[Dict]) -> Optional[str]:
        """Analyze and describe severity distribution"""
        
        if not scored_alerts:
            return None
        
        extreme = sum(1 for a in scored_alerts if a.get('threat_score', {}).get('score', 0) >= 95)
        severe = sum(1 for a in scored_alerts if 85 <= a.get('threat_score', {}).get('score', 0) < 95)
        high = sum(1 for a in scored_alerts if 70 <= a.get('threat_score', {}).get('score', 0) < 85)
        
        parts = []
        if extreme > 0:
            parts.append(f"{extreme} extreme threat{'s' if extreme > 1 else ''}")
        if severe > 0:
            parts.append(f"{severe} severe situation{'s' if severe > 1 else ''}")
        if high > 0:
            parts.append(f"{high} high-level alert{'s' if high > 1 else ''}")
        
        if parts:
            return "Breaking this down, we have " + ", ".join(parts) + "."
        
        return None
    
    def _analyze_by_region(self, alerts: List[Dict]) -> List[str]:
        """Analyze alerts by geographic region"""
        
        region_counts = {}
        for region_name, states in self.regions.items():
            count = sum(1 for alert in alerts 
                       if any(state in alert.get('areaDesc', '') for state in states))
            if count > 0:
                region_counts[region_name] = count
        
        if not region_counts:
            return []
        
        lines = []
        if len(region_counts) > 1:
            lines.append("Weather activity is scattered across several regions.")
        
        for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count >= 3:
                lines.append(f"The {region} has {count} active alerts.")
            elif count == 1:
                lines.append(f"One alert in the {region}.")
        
        return lines
    
    def _highlight_top_threats(self, top_alerts: List[Dict]) -> List[str]:
        """Highlight the top threat situations"""
        
        if not top_alerts:
            return []
        
        lines = []
        lines.append("Let's focus on the highest priority situations.")
        
        for i, alert in enumerate(top_alerts, 1):
            event = alert.get('event', 'Alert')
            location = alert.get('areaDesc', 'an area')
            score = alert.get('threat_score', {}).get('score', 0)
            
            if i == 1:
                lines.append(f"Number one concern: {event} affecting {location}, rated {score} out of 100 on our threat scale.")
            else:
                lines.append(f"Also watching a {event} for {location}.")
        
        return lines
    
    def _summarize_alert_types(self, alerts: List[Dict]) -> Optional[str]:
        """Summarize what types of weather are active"""
        
        types = {}
        for alert in alerts:
            event = alert.get('event', 'Alert')
            event_type = event.split()[0]  # Get first word (Tornado, Flood, etc.)
            types[event_type] = types.get(event_type, 0) + 1
        
        if not types:
            return None
        
        # Get top 3 types
        top_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]
        
        parts = [f"{count} {type_name.lower()}" for type_name, count in top_types]
        
        return "We're dealing with " + ", ".join(parts) + " situations across the country."
    
    def _find_unusual_weather(self, alerts: List[Dict]) -> Optional[str]:
        """Find and describe unusual weather patterns"""
        
        # Look for unusual combinations
        events = [a.get('event', '').lower() for a in alerts]
        
        if 'tornado' in ' '.join(events) and 'snow' in ' '.join(events):
            return "Quite a diverse weather day with both tornado and snow alerts active."
        
        if 'heat' in ' '.join(events) and 'winter' in ' '.join(events):
            return "The full range of American weather on display, from heat advisories to winter alerts."
        
        # Check for rare events
        if any('tsunami' in e for e in events):
            return "Notably, we have tsunami alerts which are relatively rare."
        
        if any('earthquake' in e for e in events):
            return "We're also tracking earthquake-related alerts."
        
        return None
    
    def _describe_weather_pattern(self, alerts: List[Dict]) -> str:
        """Describe the overall weather pattern"""
        
        # Count different phenomena
        has_severe = any('severe' in a.get('event', '').lower() or 'tornado' in a.get('event', '').lower() for a in alerts)
        has_flood = any('flood' in a.get('event', '').lower() for a in alerts)
        has_wind = any('wind' in a.get('event', '').lower() for a in alerts)
        has_winter = any('snow' in a.get('event', '').lower() or 'winter' in a.get('event', '').lower() for a in alerts)
        
        if has_severe and has_flood:
            return "We're seeing a classic spring severe weather setup with both thunderstorms and flooding concerns."
        elif has_wind and len(alerts) >= 5:
            return "A strong wind event is the main story today with impacts across multiple states."
        elif has_winter:
            return "Winter weather is making its presence felt."
        elif has_flood:
            return "Heavy rainfall and flooding are the primary concerns."
        else:
            return "Multiple weather systems are active across different regions."
    
    def _count_regions_affected(self, alerts: List[Dict]) -> int:
        """Count how many regions are affected"""
        
        affected_regions = set()
        for region_name, states in self.regions.items():
            if any(any(state in alert.get('areaDesc', '') for state in states) for alert in alerts):
                affected_regions.add(region_name)
        
        return len(affected_regions)
    
    def _filter_by_region(self, alerts: List[Dict], region: str) -> List[Dict]:
        """Filter alerts by region"""
        
        region_states = self.regions.get(region, [])
        return [a for a in alerts if any(state in a.get('areaDesc', '') for state in region_states)]
    
    def _filter_by_location(self, alerts: List[Dict], location: str) -> List[Dict]:
        """Filter alerts by specific location"""
        
        return [a for a in alerts if location in a.get('areaDesc', '')]
    
    def _get_opening(self) -> str:
        """Get a dynamic opening line"""
        
        openings = [
            "Good day everyone, this is NorthBamaWX with your national weather intelligence update.",
            "NorthBamaWX here with a look at active weather across the nation.",
            "Welcome to NorthBamaWX. Let's check on weather conditions nationwide.",
            "This is NorthBamaWX, your AI-powered weather intelligence system.",
        ]
        
        return random.choice(openings)
    
    def _get_closing(self) -> str:
        """Get a dynamic closing line"""
        
        closings = [
            "That's your weather intelligence update from NorthBamaWX. Stay weather aware.",
            "We'll continue monitoring these systems. Stay safe out there.",
            "NorthBamaWX keeping you informed 24/7. More updates to come.",
            "Stay tuned for updates as conditions develop. This is NorthBamaWX.",
        ]
        
        return random.choice(closings)


# Helper functions for Flask integration
def get_national_briefing(alerts: List[Dict], scored_alerts: List[Dict]) -> str:
    """Get national weather briefing with environmental enhancements"""
    commentary = WeatherCommentary()
    base_briefing = commentary.generate_national_briefing(alerts, scored_alerts)
    
    # Clean up awkward NWS text
    base_briefing = clean_nws_text(base_briefing)
    
    # Add temperature, wind, precipitation context
    if ENHANCEMENTS_AVAILABLE:
        return add_environmental_context(base_briefing, "national_briefing")
    return base_briefing


def get_regional_briefing(alerts: List[Dict], scored_alerts: List[Dict]) -> str:
    """
    Get REGIONAL briefing for North Alabama & Southern Tennessee only
    Replaces national briefing for regional monitoring
    """
    commentary = WeatherCommentary()
    
    if not alerts:
        return commentary._clean_text(commentary._generate_quiet_weather_commentary())
    
    lines = []
    
    # Opening - Regional focus
    openings = [
        "Good day everyone, this is NorthBamaWX with your regional weather update for North Alabama and Southern Tennessee.",
        "NorthBamaWX here with conditions across North Alabama and Southern Tennessee.",
        "Welcome to NorthBamaWX. Let's check weather conditions across our region.",
        "This is NorthBamaWX, monitoring weather across North Alabama and Southern Tennessee.",
    ]
    lines.append(random.choice(openings))
    
    # Alert count
    total = len(alerts)
    if total == 1:
        lines.append("We're currently monitoring 1 active weather alert across the region.")
    else:
        lines.append(f"We're currently monitoring {total} active weather alerts across the region.")
    
    # Severity breakdown
    if scored_alerts:
        high_threat = sum(1 for a in scored_alerts if a.get('threat_score', {}).get('score', 0) >= 70)
        medium_threat = sum(1 for a in scored_alerts if 40 <= a.get('threat_score', {}).get('score', 0) < 70)
        
        if high_threat > 0:
            lines.append(f"{high_threat} high-priority alert{'s' if high_threat > 1 else ''} requiring immediate attention.")
        elif medium_threat > 0:
            lines.append(f"{medium_threat} moderate-priority alert{'s' if medium_threat > 1 else ''} across the area.")
    
    # Break down by state/area
    al_alerts = [a for a in alerts if 'Alabama' in a.get('areaDesc', '')]
    tn_alerts = [a for a in alerts if 'Tennessee' in a.get('areaDesc', '')]
    
    if al_alerts and tn_alerts:
        lines.append(f"{len(al_alerts)} alert{'s' if len(al_alerts) != 1 else ''} in North Alabama, {len(tn_alerts)} in Southern Tennessee.")
    elif al_alerts:
        lines.append(f"All alerts are in North Alabama at this time.")
    elif tn_alerts:
        lines.append(f"All alerts are in Southern Tennessee at this time.")
    
    # Highlight top threats (top 2 for regional briefing)
    if scored_alerts:
        for i, alert in enumerate(scored_alerts[:2], 1):
            event = alert.get('event', 'Weather Alert')
            location = alert.get('areaDesc', 'the area')
            # Simplify location to just counties
            if ',' in location:
                location = location.split(';')[0]  # Get first county if multiple
            lines.append(f"{event} in effect for {location}.")
    
    # Alert type summary
    alert_types = {}
    for alert in alerts:
        event = alert.get('event', 'Alert')
        event_type = event.split()[0]  # Get first word
        alert_types[event_type] = alert_types.get(event_type, 0) + 1
    
    if alert_types:
        top_types = sorted(alert_types.items(), key=lambda x: x[1], reverse=True)[:2]
        type_parts = [f"{count} {type_name.lower()}" for type_name, count in top_types]
        if len(type_parts) == 1:
            lines.append(f"Primary concern: {type_parts[0]}.")
        else:
            lines.append(f"Primary concerns: {', '.join(type_parts)}.")
    
    # Closing - Regional focus
    closings = [
        "That's your regional weather update from NorthBamaWX. Stay weather aware.",
        "We'll continue monitoring conditions across the region. Stay safe out there.",
        "NorthBamaWX keeping you informed 24/7. More updates at the top and bottom of each hour.",
        "Stay tuned for updates. This is NorthBamaWX, your regional weather intelligence.",
    ]
    lines.append(random.choice(closings))
    
    # Clean and return
    return commentary._clean_text(" ".join(lines))


def get_hourly_update(alerts: List[Dict], scored_alerts: List[Dict], local_area: str = "North Alabama") -> str:
    """Get hourly weather update with environmental enhancements"""
    commentary = WeatherCommentary()
    # Use Central Time (Alabama time zone)
    central = pytz.timezone('America/Chicago')
    hour = datetime.now(central).hour
    base_update = commentary.generate_hourly_update(alerts, scored_alerts, hour, local_area)
    
    # Clean up awkward NWS text
    base_update = clean_nws_text(base_update)
    
    # Add environmental context
    if ENHANCEMENTS_AVAILABLE:
        return add_environmental_context(base_update, "hourly_update")
    return base_update


def get_weather_story(alerts: List[Dict], scored_alerts: List[Dict]) -> str:
    """Get weather story/narrative with environmental enhancements"""
    commentary = WeatherCommentary()
    base_story = commentary.generate_weather_story(alerts, scored_alerts)
    
    # Clean up awkward NWS text
    base_story = clean_nws_text(base_story)
    
    # Add environmental context
    if ENHANCEMENTS_AVAILABLE:
        return add_environmental_context(base_story, "weather_story")
    return base_story


if __name__ == '__main__':
    # Test the commentary system
    print("=" * 70)
    print("NORTHBAMAWX WEATHER COMMENTARY TEST")
    print("=" * 70)
    
    # Simulate some alerts
    test_alerts = [
        {'event': 'Tornado Warning', 'areaDesc': 'Oklahoma City, Oklahoma'},
        {'event': 'Severe Thunderstorm Warning', 'areaDesc': 'Atlanta, Georgia'},
        {'event': 'Flash Flood Warning', 'areaDesc': 'Seattle, Washington'},
        {'event': 'High Wind Warning', 'areaDesc': 'Cheyenne, Wyoming'},
        {'event': 'Tornado Watch', 'areaDesc': 'Kansas City, Kansas'},
    ]
    
    test_scored = [
        {'event': 'Tornado Warning', 'areaDesc': 'Oklahoma City, OK', 'threat_score': {'score': 90}},
        {'event': 'Severe Thunderstorm Warning', 'areaDesc': 'Atlanta, GA', 'threat_score': {'score': 75}},
        {'event': 'Flash Flood Warning', 'areaDesc': 'Seattle, WA', 'threat_score': {'score': 80}},
    ]
    
    commentary = WeatherCommentary()
    
    print("\nTEST 1: National Briefing")
    print("-" * 70)
    print(commentary.generate_national_briefing(test_alerts, test_scored))
    
    print("\n\nTEST 2: Hourly Update")
    print("-" * 70)
    print(commentary.generate_hourly_update(test_alerts, test_scored, 14))
    
    print("\n\nTEST 3: Weather Story")
    print("-" * 70)
    print(commentary.generate_weather_story(test_alerts, test_scored))
    
    print("\n\nTEST 4: Quiet Weather")
    print("-" * 70)
    print(commentary.generate_national_briefing([], []))
    
    print("\n" + "=" * 70)
    print("Weather commentary system working!")
    print("=" * 70)
