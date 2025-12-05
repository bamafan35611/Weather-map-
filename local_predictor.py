"""
local_predictor.py - Generate predictions using the local model on Render
This makes predictions directly from NWS alerts without needing the PC connection
"""

import pickle
import numpy as np
from datetime import datetime, timedelta
import requests
import json

MODEL_PATH = 'models/forecast_model.pkl'

class LocalPredictor:
    """Generate predictions using the model on Render"""
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model"""
        try:
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ Loaded model from {MODEL_PATH}")
            return True
        except Exception as e:
            print(f"⚠ Could not load model: {e}")
            return False
    
    def fetch_active_alerts(self):
        """Fetch current NWS weather alerts"""
        try:
            # Try primary API first
            url = 'https://api.weather.gov/alerts/active'
            headers = {'User-Agent': 'AtmosphericX/1.0 (Weather Learning System)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                geometry = feature.get('geometry')
                
                # Only process severe weather alerts
                event = (props.get('event') or '').lower()
                if any(keyword in event for keyword in ['tornado', 'severe', 'flood', 'wind', 'thunderstorm']):
                    alert = {
                        'id': props.get('id'),
                        'event': props.get('event'),
                        'severity': props.get('severity'),
                        'urgency': props.get('urgency'),
                        'areaDesc': props.get('areaDesc'),
                        'onset': props.get('onset'),
                        'expires': props.get('expires'),
                        'description': props.get('description'),
                        'geometry': geometry
                    }
                    alerts.append(alert)
            
            return alerts
        except requests.exceptions.ProxyError:
            print("⚠️ NWS API blocked by proxy - system will retry on next cycle")
            return []
        except Exception as e:
            print(f"⚠️ Error fetching alerts: {e}")
            return []
    
    def alert_to_features(self, alert):
        """Convert NWS alert to model features"""
        try:
            # Prediction type encoding
            event = (alert.get('event') or '').lower()
            if 'tornado' in event:
                pred_type = 0
            elif 'severe thunderstorm' in event or 'thunderstorm' in event:
                pred_type = 1
            elif 'flood' in event:
                pred_type = 2
            elif 'winter' in event or 'blizzard' in event:
                pred_type = 3
            elif 'wind' in event:
                pred_type = 4
            else:
                pred_type = 5
            
            # Severity encoding
            severity = (alert.get('severity') or '').lower()
            if severity == 'minor':
                sev_enc = 0
            elif severity == 'moderate':
                sev_enc = 1
            elif severity == 'severe':
                sev_enc = 2
            elif severity == 'extreme':
                sev_enc = 3
            else:
                sev_enc = 1  # Default moderate
            
            # Confidence based on urgency/certainty
            urgency = (alert.get('urgency') or '').lower()
            if urgency in ['immediate', 'expected']:
                confidence = 0.8
            elif urgency == 'future':
                confidence = 0.6
            else:
                confidence = 0.5
            
            # Location features (approximate from area description)
            # For now, use US center as default
            lat = 39.0  # Approximate US center
            lon = -98.0
            
            # Time features
            now = datetime.utcnow()
            hour_norm = now.hour / 24.0
            weekday_norm = now.weekday() / 7.0
            
            # Weather features (estimates based on alert type)
            if 'tornado' in event or 'severe' in event:
                temp = 75.0 / 100.0
                humidity = 70.0 / 100.0
                wind = 40.0 / 100.0
            elif 'flood' in event:
                temp = 70.0 / 100.0
                humidity = 90.0 / 100.0
                wind = 20.0 / 100.0
            else:
                temp = 70.0 / 100.0
                humidity = 60.0 / 100.0
                wind = 30.0 / 100.0
            
            # Build feature vector (must match training data format)
            features = [
                pred_type,      # 0: Prediction type
                sev_enc,        # 1: Severity
                confidence,     # 2: Confidence
                lat,            # 3: Latitude
                lon,            # 4: Longitude
                hour_norm,      # 5: Hour of day
                weekday_norm,   # 6: Day of week
                temp,           # 7: Temperature
                humidity,       # 8: Humidity
                wind            # 9: Wind speed
            ]
            
            return features
            
        except Exception as e:
            print(f"Error converting alert to features: {e}")
            return None
    
    def predict_from_alert(self, alert):
        """Generate prediction from NWS alert"""
        if not self.model:
            return None
        
        features = self.alert_to_features(alert)
        if features is None:
            return None
        
        try:
            # Make prediction
            X = np.array([features])
            prediction = self.model.predict(X)[0]
            
            # Get probability if available
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                confidence = float(max(proba)) * 100
            else:
                confidence = 70.0
            
            # Map prediction to type
            type_map = {
                0: 'tornado',
                1: 'severe_thunderstorm',
                2: 'flash_flood',
                3: 'winter_storm',
                4: 'wind'
            }
            
            severity_map = {
                0: 'minor',
                1: 'moderate',
                2: 'severe',
                3: 'extreme'
            }
            
            event = alert.get('event', 'Unknown')
            location = alert.get('areaDesc', 'Unknown')
            
            # Extract prediction type from features
            pred_type_code = int(features[0])
            pred_type = type_map.get(pred_type_code, 'weather_event')
            
            # Extract severity from features
            sev_code = int(features[1])
            pred_severity = severity_map.get(sev_code, 'moderate')
            
            # Build prediction object
            onset = alert.get('onset')
            if onset:
                try:
                    valid_time = datetime.fromisoformat(onset.replace('Z', '+00:00'))
                except:
                    valid_time = datetime.utcnow() + timedelta(hours=1)
            else:
                valid_time = datetime.utcnow() + timedelta(hours=1)
            
            prediction_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'forecast_for': valid_time.isoformat(),
                'location': location,
                'latitude': features[3],  # From features
                'longitude': features[4],  # From features
                'prediction_type': pred_type,
                'predicted_severity': pred_severity,
                'confidence': confidence,
                'details': {
                    'source': 'local_model',
                    'nws_event': event,
                    'nws_alert_id': alert.get('id'),
                    'model_prediction': int(prediction),
                    'temperature': features[7] * 100,
                    'humidity': features[8] * 100,
                    'wind_speed': features[9] * 100
                }
            }
            
            return prediction_data
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return None
    
    def generate_predictions(self):
        """Generate predictions from current alerts"""
        if not self.model:
            print("⚠ Model not loaded")
            return []
        
        # Fetch active alerts
        alerts = self.fetch_active_alerts()
        
        if not alerts:
            print("No active severe weather alerts")
            return []
        
        print(f"Processing {len(alerts)} active alerts...")
        
        predictions = []
        for alert in alerts:
            pred = self.predict_from_alert(alert)
            if pred:
                predictions.append(pred)
        
        print(f"✓ Generated {len(predictions)} predictions")
        return predictions

# Singleton instance
_predictor = None

def get_predictor():
    """Get or create predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = LocalPredictor()
    return _predictor

def generate_local_predictions():
    """Main function to generate predictions"""
    predictor = get_predictor()
    return predictor.generate_predictions()
