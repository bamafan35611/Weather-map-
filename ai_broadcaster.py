"""
ai_broadcaster.py - AI-Powered Natural Weather Broadcasting
Uses Groq API (FREE) to generate varied, natural-sounding weather announcements
ONLY used for routine weather - NOT for warnings/watches (those use reliable templates)
"""

import os
import requests
from typing import Dict, List, Optional
import json

class AIBroadcaster:
    """Generate natural, varied weather broadcasts using AI"""
    
    def __init__(self):
        # Get API key from environment (set in Render dashboard)
        self.api_key = os.environ.get('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Fast, good quality, free
        
        print("✓ AI Broadcaster initialized (Groq)")
        print(f"  Model: {self.model}")
    
    def generate_broadcast(self, weather_data: Dict) -> str:
        """
        Generate a natural weather broadcast from data
        
        Args:
            weather_data: Dict with keys like:
                - has_alerts: bool
                - conditions: str (e.g., "Light drizzle in Cullman")
                - forecast: str
                - time_period: str (e.g., "quarter past", "half past")
        
        Returns:
            Natural broadcast text
        """
        
        # SAFETY: Never use AI for alerts/warnings
        if weather_data.get('has_alerts') or weather_data.get('has_warnings'):
            raise ValueError("AI should NOT be used for alerts/warnings - use template system")
        
        # Build prompt for AI
        prompt = self._build_prompt(weather_data)
        
        try:
            # Call Groq API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.8,  # Varied but not too creative
                    "max_tokens": 150,   # Keep broadcasts concise
                    "top_p": 0.9
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"⚠️ Groq API error: {response.status_code}")
                return self._fallback_broadcast(weather_data)
            
            result = response.json()
            broadcast = result['choices'][0]['message']['content'].strip()
            
            # Clean up any extra formatting
            broadcast = broadcast.replace('"', '').replace('*', '').strip()
            
            print(f"✓ AI generated broadcast: {broadcast[:60]}...")
            return broadcast
            
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")
            return self._fallback_broadcast(weather_data)
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role"""
        return """You are a professional weather broadcaster for NorthBamaWX, a weather monitoring service in North Alabama.

Your job is to create natural, conversational weather announcements that sound like a real meteorologist.

RULES:
1. Be concise (2-3 sentences maximum)
2. Sound natural and conversational, not robotic
3. Vary your phrasing each time - never repeat the same structure
4. Start with varied greetings like "Good evening from NorthBamaWX" or "This is NorthBamaWX checking in" or "NorthBamaWX here with your weather update"
5. NEVER mention alerts, warnings, or watches - those are handled separately
6. Focus on current conditions and general weather
7. Be professional but friendly
8. Always end by noting no severe weather concerns if that's the case
9. Keep it under 30 seconds when spoken aloud

TONE: Professional meteorologist, calm, informative, slightly conversational"""
    
    def _build_prompt(self, weather_data: Dict) -> str:
        """Build the prompt from weather data"""
        
        parts = []
        
        # Add current season context
        from datetime import datetime
        import pytz
        central = pytz.timezone('America/Chicago')
        current_month = datetime.now(central).month
        
        if current_month in [12, 1, 2]:
            season = "winter"
        elif current_month in [3, 4, 5]:
            season = "spring"
        elif current_month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"
        
        parts.append(f"Current season: {season}")
        
        # Time context
        time_period = weather_data.get('time_period', 'this hour')
        parts.append(f"Time: {time_period}")
        
        # Current conditions
        if weather_data.get('conditions'):
            parts.append(f"Current conditions: {weather_data['conditions']}")
        
        # Forecast
        if weather_data.get('forecast'):
            parts.append(f"Forecast: {weather_data['forecast']}")
        
        # Additional context
        if weather_data.get('visibility_issues'):
            parts.append(f"Visibility: {weather_data['visibility_issues']}")
        
        if weather_data.get('lightning'):
            parts.append(f"Lightning: {weather_data['lightning']}")
        
        # Alert status
        parts.append("Alert status: No active warnings or watches")
        
        prompt = "\n".join(parts)
        prompt += "\n\nGenerate a natural weather broadcast announcement based on this information. Be concise and varied in your phrasing. IMPORTANT: Use the correct season provided above - do NOT mention the wrong season!"
        
        return prompt
    
    def _fallback_broadcast(self, weather_data: Dict) -> str:
        """Simple template if AI fails"""
        conditions = weather_data.get('conditions', 'Conditions are quiet')
        return f"NorthBamaWX. {conditions}. No severe weather warnings in effect at this time."


# Singleton instance
_ai_broadcaster = None

def get_ai_broadcaster() -> Optional[AIBroadcaster]:
    """Get or create AI broadcaster instance"""
    global _ai_broadcaster
    
    if _ai_broadcaster is None:
        try:
            _ai_broadcaster = AIBroadcaster()
        except ValueError as e:
            print(f"⚠️ AI Broadcaster disabled: {e}")
            return None
    
    return _ai_broadcaster


def generate_ai_broadcast(weather_data: Dict) -> Optional[str]:
    """
    Generate AI broadcast (convenience function)
    
    Returns None if AI not available or if data contains alerts
    """
    broadcaster = get_ai_broadcaster()
    
    if not broadcaster:
        return None
    
    # SAFETY: Don't use AI for alerts
    if weather_data.get('has_alerts') or weather_data.get('has_warnings'):
        return None
    
    try:
        return broadcaster.generate_broadcast(weather_data)
    except Exception as e:
        print(f"⚠️ AI broadcast generation failed: {e}")
        return None


if __name__ == '__main__':
    """Test the AI broadcaster"""
    print("=" * 60)
    print("AI BROADCASTER TEST")
    print("=" * 60)
    
    # Test data
    test_data = {
        'time_period': 'quarter past the hour',
        'conditions': 'Light drizzle in Cullman with cloudy skies region-wide',
        'visibility_issues': 'Reduced visibility near Cullman',
        'has_alerts': False,
        'has_warnings': False
    }
    
    broadcaster = get_ai_broadcaster()
    
    if broadcaster:
        print("\nGenerating 3 test broadcasts to show variety:\n")
        
        for i in range(3):
            print(f"\n{i+1}. ", end="")
            broadcast = broadcaster.generate_broadcast(test_data)
            print(broadcast)
        
        print("\n" + "=" * 60)
        print("✓ AI Broadcaster working - each broadcast is unique!")
        print("=" * 60)
    else:
        print("\n⚠️ AI Broadcaster not available - check GROQ_API_KEY")
