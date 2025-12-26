"""
storm_reports.py - NorthBamaWX Storm Reports System
Fetches and announces recent severe weather reports from NWS + SpotterNetwork
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

# Import SpotterNetwork integration
try:
    from spotternetwork import get_spotternetwork_reports
    SPOTTERNETWORK_AVAILABLE = True
    print("✓ SpotterNetwork integration enabled")
except ImportError as e:
    print(f"⚠️ SpotterNetwork not available: {e}")
    SPOTTERNETWORK_AVAILABLE = False
    get_spotternetwork_reports = None

logger = logging.getLogger(__name__)

class StormReports:
    """Fetches and formats storm reports from NWS"""
    
    def __init__(self):
        # Counties we monitor
        self.MONITORED_COUNTIES = [
            # North Alabama
            'Colbert', 'Cullman', 'DeKalb', 'Franklin', 'Jackson',
            'Lawrence', 'Lauderdale', 'Limestone', 'Madison', 'Marshall', 'Morgan',
            # Southern Tennessee  
            'Franklin', 'Lincoln', 'Moore'
        ]
        
        self.MONITORED_STATES = ['AL', 'TN']
        
    def get_recent_reports(self, hours_back: int = 24) -> Dict[str, List[Dict]]:
        """
        Get storm reports from the last N hours
        
        Args:
            hours_back: How many hours back to search
            
        Returns:
            Dictionary with 'tornado', 'hail', 'wind' report lists
        """
        reports = {
            'tornado': [],
            'hail': [],
            'wind': []
        }
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Format for NWS API (ISO 8601)
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # NWS Storm Reports endpoint
            # Note: This is a simplified approach - actual implementation may need
            # to use Storm Prediction Center (SPC) reports instead
            url = "https://api.weather.gov/alerts/active"
            
            print(f"🌪️ Fetching storm reports from {start_str} to {end_str}")
            
            headers = {
                'User-Agent': 'NorthBamaWX/2.0 (Storm Reports)',
                'Accept': 'application/geo+json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ Storm reports API returned {response.status_code}")
                return reports
            
            data = response.json()
            features = data.get('features', [])
            
            # Parse alerts that mention storm reports
            for feature in features:
                props = feature.get('properties', {})
                description = props.get('description', '').lower()
                event = props.get('event', '')
                area = props.get('areaDesc', '')
                
                # Check if this is in our monitored area
                in_monitored_area = any(
                    county in area for county in self.MONITORED_COUNTIES
                ) or any(
                    state in area for state in self.MONITORED_STATES
                )
                
                if not in_monitored_area:
                    continue
                
                # Extract reports from description
                # Look for keywords indicating actual reports
                if 'tornado' in description and 'reported' in description:
                    reports['tornado'].append({
                        'location': area,
                        'time': props.get('sent', ''),
                        'details': self._extract_report_details(description, 'tornado')
                    })
                
                if 'hail' in description and 'reported' in description:
                    reports['hail'].append({
                        'location': area,
                        'time': props.get('sent', ''),
                        'size': self._extract_hail_size(description),
                        'details': self._extract_report_details(description, 'hail')
                    })
                
                if ('wind' in description or 'damage' in description) and 'reported' in description:
                    reports['wind'].append({
                        'location': area,
                        'time': props.get('sent', ''),
                        'speed': self._extract_wind_speed(description),
                        'details': self._extract_report_details(description, 'wind')
                    })
            
            # Log what we found
            total_reports = len(reports['tornado']) + len(reports['hail']) + len(reports['wind'])
            if total_reports > 0:
                print(f"✅ Found {total_reports} storm reports:")
                print(f"   • Tornadoes: {len(reports['tornado'])}")
                print(f"   • Hail: {len(reports['hail'])}")
                print(f"   • Wind: {len(reports['wind'])}")
            else:
                print("✓ No storm reports in monitored area")
            
            return reports
            
        except Exception as e:
            print(f"❌ Error fetching storm reports: {e}")
            return reports
    
    def get_all_reports(self, hours_back: int = 24) -> Dict[str, List[Dict]]:
        """
        Get storm reports from BOTH NWS and SpotterNetwork, then merge them
        
        Args:
            hours_back: How many hours back to search
            
        Returns:
            Dictionary with 'tornado', 'hail', 'wind', 'flood' report lists
        """
        # Start with NWS reports
        print("📡 Fetching reports from multiple sources...")
        nws_reports = self.get_recent_reports(hours_back)
        
        # Add SpotterNetwork reports if available
        if SPOTTERNETWORK_AVAILABLE:
            try:
                print("🎯 Fetching SpotterNetwork reports...")
                spotter_reports = get_spotternetwork_reports(hours_back)
                
                # Merge SpotterNetwork reports into categorized dict
                for report in spotter_reports:
                    report_type = report.get('type', 'other')
                    
                    if report_type in ['tornado', 'hail', 'wind', 'flood']:
                        # Add 'flood' category if not present
                        if report_type not in nws_reports:
                            nws_reports[report_type] = []
                        
                        # Convert SpotterNetwork format to our format
                        formatted_report = {
                            'source': 'SpotterNetwork',
                            'location': report.get('location', 'Unknown'),
                            'county': report.get('county', 'Unknown'),
                            'state': report.get('state', 'Unknown'),
                            'time': report.get('timestamp').isoformat() if report.get('timestamp') else '',
                            'verified': report.get('verified', False),
                            'spotter': report.get('spotter_name', 'Weather Spotter'),
                            'details': report.get('description', ''),
                            'raw_data': report  # Keep original for detailed formatting
                        }
                        
                        # Add type-specific data
                        if report_type == 'hail':
                            formatted_report['size'] = report.get('magnitude')
                        elif report_type == 'wind':
                            formatted_report['speed'] = report.get('magnitude')
                        
                        nws_reports[report_type].append(formatted_report)
                
                # Log merged results
                spotter_count = len(spotter_reports)
                total = sum(len(v) for v in nws_reports.values())
                print(f"✅ Merged reports: {total} total ({spotter_count} from SpotterNetwork)")
                
            except Exception as e:
                print(f"⚠️ SpotterNetwork fetch failed: {e}")
        
        return nws_reports
    
    def _extract_report_details(self, description: str, report_type: str) -> str:
        """Extract relevant details from alert description"""
        # Look for sentences containing the report type
        sentences = description.split('.')
        for sentence in sentences:
            if report_type in sentence.lower() and 'reported' in sentence.lower():
                return sentence.strip()
        return ""
    
    def _extract_hail_size(self, description: str) -> Optional[str]:
        """Extract hail size from description"""
        import re
        
        # Look for patterns like "2 inch hail" or "quarter size hail"
        size_match = re.search(r'(\d+\.?\d*)\s*inch', description.lower())
        if size_match:
            return f"{size_match.group(1)} inch"
        
        # Look for object comparisons
        objects = ['quarter', 'golf ball', 'baseball', 'softball', 'grapefruit']
        for obj in objects:
            if obj in description.lower():
                return obj
        
        return None
    
    def _extract_wind_speed(self, description: str) -> Optional[str]:
        """Extract wind speed from description"""
        import re
        
        # Look for patterns like "60 mph winds" or "winds of 70 mph"
        speed_match = re.search(r'(\d+)\s*mph', description.lower())
        if speed_match:
            return f"{speed_match.group(1)} mph"
        
        return None
    
    def format_report_summary(self, reports: Dict[str, List[Dict]], max_age_hours: int = 6) -> Optional[str]:
        """
        Format storm reports into a broadcast-ready announcement
        
        Args:
            reports: Dictionary from get_recent_reports()
            max_age_hours: Only include reports from last N hours in summary
            
        Returns:
            Formatted announcement string or None if no reports
        """
        total_reports = len(reports['tornado']) + len(reports['hail']) + len(reports['wind'])
        
        if total_reports == 0:
            return None
        
        # Filter to recent reports only
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        recent_tornado = self._filter_by_time(reports['tornado'], cutoff_time)
        recent_hail = self._filter_by_time(reports['hail'], cutoff_time)
        recent_wind = self._filter_by_time(reports['wind'], cutoff_time)
        
        total_recent = len(recent_tornado) + len(recent_hail) + len(recent_wind)
        
        if total_recent == 0:
            return None
        
        # Build announcement
        parts = []
        
        # Header
        if max_age_hours <= 1:
            parts.append("Recent storm reports in our area:")
        elif max_age_hours <= 6:
            parts.append(f"Storm reports in the last {max_age_hours} hours:")
        else:
            parts.append("Recent storm reports:")
        
        # Tornado reports (highest priority)
        if recent_tornado:
            for report in recent_tornado[:3]:  # Max 3 reports
                location = report.get('location', 'Unknown location')
                time_str = self._format_time_ago(report.get('time', ''))
                parts.append(f"Tornado reported near {location} {time_str}.")
        
        # Hail reports
        if recent_hail:
            for report in recent_hail[:3]:  # Max 3 reports
                location = report.get('location', 'Unknown location')
                size = report.get('size', 'large')
                time_str = self._format_time_ago(report.get('time', ''))
                parts.append(f"{size} hail reported near {location} {time_str}.")
        
        # Wind reports
        # Wind reports - DISABLED (too many false reports)
        # if recent_wind:
        #     for report in recent_wind[:3]:  # Max 3 reports
        #         location = report.get('location', 'Unknown location')
        #         speed = report.get('speed', 'damaging')
        #         time_str = self._format_time_ago(report.get('time', ''))
        #         parts.append(f"{speed} winds reported near {location} {time_str}.")
        
        return " ".join(parts)
    
    def _filter_by_time(self, report_list: List[Dict], cutoff_time: datetime) -> List[Dict]:
        """Filter reports to only those after cutoff_time"""
        filtered = []
        for report in report_list:
            try:
                report_time = datetime.fromisoformat(report['time'].replace('Z', '+00:00'))
                if report_time > cutoff_time:
                    filtered.append(report)
            except:
                # If we can't parse time, include it anyway
                filtered.append(report)
        return filtered
    
    def _format_time_ago(self, time_str: str) -> str:
        """Convert ISO timestamp to 'X minutes ago' format"""
        try:
            report_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            now = datetime.now(report_time.tzinfo)
            delta = now - report_time
            
            if delta.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(delta.total_seconds() / 60)
                return f"{minutes} minutes ago"
            elif delta.total_seconds() < 7200:  # Less than 2 hours
                return "about an hour ago"
            else:
                hours = int(delta.total_seconds() / 3600)
                return f"{hours} hours ago"
        except:
            return "recently"


# Singleton instance
_storm_reports_instance = None

def get_storm_reports() -> StormReports:
    """Get the singleton StormReports instance"""
    global _storm_reports_instance
    if _storm_reports_instance is None:
        _storm_reports_instance = StormReports()
    return _storm_reports_instance


def get_storm_reports_summary(hours_back: int = 6, max_age_hours: int = 6) -> Optional[str]:
    """
    Convenience function to get a broadcast-ready storm reports summary
    NOW INCLUDES SPOTTERNETWORK REPORTS!
    
    Args:
        hours_back: How many hours back to search for reports
        max_age_hours: Only include reports from last N hours in summary
        
    Returns:
        Formatted announcement or None if no reports
    """
    reporter = get_storm_reports()
    # Use get_all_reports to merge NWS + SpotterNetwork
    reports = reporter.get_all_reports(hours_back=hours_back)
    return reporter.format_report_summary(reports, max_age_hours=max_age_hours)


# For testing
if __name__ == "__main__":
    print("Testing Storm Reports System...")
    print("-" * 50)
    
    reporter = StormReports()
    reports = reporter.get_recent_reports(hours_back=24)
    
    summary = reporter.format_report_summary(reports, max_age_hours=6)
    
    if summary:
        print("\n📢 BROADCAST ANNOUNCEMENT:")
        print(summary)
    else:
        print("\n✓ No storm reports to announce")
