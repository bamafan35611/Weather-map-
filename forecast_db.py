"""
forecast_db.py - SQLite Database for Weather Forecast Learning
Tracks predictions, verifications, and learns patterns over time
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Database path - Use /tmp for Render (ephemeral but works during session)
# Note: Database will reset on Render restarts, but at least it will work
DB_PATH = os.getenv('SQLITE_DB_PATH', '/tmp/weather_learning.db')

# Fallback for local development
if not os.path.exists(os.path.dirname(DB_PATH)) and os.path.dirname(DB_PATH):
    DB_PATH = 'weather_learning.db'  # Local fallback

print(f"📊 Weather Learning Database: {DB_PATH}")

def get_connection():
    """Get database connection with proper settings"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)  # 10 second timeout
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Forecasts table - stores predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            forecast_for TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            prediction_type TEXT NOT NULL,
            predicted_event TEXT,
            predicted_severity TEXT,
            confidence REAL,
            details TEXT,
            verified BOOLEAN DEFAULT 0,
            verified_at TEXT,
            actual_event TEXT,
            actual_severity TEXT,
            accuracy_score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verifications table - tracks what actually happened
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_id INTEGER,
            actual_time TEXT NOT NULL,
            actual_event TEXT,
            actual_severity TEXT,
            matched BOOLEAN,
            time_accuracy REAL,
            event_accuracy REAL,
            overall_accuracy REAL,
            notes TEXT,
            verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (forecast_id) REFERENCES forecasts(id)
        )
    ''')
    
    # Learning patterns table - stores discovered patterns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            conditions TEXT NOT NULL,
            outcome TEXT NOT NULL,
            confidence REAL,
            occurrence_count INTEGER DEFAULT 1,
            success_count INTEGER DEFAULT 0,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Alert history table - track actual alerts that occurred
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE,
            event_type TEXT NOT NULL,
            severity TEXT,
            urgency TEXT,
            certainty TEXT,
            location TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT,
            verified BOOLEAN,
            damage_reports INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_timestamp ON forecasts(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_location ON forecasts(location)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verifications_forecast_id ON verifications(forecast_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_history_issued ON alert_history(issued_at)')
    
    conn.commit()
    conn.close()
    
    print(f"✓ SQLite database initialized at: {DB_PATH}")

def save_forecast(forecast_data: Dict) -> int:
    """
    Save a forecast prediction to database
    
    Args:
        forecast_data: Dictionary containing prediction details
    
    Returns:
        Forecast ID
    """
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO forecasts (
                    timestamp, forecast_for, location, latitude, longitude,
                    prediction_type, predicted_event, predicted_severity,
                    confidence, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                forecast_data.get('timestamp', datetime.now().isoformat()),
                forecast_data.get('forecast_for'),
                forecast_data.get('location', 'Unknown'),
                forecast_data.get('latitude'),
                forecast_data.get('longitude'),
                forecast_data.get('prediction_type', 'weather_event'),
                forecast_data.get('predicted_event'),
                forecast_data.get('predicted_severity', 'moderate'),
                forecast_data.get('confidence', 0.0),
                json.dumps(forecast_data.get('details', {}))
            ))
            
            forecast_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✓ Saved forecast #{forecast_id}: {forecast_data.get('predicted_event')} for {forecast_data.get('location')}")
            return forecast_id
            
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                print(f"⚠️ Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                print(f"❌ Error saving forecast after {attempt + 1} attempts: {e}")
                raise
        except Exception as e:
            print(f"❌ Error saving forecast: {e}")
            raise
    
    raise Exception("Failed to save forecast after maximum retries")

def verify_forecast(forecast_id: int, actual_data: Dict) -> bool:
    """
    Verify a forecast against what actually happened
    
    Args:
        forecast_id: ID of the forecast to verify
        actual_data: Dictionary with actual event data
    
    Returns:
        True if verification successful
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate accuracy scores
    time_accuracy = actual_data.get('time_accuracy', 0.0)
    event_accuracy = actual_data.get('event_accuracy', 0.0)
    overall_accuracy = (time_accuracy + event_accuracy) / 2.0
    
    # Update forecast
    cursor.execute('''
        UPDATE forecasts 
        SET verified = 1,
            verified_at = ?,
            actual_event = ?,
            actual_severity = ?,
            accuracy_score = ?
        WHERE id = ?
    ''', (
        datetime.now().isoformat(),
        actual_data.get('actual_event'),
        actual_data.get('actual_severity'),
        overall_accuracy,
        forecast_id
    ))
    
    # Insert verification record
    cursor.execute('''
        INSERT INTO verifications (
            forecast_id, actual_time, actual_event, actual_severity,
            matched, time_accuracy, event_accuracy, overall_accuracy, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        forecast_id,
        actual_data.get('actual_time', datetime.now().isoformat()),
        actual_data.get('actual_event'),
        actual_data.get('actual_severity'),
        actual_data.get('matched', False),
        time_accuracy,
        event_accuracy,
        overall_accuracy,
        actual_data.get('notes')
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Verified forecast #{forecast_id}: {overall_accuracy:.2f} accuracy")
    return True

def get_forecast_history(limit: int = 100, location: Optional[str] = None) -> List[Dict]:
    """
    Get forecast history
    
    Args:
        limit: Maximum number of records to return
        location: Filter by location (optional)
    
    Returns:
        List of forecast dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if location:
        cursor.execute('''
            SELECT * FROM forecasts 
            WHERE location = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (location, limit))
    else:
        cursor.execute('''
            SELECT * FROM forecasts 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_accuracy_stats(days: int = 30) -> Dict:
    """
    Get accuracy statistics for the last N days
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Dictionary with accuracy statistics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Overall stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_forecasts,
            COUNT(CASE WHEN verified = 1 THEN 1 END) as verified_count,
            AVG(CASE WHEN verified = 1 THEN accuracy_score END) as avg_accuracy,
            MAX(accuracy_score) as best_accuracy,
            MIN(CASE WHEN verified = 1 THEN accuracy_score END) as worst_accuracy
        FROM forecasts 
        WHERE timestamp >= ?
    ''', (since,))
    
    stats = dict(cursor.fetchone())
    
    # By event type
    cursor.execute('''
        SELECT 
            predicted_event,
            COUNT(*) as count,
            AVG(CASE WHEN verified = 1 THEN accuracy_score END) as avg_accuracy
        FROM forecasts 
        WHERE timestamp >= ? AND verified = 1
        GROUP BY predicted_event
        ORDER BY count DESC
    ''', (since,))
    
    stats['by_event_type'] = [dict(row) for row in cursor.fetchall()]
    
    # Trend (last 7 days vs previous 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
    
    cursor.execute('''
        SELECT AVG(accuracy_score) as recent_accuracy
        FROM forecasts 
        WHERE timestamp >= ? AND verified = 1
    ''', (week_ago,))
    recent = cursor.fetchone()['recent_accuracy'] or 0.0
    
    cursor.execute('''
        SELECT AVG(accuracy_score) as previous_accuracy
        FROM forecasts 
        WHERE timestamp >= ? AND timestamp < ? AND verified = 1
    ''', (two_weeks_ago, week_ago))
    previous = cursor.fetchone()['previous_accuracy'] or 0.0
    
    stats['improvement'] = recent - previous if previous > 0 else 0.0
    stats['improving'] = stats['improvement'] > 0
    
    conn.close()
    
    return stats

def save_alert_history(alert_data: Dict) -> int:
    """
    Save actual alert that occurred
    
    Args:
        alert_data: Alert details
    
    Returns:
        Alert history ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO alert_history (
                alert_id, event_type, severity, urgency, certainty,
                location, issued_at, expires_at, verified, damage_reports, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert_data.get('id'),
            alert_data.get('event'),
            alert_data.get('severity'),
            alert_data.get('urgency'),
            alert_data.get('certainty'),
            alert_data.get('areaDesc', 'Unknown'),
            alert_data.get('onset', datetime.now().isoformat()),
            alert_data.get('expires'),
            alert_data.get('verified', False),
            alert_data.get('damage_reports', 0),
            alert_data.get('notes')
        ))
        
        alert_id = cursor.lastrowid
        conn.commit()
        
        return alert_id
    except Exception as e:
        print(f"Error saving alert history: {e}")
        return 0
    finally:
        conn.close()

def save_pattern(pattern_data: Dict) -> int:
    """
    Save or update a learned weather pattern
    
    Args:
        pattern_data: Pattern details
    
    Returns:
        Pattern ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if pattern exists
    cursor.execute('''
        SELECT id, occurrence_count, success_count 
        FROM patterns 
        WHERE pattern_type = ? AND conditions = ?
    ''', (pattern_data.get('pattern_type'), json.dumps(pattern_data.get('conditions'))))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing pattern
        pattern_id = existing['id']
        new_count = existing['occurrence_count'] + 1
        new_success = existing['success_count'] + (1 if pattern_data.get('success', False) else 0)
        
        cursor.execute('''
            UPDATE patterns 
            SET occurrence_count = ?,
                success_count = ?,
                confidence = ?,
                last_seen = ?
            WHERE id = ?
        ''', (new_count, new_success, new_success / new_count, datetime.now().isoformat(), pattern_id))
    else:
        # Insert new pattern
        cursor.execute('''
            INSERT INTO patterns (
                pattern_type, conditions, outcome, confidence, occurrence_count, success_count
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            pattern_data.get('pattern_type'),
            json.dumps(pattern_data.get('conditions')),
            json.dumps(pattern_data.get('outcome')),
            pattern_data.get('confidence', 0.5),
            1,
            1 if pattern_data.get('success', False) else 0
        ))
        pattern_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return pattern_id

