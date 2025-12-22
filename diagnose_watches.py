#!/usr/bin/env python3
"""
Enhanced Alert Diagnostic - Shows ALL alerts including watches
Run this to see why specific alerts (like Tornado Watch) aren't being announced
"""

import sys
sys.path.insert(0, '/home/claude/Weather-map--main')

from datetime import datetime
from local_predictor import LocalPredictor
from severity_scorer import score_all_alerts

print("=" * 80)
print("ENHANCED ALERT DIAGNOSTIC - ALL ALERTS")
print("=" * 80)
print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Current minute: :{datetime.now().minute:02d}")

print("\n" + "=" * 80)
print("FETCHING ALL ACTIVE ALERTS")
print("=" * 80)

try:
    predictor = LocalPredictor()
    alerts = predictor.fetch_active_alerts()
    
    print(f"✓ Total alerts fetched: {len(alerts)}")
    
    if not alerts:
        print("\n❌ NO ALERTS FOUND!")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error fetching alerts: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("SCORING ALL ALERTS")
print("=" * 80)

try:
    scored = score_all_alerts(alerts)
    print(f"✓ Alerts scored: {len(scored)}")
except Exception as e:
    print(f"❌ Error scoring: {e}")
    scored = []

print("\n" + "=" * 80)
print("ALL ALERTS (SORTED BY THREAT SCORE)")
print("=" * 80)

# Find watches specifically
watches = []
warnings = []

for alert in scored:
    event = alert.get('event', 'Unknown')
    if 'watch' in event.lower():
        watches.append(alert)
    elif 'warning' in event.lower():
        warnings.append(alert)

print(f"\n📊 Summary:")
print(f"   Total alerts: {len(scored)}")
print(f"   Warnings: {len(warnings)}")
print(f"   Watches: {len(watches)}")
print(f"   Other: {len(scored) - len(warnings) - len(watches)}")

print("\n" + "-" * 80)
print("COMPLETE ALERT LIST (TOP 10):")
print("-" * 80)
print(f"{'Rank':<5} {'Score':<6} {'Type':<35} {'Location':<30}")
print("-" * 80)

for i, alert in enumerate(scored[:10], 1):
    event = alert.get('event', 'Unknown')
    area = alert.get('areaDesc', 'Unknown')[:28]
    score = alert.get('threat_score', {}).get('score', 0)
    
    # Highlight watches
    marker = "🔴" if 'watch' in event.lower() else "  "
    
    print(f"{marker}{i:<3} {score:<6} {event:<35} {area:<30}")

if len(scored) > 10:
    print(f"\n... and {len(scored) - 10} more alerts")

# Show watches specifically
if watches:
    print("\n" + "=" * 80)
    print("🔴 WATCHES DETECTED")
    print("=" * 80)
    
    for watch in watches:
        event = watch.get('event', 'Unknown')
        area = watch.get('areaDesc', 'Unknown')
        score = watch.get('threat_score', {}).get('score', 0)
        
        # Find its rank
        rank = scored.index(watch) + 1
        
        print(f"\n{event}")
        print(f"   Location: {area}")
        print(f"   Threat Score: {score}")
        print(f"   Rank: #{rank} out of {len(scored)}")
        
        if rank <= 3:
            print(f"   ✅ WILL BE ANNOUNCED (Top 3)")
        elif rank <= 10:
            print(f"   ⚠️  May be announced if higher alerts are filtered by cooldown")
        else:
            print(f"   ❌ Will NOT be announced (below top 10)")
        
        # Check if it's a tornado watch
        if 'tornado' in event.lower() and 'watch' in event.lower():
            print(f"\n   💡 TORNADO WATCH DETECTED!")
            print(f"   Base score: 45 (moderate priority)")
            print(f"   Warnings score higher (70-90), so they're announced first")

print("\n" + "=" * 80)
print("BROADCAST TIMING")
print("=" * 80)

current_minute = datetime.now().minute

if current_minute == 15:
    print(f"\n✅ It's :{current_minute:02d} - Alert broadcast happening NOW!")
    print("\nTop 3 alerts will be announced:")
    for i, alert in enumerate(scored[:3], 1):
        event = alert.get('event', 'Unknown')
        score = alert.get('threat_score', {}).get('score', 0)
        print(f"   {i}. {event} (Score: {score})")
else:
    next_15 = 15 if current_minute < 15 else 30 if current_minute < 30 else 45 if current_minute < 45 else 0
    wait_time = (next_15 - current_minute) if next_15 > current_minute else (60 - current_minute + next_15)
    
    print(f"\n⏰ Current time: :{current_minute:02d}")
    print(f"   Next alert broadcast: :{next_15:02d}")
    print(f"   Wait time: {wait_time} minutes")

print("\n" + "=" * 80)
print("WHY WATCHES MIGHT NOT BE ANNOUNCED")
print("=" * 80)

print("\n1. PRIORITY SYSTEM")
print("   Warnings (70-90 score) are announced before Watches (35-50 score)")
print("   This is by design - active threats get priority")

print("\n2. TOP 3 LIMIT")
print("   Only the top 3 alerts are announced at :15")
print("   If you have 3+ warnings, watches won't make the cut")

print("\n3. COOLDOWN SYSTEM")
print("   If higher-priority warnings were recently announced,")
print("   they're filtered out, letting watches move up")

print("\n" + "=" * 80)
print("SOLUTIONS FOR ANNOUNCING WATCHES")
print("=" * 80)

print("\n✅ OPTION 1: Boost Watch Scores")
print("   Edit severity_scorer.py and increase watch scores:")
print("   'tornado watch': 65,  # Was 45, now higher priority")

print("\n✅ OPTION 2: Announce Top 5 Instead of Top 3")
print("   Edit app.py line ~1088:")
print("   for i, alert in enumerate(alerts_to_announce[:5]):  # Was [:3]")

print("\n✅ OPTION 3: Add Watch-Specific Mention")
print("   Add a separate callout for watches after the top alerts")
print("   'Also, a Tornado Watch is in effect for the region.'")

print("\n✅ OPTION 4: Wait for Warnings to Expire")
print("   Once higher-priority warnings expire or cooldown,")
print("   watches will naturally move into the top 3")

if watches:
    tornado_watches = [w for w in watches if 'tornado' in w.get('event', '').lower()]
    if tornado_watches:
        print("\n" + "=" * 80)
        print("🌪️  TORNADO WATCH SPECIFIC RECOMMENDATIONS")
        print("=" * 80)
        
        tw = tornado_watches[0]
        rank = scored.index(tw) + 1
        score = tw.get('threat_score', {}).get('score', 0)
        
        print(f"\nYour Tornado Watch is ranked #{rank} with score {score}")
        
        if rank > 3:
            print("\n⚠️  It's below the top 3, so it won't be announced automatically.")
            print("\nRECOMMENDED: Boost the score to ensure announcement:")
            print("\nEdit severity_scorer.py line 35:")
            print("  'tornado watch': 75,  # Raised from 45 to match severe warnings")
            print("\nThis ensures tornado watches are ALWAYS announced!")

print("\n" + "=" * 80)
