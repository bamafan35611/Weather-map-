print("=" * 80)
print("🚨 APP.PY STARTING - FORCING MODULE RELOAD")
print("=" * 80)

# Force reload of local_predictor
import sys
if 'local_predictor' in sys.modules:
    del sys.modules['local_predictor']

import local_predictor
print(f"✓ local_predictor loaded from: {local_predictor.__file__}")

import requests
import os
import glob
import pickle
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS

# Import ML bridge (optional - for external ML predictions)
try:
    from ml_bridge import get_ml_predictions
    ML_BRIDGE_AVAILABLE = True
    print("✓ ML bridge loaded (external predictions)")
except ImportError:
    ML_BRIDGE_AVAILABLE = False
    get_ml_predictions = None
    print("⚠ ML bridge not available (optional - using local predictions)")

# Import local prediction capability
try:
    from local_predictor import generate_local_predictions, LocalPredictor
    LOCAL_PREDICTOR_AVAILABLE = True
    print("✓ Local predictor loaded")
except ImportError as e:
    print(f"⚠ Local predictor not available: {e}")
    LOCAL_PREDICTOR_AVAILABLE = False
    generate_local_predictions = None
    LocalPredictor = None

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
    save_forecast = None
    get_forecast_history = None
    get_accuracy_stats = None
    verify_forecasts = None
    auto_retrain = None

# Import new features: Pre-Alert Predictor and Severity Scorer
try:
    from pre_alert_predictor import PreAlertPredictor, get_pre_alert_predictions, verify_pre_alerts
    PRE_ALERT_AVAILABLE = True
    print("✓ Pre-alert prediction system loaded")
except ImportError as e:
    print(f"⚠ Pre-alert system not available: {e}")
    PRE_ALERT_AVAILABLE = False
    PreAlertPredictor = None

try:
    from severity_scorer import SeverityScorer, score_alert, score_all_alerts, get_threat_announcement
    SEVERITY_SCORER_AVAILABLE = True
    print("✓ Severity scoring system loaded")
except ImportError as e:
    print(f"⚠ Severity scorer not available: {e}")
    SEVERITY_SCORER_AVAILABLE = False
    SeverityScorer = None

# Import voice styles system
try:
    from voice_styles import VoiceStyleManager, get_announcement_for_alert, get_announcement_for_pre_alert, get_ssml_for_text
    VOICE_STYLES_AVAILABLE = True
    print("✓ Voice styles system loaded")
except ImportError as e:
    print(f"⚠ Voice styles not available: {e}")
    VOICE_STYLES_AVAILABLE = False
    VoiceStyleManager = None

# Import social media poster
try:
    from social_media_poster import SocialMediaPoster, post_alert_to_social_media, post_pre_alert_to_social_media, post_stats_to_social_media
    SOCIAL_MEDIA_AVAILABLE = True
    print("✓ Social media poster loaded")
except ImportError as e:
    print(f"⚠ Social media poster not available: {e}")
    SOCIAL_MEDIA_AVAILABLE = False
    SocialMediaPoster = None

# Import weather commentary system
try:
    from weather_commentary import WeatherCommentary, get_national_briefing, get_regional_briefing, get_hourly_update, get_weather_story
    COMMENTARY_AVAILABLE = True
    print("✓ Weather commentary system loaded - Regional briefing enabled")
except ImportError as e:
    print(f"⚠ Weather commentary not available: {e}")
    COMMENTARY_AVAILABLE = False
    WeatherCommentary = None

# Import NWS forecast fetcher (fixes the "stormy weather on clear days" issue)
try:
    from nws_forecast_fetcher import (
        get_athens_forecast, 
        get_forecast_fetcher, 
        NWSForecastFetcher,
        get_athens_briefing_with_conditions,
        get_athens_current_conditions,
        get_city_briefing_with_conditions
    )
    FORECAST_FETCHER_AVAILABLE = True
    print("✓ NWS forecast fetcher loaded - Athens, AL forecasts with current conditions enabled")
except ImportError as e:
    print(f"⚠ Forecast fetcher not available: {e}")
    FORECAST_FETCHER_AVAILABLE = False
    get_athens_forecast = None
    get_forecast_fetcher = None
    get_athens_briefing_with_conditions = None
    get_athens_current_conditions = None
    get_city_briefing_with_conditions = None

# Import local cities database
try:
    from local_cities import get_random_city, format_city_location
    LOCAL_CITIES_AVAILABLE = True
    print("✓ Local cities database loaded - Random city briefings enabled")
except ImportError as e:
    print(f"⚠ Local cities database not available: {e}")
    LOCAL_CITIES_AVAILABLE = False
    get_random_city = None
    format_city_location = None

