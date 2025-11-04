import os
import glob
import pickle
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS

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
    return jsonify({'count': 0, 'history': []})

@app.post('/api/ml/predictions')
def api_predictions():
    model = _load_model_once()
    if model is None:
        return jsonify({
            'model_trained': False,
            'total_forecasts': 0,
            'verified_forecasts': 0,
            'accuracy': {},
            'note': 'No model loaded. Place a .pkl in /models or implement your own loader.'
        })
    return jsonify({
        'model_trained': True,
        'model_path': _model_path,
        'message': 'Model is loaded. Implement real inference here.'
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
