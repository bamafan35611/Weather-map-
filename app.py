# app.py
# Localized Weather Intelligence API for North Alabama + Southern Tennessee

from flask import Flask, jsonify
from flask_cors import CORS
from pre_alert_predictor import PreAlertPredictor
from severity_scorer import SeverityScorer  # assuming you already have this
import time

app = Flask(__name__)
CORS(app)

# Initialize systems
predictor = PreAlertPredictor()
scorer = SeverityScorer()

# ✅ Target states for filtering
TARGET_STATES = ["Alabama", "Tennessee"]

def is_local_alert(alert):
    """Filter alerts to only AL/TN region."""
    area = alert.get("areaDesc", "")
    return any(state in area for state in TARGET_STATES)


# -------------------------------
# Pre‑Alert Endpoints
# -------------------------------

@app.route("/api/pre-alerts", methods=["GET"])
def get_pre_alerts():
    alerts = predictor.scan_for_pre_alerts()
    return jsonify({
        "success": True,
        "count": len(alerts),
        "predictions": alerts,
        "message": f"Monitoring {len(alerts)} developing situations in North Alabama & Southern Tennessee"
    })


@app.route("/api/pre-alerts/stats", methods=["GET"])
def get_pre_alert_stats():
    results = predictor.verify_predictions()
    correct = sum(1 for r in results if r["verified"])
    false_alarms = len(results) - correct
    accuracy = round((correct / len(results) * 100), 1) if results else 0.0

    return jsonify({
        "success": True,
        "stats": {
            "total_predictions": len(results),
            "correct": correct,
            "false_alarms": false_alarms,
            "accuracy": accuracy,
            "avg_time_advantage": 10.0  # placeholder until real lead time is tracked
        },
        "message": f"Pre‑alert accuracy: {accuracy}%"
    })


# -------------------------------
# Severity Scoring Endpoints
# -------------------------------

@app.route("/api/alerts/scored", methods=["GET"])
def get_scored_alerts():
    # Replace with your actual NWS alert fetch
    nws_alerts = []  # TODO: fetch from NWS API
    local_alerts = [a for a in nws_alerts if is_local_alert(a)]
    scored = [scorer.score_alert(a) for a in local_alerts]

    return jsonify({
        "success": True,
        "count": len(scored),
        "alerts": scored
    })


@app.route("/api/threat/current", methods=["GET"])
def get_current_threat():
    # Replace with your actual NWS alert fetch
    nws_alerts = []  # TODO: fetch from NWS API
    local_alerts = [a for a in nws_alerts if is_local_alert(a)]
    scored = [scorer.score_alert(a) for a in local_alerts]

    if not scored:
        return jsonify({"success": True, "message": "No active local alerts"})

    highest = max(scored, key=lambda x: x["threat_score"])
    return jsonify({
        "success": True,
        "threat_score": highest["threat_score"],
        "threat_level": highest["threat_level"],
        "color": highest["color"],
        "action": highest["action"],
        "alert_type": highest["event"],
        "location": highest["areaDesc"],
        "active_alerts": len(scored)
    })


# -------------------------------
# Debug Route
# -------------------------------

@app.route("/api/debug/routes", methods=["GET"])
def debug_routes():
    return jsonify({
        "success": True,
        "routes": [
            "/api/pre-alerts",
            "/api/pre-alerts/stats",
            "/api/alerts/scored",
            "/api/threat/current"
        ],
        "region": "North Alabama & Southern Tennessee"
    })


# -------------------------------
# Run App
# -------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)