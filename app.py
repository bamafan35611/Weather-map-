import os
import glob
import pickle
import threading
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
from ml_bridge import get_ml_predictions  # Fetch ML from local PC

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
