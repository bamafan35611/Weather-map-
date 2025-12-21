"""
accuracy_announcer.py - Forecast Accuracy Announcements
Announces monthly accuracy statistics to build credibility
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import calendar

class AccuracyAnnouncer:
    """Generates accuracy announcements from verification data"""
    
    def __init__(self, db_path: str = '/data/weather_learning.db'):
        self.db_path = db_path
        self.last_announcement = None
        self.announcement_interval_hours = 168  # Once per week
    
    def get_monthly_accuracy(self, year: int = None, month: int = None) -> Optional[Dict]:
        """
        Get accuracy statistics for a specific month
        
        Args:
            year: Year (default: current year)
            month: Month (default: last month)
        
        Returns:
            Dict with accuracy statistics or None
        """
        if year is None or month is None:
            # Default to last month
            today = datetime.now()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
        
        # Get first and last day of month
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get verification results for the month
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN severity = 'severe' THEN 1 ELSE 0 END) as severe_events
                FROM predictions
                WHERE predicted_at >= ? AND predicted_at <= ?
                AND verified = 1
            ''', (first_day.isoformat(), last_day.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or result[0] == 0:
                return None
            
            total, correct, avg_conf, severe = result
            
            accuracy = (correct / total * 100) if total > 0 else 0
            
            return {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy_percent': accuracy,
                'average_confidence': avg_conf,
                'severe_events': severe
            }
        
        except Exception as e:
            print(f"Error getting monthly accuracy: {e}")
            return None
    
    def get_year_to_date_accuracy(self) -> Optional[Dict]:
        """
        Get accuracy for current year
        
        Returns:
            Dict with YTD accuracy or None
        """
        year = datetime.now().year
        start_of_year = datetime(year, 1, 1)
        now = datetime.now()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions
                FROM predictions
                WHERE predicted_at >= ? AND predicted_at <= ?
                AND verified = 1
            ''', (start_of_year.isoformat(), now.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or result[0] == 0:
                return None
            
            total, correct = result
            accuracy = (correct / total * 100) if total > 0 else 0
            
            return {
                'year': year,
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy_percent': accuracy
            }
        
        except Exception as e:
            print(f"Error getting YTD accuracy: {e}")
            return None
    
    def should_announce(self) -> bool:
        """
        Check if it's time for an accuracy announcement
        
        Returns:
            True if should announce, False otherwise
        """
        if self.last_announcement is None:
            return True
        
        time_since_last = datetime.now() - self.last_announcement
        return time_since_last.total_seconds() > (self.announcement_interval_hours * 3600)
    
    def get_accuracy_announcement(self, force: bool = False) -> Optional[str]:
        """
        Generate accuracy announcement
        
        Args:
            force: Force announcement even if not time yet
        
        Returns:
            Announcement text or None
        """
        if not force and not self.should_announce():
            return None
        
        # Try to get last month's accuracy
        stats = self.get_monthly_accuracy()
        
        if not stats:
            # Fall back to year-to-date
            stats = self.get_year_to_date_accuracy()
            if not stats:
                return None
            
            # YTD announcement
            announcement = (
                f"Weather intelligence update: NorthBamaWX predictions have been "
                f"{stats['accuracy_percent']:.0f}% accurate so far this year, "
                f"correctly forecasting {stats['correct_predictions']} of {stats['total_predictions']} events."
            )
        else:
            # Monthly announcement
            month_name = stats['month_name']
            accuracy = stats['accuracy_percent']
            correct = stats['correct_predictions']
            total = stats['total_predictions']
            
            announcement = (
                f"Weather intelligence update: NorthBamaWX predictions were "
                f"{accuracy:.0f}% accurate in {month_name}, "
                f"correctly forecasting {correct} of {total} severe weather events."
            )
            
            # Add extra context for high accuracy
            if accuracy >= 90:
                announcement += " Exceptional forecast performance."
            elif accuracy >= 85:
                announcement += " Strong forecast performance."
        
        # Record that we announced
        self.last_announcement = datetime.now()
        
        return announcement


# Singleton instance
_accuracy_announcer = None

def get_accuracy_announcer():
    """Get singleton accuracy announcer"""
    global _accuracy_announcer
    if _accuracy_announcer is None:
        _accuracy_announcer = AccuracyAnnouncer()
    return _accuracy_announcer


def get_accuracy_announcement(force: bool = False) -> Optional[str]:
    """Get accuracy announcement if it's time"""
    announcer = get_accuracy_announcer()
    return announcer.get_accuracy_announcement(force)


if __name__ == '__main__':
    # Test the accuracy announcer
    print("=" * 70)
    print("FORECAST ACCURACY ANNOUNCER TEST")
    print("=" * 70)
    
    # Create test database with sample data
    import os
    test_db = '/tmp/test_accuracy.db'
    
    if os.path.exists(test_db):
        os.remove(test_db)
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY,
            predicted_at TEXT,
            verified INTEGER,
            was_correct INTEGER,
            confidence REAL,
            severity TEXT
        )
    ''')
    
    # Add sample data for last month
    today = datetime.now()
    if today.month == 1:
        last_month = datetime(today.year - 1, 12, 15)
    else:
        last_month = datetime(today.year, today.month - 1, 15)
    
    # Insert test predictions (87% accuracy)
    for i in range(100):
        was_correct = 1 if i < 87 else 0
        cursor.execute('''
            INSERT INTO predictions (predicted_at, verified, was_correct, confidence, severity)
            VALUES (?, 1, ?, 75.0, 'severe')
        ''', (last_month.isoformat(), was_correct))
    
    conn.commit()
    conn.close()
    
    # Test the announcer
    announcer = AccuracyAnnouncer(db_path=test_db)
    
    print("\n1. Monthly accuracy:")
    print("-" * 70)
    stats = announcer.get_monthly_accuracy()
    if stats:
        print(f"Month: {stats['month_name']} {stats['year']}")
        print(f"Accuracy: {stats['accuracy_percent']:.1f}%")
        print(f"Correct: {stats['correct_predictions']}/{stats['total_predictions']}")
    
    print("\n2. Generate announcement:")
    print("-" * 70)
    announcement = announcer.get_accuracy_announcement(force=True)
    if announcement:
        print(f"Announcement: {announcement}")
    
    print("\n" + "=" * 70)
    print("✓ Accuracy announcer working!")
    print("=" * 70)
