"""
auto_fix_ml.py - Automatically fixes ML model on startup
Detects incompatible models and retrains automatically
"""

import os
import pickle
from datetime import datetime

def check_and_fix_model(model_path='/data/weather_model.pkl'):
    """
    Check if ML model is compatible, delete if not
    Returns: True if model is good/fixed, False if needs training
    """
    
    if not os.path.exists(model_path):
        print("ℹ️ No ML model found - will train new one")
        return False
    
    try:
        # Try to load the model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Check if it's the right structure
        if isinstance(model_data, dict):
            model = model_data.get('model')
            expected_features = model_data.get('expected_features', 0)
            
            # Check if features match (should be 10 now)
            if expected_features == 10:
                print(f"✅ ML model valid ({expected_features} features)")
                return True
            else:
                print(f"⚠️ ML model has {expected_features} features, need 10")
                print("🔧 Deleting incompatible model...")
                os.remove(model_path)
                print("✅ Old model deleted - will train new one")
                return False
        else:
            print("⚠️ ML model has old format")
            print("🔧 Deleting old format model...")
            os.remove(model_path)
            print("✅ Old model deleted - will train new one")
            return False
            
    except Exception as e:
        print(f"⚠️ Error loading ML model: {e}")
        print("🔧 Deleting corrupted model...")
        try:
            os.remove(model_path)
            print("✅ Corrupted model deleted - will train new one")
        except:
            print("⚠️ Could not delete model file")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("ML MODEL AUTO-FIX")
    print("=" * 70)
    check_and_fix_model()
    print("=" * 70)
