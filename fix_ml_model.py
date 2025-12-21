"""
fix_ml_model.py - Fix ML Model Feature Mismatch
This script retrains the model with the correct number of features
"""

import os
import pickle
import numpy as np
from datetime import datetime

def fix_ml_model():
    """Fix the ML model feature mismatch"""
    
    model_path = '/data/weather_model.pkl'
    
    print("=" * 70)
    print("ML MODEL FIX SCRIPT")
    print("=" * 70)
    
    # Check if model exists
    if not os.path.exists(model_path):
        print("✓ No existing model found - will be created on first prediction")
        return
    
    print(f"\n⚠️  Found existing model at: {model_path}")
    
    # Try to load and inspect it
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        print(f"Model type: {type(model)}")
        
        # Check if it's a RandomForestClassifier
        if hasattr(model, 'n_features_in_'):
            print(f"Model expects {model.n_features_in_} features")
            print(f"Current code provides 10 features")
            print()
            print("🔧 SOLUTION: Deleting old model...")
            
            # Backup the old model
            backup_path = f'{model_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.rename(model_path, backup_path)
            print(f"✓ Old model backed up to: {backup_path}")
            print(f"✓ Model will be retrained on next prediction")
            print()
            print("✅ FIX COMPLETE!")
            print("The bot will automatically train a new model with correct features.")
            
        else:
            print("⚠️  Cannot determine model features")
            print("Deleting model to force retrain...")
            os.remove(model_path)
            print("✓ Model deleted - will retrain automatically")
    
    except Exception as e:
        print(f"Error inspecting model: {e}")
        print("Deleting model to be safe...")
        try:
            os.remove(model_path)
            print("✓ Model deleted - will retrain automatically")
        except Exception as e2:
            print(f"Could not delete model: {e2}")
    
    print("=" * 70)


if __name__ == '__main__':
    fix_ml_model()
