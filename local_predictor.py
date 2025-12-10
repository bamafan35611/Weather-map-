import requests
import json
import traceback

COVERAGE_KEYWORDS = [
    # North Alabama core + expanded DMA
    'colbert county', 'cullman county', 'franklin county', 'jackson county',
    'lawrence county', 'lauderdale county', 'limestone county', 'madison county',
    'marshall county', 'morgan county', 'marion county', 'winston county',
    # Southern middle Tennessee (slim set)
    'giles county', 'lincoln county', 'franklin county, tn'
]

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
            area_desc = (props.get('areaDesc') or '').lower()

            severe_keywords = ['tornado', 'severe', 'flood', 'wind', 'thunderstorm']
            winter_keywords = ['winter', 'snow', 'blizzard', 'ice', 'freezing', 'sleet']

            # Only keep alerts inside our Tennessee Valley coverage area
            if not any(keyword in area_desc for keyword in COVERAGE_KEYWORDS):
                continue

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

                print(f"❄️ Local Winter/Severe Alert: {alert['event']} in {alert['areaDesc']}")

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
