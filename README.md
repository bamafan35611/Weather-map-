# 🌩️ NorthBamaWX - AI-Powered Weather Intelligence System

**Professional weather broadcasting bot for North Alabama and Southern Tennessee**

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📡 Overview

NorthBamaWX is a sophisticated weather intelligence platform that monitors 14 counties across North Alabama and Southern Tennessee, providing automated weather broadcasts every 15 minutes with real-time severe weather alerts, storm reports, and AI-powered forecast analysis.

**Coverage Area:**
- **Alabama**: Madison, Limestone, Morgan, Lauderdale, Colbert, Franklin, Lawrence, Cullman, Marshall, DeKalb, Blount Counties
- **Tennessee**: Giles, Lincoln, Franklin Counties
- **Total Population Monitored**: ~1.4 million residents

---

## ✨ Features

### 🎙️ Automated Broadcasting
- **:00** - Regional weather briefing with storm reports, air quality, weekend outlook
- **:15** - Top weather alerts with severity scoring and impact predictions
- **:30** - Athens, AL local forecast with current conditions
- **:45** - Weather stories and historical comparisons

### 🚨 Advanced Alert System
- Real-time NWS alert monitoring
- Severity scoring and threat assessment
- **Alert impact predictions** - Population and city analysis
- Storm motion tracking
- Alert cooldown system (prevents spam)
- Watch callouts for regional awareness

### 🌪️ Multi-Source Storm Reports
- **NWS Local Storm Reports (LSR)** - Official reports
- **SpotterNetwork Integration** - Trained weather spotter reports
- Hail size translation (golf ball, baseball, etc.)
- Wind damage assessments
- Tornado and funnel cloud reports
- Flash flood reports

### 🤖 Machine Learning & AI
- **SQLite-based ML system** - Forecast accuracy tracking
- Pattern recognition for weather trends
- Historical forecast verification
- Continuous model improvement
- Temperature trend analysis
- Natural language processing for announcements

