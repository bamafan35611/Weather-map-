"""
storm_motion.py - Extract Storm Motion from NWS Alert Descriptions
Parses direction and speed from warning text
"""

import re
from typing import Optional, Dict

class StormMotionExtractor:
    """Extracts storm motion information from NWS alerts"""
    
    def __init__(self):
        # Regex patterns for different motion formats
        self.patterns = [
            # "moving northeast at 45 mph"
            r'moving\s+(\w+)\s+at\s+(\d+)\s*mph',
            
            # "moving to the northeast at 45 mph"
            r'moving\s+to\s+the\s+(\w+)\s+at\s+(\d+)\s*mph',
            
            # "moving east northeast at 45 mph"
            r'moving\s+((?:north|south|east|west)(?:\s*(?:north|south|east|west))?)\s+at\s+(\d+)\s*mph',
            
            # "traveling northeast at 45 mph"
            r'traveling\s+(\w+)\s+at\s+(\d+)\s*mph',
            
            # "nearly stationary" or "stationary"
            r'(nearly\s+stationary|stationary)',
            
            # "moving slowly to the northeast"
            r'moving\s+slowly\s+(?:to\s+the\s+)?(\w+)',
        ]
        
        # Direction abbreviations to full words
        self.direction_map = {
            'n': 'north',
            'ne': 'northeast',
            'e': 'east',
            'se': 'southeast',
            's': 'south',
            'sw': 'southwest',
            'w': 'west',
            'nw': 'northwest',
            'nne': 'north northeast',
            'ene': 'east northeast',
            'ese': 'east southeast',
            'sse': 'south southeast',
            'ssw': 'south southwest',
            'wsw': 'west southwest',
            'wnw': 'west northwest',
            'nnw': 'north northwest'
        }
    
    def extract_motion(self, alert: Dict) -> Optional[Dict]:
        """
        Extract storm motion from alert description
        
        Args:
            alert: NWS alert dictionary
        
        Returns:
            Dict with 'direction', 'speed', 'text' or None
        """
        # Get description text
        description = alert.get('description', '')
        if not description:
            return None
        
        description_lower = description.lower()
        
        # Try each pattern
        for pattern in self.patterns:
            match = re.search(pattern, description_lower)
            
            if match:
                groups = match.groups()
                
                # Stationary case
                if 'stationary' in groups[0]:
                    return {
                        'direction': None,
                        'speed': 0,
                        'text': 'nearly stationary' if 'nearly' in groups[0] else 'stationary',
                        'broadcast_text': 'Storm is nearly stationary' if 'nearly' in groups[0] else 'Storm is stationary'
                    }
                
                # Slow movement without speed
                if len(groups) == 1:
                    direction = self._normalize_direction(groups[0])
                    return {
                        'direction': direction,
                        'speed': None,
                        'text': f'moving slowly {direction}',
                        'broadcast_text': f'Storm moving slowly {direction}'
                    }
                
                # Full motion with speed
                if len(groups) >= 2:
                    direction = self._normalize_direction(groups[0])
                    try:
                        speed = int(groups[1])
                        return {
                            'direction': direction,
                            'speed': speed,
                            'text': f'moving {direction} at {speed} mph',
                            'broadcast_text': f'Storm moving {direction} at {speed} miles per hour'
                        }
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _normalize_direction(self, direction: str) -> str:
        """
        Normalize direction to full words
        
        Args:
            direction: Direction string (could be abbreviated)
        
        Returns:
            Full direction name
        """
        direction = direction.strip().lower()
        
        # Remove extra words
        direction = direction.replace('to the', '').strip()
        direction = direction.replace('the', '').strip()
        
        # Check if it's an abbreviation
        if direction in self.direction_map:
            return self.direction_map[direction]
        
        # Already full word
        return direction
    
    def get_broadcast_text(self, alert: Dict, include_in_announcement: bool = True) -> Optional[str]:
        """
        Get broadcast-ready storm motion text
        
        Args:
            alert: NWS alert dictionary
            include_in_announcement: If True, returns full sentence
        
        Returns:
            Broadcast text or None
        """
        motion = self.extract_motion(alert)
        
        if not motion:
            return None
        
        if include_in_announcement:
            return motion['broadcast_text']
        else:
            return motion['text']
    
    def enhance_alert_announcement(self, announcement: str, alert: Dict) -> str:
        """
        Add storm motion to existing alert announcement
        
        Args:
            announcement: Current announcement text
            alert: NWS alert dictionary
        
        Returns:
            Enhanced announcement with motion
        """
        motion_text = self.get_broadcast_text(alert)
        
        if motion_text:
            # Add motion after the main alert, before any other info
            return f"{announcement} {motion_text}."
        
        return announcement


