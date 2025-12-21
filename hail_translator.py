"""
hail_translator.py - Translate Hail Sizes to Relatable Objects
Makes hail sizes more understandable with object comparisons and damage info
"""

import re
from typing import Optional, Dict

class HailTranslator:
    """Translates hail sizes into relatable terms"""
    
    def __init__(self):
        # Hail size reference chart (inches)
        self.hail_sizes = {
            'pea': {
                'inches': 0.25,
                'cm': 0.6,
                'damage': 'Minor damage to crops and plants',
                'threat': 'Low'
            },
            'marble': {
                'inches': 0.5,
                'cm': 1.3,
                'damage': 'Damage to vegetation and crops',
                'threat': 'Low to Moderate'
            },
            'dime': {
                'inches': 0.75,
                'cm': 1.9,
                'damage': 'Damage to vehicles and vegetation',
                'threat': 'Moderate'
            },
            'penny': {
                'inches': 0.75,
                'cm': 1.9,
                'damage': 'Damage to vehicles and vegetation',
                'threat': 'Moderate'
            },
            'nickel': {
                'inches': 0.88,
                'cm': 2.2,
                'damage': 'Damage to vehicles, breaks windows',
                'threat': 'Moderate'
            },
            'quarter': {
                'inches': 1.0,
                'cm': 2.5,
                'damage': 'Significant vehicle damage, breaks windows',
                'threat': 'Significant'
            },
            'half dollar': {
                'inches': 1.25,
                'cm': 3.2,
                'damage': 'Severe vehicle damage, shatters windows',
                'threat': 'Significant'
            },
            'ping pong ball': {
                'inches': 1.5,
                'cm': 3.8,
                'damage': 'Severe damage to vehicles and structures',
                'threat': 'Severe'
            },
            'golf ball': {
                'inches': 1.75,
                'cm': 4.4,
                'damage': 'Severe vehicle damage, structural damage possible',
                'threat': 'Severe'
            },
            'tennis ball': {
                'inches': 2.5,
                'cm': 6.4,
                'damage': 'Extensive vehicle and structural damage',
                'threat': 'Extreme'
            },
            'baseball': {
                'inches': 2.75,
                'cm': 7.0,
                'damage': 'Devastating damage to vehicles and structures',
                'threat': 'Extreme'
            },
            'softball': {
                'inches': 4.0,
                'cm': 10.2,
                'damage': 'Catastrophic damage, life-threatening',
                'threat': 'Catastrophic'
            },
            'grapefruit': {
                'inches': 4.5,
                'cm': 11.4,
                'damage': 'Catastrophic damage, life-threatening',
                'threat': 'Catastrophic'
            }
        }
        
        # Regex patterns to find hail size mentions
        self.patterns = [
            r'(\d+(?:\.\d+)?)\s*inch(?:es)?\s*(?:diameter\s+)?hail',
            r'(\d+(?:\.\d+)?)"?\s*hail',
            r'(pea|marble|dime|penny|nickel|quarter|half\s+dollar|ping\s+pong\s+ball|golf\s+ball|tennis\s+ball|baseball|softball|grapefruit)\s*(?:size|sized)?\s*hail',
        ]
    
    def extract_hail_size(self, text: str) -> Optional[Dict]:
        """
        Extract hail size from text
        
        Args:
            text: Alert description text
        
        Returns:
            Dict with hail size info or None
        """
        text_lower = text.lower()
        
        # Try to match object comparisons first
        for size_name, size_info in self.hail_sizes.items():
            pattern = rf'\b{size_name}\b'
            if re.search(pattern, text_lower):
                return {
                    'object': size_name.title(),
                    'inches': size_info['inches'],
                    'cm': size_info['cm'],
                    'damage': size_info['damage'],
                    'threat': size_info['threat']
                }
        
        # Try to match numeric sizes
        for pattern in self.patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    size_str = match.group(1)
                    size_inches = float(size_str)
                    
                    # Find closest object comparison
                    closest_object = self._find_closest_object(size_inches)
                    
                    if closest_object:
                        return {
                            'object': closest_object['name'],
                            'inches': size_inches,
                            'cm': round(size_inches * 2.54, 1),
                            'damage': closest_object['damage'],
                            'threat': closest_object['threat']
                        }
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _find_closest_object(self, inches: float) -> Optional[Dict]:
        """Find closest object comparison for a given size"""
        closest = None
        min_diff = float('inf')
        
        for size_name, size_info in self.hail_sizes.items():
            diff = abs(size_info['inches'] - inches)
            if diff < min_diff:
                min_diff = diff
                closest = {
                    'name': size_name.title(),
                    'inches': size_info['inches'],
                    'damage': size_info['damage'],
                    'threat': size_info['threat']
                }
        
        return closest
    
    def get_hail_announcement(self, text: str) -> Optional[str]:
        """
        Get broadcast-ready hail size announcement
        
        Args:
            text: Alert description
        
        Returns:
            Announcement text or None
        """
        hail_info = self.extract_hail_size(text)
        
        if not hail_info:
            return None
        
        object_name = hail_info['object']
        inches = hail_info['inches']
        damage = hail_info['damage']
        threat = hail_info['threat']
        
        # Build announcement based on threat level
        if threat in ['Catastrophic', 'Extreme']:
            announcement = f"{object_name} sized hail - {inches} inches. {damage}. Seek shelter immediately."
        elif threat == 'Severe':
            announcement = f"{object_name} sized hail - {inches} inches. {damage}. Take cover now."
        elif threat == 'Significant':
            announcement = f"{object_name} sized hail - {inches} inches. {damage}. Move vehicles to covered areas."
        else:
            announcement = f"{object_name} sized hail reported - {inches} inches."
        
        return announcement
    
    def enhance_alert_with_hail_info(self, alert_text: str) -> str:
        """
        Add hail size information to alert text
        
        Args:
            alert_text: Original alert announcement
        
        Returns:
            Enhanced announcement with hail details
        """
        hail_announcement = self.get_hail_announcement(alert_text)
        
        if hail_announcement:
            # Add hail info after main announcement
            return f"{alert_text} {hail_announcement}"
        
        return alert_text


