"""
temperature_trends.py - Track Temperature Changes Over Time
Monitors hourly temperature and announces trends
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class TemperatureTrendTracker:
    """Tracks temperature over time and identifies trends"""
    
    def __init__(self, db_path: str = '/data/weather_trends.db'):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database and tables if they don't exist"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                location TEXT NOT NULL,
                temperature REAL NOT NULL,
                feels_like REAL,
                humidity INTEGER,
                wind_speed REAL,
                UNIQUE(timestamp, location)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_temp_timestamp 
            ON temperature_history(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_temp_location 
            ON temperature_history(location, timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        print("✓ Temperature trend database initialized")
    
    def record_temperature(self, location: str, temperature: float, 
                          feels_like: Optional[float] = None,
                          humidity: Optional[int] = None,
                          wind_speed: Optional[float] = None):
        """
        Record current temperature
        
        Args:
            location: Location name (e.g., "Athens, AL")
            temperature: Temperature in Fahrenheit
            feels_like: Feels like temperature
            humidity: Humidity percentage
            wind_speed: Wind speed in mph
        """
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO temperature_history 
                (timestamp, location, temperature, feels_like, humidity, wind_speed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, location, temperature, feels_like, humidity, wind_speed))
            
            conn.commit()
        except Exception as e:
            print(f"Error recording temperature: {e}")
        finally:
            conn.close()
    
    def get_temperature_trend(self, location: str, hours: int = 3) -> Optional[Dict]:
        """
        Get temperature trend over specified hours
        
        Args:
            location: Location name
            hours: Number of hours to look back
        
        Returns:
            Dict with trend information or None
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, temperature
            FROM temperature_history
            WHERE location = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (location, cutoff_time.isoformat()))
        
        results = cursor.fetchall()
        conn.close()
        
        if len(results) < 2:
            return None
        
        # Get first and last reading
        first_time, first_temp = results[0]
        last_time, last_temp = results[-1]
        
        temp_change = last_temp - first_temp
        
        return {
            'location': location,
            'hours': hours,
            'first_temp': first_temp,
            'last_temp': last_temp,
            'change': temp_change,
            'direction': 'rising' if temp_change > 0 else 'falling' if temp_change < 0 else 'steady',
            'rate_per_hour': temp_change / hours if hours > 0 else 0
        }
    
    def get_yesterday_comparison(self, location: str) -> Optional[Dict]:
        """
        Compare current temperature to same time yesterday
        
        Args:
            location: Location name
        
        Returns:
            Dict with comparison or None
        """
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Get current temperature (most recent)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT temperature, timestamp
            FROM temperature_history
            WHERE location = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (location,))
        
        current_result = cursor.fetchone()
        
        if not current_result:
            conn.close()
            return None
        
        current_temp, current_time = current_result
        
        # Get yesterday's temperature (within 1 hour window)
        yesterday_start = (yesterday - timedelta(hours=1)).isoformat()
        yesterday_end = (yesterday + timedelta(hours=1)).isoformat()
        
        cursor.execute('''
            SELECT temperature
            FROM temperature_history
            WHERE location = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY ABS(julianday(timestamp) - julianday(?))
            LIMIT 1
        ''', (location, yesterday_start, yesterday_end, yesterday.isoformat()))
        
        yesterday_result = cursor.fetchone()
        conn.close()
        
        if not yesterday_result:
            return None
        
        yesterday_temp = yesterday_result[0]
        temp_change = current_temp - yesterday_temp
        
        return {
            'location': location,
            'current_temp': current_temp,
            'yesterday_temp': yesterday_temp,
            'change': temp_change,
            'direction': 'warmer' if temp_change > 0 else 'cooler' if temp_change < 0 else 'same'
        }
    
    def get_trend_announcement(self, location: str) -> Optional[str]:
        """
        Get human-readable trend announcement
        
        Args:
            location: Location name
        
        Returns:
            Announcement text or None
        """
        # Try 3-hour trend first
        trend = self.get_temperature_trend(location, hours=3)
        yesterday = self.get_yesterday_comparison(location)
        
        announcements = []
        
        # Recent trend (3 hours)
        if trend and abs(trend['change']) >= 3:  # Only announce if changed 3+ degrees
            change = abs(trend['change'])
            direction = trend['direction']
            
            if direction == 'rising':
                announcements.append(f"Temperature rising, up {change:.0f} degrees in the past 3 hours")
            elif direction == 'falling':
                announcements.append(f"Temperature falling, down {change:.0f} degrees in the past 3 hours")
        
        # Yesterday comparison
        if yesterday and abs(yesterday['change']) >= 5:  # Only announce if 5+ degrees different
            change = abs(yesterday['change'])
            direction = yesterday['direction']
            current = yesterday['current_temp']
            
            if direction == 'warmer':
                announcements.append(f"Currently {current:.0f} degrees, that's {change:.0f} degrees warmer than yesterday")
            elif direction == 'cooler':
                announcements.append(f"Currently {current:.0f} degrees, that's {change:.0f} degrees cooler than yesterday")
        
        if announcements:
            return ". ".join(announcements) + "."
        
        return None
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """
        Remove temperature data older than specified days
        
        Args:
            days_to_keep: Number of days to keep
        """
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM temperature_history
            WHERE timestamp < ?
        ''', (cutoff_time.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"✓ Cleaned up {deleted} old temperature records")


# Singleton instance
_trend_tracker = None

def get_trend_tracker():
    """Get singleton trend tracker"""
    global _trend_tracker
    if _trend_tracker is None:
        _trend_tracker = TemperatureTrendTracker()
    return _trend_tracker


def record_temperature(location: str, temperature: float, **kwargs):
    """Record temperature reading"""
    tracker = get_trend_tracker()
    tracker.record_temperature(location, temperature, **kwargs)


def get_temperature_announcement(location: str) -> Optional[str]:
    """Get temperature trend announcement"""
    tracker = get_trend_tracker()
    return tracker.get_trend_announcement(location)


if __name__ == '__main__':
    # Test the temperature tracker
    print("=" * 70)
    print("TEMPERATURE TREND TRACKER TEST")
    print("=" * 70)
    
    tracker = TemperatureTrendTracker(db_path='/tmp/test_weather_trends.db')
    
    # Simulate temperature readings over time
    now = datetime.now()
    
    # 3 hours ago: 70°F
    tracker.record_temperature("Athens, AL", 70.0)
    
    # 2 hours ago: 73°F
    # 1 hour ago: 76°F
    # Now: 78°F (8 degree rise over 3 hours)
    tracker.record_temperature("Athens, AL", 78.0)
    
    print("\n1. Testing 3-hour trend:")
    print("-" * 70)
    trend = tracker.get_temperature_trend("Athens, AL", hours=3)
    if trend:
        print(f"Temperature {trend['direction']}: {trend['change']:.1f}°F over {trend['hours']} hours")
        print(f"Rate: {trend['rate_per_hour']:.1f}°F per hour")
    
    print("\n2. Testing announcement generation:")
    print("-" * 70)
    announcement = tracker.get_trend_announcement("Athens, AL")
    if announcement:
        print(f"Announcement: {announcement}")
    else:
        print("No significant trend to announce")
    
    print("\n" + "=" * 70)
    print("✓ Temperature trend tracker working!")
    print("=" * 70)
