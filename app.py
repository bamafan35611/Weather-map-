import os
import glob
import pickle
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

_model = None
_model_path = None

def _load_model_once():
    global _model, _model_path
    if _model is not None:
        return _model
    # Load the first .pkl in models/ if available
    candidates = sorted(glob.glob(os.path.join('models', '*.pkl')))
    if not candidates:
        return None
    _model_path = candidates[0]
    try:
        with open(_model_path, 'rb') as f:
            _model = pickle.load(f)
    except Exception as e:
        # Keep it None if load fails; return error on inference route
        _model = None
    return _model

@app.get('/')
def root():
    return send_from_directory(app.static_folder, 'RadarMap-optimized.html')

@app.get('/api/test')
def api_test():
    return jsonify({'ok': True})

@app.get('/api/weather/alerts')
def api_alerts():
    # TODO: Replace with your merged backend alerts (monitored counties + NWS, etc.)
    return jsonify({'alerts': []})

@app.get('/api/outlooks')
def api_outlooks():
    # TODO: Replace with your outlook polygons
    return jsonify({'outlooks': []})

@app.get('/api/learning/history')
def api_history():
    # TODO: Replace with your DB-backed forecast history
    return jsonify({'count': 0, 'history': []})

@app.post('/api/ml/predictions')
def api_predictions():
    # Example: Try to use the loaded model if present; otherwise stub
    model = _load_model_once()
    if model is None:
        return jsonify({
            'model_trained': False,
            'total_forecasts': 0,
            'verified_forecasts': 0,
            'accuracy': {},
            'note': 'No model loaded. Place a .pkl in /models or implement your own loader.'
        })
    # If you know your model's expected inputs, plug that logic here.
    # We return metadata only to prove the model is present.
    return jsonify({
        'model_trained': True,
        'model_path': _model_path,
        'message': 'Model is loaded. Implement real inference here.'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)