"""
severity_scorer.py - NorthBamaWX Threat Scoring System
Rates every weather alert on a 0-100 scale for easy understanding
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SeverityScorer:
    """Calculate threat scores for weather alerts"""
    
    def __init__(self):
        # Base severity scores by alert type
        self.base_scores = {
            'tornado emergency': 100,
            'pds tornado warning': 98,
            'confirmed tornado warning': 95,
            'tornado warning': 90,
            'particularly dangerous situation': 95,
            'destructive': 92,
            'considerable': 85,
            'severe thunderstorm warning': 75,
            'flash flood emergency': 95,
            'flash flood warning': 80,
            'hurricane warning': 85,
            'tsunami warning': 98,
            'earthquake warning': 95,
            'blizzard warning': 70,
            'ice storm warning': 75,
            'high wind warning': 65,
            'tornado watch': 60,  # 🆕 RAISED from 45 - Important to announce!
            'severe thunderstorm watch': 55,  # 🆕 RAISED from 40
            'wind advisory': 45,  # 🆕 ADDED - Should be announced!
            'dense fog advisory': 40,
            'winter weather advisory': 42,
            'flood advisory': 38,
            'flash flood watch': 35,
            'winter storm warning': 50,
            'snow squall warning': 60,
            'special marine warning': 55,
            'hurricane watch': 50,
            'tsunami watch': 60,
        }
        
        # Severity level multipliers
        self.severity_multipliers = {
            'extreme': 1.15,
            'severe': 1.10,
            'moderate': 1.0,
            'minor': 0.85,
            'unknown': 1.0
        }
        
        # Urgency multipliers
        self.urgency_multipliers = {
            'immediate': 1.15,
            'expected': 1.05,
            'future': 0.95,
            'past': 0.7,
            'unknown': 1.0
        }
        
        # Time of day impact (nighttime is more dangerous)
        self.time_of_day_bonus = {
            'night': 5,  # 9 PM - 6 AM
            'evening': 3,  # 6 PM - 9 PM
            'day': 0
        }
    
    def calculate_threat_score(self, alert: Dict) -> Dict:
        """Calculate comprehensive threat score for an alert"""
        
        try:
            event = (alert.get('event') or '').lower()
            severity = (alert.get('severity') or 'unknown').lower()
            urgency = (alert.get('urgency') or 'unknown').lower()
            description = (alert.get('description') or '').lower()
            
            # Start with base score
            base_score = self._get_base_score(event)
            
            # Apply severity multiplier
            severity_mult = self.severity_multipliers.get(severity, 1.0)
            
            # Apply urgency multiplier
            urgency_mult = self.urgency_multipliers.get(urgency, 1.0)
            
            # Calculate initial score
            score = base_score * severity_mult * urgency_mult
            
            # Add special condition bonuses
            score += self._check_special_conditions(event, description)
            
            # Add time of day bonus
            score += self._get_time_of_day_bonus()
            
            # Add populated area bonus
            score += self._check_populated_area(alert)
            
            # Add movement/speed bonuses
            score += self._check_storm_characteristics(description)
            
            # Cap at 100
            final_score = min(int(score), 100)
            
            # Determine threat level
            threat_level = self._get_threat_level(final_score)
            threat_color = self._get_threat_color(final_score)
            
            # Get action recommendation
            action = self._get_recommended_action(final_score, event)
            
            return {
                'score': final_score,
                'threat_level': threat_level,
                'color': threat_color,
                'action': action,
                'components': {
                    'base_score': int(base_score),
                    'severity_impact': int(base_score * (severity_mult - 1)),
                    'urgency_impact': int(base_score * (urgency_mult - 1)),
                    'special_conditions': int(self._check_special_conditions(event, description)),
                    'time_factor': self._get_time_of_day_bonus(),
                    'populated_area': self._check_populated_area(alert),
                    'storm_characteristics': self._check_storm_characteristics(description)
                },
                'severity': severity,
                'urgency': urgency
            }
            
        except Exception as e:
            logger.error(f"Error calculating threat score: {e}")
            return {
                'score': 50,
                'threat_level': 'MODERATE',
                'color': '#FFA500',
                'action': 'Monitor conditions',
                'components': {},
                'severity': 'unknown',
                'urgency': 'unknown'
            }
    
    def _get_base_score(self, event: str) -> float:
        """Get base score for alert type"""
        
        # Check for exact matches first
        for alert_type, score in self.base_scores.items():
            if alert_type in event:
                return float(score)
        
        # Default scores for common terms
        if 'warning' in event:
            return 70.0
        elif 'watch' in event:
            return 40.0
        elif 'advisory' in event:
            return 30.0
        else:
            return 50.0
    
    def _check_special_conditions(self, event: str, description: str) -> int:
        """Check for special high-threat conditions"""
        bonus = 0
        
        # Keywords that increase threat
        high_threat_keywords = {
            'confirmed': 5,
            'observed': 5,
            'radar indicated': 3,
            'debris': 8,
            'large and extremely dangerous': 10,
            'life-threatening': 8,
            'catastrophic': 10,
            'devastating': 8,
            'unsurvivable': 10,
            'violent': 7,
            'destructive': 6,
            'considerable': 5,
            'baseball': 5,
            'softball': 6,
            'grapefruit': 7,
            'gorilla hail': 8,
            'tornado emergency': 10,
            'pds': 8,
            'ground stop': 6,
            'total destruction': 10,
            'wedge tornado': 8,
            'multiple vortex': 6
        }
        
        combined_text = f"{event} {description}".lower()
        
        for keyword, points in high_threat_keywords.items():
            if keyword in combined_text:
                bonus += points
        
        return min(bonus, 15)  # Cap special condition bonus
    
    def _get_time_of_day_bonus(self) -> int:
        """Add bonus for nighttime severe weather"""
        hour = datetime.now().hour
        
        if 21 <= hour or hour < 6:  # 9 PM - 6 AM
            return self.time_of_day_bonus['night']
        elif 18 <= hour < 21:  # 6 PM - 9 PM
            return self.time_of_day_bonus['evening']
        else:
            return self.time_of_day_bonus['day']
    
    def _check_populated_area(self, alert: Dict) -> int:
        """Add bonus if alert affects populated area"""
        area_desc = (alert.get('areaDesc') or '').lower()
        
        # Major cities (more impact)
        major_cities = [
            'oklahoma city', 'nashville', 'atlanta', 'dallas', 'fort worth',
            'houston', 'chicago', 'memphis', 'birmingham', 'huntsville',
            'mobile', 'montgomery', 'little rock', 'jackson', 'new orleans',
            'miami', 'tampa', 'orlando', 'jacksonville', 'charlotte',
            'raleigh', 'richmond', 'washington', 'baltimore', 'philadelphia',
            'new york', 'boston', 'detroit', 'cleveland', 'pittsburgh',
            'cincinnati', 'indianapolis', 'milwaukee', 'minneapolis', 'st. louis',
            'kansas city', 'omaha', 'des moines', 'denver', 'phoenix',
            'las vegas', 'los angeles', 'san diego', 'san francisco', 'seattle',
            'portland', 'salt lake city'
        ]
        
        for city in major_cities:
            if city in area_desc:
                return 5
        
        # Medium cities
        if any(word in area_desc for word in ['city', 'county', 'metro', 'urban']):
            return 2
        
        return 0
    
    def _check_storm_characteristics(self, description: str) -> int:
        """Check storm movement and characteristics"""
        bonus = 0
        description = description.lower()
        
        # Fast-moving storms are more dangerous
        if 'rapidly moving' in description or 'fast moving' in description:
            bonus += 3
        
        # Strong rotation
        if 'strong rotation' in description or 'intense rotation' in description:
            bonus += 4
        
        # Multiple threats
        threats = ['tornado', 'hail', 'wind', 'flood']
        threat_count = sum(1 for threat in threats if threat in description)
        if threat_count >= 2:
            bonus += 2 * threat_count
        
        # Extreme wind speeds
        if '80 mph' in description or '90 mph' in description or '100 mph' in description:
            bonus += 5
        
        return min(bonus, 10)  # Cap storm characteristic bonus
    
    def _get_threat_level(self, score: int) -> str:
        """Convert score to threat level"""
        if score >= 95:
            return 'EXTREME'
        elif score >= 85:
            return 'SEVERE'
        elif score >= 70:
            return 'HIGH'
        elif score >= 50:
            return 'ELEVATED'
        elif score >= 30:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def _get_threat_color(self, score: int) -> str:
        """Get color code for threat level"""
        if score >= 95:
            return '#FF00FF'  # Magenta - EXTREME
        elif score >= 85:
            return '#FF0000'  # Red - SEVERE
        elif score >= 70:
            return '#FF4500'  # Orange-Red - HIGH
        elif score >= 50:
            return '#FFA500'  # Orange - ELEVATED
        elif score >= 30:
            return '#FFFF00'  # Yellow - MODERATE
        else:
            return '#00FF00'  # Green - LOW
    
    def _get_recommended_action(self, score: int, event: str) -> str:
        """Get recommended action based on score"""
        
        if score >= 95:
            if 'tornado' in event.lower():
                return 'TAKE SHELTER IMMEDIATELY - Go to lowest floor, interior room, cover head'
            elif 'tsunami' in event.lower():
                return 'EVACUATE TO HIGH GROUND IMMEDIATELY - Move inland now'
            elif 'flood' in event.lower():
                return 'MOVE TO HIGHER GROUND IMMEDIATELY - Do not drive through water'
            else:
                return 'TAKE IMMEDIATE PROTECTIVE ACTION - This is life-threatening'
        
        elif score >= 85:
            if 'tornado' in event.lower():
                return 'Seek shelter in sturdy building - Stay away from windows'
            elif 'wind' in event.lower() or 'thunderstorm' in event.lower():
                return 'Seek shelter indoors - Secure loose objects, avoid windows'
            else:
                return 'Take protective action now - Situation is dangerous'
        
        elif score >= 70:
            return 'Be prepared to take action - Monitor conditions closely'
        
        elif score >= 50:
            return 'Stay alert - Be ready to act if conditions worsen'
        
        elif score >= 30:
            return 'Monitor weather - Stay informed of changing conditions'
        
        else:
            return 'Stay aware - Low threat but watch for updates'
    
    def batch_score_alerts(self, alerts: list) -> list:
        """Score multiple alerts at once"""
        scored_alerts = []
        
        for alert in alerts:
            score_data = self.calculate_threat_score(alert)
            
            # Add score data to alert
            alert_with_score = alert.copy()
            alert_with_score['threat_score'] = score_data
            
            scored_alerts.append(alert_with_score)
        
        # Sort by score (highest first)
        scored_alerts.sort(key=lambda x: x['threat_score']['score'], reverse=True)
        
        return scored_alerts
    
    def get_highest_threat(self, alerts: list) -> Optional[Dict]:
        """Get the highest threat alert"""
        if not alerts:
            return None
        
        scored = self.batch_score_alerts(alerts)
        return scored[0] if scored else None
    
    def format_threat_announcement(self, alert: Dict, score_data: Dict) -> str:
        """Format a spoken announcement with threat score"""
        
        event = alert.get('event', 'Weather Alert')
        area = alert.get('areaDesc', 'Unknown area')
        score = score_data['score']
        threat_level = score_data['threat_level']
        action = score_data['action']
        
        # Build announcement
        announcement = f"{event} for {area}. "
        announcement += f"NorthBamaWX Threat Score: {score} out of 100. "
        announcement += f"Threat level: {threat_level}. "
        announcement += f"{action}"
        
        return announcement


# API helper functions
def score_alert(alert: Dict) -> Dict:
    """Score a single alert"""
    scorer = SeverityScorer()
    return scorer.calculate_threat_score(alert)


def score_all_alerts(alerts: list) -> list:
    """Score and sort all alerts"""
    scorer = SeverityScorer()
    return scorer.batch_score_alerts(alerts)


def get_threat_announcement(alert: Dict) -> str:
    """Get formatted announcement for alert"""
    scorer = SeverityScorer()
    score_data = scorer.calculate_threat_score(alert)
    return scorer.format_threat_announcement(alert, score_data)


if __name__ == '__main__':
    # Test the scoring system
    print("=" * 60)
    print("NORTHBAMAWX THREAT SCORING SYSTEM TEST")
    print("=" * 60)
    
    # Test alerts
    test_alerts = [
        {
            'event': 'Tornado Warning',
            'severity': 'Extreme',
            'urgency': 'Immediate',
            'areaDesc': 'Oklahoma City, OK',
            'description': 'Confirmed large and extremely dangerous tornado observed. This is a life-threatening situation.'
        },
        {
            'event': 'Severe Thunderstorm Warning',
            'severity': 'Severe',
            'urgency': 'Immediate',
            'areaDesc': 'Decatur, AL',
            'description': 'Baseball size hail and 70 mph winds expected.'
        },
        {
            'event': 'Flash Flood Watch',
            'severity': 'Moderate',
            'urgency': 'Expected',
            'areaDesc': 'North Alabama',
            'description': 'Heavy rainfall possible later today.'
        }
    ]
    
    scorer = SeverityScorer()
    
    print("\n📊 SCORING TEST ALERTS:\n")
    
    for i, alert in enumerate(test_alerts, 1):
        score_data = scorer.calculate_threat_score(alert)
        
        print(f"Alert {i}: {alert['event']}")
        print(f"  Location: {alert['areaDesc']}")
        print(f"  Threat Score: {score_data['score']}/100")
        print(f"  Threat Level: {score_data['threat_level']}")
        print(f"  Color: {score_data['color']}")
        print(f"  Action: {score_data['action']}")
        print(f"  Components:")
        for key, value in score_data['components'].items():
            print(f"    - {key}: {value}")
        print()
    
    # Test announcement
    print("🎙️ SAMPLE ANNOUNCEMENT:")
    print()
    announcement = scorer.format_threat_announcement(test_alerts[0], 
                                                      scorer.calculate_threat_score(test_alerts[0]))
    print(announcement)
