#!/usr/bin/env python3
"""
Test the enhanced Athens briefing with current temperature and wind speed
"""

import sys
sys.path.insert(0, '/home/claude/Weather-map--main')

from nws_forecast_fetcher import (
    get_athens_forecast,
    get_athens_current_conditions,
    get_athens_briefing_with_conditions
)

print("=" * 80)
print("TESTING ATHENS BRIEFING WITH CURRENT CONDITIONS")
print("=" * 80)

print("\n1. Testing current conditions fetch...")
print("-" * 80)
conditions = get_athens_current_conditions()

if conditions:
    print("✅ Current conditions retrieved successfully!")
    print(f"   Data: {conditions}")
    
    if 'temperature' in conditions:
        print(f"   🌡️  Temperature: {conditions['temperature']}°F")
    
    if 'wind_speed' in conditions:
        wind_dir = conditions.get('wind_direction', '')
        print(f"   💨 Wind: {wind_dir} at {conditions['wind_speed']} mph")
        
        if 'wind_gust' in conditions:
            print(f"      Gusts: {conditions['wind_gust']} mph")
else:
    print("⚠️  Could not retrieve current conditions")

print("\n2. Testing basic forecast (without conditions)...")
print("-" * 80)
basic_forecast = get_athens_forecast()
print(basic_forecast)

print("\n3. Testing enhanced briefing (WITH temperature and wind)...")
print("-" * 80)
enhanced_briefing = get_athens_briefing_with_conditions()
print(enhanced_briefing)

print("\n" + "=" * 80)
print("COMPARISON:")
print("=" * 80)
print(f"\nBasic forecast length: {len(basic_forecast)} characters")
print(f"Enhanced briefing length: {len(enhanced_briefing)} characters")

if conditions:
    print("\n✅ SUCCESS! The bot will now announce temperature and wind speed!")
    print("\nExample broadcast at :30 minute mark:")
    print(f'   "{enhanced_briefing}"')
else:
    print("\n⚠️  Warning: Current conditions unavailable, bot will use basic forecast")

print("\n" + "=" * 80)
