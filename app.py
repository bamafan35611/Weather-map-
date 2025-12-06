import os
from flask import Flask, jsonify, request
from local_predictor import LocalPredictor
from pre_alert_predictor import PreAlertPredictor
from severity_scorer import SeverityScorer
from forecast_db import save_forecast_prediction
from verification_service import verify_forecasts
from voice_styles import get_announcement_for_alert, get_all_announcements
from weather_speaker import build_weather_narration

app = Flask(__name__)

LOCAL = None
PREDICT = None
SCORE = None

def initialize_services():
    global LOCAL, PREDICT, SCORE
    try:
        LOCAL = LocalPredictor()
        print("✓ Local predictor ready")
    except:
        LOCAL = None
        print("⚠ Local predictor offline")

    try:
        PREDICT = PreAlertPredictor()
        print("✓ Pre-alert predictor ready")
    except:
        PREDICT = None
        print("⚠ Pre-alert offline")

    SCORE = SeverityScorer()
    print("✓ Severity scoring ready")

@app.get("/api/test")
def test():
    return jsonify({"status": "ok"})

@app.get("/api/alerts/active")
def active_alerts():
    if not LOCAL:
        return jsonify([])
    return jsonify(LOCAL.fetch_active_alerts())

@app.post("/api/predict/alert")
def predict():
    if not PREDICT:
        return jsonify({"error": "offline"}), 500
    data = request.json
    r = PREDICT.predict_alert_probability(data["lat"], data["lon"], data.get("location", "here"))
    if r:
        save_forecast_prediction(r)
    return jsonify(r)

@app.get("/api/verify")
def verify():
    verify_forecasts()
    return jsonify({"verified": True})

@app.get("/api/voice/announcements/all")
def all_announcements():
    return jsonify(get_all_announcements())

@app.get("/api/voice/weather-summary")
def voice_narration():
    try:
        return jsonify(build_weather_narration())
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    initialize_services()
    app.run(host="0.0.0.0", port=5000)
