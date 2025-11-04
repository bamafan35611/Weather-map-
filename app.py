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
    # ✅ Add a simple example polygon so the layer displays
    return jsonify({
        'outlooks': [{
            'type': 'convective',
            'risk_level': 'SLGT',
            'probability': '15%',
            'description': 'Test slight risk (demo polygon)',
            'day': 1,
            'polygon': [
                [-87.0, 34.6], [-86.6, 34.6],
                [-86.6, 34.9], [-87.0, 34.9],
                [-87.0, 34.6]
            ]
        }]
    })

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