# Singleton instance
_hail_translator = None

def get_hail_translator():
    """Get singleton hail translator"""
    global _hail_translator
    if _hail_translator is None:
        _hail_translator = HailTranslator()
    return _hail_translator


def extract_hail_info(text: str) -> Optional[Dict]:
    """Extract hail size information from text"""
    translator = get_hail_translator()
    return translator.extract_hail_size(text)


def get_hail_announcement(text: str) -> Optional[str]:
    """Get hail size announcement"""
    translator = get_hail_translator()
    return translator.get_hail_announcement(text)


def add_hail_info_to_alert(alert_text: str) -> str:
    """Add hail information to alert"""
    translator = get_hail_translator()
    return translator.enhance_alert_with_hail_info(alert_text)


if __name__ == '__main__':
    # Test the hail translator
    print("=" * 70)
    print("HAIL SIZE TRANSLATOR TEST")
    print("=" * 70)
    
    translator = HailTranslator()
    
    # Test cases
    test_alerts = [
        "Severe thunderstorm producing quarter size hail and 60 mph winds.",
        "Golf ball sized hail reported near Huntsville.",
        "2 inch diameter hail possible with this storm.",
        "Tennis ball size hail observed in Madison County.",
        "Pea size hail reported."
    ]
    
    print("\n1. Testing hail extraction:")
    print("-" * 70)
    for i, alert in enumerate(test_alerts, 1):
        print(f"\nAlert {i}: {alert}")
        hail_info = translator.extract_hail_size(alert)
        
        if hail_info:
            print(f"  Object: {hail_info['object']}")
            print(f"  Size: {hail_info['inches']} inches ({hail_info['cm']} cm)")
            print(f"  Threat: {hail_info['threat']}")
            print(f"  Damage: {hail_info['damage']}")
        else:
            print("  No hail size detected")
    
    print("\n2. Testing announcements:")
    print("-" * 70)
    for i, alert in enumerate(test_alerts, 1):
        announcement = translator.get_hail_announcement(alert)
        if announcement:
            print(f"\nAlert {i}: {announcement}")
    
    print("\n3. Testing alert enhancement:")
    print("-" * 70)
    sample_alert = "Severe Thunderstorm Warning for Madison County. Damaging winds and large hail."
    sample_with_hail = "Severe Thunderstorm Warning for Madison County. Golf ball sized hail and 60 mph winds."
    
    enhanced = translator.enhance_alert_with_hail_info(sample_with_hail)
    print(f"\nOriginal: {sample_with_hail}")
    print(f"Enhanced: {enhanced}")
    
    print("\n" + "=" * 70)
    print("✓ Hail translator working!")
    print("=" * 70)
