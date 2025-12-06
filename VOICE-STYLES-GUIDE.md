# 🗣️ NorthBamaWX Multiple Voice Styles - Complete Guide

## 🎯 What This Does

Your bot now has **4 different voice styles** that automatically match the threat level!

---

## 🎙️ The 4 Voice Styles

### 🟢 CALM (Scores 0-29)
**Used for:** Low-threat advisories, minor alerts

**Voice Settings:**
- Voice: Guy (professional male)
- Style: Newscast
- Speed: Normal
- Pitch: Normal
- Volume: Normal

**Example:**
```
"NorthBamaWX advisory. 
Wind Advisory for Decatur, Alabama. 
Threat Score: 25 out of 100. Low threat. 
Stay aware and monitor for updates."
```

**Tone:** Calm, informative, like a weather update

---

### 🟡 CONCERNED (Scores 30-69)
**Used for:** Watches, elevated threats

**Voice Settings:**
- Voice: Guy (professional male)
- Style: Newscast-casual
- Speed: +5% faster
- Pitch: +5% higher
- Volume: +5% louder

**Example:**
```
"NorthBamaWX weather update. 
Tornado Watch for North Alabama. 
Threat Score: 45 out of 100. Moderate threat. 
Monitor weather conditions and stay informed."
```

**Tone:** Attentive, slightly concerned, stay alert

---

### 🟠 URGENT (Scores 70-94)
**Used for:** Warnings, high/severe threats

**Voice Settings:**
- Voice: Davis (strong male)
- Style: Shouting
- Speed: +10% faster
- Pitch: +10% higher
- Volume: +10% louder

**Example:**
```
"NorthBamaWX URGENT ALERT! 
Tornado Warning for Oklahoma City, Oklahoma! 
Threat Score: 90 out of 100! SEVERE threat! 
Seek shelter in a sturdy building! 
Stay away from windows! Stay safe!"
```

**Tone:** Fast, loud, emphatic, take action NOW

---

### 🔴 EMERGENCY (Scores 95-100)
**Used for:** Tornado emergencies, extreme threats

**Voice Settings:**
- Voice: Davis (strong male)
- Style: Angry
- Speed: +15% faster (very fast)
- Pitch: +15% higher (very high)
- Volume: +20% louder (LOUD!)

**Example:**
```
"ATTENTION! EMERGENCY WEATHER ALERT! 
Tornado Emergency NOW in effect for Moore, Oklahoma! 
NorthBamaWX Threat Score: 100 out of 100! EXTREME DANGER! 
TAKE SHELTER IMMEDIATELY! GO TO YOUR SAFE PLACE NOW! 
Basement or interior room on lowest floor! PROTECT YOUR HEAD! 
This is NorthBamaWX!"
```

**Tone:** YELLING, COMMANDING, LIFE OR DEATH URGENCY

---

## 🎯 How It Works

### Automatic Style Selection

```
Alert Comes In
      ↓
Calculate Threat Score (0-100)
      ↓
  Score 95-100? → EMERGENCY Voice 🔴
  Score 85-94?  → EMERGENCY Voice 🔴
  Score 70-84?  → URGENT Voice 🟠
  Score 50-69?  → CONCERNED Voice 🟡
  Score 30-49?  → CONCERNED Voice 🟡
  Score 0-29?   → CALM Voice 🟢
```

**No manual selection needed!** System picks automatically! ✅

---

## 🆕 API Endpoints

### 1. Get Voice Announcement for Single Alert
```bash
GET /api/voice/announcement/<alert_id>
```

**Response:**
```json
{
  "success": true,
  "announcement": {
    "text": "ATTENTION! EMERGENCY WEATHER ALERT!...",
    "ssml": "<speak>...</speak>",
    "style": "emergency",
    "threat_score": 100
  },
  "alert": {...},
  "threat_score": 100
}
```

---

### 2. Get ALL Voice Announcements (Sorted by Threat)
```bash
GET /api/voice/announcements/all
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "announcements": [
    {
      "alert_id": "urn:oid:...",
      "event": "Tornado Warning",
      "location": "Oklahoma City, OK",
      "threat_score": 90,
      "voice_style": "emergency",
      "text": "ATTENTION! EMERGENCY WEATHER ALERT!...",
      "ssml": "<speak>...</speak>"
    },
    {
      "event": "Severe Thunderstorm Warning",
      "location": "Atlanta, GA",
      "threat_score": 75,
      "voice_style": "urgent",
      "text": "NorthBamaWX URGENT ALERT...",
      "ssml": "<speak>...</speak>"
    }
  ],
  "highest_threat": {...}
}
```

---

### 3. Get Pre-Alert Voice Announcements
```bash
GET /api/voice/pre-alert-announcements
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "announcements": [
    {
      "alert_type": "Tornado Warning",
      "location": "Oklahoma City, OK",
      "confidence": 87.3,
      "voice_style": "urgent",
      "text": "NorthBamaWX AI PREDICTION ALERT...",
      "ssml": "<speak>...</speak>"
    }
  ]
}
```