# Singleton instance
_motion_extractor = None

def get_motion_extractor():
    """Get singleton motion extractor"""
    global _motion_extractor
    if _motion_extractor is None:
        _motion_extractor = StormMotionExtractor()
    return _motion_extractor


def extract_storm_motion(alert: Dict) -> Optional[Dict]:
    """
    Quick function to extract storm motion
    
    Args:
        alert: NWS alert dictionary
    
    Returns:
        Motion dict with direction, speed, text
    """
    extractor = get_motion_extractor()
    return extractor.extract_motion(alert)


def get_motion_for_broadcast(alert: Dict) -> Optional[str]:
    """
    Quick function to get broadcast-ready motion text
    
    Args:
        alert: NWS alert dictionary
    
    Returns:
        Broadcast text like "Storm moving northeast at 45 miles per hour"
    """
    extractor = get_motion_extractor()
    return extractor.get_broadcast_text(alert)


def add_motion_to_announcement(announcement: str, alert: Dict) -> str:
    """
    Add storm motion to alert announcement
    
    Args:
        announcement: Current announcement
        alert: NWS alert
    
    Returns:
        Enhanced announcement
    """
    extractor = get_motion_extractor()
    return extractor.enhance_alert_announcement(announcement, alert)


if __name__ == '__main__':
    # Test the motion extractor
    print("=" * 70)
    print("STORM MOTION EXTRACTOR TEST")
    print("=" * 70)
    
    extractor = StormMotionExtractor()
    
    # Test cases
    test_alerts = [
        {
            'event': 'Severe Thunderstorm Warning',
            'description': '...A SEVERE THUNDERSTORM WARNING REMAINS IN EFFECT UNTIL 430 PM CST FOR MADISON COUNTY... At 356 PM CST, a severe thunderstorm was located over Huntsville, moving northeast at 45 mph.'
        },
        {
            'event': 'Tornado Warning',
            'description': 'At 220 PM, a confirmed tornado was located near Athens, moving east at 35 mph. TAKE COVER NOW!'
        },
        {
            'event': 'Severe Thunderstorm Warning',
            'description': 'Doppler radar indicated a severe thunderstorm capable of producing quarter size hail. This storm was nearly stationary.'
        },
        {
            'event': 'Tornado Warning',
            'description': 'A tornado was reported on the ground moving slowly to the southeast.'
        },
        {
            'event': 'Flash Flood Warning',
            'description': 'Heavy rainfall continues across the area. No motion information available.'
        }
    ]
    
    print("\nExtracting motion from alerts:")
    print("-" * 70)
    
    for i, alert in enumerate(test_alerts, 1):
        print(f"\n{i}. {alert['event']}")
        motion = extractor.extract_motion(alert)
        
        if motion:
            print(f"   Direction: {motion['direction']}")
            print(f"   Speed: {motion['speed']} mph" if motion['speed'] else "   Speed: N/A")
            print(f"   Text: {motion['text']}")
            print(f"   Broadcast: {motion['broadcast_text']}")
        else:
            print("   No motion information found")
    
    print("\n" + "=" * 70)
    print("Testing broadcast enhancement:")
    print("-" * 70)
    
    sample_announcement = "Severe Thunderstorm Warning for Madison County until 4:30 PM"
    enhanced = extractor.enhance_alert_announcement(sample_announcement, test_alerts[0])
    
    print(f"\nOriginal: {sample_announcement}")
    print(f"Enhanced: {enhanced}")
    
    print("\n" + "=" * 70)
    print("✓ Storm motion extractor working!")
    print("=" * 70)
