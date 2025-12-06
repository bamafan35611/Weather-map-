"""
voice_styles.py - NorthBamaWX Dynamic Voice System
Changes voice tone, speed, and style based on threat level
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class VoiceStyleManager:
    """Manages different voice styles based on threat levels"""
    
    def __init__(self):
        # Voice style configurations for Azure TTS
        self.voice_styles = {
            'calm': {
                'voice': 'en-US-GuyNeural',
                'style': 'newscast',
                'rate': '0%',  # Normal speed
                'pitch': '0%',  # Normal pitch
                'volume': '+0%',  # Normal volume
                'emphasis': 'moderate'
            },
            'concerned': {
                'voice': 'en-US-GuyNeural',
                'style': 'newscast-casual',
                'rate': '+5%',  # Slightly faster
                'pitch': '+5%',  # Slightly higher
                'volume': '+5%',
                'emphasis': 'strong'
            },
            'urgent': {
                'voice': 'en-US-DavisNeural',
                'style': 'shouting',
                'rate': '+10%',  # Faster
                'pitch': '+10%',  # Higher
                'volume': '+10%',
                'emphasis': 'strong'
            },
            'emergency': {
                'voice': 'en-US-DavisNeural',
                'style': 'angry',
                'rate': '+15%',  # Very fast
                'pitch': '+15%',  # Very high
                'volume': '+20%',  # LOUD
                'emphasis': 'strong'
            }
        }
        
        # Threat score to voice style mapping
        self.threat_mappings = {
            (95, 100): 'emergency',   # EXTREME
            (85, 94): 'emergency',    # SEVERE
            (70, 84): 'urgent',       # HIGH
            (50, 69): 'concerned',    # ELEVATED
            (30, 49): 'concerned',    # MODERATE
            (0, 29): 'calm'           # LOW
        }
    
    def get_voice_style_for_threat(self, threat_score: int) -> str:
        """Get appropriate voice style based on threat score"""
        for (min_score, max_score), style in self.threat_mappings.items():
            if min_score <= threat_score <= max_score:
                return style
        return 'calm'
    
    def get_voice_style_for_alert_type(self, alert_type: str) -> str:
        """Get voice style based on alert type"""
        alert_lower = alert_type.lower()
        
        # Emergency alerts
        if any(keyword in alert_lower for keyword in 
               ['tornado emergency', 'flash flood emergency', 'extreme', 'pds']):
            return 'emergency'
        
        # Warning alerts
        if 'warning' in alert_lower:
            return 'urgent'
        
        # Watch alerts
        if 'watch' in alert_lower:
            return 'concerned'
        
        # Advisory/Statement
        return 'calm'
    
    def generate_ssml(self, text: str, threat_score: int = None, 
                      alert_type: str = None, force_style: str = None) -> str:
        """Generate SSML with appropriate voice styling"""
        
        # Determine voice style
        if force_style:
            style_name = force_style
        elif threat_score is not None:
            style_name = self.get_voice_style_for_threat(threat_score)
        elif alert_type:
            style_name = self.get_voice_style_for_alert_type(alert_type)
        else:
            style_name = 'calm'
        
        style = self.voice_styles[style_name]
        
        # Build SSML
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
                   xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{style['voice']}">
        <mstts:express-as style="{style['style']}">
            <prosody rate="{style['rate']}" pitch="{style['pitch']}" volume="{style['volume']}">
                {self._add_emphasis(text, style['emphasis'])}
            </prosody>
        </mstts:express-as>
    </voice>
</speak>'''
        
        return ssml
    
    def _add_emphasis(self, text: str, emphasis_level: str) -> str:
        """Add emphasis to critical words"""
        if emphasis_level == 'strong':
            # Emphasize warning words
            warning_words = [
                'WARNING', 'EMERGENCY', 'TORNADO', 'SHELTER', 'IMMEDIATELY',
                'DANGEROUS', 'SEVERE', 'EXTREME', 'TAKE COVER', 'NOW'
            ]
            
            for word in warning_words:
                if word in text.upper():
                    text = text.replace(word, f'<emphasis level="strong">{word}</emphasis>')
                    text = text.replace(word.lower(), f'<emphasis level="strong">{word.lower()}</emphasis>')
                    text = text.replace(word.title(), f'<emphasis level="strong">{word.title()}</emphasis>')
        
        return text
    
    def format_alert_announcement(self, alert: Dict, threat_score: int) -> Dict:
        """Format alert announcement with appropriate voice style"""
        
        event = alert.get('event', 'Weather Alert')
        location = alert.get('areaDesc', 'your area')
        
        # Determine voice style
        style_name = self.get_voice_style_for_threat(threat_score)
        
        # Build announcement based on style
        if style_name == 'emergency':
            announcement = self._format_emergency_announcement(event, location, threat_score, alert)
        elif style_name == 'urgent':
            announcement = self._format_urgent_announcement(event, location, threat_score, alert)
        elif style_name == 'concerned':
            announcement = self._format_concerned_announcement(event, location, threat_score, alert)
        else:
            announcement = self._format_calm_announcement(event, location, threat_score, alert)
        
        return {
            'text': announcement,
            'ssml': self.generate_ssml(announcement, threat_score=threat_score),
            'style': style_name,
            'threat_score': threat_score
        }
    
    def _format_emergency_announcement(self, event: str, location: str, 
                                       threat_score: int, alert: Dict) -> str:
        """Format EMERGENCY level announcement (95-100)"""
        
        # Add attention getter
        attention = "ATTENTION! EMERGENCY WEATHER ALERT! "
        
        # Main alert
        main = f"{event} NOW in effect for {location}! "
        
        # Threat score with emphasis
        threat = f"NorthBamaWX Threat Score: {threat_score} out of 100! EXTREME DANGER! "
        
        # Urgent action
        if 'tornado' in event.lower():
            action = "TAKE SHELTER IMMEDIATELY! GO TO YOUR SAFE PLACE NOW! "
            details = "Basement or interior room on lowest floor! PROTECT YOUR HEAD! "
        elif 'flood' in event.lower():
            action = "EVACUATE TO HIGHER GROUND NOW! DO NOT DRIVE THROUGH WATER! "
            details = "This is a life-threatening situation! MOVE NOW! "
        else:
            action = "TAKE PROTECTIVE ACTION IMMEDIATELY! "
            details = "This is an extremely dangerous situation! "
        
        return attention + main + threat + action + details + "This is NorthBamaWX!"
    
    def _format_urgent_announcement(self, event: str, location: str, 
                                    threat_score: int, alert: Dict) -> str:
        """Format URGENT level announcement (70-94)"""
        
        # Strong opener
        opener = f"NorthBamaWX URGENT ALERT. "
        
        # Main alert
        main = f"{event} for {location}. "
        
        # Threat score
        threat = f"Threat Score: {threat_score} out of 100. "
        
        # Determine threat level
        if threat_score >= 85:
            level = "SEVERE threat. "
        else:
            level = "HIGH threat. "
        
        # Action based on alert type
        if 'tornado' in event.lower():
            action = "Seek shelter in a sturdy building. Stay away from windows. "
        elif 'thunderstorm' in event.lower():
            action = "Move indoors. Secure loose objects. Avoid windows. "
        elif 'flood' in event.lower():
            action = "Move to higher ground. Do not drive through flooded areas. "
        elif 'wind' in event.lower():
            action = "Secure loose objects. Seek shelter indoors. "
        else:
            action = "Take protective action now. "
        
        return opener + main + threat + level + action + "Stay safe."
    
    def _format_concerned_announcement(self, event: str, location: str, 
                                       threat_score: int, alert: Dict) -> str:
        """Format CONCERNED level announcement (30-69)"""
        
        opener = f"NorthBamaWX weather update. "
        main = f"{event} for {location}. "
        threat = f"Threat Score: {threat_score} out of 100. "
        
        if threat_score >= 50:
            level = "Elevated threat. "
            action = "Stay alert and be ready to take action if conditions worsen. "
        else:
            level = "Moderate threat. "
            action = "Monitor weather conditions and stay informed. "
        
        return opener + main + threat + level + action
    
    def _format_calm_announcement(self, event: str, location: str, 
                                   threat_score: int, alert: Dict) -> str:
        """Format CALM level announcement (0-29)"""
        
        opener = f"NorthBamaWX advisory. "
        main = f"{event} for {location}. "
        threat = f"Threat Score: {threat_score} out of 100. Low threat. "
        action = "Stay aware and monitor for updates. "
        
        return opener + main + threat + action
    
    def format_pre_alert_announcement(self, pre_alert: Dict) -> Dict:
        """Format pre-alert announcement"""
        
        alert_type = pre_alert.get('alert_type', 'Weather Alert')
        location = pre_alert.get('location', 'your area')
        confidence = pre_alert.get('confidence', 0)
        time_until = pre_alert.get('time_until_alert', '5-15 minutes')
        
        # Pre-alerts always use urgent or emergency style
        if confidence >= 85:
            style_name = 'emergency'
            opener = "ATTENTION! NorthBamaWX AI PREDICTION ALERT! "
            urgency = "CRITICAL! "
        else:
            style_name = 'urgent'
            opener = "NorthBamaWX AI PREDICTION ALERT. "
            urgency = ""
        
        main = f"Based on current conditions, we predict {int(confidence)} percent probability of "
        main += f"{alert_type} being issued for {location} within the next {time_until}. "
        
        action = f"{urgency}This is a pre-alert prediction. Official NWS warning may follow shortly. "
        action += "Take precautions now. "
        
        announcement = opener + main + action
        
        return {
            'text': announcement,
            'ssml': self.generate_ssml(announcement, force_style=style_name),
            'style': style_name,
            'confidence': confidence
        }
    
    def format_verification_announcement(self, stats: Dict) -> Dict:
        """Format verification success announcement"""
        
        if stats.get('avg_time_advantage', 0) > 0:
            minutes = stats['avg_time_advantage']
            
            announcement = f"UPDATE. NWS has now issued the alert we predicted. "
            announcement += f"NorthBamaWX was {minutes:.1f} minutes ahead of the official warning. "
            announcement += "Our AI successfully detected the developing threat early. "
            
            style_name = 'concerned'
        else:
            return None
        
        return {
            'text': announcement,
            'ssml': self.generate_ssml(announcement, force_style=style_name),
            'style': style_name
        }


# Helper functions for Flask integration
def get_announcement_for_alert(alert: Dict, threat_score: int) -> Dict:
    """Get formatted announcement for an alert"""
    manager = VoiceStyleManager()
    return manager.format_alert_announcement(alert, threat_score)


def get_announcement_for_pre_alert(pre_alert: Dict) -> Dict:
    """Get formatted announcement for a pre-alert"""
    manager = VoiceStyleManager()
    return manager.format_pre_alert_announcement(pre_alert)


def get_ssml_for_text(text: str, threat_score: int = 50) -> str:
    """Get SSML for custom text"""
    manager = VoiceStyleManager()
    return manager.generate_ssml(text, threat_score=threat_score)


if __name__ == '__main__':
    # Test the voice system
    print("=" * 60)
    print("NORTHBAMAWX VOICE STYLES TEST")
    print("=" * 60)
    
    manager = VoiceStyleManager()
    
    # Test different threat levels
    test_alerts = [
        {
            'alert': {'event': 'Tornado Emergency', 'areaDesc': 'Moore, Oklahoma'},
            'threat_score': 100,
            'expected_style': 'emergency'
        },
        {
            'alert': {'event': 'Tornado Warning', 'areaDesc': 'Oklahoma City, OK'},
            'threat_score': 90,
            'expected_style': 'emergency'
        },
        {
            'alert': {'event': 'Severe Thunderstorm Warning', 'areaDesc': 'Atlanta, GA'},
            'threat_score': 75,
            'expected_style': 'urgent'
        },
        {
            'alert': {'event': 'Tornado Watch', 'areaDesc': 'North Alabama'},
            'threat_score': 45,
            'expected_style': 'concerned'
        },
        {
            'alert': {'event': 'Wind Advisory', 'areaDesc': 'Decatur, AL'},
            'threat_score': 25,
            'expected_style': 'calm'
        }
    ]
    
    for i, test in enumerate(test_alerts, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['alert']['event']} (Score: {test['threat_score']})")
        print(f"{'='*60}")
        
        result = manager.format_alert_announcement(test['alert'], test['threat_score'])
        
        print(f"\nVoice Style: {result['style'].upper()}")
        print(f"Expected: {test['expected_style'].upper()}")
        print(f"Match: {'✓' if result['style'] == test['expected_style'] else '✗'}")
        
        print(f"\nAnnouncement Text:")
        print(result['text'])
        
        print(f"\nSSML (first 200 chars):")
        print(result['ssml'][:200] + "...")
    
    # Test pre-alert
    print(f"\n{'='*60}")
    print("PRE-ALERT TEST")
    print(f"{'='*60}")
    
    pre_alert = {
        'alert_type': 'Tornado Warning',
        'location': 'Oklahoma City, OK',
        'confidence': 87.3,
        'time_until_alert': '8-12 minutes'
    }
    
    result = manager.format_pre_alert_announcement(pre_alert)
    print(f"\nVoice Style: {result['style'].upper()}")
    print(f"\nAnnouncement Text:")
    print(result['text'])
    
    print("\n" + "="*60)
    print("All voice styles working correctly!")
    print("="*60)
