"""
historical_comparisons.py - NorthBamaWX Historical Weather Comparisons
Compares current weather events to historical data for context
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class HistoricalComparisons:
    """Tracks and compares current weather to historical patterns"""
    
    def __init__(self, db_path: str = "data/weather_history.db"):
        """
        Initialize historical comparisons system
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for historical tracking"""
        try:
            # Ensure data directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Alert history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    county TEXT NOT NULL,
                    state TEXT NOT NULL,
                    issued_time TIMESTAMP NOT NULL,
                    expired_time TIMESTAMP,
                    severity TEXT,
                    urgency TEXT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    day_of_year INTEGER NOT NULL
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON alert_history(event_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_year_month 
                ON alert_history(year, month)
            ''')
            
            # Temperature extremes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temperature_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    date DATE NOT NULL,
                    high_temp REAL,
                    low_temp REAL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Historical database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing historical database: {e}")
    
    def record_alert(self, alert: Dict):
        """
        Record an alert in historical database
        
        Args:
            alert: Alert dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse alert info
            event_type = alert.get('event', 'Unknown')
            area_desc = alert.get('areaDesc', '')
            
            # Extract first county/state
            county = 'Unknown'
            state = 'Unknown'
            if area_desc:
                parts = area_desc.split(';')[0].strip().split(',')
                if len(parts) >= 1:
                    county = parts[0].strip()
                if len(parts) >= 2:
                    state = parts[1].strip()
            
            # Parse timestamp
            sent_time = alert.get('sent', '')
            try:
                issued = datetime.fromisoformat(sent_time.replace('Z', '+00:00'))
            except:
                issued = datetime.utcnow()
            
            expires_time = alert.get('expires', '')
            try:
                expired = datetime.fromisoformat(expires_time.replace('Z', '+00:00'))
            except:
                expired = None
            
            # Insert record
            cursor.execute('''
                INSERT INTO alert_history 
                (event_type, county, state, issued_time, expired_time, severity, urgency, year, month, day_of_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_type,
                county,
                state,
                issued,
                expired,
                alert.get('severity', ''),
                alert.get('urgency', ''),
                issued.year,
                issued.month,
                issued.timetuple().tm_yday
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording alert to history: {e}")
    
    def get_alert_comparison(self, current_alert: Dict) -> Optional[str]:
        """
        Compare current alert to historical patterns
        
        Args:
            current_alert: Current alert dictionary
            
        Returns:
            Comparison text or None
        """
        try:
            event_type = current_alert.get('event', '')
            
            if not event_type:
                return None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.utcnow()
            
            # Count this type of alert this year
            cursor.execute('''
                SELECT COUNT(*) FROM alert_history
                WHERE event_type = ? AND year = ?
            ''', (event_type, now.year))
            
            count_this_year = cursor.fetchone()[0]
            
            # Get historical average for this alert type
            cursor.execute('''
                SELECT COUNT(*) as total, COUNT(DISTINCT year) as years
                FROM alert_history
                WHERE event_type = ? AND year < ?
            ''', (event_type, now.year))
            
            result = cursor.fetchone()
            total_historical = result[0]
            years = result[1]
            
            conn.close()
            
            # Generate comparison
            if count_this_year == 0:
                return None  # First one, no comparison yet
            
            parts = []
            
            # Year-to-date comparison
            if count_this_year == 1:
                parts.append(f"This is the first {event_type} of the year")
            elif count_this_year <= 3:
                parts.append(f"This is the {self._ordinal(count_this_year)} {event_type} this year")
            else:
                parts.append(f"This is the {self._ordinal(count_this_year)} {event_type} this year")
                
                # Add context if above/below average
                if years > 0:
                    avg_per_year = total_historical / years
                    
                    if count_this_year > avg_per_year * 1.5:
                        parts.append(f"well above the average of {int(avg_per_year)} per year")
                    elif count_this_year < avg_per_year * 0.5:
                        parts.append(f"below the average of {int(avg_per_year)} per year")
            
            if parts:
                return ". ".join(parts) + "."
            
        except Exception as e:
            logger.error(f"Error getting alert comparison: {e}")
        
        return None
    
    def get_recent_activity_summary(self, days: int = 30) -> Optional[str]:
        """
        Get summary of recent severe weather activity
        
        Args:
            days: Number of days to look back
            
        Returns:
            Activity summary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Count warnings by type
            cursor.execute('''
                SELECT event_type, COUNT(*) as count
                FROM alert_history
                WHERE issued_time >= ? AND event_type LIKE '%Warning%'
                GROUP BY event_type
                ORDER BY count DESC
            ''', (cutoff,))
            
            warnings = cursor.fetchall()
            conn.close()
            
            if not warnings:
                return None
            
            # Format summary
            total = sum(w[1] for w in warnings)
            
            if total == 0:
                return None
            
            if total == 1:
                return f"One weather warning in the past {days} days."
            
            parts = [f"{total} weather warnings in the past {days} days"]
            
            # List breakdown if multiple types
            if len(warnings) > 1:
                breakdown = []
                for event_type, count in warnings[:3]:  # Top 3
                    # Simplify event name
                    simple_name = event_type.replace(' Warning', '')
                    breakdown.append(f"{count} {simple_name}")
                
                parts.append("including " + ", ".join(breakdown))
            
            return ". ".join(parts) + "."
            
        except Exception as e:
            logger.error(f"Error getting activity summary: {e}")
        
        return None
    
    def get_busiest_day_comparison(self) -> Optional[str]:
        """
        Compare today's alert activity to busiest day on record
        
        Returns:
            Comparison text or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get today's count
            today = datetime.utcnow().date()
            cursor.execute('''
                SELECT COUNT(*) FROM alert_history
                WHERE DATE(issued_time) = ?
            ''', (today,))
            
            today_count = cursor.fetchone()[0]
            
            if today_count < 3:  # Not significant enough
                conn.close()
                return None
            
            # Get max count day
            cursor.execute('''
                SELECT DATE(issued_time) as alert_date, COUNT(*) as count
                FROM alert_history
                WHERE DATE(issued_time) < ?
                GROUP BY alert_date
                ORDER BY count DESC
                LIMIT 1
            ''', (today,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return f"Today's weather activity is among the most active on record with {today_count} alerts."
            
            max_date, max_count = result
            
            if today_count >= max_count:
                return f"Today's weather activity matches the busiest day on record with {today_count} alerts."
            elif today_count >= max_count * 0.8:
                return f"Today has been one of the most active weather days with {today_count} alerts."
            
        except Exception as e:
            logger.error(f"Error getting busiest day comparison: {e}")
        
        return None
    
    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


# Singleton instance
_historical_comparisons = None

def get_historical_comparisons(db_path: str = "data/weather_history.db") -> HistoricalComparisons:
    """Get singleton HistoricalComparisons instance"""
    global _historical_comparisons
    if _historical_comparisons is None:
        _historical_comparisons = HistoricalComparisons(db_path)
    return _historical_comparisons


def get_historical_context(current_alert: Dict) -> Optional[str]:
    """
    Convenience function to get historical context for an alert
    
    Args:
        current_alert: Current alert dictionary
        
    Returns:
        Historical context text or None
    """
    comparisons = get_historical_comparisons()
    return comparisons.get_alert_comparison(current_alert)


def record_current_alert(alert: Dict):
    """
    Convenience function to record alert in history
    
    Args:
        alert: Alert dictionary to record
    """
    comparisons = get_historical_comparisons()
    comparisons.record_alert(alert)
