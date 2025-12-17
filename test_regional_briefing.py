#!/usr/bin/env python3
"""
Test the regional briefing system (North Alabama & Southern Tennessee)
"""

import sys
sys.path.insert(0, '/home/claude/Weather-map--main')

from weather_commentary import get_regional_briefing

print("=" * 80)
print("REGIONAL BRIEFING TEST")
print("=" * 80)

# Simulate regional alerts
test_alerts = [
    {
        'event': 'Severe Thunderstorm Warning',
        'areaDesc': 'Madison County, Alabama',
        'id': 'test1'
    },
    {
        'event': 'Flash Flood Watch',
        'areaDesc': 'Jackson County, Alabama; DeKalb County, Alabama',
        'id': 'test2'
    },
    {
        'event': 'Special Weather Statement',
        'areaDesc': 'Franklin County, Tennessee',
        'id': 'test3'
    }
]

test_scored = [
    {
        'event': 'Severe Thunderstorm Warning',
        'areaDesc': 'Madison County, Alabama',
        'threat_score': {'score': 75}
    },
    {
        'event': 'Flash Flood Watch',
        'areaDesc': 'Jackson County, Alabama; DeKalb County, Alabama',
        'threat_score': {'score': 65}
    },
    {
        'event': 'Special Weather Statement',
        'areaDesc': 'Franklin County, Tennessee',
        'threat_score': {'score': 25}
    }
]

print("\n📻 TESTING REGIONAL BRIEFING (With Alerts)")
print("-" * 80)
briefing = get_regional_briefing(test_alerts, test_scored)
print(briefing)

print("\n\n📻 TESTING REGIONAL BRIEFING (No Alerts)")
print("-" * 80)
quiet_briefing = get_regional_briefing([], [])
print(quiet_briefing)

print("\n\n✅ KEY DIFFERENCES FROM NATIONAL BRIEFING:")
print("-" * 80)
print("BEFORE (National):")
print('  "...monitoring X active weather alerts across the nation"')
print('  "...from coast to coast"')
print('  "...nationwide"')
print()
print("AFTER (Regional):")
print('  "...monitoring X active weather alerts across the region"')
print('  "...across North Alabama and Southern Tennessee"')
print('  "...regional weather intelligence"')

print("\n\n📊 BROADCAST SCHEDULE:")
print("-" * 80)
print(":00 - REGIONAL BRIEFING (North Alabama & Southern Tennessee)")
print(":15 - Top Alerts + Random City")
print(":30 - Athens Local + Current Conditions")
print(":45 - Weather Story")

print("\n" + "=" * 80)
print("Regional briefing system ready!")
print("=" * 80)
