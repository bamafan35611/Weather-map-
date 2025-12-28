"""
personal_station_ml.py - Machine Learning Predictions from Personal Weather Station
Uses YOUR Ambient Weather station data to predict weather conditions
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

class PersonalStationML:
    """Machine learning predictions from personal weather station data"""
    
    def __init__(self, db_path: str = 'data/personal_station_history.db'):
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for continuous observations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                wind_speed REAL,
                wind_direction TEXT,
                wind_gust REAL,
                daily_rain REAL,
                recorded_at TEXT
            )
        ''')
        
        # Table for alert correlations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_time TEXT,
                alert_type TEXT,
                pressure_1hr_before REAL,
                pressure_2hr_before REAL,
                pressure_3hr_before REAL,
                temp_1hr_before REAL,
                humidity_1hr_before REAL,
                wind_speed_1hr_before REAL,
                pressure_drop_rate REAL,
                recorded_at TEXT
            )
        ''')
        
        # Table for predictions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_time TEXT,
                prediction_type TEXT,
                confidence REAL,
                reason TEXT,
                conditions TEXT,
                verified INTEGER DEFAULT 0,
                verification_time TEXT,
                accurate INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_observation(self, conditions: Dict) -> None:
        """Record a weather observation from personal station"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO observations 
                (timestamp, temperature, humidity, pressure, wind_speed, 
                 wind_direction, wind_gust, daily_rain, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now,
                conditions.get('temperature'),
                conditions.get('humidity'),
                conditions.get('pressure'),
                conditions.get('wind_speed'),
                conditions.get('wind_direction'),
                conditions.get('wind_gust'),
                conditions.get('daily_rain'),
                now
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Recorded observation: {conditions.get('temperature')}°F, {conditions.get('pressure')} inHg")
            
        except Exception as e:
            print(f"⚠️ Error recording observation: {e}")
    
    def correlate_alert(self, alert_type: str) -> None:
        """When alert happens, correlate with recent station data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Get observations from past 3 hours
            cursor.execute('''
                SELECT timestamp, pressure, temperature, humidity, wind_speed
                FROM observations
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', ((now - timedelta(hours=3)).isoformat(),))
            
            recent_obs = cursor.fetchall()
            
            if len(recent_obs) < 12:  # Need at least 12 observations (1 hour at 5-min intervals)
                print(f"⚠️ Not enough data to correlate alert (have {len(recent_obs)})")
                conn.close()
                return
            
            # Extract values at specific times before alert
            pressure_1hr = None
            pressure_2hr = None
            pressure_3hr = None
            temp_1hr = None
            humidity_1hr = None
            wind_1hr = None
            
            one_hour_ago = now - timedelta(hours=1)
            two_hours_ago = now - timedelta(hours=2)
            three_hours_ago = now - timedelta(hours=3)
            
            for obs in recent_obs:
                obs_time = datetime.fromisoformat(obs[0])
                
                # Find closest to 1 hour ago
                if abs((obs_time - one_hour_ago).total_seconds()) < 600:  # Within 10 min
                    pressure_1hr = obs[1]
                    temp_1hr = obs[2]
                    humidity_1hr = obs[3]
                    wind_1hr = obs[4]
                
                # Find closest to 2 hours ago
                if abs((obs_time - two_hours_ago).total_seconds()) < 600:
                    pressure_2hr = obs[1]
                
                # Find closest to 3 hours ago
                if abs((obs_time - three_hours_ago).total_seconds()) < 600:
                    pressure_3hr = obs[1]
            
            # Calculate pressure drop rate
            pressure_drop_rate = None
            if pressure_3hr and pressure_1hr:
                pressure_drop_rate = (pressure_3hr - pressure_1hr) / 2.0  # inHg per hour
            
            # Store correlation
            cursor.execute('''
                INSERT INTO alert_correlations
                (alert_time, alert_type, pressure_1hr_before, pressure_2hr_before,
                 pressure_3hr_before, temp_1hr_before, humidity_1hr_before,
                 wind_speed_1hr_before, pressure_drop_rate, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.isoformat(), alert_type, pressure_1hr, pressure_2hr,
                pressure_3hr, temp_1hr, humidity_1hr, wind_1hr,
                pressure_drop_rate, datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Correlated {alert_type} with station data")
            if pressure_drop_rate:
                print(f"   Pressure drop rate: {pressure_drop_rate:.3f} inHg/hour")
            
        except Exception as e:
            print(f"⚠️ Error correlating alert: {e}")
    
    def get_current_trends(self) -> Optional[Dict]:
        """Analyze current trends from recent observations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 3 hours of data
            three_hours_ago = (datetime.now() - timedelta(hours=3)).isoformat()
            
            cursor.execute('''
                SELECT timestamp, temperature, humidity, pressure, wind_speed
                FROM observations
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (three_hours_ago,))
            
            observations = cursor.fetchall()
            conn.close()
            
            if len(observations) < 12:  # Need at least 1 hour of data
                return None
            
            # Calculate trends
            trends = {}
            
            # Pressure trend (most important!)
            pressures = [obs[3] for obs in observations if obs[3] is not None]
            if len(pressures) >= 12:
                pressure_3hr_ago = pressures[0]
                pressure_now = pressures[-1]
                pressure_change = pressure_now - pressure_3hr_ago
                pressure_rate = pressure_change / 3.0  # inHg per hour
                
                trends['pressure_change'] = pressure_change
                trends['pressure_rate'] = pressure_rate
                trends['pressure_current'] = pressure_now
                
                # Categorize pressure trend
                if pressure_rate < -0.06:
                    trends['pressure_trend'] = 'rapidly_falling'
                elif pressure_rate < -0.03:
                    trends['pressure_trend'] = 'falling'
                elif pressure_rate > 0.06:
                    trends['pressure_trend'] = 'rapidly_rising'
                elif pressure_rate > 0.03:
                    trends['pressure_trend'] = 'rising'
                else:
                    trends['pressure_trend'] = 'steady'
            
            # Temperature trend
            temps = [obs[1] for obs in observations if obs[1] is not None]
            if len(temps) >= 12:
                temp_3hr_ago = temps[0]
                temp_now = temps[-1]
                temp_change = temp_now - temp_3hr_ago
                
                trends['temp_change'] = temp_change
                trends['temp_current'] = temp_now
            
            # Humidity trend
            humidity = [obs[2] for obs in observations if obs[2] is not None]
            if len(humidity) >= 12:
                humidity_3hr_ago = humidity[0]
                humidity_now = humidity[-1]
                humidity_change = humidity_now - humidity_3hr_ago
                
                trends['humidity_change'] = humidity_change
                trends['humidity_current'] = humidity_now
            
            # Wind trend
            winds = [obs[4] for obs in observations if obs[4] is not None]
            if len(winds) >= 12:
                wind_3hr_ago = winds[0]
                wind_now = winds[-1]
                
                trends['wind_change'] = wind_now - wind_3hr_ago
                trends['wind_current'] = wind_now
            
            return trends
            
        except Exception as e:
            print(f"⚠️ Error analyzing trends: {e}")
            return None
    
    def predict_severe_weather(self) -> Optional[Dict]:
        """Predict severe weather based on current trends and historical patterns"""
        try:
            trends = self.get_current_trends()
            
            if not trends:
                return None
            
            # Check for severe weather indicators
            indicators = []
            confidence = 0
            
            # Rapidly falling pressure (strongest indicator)
            if trends.get('pressure_trend') == 'rapidly_falling':
                indicators.append('rapidly falling pressure')
                confidence += 40
            elif trends.get('pressure_trend') == 'falling':
                indicators.append('falling pressure')
                confidence += 20
            
            # Rising humidity
            if trends.get('humidity_change', 0) > 10:
                indicators.append('rapidly increasing humidity')
                confidence += 15
            
            # Increasing winds
            if trends.get('wind_change', 0) > 5:
                indicators.append('increasing winds')
                confidence += 10
            
            # Temperature changes (cold front or warm front)
            temp_change = trends.get('temp_change', 0)
            if temp_change < -5:
                indicators.append('rapid temperature drop')
                confidence += 10
            elif temp_change > 5:
                indicators.append('rapid temperature rise')
                confidence += 5
            
            # Check historical correlations
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # How often did similar pressure drops lead to alerts?
            if trends.get('pressure_rate'):
                cursor.execute('''
                    SELECT COUNT(*) FROM alert_correlations
                    WHERE alert_type LIKE '%Severe%'
                    AND pressure_drop_rate < ?
                ''', (trends['pressure_rate'] * 1.2,))  # Similar or worse drop
                
                similar_events = cursor.fetchone()[0]
                
                if similar_events > 0:
                    indicators.append(f'{similar_events} similar events in history')
                    confidence += min(similar_events * 5, 20)  # Max 20 points from history
            
            conn.close()
            
            # Generate prediction if confidence is high enough
            if confidence >= 30:
                return {
                    'confidence': min(confidence, 95),  # Cap at 95%
                    'indicators': indicators,
                    'trends': trends,
                    'timeframe': '2-4 hours'
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error predicting severe weather: {e}")
            return None
    
    def get_prediction_announcement(self) -> Optional[str]:
        """Generate announcement for severe weather prediction"""
        try:
            prediction = self.predict_severe_weather()
            
            if not prediction:
                return None
            
            confidence = prediction['confidence']
            indicators = prediction['indicators']
            timeframe = prediction['timeframe']
            
            # Build announcement based on confidence
            if confidence >= 70:
                urgency = "Severe weather is likely"
            elif confidence >= 50:
                urgency = "Conditions favor severe weather development"
            else:
                urgency = "Conditions are becoming favorable for severe weather"
            
            # Format indicators
            indicator_text = ", ".join(indicators[:3])  # Top 3 indicators
            
            announcement = (
                f"{urgency} within the next {timeframe}. "
                f"Our weather station shows {indicator_text}. "
                f"Confidence: {confidence}%. Monitor conditions closely."
            )
            
            return announcement
            
        except Exception as e:
            print(f"⚠️ Error generating prediction announcement: {e}")
            return None


# Singleton instance
_predictor = None

def get_personal_ml() -> PersonalStationML:
    """Get or create ML predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = PersonalStationML()
    return _predictor


def record_station_observation(conditions: Dict) -> None:
    """Record observation from personal station"""
    predictor = get_personal_ml()
    predictor.record_observation(conditions)


def correlate_alert_with_station(alert_type: str) -> None:
    """Correlate alert with recent station data"""
    predictor = get_personal_ml()
    predictor.correlate_alert(alert_type)


def get_severe_weather_prediction() -> Optional[str]:
    """Get severe weather prediction announcement"""
    predictor = get_personal_ml()
    return predictor.get_prediction_announcement()


if __name__ == '__main__':
    # Test the system
    print("=" * 70)
    print("PERSONAL STATION ML PREDICTION SYSTEM TEST")
    print("=" * 70)
    
    ml = PersonalStationML()
    
    # Simulate some observations
    print("\n1. Simulating observations...")
    from datetime import datetime
    import random
    
    base_pressure = 29.92
    for i in range(36):  # 3 hours of 5-minute observations
        conditions = {
            'temperature': 75 - (i * 0.1),  # Slow temp drop
            'humidity': 60 + (i * 0.5),  # Rising humidity
            'pressure': base_pressure - (i * 0.01),  # Falling pressure
            'wind_speed': 5 + (i * 0.2),  # Increasing wind
            'wind_direction': 'South'
        }
        ml.record_observation(conditions)
    
    print(f"✓ Recorded 36 observations")
    
    print("\n2. Analyzing trends...")
    trends = ml.get_current_trends()
    if trends:
        print(f"✓ Pressure trend: {trends.get('pressure_trend')}")
        print(f"   Pressure change: {trends.get('pressure_change'):.2f} inHg")
        print(f"   Temperature change: {trends.get('temp_change'):.1f}°F")
    
    print("\n3. Testing prediction...")
    prediction = ml.predict_severe_weather()
    if prediction:
        print(f"✓ Prediction confidence: {prediction['confidence']}%")
        print(f"   Indicators: {', '.join(prediction['indicators'])}")
    
    print("\n4. Testing announcement...")
    announcement = ml.get_prediction_announcement()
    if announcement:
        print(f"✓ Announcement:")
        print(f"   {announcement}")
    else:
        print("⚠️ No prediction (confidence too low)")
    
    print("\n" + "=" * 70)
