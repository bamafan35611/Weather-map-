"""
pre_alert_predictor.py - NorthBamaWX Pre-Alert Prediction System
Predicts severe weather alerts 5-15 minutes before NWS issues them
"""

import requests
import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PreAlertPredictor:
    """Predicts alerts before they're officially issued"""
    
    def __init__(self, model_path='models/forecast_model.pkl'):
        self.model = None
        self.load_model(model_path)
        self.active_predictions = []  # Track our predictions
        self.prediction_history = []  # Track accuracy
        
    def load_model(self, model_path):
        """Load the trained ML model"""
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info("✓ Pre-alert model loaded")
        except Exception as e:
            logger.error(f"Could not load model: {e}")
    
    def fetch_current_conditions(self, lat: float, lon: float) -> Dict:
        """Fetch current atmospheric conditions from NWS"""
        try:
            # Get nearest weather station
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            headers = {'User-Agent': 'NorthBamaWX/1.0 (Pre-Alert System)'}
            
            response = requests.get(points_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return {}
            
            data = response.json()
            properties = data.get('properties', {})
            
            # Get observation station
            stations_url = properties.get('observationStations')
            if not stations_url:
                return {}
            
            stations_response = requests.get(stations_url, headers=headers, timeout=10)
            if stations_response.status_code != 200:
                return {}
            
            stations_data = stations_response.json()
            features = stations_data.get('features', [])
            if not features:
                return {}
            
            # Get latest observation from first station
            station_url = features[0].get('id')
            obs_url = f"{station_url}/observations/latest"
            
            obs_response = requests.get(obs_url, headers=headers, timeout=10)
            if obs_response.status_code != 200:
                return {}
            
            obs_data = obs_response.json()
            obs_props = obs_data.get('properties', {})
            
            # Extract key atmospheric parameters
            conditions = {
                'temperature': self._celsius_to_fahrenheit(obs_props.get('temperature', {}).get('value')),
                'dewpoint': self._celsius_to_fahrenheit(obs_props.get('dewpoint', {}).get('value')),
                'humidity': obs_props.get('relativeHumidity', {}).get('value', 50),
                'pressure': obs_props.get('barometricPressure', {}).get('value', 101325),
                'wind_speed': self._mps_to_mph(obs_props.get('windSpeed', {}).get('value')),
                'wind_direction': obs_props.get('windDirection', {}).get('value', 0),
                'wind_gust': self._mps_to_mph(obs_props.get('windGust', {}).get('value')),
                'visibility': obs_props.get('visibility', {}).get('value', 10000),
                'timestamp': obs_props.get('timestamp', datetime.utcnow().isoformat())
            }
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error fetching conditions: {e}")
            return {}
    
    def _celsius_to_fahrenheit(self, celsius):
        """Convert Celsius to Fahrenheit"""
        if celsius is None:
            return 70.0
        return (celsius * 9/5) + 32
    
    def _mps_to_mph(self, mps):
        """Convert meters per second to miles per hour"""
        if mps is None:
            return 0.0
        return mps * 2.237
    
    def analyze_radar_trends(self, lat: float, lon: float) -> Dict:
        """Analyze radar data for developing storms"""
        # This is a simplified version - in production, you'd analyze actual radar data
        # For now, we'll use the current conditions as a proxy
        
        conditions = self.fetch_current_conditions(lat, lon)
        
        if not conditions:
            return {'developing': False, 'confidence': 0}
        
        # Calculate instability indicators
        temp = conditions.get('temperature', 70)
        dewpoint = conditions.get('dewpoint', 50)
        wind_speed = conditions.get('wind_speed', 0)
        wind_gust = conditions.get('wind_gust', 0)
        
        # Simple indicators of severe weather potential
        indicators = {
            'temperature_dewpoint_spread': abs(temp - dewpoint),
            'high_winds': wind_speed > 20 or wind_gust > 30,
            'rapid_wind_increase': (wind_gust - wind_speed) > 15,
            'unstable_atmosphere': temp > 75 and dewpoint > 65
        }
        
        # Score the conditions
        score = 0
        if indicators['temperature_dewpoint_spread'] < 5:  # High humidity
            score += 20
        if indicators['high_winds']:
            score += 25
        if indicators['rapid_wind_increase']:
            score += 30
        if indicators['unstable_atmosphere']:
            score += 25
        
        return {
            'developing': score > 40,
            'confidence': min(score, 100),
            'indicators': indicators,
            'conditions': conditions
        }
    
    def predict_alert_probability(self, lat: float, lon: float, area_desc: str) -> Optional[Dict]:
        """Main prediction function - predicts if alert will be issued soon"""
        
        if not self.model:
            return None
        
        try:
            # Analyze current conditions
            radar_analysis = self.analyze_radar_trends(lat, lon)
            
            if not radar_analysis['developing']:
                return None  # No threatening weather developing
            
            conditions = radar_analysis['conditions']
            
            # Prepare features for ML model
            # Model expects: [pred_type, severity, confidence, lat, lon, hour, weekday, temp, humidity, wind]
            now = datetime.utcnow()
            
            features = [
                1,  # Default to severe thunderstorm type
                2,  # Assume severe severity
                radar_analysis['confidence'] / 100.0,
                lat,
                lon,
                now.hour / 24.0,
                now.weekday() / 7.0,
                conditions.get('temperature', 75) / 100.0,
                conditions.get('humidity', 60) / 100.0,
                conditions.get('wind_speed', 20) / 100.0
            ]
            
            # Run through model
            X = np.array([features])
            
            # Get probability
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                alert_probability = float(proba[1]) * 100  # Probability of severe weather
            else:
                prediction = self.model.predict(X)[0]
                alert_probability = 75.0 if prediction == 1 else 25.0
            
            # Combine ML probability with radar analysis confidence
            final_confidence = (alert_probability + radar_analysis['confidence']) / 2
            
            # Only issue prediction if confidence is high enough
            if final_confidence < 70:
                return None
            
            # Determine alert type based on conditions
            alert_type = self._determine_alert_type(conditions, radar_analysis['indicators'])
            
            prediction = {
                'type': 'pre_alert_prediction',
                'alert_type': alert_type,
                'location': area_desc,
                'latitude': lat,
                'longitude': lon,
                'confidence': round(final_confidence, 1),
                'time_until_alert': '5-15 minutes',
                'conditions': conditions,
                'indicators': radar_analysis['indicators'],
                'timestamp': datetime.utcnow().isoformat(),
                'predicted_at': datetime.utcnow(),
                'verified': False
            }
            
            # Store prediction for verification
            self.active_predictions.append(prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return None
    
    def _determine_alert_type(self, conditions: Dict, indicators: Dict) -> str:
        """Determine most likely alert type based on conditions"""
        
        wind_speed = conditions.get('wind_speed', 0)
        wind_gust = conditions.get('wind_gust', 0)
        temp = conditions.get('temperature', 70)
        dewpoint = conditions.get('dewpoint', 50)
        
        # Tornado conditions
        if indicators.get('rapid_wind_increase') and temp > 70 and dewpoint > 60:
            return 'Tornado Warning'
        
        # High wind conditions
        if wind_gust > 50:
            return 'Severe Thunderstorm Warning'
        
        # Flash flood conditions
        if indicators.get('temperature_dewpoint_spread', 10) < 3:
            return 'Flash Flood Warning'
        
        # Default to severe thunderstorm
        return 'Severe Thunderstorm Warning'
    
    def scan_for_developing_weather(self) -> List[Dict]:
        """Scan high-risk areas for developing severe weather"""
        
        # Priority areas to monitor - Strategic nationwide coverage (20 cities)
        priority_areas = [
            # Southeast
            {'lat': 34.7304, 'lon': -86.5861, 'name': 'Huntsville, AL'},
            {'lat': 34.6059, 'lon': -86.9833, 'name': 'Decatur, AL'},
            {'lat': 33.7490, 'lon': -84.3880, 'name': 'Atlanta, GA'},
            {'lat': 36.1627, 'lon': -86.7816, 'name': 'Nashville, TN'},
            
            # Plains (Tornado Alley)
            {'lat': 35.4676, 'lon': -97.5164, 'name': 'Oklahoma City, OK'},
            {'lat': 37.6872, 'lon': -97.3301, 'name': 'Wichita, KS'},
            {'lat': 41.2565, 'lon': -95.9345, 'name': 'Omaha, NE'},
            
            # Midwest
            {'lat': 41.8781, 'lon': -87.6298, 'name': 'Chicago, IL'},
            {'lat': 39.7392, 'lon': -104.9903, 'name': 'Denver, CO'},
            {'lat': 38.6270, 'lon': -90.1994, 'name': 'St. Louis, MO'},
            
            # Texas
            {'lat': 32.7157, 'lon': -97.3307, 'name': 'Fort Worth, TX'},
            {'lat': 29.7604, 'lon': -95.3698, 'name': 'Houston, TX'},
            
            # Northeast
            {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York, NY'},
            {'lat': 42.3601, 'lon': -71.0589, 'name': 'Boston, MA'},
            
            # Mid-Atlantic
            {'lat': 38.9072, 'lon': -77.0369, 'name': 'Washington, DC'},
            
            # Southwest
            {'lat': 33.4484, 'lon': -112.0740, 'name': 'Phoenix, AZ'},
            {'lat': 36.1699, 'lon': -115.1398, 'name': 'Las Vegas, NV'},
            
            # West Coast
            {'lat': 34.0522, 'lon': -118.2437, 'name': 'Los Angeles, CA'},
            {'lat': 47.6062, 'lon': -122.3321, 'name': 'Seattle, WA'},
            
            # Florida
            {'lat': 25.7617, 'lon': -80.1918, 'name': 'Miami, FL'},
        ]
        
        predictions = []
        
        for area in priority_areas:
            prediction = self.predict_alert_probability(
                area['lat'], 
                area['lon'], 
                area['name']
            )
            
            if prediction:
                predictions.append(prediction)
                logger.info(f"🚨 PRE-ALERT: {prediction['alert_type']} predicted for {area['name']} "
                          f"with {prediction['confidence']}% confidence")
        
        return predictions
    
    def verify_predictions(self, current_alerts: List[Dict]) -> Dict:
        """Verify if our predictions were correct against actual NWS alerts"""
        
        stats = {
            'total_predictions': len(self.active_predictions),
            'correct': 0,
            'false_alarms': 0,
            'time_advantage': []
        }
        
        current_time = datetime.utcnow()
        
        for prediction in self.active_predictions:
            if prediction.get('verified'):
                continue
            
            predicted_at = prediction['predicted_at']
            time_elapsed = (current_time - predicted_at).total_seconds() / 60  # minutes
            
            # Only verify predictions that are 5-20 minutes old
            if time_elapsed < 5 or time_elapsed > 20:
                continue
            
            # Check if a matching alert was issued
            predicted_type = prediction['alert_type'].lower()
            predicted_location = prediction['location']
            
            match_found = False
            for alert in current_alerts:
                alert_event = alert.get('event', '').lower()
                alert_area = alert.get('areaDesc', '').lower()
                
                # Check for type match
                type_match = any(word in alert_event for word in predicted_type.split())
                
                # Check for location match (loose matching)
                location_match = any(word in alert_area for word in predicted_location.lower().split(',')[0].split())
                
                if type_match and location_match:
                    match_found = True
                    stats['correct'] += 1
                    stats['time_advantage'].append(time_elapsed)
                    prediction['verified'] = True
                    prediction['verification_result'] = 'correct'
                    prediction['time_advantage_minutes'] = time_elapsed
                    
                    logger.info(f"✅ VERIFIED: Predicted {predicted_type} for {predicted_location} "
                              f"{time_elapsed:.1f} minutes before NWS alert!")
                    break
            
            if not match_found and time_elapsed > 15:
                stats['false_alarms'] += 1
                prediction['verified'] = True
                prediction['verification_result'] = 'false_alarm'
                
                logger.info(f"❌ FALSE ALARM: Predicted {predicted_type} for {predicted_location} "
                          f"- no alert issued after 15 minutes")
        
        # Calculate average time advantage
        if stats['time_advantage']:
            stats['avg_time_advantage'] = sum(stats['time_advantage']) / len(stats['time_advantage'])
        else:
            stats['avg_time_advantage'] = 0
        
        # Calculate accuracy
        verified_count = stats['correct'] + stats['false_alarms']
        if verified_count > 0:
            stats['accuracy'] = (stats['correct'] / verified_count) * 100
        else:
            stats['accuracy'] = 0
        
        return stats


# Flask API integration functions
def get_pre_alert_predictions() -> List[Dict]:
    """Get current pre-alert predictions"""
    try:
        predictor = PreAlertPredictor()
        predictions = predictor.scan_for_developing_weather()
        return predictions
    except Exception as e:
        logger.error(f"Error getting pre-alert predictions: {e}")
        return []


def verify_pre_alerts(current_alerts: List[Dict]) -> Dict:
    """Verify pre-alert predictions against actual alerts"""
    try:
        predictor = PreAlertPredictor()
        stats = predictor.verify_predictions(current_alerts)
        return stats
    except Exception as e:
        logger.error(f"Error verifying pre-alerts: {e}")
        return {}


if __name__ == '__main__':
    # Test the pre-alert system
    print("=" * 60)
    print("NORTHBAMAWX PRE-ALERT PREDICTION SYSTEM TEST")
    print("=" * 60)
    
    predictor = PreAlertPredictor()
    
    print("\n🔍 Scanning for developing severe weather...\n")
    predictions = predictor.scan_for_developing_weather()
    
    if predictions:
        print(f"🚨 {len(predictions)} PRE-ALERT PREDICTIONS:\n")
        for pred in predictions:
            print(f"  Alert Type: {pred['alert_type']}")
            print(f"  Location: {pred['location']}")
            print(f"  Confidence: {pred['confidence']}%")
            print(f"  Time Until Alert: {pred['time_until_alert']}")
            print(f"  Conditions: Temp {pred['conditions']['temperature']:.1f}°F, "
                  f"Wind {pred['conditions']['wind_speed']:.1f} mph")
            print()
    else:
        print("✓ No severe weather currently developing in monitored areas")
        print("  System is monitoring conditions every 2 minutes...")
