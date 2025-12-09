"""
EXACT CODE CHANGES FOR app.py

Copy these sections into your app.py file
"""

# ============================================================================
# CHANGE 1: Add import at top of file (around line 10)
# ============================================================================

# Add this with your other imports:
from nws_forecast_fetcher import get_athens_forecast, get_forecast_fetcher, NWSForecastFetcher


# ============================================================================
# CHANGE 2: Add new API endpoint (add this anywhere before the catch-all route)
# ============================================================================

@app.route('/api/local-forecast')
def local_forecast():
    """Get actual NWS forecast for Athens, AL"""
    try:
        fetcher = get_forecast_fetcher()
        forecast_data = fetcher.get_home_forecast()
        
        if forecast_data:
            return jsonify({
                'success': True,
                'location': 'Athens, AL',
                'coordinates': '34.80°N, 86.97°W',
                'forecast': forecast_data,
                'summary': fetcher.get_short_forecast_summary(forecast_data, 3),
                'athens_broadcast': fetcher.get_athens_forecast_specifically(),
                'severe_expected': fetcher.is_severe_weather_expected(forecast_data),
                'updated': forecast_data.get('updated'),
                'periods_count': len(forecast_data.get('periods', []))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not fetch forecast from NWS'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CHANGE 3: Update the /api/weather-broadcast endpoint
# ============================================================================

# Find the section around line 982 that handles :15 minute broadcasts
# Replace the hourly update section with this:

        # :15 - Hourly Update WITH LOCAL FORECAST
        elif current_minute == 15:
            broadcast_data['broadcast_type'] = 'hourly_update'
            
            # FIRST: Get Athens, AL local forecast
            try:
                fetcher = get_forecast_fetcher()
                local_forecast = get_athens_forecast()
                broadcast_data['content'].append({
                    'type': 'local_forecast',
                    'priority': 'high',
                    'text': local_forecast,
                    'duration_estimate': '15-20 seconds'
                })
                print(f"✓ Local forecast added to broadcast: {local_forecast[:50]}...")
            except Exception as e:
                print(f"⚠ Error getting local forecast: {e}")
                broadcast_data['content'].append({
                    'type': 'local_forecast',
                    'priority': 'high',
                    'text': 'Local forecast temporarily unavailable.',
                    'duration_estimate': '5 seconds'
                })
            
            # SECOND: Add alert commentary if available
            if COMMENTARY_AVAILABLE:
                update = get_hourly_update(alerts, scored, "North Alabama")
                broadcast_data['content'].append({
                    'type': 'commentary',
                    'priority': 'medium',
                    'text': update,
                    'duration_estimate': '15-30 seconds'
                })


# ============================================================================
# CHANGE 4: Add a debug endpoint to check forecast status
# ============================================================================

@app.route('/api/forecast-debug')
def forecast_debug():
    """Debug endpoint to check forecast fetching"""
    try:
        fetcher = get_forecast_fetcher()
        forecast = fetcher.get_home_forecast()
        
        if forecast:
            periods = forecast.get('periods', [])
            return jsonify({
                'status': 'OK',
                'message': 'Forecast fetching is working',
                'location': 'Athens, AL (34.80°N, 86.97°W)',
                'periods_fetched': len(periods),
                'first_period': periods[0] if periods else None,
                'updated': forecast.get('updated'),
                'current_forecast': fetcher.get_athens_forecast_specifically()
            })
        else:
            return jsonify({
                'status': 'ERROR',
                'message': 'Could not fetch forecast',
                'location': 'Athens, AL (34.80°N, 86.97°W)'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': f'Exception occurred: {str(e)}'
        }), 500


# ============================================================================
# TESTING YOUR CHANGES
# ============================================================================

"""
After deploying these changes, test with:

1. Test local forecast endpoint:
   curl https://your-app.onrender.com/api/local-forecast

2. Test debug endpoint:
   curl https://your-app.onrender.com/api/forecast-debug

3. Test broadcast at :15 after the hour:
   curl https://your-app.onrender.com/api/weather-broadcast

You should now see actual Athens, AL forecast data in your broadcasts!
"""
