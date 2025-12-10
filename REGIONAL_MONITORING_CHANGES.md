# Regional Monitoring Changes - North Alabama & Southern Tennessee Only

## Overview
Modified NorthBamaWX to monitor ONLY North Alabama and southern Tennessee counties, eliminating nationwide alert noise.

## What Changed

### Before
- Fetched ALL nationwide alerts from NWS API (~500-1000+ alerts)
- Filtered/prioritized North Alabama after fetching
- Still displayed/processed alerts from all 50 states
- Created alert overload and unnecessary announcements

### After
- Fetches ONLY alerts for your specific monitored zones
- 11 North Alabama counties + 3 southern Tennessee counties = 14 zones total
- All alerts from monitored zones are automatically HIGH priority
- Dramatically reduced API load and processing overhead

## Monitored Counties

### North Alabama (11 counties)
- Colbert County
- Cullman County
- DeKalb County
- Franklin County
- Jackson County
- Lawrence County
- Lauderdale County
- Limestone County (Athens!)
- Madison County (Huntsville)
- Marshall County
- Morgan County

### Southern Tennessee (3 counties)
- Franklin County (Winchester)
- Lincoln County (Fayetteville)
- Moore County (Lynchburg)

## Technical Changes

### File Modified
`static/RadarMap-optimized.html` - `fetchAlerts()` function (lines ~2609-2656)

### Key Changes
1. **Added MONITORED_ZONES array** with FIPS codes for all 14 counties
2. **Changed NWS API call** from:
   ```javascript
   fetch('https://api.weather.gov/alerts/active')  // All nationwide
   ```
   To:
   ```javascript
   fetch('https://api.weather.gov/alerts/active?zone=ALC083&zone=ALC089&...')  // Only monitored
   ```
3. **Set all monitored alerts to HIGH priority** (no more LOW/MEDIUM from other states)
4. **Updated console logging** to reflect regional monitoring
5. **Changed source tag** from 'nws_national' to 'monitored_area'

## Benefits

### Performance
- **Reduced API response size** from ~1000 alerts to typically 0-20 alerts
- **Faster processing** - no need to filter through nationwide data
- **Less memory usage** - storing only relevant alerts

### Accuracy
- **No more false alarms** from California, Texas, Florida, etc.
- **100% relevance** - every alert is for your monitoring area
- **Clear Athens forecast** - system focuses on local conditions

### User Experience
- **No alert spam** from distant states
- **More responsive** - system reacts faster with less data
- **Cleaner display** - map shows only relevant alerts

## Configuration

### To Add More Counties
Edit the `MONITORED_ZONES` array in the fetchAlerts() function:
```javascript
const MONITORED_ZONES = [
    'ALC089',  // Madison County, AL
    'TNC037',  // Davidson County, TN
    'ALC999',  // Add new county here (use FIPS zone code)
];
```

### To Find FIPS Zone Codes
1. Visit: https://www.weather.gov/
2. Enter city/county name
3. Look at the URL - zone code appears as: `/your-office/zone/XXXNNN`
4. Format: 2-letter state + 3-digit county code (e.g., ALC089)

### Alert Filtering Still Active
- `MAX_ALERTS_PER_BATCH = 3` - Limits simultaneous announcements
- `WARNINGS_ONLY = true` - Only announces warnings (not watches/advisories)
- All alerts from monitored zones are automatically HIGH priority

## Deployment

### Files Changed
- `static/RadarMap-optimized.html` (main change)

### How to Deploy
1. Replace your current `RadarMap-optimized.html` with the modified version
2. Commit and push to your repository
3. Render will auto-deploy the changes
4. Test by checking console logs for "Retrieved X alerts for monitored area"

### Verification
After deployment, check the browser console:
- Should see: `Fetching alerts for 14 monitored counties only...`
- Should see: `Retrieved X alerts for monitored area` (not "national alerts")
- Alert count should be much lower (typically 0-20 instead of hundreds)

## Future Enhancements

### Possible Additions
1. **User-configurable zones** - Let users select counties via UI
2. **State-level monitoring** - Option to monitor entire state(s)
3. **Distance-based monitoring** - Monitor all counties within X miles of a point
4. **Saved profiles** - Store different monitoring configurations

### Not Recommended
- Don't go back to nationwide monitoring - too much noise
- Keep the zone list manageable (under 50 counties for best performance)
- Use watches for broader awareness instead of adding more counties

## Rollback Instructions

If you need to revert to nationwide monitoring:

Replace the MONITORED_ZONES section with:
```javascript
const nationalResponse = await fetch('https://api.weather.gov/alerts/active', {
    headers: {'Accept': 'application/geo+json'},
    timeout: 10000
});
```

And restore the old priority logic (check areaDesc for county names).

---

**Created:** December 2024  
**System:** NorthBamaWX / AtmosphericX  
**Purpose:** Regional weather intelligence for North Alabama & Southern Tennessee