---

### 4. Generate Custom Voice (Advanced)
```bash
POST /api/voice/custom
Content-Type: application/json

{
  "text": "This is a test announcement",
  "threat_score": 95
}
```

**Response:**
```json
{
  "success": true,
  "text": "This is a test announcement",
  "ssml": "<speak>...</speak>",
  "voice_style": "emergency",
  "threat_score": 95
}
```

---

## 🔧 Integration with Your Voice System

### JavaScript Example (For OBS/Browser):

```javascript
// Fetch and speak alert with automatic voice styling
async function speakAlert(alertId) {
    const response = await fetch(`/api/voice/announcement/${alertId}`);
    const data = await response.json();
    
    if (data.success) {
        const announcement = data.announcement;
        
        console.log(`Speaking with ${announcement.style.toUpperCase()} voice`);
        console.log(`Threat Score: ${announcement.threat_score}/100`);
        
        // Use the text for simple TTS
        speakText(announcement.text);
        
        // OR use SSML for Azure TTS (better quality)
        speakWithAzureTTS(announcement.ssml);
    }
}

// Speak all active alerts in priority order
async function speakAllAlerts() {
    const response = await fetch('/api/voice/announcements/all');
    const data = await response.json();
    
    if (data.success && data.announcements.length > 0) {
        console.log(`Speaking ${data.count} alerts...`);
        
        for (const announcement of data.announcements) {
            console.log(`\n${announcement.voice_style.toUpperCase()}: ${announcement.event}`);
            
            // Speak the announcement
            speakText(announcement.text);
            
            // Wait 3 seconds between announcements
            await sleep(3000);
        }
    } else {
        console.log("No active alerts to announce");
    }
}

// Speak pre-alerts
async function speakPreAlerts() {
    const response = await fetch('/api/voice/pre-alert-announcements');
    const data = await response.json();
    
    if (data.success && data.announcements.length > 0) {
        for (const announcement of data.announcements) {
            speakText(announcement.text);
            await sleep(3000);
        }
    }
}

// Helper function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## 🎬 Real-World Example

### Tornado Warning Scenario:

**Alert Received:**
- Event: Tornado Warning
- Location: Oklahoma City
- Threat Score: 90/100

**System Automatically:**
1. ✅ Calculates score (90)
2. ✅ Selects EMERGENCY voice
3. ✅ Formats announcement
4. ✅ Generates SSML
5. ✅ Returns via API

**Your Code:**
```javascript
// Just call the API
const data = await fetch('/api/voice/announcement/alert123').then(r => r.json());

