"""
aprs_integration.py - NorthBamaWX APRS Ham Radio Integration
Real-time weather reports from amateur radio operators via APRS network
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class APRSIntegration:
    """Fetches weather reports from APRS (Automatic Packet Reporting System)"""
    
    # Your coverage area (North Alabama + Southern Tennessee)
    COVERAGE_BOUNDS = {
        'min_lat': 34.0,   # Southern edge
        'max_lat': 35.5,   # Northern edge
        'min_lon': -88.0,  # Western edge
        'max_lon': -85.5   # Eastern edge
    }
    
    # APRS.fi API endpoint (FREE!)
    APRS_API_BASE = "https://api.aprs.fi/api/get"
    
    def __init__(self, api_key: str = ""):
        """
        Initialize APRS integration
        
        Args:
            api_key: APRS.fi API key (optional - use public tier if not provided)
        """
        self.api_key = api_key or "public"  # Use public API if no key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NorthBamaWX/4.0 (APRS Weather Integration)'
        })
    
    def get_weather_reports(self, hours_back: int = 6) -> List[Dict]:
        """
        Fetch weather reports from APRS network
        
        Args:
            hours_back: How many hours back to search
            
        Returns:
            List of weather report dictionaries
        """
        try:
            # Calculate bounding box for query
            bounds = self.COVERAGE_BOUNDS
            
            # APRS.fi API parameters
            params = {
                'name': '*',  # All stations
                'what': 'wx',  # Weather reports only
                'apikey': self.api_key,
                'format': 'json'
            }
            
            logger.info(f"Fetching APRS weather reports for last {hours_back} hours")
            
            response = self.session.get(
                self.APRS_API_BASE,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"APRS API returned status {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('result') != 'ok':
                logger.warning(f"APRS API error: {data.get('description', 'Unknown error')}")
                return []
            
            # Parse and filter reports
            reports = self._parse_reports(data, hours_back)
            
            logger.info(f"Found {len(reports)} APRS weather reports in coverage area")
            
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching APRS reports: {e}")
            return []
    
    def _parse_reports(self, data: Dict, hours_back: int) -> List[Dict]:
        """Parse APRS data and filter for our coverage area and timeframe"""
        reports = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        try:
            entries = data.get('entries', [])
            
            for entry in entries:
                # Check if in our coverage area
                if not self._is_in_coverage(entry):
                    continue
                
                # Parse report
                report = self._extract_report_info(entry)
                
                if report:
                    # Check if within time window
                    report_time = report.get('timestamp')
                    if report_time and report_time >= cutoff_time:
                        reports.append(report)
        
        except Exception as e:
            logger.error(f"Error parsing APRS reports: {e}")
        
        return reports
    
    def _is_in_coverage(self, entry: Dict) -> bool:
        """Check if station is in our coverage area"""
        try:
            lat = float(entry.get('lat', 0))
            lon = float(entry.get('lng', 0))
            
            bounds = self.COVERAGE_BOUNDS
            
            if (bounds['min_lat'] <= lat <= bounds['max_lat'] and
                bounds['min_lon'] <= lon <= bounds['max_lon']):
                return True
        
        except (ValueError, TypeError):
            pass
        
        return False
    
    def _extract_report_info(self, entry: Dict) -> Optional[Dict]:
        """Extract relevant information from APRS entry"""
        try:
            # Parse timestamp
            time_str = entry.get('time', '')
            try:
                timestamp = datetime.fromtimestamp(int(time_str))
            except:
                timestamp = datetime.utcnow()
            
            # Extract weather data
            report = {
                'source': 'APRS',
                'callsign': entry.get('name', 'Unknown'),
                'timestamp': timestamp,
                'lat': float(entry.get('lat', 0)),
                'lon': float(entry.get('lng', 0)),
                'comment': entry.get('comment', ''),
                'weather': {}
            }
            
            # Parse weather parameters
            temp = entry.get('temp')
            if temp:
                try:
                    # Convert Celsius to Fahrenheit
                    temp_f = (float(temp) * 9/5) + 32
                    report['weather']['temperature'] = round(temp_f, 1)
                except:
                    pass
            
            # Wind data
            wind_dir = entry.get('wind_direction')
            wind_speed = entry.get('wind_speed')
            wind_gust = entry.get('wind_gust')
            
            if wind_dir is not None:
                report['weather']['wind_direction'] = int(wind_dir)
            if wind_speed is not None:
                try:
                    # Convert to mph if needed
                    report['weather']['wind_speed'] = round(float(wind_speed), 1)
                except:
                    pass
            if wind_gust is not None:
                try:
                    report['weather']['wind_gust'] = round(float(wind_gust), 1)
                except:
                    pass
            
            # Pressure
            pressure = entry.get('pressure')
            if pressure:
                try:
                    report['weather']['pressure'] = round(float(pressure), 2)
                except:
                    pass
            
            # Rainfall
            rain_1h = entry.get('rain_1h')
            rain_24h = entry.get('rain_24h')
            
            if rain_1h:
                try:
                    report['weather']['rain_1h'] = round(float(rain_1h), 2)
                except:
                    pass
            if rain_24h:
                try:
                    report['weather']['rain_24h'] = round(float(rain_24h), 2)
                except:
                    pass
            
            # Humidity
            humidity = entry.get('humidity')
            if humidity:
                try:
                    report['weather']['humidity'] = int(humidity)
                except:
                    pass
            
            return report
            
        except Exception as e:
            logger.error(f"Error extracting APRS report info: {e}")
            return None
    
    def format_significant_reports(self, reports: List[Dict]) -> Optional[str]:
        """
        Format significant weather reports for announcement
        Only announces noteworthy conditions
        
        Args:
            reports: List of APRS reports
            
        Returns:
            Formatted announcement or None
        """
        if not reports:
            return None
        
        significant = []
        
        for report in reports:
            weather = report.get('weather', {})
            callsign = report.get('callsign', 'Unknown')
            
            # Check for significant conditions
            
            # High winds - DISABLED (too many false reports from home weather stations)
            # wind_gust = weather.get('wind_gust', 0)
            # if wind_gust >= 60:  # 60+ mph gusts (severe threshold - filters bad home station data)
            #     significant.append({
            #         'type': 'wind',
            #         'callsign': callsign,
            #         'value': wind_gust,
            #         'timestamp': report['timestamp']
            #     })
            
            # Heavy rainfall
            rain_1h = weather.get('rain_1h', 0)
            if rain_1h >= 0.5:  # 0.5+ inches in 1 hour
                significant.append({
                    'type': 'rain',
                    'callsign': callsign,
                    'value': rain_1h,
                    'timestamp': report['timestamp']
                })
            
            # Extreme temperatures
            temp = weather.get('temperature')
            if temp:
                if temp >= 100 or temp <= 20:  # Extreme heat or cold
                    significant.append({
                        'type': 'temperature',
                        'callsign': callsign,
                        'value': temp,
                        'timestamp': report['timestamp']
                    })
        
        if not significant:
            return None
        
        # Format announcement
        parts = []
        
        # Sort by most recent
        significant.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take top 3 most significant
        for item in significant[:3]:
            report_type = item['type']
            callsign = item['callsign']
            value = item['value']
            
            if report_type == 'wind':
                parts.append(f"Ham radio station {callsign} reports wind gusts of {int(value)} miles per hour")
            elif report_type == 'rain':
                parts.append(f"Ham radio station {callsign} reports {value:.2f} inches of rain in the past hour")
            elif report_type == 'temperature':
                parts.append(f"Ham radio station {callsign} reports temperature of {int(value)} degrees")
        
        if parts:
            intro = "Weather reports from the APRS ham radio network: "
            return intro + ". ".join(parts) + "."
        
        return None
    
    def get_spotter_reports(self, reports: List[Dict]) -> List[Dict]:
        """
        Extract storm spotter reports from APRS data
        Looks for SKYWARN callsigns and storm-related comments
        
        Args:
            reports: List of APRS reports
            
        Returns:
            List of spotter reports
        """
        spotter_reports = []
        
        # Keywords indicating storm reports
        storm_keywords = [
            'tornado', 'funnel', 'rotation', 'hail', 'flooding',
            'damage', 'debris', 'severe', 'storm', 'lightning'
        ]
        
        for report in reports:
            callsign = report.get('callsign', '').upper()
            comment = report.get('comment', '').lower()
            
            # Check if SKYWARN spotter
            is_skywarn = 'SKYWARN' in callsign or 'WX' in callsign
            
            # Check for storm-related comments
            has_storm_report = any(keyword in comment for keyword in storm_keywords)
            
            if is_skywarn or has_storm_report:
                spotter_reports.append({
                    'callsign': report['callsign'],
                    'comment': report['comment'],
                    'timestamp': report['timestamp'],
                    'lat': report['lat'],
                    'lon': report['lon'],
                    'is_skywarn': is_skywarn
                })
        
        return spotter_reports


# Singleton instance
_aprs_integration = None

def get_aprs_integration(api_key: str = "") -> APRSIntegration:
    """Get singleton APRSIntegration instance"""
    global _aprs_integration
    if _aprs_integration is None:
        _aprs_integration = APRSIntegration(api_key)
    return _aprs_integration


def get_aprs_announcement(hours_back: int = 6) -> Optional[str]:
    """
    Convenience function to get APRS weather announcement
    
    Args:
        hours_back: Hours to look back for reports
        
    Returns:
        Formatted announcement or None
    """
    aprs = get_aprs_integration()
    reports = aprs.get_weather_reports(hours_back)
    return aprs.format_significant_reports(reports)
