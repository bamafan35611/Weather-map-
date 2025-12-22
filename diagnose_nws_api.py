"""
diagnose_nws_api.py - Diagnostic script to test NWS API connectivity
Run this on your Render server to see exactly what's happening
"""

import requests
import json
from datetime import datetime

def test_nws_api():
    """Test NWS API step by step"""
    
    print("=" * 80)
    print("NWS API DIAGNOSTIC TEST")
    print("=" * 80)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Athens, AL coordinates
    lat = 34.80
    lon = -86.97
    
    # Test 1: Basic connectivity
    print("TEST 1: Basic NWS API Connectivity")
    print("-" * 80)
    try:
        response = requests.get("https://api.weather.gov/", timeout=10)
        print(f"✅ NWS API is reachable")
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
    except Exception as e:
        print(f"❌ Cannot reach NWS API: {e}")
        print("   This could be a network/firewall issue on Render")
        return
    
    print()
    
    # Test 2: Points endpoint
    print("TEST 2: Points Endpoint (Athens, AL)")
    print("-" * 80)
    points_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
    print(f"URL: {points_url}")
    
    try:
        headers = {
            'User-Agent': '(NorthBamaWX Diagnostic Test, northbamawx@example.com)',
            'Accept': 'application/geo+json'
        }
        
        response = requests.get(points_url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            print(f"✅ Points endpoint working")
            data = response.json()
            
            # Extract key info
            if 'properties' in data:
                props = data['properties']
                print(f"\nGrid Information:")
                print(f"   Office: {props.get('gridId', 'N/A')}")
                print(f"   Grid X: {props.get('gridX', 'N/A')}")
                print(f"   Grid Y: {props.get('gridY', 'N/A')}")
                print(f"   Forecast URL: {props.get('forecast', 'N/A')}")
                print(f"   Forecast Hourly: {props.get('forecastHourly', 'N/A')}")
                
                forecast_url = props.get('forecast')
                
                if forecast_url:
                    print()
                    # Test 3: Forecast endpoint
                    print("TEST 3: Forecast Endpoint")
                    print("-" * 80)
                    print(f"URL: {forecast_url}")
                    
                    try:
                        forecast_response = requests.get(forecast_url, headers=headers, timeout=15)
                        print(f"Status: {forecast_response.status_code}")
                        print(f"Response time: {forecast_response.elapsed.total_seconds():.2f}s")
                        
                        if forecast_response.status_code == 200:
                            print(f"✅ Forecast endpoint working")
                            forecast_data = forecast_response.json()
                            
                            if 'properties' in forecast_data:
                                periods = forecast_data['properties'].get('periods', [])
                                print(f"\nForecast Periods: {len(periods)}")
                                
                                if periods:
                                    print("\nFirst 2 Periods:")
                                    for i, period in enumerate(periods[:2], 1):
                                        print(f"\n{i}. {period.get('name', 'N/A')}")
                                        print(f"   Temp: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', 'N/A')}")
                                        print(f"   Forecast: {period.get('shortForecast', 'N/A')}")
                                        print(f"   Detail: {period.get('detailedForecast', 'N/A')[:100]}...")
                                    
                                    print("\n" + "=" * 80)
                                    print("✅ ALL TESTS PASSED - NWS API IS WORKING")
                                    print("=" * 80)
                                    print("\nThe forecast system should work correctly.")
                                    print("If you're still getting errors, check:")
                                    print("  1. File permissions on nws_forecast_fetcher.py")
                                    print("  2. Python import errors in app.py")
                                    print("  3. Render logs for specific error messages")
                                else:
                                    print("❌ No forecast periods in response")
                            else:
                                print("❌ Invalid forecast response structure")
                                print(f"Response keys: {forecast_data.keys()}")
                        
                        elif forecast_response.status_code == 500:
                            print("❌ NWS forecast server error (500)")
                            print("   This is a temporary NWS API issue")
                            print("   Try again in a few minutes")
                        
                        else:
                            print(f"❌ Unexpected status code: {forecast_response.status_code}")
                            print(f"Response: {forecast_response.text[:500]}")
                    
                    except requests.exceptions.Timeout:
                        print("❌ Forecast endpoint timeout (>15s)")
                        print("   Network connection may be slow")
                    
                    except Exception as e:
                        print(f"❌ Error fetching forecast: {type(e).__name__}: {e}")
                
                else:
                    print("❌ No forecast URL in points response")
            else:
                print("❌ Invalid points response structure")
                print(f"Response keys: {data.keys()}")
        
        elif response.status_code == 404:
            print("❌ Location not found (404)")
            print("   Coordinates may be outside NWS coverage area")
        
        elif response.status_code == 500:
            print("❌ NWS server error (500)")
            print("   This is a temporary NWS API issue")
        
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print("❌ Points endpoint timeout (>15s)")
        print("   Network connection may be slow")
    
    except Exception as e:
        print(f"❌ Error fetching points: {type(e).__name__}: {e}")
    
    print()
    print("=" * 80)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    test_nws_api()
