#!/usr/bin/env python3
"""
Test the random city briefing feature for :15 broadcasts
"""

import sys
sys.path.insert(0, '/home/claude/Weather-map--main')

from local_cities import (
    get_random_city, 
    format_city_location,
    MONITORED_CITIES,
    get_cities_by_county,
    get_cities_by_state
)

print("=" * 80)
print("RANDOM CITY BRIEFING TEST")
print("=" * 80)

print("\n📊 CITY DATABASE OVERVIEW")
print("-" * 80)
print(f"Total cities/towns: {len(MONITORED_CITIES)}")

al_cities = get_cities_by_state('AL')
tn_cities = get_cities_by_state('TN')
print(f"Alabama: {len(al_cities)} cities")
print(f"Tennessee: {len(tn_cities)} cities")

print("\n🎲 SIMULATING 10 RANDOM :15 BROADCASTS")
print("-" * 80)
print("This shows what cities would be randomly selected at :15 mark:")
print()

for i in range(10):
    city = get_random_city()
    location = format_city_location(city)
    print(f"{i+1:2d}. {location:30s} ({city['county']} County)")

print("\n📍 CITIES BY COUNTY")
print("-" * 80)

counties = {}
for name, data in MONITORED_CITIES.items():
    county_key = f"{data['county']} County, {data['state']}"
    if county_key not in counties:
        counties[county_key] = []
    counties[county_key].append(name)

for county in sorted(counties.keys()):
    print(f"\n{county}:")
    for city in sorted(counties[county]):
        print(f"  • {city}")

print("\n" + "=" * 80)
print("EXAMPLE :15 BROADCAST WITH CITY BRIEFING")
print("=" * 80)

city = get_random_city()
print(f"""
Broadcast Flow:
1. Intro: "NorthBamaWX with current weather alerts."
2. Alert #1: [if any alerts]
3. Alert #2: [if any alerts]
4. Alert #3: [if any alerts]
5. 🆕 CITY BRIEFING: "{city['name']}, {city['state']}: Currently 62 degrees, 
   winds South at 8 miles per hour. This Afternoon, Partly Cloudy. High of 68 degrees."
6. Pre-alerts: [if any AI predictions]

Total duration: ~45-60 seconds
""")

print("\n✅ Random city briefings will add local flavor to your broadcasts!")
print("   Cities selected randomly from your 14 monitored counties.")
print("=" * 80)
