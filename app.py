import os
import glob
import pickle
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
from ml_bridge import get_ml_predictions  # Fetch ML from local PC

# NEW: requests used to fetch NWS data
import requests

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
    """Return simplified alerts so the frontend marks them HIGH priority and renders polygons.
    We proxy NWS active alerts but only pass through Tornado/Severe Thunderstorm WATCHES (the ones missing).
    If you want *all* alerts, set env PASS_ALL_ALERTS=1.
    """
    NWS_URL = 'https://api.weather.gov/alerts/active'
    headers = {
        # NWS requires a UA with contact
        'User-Agent': '(WeatherMap/1.0, contact: example@example.com)',
        'Accept': 'application/geo+json'
    }
    try:
        r = requests.get(NWS_URL, headers=headers, timeout=12)
        r.raise_for_status()
        gj = r.json() or {}
        feats = gj.get('features', [])

        pass_all = os.environ.get('PASS_ALL_ALERTS', '').strip() == '1'

        WATCH_EVENTS = {
            'tornado watch',
            'severe thunderstorm watch'
        }

        out = []
        for f in feats:
            props = (f.get('properties') or {})
            geom = f.get('geometry') or {}

            # Require usable geometry (Polygon or MultiPolygon with coordinates)
            if not geom or not geom.get('coordinates'):
                continue

            ev = (props.get('event') or '').strip()
            ev_l = ev.lower()

            # Filter unless PASS_ALL_ALERTS=1
            if not pass_all and ev_l not in WATCH_EVENTS:
                continue

            # Normalize basic fields used by the frontend mapping step
            out.append({
                'id': props.get('id') or props.get('sent') or f.get('id'),
                'event': ev or 'Weather Alert',
                'headline': props.get('headline') or '',
                'areaDesc': props.get('areaDesc') or '',
                'description': props.get('description') or '',
                'expires': props.get('expires') or props.get('ends') or '',
                'geometry': geom
            })

        return jsonify({'alerts': out})
    except Exception as e:
        # Don't break frontend
        return jsonify({'alerts': [], 'error': str(e)}), 200

@app.get('/api/outlooks')
def api_outlooks():
    """Return current SPC convective outlook polygons (categorical) as simple JSON
    the front-end already understands. No fake/demo boxes."""
    import requests

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
    return jsonify({'count': 0, 'history': []})

@app.get('/api/ml/predictions')
def api_predictions():
    """Fetch ML predictions from local PC via ngrok"""
    data = get_ml_predictions()
    
    if data.get('success'):
        return jsonify(data)
    else:
        # Return error but don't break frontend
        return jsonify(data), 200

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
# Entrypoint
# ----------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
