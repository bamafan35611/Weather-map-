import os
import glob
import pickle
import threading
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
from ml_bridge import get_ml_predictions  # Fetch ML from local PC

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

# ----------------------------------------------------------------------
# National weather summary API (Lower 48, NWS-based)
# ----------------------------------------------------------------------
import requests as _requests
import datetime as _dt

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"


def _national_safe_get(url: str, timeout: int = 8):
    try:
        resp = _requests.get(url, timeout=timeout, headers={"User-Agent": "NorthBamaWX NationalBot"})
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[national] Failed to fetch {url}: {exc}")
        return None


def _fetch_nws_national_alerts():
    """Fetch active NWS alerts across the US and return GeoJSON features list."""
    params = {
        "status": "actual",
        "message_type": "alert"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    data = _national_safe_get(f"{NWS_ALERTS_URL}?{query}")
    if not data:
        return []
    return data.get("features", [])


def _categorize_national_alert(alert):
    """Simplified national categorization for headlines."""
    props = (alert or {}).get("properties", {}) or {}
    event = (props.get("event") or "").lower()
    area_desc = (props.get("areaDesc") or "")
    severity = (props.get("severity") or "").lower()

    # Rank by hazard type – mirrors your local tier thinking
    if "tornado emergency" in event:
        hazard = "tornado_emergency"
        rank = 100
    elif "tornado warning" in event:
        hazard = "tornado_warning"
        rank = 95
    elif "severe thunderstorm warning" in event:
        hazard = "severe_thunderstorm_warning"
        rank = 85
    elif "flash flood emergency" in event:
        hazard = "flash_flood_emergency"
        rank = 90
    elif "flash flood warning" in event:
        hazard = "flash_flood_warning"
        rank = 80
    elif "winter storm warning" in event or "blizzard warning" in event:
        hazard = "winter_storm_warning"
        rank = 75
    elif "snow squall warning" in event:
        hazard = "snow_squall_warning"
        rank = 74
    elif "excessive heat warning" in event or "heat advisory" in event:
        hazard = "heat"
        rank = 70
    elif "red flag warning" in event or "fire weather" in event:
        hazard = "fire_weather"
        rank = 65
    else:
        hazard = "other"
        rank = 40

    # Rough regional labeling by state names in areaDesc
    al = area_desc.lower()
    regions = []
    if any(st in al for st in ["texas", "oklahoma", "arkansas", "louisiana"]):
        regions.append("the Southern Plains and Lower Mississippi Valley")
    if any(st in al for st in ["alabama", "mississippi", "georgia", "tennessee"]):
        regions.append("the Deep South and Tennessee Valley")
    if any(st in al for st in ["kansas", "nebraska", "iowa", "missouri"]):
        regions.append("the Central Plains and Midwest")
    if any(st in al for st in ["minnesota", "north dakota", "south dakota", "wisconsin"]):
        regions.append("the Northern Plains and Upper Midwest")
    if any(st in al for st in ["colorado", "wyoming", "montana", "idaho", "utah"]):
        regions.append("the Rockies")
    if any(st in al for st in ["california", "oregon", "washington", "nevada"]):
        regions.append("the West Coast and Sierra")
    if any(st in al for st in ["new york", "pennsylvania", "new jersey", "massachusetts", "maine", "vermont", "connecticut", "rhode island", "new hampshire"]):
        regions.append("the Northeast")
    if any(st in al for st in ["florida", "south carolina", "north carolina", "virginia"]):
        regions.append("the Southeast and Atlantic Coast")

    if not regions:
        regions.append("parts of the country")

    return {
        "event": props.get("event") or "",
        "hazard_type": hazard,
        "rank": rank,
        "regions": list(dict.fromkeys(regions)),
        "area_desc": area_desc,
        "severity": severity or "unknown"
    }


def _build_national_headlines(features):
    if not features:
        return []

    processed = [_categorize_national_alert(a) for a in features]
    processed.sort(key=lambda x: x["rank"], reverse=True)

    headlines = []
    seen_hazards = set()

    for item in processed:
        htype = item["hazard_type"]
        if htype in seen_hazards:
            continue
        seen_hazards.add(htype)

        summary = ""
        regions = ", ".join(item["regions"])

        if htype == "tornado_emergency":
            summary = f"Tornado emergencies are in effect across {regions}"
        elif htype == "tornado_warning":
            summary = f"Tornado warnings continue for parts of {regions}"
        elif htype == "severe_thunderstorm_warning":
            summary = f"Severe thunderstorm warnings are in place across {regions}"
        elif htype == "flash_flood_emergency":
            summary = f"Flash flood emergencies are ongoing in {regions}"
        elif htype == "flash_flood_warning":
            summary = f"Flash flood warnings are active in {regions}"
        elif htype == "winter_storm_warning":
            summary = f"Significant winter weather is impacting {regions}"
        elif htype == "snow_squall_warning":
            summary = f"Snow squall warnings are in effect for portions of {regions}"
        elif htype == "heat":
            summary = f"Dangerous heat is affecting portions of {regions}"
        elif htype == "fire_weather":
            summary = f"Critical fire weather conditions are present across {regions}"
        else:
            ev = item["event"] or "A weather alert"
            summary = f"{ev} is in effect for {regions}"

        headlines.append({
            "severity": item["severity"],
            "hazard_type": htype,
            "regions": item["regions"],
            "cities": [],
            "summary": summary
        })

        if len(headlines) >= 5:
            break

    return headlines


def _build_top_of_hour_script(headlines):
    now_ct = _dt.datetime.now(_dt.timezone.utc).astimezone()
    time_str = now_ct.strftime("%-I:%M %p").lstrip('0')
    parts = [f"It's {time_str} Central. Here's a national weather update for the Lower 48."]

    if not headlines:
        parts.append("Overall, conditions are relatively quiet across the country. No major hazard areas are highlighted at this time.")
        return " ".join(parts)

    for h in headlines:
        parts.append(h["summary"] + ".")

    return " ".join(parts)


@app.get('/api/national/summary')
def api_national_summary():
    """Return a national top-of-hour script + headline items for your bot to read."""
    features = _fetch_nws_national_alerts()
    headlines = _build_national_headlines(features)
    script = _build_top_of_hour_script(headlines)

    payload = {
        "generated_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "top_of_hour_script": script,
        "headline_items": headlines,
        "breaking_script": None
    }
    return jsonify(payload)


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
# Entrypoint
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Start verification loop
    start_verification_loop()
    
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
