"""
forecast_db.py - Database module for forecast tracking
Supports both SQLite (local) and PostgreSQL (Render)
"""

import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

# Determine database type from environment
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Fix for Render's postgres:// URLs
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    import sqlite3

@contextmanager
def get_db():
    """Context manager for database connections"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect('weather_forecasts.db')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def init_database():
    """Initialize the database schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            # PostgreSQL schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forecasts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    forecast_for TIMESTAMP NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    prediction_type TEXT NOT NULL,
                    predicted_severity TEXT,
                    confidence REAL,
                    details TEXT,
                    verified INTEGER DEFAULT 0,
                    verification_result TEXT,
                    verification_timestamp TIMESTAMP,
                    actual_event TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actual_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    event_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    severity TEXT,
                    details TEXT,
                    nws_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    forecast_for TEXT NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    prediction_type TEXT NOT NULL,
                    predicted_severity TEXT,
                    confidence REAL,
                    details TEXT,
                    verified INTEGER DEFAULT 0,
                    verification_result TEXT,
                    verification_timestamp TEXT,
                    actual_event TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actual_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    severity TEXT,
                    details TEXT,
                    nws_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        print("✓ Database initialized successfully (PostgreSQL)" if USE_POSTGRES else "✓ Database initialized successfully (SQLite)")

def save_forecast(forecast_data):
    """Save a new forecast prediction"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO forecasts 
                (timestamp, forecast_for, location, latitude, longitude, 
                 prediction_type, predicted_severity, confidence, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                forecast_data.get('timestamp', datetime.utcnow()),
                forecast_data.get('forecast_for'),
                forecast_data.get('location'),
                forecast_data.get('latitude'),
                forecast_data.get('longitude'),
                forecast_data.get('prediction_type'),
                forecast_data.get('predicted_severity'),
                forecast_data.get('confidence'),
                json.dumps(forecast_data.get('details', {}))
            ))
            forecast_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO forecasts 
                (timestamp, forecast_for, location, latitude, longitude, 
                 prediction_type, predicted_severity, confidence, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                forecast_data.get('timestamp', datetime.utcnow().isoformat()),
                forecast_data.get('forecast_for'),
                forecast_data.get('location'),
                forecast_data.get('latitude'),
                forecast_data.get('longitude'),
                forecast_data.get('prediction_type'),
                forecast_data.get('predicted_severity'),
                forecast_data.get('confidence'),
                json.dumps(forecast_data.get('details', {}))
            ))
            forecast_id = cursor.lastrowid
        
        print(f"✓ Saved forecast #{forecast_id}: {forecast_data.get('prediction_type')} for {forecast_data.get('location')}")
        return forecast_id

def save_actual_event(event_data):
    """Save an actual weather event for verification"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO actual_events 
                (timestamp, event_type, location, latitude, longitude, severity, details, nws_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                event_data.get('timestamp', datetime.utcnow()),
                event_data.get('event_type'),
                event_data.get('location'),
                event_data.get('latitude'),
                event_data.get('longitude'),
                event_data.get('severity'),
                json.dumps(event_data.get('details', {})),
                event_data.get('nws_id')
            ))
            event_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO actual_events 
                (timestamp, event_type, location, latitude, longitude, severity, details, nws_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_data.get('timestamp', datetime.utcnow().isoformat()),
                event_data.get('event_type'),
                event_data.get('location'),
                event_data.get('latitude'),
                event_data.get('longitude'),
                event_data.get('severity'),
                json.dumps(event_data.get('details', {})),
                event_data.get('nws_id')
            ))
            event_id = cursor.lastrowid
        
        print(f"✓ Saved actual event #{event_id}: {event_data.get('event_type')} in {event_data.get('location')}")
        return event_id