### 🎨 Voice & Style System
- Dynamic voice styling based on alert severity
- Azure Text-to-Speech integration
- Holiday greetings (Christmas, New Year's, etc.)
- Natural conversational tone
- Regional-specific commentary

### 🌬️ Environmental Monitoring
- **Air Quality Index (AQI)** tracking
- Temperature and wind data
- Precipitation monitoring
- Weekend weather outlooks (Friday PM & Saturday)
- SPC severe weather outlooks

### 📊 Data Visualization
- Interactive Mapbox radar display
- Warning polygon overlay
- Real-time alert highlighting
- Multi-county coverage maps

---

## 🏗️ Architecture

### Backend (Python/Flask)
```
Flask API Server
├── Alert Processing (local_predictor.py)
├── Storm Reports (storm_reports.py, spotternetwork.py)
├── Impact Predictions (impact_predictor.py)
├── ML System (forecast_db.py, auto_retrain.py)
├── Voice Generation (announcement_variations.py, voice_styles.py)
├── Weather Data (nws_forecast_fetcher.py, weather_enhancements.py)
└── Air Quality (air_quality.py)
```

### Frontend (HTML/JavaScript)
```
Interactive Radar Map
├── Mapbox GL JS
├── Real-time WebSocket updates
├── Voice relay system
└── 15-minute broadcast timer
```

### Data Sources
- **National Weather Service (NWS)** - Alerts, forecasts, warnings
- **SpotterNetwork** - Trained spotter reports
- **EPA AirNow** - Air quality data
- **Storm Prediction Center (SPC)** - Severe weather outlooks
- **US Census Bureau** - Population data for impact predictions

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip
Git
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Weather-map.git
cd Weather-map
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
touch .env

# Add your credentials:
MAPBOX_TOKEN=your_mapbox_token_here
AZURE_SPEECH_KEY=your_azure_key_here
AZURE_SPEECH_REGION=your_region_here
```

4. **Run the application**
```bash
python app.py
```

5. **Access the interface**
```
Open browser to: http://localhost:5000
```

---

## 📦 Dependencies

### Core Libraries
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Requests** - HTTP library
- **NumPy** - Numerical computing
- **Scikit-learn** - Machine learning
- **Shapely** - Geometric operations

### Additional Libraries
- **PyTz** - Timezone handling
- **Astral** - Sun/moon calculations
- **WebSockets** - Real-time communication
- **Gunicorn** - Production WSGI server
- **Gevent** - Async networking

---

## 🎯 Deployment

### Render.com (Current)
```bash
# Automatic deployment from GitHub
git push origin main

# Render auto-deploys on push
# Check logs: https://dashboard.render.com
```

### N100 Mini PC (Planned - Phase 4)
- Ubuntu Server 24.04 LTS
- Systemd service for auto-start
- Local hardware control
- Enhanced ML capabilities

---

## 📊 System Stats

### Coverage
- **14 Counties** monitored
- **30+ Cities** tracked
- **~1.4 Million** residents in coverage area
- **100 Mile Radius** from Athens, AL

### Performance
- **15-minute** broadcast cycle
- **<2 second** alert processing
- **24/7** uptime monitoring
- **Multi-source** data aggregation

### Intelligence
- **ML-based** forecast verification
- **Population impact** analysis
- **Real-time** spotter integration
- **Historical** pattern recognition

---

## 🗂️ File Structure

```
Weather-map/
├── app.py                          # Main Flask application
├── local_predictor.py              # Alert processing & prediction
├── storm_reports.py                # Multi-source storm reports
├── spotternetwork.py               # SpotterNetwork API client
├── impact_predictor.py             # Population impact analysis
├── forecast_db.py                  # ML database system
├── auto_retrain.py                 # Automatic model retraining
├── announcement_variations.py      # Voice style management
├── voice_styles.py                 # Dynamic voice generation
├── weather_commentary.py           # Natural language generation
├── air_quality.py                  # AQI monitoring
├── nws_forecast_fetcher.py         # NWS data fetching
├── weather_enhancements.py         # Environmental data
├── holiday_greetings.py            # Seasonal messages
├── local_cities.py                 # City database
├── city_rotation.py                # Random city selection
├── requirements.txt                # Python dependencies
└── static/
    └── RadarMap-optimized.html     # Interactive frontend
```

---

## 🛠️ Configuration

### Monitored Counties
Edit `local_predictor.py` to modify coverage area:
```python
MONITORED_ZONES = {
    'ALZ001', 'ALZ002', 'ALZ003',  # Alabama zones
    'TNZ001', 'TNZ002', 'TNZ003'   # Tennessee zones
}
```

### Broadcast Schedule
Modify timing in `static/RadarMap-optimized.html`:
```javascript
// :00 - Regional Briefing
// :15 - Top Alerts
// :30 - Athens Local
// :45 - Weather Story
```

### Voice Settings
Adjust Azure TTS parameters in voice relay system:
```python
AZURE_SPEECH_KEY = "your_key"
AZURE_SPEECH_REGION = "your_region"
VOICE_NAME = "en-US-JennyNeural"
```

---

## 📈 Roadmap

### Phase 3 ✅ (Current - Complete!)
- [x] Storm reports at :00 broadcasts
- [x] SpotterNetwork integration
- [x] Alert impact predictions

### Phase 4 🔮 (Next - N100 Migration)
- [ ] Migrate to N100 mini PC
- [ ] Deep learning weather models
- [ ] Enhanced radar processing
- [ ] Historical weather analysis
- [ ] Local sensor integration

### Future Enhancements
- [ ] APRS ham radio integration
- [ ] Scanner audio monitoring (Broadcastify)
- [ ] School closure predictions
- [ ] Infrastructure impact analysis
- [ ] Mobile app development
- [ ] Web dashboard with analytics

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

### Data Sources
- **National Weather Service** - Weather data and alerts
- **SpotterNetwork** - Trained spotter reports
- **EPA AirNow** - Air quality data
- **Storm Prediction Center** - Severe weather outlooks
- **US Census Bureau** - Population statistics

### Technologies
- **Mapbox** - Interactive mapping
- **Azure Cognitive Services** - Text-to-Speech
- **Anthropic Claude** - AI assistance
- **Python/Flask** - Backend framework
- **Scikit-learn** - Machine learning

### Special Thanks
- Local storm spotters and ham radio operators
- NWS Huntsville forecast office
- Weather enthusiast community
- Open source contributors

---

## 📞 Contact

**Project Maintainer**: Michael  
**System**: NorthBamaWX  
**Coverage**: North Alabama & Southern Tennessee  
**GitHub**: [Weather-map](https://github.com/yourusername/Weather-map)

---

## 📊 Statistics

![GitHub Stars](https://img.shields.io/github/stars/yourusername/Weather-map?style=social)
![GitHub Forks](https://img.shields.io/github/forks/yourusername/Weather-map?style=social)
![GitHub Issues](https://img.shields.io/github/issues/yourusername/Weather-map)
![GitHub Last Commit](https://img.shields.io/github/last-commit/yourusername/Weather-map)

---

## 🌟 Key Highlights

### 🎯 Accuracy
- ML-verified forecast tracking
- Continuous model improvement
- Historical pattern analysis

### 🚀 Speed
- <2 second alert processing
- Real-time spotter integration
- 15-minute broadcast cycle

### 🧠 Intelligence
- Population impact predictions
- Multi-source data fusion
- Natural language generation

### 📡 Coverage
- 14 counties monitored
- 1.4 million residents protected
- 30+ cities tracked

---

## 🔥 Recent Updates

### Version 3.0 (Phase 3 Complete!)
- ✅ Added alert impact predictions with population analysis
- ✅ Integrated SpotterNetwork for trained spotter reports
- ✅ Enhanced storm reports at :00 broadcasts
- ✅ Multi-source data aggregation (NWS + SpotterNetwork)
- ✅ City and population tracking for all 14 counties

### Version 2.0 (Phase 2)
- ✅ Added air quality monitoring
- ✅ Weekend outlook announcements
- ✅ Storm reports system
- ✅ Holiday greetings
- ✅ Voice style variations

### Version 1.0 (Phase 1)
- ✅ Core alert monitoring
- ✅ ML forecast tracking
- ✅ 15-minute broadcast cycle
- ✅ Interactive radar map
- ✅ Voice relay system

---

<div align="center">

### Made with ❤️ for North Alabama & Southern Tennessee

**Keeping communities safe, one broadcast at a time** 🌩️

[⬆ Back to Top](#-northbamawx---ai-powered-weather-intelligence-system)

</div>
