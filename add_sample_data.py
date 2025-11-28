#!/usr/bin/env python3
"""
Add sample forecast data to test the history system
"""

from datetime import datetime, timedelta
from forecast_db import save_forecast, verify_forecast
import random

def add_sample_forecasts():
    """Add realistic sample forecast data"""
    
    print("Adding sample forecast data...\n")
    
    # Sample locations in Alabama
    locations = [
        {"name": "Madison County", "lat": 34.7304, "lon": -86.5861},
        {"name": "Limestone County", "lat": 34.8104, "lon": -86.9828},
        {"name": "Morgan County", "lat": 34.4859, "lon": -86.9833},
        {"name": "Jackson County", "lat": 34.7598, "lon": -86.0894},
        {"name": "Marshall County", "lat": 34.3589, "lon": -86.2939}
    ]
    
    # Sample forecast types
    forecast_types = [
        "severe_thunderstorm",
        "tornado",
        "flash_flood",
        "winter_storm",
        "wind"
    ]
    
    severities = ["minor", "moderate", "severe", "extreme"]
    
    # Create forecasts over the past 14 days
    forecasts = []
    
    for days_ago in range(14, 0, -1):
        # 2-3 forecasts per day
        num_forecasts = random.randint(2, 3)
        
        for _ in range(num_forecasts):
            location = random.choice(locations)
            forecast_type = random.choice(forecast_types)
            severity = random.choice(severities)
            
            # Timestamp when forecast was made
            made_time = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 18))
            
            # When the forecast was for (2-6 hours ahead)
            forecast_for_time = made_time + timedelta(hours=random.randint(2, 6))
            
            confidence = random.randint(60, 95)
            
            forecast_data = {
                'timestamp': made_time.isoformat(),
                'forecast_for': forecast_for_time.isoformat(),
                'location': location['name'],
                'latitude': location['lat'],
                'longitude': location['lon'],
                'prediction_type': forecast_type,
                'predicted_severity': severity,
                'confidence': confidence,
                'details': {
                    'model': 'RandomForestClassifier',
                    'features': 'radar + surface conditions'
                }
            }
            
            forecast_id = save_forecast(forecast_data)
            forecasts.append((forecast_id, forecast_type, severity, location['name']))
            
            # Verify the forecast (simulate results)
            # 70% correct, 25% false positive, 5% false negative
            rand = random.random()
            if rand < 0.70:
                result = 'correct'
                actual = f"{forecast_type.replace('_', ' ').title()} Warning"
            elif rand < 0.95:
                result = 'false_positive'
                actual = None
            else:
                result = 'false_negative'
                actual = "Severe Weather Warning"
            
            verify_forecast(forecast_id, result, actual)
            
            print(f"  ✓ Forecast #{forecast_id}: {forecast_type} ({severity}) for {location['name']} - {result.upper()}")
    
    print(f"\n✓ Added {len(forecasts)} sample forecasts")
    print("\nYou can now view the history in your weather map!")
    print("The history panel will show verification results with accuracy stats.\n")

if __name__ == '__main__':
    try:
        add_sample_forecasts()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure forecast_db.py is in the same directory and the database is initialized.")
