"""
alert_processing_enhanced.py - NorthBamaWX Enhanced Alert Processing
Multi-level prioritization, duplicate detection, and intelligent alert ordering
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class EnhancedAlertProcessor:
    """Enhanced alert processing with sophisticated prioritization"""
    
    # Priority levels
    PRIORITY_CRITICAL = 100
    PRIORITY_HIGH = 75
    PRIORITY_MEDIUM = 50
    PRIORITY_LOW = 25
    PRIORITY_INFO = 10
    
    def __init__(self):
        # Track alert fingerprints for duplicate detection
        self.seen_alerts = {}
        self.max_fingerprint_age = 3600  # 1 hour
        
    def process_alerts(self, raw_alerts: List[Dict]) -> Dict:
        """
        Process and prioritize alerts
        
        Args:
            raw_alerts: Raw alert data from NWS
            
        Returns:
            Processed alert dictionary
        """
        try:
            result = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': [],
                'duplicates_removed': 0,
                'total_processed': 0,
                'highest_priority': None
            }
            
            # Clean old fingerprints
            self._cleanup_fingerprints()
            
            # Process each alert
            for alert in raw_alerts:
                # Check for duplicate
                if self._is_duplicate(alert):
                    result['duplicates_removed'] += 1
                    continue
                
                # Calculate priority
                priority = self._calculate_priority(alert)
                alert['calculated_priority'] = priority
                
                # Categorize by priority
                if priority >= self.PRIORITY_CRITICAL:
                    result['critical'].append(alert)
                elif priority >= self.PRIORITY_HIGH:
                    result['high'].append(alert)
                elif priority >= self.PRIORITY_MEDIUM:
                    result['medium'].append(alert)
                elif priority >= self.PRIORITY_LOW:
                    result['low'].append(alert)
                else:
                    result['info'].append(alert)
                
                result['total_processed'] += 1
            
            # Sort each category by priority (highest first)
            for category in ['critical', 'high', 'medium', 'low', 'info']:
                result[category].sort(
                    key=lambda x: x.get('calculated_priority', 0),
                    reverse=True
                )
            
            # Determine highest priority level
            if result['critical']:
                result['highest_priority'] = 'critical'
            elif result['high']:
                result['highest_priority'] = 'high'
            elif result['medium']:
                result['highest_priority'] = 'medium'
            elif result['low']:
                result['highest_priority'] = 'low'
            else:
                result['highest_priority'] = 'info'
            
            logger.info(f"Processed {result['total_processed']} alerts, removed {result['duplicates_removed']} duplicates")
            logger.info(f"Priority breakdown - Critical: {len(result['critical'])}, High: {len(result['high'])}, Medium: {len(result['medium'])}, Low: {len(result['low'])}, Info: {len(result['info'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
            return {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': [],
                'duplicates_removed': 0,
                'total_processed': 0,
                'highest_priority': None
            }
    
    def _calculate_priority(self, alert: Dict) -> int:
        """
        Calculate alert priority using multiple factors
        
        Returns priority score (0-100+)
        """
        try:
            event = alert.get('event', '').lower()
            severity = alert.get('severity', '').lower()
            urgency = alert.get('urgency', '').lower()
            certainty = alert.get('certainty', '').lower()
            
            priority = 0
            
            # Base priority by event type
            if 'tornado' in event and 'warning' in event:
                priority = self.PRIORITY_CRITICAL  # 100
            elif 'tornado' in event and 'emergency' in event:
                priority = self.PRIORITY_CRITICAL + 10  # 110 (highest possible)
            elif 'severe thunderstorm' in event and 'warning' in event:
                priority = self.PRIORITY_HIGH  # 75
            elif 'flash flood' in event and 'warning' in event:
                priority = self.PRIORITY_HIGH  # 75
            elif 'tornado' in event and 'watch' in event:
                priority = self.PRIORITY_MEDIUM  # 50
            elif 'severe thunderstorm' in event and 'watch' in event:
                priority = self.PRIORITY_MEDIUM  # 50
            elif 'warning' in event:
                priority = self.PRIORITY_MEDIUM  # 50
            elif 'watch' in event:
                priority = self.PRIORITY_LOW  # 25
            elif 'advisory' in event:
                priority = self.PRIORITY_INFO  # 10
            else:
                priority = self.PRIORITY_INFO  # 10
            
            # Boost priority based on NWS severity
            if severity == 'extreme':
                priority += 15
            elif severity == 'severe':
                priority += 10
            elif severity == 'moderate':
                priority += 5
            
            # Boost priority based on urgency
            if urgency == 'immediate':
                priority += 10
            elif urgency == 'expected':
                priority += 5
            
            # Boost priority based on certainty
            if certainty == 'observed':
                priority += 10
            elif certainty == 'likely':
                priority += 5
            
            # Check for special keywords in description
            description = alert.get('description', '').lower()
            
            # Tornado on ground (highest boost)
            if 'tornado on the ground' in description or 'tornado on ground' in description:
                priority += 20
            
            # Confirmed tornado
            if 'confirmed tornado' in description:
                priority += 15
            
            # Particularly dangerous situation
            if 'particularly dangerous situation' in description:
                priority += 15
            
            # Large hail
            if 'baseball' in description or 'softball' in description:
                priority += 8
            elif 'golf ball' in description:
                priority += 5
            
            # Destructive winds
            if 'destructive' in description and 'wind' in description:
                priority += 10
            elif '70 mph' in description or '80 mph' in description or '90 mph' in description:
                priority += 8
            
            # Flash flooding
            if 'flash flood emergency' in description:
                priority += 15
            elif 'life threatening' in description and 'flood' in description:
                priority += 10
            
            return priority
            
        except Exception as e:
            logger.error(f"Error calculating priority: {e}")
            return self.PRIORITY_INFO
    
    def _is_duplicate(self, alert: Dict) -> bool:
        """
        Check if alert is a duplicate using fingerprinting
        
        Returns True if duplicate, False if unique
        """
        try:
            # Create fingerprint from key alert attributes
            fingerprint = self._create_fingerprint(alert)
            
            # Check if we've seen this fingerprint recently
            if fingerprint in self.seen_alerts:
                last_seen = self.seen_alerts[fingerprint]
                age = (datetime.utcnow() - last_seen).total_seconds()
                
                # If seen within last hour, it's a duplicate
                if age < self.max_fingerprint_age:
                    return True
            
            # Not a duplicate, record it
            self.seen_alerts[fingerprint] = datetime.utcnow()
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return False
    
    def _create_fingerprint(self, alert: Dict) -> str:
        """Create unique fingerprint for alert"""
        try:
            # Use event type + area + onset time
            event = alert.get('event', '')
            area = alert.get('areaDesc', '')
            onset = alert.get('onset', alert.get('sent', ''))
            
            # Create hash
            fingerprint_str = f"{event}|{area}|{onset}"
            return hashlib.md5(fingerprint_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error creating fingerprint: {e}")
            return ""
    
    def _cleanup_fingerprints(self):
        """Remove old fingerprints from tracking"""
        try:
            now = datetime.utcnow()
            expired = []
            
            for fingerprint, timestamp in self.seen_alerts.items():
                age = (now - timestamp).total_seconds()
                if age > self.max_fingerprint_age:
                    expired.append(fingerprint)
            
            for fingerprint in expired:
                del self.seen_alerts[fingerprint]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} old alert fingerprints")
                
        except Exception as e:
            logger.error(f"Error cleaning fingerprints: {e}")
    
    def get_top_alerts(self, processed: Dict, max_count: int = 10) -> List[Dict]:
        """
        Get top N alerts across all priority levels
        
        Args:
            processed: Processed alert dictionary from process_alerts()
            max_count: Maximum number of alerts to return
            
        Returns:
            List of top alerts ordered by priority
        """
        top_alerts = []
        
        # Add alerts from each priority level
        for category in ['critical', 'high', 'medium', 'low', 'info']:
            top_alerts.extend(processed[category])
            
            # Stop if we have enough
            if len(top_alerts) >= max_count:
                break
        
        # Trim to max count
        return top_alerts[:max_count]
    
    def get_priority_summary(self, processed: Dict) -> Optional[str]:
        """
        Get a summary of alert priorities for announcement
        
        Args:
            processed: Processed alert dictionary
            
        Returns:
            Priority summary text or None
        """
        highest = processed.get('highest_priority')
        
        if not highest or highest == 'info':
            return None
        
        critical_count = len(processed.get('critical', []))
        high_count = len(processed.get('high', []))
        
        parts = []
        
        if critical_count > 0:
            if critical_count == 1:
                parts.append("One critical weather alert")
            else:
                parts.append(f"{critical_count} critical weather alerts")
        
        if high_count > 0:
            if high_count == 1:
                if parts:
                    parts.append("and one high priority alert")
                else:
                    parts.append("One high priority weather alert")
            else:
                if parts:
                    parts.append(f"and {high_count} high priority alerts")
                else:
                    parts.append(f"{high_count} high priority weather alerts")
        
        if parts:
            return " ".join(parts) + " in effect."
        
        return None


# Singleton instance
_alert_processor = None

def get_alert_processor() -> EnhancedAlertProcessor:
    """Get singleton EnhancedAlertProcessor instance"""
    global _alert_processor
    if _alert_processor is None:
        _alert_processor = EnhancedAlertProcessor()
    return _alert_processor


def process_and_prioritize_alerts(raw_alerts: List[Dict]) -> Dict:
    """
    Convenience function to process and prioritize alerts
    
    Args:
        raw_alerts: Raw alert data from NWS
        
    Returns:
        Processed alert dictionary
    """
    processor = get_alert_processor()
    return processor.process_alerts(raw_alerts)
