"""
city_rotation.py - Smart City Rotation Tracker
Ensures variety in city forecasts by tracking recent mentions
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import random

class CityRotationTracker:
    """Tracks which cities have been recently mentioned"""
    
    def __init__(self, db_path: str = '/data/city_rotation.db'):
        self.db_path = db_path
        self.cooldown_hours = 6  # Don't repeat city within 6 hours
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database and tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS city_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT NOT NULL,
                state TEXT NOT NULL,
                mentioned_at TEXT NOT NULL,
                broadcast_type TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_city_time 
            ON city_mentions(city_name, mentioned_at DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        print("✓ City rotation tracker initialized")
    
    def record_mention(self, city_name: str, state: str, broadcast_type: str = 'city_briefing'):
        """
        Record that a city was mentioned
        
        Args:
            city_name: City name
            state: State abbreviation
            broadcast_type: Type of broadcast
        """
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO city_mentions (city_name, state, mentioned_at, broadcast_type)
            VALUES (?, ?, ?, ?)
        ''', (city_name, state, timestamp, broadcast_type))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Recorded mention: {city_name}, {state}")
    
    def get_recently_mentioned_cities(self, hours: int = None) -> List[str]:
        """
        Get cities mentioned within specified hours
        
        Args:
            hours: Number of hours to look back (default: cooldown_hours)
        
        Returns:
            List of city names
        """
        if hours is None:
            hours = self.cooldown_hours
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT city_name
            FROM city_mentions
            WHERE mentioned_at >= ?
        ''', (cutoff_time.isoformat(),))
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def is_city_on_cooldown(self, city_name: str) -> bool:
        """
        Check if city is in cooldown period
        
        Args:
            city_name: City name to check
        
        Returns:
            True if on cooldown, False otherwise
        """
        recent_cities = self.get_recently_mentioned_cities()
        return city_name in recent_cities
    
    def get_city_stats(self) -> Dict:
        """
        Get statistics about city mentions
        
        Returns:
            Dict with mention statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total mentions per city
        cursor.execute('''
            SELECT city_name, state, COUNT(*) as mention_count
            FROM city_mentions
            GROUP BY city_name, state
            ORDER BY mention_count DESC
        ''')
        
        city_counts = cursor.fetchall()
        
        # Get recent activity (last 24 hours)
        yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('''
            SELECT COUNT(DISTINCT city_name)
            FROM city_mentions
            WHERE mentioned_at >= ?
        ''', (yesterday,))
        
        recent_unique = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_mentions': sum(count for _, _, count in city_counts),
            'unique_cities': len(city_counts),
            'recent_unique_24h': recent_unique,
            'top_cities': [(name, state, count) for name, state, count in city_counts[:10]]
        }
    
    def filter_available_cities(self, all_cities: List[Dict]) -> List[Dict]:
        """
        Filter out cities on cooldown
        
        Args:
            all_cities: List of city dicts with 'name' and 'state' keys
        
        Returns:
            List of cities not on cooldown
        """
        recent_cities = self.get_recently_mentioned_cities()
        
        available = [
            city for city in all_cities 
            if city['name'] not in recent_cities
        ]
        
        # If all cities on cooldown, return all cities (reset rotation)
        if not available:
            print("⚠️ All cities on cooldown - resetting rotation")
            return all_cities
        
        print(f"✓ {len(available)} cities available (filtered {len(all_cities) - len(available)} on cooldown)")
        return available
    
    def cleanup_old_records(self, days_to_keep: int = 30):
        """
        Remove old mention records
        
        Args:
            days_to_keep: Number of days to keep
        """
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM city_mentions
            WHERE mentioned_at < ?
        ''', (cutoff_time.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"✓ Cleaned up {deleted} old city mention records")


# Singleton instance
_rotation_tracker = None

def get_rotation_tracker():
    """Get singleton rotation tracker"""
    global _rotation_tracker
    if _rotation_tracker is None:
        _rotation_tracker = CityRotationTracker()
    return _rotation_tracker


def record_city_mention(city_name: str, state: str, broadcast_type: str = 'city_briefing'):
    """Record a city mention"""
    tracker = get_rotation_tracker()
    tracker.record_mention(city_name, state, broadcast_type)


def get_available_cities(all_cities: List[Dict]) -> List[Dict]:
    """Get cities not on cooldown"""
    tracker = get_rotation_tracker()
    return tracker.filter_available_cities(all_cities)


def is_city_available(city_name: str) -> bool:
    """Check if city is available (not on cooldown)"""
    tracker = get_rotation_tracker()
    return not tracker.is_city_on_cooldown(city_name)


if __name__ == '__main__':
    # Test the city rotation tracker
    print("=" * 70)
    print("CITY ROTATION TRACKER TEST")
    print("=" * 70)
    
    tracker = CityRotationTracker(db_path='/tmp/test_city_rotation.db')
    
    # Simulate some city mentions
    test_cities = [
        ('Huntsville', 'AL'),
        ('Athens', 'AL'),
        ('Decatur', 'AL'),
        ('Florence', 'AL'),
        ('Huntsville', 'AL'),  # Duplicate
    ]
    
    print("\n1. Recording city mentions:")
    print("-" * 70)
    for city, state in test_cities:
        tracker.record_mention(city, state)
    
    print("\n2. Recently mentioned cities:")
    print("-" * 70)
    recent = tracker.get_recently_mentioned_cities()
    print(f"Cities on cooldown: {', '.join(recent)}")
    
    print("\n3. City statistics:")
    print("-" * 70)
    stats = tracker.get_city_stats()
    print(f"Total mentions: {stats['total_mentions']}")
    print(f"Unique cities: {stats['unique_cities']}")
    print(f"Recent unique (24h): {stats['recent_unique_24h']}")
    print("\nTop cities:")
    for city, state, count in stats['top_cities']:
        print(f"  {city}, {state}: {count} mentions")
    
    print("\n4. Testing city filtering:")
    print("-" * 70)
    all_test_cities = [
        {'name': 'Huntsville', 'state': 'AL'},
        {'name': 'Athens', 'state': 'AL'},
        {'name': 'Decatur', 'state': 'AL'},
        {'name': 'Florence', 'state': 'AL'},
        {'name': 'Scottsboro', 'state': 'AL'},
    ]
    available = tracker.filter_available_cities(all_test_cities)
    print(f"Available cities: {[c['name'] for c in available]}")
    
    print("\n" + "=" * 70)
    print("✓ City rotation tracker working!")
    print("=" * 70)
