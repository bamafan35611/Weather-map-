import os
import glob
import pickle
import threading
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
from ml_bridge import get_ml_predictions  # Fetch ML from local PC

# Import local prediction capability
try:
    from local_predictor import generate_local_predictions
    LOCAL_PREDICTOR_AVAILABLE = True
    print("✓ Local predictor loaded")
except ImportError as e:
    print(f"⚠ Local predictor not available: {e}")
    LOCAL_PREDICTOR_AVAILABLE = False
    generate_local_predictions = None

# Import forecast tracking system
try:
    from forecast_db import (
        save_forecast, 
        get_forecast_history, 
        get_accuracy_stats,
        format_history_for_frontend
    )
    from verification_service import verify_forecasts
    from auto_retrain import auto_retrain
    FORECAST_SYSTEM_AVAILABLE = True
    print("✓ Forecast tracking system loaded")
except ImportError as e:
    print(f"⚠ Forecast system not available: {e}")
    FORECAST_SYSTEM_AVAILABLE = False
    auto_retrain = None

app = Flask(__name__, static_folder='static')
CORS(app)

_model = None
_model_path = None

# ----------------------------------------------------------------------
# Load ML model (optional)
# ----------------------------------------------------------------------
def _load_model_once():
    global _model, _model_path
    if _model is not None:
        return _model
    candidates = sorted(glob.glob(os.path.join('models', '*.pkl')))
    if not candidates:
        return None
    _model_path = candidates[0]
    try:
        with open(_model_path, 'rb') as f:
            _model = pickle.load(f)
    except Exception:
        _model = None
    return _model

# ----------------------------------------------------------------------
# Core routes
# ----------------------------------------------------------------------
@app.get('/')
def root():
    # ✅ Serve your main weather map file
    return send_from_directory(app.static_folder, 'RadarMap-optimized.html')

@app.route('/favicon.ico')
def favicon():
    # ✅ Prevent annoying favicon 404s
    return Response(status=204)

# ----------------------------------------------------------------------
# API endpoints
# ----------------------------------------------------------------------
@app.get('/api/test')
def api_test():
    return jsonify({'ok': True})

@app.get('/api/weather/alerts')
def api_alerts():
    # You can merge NWS + custom alerts here
    return jsonify({'alerts': []})

