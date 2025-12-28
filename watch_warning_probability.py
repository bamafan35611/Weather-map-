"""
watch_warning_probability.py - Watch to Warning Probability Predictions
Predicts likelihood of watches producing warnings based on historical data
"""

from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Optional, Tuple
import os

class WatchWarningPredictor:
    """Predicts probability of watches producing warnings"""
    
    def __init__(self, db_path: str = 'data/weather_history.db'):
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for watch tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watch_id TEXT UNIQUE,
                watch_type TEXT,
                counties TEXT,
                start_time TEXT,
                end_time TEXT,
                produced_warning INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                recorded_at TEXT
            )
        ''')
        
        # Table for watch-warning linkage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_warning_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watch_id TEXT,
                warning_id TEXT,
                warning_type TEXT,
                link_time TEXT,
                FOREIGN KEY (watch_id) REFERENCES watch_tracking(watch_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_watch(self, alert: Dict) -> None:
        """Record a new watch being issued"""
        try:
            watch_id = alert.get('id', '')
            if not watch_id:
                return
            
            watch_type = alert.get('event', '')
            if 'watch' not in watch_type.lower():
                return
            
            # Normalize watch type
            if 'tornado' in watch_type.lower():
                normalized_type = 'Tornado Watch'
            elif 'severe thunderstorm' in watch_type.lower():
                normalized_type = 'Severe Thunderstorm Watch'
            elif 'flash flood' in watch_type.lower():
                normalized_type = 'Flash Flood Watch'
            elif 'flood' in watch_type.lower():
                normalized_type = 'Flood Watch'
            else:
                normalized_type = watch_type
            
            counties = alert.get('areaDesc', 'Unknown')
            start_time = alert.get('onset', datetime.now().isoformat())
            end_time = alert.get('expires', '')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO watch_tracking 
                (watch_id, watch_type, counties, start_time, end_time, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (watch_id, normalized_type, counties, start_time, end_time, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Recorded {normalized_type} for tracking")
            
        except Exception as e:
            print(f"Error recording watch: {e}")
    
    def check_and_link_warning(self, warning: Dict) -> None:
        """Check if warning occurred during a watch and link them"""
        try:
            warning_type = warning.get('event', '')
            if 'warning' not in warning_type.lower():
                return
            
            warning_id = warning.get('id', '')
            if not warning_id:
                return
            
            # Normalize warning type
            if 'tornado' in warning_type.lower():
                normalized_warning = 'Tornado Warning'
                watch_type = 'Tornado Watch'
            elif 'severe thunderstorm' in warning_type.lower():
                normalized_warning = 'Severe Thunderstorm Warning'
                watch_type = 'Severe Thunderstorm Watch'
            elif 'flash flood' in warning_type.lower():
                normalized_warning = 'Flash Flood Warning'
                watch_type = 'Flash Flood Watch'
            elif 'flood' in warning_type.lower():
                normalized_warning = 'Flood Warning'
                watch_type = 'Flood Watch'
            else:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find active watches of matching type
            now = datetime.now().isoformat()
            cursor.execute('''
                SELECT watch_id FROM watch_tracking 
                WHERE watch_type = ? 
                AND start_time <= ? 
                AND (end_time >= ? OR end_time = '')
                AND produced_warning = 0
            ''', (watch_type, now, now))
            
            active_watches = cursor.fetchall()
            
            if active_watches:
                for (watch_id,) in active_watches:
                    # Link warning to watch
                    cursor.execute('''
                        INSERT INTO watch_warning_links 
                        (watch_id, warning_id, warning_type, link_time)
                        VALUES (?, ?, ?, ?)
                    ''', (watch_id, warning_id, normalized_warning, now))
                    
                    # Update watch as having produced warning
                    cursor.execute('''
                        UPDATE watch_tracking 
                        SET produced_warning = 1,
                            warning_count = warning_count + 1
                        WHERE watch_id = ?
                    ''', (watch_id,))
                    
                    print(f"✓ Linked {normalized_warning} to {watch_type}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error linking warning to watch: {e}")
    
    def get_probability(self, watch_type: str, months_back: int = 6) -> Optional[Dict]:
        """Calculate probability of watch producing warning"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Normalize watch type
            if 'tornado' in watch_type.lower():
                normalized_type = 'Tornado Watch'
            elif 'severe thunderstorm' in watch_type.lower():
                normalized_type = 'Severe Thunderstorm Watch'
            elif 'flash flood' in watch_type.lower():
                normalized_type = 'Flash Flood Watch'
            else:
                normalized_type = watch_type
            
            cutoff_date = (datetime.now() - timedelta(days=months_back * 30)).isoformat()
            
            # Get total watches
            cursor.execute('''
                SELECT COUNT(*) FROM watch_tracking 
                WHERE watch_type = ? AND recorded_at >= ?
            ''', (normalized_type, cutoff_date))
            
            total_watches = cursor.fetchone()[0]
            
            if total_watches == 0:
                conn.close()
                return None
            
            # Get watches that produced warnings
            cursor.execute('''
                SELECT COUNT(*) FROM watch_tracking 
                WHERE watch_type = ? AND recorded_at >= ? AND produced_warning = 1
            ''', (normalized_type, cutoff_date))
            
            converted_watches = cursor.fetchone()[0]
            
            conn.close()
            
            probability = converted_watches / total_watches if total_watches > 0 else 0
            
            return {
                'watch_type': normalized_type,
                'total_watches': total_watches,
                'converted_watches': converted_watches,
                'probability': probability,
                'percentage': round(probability * 100)
            }
            
        except Exception as e:
            print(f"Error calculating probability: {e}")
            return None
    
    def get_probability_announcement(self, alert: Dict) -> Optional[str]:
        """Generate announcement text for watch probability"""
        try:
            watch_type = alert.get('event', '')
            if 'watch' not in watch_type.lower():
                return None
            
            prob_data = self.get_probability(watch_type)
            
            if not prob_data:
                # Not enough historical data yet
                return None
            
            if prob_data['total_watches'] < 3:
                # Need at least 3 watches for meaningful probability
                return None
            
            percentage = prob_data['percentage']
            total = prob_data['total_watches']
            converted = prob_data['converted_watches']
            
            # Generate appropriate message based on probability
            if percentage >= 60:
                confidence = "WARNING LIKELY"
                action = "Monitor conditions very closely and be prepared to take shelter."
            elif percentage >= 40:
                confidence = "Elevated probability of warning development"
                action = "Stay weather aware and monitor updates."
            elif percentage >= 20:
                confidence = "Moderate probability of warning issuance"
                action = "Remain weather aware."
            else:
                confidence = "Low probability of warning development"
                action = "Continue normal activities but stay informed."
            
            announcement = f"{confidence}. Based on {total} similar watches in the past 6 months, {converted} produced warnings ({percentage}% probability). {action}"
            
            return announcement
            
        except Exception as e:
            print(f"Error generating probability announcement: {e}")
            return None


# Singleton instance
_predictor = None

def get_watch_predictor() -> WatchWarningPredictor:
    """Get or create predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = WatchWarningPredictor()
    return _predictor


def record_watch(alert: Dict) -> None:
    """Record a watch for tracking"""
    predictor = get_watch_predictor()
    predictor.record_watch(alert)


def check_warning_linkage(warning: Dict) -> None:
    """Check if warning should be linked to active watch"""
    predictor = get_watch_predictor()
    predictor.check_and_link_warning(warning)


def get_watch_probability_announcement(alert: Dict) -> Optional[str]:
    """Get probability announcement for a watch"""
    predictor = get_watch_predictor()
    return predictor.get_probability_announcement(alert)


if __name__ == '__main__':
    # Test the system
    print("=" * 70)
    print("WATCH → WARNING PROBABILITY SYSTEM TEST")
    print("=" * 70)
    
    predictor = WatchWarningPredictor()
    
    # Simulate some watches and warnings
    test_watch = {
        'id': 'TEST-WATCH-001',
        'event': 'Tornado Watch',
        'areaDesc': 'Madison County',
        'onset': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(hours=6)).isoformat()
    }
    
    print("\nRecording test watch...")
    predictor.record_watch(test_watch)
    
    print("\nGetting probability...")
    prob = predictor.get_probability('Tornado Watch')
    if prob:
        print(f"Probability: {prob['percentage']}% ({prob['converted_watches']}/{prob['total_watches']})")
    else:
        print("Not enough data yet")
    
    print("\n" + "=" * 70)
