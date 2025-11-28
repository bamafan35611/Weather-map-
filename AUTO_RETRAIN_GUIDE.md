# 🤖 Automatic Model Retraining System

## What It Does

Your weather prediction model now **automatically improves itself** based on real-world results!

### The Learning Loop:

1. **ML makes predictions** → Saved to database
2. **Verification happens** → Checks against actual weather (every 30 min)
3. **Model retrains** → Uses verified data to improve (every 12 hours)
4. **New model deploys** → Better predictions automatically

## How It Works

### Automatic Schedule

**Every 30 minutes:**
- Verifies forecasts against NWS alerts
- Marks predictions as correct/incorrect

**Every 12 hours:**
- Checks if retraining is needed
- Requires minimum 20 verified forecasts
- Must be 7+ days since last retrain
- Trains new model on accumulated data
- Replaces old model automatically

### What Gets Better

The model learns from:
- ✓ **Correct predictions** - Patterns that work
- ✗ **False positives** - When it was too aggressive
- ✗ **False negatives** - When it missed events

### Training Features

The model considers:
- Prediction type (tornado, thunderstorm, etc.)
- Severity level
- Confidence score
- Location (lat/lon)
- Time of day / day of week
- Weather conditions (temp, humidity, wind)

## Retraining Requirements

**Minimum criteria:**
- At least 20 verified forecasts
- 7+ days since last retrain
- Valid training data available

**Safety features:**
- Backs up old model before retraining
- Logs all retraining events
- Validates new model accuracy
- Falls back if training fails

## API Endpoints

### POST /api/learning/retrain
Manually trigger retraining (runs in background)

```bash
curl -X POST https://your-app.onrender.com/api/learning/retrain
```

**Response:**
```json
{
  "success": true,
  "message": "Model retraining started in background"
}
```

### GET /api/learning/retrain/status
Check retraining history

```bash
curl https://your-app.onrender.com/api/learning/retrain/status
```

**Response:**
```json
{
  "success": true,
  "retrain_count": 3,
  "last_retrain": {
    "timestamp": "2025-11-28T14:30:00",
    "num_forecasts": 45,
    "num_samples": 45,
    "metrics": {
      "train_accuracy": 0.82,
      "test_accuracy": 0.78,
      "overall_accuracy": 0.80,
      "num_samples": 45
    }
  },
  "history": [...]
}
```

## Files Created

**auto_retrain.py** - Main retraining logic
- Fetches verified forecasts from database
- Prepares training data
- Trains new RandomForest model
- Saves and deploys updated model

**models/retrain_log.json** - Retraining history
- Tracks all retraining events
- Stores accuracy metrics
- Shows improvement over time

**models/forecast_model_backup.pkl** - Safety backup
- Previous model saved before each retrain
- Can restore if new model fails

## Monitoring Retraining

### Check Logs

In your Render logs, look for:

```
🔄 Starting automatic model retraining...
✓ Fetched 45 verified forecasts
✓ Proceeding with retrain on 45 verified forecasts
✓ Prepared 45 training samples
✓ Backed up current model
✓ Model trained:
  - Training accuracy: 82.00%
  - Testing accuracy: 78.00%
  - Overall accuracy: 80.00%
✓ Saved new model
✅ RETRAIN COMPLETE!
   - New model accuracy: 80.00%
   - Trained on 45 samples
```

### View Retrain History

```bash
# Get full status
curl https://your-app.onrender.com/api/learning/retrain/status

# Pretty print with jq
curl -s https://your-app.onrender.com/api/learning/retrain/status | jq .
```

## Expected Timeline

### Week 1-2
- System collects predictions
- Verification builds dataset
- Not enough data yet

### Week 3
- ✅ **First retrain!** (20+ forecasts)
- Model improves based on real data
- Accuracy baseline established

### Month 2+
- Retrains every 1-2 weeks
- Continuous improvement
- Accuracy trends upward

## Performance Tracking

Each retrain logs:
- Number of training samples
- Training accuracy
- Testing accuracy
- Overall model performance

**Example progression:**
```
Retrain 1: 20 samples → 65% accuracy
Retrain 2: 45 samples → 72% accuracy
Retrain 3: 78 samples → 78% accuracy
Retrain 4: 120 samples → 83% accuracy
```

## Manual Retraining

Want to force a retrain?

```bash
# Trigger retraining now
curl -X POST https://your-app.onrender.com/api/learning/retrain
```

**Note:** Still requires minimum 20 verified forecasts

## Safety Features

### Backup System
- Old model backed up before each retrain
- Can manually restore if needed:
  ```bash
  cp models/forecast_model_backup.pkl models/forecast_model.pkl
  ```

### Validation
- New model tested on holdout data
- Accuracy metrics logged
- Training errors caught and logged

### Fail-Safe
- If retraining fails, old model stays active
- System continues with existing predictions
- Error logged for investigation

## Configuration

Edit `auto_retrain.py` to adjust:

```python
# Minimum forecasts before retraining
MIN_FORECASTS_FOR_RETRAIN = 20  # Lower = retrain sooner

# Days between retrains
if days_since < 7:  # Change 7 to your preference
    return False
```

Edit `app.py` to change schedule:

```python
# Retrain every X checks (currently 24 = 12 hours)
if check_count % 24 == 0:  # Change 24 to adjust frequency
    auto_retrain()
```

## Troubleshooting

### Retraining not happening

**Check requirements:**
- Minimum 20 verified forecasts?
- 7+ days since last retrain?
- Check logs for error messages

**View status:**
```bash
curl https://your-app.onrender.com/api/learning/retrain/status
```

### Model accuracy not improving

**Possible causes:**
- Not enough diverse data yet
- Need more weather events
- Feature engineering could improve

**Give it time:**
- Needs 50+ verified forecasts
- Several weather events
- Different conditions

### Training errors

**Check logs for:**
- Database connection issues
- Missing forecast data
- Invalid feature values

**Solutions:**
- Verify DATABASE_URL is set
- Check forecast_db.py is working
- Review verification results

## What You Get

### Continuous Improvement
- Model gets smarter over time
- Learns from real weather events
- Adapts to local patterns

### No Manual Work
- Fully automatic
- Runs in background
- Self-improving

### Transparency
- Full retraining logs
- Accuracy tracking
- Performance metrics

## Advanced: Feature Engineering

Want to improve the model? Edit the feature extraction in `auto_retrain.py`:

```python
def prepare_training_data(self, forecasts):
    # Add more features here:
    features.append(pressure_reading)
    features.append(cloud_cover)
    features.append(storm_motion)
    # etc.
```

Better features = better predictions!

## Summary

Your ML model now:
- ✅ Learns from real weather events
- ✅ Retrains automatically every 1-2 weeks
- ✅ Improves accuracy over time
- ✅ Requires zero manual intervention
- ✅ Logs all improvements

**The system literally gets smarter as you use it!** 🧠✨

---

## Quick Reference

```bash
# Check retrain status
curl https://your-app.onrender.com/api/learning/retrain/status

# Force retrain now
curl -X POST https://your-app.onrender.com/api/learning/retrain

# View accuracy stats
curl https://your-app.onrender.com/api/learning/stats

# Check verification history
curl https://your-app.onrender.com/api/learning/history
```

Your weather bot is now a true learning system! 🤖🌦️
