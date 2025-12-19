print("🚨🚨🚨 NEW LOCAL_PREDICTOR.PY LOADED 🚨🚨🚨")
import requests
import json
import traceback

class LocalPredictor:

    def __init__(self):
        # 14 monitored counties - North Alabama (11) + Southern Tennessee (3)
        self.MONITORED_ZONES = [
            # North Alabama counties
            'ALC033',  # Colbert County, AL
            'ALC043',  # Cullman County, AL
            'ALC049',  # DeKalb County, AL
            'ALC059',  # Franklin County, AL
            'ALC071',  # Jackson County, AL
            'ALC079',  # Lawrence County, AL
            'ALC077',  # Lauderdale County, AL
            'ALC083',  # Limestone County, AL (Athens)
            'ALC089',  # Madison County, AL (Huntsville)
            'ALC095',  # Marshall County, AL
            'ALC103',  # Morgan County, AL
            # Southern Tennessee counties
            'TNC051',  # Franklin County, TN
            'TNC103',  # Lincoln County, TN
            'TNC127'   # Moore County, TN
        ]

    def fetch_active_alerts(self):
        """Fetch alerts ONLY for the 14 monitored counties"""
        
        # Build URL with zone filtering
        zone_params = '&'.join([f'zone={zone}' for zone in self.MONITORED_ZONES])
        url = f"https://api.weather.gov/alerts/active?{zone_params}"
        
        print(f"🌍 Fetching alerts for {len(self.MONITORED_ZONES)} monitored counties...")
        
        try:
            response = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=10)
            response.raise_for_status()
            data = response.json()
            features = data.get('features', [])
            
            print(f"✅ Retrieved {len(features)} alerts for monitored area")
            
            alerts = []

            for feature in features:
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})

                alert = {
                    'id': props.get('id'),
                    'event': props.get('event'),
                    'severity': props.get('severity'),
                    'urgency': props.get('urgency'),
                    'certainty': props.get('certainty'),
                    'areaDesc': props.get('areaDesc'),
                    'onset': props.get('onset'),
                    'expires': props.get('expires'),
                    'description': props.get('description'),
                    'instruction': props.get('instruction'),
                    'geometry': geometry
                }

                event_name = alert['event'] or 'Unknown'
                area = alert['areaDesc'] or 'Unknown'
                print(f"  📍 {event_name} - {area}")

                alerts.append(alert)

            if len(alerts) == 0:
                print("✓ No active alerts in monitored counties")
            
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
