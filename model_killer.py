"""
model_killer.py - ULTRA-NUCLEAR MODEL DESTROYER
Continuously hunts and kills incompatible ML models
"""

import os
import time
import threading
import pickle

MODEL_PATH = '/data/weather_model.pkl'
KILL_INTERVAL = 10  # Check every 10 seconds
RUNNING = True

def is_model_incompatible():
    """Check if model exists and is incompatible"""
    if not os.path.exists(MODEL_PATH):
        return False
    
    try:
        with open(MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        
        if isinstance(model_data, dict):
            expected_features = model_data.get('expected_features', 0)
            if expected_features == 10:
                # Model is good!
                return False
            else:
                # Model has wrong feature count
                return True
        else:
            # Old format model
            return True
    except:
        # Corrupted or unreadable
        return True

def kill_incompatible_model():
    """Delete the model if it's incompatible"""
    if not os.path.exists(MODEL_PATH):
        return False
    
    if is_model_incompatible():
        try:
            size = os.path.getsize(MODEL_PATH)
            os.remove(MODEL_PATH)
            print(f"💀 MODEL KILLER: Deleted incompatible model ({size:,} bytes)")
            return True
        except Exception as e:
            print(f"⚠️ MODEL KILLER: Failed to delete: {e}")
            return False
    else:
        print(f"✅ MODEL KILLER: Model is compatible (10 features) - standing down")
        return False

def model_killer_loop():
    """Background loop that continuously hunts for bad models"""
    global RUNNING
    
    print("=" * 70)
    print("🔥 MODEL KILLER: Active and hunting...")
    print("=" * 70)
    
    consecutive_good = 0
    
    while RUNNING:
        try:
            # Check if model exists and is bad
            if os.path.exists(MODEL_PATH):
                if is_model_incompatible():
                    print(f"\n🚨 MODEL KILLER: Found incompatible model!")
                    if kill_incompatible_model():
                        consecutive_good = 0
                        print("💀 MODEL KILLER: Threat eliminated. Continuing patrol...")
                else:
                    consecutive_good += 1
                    if consecutive_good == 1:
                        print(f"\n✅ MODEL KILLER: Compatible model detected!")
                        print("✅ MODEL KILLER: Mission accomplished - standing down")
                        RUNNING = False
                        break
            
            time.sleep(KILL_INTERVAL)
            
        except Exception as e:
            print(f"⚠️ MODEL KILLER: Error in patrol: {e}")
            time.sleep(KILL_INTERVAL)
    
    print("\n" + "=" * 70)
    print("✅ MODEL KILLER: Terminated - compatible model is safe")
    print("=" * 70 + "\n")

def start_model_killer():
    """Start the background model killer thread"""
    global RUNNING
    RUNNING = True
    
    # Initial check and kill
    if os.path.exists(MODEL_PATH):
        print(f"\n🔍 MODEL KILLER: Found existing model on startup")
        if is_model_incompatible():
            print(f"💀 MODEL KILLER: Model is incompatible - destroying...")
            kill_incompatible_model()
    
    # Start background thread
    killer_thread = threading.Thread(target=model_killer_loop, daemon=True)
    killer_thread.start()
    print("🔥 MODEL KILLER: Background patrol started")

def stop_model_killer():
    """Stop the model killer"""
    global RUNNING
    RUNNING = False