// Speak it - voice style already selected!
speak(data.announcement.text);
```

**Result:**
```
🔴 EMERGENCY VOICE:
"ATTENTION! EMERGENCY WEATHER ALERT! 
Tornado Warning NOW in effect for Oklahoma City! 
Threat Score: 90 out of 100! EXTREME DANGER! 
TAKE SHELTER IMMEDIATELY!"
```

**Voice:** Fast, loud, commanding, like a 911 operator!

---

## ✨ Special Features

### 1. Automatic Word Emphasis

Emergency/Urgent voices automatically emphasize critical words:

**Emphasized Words:**
- WARNING
- EMERGENCY
- TORNADO
- SHELTER
- IMMEDIATELY
- DANGEROUS
- SEVERE
- EXTREME
- TAKE COVER
- NOW

**In SSML:**
```xml
<emphasis level="strong">TORNADO</emphasis>
<emphasis level="strong">IMMEDIATELY</emphasis>
```

### 2. Dynamic Announcements

Different announcements based on alert type:

**Tornado:**
```
"TAKE SHELTER IMMEDIATELY! GO TO YOUR SAFE PLACE NOW!
Basement or interior room on lowest floor! PROTECT YOUR HEAD!"
```

**Flood:**
```
"EVACUATE TO HIGHER GROUND NOW! 
DO NOT DRIVE THROUGH WATER!"
```

**Wind:**
```
"Seek shelter indoors! Secure loose objects! Avoid windows!"
```

### 3. Pre-Alert Styling

Pre-alerts use urgent/emergency voice:

**High Confidence (85%+):**
```
⚡ EMERGENCY Voice:
"ATTENTION! NorthBamaWX AI PREDICTION ALERT! CRITICAL!"
```

**Medium Confidence (70-84%):**
```
🟠 URGENT Voice:
"NorthBamaWX AI PREDICTION ALERT..."
```

---

## 🎯 Voice Comparison

### Same Alert, Different Threats:

**Wind Advisory (Score: 25) - CALM:**
```
Normal voice, normal speed:
"NorthBamaWX advisory. Wind Advisory. 
Stay aware and monitor for updates."
```

**Tornado Watch (Score: 45) - CONCERNED:**
```
Slightly faster, more concerned:
"NorthBamaWX weather update. Tornado Watch. 
Monitor weather conditions and stay informed."
```

**Tornado Warning (Score: 90) - EMERGENCY:**
```
VERY FAST, VERY LOUD:
"ATTENTION! EMERGENCY WEATHER ALERT! 
Tornado Warning! TAKE SHELTER IMMEDIATELY!"
```

**Same info, TOTALLY different delivery!** 🎙️

---

## 📊 When Each Style is Used

### Current 40 Active Alerts:

Based on your current alerts:
- **EMERGENCY (88):** 1 alert (High Wind Warning - Alaska)
- **HIGH (77):** 5 alerts (Various High Wind Warnings)
- **ELEVATED (49-57):** 2 alerts (Flood Watches)
- **MODERATE (28-46):** 32 alerts (Coastal floods, wind advisories)

**Each would be announced with appropriate voice style!**

---

## 🚀 How to Test

### Test with Real Alerts:
```bash
# Get all alerts with voice styling
curl https://weather-map-zfln.onrender.com/api/voice/announcements/all
```

**You'll see:**
- Highest threat first (emergency voice)
- All announcements formatted
- SSML ready for Azure TTS
- Voice styles assigned

### Test Output:
```json
{
  "announcements": [
    {
      "event": "High Wind Warning",
      "threat_score": 88,
      "voice_style": "emergency",  ← Automatic!
      "text": "ATTENTION! EMERGENCY WEATHER ALERT!..."
    },
    {
      "event": "Flood Watch",
      "threat_score": 57,
      "voice_style": "concerned",  ← Automatic!
      "text": "NorthBamaWX weather update..."
    }
  ]
}
```

---

## 💡 Integration Tips

### For OBS Voice Relay:

1. **Poll the API every minute:**
   ```javascript
   setInterval(speakAllAlerts, 60000);
   ```

2. **Speak announcements in order:**
   - Highest threat first
   - Automatic voice styling
   - 3-second pause between alerts

3. **Voice will automatically match threat:**
   - No manual configuration
   - Just fetch and speak!

### For Scheduled Broadcasts:

**Every hour on :00** - Nationwide update:
```javascript
// Speak top 5 threats
const data = await fetch('/api/voice/announcements/all').then(r => r.json());
for (let i = 0; i < Math.min(5, data.count); i++) {
    speak(data.announcements[i].text);
}
```

**Every hour on :30** - Local update:
```javascript
// Filter for local area
const data = await fetch('/api/voice/announcements/all').then(r => r.json());
const local = data.announcements.filter(a => 
    a.location.includes('Alabama') || 
    a.location.includes('Huntsville') ||
    a.location.includes('Decatur')
);
local.forEach(a => speak(a.text));
```

---

## 🎊 What You Get

✅ **4 voice styles** - Calm → Concerned → Urgent → Emergency  
✅ **Automatic selection** - Based on threat score  
✅ **Dynamic emphasis** - Critical words highlighted  
✅ **SSML generation** - Azure TTS ready  
✅ **API endpoints** - Easy integration  
✅ **Pre-alert support** - Predictions get urgent voice  
✅ **Custom text** - Generate voice for anything  

---

## 📦 Files Added

- ✅ `voice_styles.py` (15KB) - Voice engine
- ✅ API endpoints in `app.py` - 4 new endpoints
- ✅ This guide - Complete documentation

**No new requirements!** Uses existing system ✅

---

## 🎯 Quick Start

### 1. Deploy to Render
Upload your updated files

### 2. Test API
```bash
curl https://weather-map-zfln.onrender.com/api/voice/announcements/all
```

### 3. Integrate with Voice
```javascript
const data = await fetch('/api/voice/announcements/all').then(r => r.json());
data.announcements.forEach(a => speak(a.text));
```

### 4. Done!
Voice automatically matches threat level! 🎙️

---

## 🔥 The Difference It Makes

### Before:
```
Same boring voice every time:
"Tornado warning for Oklahoma City."
```
😴 Viewers tune out

### After:
```
Threat 25: "NorthBamaWX advisory..."
          (calm, normal)
          
Threat 75: "NorthBamaWX URGENT ALERT! Tornado warning..."
          (fast, loud, serious)
          
Threat 100: "ATTENTION! EMERGENCY! TAKE SHELTER NOW!"
           (VERY FAST, VERY LOUD, COMMANDING)
```
👀 Viewers PAY ATTENTION!

---

## 🎊 Your Bot is Now Professional!

**Sounds like a real meteorologist:**
- Calm for advisories
- Concerned for watches
- Urgent for warnings
- EMERGENCY for life-threatening situations

**Deploy and your bot will speak with emotion!** 🗣️⚡

---

**NorthBamaWX: The bot that knows when to whisper and when to YELL!** 📢