@app.get('/api/outlooks')
def api_outlooks():
    """Return current SPC convective outlook polygons (categorical) as simple JSON
    the front-end already understands. No fake/demo boxes."""
    import os, requests

    # Choose outlook day (1, 2, or 3). Default Day 1.
    day = int(os.environ.get("SPC_OUTLOOK_DAY", "1"))
    if day not in (1, 2, 3):
        day = 1

    # Map day -> categorical layer id on NOAA MapServer
    layer_ids = {1: 1, 2: 9, 3: 17}
    layer_id = layer_ids[day]

    base_url = "https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/MapServer"
    url = f"{base_url}/{layer_id}/query"
    params = {
        "where": "1=1",
        "outFields": "label,dn,valid,expire",
        "f": "geojson",
        "returnGeometry": "true"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        gj = r.json()
    except Exception as e:
        return jsonify({"outlooks": [], "error": str(e)}), 200

    def map_label_to_code(label: str) -> str:
        lab = (label or "").strip().upper()
        if lab.startswith("THUNDER"): return "MRGL"
        if lab.startswith("MARGINAL"): return "MRGL"
        if lab.startswith("SLIGHT"): return "SLGT"
        if lab.startswith("ENHANCED"): return "ENH"
        if lab.startswith("MODERATE"): return "MDT"
        if lab.startswith("HIGH"): return "HIGH"
        return "MRGL"

    out = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        label = props.get("label") or ""
        risk_code = map_label_to_code(label)

        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        rings = None
        if gtype == "Polygon" and coords:
            rings = coords[0]
        elif gtype == "MultiPolygon" and coords and coords[0]:
            rings = coords[0][0]
        if not rings or len(rings) < 3:
            continue

        out.append({
            "type": "convective",
            "risk_level": risk_code,
            "probability": "",
            "description": props.get("label") or "",
            "day": day,
            "polygon": rings
        })

    return jsonify({"outlooks": out})
@app.get('/api/learning/history')
def api_history():
    """Return verified forecast history"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({'count': 0, 'history': [], 'message': 'Forecast system initializing...'})
    
    try:
        # Get verified forecasts
        forecasts = get_forecast_history(limit=50)
        
        # Format for frontend
        history = format_history_for_frontend(forecasts)
        
        # Get accuracy stats
        stats = get_accuracy_stats(days=30)
        
        return jsonify({
            'count': len(history),
            'history': history,
            'stats': stats,
            'success': True
        })
    except Exception as e:
        print(f"Error in history endpoint: {e}")
        return jsonify({
            'count': 0,
            'history': [],
            'error': str(e),
            'success': False
        })

@app.get('/api/ml/predictions')
def api_predictions():
    """Fetch ML predictions from local PC via ngrok"""
    data = get_ml_predictions()
    
    if data.get('success'):
        # Save predictions to database for later verification
        if FORECAST_SYSTEM_AVAILABLE and data.get('predictions'):
            try:
                for pred in data['predictions']:
                    forecast_data = {
                        'timestamp': pred.get('timestamp'),
                        'forecast_for': pred.get('valid_time'),
                        'location': pred.get('location', 'Unknown'),
                        'latitude': pred.get('lat'),
                        'longitude': pred.get('lon'),
                        'prediction_type': pred.get('type', 'weather_event'),
                        'predicted_severity': pred.get('severity', 'moderate'),
                        'confidence': pred.get('confidence', 0.0),
                        'details': pred
                    }
                    save_forecast(forecast_data)
                print(f"✓ Saved {len(data['predictions'])} predictions to database")
            except Exception as e:
                print(f"⚠ Could not save predictions: {e}")
        
        return jsonify(data)
    else:
        # Return error but don't break frontend
        return jsonify(data), 200

@app.route('/api/ml/predictions/local', methods=['POST'])
def api_local_predictions():
    """Generate predictions using local model from NWS alerts"""
    if not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Local predictor not available'
        }), 503
    
    try:
        # Generate predictions
        predictions = generate_local_predictions()
        
        # Save to database
        if FORECAST_SYSTEM_AVAILABLE and predictions:
            for pred in predictions:
                save_forecast(pred)
            print(f"✓ Saved {len(predictions)} local predictions to database")
        
        return jsonify({
            'success': True,
            'count': len(predictions),
            'predictions': predictions,
            'message': f'Generated {len(predictions)} predictions from NWS alerts'
        })
    
    except Exception as e:
        print(f"Error generating local predictions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.post('/api/learning/forecast')
def api_save_forecast():
    """Manually save a forecast prediction"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({'success': False, 'error': 'Forecast system not available'}), 503
    
    try:
        forecast_data = request.get_json()
        forecast_id = save_forecast(forecast_data)
        return jsonify({'success': True, 'forecast_id': forecast_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/learning/verify')
def api_verify_forecasts():
    """Manually trigger forecast verification"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({'success': False, 'error': 'Forecast system not available'}), 503
    
    try:
        # Run verification in background thread
        thread = threading.Thread(target=verify_forecasts)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Verification started in background'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/learning/stats')
def api_accuracy_stats():
    """Get accuracy statistics"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({'success': False, 'error': 'Forecast system not available'}), 503
    
    try:
        stats = get_accuracy_stats(days=30)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/learning/retrain')
def api_retrain_model():
    """Manually trigger model retraining"""
    if not FORECAST_SYSTEM_AVAILABLE or auto_retrain is None:
        return jsonify({'success': False, 'error': 'Retraining not available'}), 503
    
    try:
        # Run retraining in background thread
        def retrain_worker():
            success = auto_retrain()
            print(f"Retraining {'completed' if success else 'skipped'}")
        
        thread = threading.Thread(target=retrain_worker)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Model retraining started in background'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/learning/retrain/status')
def api_retrain_status():
    """Get retraining history and status"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({'success': False, 'error': 'Retraining not available'}), 503
    
    try:
        import json
        retrain_log_path = 'models/retrain_log.json'
        
        if os.path.exists(retrain_log_path):
            with open(retrain_log_path, 'r') as f:
                history = json.load(f)
            
            return jsonify({
                'success': True,
                'retrain_count': len(history),
                'history': history[-5:],  # Last 5 retrains
                'last_retrain': history[-1] if history else None
            })
        else:
            return jsonify({
                'success': True,
                'retrain_count': 0,
                'history': [],
                'last_retrain': None,
                'message': 'No retraining has occurred yet'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/ml/status')
def api_ml_status():
    """Check if local ML connection is configured"""
    local_ml_url = os.environ.get('LOCAL_ML_URL', '')
    
    return jsonify({
        'configured': bool(local_ml_url),
        'url': local_ml_url if local_ml_url else 'Not set',
        'message': 'Local ML is configured' if local_ml_url else 'Set LOCAL_ML_URL in Render environment variables'
    })

# ----------------------------------------------------------------------
# Catch-all so OBS and browser routing never 404
# ----------------------------------------------------------------------
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(app.static_folder, 'RadarMap-optimized.html')

# ----------------------------------------------------------------------
# Background verification task
# ----------------------------------------------------------------------
def start_verification_loop():
    """Start background verification task"""
    if not FORECAST_SYSTEM_AVAILABLE:
        print("⚠ Forecast system not available - skipping verification loop")
        return
    
    def verification_worker():
        import time
        print("🔍 Starting background verification and retraining loop...")
        time.sleep(60)  # Wait 1 minute before first check
        
        check_count = 0
        while True:
            try:
                # Generate local predictions from NWS alerts
                if LOCAL_PREDICTOR_AVAILABLE:
                    try:
                        predictions = generate_local_predictions()
                        if FORECAST_SYSTEM_AVAILABLE and predictions:
                            for pred in predictions:
                                save_forecast(pred)
                            print(f"✓ Generated and saved {len(predictions)} local predictions")
                    except Exception as e:
                        print(f"⚠ Error generating local predictions: {e}")
                
                # Run verification every cycle
                verify_forecasts()
                check_count += 1
                
                # Run retraining every 24 checks (12 hours if checking every 30 min)
                if check_count % 24 == 0 and auto_retrain is not None:
                    print("\n🤖 Automatic retraining check...")
                    auto_retrain()
                
            except Exception as e:
                print(f"⚠ Error in verification loop: {e}")
            
            # Check every 30 minutes
            time.sleep(1800)
    
    thread = threading.Thread(target=verification_worker)
    thread.daemon = True
    thread.start()
    print("✓ Background verification and retraining loop started")

# ----------------------------------------------------------------------
# Start background loop (for gunicorn)
# ----------------------------------------------------------------------
# Start the loop when the module loads (works with gunicorn)
start_verification_loop()

# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
