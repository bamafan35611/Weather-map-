# 🚀 Render Deployment Guide - Weather Map with Forecast History

## What's New

✅ **Enhanced Alert Speech** - Natural, conversational weather alerts
✅ **Forecast History System** - Track ML predictions and accuracy
✅ **PostgreSQL Support** - Database persists on Render
✅ **Auto-Verification** - Checks forecasts against NWS alerts every 30 min
✅ **State Names in Alerts** - "Madison County in Alabama"

## Files Updated

- `app.py` - Added forecast endpoints
- `forecast_db.py` - NEW: Database with PostgreSQL support
- `verification_service.py` - NEW: Auto-verification system  
- `static/RadarMap-optimized.html` - Enhanced alert speech
- `requirements.txt` - Added psycopg2-binary

## Step-by-Step Deployment

### 1. Add PostgreSQL Database (FREE)

In your Render dashboard:

1. Click "New +" → "PostgreSQL"
2. Name it: `weather-forecast-db`
3. Choose: **Free** plan
4. Click "Create Database"
5. **Copy the Internal Database URL** (starts with `postgres://`)

### 2. Connect Database to Your Service

1. Go to your web service
2. Click "Environment" tab
3. Add new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL URL you copied
4. Click "Save Changes"

### 3. Upload New Files

Upload these files to your Render service (via Git or manual upload):

```
forecast_db.py          ← NEW
verification_service.py ← NEW  
app.py                  ← UPDATED
requirements.txt        ← UPDATED
static/RadarMap-optimized.html ← UPDATED
```

### 4. Deploy

Render will automatically:
- Install `psycopg2-binary` 
- Create database tables
- Start verification loop
- Begin tracking forecasts

### 5. Verify It Works

After deployment completes:

**Check History Endpoint:**
```
https://your-app.onrender.com/api/learning/history
```

Should return:
```json
{
  "count": 0,
  "history": [],
  "stats": {...},
  "success": true
}
```

**Check Your Map:**
- Open your weather map
- Click "History" button
- Should say "No forecast history available yet"
- As ML predictions come in, history will populate!

## How the System Works

### Automatic Flow

1. **ML Predictions** → Your local PC sends predictions via ngrok
2. **Saved to Database** → Backend saves them to PostgreSQL
3. **Verification Runs** → Every 30 minutes, checks against NWS alerts
4. **Results Recorded** → Marked as correct/false positive/false negative
5. **History Displays** → Shows in your map's History panel

### Manual Triggers

**Trigger verification manually:**
```bash
curl -X POST https://your-app.onrender.com/api/learning/verify
```

**Get accuracy stats:**
```bash
curl https://your-app.onrender.com/api/learning/stats
```

## Environment Variables

Your Render service should have:

- `DATABASE_URL` - PostgreSQL connection (from Step 1)
- `LOCAL_ML_URL` - Your ngrok URL (already set)
- `PORT` - Auto-set by Render

## Troubleshooting

### History still empty after deployment

1. **Check logs** for "✓ Forecast tracking system loaded"
2. **Verify DATABASE_URL** is set correctly
3. **Wait for predictions** - Need ML system running
4. **Check database connection** in logs

### "Forecast system not available" error

- Database not connected
- Check DATABASE_URL format
- View logs for connection errors

### Verification not running

- Check logs for "✓ Background verification loop started"
- Manually trigger: `POST /api/learning/verify`
- Check NWS API access in logs

## Testing Locally (Optional)

Want to test before deploying to Render?

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (uses SQLite)
python app.py

# Add sample data
python add_sample_data.py

# Open browser
http://localhost:8000
```

## Database Schema

### forecasts table
Stores ML predictions with verification results

### actual_events table  
Stores real NWS alerts for matching

## What You'll See

After predictions accumulate and verify:

```
Weather History
Total Events: 15 | Accuracy: 73.33%

Nov 28, 2025 2:30 PM
Predicted severe_thunderstorm (moderate) for Madison County (85% confidence) - ✓ CORRECT

Nov 28, 2025 10:15 AM
Predicted tornado (severe) for Limestone County (78% confidence) - ✗ FALSE ALARM

Nov 27, 2025 6:45 PM
Predicted flash_flood (moderate) for Morgan County (92% confidence) - ✓ CORRECT
```

## Next Steps

1. ✅ Deploy to Render
2. ✅ Add PostgreSQL database
3. ✅ Set DATABASE_URL
4. ✅ Upload new files
5. ⏳ Wait for ML predictions
6. 📊 Watch accuracy improve!

## Support

Check Render logs for:
- ✓ Success messages
- ⚠ Warnings  
- 🔍 Verification activity
- Database operations

Everything logs to console for easy debugging!

---

**Questions?** Check the logs first - they show everything happening in real-time.