# ----------------------------------------------------------------------
# 🆕 ALERT ANNOUNCEMENT COOLDOWN SYSTEM
# ----------------------------------------------------------------------

# COOLDOWN CONFIGURATION
ENABLE_ALERT_COOLDOWN = True  # Set to False to announce ALL alerts every time (for testing)

class AlertAnnouncementManager:
    """Prevents alert spam by tracking announcements and applying cooldowns"""
    
    def __init__(self):
        self.announced_alerts = {}  # alert_id: last_announcement_time
        self.alert_hashes = {}  # alert_id: content_hash (detect updates)
        
        # Configuration
        self.INITIAL_COOLDOWN = 0  # Announce new alerts immediately
        self.REPEAT_COOLDOWN = 1800  # 30 minutes before re-announcing
        self.UPDATE_COOLDOWN = 300  # 5 minutes after update announcement
        
        print("✓ Alert announcement manager initialized")
        if not ENABLE_ALERT_COOLDOWN:
            print("⚠️  COOLDOWN DISABLED - All alerts will be announced every time!")
    
    def should_announce(self, alert):
        """Determine if an alert should be announced"""
        # If cooldown disabled, always announce
        if not ENABLE_ALERT_COOLDOWN:
            return True
        
        alert_id = alert.get('id')
        if not alert_id:
            return False
        
        current_time = datetime.now()
        
        # Check if this is a new alert (never announced)
        if alert_id not in self.announced_alerts:
            print(f"✓ New alert detected: {alert.get('event')}")
            self.announced_alerts[alert_id] = current_time
            self.alert_hashes[alert_id] = self._hash_alert(alert)
            return True
        
        # Check if alert content changed (update)
        current_hash = self._hash_alert(alert)
        if current_hash != self.alert_hashes.get(alert_id):
            time_since_last = (current_time - self.announced_alerts[alert_id]).total_seconds()
            if time_since_last >= self.UPDATE_COOLDOWN:
                print(f"✓ Alert updated: {alert.get('event')}")
                self.announced_alerts[alert_id] = current_time
                self.alert_hashes[alert_id] = current_hash
                return True
            else:
                print(f"⏸ Update too recent, skipping: {alert.get('event')}")
                return False
        
        # Check if enough time passed for re-announcement
        time_since_last = (current_time - self.announced_alerts[alert_id]).total_seconds()
        if time_since_last >= self.REPEAT_COOLDOWN:
            print(f"✓ Re-announcing (30+ min passed): {alert.get('event')}")
            self.announced_alerts[alert_id] = current_time
            return True
        
        # Otherwise skip (too recent)
        minutes_left = int((self.REPEAT_COOLDOWN - time_since_last) / 60)
        print(f"⏸ Skipping repeat announcement ({minutes_left} min until next): {alert.get('event')}")
        return False
    
    def _hash_alert(self, alert):
        """Create hash of alert content to detect changes"""
        # Combine key fields that would indicate an update
        content = f"{alert.get('event')}|{alert.get('severity')}|{alert.get('description', '')[:100]}"
        return hash(content)
    
    def cleanup_expired(self, active_alert_ids):
        """Remove tracking for expired alerts"""
        current_ids = set(active_alert_ids)
        expired = [aid for aid in self.announced_alerts.keys() if aid not in current_ids]
        
        for alert_id in expired:
            del self.announced_alerts[alert_id]
            if alert_id in self.alert_hashes:
                del self.alert_hashes[alert_id]
        
        if expired:
            print(f"🗑️ Cleaned up {len(expired)} expired alert(s)")

# Global alert manager instance
alert_manager = AlertAnnouncementManager()

app = Flask(__name__, static_folder='static')

# Enable CORS for all routes and origins
# This allows the map to load from anywhere (Render, local file, OBS, etc.)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

print("✓ CORS enabled for all API routes")

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

@app.get('/api/debug/routes')
def debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': str(rule.rule)
        })
    return jsonify({
        'total_routes': len(routes),
        'routes': sorted(routes, key=lambda x: x['path']),
        'local_predictor_available': LOCAL_PREDICTOR_AVAILABLE,
        'forecast_system_available': FORECAST_SYSTEM_AVAILABLE
    })

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
    if not ML_BRIDGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'ML bridge not available - external predictions disabled',
            'message': 'Use /api/ml/predictions/local for local predictions'
        }), 503
    
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