def get_unverified_forecasts():
    """Get all forecasts that haven't been verified yet and are past their forecast time"""
    with get_db() as conn:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM forecasts 
                WHERE verified = 0 AND forecast_for < NOW()
                ORDER BY forecast_for ASC
            ''')
        else:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute('''
                SELECT * FROM forecasts 
                WHERE verified = 0 AND forecast_for < ?
                ORDER BY forecast_for ASC
            ''', (now,))
        return [dict(row) for row in cursor.fetchall()]

def verify_forecast(forecast_id, result, actual_event=None):
    """Mark a forecast as verified with the result"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                UPDATE forecasts 
                SET verified = 1, 
                    verification_result = %s,
                    verification_timestamp = NOW(),
                    actual_event = %s
                WHERE id = %s
            ''', (result, actual_event, forecast_id))
        else:
            cursor.execute('''
                UPDATE forecasts 
                SET verified = 1, 
                    verification_result = ?,
                    verification_timestamp = ?,
                    actual_event = ?
                WHERE id = ?
            ''', (result, datetime.utcnow().isoformat(), actual_event, forecast_id))
        
        print(f"✓ Verified forecast #{forecast_id}: {result}")

def get_forecast_history(limit=50):
    """Get verified forecast history"""
    with get_db() as conn:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM forecasts 
                WHERE verified = 1 
                ORDER BY verification_timestamp DESC 
                LIMIT %s
            ''', (limit,))
        else:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM forecasts 
                WHERE verified = 1 
                ORDER BY verification_timestamp DESC 
                LIMIT ?
            ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_accuracy_stats(days=30):
    """Calculate accuracy statistics"""
    with get_db() as conn:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN verification_result = 'correct' THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN verification_result = 'false_positive' THEN 1 ELSE 0 END) as false_positives,
                    SUM(CASE WHEN verification_result = 'false_negative' THEN 1 ELSE 0 END) as false_negatives
                FROM forecasts 
                WHERE verified = 1 AND verification_timestamp > NOW() - INTERVAL '%s days'
            ''' % days)
        else:
            cursor = conn.cursor()
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN verification_result = 'correct' THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN verification_result = 'false_positive' THEN 1 ELSE 0 END) as false_positives,
                    SUM(CASE WHEN verification_result = 'false_negative' THEN 1 ELSE 0 END) as false_negatives
                FROM forecasts 
                WHERE verified = 1 AND verification_timestamp > ?
            ''', (since,))
        
        row = cursor.fetchone()
        if row and row['total'] > 0:
            total = row['total']
            correct = row['correct'] or 0
            accuracy = (correct / total) * 100 if total > 0 else 0
            
            return {
                'total_forecasts': total,
                'correct': correct,
                'false_positives': row['false_positives'] or 0,
                'false_negatives': row['false_negatives'] or 0,
                'accuracy_percentage': round(accuracy, 2),
                'days': days
            }
        return {
            'total_forecasts': 0,
            'correct': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'accuracy_percentage': 0,
            'days': days
        }

def format_history_for_frontend(forecasts):
    """Format forecast history for the frontend display"""
    history = []
    for f in forecasts:
        timestamp = f.get('verification_timestamp') or f.get('timestamp')
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
            
        prediction = f['prediction_type']
        location = f['location']
        result = f.get('verification_result')
        
        # Format result emoji
        if result == 'correct':
            result_icon = '✓ CORRECT'
            result_color = '#00ff00'
        elif result == 'false_positive':
            result_icon = '✗ FALSE ALARM'
            result_color = '#ffaa00'
        elif result == 'false_negative':
            result_icon = '✗ MISSED'
            result_color = '#ff4444'
        else:
            result_icon = '? UNKNOWN'
            result_color = '#888888'
        
        # Build event description
        severity = f.get('predicted_severity') or 'unknown'
        confidence = f.get('confidence')
        conf_text = f" ({int(confidence)}% confidence)" if confidence else ""
        
        event_text = f"Predicted {prediction} ({severity}) for {location}{conf_text} - {result_icon}"
        
        history.append({
            'timestamp': timestamp,
            'event': event_text,
            'result': result,
            'color': result_color
        })
    
    return history

# Initialize database on module import
try:
    init_database()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
