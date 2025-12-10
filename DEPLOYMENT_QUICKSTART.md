# Quick Deployment Guide - Regional Monitoring Update

## What Changed
✅ **ONLY monitoring 14 counties now** (was monitoring nationwide ~3000+ counties)
- 11 North Alabama counties
- 3 Southern Tennessee counties (Giles, Lawrence, Lincoln)

## Counties Being Monitored

### Alabama (11)
- Colbert, Cullman, DeKalb, Franklin, Jackson, Lawrence, Lauderdale
- **Limestone (Athens)** ⭐
- **Madison (Huntsville)** ⭐
- Marshall, Morgan

### Tennessee (3)
- Franklin County, TN (Winchester)
- Lincoln County, TN (Fayetteville)
- Moore County, TN (Lynchburg)

## Deployment Steps

1. **Extract the zip file**
2. **Replace your current `static/RadarMap-optimized.html`** with the modified version
3. **Commit and push to your repository**
4. **Render will auto-deploy**

## Verification

After deployment, open browser console and look for:
```
✓ Fetching alerts for 14 monitored counties only...
✓ Retrieved X alerts for monitored area
```

**Before:** Would see "Retrieved 500+ national alerts"  
**After:** Will see "Retrieved 0-20 alerts for monitored area"

## Key Changes in Code

**File:** `static/RadarMap-optimized.html`  
**Line:** ~2613 (MONITORED_ZONES array)

Changed from fetching all nationwide alerts to only your 14 specific counties using NWS zone codes.

## Benefits

✅ No more California/Texas/Florida alerts  
✅ 100% relevant alerts for your area  
✅ Faster performance (less data to process)  
✅ Accurate Athens forecasts  
✅ Cleaner map display  

## To Modify Counties

Edit the `MONITORED_ZONES` array in line ~2613:

```javascript
const MONITORED_ZONES = [
    'ALC083',  // Your county
    'ALC089',  // Another county
    // Add more...
];
```

Find zone codes: https://www.weather.gov/ (enter city, check URL for zone code)

## Need Different TN Counties?

Current TN counties are Franklin, Lincoln, and Moore. To change:

1. Find the MONITORED_ZONES section (line ~2613)
2. Replace the TNC codes:
   - TNC051 = Franklin County, TN
   - TNC103 = Lincoln County, TN
   - TNC127 = Moore County, TN

Example other options:
- TNC061 = Giles County, TN
- TNC099 = Lawrence County, TN
- TNC117 = Marshall County, TN
- TNC119 = Maury County, TN

---

**Questions?** Check `REGIONAL_MONITORING_CHANGES.md` for full details.
