import requests
import json
import traceback

class LocalPredictor:

    def __init__(self):
        pass

    def fetch_active_alerts(self):
        url = "https://api.weather.gov/alerts/active"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            features = data.get('features', [])
            alerts = []

            for feature in features:
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})

                # Process severe and high-impact alerts, including winter weather
                event = (props.get('event') or '').lower()

                severe_keywords = ['tornado', 'severe', 'flood', 'wind', 'thunderstorm']
                winter_keywords = ['winter', 'snow', 'blizzard', 'ice', 'freezing', 'sleet', 'cold']

                if any(keyword in event for keyword in severe_keywords + winter_keywords):
                    alert = {
                        'id': props.get('id'),
                        'event': props.get('event'),
                        'severity': props.get('severity'),
                        'urgency': props.get('urgency'),
                        'areaDesc': props.get('areaDesc'),
                        'onset': props.get('onset'),
                        'expires': props.get('expires'),
                        'description': props.get('description'),
                        'geometry': geometry
                    }

                    print(f"❄️ Winter/Severe Alert Detected: {alert['event']} in {alert['areaDesc']}")

                    alerts.append(alert)

            return alerts

        except Exception as e:
            print("⚠️ Error fetching alerts:", e)
            traceback.print_exc()
            return []

def generate_local_predictions():
    try:
        predictor = LocalPredictor()
        alerts = predictor.fetch_active_alerts()
        return alerts
    except Exception as e:
        print("⚠️ Error generating predictions:", e)
        traceback.print_exc()
        return []
