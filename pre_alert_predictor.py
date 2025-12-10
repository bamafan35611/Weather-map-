# pre_alert_predictor.py
# Focused Pre‑Alert Prediction Engine for North Alabama + Southern Tennessee

import time
import random

# ✅ Only monitor local cities
PRIORITY_CITIES = [
    "Huntsville, AL",
    "Decatur, AL",
    "Madison, AL",
    "Athens, AL",
    "Florence, AL",
    "Fayetteville, TN",
    "Pulaski, TN",
    "Winchester, TN",
    "Shelbyville, TN"
]

class PreAlertPredictor:
    def __init__(self):
        self.predictions = []

    def scan_for_pre_alerts(self):
        """
        Simulate scanning radar/conditions for developing severe weather.
        Replace this with real ML/radar logic in production.
        """
        new_predictions = []
        for city in PRIORITY_CITIES:
            # Example: random confidence for demo purposes
            confidence = random.uniform(50, 95)

            if confidence >= 70:  # Only issue pre‑alerts if confidence is high
                prediction = {
                    "type": "pre_alert_prediction",
                    "alert_type": random.choice([
                        "Tornado Warning",
                        "Severe Thunderstorm Warning",
                        "Flash Flood Warning"
                    ]),
                    "location": city,
                    "confidence": round(confidence, 1),
                    "time_until_alert": "5-15 minutes",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                new_predictions.append(prediction)

        self.predictions = new_predictions
        return new_predictions

    def verify_predictions(self):
        """
        Stub for verifying predictions against actual NWS alerts.
        In production, connect to NWS API and compare.
        """
        results = []
        for pred in self.predictions:
            # Simulate verification: 80% chance correct
            correct = random.random() < 0.8
            results.append({
                "prediction": pred,
                "verified": correct
            })
        return results


# ✅ Example usage
if __name__ == "__main__":
    predictor = PreAlertPredictor()
    alerts = predictor.scan_for_pre_alerts()
    if alerts:
        print("🚨 PRE‑ALERTS ISSUED:")
        for a in alerts:
            print(f"- {a['alert_type']} for {a['location']} ({a['confidence']}% confidence)")
    else:
        print("No developing situations detected.")

    # Verify after 10 minutes (simulated)
    time.sleep(1)  # shorten for demo
    results = predictor.verify_predictions()
    for r in results:
        print(f"Verification: {r['prediction']['alert_type']} in {r['prediction']['location']} → "
              f"{'CORRECT' if r['verified'] else 'FALSE ALARM'}")