def format_history_for_frontend(history: List[Dict]) -> List[Dict]:
    """
    Format forecast history for frontend display
    
    Args:
        history: Raw history from database
    
    Returns:
        Formatted history
    """
    formatted = []
    
    for record in history:
        formatted.append({
            'id': record['id'],
            'timestamp': record['timestamp'],
            'location': record['location'],
            'predicted_event': record['predicted_event'],
            'confidence': f"{record['confidence']:.0%}" if record['confidence'] else "N/A",
            'verified': "✓" if record['verified'] else "Pending",
            'accuracy': f"{record['accuracy_score']:.0%}" if record['accuracy_score'] else "N/A",
            'actual_event': record['actual_event'] or "Pending"
        })
    
    return formatted

# Initialize database on import
try:
    init_database()
except Exception as e:
    print(f"⚠️ Error initializing database: {e}")

if __name__ == '__main__':
    print("=" * 70)
    print("NORTHBAMAWX LEARNING DATABASE - SQLite")
    print("=" * 70)
    print(f"\nDatabase location: {DB_PATH}")
    
    # Test the database
    print("\n1. Testing forecast save...")
    forecast_id = save_forecast({
        'timestamp': datetime.now().isoformat(),
        'forecast_for': (datetime.now() + timedelta(hours=2)).isoformat(),
        'location': 'Madison County, AL',
        'latitude': 34.73,
        'longitude': -86.59,
        'prediction_type': 'severe_weather',
        'predicted_event': 'Severe Thunderstorm Warning',
        'predicted_severity': 'moderate',
        'confidence': 0.85,
        'details': {'temp': 85, 'dewpoint': 72}
    })
    print(f"   Saved as forecast #{forecast_id}")
    
    print("\n2. Getting accuracy stats...")
    stats = get_accuracy_stats(30)
    print(f"   Total forecasts (30 days): {stats['total_forecasts']}")
    print(f"   Verified: {stats['verified_count']}")
    print(f"   Avg accuracy: {stats.get('avg_accuracy', 0):.2%}")
    
    print("\n3. Getting forecast history...")
    history = get_forecast_history(limit=5)
    print(f"   Retrieved {len(history)} records")
    
    print("\n" + "=" * 70)
    print("✓ SQLite learning database is working!")
    print("=" * 70)

# Initialize database on module load
try:
    init_database()
except Exception as e:
    print(f"❌ Failed to initialize forecast database: {e}")