@app.route('/api/ml/predictions/local', methods=['GET', 'POST'])
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
# Learning System Endpoints (SQLite)
# ----------------------------------------------------------------------
@app.get('/api/ml/history')
def api_ml_history():
    """Get forecast history - shows what bot has learned"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Learning system not available - forecast_db.py not loaded'
        }), 503
    
    try:
        limit = request.args.get('limit', 100, type=int)
        location = request.args.get('location', None, type=str)
        
        history = get_forecast_history(limit=limit, location=location)
        formatted = format_history_for_frontend(history)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': formatted,
            'message': f'Retrieved {len(history)} forecast records'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.get('/api/ml/accuracy')
def api_ml_accuracy():
    """Get learning accuracy statistics"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Learning system not available - forecast_db.py not loaded'
        }), 503
    
    try:
        days = request.args.get('days', 30, type=int)
        stats = get_accuracy_stats(days=days)
        
        return jsonify({
            'success': True,
            'period_days': days,
            **stats,
            'message': f'Accuracy stats for last {days} days'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.get('/api/ml/learning-status')
def api_learning_status():
    """Get overall learning status - is bot getting smarter?"""
    if not FORECAST_SYSTEM_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Learning system not available',
            'learning': False
        })
    
    try:
        stats = get_accuracy_stats(days=30)
        history = get_forecast_history(limit=10)
        
        total = stats.get('total_forecasts', 0)
        verified = stats.get('verified_count', 0)
        accuracy = stats.get('avg_accuracy', 0)
        improving = stats.get('improving', False)
        
        # Determine learning stage
        if total == 0:
            stage = 'WAITING FOR DATA'
            message = 'Bot is ready to start learning from weather events'
        elif total < 10:
            stage = 'GATHERING DATA'
            message = f'Early stage: {total}/100 forecasts collected'
        elif total < 100:
            stage = 'LEARNING PATTERNS'
            message = f'Building knowledge: {total}/100 forecasts for baseline'
        elif total < 500:
            stage = 'IMPROVING ACCURACY'
            message = f'Getting smarter: {total} forecasts analyzed'
        else:
            stage = 'EXPERT LEVEL'
            message = f'Highly trained: {total} forecasts analyzed'
        
        return jsonify({
            'success': True,
            'learning': True,
            'stage': stage,
            'message': message,
            'total_forecasts': total,
            'verified_forecasts': verified,
            'current_accuracy': f"{accuracy*100:.1f}%" if accuracy else "N/A",
            'improving': improving,
            'recent_predictions': len(history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'learning': False
        }), 500

# ----------------------------------------------------------------------
# Pre-Alert Prediction System Endpoints
# ----------------------------------------------------------------------
@app.get('/api/pre-alerts')
def api_pre_alerts():
    """Get current pre-alert predictions"""
    if not PRE_ALERT_AVAILABLE:
        return jsonify({'success': False, 'error': 'Pre-alert system not available'}), 503
    
    try:
        predictions = get_pre_alert_predictions()
        return jsonify({
            'success': True,
            'count': len(predictions),
            'predictions': predictions,
            'message': f'NorthBamaWX monitoring {len(predictions)} developing situations'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/pre-alerts/stats')
def api_pre_alert_stats():
    """Get pre-alert verification statistics"""
    if not PRE_ALERT_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Pre-alert verification not available'}), 503
    
    try:
        # Get current alerts for verification
        predictor = LocalPredictor()
        current_alerts = predictor.fetch_active_alerts()
        
        # Verify predictions
        stats = verify_pre_alerts(current_alerts)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'Pre-alert accuracy: {stats.get("accuracy", 0):.1f}%'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------------------------------------------------------
# Severity Scoring System Endpoints
# ----------------------------------------------------------------------
@app.get('/api/alerts/scored')
def api_scored_alerts():
    """Get all alerts with threat scores"""
    if not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Severity scoring not available'}), 503
    
    try:
        # Fetch active alerts
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        
        # Score all alerts
        scored = score_all_alerts(alerts)
        
        # Get highest threat
        highest = scored[0] if scored else None
        highest_score = highest['threat_score']['score'] if highest else 0
        
        return jsonify({
            'success': True,
            'count': len(scored),
            'alerts': scored,
            'highest_threat': highest_score,
            'highest_alert': highest,
            'message': f'{len(scored)} alerts, highest threat: {highest_score}/100'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/alerts/<alert_id>/score')
def api_alert_score(alert_id):
    """Get threat score for specific alert"""
    if not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Severity scoring not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        
        # Find the alert
        alert = next((a for a in alerts if a.get('id') == alert_id), None)
        if not alert:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        score_data = score_alert(alert)
        announcement = get_threat_announcement(alert)
        
        return jsonify({
            'success': True,
            'alert': alert,
            'score': score_data,
            'announcement': announcement
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/threat/current')
def api_current_threat():
    """Get current highest threat level"""
    if not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Threat scoring not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        
        if not alerts:
            return jsonify({
                'success': True,
                'threat_score': 0,
                'threat_level': 'NO THREATS',
                'color': '#00FF00',
                'action': 'System monitoring - no threats detected',
                'active_alerts': 0
            })
        
        scored = score_all_alerts(alerts)
        highest = scored[0]
        
        return jsonify({
            'success': True,
            'threat_score': highest['threat_score']['score'],
            'threat_level': highest['threat_score']['threat_level'],
            'color': highest['threat_score']['color'],
            'action': highest['threat_score']['action'],
            'alert_type': highest.get('event'),
            'location': highest.get('areaDesc'),
            'active_alerts': len(alerts)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------------------------------------------------------
# Voice Styles System Endpoints
# ----------------------------------------------------------------------
@app.get('/api/voice/announcement/<alert_id>')
def api_voice_announcement(alert_id):
    """Get voice announcement for specific alert with dynamic styling"""
    if not VOICE_STYLES_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Voice system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        
        # Find the alert
        alert = next((a for a in alerts if a.get('id') == alert_id), None)
        if not alert:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        # Get threat score
        score_data = score_alert(alert)
        threat_score = score_data['score']
        
        # Generate voice announcement
        announcement = get_announcement_for_alert(alert, threat_score)
        
        return jsonify({
            'success': True,
            'announcement': announcement,
            'alert': alert,
            'threat_score': threat_score
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/voice/announcements/all')
def api_voice_announcements_all():
    """Get voice announcements for all active alerts, sorted by threat"""
    if not VOICE_STYLES_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Voice system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        
        if not alerts:
            return jsonify({
                'success': True,
                'count': 0,
                'announcements': [],
                'message': 'No active alerts'
            })
        
        # Score all alerts
        scored = score_all_alerts(alerts)
        
        # Generate announcements for each
        announcements = []
        for alert in scored:
            threat_score = alert['threat_score']['score']
            announcement = get_announcement_for_alert(alert, threat_score)
            announcements.append({
                'alert_id': alert.get('id'),
                'event': alert.get('event'),
                'location': alert.get('areaDesc'),
                'threat_score': threat_score,
                'voice_style': announcement['style'],
                'text': announcement['text'],
                'ssml': announcement['ssml']
            })
        
        return jsonify({
            'success': True,
            'count': len(announcements),
            'announcements': announcements,
            'highest_threat': announcements[0] if announcements else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/voice/pre-alert-announcements')
def api_voice_pre_alert_announcements():
    """Get voice announcements for pre-alerts"""
    if not VOICE_STYLES_AVAILABLE or not PRE_ALERT_AVAILABLE:
        return jsonify({'success': False, 'error': 'Voice system not available'}), 503
    
    try:
        pre_alerts = get_pre_alert_predictions()
        
        if not pre_alerts:
            return jsonify({
                'success': True,
                'count': 0,
                'announcements': [],
                'message': 'No pre-alerts active'
            })
        
        # Generate announcements for each pre-alert
        announcements = []
        for pre_alert in pre_alerts:
            announcement = get_announcement_for_pre_alert(pre_alert)
            announcements.append({
                'alert_type': pre_alert.get('alert_type'),
                'location': pre_alert.get('location'),
                'confidence': pre_alert.get('confidence'),
                'voice_style': announcement['style'],
                'text': announcement['text'],
                'ssml': announcement['ssml']
            })
        
        return jsonify({
            'success': True,
            'count': len(announcements),
            'announcements': announcements
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/voice/custom')
def api_voice_custom():
    """Generate voice SSML for custom text with threat-based styling"""
    if not VOICE_STYLES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Voice system not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text')
        threat_score = data.get('threat_score', 50)
        
        if not text:
            return jsonify({'success': False, 'error': 'Text required'}), 400
        
        ssml = get_ssml_for_text(text, threat_score)
        
        manager = VoiceStyleManager()
        style = manager.get_voice_style_for_threat(threat_score)
        
        return jsonify({
            'success': True,
            'text': text,
            'ssml': ssml,
            'voice_style': style,
            'threat_score': threat_score
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------------------------------------------------------
# Weather Commentary Endpoints
# ----------------------------------------------------------------------
@app.get('/api/commentary/regional')
def api_commentary_regional():
    """Get REGIONAL weather briefing for North Alabama & Southern Tennessee"""
    if not COMMENTARY_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Commentary system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        scored = score_all_alerts(alerts) if alerts else []
        
        briefing = get_regional_briefing(alerts, scored)
        
        return jsonify({
            'success': True,
            'commentary': briefing,
            'alert_count': len(alerts),
            'region': 'North Alabama & Southern Tennessee',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/commentary/national')
def api_commentary_national():
    """Get regional weather briefing (legacy endpoint - now returns regional data)"""
    # Keep this endpoint for backward compatibility, but return regional briefing
    if not COMMENTARY_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Commentary system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        scored = score_all_alerts(alerts) if alerts else []
        
        # Use regional briefing instead of national
        briefing = get_regional_briefing(alerts, scored)
        
        return jsonify({
            'success': True,
            'commentary': briefing,
            'alert_count': len(alerts),
            'note': 'This endpoint now returns regional briefings for North Alabama & Southern Tennessee',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/commentary/hourly')
def api_commentary_hourly():
    """Get hourly weather update"""
    if not COMMENTARY_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Commentary system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        scored = score_all_alerts(alerts) if alerts else []
        
        # Get local area from query params (default: North Alabama)
        local_area = request.args.get('local_area', 'North Alabama')
        
        update = get_hourly_update(alerts, scored, local_area)
        
        return jsonify({
            'success': True,
            'commentary': update,
            'local_area': local_area,
            'alert_count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/commentary/story')
def api_commentary_story():
    """Get weather story/narrative"""
    if not COMMENTARY_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Commentary system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        scored = score_all_alerts(alerts) if alerts else []
        
        story = get_weather_story(alerts, scored)
        
        return jsonify({
            'success': True,
            'commentary': story,
            'alert_count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/local-forecast')
def api_local_forecast():
    """Get actual NWS forecast for Athens, AL with current temperature and wind conditions"""
    if not FORECAST_FETCHER_AVAILABLE:
        return jsonify({'success': False, 'error': 'Forecast fetcher not available'}), 503
    
    try:
        fetcher = get_forecast_fetcher()
        forecast_data = fetcher.get_home_forecast()
        current_conditions = fetcher.get_athens_current_conditions()
        
        if forecast_data:
            response_data = {
                'success': True,
                'location': 'Athens, AL',
                'coordinates': '34.80°N, 86.97°W',
                'forecast': forecast_data,
                'summary': fetcher.get_short_forecast_summary(forecast_data, 3),
                'athens_broadcast': fetcher.get_athens_forecast_specifically(),
                'athens_broadcast_with_conditions': get_athens_briefing_with_conditions(),
                'severe_expected': fetcher.is_severe_weather_expected(forecast_data),
                'updated': forecast_data.get('updated'),
                'periods_count': len(forecast_data.get('periods', []))
            }
            
            # Add current conditions if available
            if current_conditions:
                response_data['current_conditions'] = current_conditions
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': 'Could not fetch forecast from NWS'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/forecast-debug')
def api_forecast_debug():
    """Debug endpoint to check forecast fetching status"""
    try:
        if not FORECAST_FETCHER_AVAILABLE:
            return jsonify({
                'status': 'ERROR',
                'message': 'Forecast fetcher module not loaded',
                'location': 'Athens, AL (34.80°N, 86.97°W)'
            }), 503
        
        fetcher = get_forecast_fetcher()
        forecast = fetcher.get_home_forecast()
        current_conditions = fetcher.get_athens_current_conditions()
        
        if forecast:
            periods = forecast.get('periods', [])
            response = {
                'status': 'OK',
                'message': 'Forecast fetching is working',
                'location': 'Athens, AL (34.80°N, 86.97°W)',
                'periods_fetched': len(periods),
                'first_period': periods[0] if periods else None,
                'updated': forecast.get('updated'),
                'current_forecast': fetcher.get_athens_forecast_specifically(),
                'forecast_with_conditions': get_athens_briefing_with_conditions()
            }
            
            if current_conditions:
                response['current_conditions'] = current_conditions
            
            return jsonify(response)
        else:
            return jsonify({
                'status': 'ERROR',
                'message': 'Could not fetch forecast from NWS API',
                'location': 'Athens, AL (34.80°N, 86.97°W)'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': f'Exception occurred: {str(e)}'
        }), 500

@app.get('/api/broadcast/scheduled')
def api_broadcast_scheduled():
    """Get the appropriate broadcast content based on current time (15-min schedule)"""
    if not COMMENTARY_AVAILABLE or not SEVERITY_SCORER_AVAILABLE or not LOCAL_PREDICTOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Broadcast system not available'}), 503
    
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        scored = score_all_alerts(alerts) if alerts else []
        
        # 🆕 CLEANUP EXPIRED ALERTS FROM TRACKING
        if alerts:
            active_ids = [a.get('id') for a in alerts if a.get('id')]
            alert_manager.cleanup_expired(active_ids)
        
        # Get current minute
        current_minute = datetime.now().minute
        local_area = request.args.get('local_area', 'North Alabama')
        
        broadcast_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'alert_count': len(alerts),
            'current_minute': current_minute,
            'broadcast_type': None,
            'content': []
        }
        
        # :00 - Regional Briefing (North Alabama & Southern Tennessee)
        if current_minute == 0:
            briefing = get_regional_briefing(alerts, scored)
            broadcast_data['broadcast_type'] = 'regional_briefing'
            broadcast_data['content'].append({
                'type': 'commentary',
                'text': briefing,
                'duration_estimate': '45-60 seconds'
            })
        
        # :15 - Top Alerts with Voice Styles (🔧 NOW WITH COOLDOWN!)
        elif current_minute == 15:
            broadcast_data['broadcast_type'] = 'top_alerts'
            
            if len(scored) > 0:
                # 🆕 FILTER ALERTS THROUGH COOLDOWN SYSTEM
                alerts_to_announce = []
                for alert in scored[:10]:  # Check top 10
                    if alert_manager.should_announce(alert):
                        alerts_to_announce.append(alert)
                
                # Announce filtered alerts
                if alerts_to_announce:
                    broadcast_data['content'].append({
                        'type': 'intro',
                        'text': 'NorthBamaWX with current weather alerts.',
                        'voice_style': 'calm'
                    })
                    
                    # Top 3 alerts with voice styling
                    for i, alert in enumerate(alerts_to_announce[:3]):
                        threat_score = alert.get('threat_score', {}).get('score', 0)
                        announcement = get_announcement_for_alert(alert, threat_score) if VOICE_STYLES_AVAILABLE else None
                        
                        if announcement:
                            broadcast_data['content'].append({
                                'type': 'alert',
                                'text': announcement['text'],
                                'voice_style': announcement['style'],
                                'threat_score': threat_score,
                                'alert_info': {
                                    'event': alert.get('event'),
                                    'location': alert.get('areaDesc')
                                }
                            })
                    
                    # 🆕 ADD WATCH CALLOUT (if any watches in top 10 weren't announced)
                    watches_in_top_10 = [a for a in alerts_to_announce[:10] if 'watch' in a.get('event', '').lower()]
                    announced_watches = [a for a in alerts_to_announce[:3] if 'watch' in a.get('event', '').lower()]
                    
                    # If there are watches that didn't make the top 3
                    if len(watches_in_top_10) > len(announced_watches):
                        unannounced_watches = [w for w in watches_in_top_10 if w not in announced_watches]
                        
                        # Focus on tornado and severe thunderstorm watches
                        important_watches = [w for w in unannounced_watches 
                                            if 'tornado' in w.get('event', '').lower() or 
                                               'severe' in w.get('event', '').lower()]
                        
                        if important_watches:
                            watch_event = important_watches[0].get('event', 'Weather Watch')
                            watch_area = important_watches[0].get('areaDesc', 'the region')
                            
                            # Simplify area description
                            if ';' in watch_area:
                                watch_area = watch_area.split(';')[0] + " and surrounding counties"
                            
                            broadcast_data['content'].append({
                                'type': 'watch_callout',
                                'text': f"Also, a {watch_event} remains in effect for {watch_area}.",
                                'voice_style': 'concerned',
                                'duration_estimate': '5 seconds'
                            })
                            print(f"✓ Added watch callout: {watch_event}")
                else:
                    # All alerts filtered by cooldown
                    print("⏸ All alerts recently announced - skipping alert broadcast")
                    broadcast_data['content'].append({
                        'type': 'status',
                        'text': 'Weather conditions continue across monitored areas. No new alerts at this time.',
                        'voice_style': 'calm'
                    })
                
                # 🆕 ADD RANDOM CITY BRIEFING AT :15 WITH FALLBACK
                if FORECAST_FETCHER_AVAILABLE and LOCAL_CITIES_AVAILABLE:
                    city_briefing = None
                    attempts = 0
                    max_city_attempts = 3  # Try up to 3 different cities
                    
                    while city_briefing is None and attempts < max_city_attempts:
                        try:
                            random_city = get_random_city()
                            print(f"🎲 Trying city {attempts + 1}/{max_city_attempts}: {random_city['name']}, {random_city['state']}")
                            
                            city_briefing = get_city_briefing_with_conditions(
                                random_city['name'],
                                random_city['lat'],
                                random_city['lon'],
                                random_city['state']
                            )
                            
                            # Check if it's an error message
                            if "temporarily unavailable" in city_briefing:
                                print(f"⚠️ {random_city['name']} forecast unavailable, trying another city...")
                                city_briefing = None
                                attempts += 1
                            else:
                                # Success!
                                broadcast_data['content'].append({
                                    'type': 'local_city_briefing',
                                    'text': city_briefing,
                                    'voice_style': 'calm',
                                    'city_info': {
                                        'name': random_city['name'],
                                        'state': random_city['state'],
                                        'county': random_city['county']
                                    },
                                    'duration_estimate': '15-20 seconds'
                                })
                                print(f"✓ Random city briefing added: {random_city['name']}, {random_city['state']}")
                                break
                        except Exception as e:
                            print(f"⚠️ Error with {random_city['name']}: {e}")
                            attempts += 1
                    
                    if city_briefing is None:
                        print(f"❌ All {max_city_attempts} city attempts failed, skipping city briefing")
                
                # Check for pre-alerts
                if PRE_ALERT_AVAILABLE:
                    pre_alerts = get_pre_alert_predictions()
                    if pre_alerts:
                        broadcast_data['content'].append({
                            'type': 'intro',
                            'text': 'And now, AI predictions from NorthBamaWX.',
                            'voice_style': 'concerned'
                        })
                        for pre_alert in pre_alerts:
                            announcement = get_announcement_for_pre_alert(pre_alert) if VOICE_STYLES_AVAILABLE else None
                            if announcement:
                                broadcast_data['content'].append({
                                    'type': 'pre_alert',
                                    'text': announcement['text'],
                                    'voice_style': announcement['style']
                                })
            else:
                # No alerts - just give city briefing
                broadcast_data['content'].append({
                    'type': 'quiet',
                    'text': 'NorthBamaWX. All clear at this time.',
                    'voice_style': 'calm'
                })
                
                # 🆕 ADD RANDOM CITY BRIEFING WHEN NO ALERTS WITH FALLBACK
                if FORECAST_FETCHER_AVAILABLE and LOCAL_CITIES_AVAILABLE:
                    city_briefing = None
                    attempts = 0
                    max_city_attempts = 3
                    
                    while city_briefing is None and attempts < max_city_attempts:
                        try:
                            random_city = get_random_city()
                            print(f"🎲 Trying city {attempts + 1}/{max_city_attempts}: {random_city['name']}, {random_city['state']}")
                            
                            city_briefing = get_city_briefing_with_conditions(
                                random_city['name'],
                                random_city['lat'],
                                random_city['lon'],
                                random_city['state']
                            )
                            
                            if "temporarily unavailable" in city_briefing:
                                print(f"⚠️ {random_city['name']} forecast unavailable, trying another city...")
                                city_briefing = None
                                attempts += 1
                            else:
                                broadcast_data['content'].append({
                                    'type': 'local_city_briefing',
                                    'text': city_briefing,
                                    'voice_style': 'calm',
                                    'city_info': {
                                        'name': random_city['name'],
                                        'state': random_city['state'],
                                        'county': random_city['county']
                                    },
                                    'duration_estimate': '15-20 seconds'
                                })
                                print(f"✓ Random city briefing added: {random_city['name']}, {random_city['state']}")
                                break
                        except Exception as e:
                            print(f"⚠️ Error with {random_city['name']}: {e}")
                            attempts += 1
                    
                    if city_briefing is None:
                        print(f"❌ All {max_city_attempts} city attempts failed, skipping city briefing")
        
        # :30 - Hourly Update WITH LOCAL FORECAST
        elif current_minute == 30:
            broadcast_data['broadcast_type'] = 'hourly_update'
            broadcast_data['local_area'] = local_area
            
            # FIRST: Get Athens, AL local forecast WITH CURRENT CONDITIONS
            if FORECAST_FETCHER_AVAILABLE:
                try:
                    local_forecast = get_athens_briefing_with_conditions()
                    broadcast_data['content'].append({
                        'type': 'local_forecast',
                        'priority': 'high',
                        'text': local_forecast,
                        'duration_estimate': '20-25 seconds'
                    })
                    print(f"✓ Local forecast with current conditions added to :30 broadcast")
                except Exception as e:
                    print(f"⚠ Error getting local forecast: {e}")
                    broadcast_data['content'].append({
                        'type': 'local_forecast',
                        'priority': 'high',
                        'text': 'Athens, Alabama local forecast temporarily unavailable.',
                        'duration_estimate': '5 seconds'
                    })
            
            # SECOND: Add alert commentary if available
            if COMMENTARY_AVAILABLE:
                update = get_hourly_update(alerts, scored, local_area)
                broadcast_data['content'].append({
                    'type': 'commentary',
                    'priority': 'medium',
                    'text': update,
                    'duration_estimate': '15-30 seconds'
                })
        
        # :45 - Weather Story
        elif current_minute == 45:
            story = get_weather_story(alerts, scored)
            broadcast_data['broadcast_type'] = 'weather_story'
            broadcast_data['content'].append({
                'type': 'commentary',
                'text': story,
                'duration_estimate': '30-60 seconds'
            })
        
        # Not a scheduled time
        else:
            broadcast_data['broadcast_type'] = 'none'
            broadcast_data['message'] = f'No scheduled broadcast at :{current_minute:02d}. Next broadcast at :{(current_minute // 15 + 1) * 15 % 60:02d}'
        
        return jsonify(broadcast_data)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        
        # Initialize pre-alert predictor if available
        pre_alert_predictor = None
        if PRE_ALERT_AVAILABLE:
            try:
                pre_alert_predictor = PreAlertPredictor()
                print("✓ Pre-alert predictor initialized in background loop")
            except Exception as e:
                print(f"⚠ Could not initialize pre-alert predictor: {e}")
        
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
                
                # Check for pre-alerts every cycle (every 2 minutes)
                if pre_alert_predictor and LOCAL_PREDICTOR_AVAILABLE:
                    try:
                        pre_alerts = pre_alert_predictor.scan_for_developing_weather()
                        if pre_alerts:
                            print(f"🚨 PRE-ALERT: {len(pre_alerts)} developing situations detected")
                            for pre_alert in pre_alerts:
                                print(f"  - {pre_alert['alert_type']} for {pre_alert['location']} "
                                      f"({pre_alert['confidence']}% confidence)")
                                
                                # Post pre-alert to social media
                                if SOCIAL_MEDIA_AVAILABLE:
                                    try:
                                        post_pre_alert_to_social_media(pre_alert)
                                    except Exception as e:
                                        print(f"⚠ Error posting pre-alert: {e}")
                    except Exception as e:
                        print(f"⚠ Error checking pre-alerts: {e}")
                
                # Check for new alerts and post high-priority ones
                if SOCIAL_MEDIA_AVAILABLE and SEVERITY_SCORER_AVAILABLE and LOCAL_PREDICTOR_AVAILABLE:
                    try:
                        predictor = LocalPredictor()
                        alerts = predictor.fetch_active_alerts()
                        if alerts:
                            scored = score_all_alerts(alerts)
                            for alert in scored[:5]:  # Top 5 threats only
                                threat_score = alert['threat_score']['score']
                                if threat_score >= 50:  # Only post elevated+ threats
                                    post_alert_to_social_media(alert, threat_score)
                    except Exception as e:
                        print(f"⚠ Error posting alerts: {e}")
                
                # Verify pre-alerts against actual alerts every 5 cycles (10 minutes)
                if pre_alert_predictor and check_count % 5 == 0 and LOCAL_PREDICTOR_AVAILABLE:
                    try:
                        predictor = LocalPredictor()
                        current_alerts = predictor.fetch_active_alerts()
                        stats = pre_alert_predictor.verify_predictions(current_alerts)
                        if stats.get('correct', 0) > 0 or stats.get('false_alarms', 0) > 0:
                            print(f"✅ Pre-alert verification: {stats['correct']} correct, "
                                  f"{stats['false_alarms']} false alarms, "
                                  f"avg {stats.get('avg_time_advantage', 0):.1f} min lead time")
                            
                            # Post verification success if we got predictions right
                            if SOCIAL_MEDIA_AVAILABLE and stats.get('correct', 0) > 0:
                                try:
                                    from social_media_poster import post_stats_to_social_media
                                    poster = SocialMediaPoster()
                                    poster.post_verification(stats)
                                except Exception as e:
                                    print(f"⚠ Error posting verification: {e}")
                    except Exception as e:
                        print(f"⚠ Error verifying pre-alerts: {e}")
                
                # Post daily stats once per day (check every 12 hours)
                if SOCIAL_MEDIA_AVAILABLE and check_count % 360 == 0:
                    try:
                        # Gather stats
                        accuracy_stats = get_accuracy_stats() if FORECAST_SYSTEM_AVAILABLE else {}
                        predictor = LocalPredictor() if LOCAL_PREDICTOR_AVAILABLE else None
                        alerts = predictor.fetch_active_alerts() if predictor else []
                        
                        daily_stats = {
                            'alerts_monitored': len(alerts),
                            'pre_alerts_issued': len(pre_alert_predictor.predictions) if pre_alert_predictor else 0,
                            'accuracy': accuracy_stats.get('accuracy_pct', 0),
                            'avg_lead_time': 0,  # Would calculate from pre-alert data
                            'highest_threat': max([a.get('threat_score', {}).get('score', 0) for a in score_all_alerts(alerts)]) if alerts and SEVERITY_SCORER_AVAILABLE else 0
                        }
                        
                        post_stats_to_social_media(daily_stats)
                    except Exception as e:
                        print(f"⚠ Error posting daily stats: {e}")
                
                # Run verification every cycle
                verify_forecasts()
                check_count += 1
                
                # Run retraining every 360 checks (12 hours if checking every 2 min)
                if check_count % 360 == 0 and auto_retrain is not None:
                    print("\n🤖 Automatic retraining check...")
                    auto_retrain()
                
            except Exception as e:
                print(f"⚠ Error in verification loop: {e}")
            
            # Check every 2 minutes for severe weather
            time.sleep(120)
    
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
