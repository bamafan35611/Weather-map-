# 15-Minute Rotating Broadcast System

## Overview
Your NorthBamaWX system now speaks **every 15 minutes** with a rotating cycle to keep updates fresh and interesting!

## The Schedule

### **:00** - Top of Hour: Alert Status Update
**Example:** "It's 2 o'clock Central. Currently monitoring conditions across North Alabama and southern Tennessee. All clear at this time. No weather alerts in effect across the monitoring area."

**Focus:** Quick status check
- Time announcement
- Current alert count
- Brief status

### **:15** - Quarter Past: Brief Weather Summary  
**Example:** "Quarter past the hour. Conditions remain calm across North Alabama and southern Tennessee. All clear at this time."

**Focus:** Simple conditions update
- Very brief
- Current state
- Quick check-in

### **:30** - Half Past: Detailed Regional Update
**Example:** "It's 2:30 Central. Here's your North Alabama and southern Middle Tennessee weather update, including Athens and surrounding areas. Skies are generally quiet across North Alabama and southern Middle Tennessee at this time, with no major weather alerts in effect."

**Focus:** Full comprehensive update
- Detailed conditions
- County-by-county breakdown
- Most thorough update of the cycle

### **:45** - Quarter Till: Alert Check + Outlook
**Example:** "Quarter till the hour. Checking the radar across North Alabama and southern Tennessee. All clear. Expect calm conditions continuing into the 3 o'clock hour."

**Focus:** Current status + what's ahead
- Radar check
- Current alerts
- Brief outlook for next hour

---

## Benefits of This System

✅ **Never Repetitive** - Each update has a different focus  
✅ **Constant Monitoring** - Something every 15 minutes  
✅ **Professional** - Sounds like a real weather broadcast  
✅ **Variety** - Keeps listeners engaged  
✅ **Regional Only** - Never mentions nationwide weather  

## Update Length by Time

- **:00** - ~10-15 seconds (brief)
- **:15** - ~8-10 seconds (very brief)
- **:30** - ~20-30 seconds (detailed)
- **:45** - ~12-18 seconds (medium)

**Average:** ~15 seconds per update  
**Total talk time:** ~1 minute per hour

## What Happened to Old System

### Removed:
❌ Nationwide hourly update (was talking about the country)  
❌ Separate :30 local update scheduler  
❌ Top-of-hour scheduler

### Replaced With:
✅ Unified rotating 15-minute system  
✅ All updates are regional (North Alabama + Southern Tennessee)  
✅ Triggered automatically every 15 minutes  

## Examples During Different Conditions

### All Clear Day
- **:00** - "It's 2 o'clock Central. All clear at this time."
- **:15** - "Quarter past. Conditions remain calm."
- **:30** - "It's 2:30. Here's your North Alabama weather update... [detailed]"
- **:45** - "Quarter till. All clear. Expect calm conditions into the 3 o'clock hour."

### Active Weather Day
- **:00** - "It's 2 o'clock Central. Currently tracking 2 active warnings affecting the region."
- **:15** - "Quarter past. Weather conditions remain active with 2 warnings ongoing."
- **:30** - "It's 2:30. Here's your North Alabama weather update. Stronger weather is impacting parts of North Alabama... [detailed]"
- **:45** - "Quarter till. 2 severe thunderstorm warnings continue. Monitoring through the 3 o'clock hour."

## Technical Details

### How It Works
1. Main timer checks every second
2. At :00, :15, :30, :45 - triggers `checkForBriefing()`
3. `checkForBriefing()` calls appropriate function based on minute:
   - minute === 0 → `runTopOfHourUpdate()`
   - minute === 15 → `runQuarterPastUpdate()`
   - minute === 30 → `runHalfPastUpdate()` (calls existing detailed function)
   - minute === 45 → `runQuarterTillUpdate()`

### Voice Announcements
- All use your existing `speakText()` function
- Non-blocking (won't freeze the map)
- Can be disabled with voice toggle

### Alert Processing
- If an alert is being processed, briefing waits
- Prevents overlapping announcements
- Maintains clean audio flow

## Customization

Want to change what's said? Edit these functions in `RadarMap-optimized.html`:
- `runTopOfHourUpdate()` - Line ~1086
- `runQuarterPastUpdate()` - Line ~1130
- `runHalfPastUpdate()` - Line ~1160  
- `runQuarterTillUpdate()` - Line ~1165

---

**Result:** Professional, engaging, regional-only weather broadcasts every 15 minutes that never get repetitive!
