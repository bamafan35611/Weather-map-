print("🚨🚨🚨 NEW LOCAL_PREDICTOR.PY LOADED 🚨🚨🚨")
import requests
import json
import traceback

class LocalPredictor:

    def __init__(self):
        # ENHANCED: Monitor BOTH county zones AND forecast zones for maximum coverage
        # This ensures we catch warnings regardless of which zone type NWS uses
        
        self.MONITORED_ZONES = [
            # ============================================
            # NORTH ALABAMA - COUNTY CODES (ALC)
            # ============================================
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
            
            # ============================================
            # NORTH ALABAMA - FORECAST ZONES (ALZ)
            # ============================================
            'ALZ001',  # Lauderdale County
            'ALZ002',  # Colbert County
            'ALZ003',  # Franklin County AL
            'ALZ004',  # Lawrence County
            'ALZ005',  # Limestone County (Athens)
            'ALZ006',  # Madison County (Huntsville)
            'ALZ007',  # Jackson County
            'ALZ008',  # DeKalb County
            'ALZ009',  # Marshall County
            'ALZ016',  # Morgan County
            'ALZ017',  # Cullman County
            
            # ============================================
            # SOUTHERN TENNESSEE - COUNTY CODES (TNC)
            # ============================================
            'TNC051',  # Franklin County, TN
            'TNC103',  # Lincoln County, TN
            'TNC127',  # Moore County, TN
            
            # ============================================
            # SOUTHERN TENNESSEE - FORECAST ZONES (TNZ)
            # ============================================
            'TNZ076',  # Lincoln County, TN
            'TNZ096',  # Franklin County, TN
            'TNZ097'   # Moore County, TN
        ]
        
        print(f"📡 Monitoring {len(self.MONITORED_ZONES)} total zones (county + forecast zones)")
        print(f"   • North Alabama: 22 zones (11 counties × 2 zone types)")
        print(f"   • Southern Tennessee: 6 zones (3 counties × 2 zone types)")

    def fetch_active_alerts(self):
        """Fetch alerts ONLY for the monitored zones with retry logic"""
        
        # Build URL with zone filtering
        zone_params = '&'.join([f'zone={zone}' for zone in self.MONITORED_ZONES])
        url = f"https://api.weather.gov/alerts/active?{zone_params}"
        
        print(f"🌍 Fetching alerts for {len(self.MONITORED_ZONES)} monitored zones...")
        
        # Try up to 3 times with exponential backoff
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"  Attempt {attempt}/{max_attempts}...")
                response = requests.get(
                    url, 
                    headers={'Accept': 'application/geo+json'}, 
                    timeout=15  # Increased from 10 to 15 seconds
                )
                response.raise_for_status()
                data = response.json()
                features = data.get('features', [])
                
                print(f"✅ Retrieved {len(features)} alerts for monitored area")
                
                # Deduplicate alerts (same alert might appear in both county and forecast zones)
                seen_ids = set()
                alerts = []

                for feature in features:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    alert_id = props.get('id')
                    
                    # Skip duplicates
                    if alert_id in seen_ids:
                        continue
                    seen_ids.add(alert_id)

                    alert = {
                        'id': alert_id,
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
                else:
                    print(f"📊 Total unique alerts after deduplication: {len(alerts)}")
                
                return alerts
                
            except requests.exceptions.Timeout:
                print(f"⚠️ Timeout on attempt {attempt}/{max_attempts}")
                if attempt < max_attempts:
                    import time
                    wait_time = attempt * 2  # 2, 4 seconds
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("❌ All retry attempts failed - returning empty alerts")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Network error on attempt {attempt}/{max_attempts}: {e}")
                if attempt < max_attempts:
                    import time
                    wait_time = attempt * 2
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("❌ All retry attempts failed - returning empty alerts")
                    return []
                    
            except Exception as e:
                print(f"⚠️ Unexpected error fetching alerts: {e}")
                traceback.print_exc()
                return []
        
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
