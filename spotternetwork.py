"""
spotternetwork.py - SpotterNetwork API Integration for NorthBamaWX
Fetches verified storm reports from trained weather spotters
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SpotterNetwork:
    """Fetches storm reports from SpotterNetwork API"""
    
    # Your 14 monitored counties
    MONITORED_COUNTIES = {
        'AL': ['Colbert', 'Franklin', 'Lauderdale', 'Lawrence', 'Limestone', 
               'Madison', 'Marshall', 'Morgan', 'Cullman', 'Blount', 'DeKalb'],
        'TN': ['Giles', 'Lincoln', 'Franklin']
    }
    
    # Bounding box for your coverage area (approximate)
    # North Alabama + Southern Tennessee
    COVERAGE_BOUNDS = {
        'min_lat': 34.0,   # Southern edge
        'max_lat': 35.5,   # Northern edge  
        'min_lon': -88.0,  # Western edge
        'max_lon': -85.5   # Eastern edge
    }
    
    def __init__(self):
        self.base_url = "https://www.spotternetwork.org/data.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NorthBamaWX/3.0 (SpotterNetwork Integration)'
        })
    
    def get_reports(self, hours_back: int = 24) -> List[Dict]:
        """
        Fetch storm reports from SpotterNetwork
        
        Args:
            hours_back: How many hours back to search
            
        Returns:
            List of storm report dictionaries
        """
        try:
            # SpotterNetwork API parameters
            # mode=3 gets storm reports
            params = {
                'mode': '3',  # Storm reports mode
                'lat': 34.8,  # Center of coverage (Athens, AL)
                'lon': -86.97,
                'radius': 100  # Miles radius
            }
            
            logger.info(f"Fetching SpotterNetwork reports for last {hours_back} hours")
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse and filter reports
            reports = self._parse_reports(data, hours_back)
            
            logger.info(f"Found {len(reports)} SpotterNetwork reports")
            
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching SpotterNetwork reports: {e}")
            return []
    
    def _parse_reports(self, data: Dict, hours_back: int) -> List[Dict]:
        """Parse SpotterNetwork data and filter for our area and timeframe"""
        reports = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        try:
            # SpotterNetwork returns reports in various formats
            # Check for 'reports' key or iterate features
            raw_reports = []
            
            if isinstance(data, dict):
                if 'reports' in data:
                    raw_reports = data['reports']
                elif 'features' in data:
                    raw_reports = data['features']
            elif isinstance(data, list):
                raw_reports = data
            
            for raw_report in raw_reports:
                report = self._extract_report_info(raw_report)
                
                if report:
                    # Check if within time window
                    report_time = report.get('timestamp')
                    if report_time and report_time >= cutoff_time:
                        # Check if in our coverage area
                        if self._is_in_coverage_area(report):
                            reports.append(report)
        
        except Exception as e:
            logger.error(f"Error parsing SpotterNetwork reports: {e}")
        
        return reports
    
    def _extract_report_info(self, raw_report: Dict) -> Optional[Dict]:
        """Extract relevant information from a SpotterNetwork report"""
        try:
            # SpotterNetwork format varies, try multiple structures
            props = raw_report.get('properties', raw_report)
            
            # Parse timestamp
            timestamp_str = props.get('time', props.get('timestamp', ''))
            try:
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.utcnow()
            except:
                timestamp = datetime.utcnow()
            
            # Extract report type
            report_type = props.get('type', props.get('event', 'unknown')).lower()
            
            # Map SpotterNetwork types to our types
            if 'tornado' in report_type or 'funnel' in report_type:
                report_category = 'tornado'
            elif 'hail' in report_type:
                report_category = 'hail'
            elif 'wind' in report_type or 'gust' in report_type:
                report_category = 'wind'
            elif 'flood' in report_type:
                report_category = 'flood'
            else:
                report_category = 'other'
            
            # Extract location
            lat = props.get('lat', props.get('latitude'))
            lon = props.get('lon', props.get('longitude'))
            
            if lat is None or lon is None:
                return None
            
            report = {
                'source': 'SpotterNetwork',
                'type': report_category,
                'raw_type': report_type,
                'timestamp': timestamp,
                'location': props.get('location', props.get('city', 'Unknown')),
                'county': props.get('county', 'Unknown'),
                'state': props.get('state', 'Unknown'),
                'lat': float(lat),
                'lon': float(lon),
                'magnitude': props.get('magnitude', props.get('size', props.get('speed'))),
                'description': props.get('description', props.get('remarks', '')),
                'spotter_name': props.get('spotter', props.get('observer', 'Unknown')),
                'verified': props.get('verified', False),
                'has_photo': props.get('photo', False) or props.get('hasPhoto', False)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error extracting report info: {e}")
            return None
    
    def _is_in_coverage_area(self, report: Dict) -> bool:
        """Check if report is within our coverage area"""
        lat = report.get('lat')
        lon = report.get('lon')
        
        if lat is None or lon is None:
            return False
        
        # Check bounding box
        if (self.COVERAGE_BOUNDS['min_lat'] <= lat <= self.COVERAGE_BOUNDS['max_lat'] and
            self.COVERAGE_BOUNDS['min_lon'] <= lon <= self.COVERAGE_BOUNDS['max_lon']):
            return True
        
        # Also check by county name if available
        county = report.get('county', '')
        state = report.get('state', '').upper()
        
        if state in self.MONITORED_COUNTIES:
            return any(c.lower() in county.lower() for c in self.MONITORED_COUNTIES[state])
        
        return False
    
    def format_report_for_voice(self, report: Dict) -> str:
        """
        Format a SpotterNetwork report for voice announcement
        
        Args:
            report: Report dictionary
            
        Returns:
            Natural language description
        """
        report_type = report['type']
        location = report.get('location', 'the area')
        county = report.get('county', 'the region')
        
        # Format time
        timestamp = report['timestamp']
        local_time = timestamp - timedelta(hours=6)  # UTC to CST
        time_str = local_time.strftime('%I:%M %p').lstrip('0')
        
        # Base announcement
        if report_type == 'tornado':
            announcement = self._format_tornado_report(report, location, county, time_str)
        elif report_type == 'hail':
            announcement = self._format_hail_report(report, location, county, time_str)
        elif report_type == 'wind':
            announcement = self._format_wind_report(report, location, county, time_str)
        elif report_type == 'flood':
            announcement = self._format_flood_report(report, location, county, time_str)
        else:
            announcement = f"Severe weather was reported near {location} at {time_str}"
        
        # Add spotter verification note for high-confidence reports
        if report.get('verified'):
            announcement += ", confirmed by trained spotter"
        
        return announcement + "."
    
    def _format_tornado_report(self, report: Dict, location: str, county: str, time_str: str) -> str:
        """Format tornado report"""
        description = report.get('description', '')
        
        announcement = f"A tornado was reported near {location}"
        
        if county and county != 'Unknown':
            announcement += f" in {county} County"
        
        announcement += f" at {time_str}"
        
        if 'damage' in description.lower():
            announcement += ", with damage reported"
        
        return announcement
    
    def _format_hail_report(self, report: Dict, location: str, county: str, time_str: str) -> str:
        """Format hail report with size description"""
        magnitude = report.get('magnitude')
        size_desc = self._translate_hail_size(magnitude)
        
        announcement = f"{size_desc} hail was reported near {location}"
        
        if county and county != 'Unknown':
            announcement += f" in {county} County"
        
        announcement += f" at {time_str}"
        
        return announcement
    
    def _format_wind_report(self, report: Dict, location: str, county: str, time_str: str) -> str:
        """Format wind report"""
        magnitude = report.get('magnitude')
        description = report.get('description', '')
        
        announcement = f"Damaging winds were reported near {location}"
        
        if county and county != 'Unknown':
            announcement += f" in {county} County"
        
        announcement += f" at {time_str}"
        
        if magnitude:
            try:
                speed = int(float(magnitude))
                announcement += f", with winds estimated at {speed} miles per hour"
            except:
                pass
        
        if 'tree' in description.lower() or 'damage' in description.lower():
            announcement += ". Tree and power line damage reported"
        
        return announcement
    
    def _format_flood_report(self, report: Dict, location: str, county: str, time_str: str) -> str:
        """Format flooding report"""
        announcement = f"Flash flooding was reported near {location}"
        
        if county and county != 'Unknown':
            announcement += f" in {county} County"
        
        announcement += f" at {time_str}"
        
        return announcement
    
    def _translate_hail_size(self, size_inches: Optional[float]) -> str:
        """Translate hail size to common object comparisons"""
        if not size_inches:
            return "Large"
        
        try:
            size = float(size_inches)
        except:
            return "Large"
        
        if size >= 4.0:
            return "Softball sized"
        elif size >= 2.75:
            return "Baseball sized"
        elif size >= 2.0:
            return "Tennis ball sized"
        elif size >= 1.75:
            return "Golf ball sized"
        elif size >= 1.5:
            return "Ping pong ball sized"
        elif size >= 1.0:
            return "Quarter sized"
        elif size >= 0.75:
            return "Penny sized"
        elif size >= 0.5:
            return "Dime sized"
        else:
            return "Pea sized"


# Singleton instance
spotter_network = SpotterNetwork()


def get_spotternetwork_reports(hours_back: int = 24) -> List[Dict]:
    """
    Convenience function to get SpotterNetwork reports
    
    Args:
        hours_back: Hours to search back
        
    Returns:
        List of report dictionaries
    """
    return spotter_network.get_reports(hours_back)
