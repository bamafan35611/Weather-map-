"""
auto_retrain.py - Automatic model retraining system
Retrains ML model based on verified forecast data
"""

import os
import pickle
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import json

try:
    from forecast_db import get_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠ Database module not available")

# Minimum verified forecasts needed before retraining
MIN_FORECASTS_FOR_RETRAIN = 20

# Model configuration
MODEL_PATH = 'models/forecast_model.pkl'
MODEL_BACKUP_PATH = 'models/forecast_model_backup.pkl'
RETRAIN_LOG_PATH = 'models/retrain_log.json'

class ModelRetrainer:
    """Handles automatic model retraining"""
    
    def __init__(self):
        self.model = None
        self.retrain_history = self.load_retrain_log()
    
    def load_current_model(self):
        """Load the current model"""
        try:
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ Loaded current model from {MODEL_PATH}")
            return True
        except Exception as e:
            print(f"⚠ Could not load model: {e}")
            return False
    
    def load_retrain_log(self):
        """Load retraining history"""
        try:
            if os.path.exists(RETRAIN_LOG_PATH):
                with open(RETRAIN_LOG_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠ Could not load retrain log: {e}")
        return []
    
    def save_retrain_log(self):
        """Save retraining history"""
        try:
            os.makedirs(os.path.dirname(RETRAIN_LOG_PATH), exist_ok=True)
            with open(RETRAIN_LOG_PATH, 'w') as f:
                json.dump(self.retrain_history, f, indent=2)
        except Exception as e:
            print(f"⚠ Could not save retrain log: {e}")
    
    def fetch_verified_forecasts(self):
        """Fetch all verified forecasts from database"""
        if not DB_AVAILABLE:
            print("⚠ Database not available")
            return []
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Get all verified forecasts with features
                cursor.execute('''
                    SELECT 
                        prediction_type,
                        predicted_severity,
                        confidence,
                        verification_result,
                        details,
                        latitude,
                        longitude,
                        timestamp,
                        forecast_for
                    FROM forecasts 
                    WHERE verified = 1
                    ORDER BY timestamp ASC
                ''')
                
                rows = cursor.fetchall()
                forecasts = [dict(row) for row in rows]
                
                print(f"✓ Fetched {len(forecasts)} verified forecasts")
                return forecasts
        except Exception as e:
            print(f"⚠ Error fetching forecasts: {e}")
            return []
    
    def prepare_training_data(self, forecasts):
        """Convert verified forecasts into training features and labels"""
        X = []  # Features
        y = []  # Labels (1 = correct, 0 = incorrect)
        
        for forecast in forecasts:
            try:
                # Extract features
                details = json.loads(forecast.get('details', '{}')) if isinstance(forecast.get('details'), str) else forecast.get('details', {})
                
                # Create feature vector
                features = []
                
                # Prediction type encoding
                pred_type = forecast.get('prediction_type', 'unknown')
                type_encoding = {
                    'tornado': 0,
                    'severe_thunderstorm': 1,
                    'flash_flood': 2,
                    'winter_storm': 3,
                    'wind': 4
                }
                features.append(type_encoding.get(pred_type, 5))
                
                # Severity encoding
                severity = forecast.get('predicted_severity', 'moderate')
                severity_encoding = {
                    'minor': 0,
                    'moderate': 1,
                    'severe': 2,
                    'extreme': 3
                }
                features.append(severity_encoding.get(severity, 1))
                
                # Confidence
                confidence = forecast.get('confidence', 50.0)
                features.append(confidence / 100.0)  # Normalize to 0-1
                
                # Location features
                lat = forecast.get('latitude', 0.0) or 0.0
                lon = forecast.get('longitude', 0.0) or 0.0
                features.append(lat)
                features.append(lon)
                
                # Time features (hour of day, day of week)
                try:
                    timestamp = forecast.get('timestamp')
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    features.append(dt.hour / 24.0)  # Normalize
                    features.append(dt.weekday() / 7.0)  # Normalize
                except:
                    features.append(0.5)  # Default
                    features.append(0.5)  # Default
                
                # Additional features from details
                features.append(details.get('temperature', 70.0) / 100.0)  # Normalized temp
                features.append(details.get('humidity', 50.0) / 100.0)  # Normalized humidity
                features.append(details.get('wind_speed', 10.0) / 100.0)  # Normalized wind
                
                X.append(features)
                
                # Label: 1 if correct, 0 if false positive/negative
                result = forecast.get('verification_result')
                y.append(1 if result == 'correct' else 0)
                
            except Exception as e:
                print(f"⚠ Error processing forecast: {e}")
                continue
        
        return np.array(X), np.array(y)
    
    def should_retrain(self, num_forecasts):
        """Determine if retraining is needed"""
        if num_forecasts < MIN_FORECASTS_FOR_RETRAIN:
            print(f"⚠ Not enough data: {num_forecasts}/{MIN_FORECASTS_FOR_RETRAIN} forecasts")
            return False
        
        # Check when last retrain happened
        if self.retrain_history:
            last_retrain = self.retrain_history[-1]
            last_date = datetime.fromisoformat(last_retrain['timestamp'])
            days_since = (datetime.utcnow() - last_date).days
            
            if days_since < 7:
                print(f"⚠ Last retrain was {days_since} days ago - waiting for 7 days")
                return False
        
        return True
    
    def backup_current_model(self):
        """Backup current model before retraining"""
        try:
            if os.path.exists(MODEL_PATH):
                os.makedirs(os.path.dirname(MODEL_BACKUP_PATH), exist_ok=True)
                with open(MODEL_PATH, 'rb') as src:
                    with open(MODEL_BACKUP_PATH, 'wb') as dst:
                        dst.write(src.read())
                print(f"✓ Backed up current model to {MODEL_BACKUP_PATH}")
                return True
        except Exception as e:
            print(f"⚠ Could not backup model: {e}")
            return False
    
    def train_new_model(self, X, y):
        """Train a new model on the data"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"✓ Model trained:")
            print(f"  - Training accuracy: {train_score:.2%}")
            print(f"  - Testing accuracy: {test_score:.2%}")
            print(f"  - Overall accuracy: {accuracy:.2%}")
            
            return model, {
                'train_accuracy': float(train_score),
                'test_accuracy': float(test_score),
                'overall_accuracy': float(accuracy),
                'num_samples': len(X)
            }
        
        except Exception as e:
            print(f"⚠ Error training model: {e}")
            return None, None
    
    def save_new_model(self, model):
        """Save the newly trained model"""
        try:
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(model, f)
            print(f"✓ Saved new model to {MODEL_PATH}")
            return True
        except Exception as e:
            print(f"⚠ Could not save model: {e}")
            return False
    
    def retrain(self):
        """Main retraining function"""
        print("\n🔄 Starting automatic model retraining...")
        
        # Fetch verified forecasts
        forecasts = self.fetch_verified_forecasts()
        
        if not forecasts:
            print("⚠ No verified forecasts available")
            return False
        
        # Check if retraining is needed
        if not self.should_retrain(len(forecasts)):
            return False
        
        print(f"✓ Proceeding with retrain on {len(forecasts)} verified forecasts")
        
        # Prepare training data
        X, y = self.prepare_training_data(forecasts)
        
        if len(X) == 0:
            print("⚠ No valid training data")
            return False
        
        print(f"✓ Prepared {len(X)} training samples")
        
        # Backup current model
        self.backup_current_model()
        
        # Train new model
        new_model, metrics = self.train_new_model(X, y)
        
        if new_model is None:
            print("⚠ Training failed")
            return False
        
        # Save new model
        if not self.save_new_model(new_model):
            print("⚠ Could not save new model")
            return False
        
        # Log the retrain
        retrain_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'num_forecasts': len(forecasts),
            'num_samples': len(X),
            'metrics': metrics
        }
        
        self.retrain_history.append(retrain_entry)
        self.save_retrain_log()
        
        print(f"\n✅ RETRAIN COMPLETE!")
        print(f"   - New model accuracy: {metrics['overall_accuracy']:.2%}")
        print(f"   - Trained on {len(X)} samples")
        print(f"   - Model saved to {MODEL_PATH}")
        
        return True

def auto_retrain():
    """Run automatic retraining"""
    retrainer = ModelRetrainer()
    return retrainer.retrain()

if __name__ == '__main__':
    # Run retraining
    success = auto_retrain()
    
    if success:
        print("\n🎉 Model successfully retrained and deployed!")
    else:
        print("\n⏸ Retraining skipped or failed")
