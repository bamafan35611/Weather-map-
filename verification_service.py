import requests
from datetime import datetime, timedelta
from forecast_db import (
    get_unverified_forecasts, 
    verify_forecast, 
    save_actual_event
)
from typing import List, Dict, Optional
import time

def fetch_nws_alerts(active_only=True):
    """Fetch current NWS alerts"""
    try:
        url = 'https://api.weather.gov/alerts'
        params = {'status': 'actual'} if active_only else {}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        alerts = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            geometry = feature.get('geometry')
            
            alert = {
                'id': props.get('id'),
                'event': props.get('event'),
                'severity': props.get('severity'),
                'urgency': props.get('urgency'),
                'certainty': props.get('certainty'),
                'areaDesc': props.get('areaDesc'),
                'onset': props.get('onset'),
                'expires': props.get('expires'),
                'headline': props.get('headline'),
                'description': props.get('description'),
                'geometry': geometry
            }
            alerts.append(alert)
        
        return alerts
    except Exception as e:
        print(f"Error fetching NWS alerts: {e}")
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate approximate distance in kilometers using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    
    return km

def check_if_event_matches_forecast(forecast: Dict, alerts: List[Dict]) -> Optional[Dict]:
    """Check if any alert matches the forecast prediction"""
    
    forecast_type = forecast['prediction_type'].lower()
    forecast_lat = forecast.get('latitude')
    forecast_lon = forecast.get('longitude')
    forecast_time = datetime.fromisoformat(forecast['forecast_for'])
    
    # Define matching criteria
    type_keywords = {
        'tornado': ['tornado'],
        'severe_thunderstorm': ['severe thunderstorm', 'thunderstorm'],
        'flash_flood': ['flash flood', 'flood'],
        'winter_storm': ['winter storm', 'blizzard', 'ice storm'],
        'wind': ['wind', 'high wind'],
        'hail': ['hail']
    }
    
    keywords = type_keywords.get(forecast_type, [forecast_type])
    
    for alert in alerts:
        event_name = (alert.get('event') or '').lower()
        
        # Check if event type matches
        type_match = any(keyword in event_name for keyword in keywords)
        if not type_match:
            continue
        
        # Check time window (alert should be within 6 hours of forecast time)
        alert_onset = alert.get('onset')
        if alert_onset:
            try:
                alert_time = datetime.fromisoformat(alert_onset.replace('Z', '+00:00'))
                time_diff = abs((alert_time - forecast_time).total_seconds() / 3600)
                if time_diff > 6:  # More than 6 hours difference
                    continue
            except:
                pass
        
        # Check location proximity if coordinates available
        if forecast_lat and forecast_lon and alert.get('geometry'):
            # For simplicity, check if location name matches
            area_desc = (alert.get('areaDesc') or '').lower()
            forecast_location = forecast['location'].lower()
            
            if forecast_location in area_desc or area_desc in forecast_location:
                return alert
        else:
            # If no coordinates, just check location name
            area_desc = (alert.get('areaDesc') or '').lower()
            forecast_location = forecast['location'].lower()
            
            if forecast_location in area_desc or area_desc in forecast_location:
                return alert
    
    return None

def verify_forecasts():
    """Main verification function - check unverified forecasts against actual events"""
    print("\n🔍 Starting forecast verification...")
    
    # Get forecasts that need verification
    unverified = get_unverified_forecasts()
    
    if not unverified:
        print("No forecasts to verify")
        return
    
    print(f"Found {len(unverified)} forecasts to verify")
    
    # Fetch recent NWS alerts (last 24 hours)
    alerts = fetch_nws_alerts(active_only=False)
    print(f"Fetched {len(alerts)} recent NWS alerts")
    
    verified_count = 0
    
    for forecast in unverified:
        forecast_id = forecast['id']
        forecast_type = forecast['prediction_type']
        location = forecast['location']
        
        print(f"\n  Checking forecast #{forecast_id}: {forecast_type} for {location}")
        
        # Check if actual event occurred
        matching_alert = check_if_event_matches_forecast(forecast, alerts)
        
        if matching_alert:
            # Forecast was correct - event occurred
            result = 'correct'
            actual_event = matching_alert.get('event')
            print(f"  ✓ CORRECT - Found matching event: {actual_event}")
            
            # Save the actual event for records
            save_actual_event({
                'timestamp': matching_alert.get('onset'),
                'event_type': matching_alert.get('event'),
                'location': matching_alert.get('areaDesc'),
                'severity': matching_alert.get('severity'),
                'details': {
                    'headline': matching_alert.get('headline'),
                    'description': matching_alert.get('description')[:200]
                },
                'nws_id': matching_alert.get('id')
            })
        else:
            # No matching event found - false positive
            result = 'false_positive'
            actual_event = None
            print(f"  ✗ FALSE ALARM - No matching event occurred")
        
        verify_forecast(forecast_id, result, actual_event)
        verified_count += 1
    
    print(f"\n✓ Verification complete: {verified_count} forecasts verified")

def auto_verify_loop(interval_seconds=300):
    """Run verification in a loop (for background task)"""
    print(f"Starting auto-verification loop (every {interval_seconds} seconds)")
    
    while True:
        try:
            verify_forecasts()
        except Exception as e:
            print(f"Error in verification loop: {e}")
        
        time.sleep(interval_seconds)

if __name__ == '__main__':
    # Run verification once
    verify_forecasts()
