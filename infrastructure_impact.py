"""
infrastructure_impact.py - NorthBamaWX Infrastructure Impact Analysis
Identifies schools, hospitals, and critical infrastructure in alert areas
"""

import logging
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, Polygon

logger = logging.getLogger(__name__)

class InfrastructureImpact:
    """Identifies critical infrastructure at risk during weather alerts"""
    
    # Schools in your 14-county coverage area
    SCHOOLS = {
        'AL': {
            'Madison': [
                {'name': 'Huntsville High School', 'lat': 34.7304, 'lon': -86.5861, 'type': 'high_school', 'students': 2000},
                {'name': 'Bob Jones High School', 'lat': 34.7504, 'lon': -86.5561, 'type': 'high_school', 'students': 2200},
                {'name': 'Grissom High School', 'lat': 34.7104, 'lon': -86.6261, 'type': 'high_school', 'students': 1800},
                {'name': 'Madison Academy', 'lat': 34.6993, 'lon': -86.7483, 'type': 'private', 'students': 800},
                {'name': 'UAH (University)', 'lat': 34.7243, 'lon': -86.6408, 'type': 'university', 'students': 10000},
            ],
            'Limestone': [
                {'name': 'Athens High School', 'lat': 34.8023, 'lon': -86.9717, 'type': 'high_school', 'students': 1200},
                {'name': 'Athens Middle School', 'lat': 34.7923, 'lon': -86.9617, 'type': 'middle_school', 'students': 800},
                {'name': 'Elkmont High School', 'lat': 34.9262, 'lon': -86.9828, 'type': 'high_school', 'students': 600},
                {'name': 'Athens State University', 'lat': 34.8048, 'lon': -86.9739, 'type': 'university', 'students': 3000},
            ],
            'Morgan': [
                {'name': 'Decatur High School', 'lat': 34.6059, 'lon': -86.9833, 'type': 'high_school', 'students': 1500},
                {'name': 'Hartselle High School', 'lat': 34.4431, 'lon': -86.9350, 'type': 'high_school', 'students': 900},
            ],
            'Lauderdale': [
                {'name': 'Florence High School', 'lat': 34.7998, 'lon': -87.6773, 'type': 'high_school', 'students': 1100},
                {'name': 'UNA (University)', 'lat': 34.8312, 'lon': -87.6675, 'type': 'university', 'students': 7500},
            ],
            'Cullman': [
                {'name': 'Cullman High School', 'lat': 34.1748, 'lon': -86.8436, 'type': 'high_school', 'students': 1300},
            ],
            'Marshall': [
                {'name': 'Albertville High School', 'lat': 34.2676, 'lon': -86.2089, 'type': 'high_school', 'students': 1000},
            ],
        },
        'TN': {
            'Giles': [
                {'name': 'Giles County High School', 'lat': 35.1998, 'lon': -87.0306, 'type': 'high_school', 'students': 800},
            ],
        }
    }
    
    # Hospitals and medical facilities
    HOSPITALS = {
        'AL': {
            'Madison': [
                {'name': 'Huntsville Hospital', 'lat': 34.7304, 'lon': -86.5861, 'beds': 971, 'level': 'Level 1 Trauma'},
                {'name': 'Crestwood Medical Center', 'lat': 34.7204, 'lon': -86.5961, 'beds': 180, 'level': 'General'},
                {'name': 'Madison Hospital', 'lat': 34.6993, 'lon': -86.7483, 'beds': 80, 'level': 'Community'},
            ],
            'Limestone': [
                {'name': 'Athens-Limestone Hospital', 'lat': 34.8023, 'lon': -86.9717, 'beds': 120, 'level': 'Community'},
            ],
            'Morgan': [
                {'name': 'Decatur Morgan Hospital', 'lat': 34.6059, 'lon': -86.9833, 'beds': 200, 'level': 'General'},
            ],
            'Lauderdale': [
                {'name': 'North Alabama Medical Center', 'lat': 34.7998, 'lon': -87.6773, 'beds': 196, 'level': 'General'},
            ],
        }
    }
    
    # Major businesses and shopping centers
    BUSINESS_CENTERS = {
        'AL': {
            'Madison': [
                {'name': 'Bridge Street Town Centre', 'lat': 34.7404, 'lon': -86.6161, 'type': 'shopping'},
                {'name': 'Redstone Arsenal', 'lat': 34.6793, 'lon': -86.6511, 'type': 'military'},
                {'name': 'Cummings Research Park', 'lat': 34.7104, 'lon': -86.6261, 'type': 'business'},
            ],
        }
    }
    
    def __init__(self):
        pass
    
    def analyze_impact(self, alert: Dict) -> Dict:
        """
        Analyze infrastructure impact for an alert
        
        Args:
            alert: Alert dictionary with geometry
            
        Returns:
            Impact analysis dictionary
        """
        try:
            impact = {
                'schools_affected': [],
                'hospitals_affected': [],
                'businesses_affected': [],
                'total_students': 0,
                'total_beds': 0,
                'has_university': False,
                'has_major_hospital': False
            }
            
            # Get alert polygon
            polygon = self._extract_polygon(alert)
            
            # Get affected counties from area description
            area_desc = alert.get('areaDesc', '')
            affected_counties = self._parse_counties(area_desc)
            
            if polygon:
                # Use polygon for accurate analysis
                impact.update(self._analyze_polygon_impact(polygon))
            elif affected_counties:
                # Fallback to county-based analysis
                impact.update(self._analyze_county_impact(affected_counties))
            
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing infrastructure impact: {e}")
            return {
                'schools_affected': [],
                'hospitals_affected': [],
                'businesses_affected': [],
                'total_students': 0,
                'total_beds': 0,
                'has_university': False,
                'has_major_hospital': False
            }
    
    def _extract_polygon(self, alert: Dict) -> Optional[Polygon]:
        """Extract warning polygon from alert"""
        try:
            geometry = alert.get('geometry')
            if not geometry:
                return None
            
            if geometry.get('type') == 'Polygon':
                coords = geometry.get('coordinates', [[]])[0]
                points = [(lon, lat) for lon, lat in coords]
                return Polygon(points)
            
        except Exception as e:
            logger.error(f"Error extracting polygon: {e}")
        
        return None
    
    def _parse_counties(self, area_desc: str) -> List[Dict]:
        """Parse county names from area description"""
        affected = []
        parts = area_desc.replace(';', ',').split(',')
        
        for part in parts:
            part = part.strip()
            
            # Check Alabama counties
            if 'AL' in part or 'Alabama' in part:
                for county in self.SCHOOLS.get('AL', {}).keys():
                    if county in part:
                        affected.append({'county': county, 'state': 'AL'})
            
            # Check Tennessee counties
            if 'TN' in part or 'Tennessee' in part:
                for county in self.SCHOOLS.get('TN', {}).keys():
                    if county in part:
                        affected.append({'county': county, 'state': 'TN'})
        
        return affected
    
    def _analyze_polygon_impact(self, polygon: Polygon) -> Dict:
        """Analyze infrastructure within warning polygon"""
        impact = {
            'schools_affected': [],
            'hospitals_affected': [],
            'businesses_affected': [],
            'total_students': 0,
            'total_beds': 0,
            'has_university': False,
            'has_major_hospital': False
        }
        
        # Check schools
        for state, counties in self.SCHOOLS.items():
            for county, schools in counties.items():
                for school in schools:
                    point = Point(school['lon'], school['lat'])
                    if polygon.contains(point):
                        impact['schools_affected'].append(school)
                        impact['total_students'] += school.get('students', 0)
                        if school['type'] == 'university':
                            impact['has_university'] = True
        
        # Check hospitals
        for state, counties in self.HOSPITALS.items():
            for county, hospitals in counties.items():
                for hospital in hospitals:
                    point = Point(hospital['lon'], hospital['lat'])
                    if polygon.contains(point):
                        impact['hospitals_affected'].append(hospital)
                        impact['total_beds'] += hospital.get('beds', 0)
                        if 'Level 1' in hospital.get('level', ''):
                            impact['has_major_hospital'] = True
        
        # Check businesses
        for state, counties in self.BUSINESS_CENTERS.items():
            for county, businesses in counties.items():
                for business in businesses:
                    point = Point(business['lon'], business['lat'])
                    if polygon.contains(point):
                        impact['businesses_affected'].append(business)
        
        return impact
    
    def _analyze_county_impact(self, affected_counties: List[Dict]) -> Dict:
        """Analyze infrastructure in affected counties"""
        impact = {
            'schools_affected': [],
            'hospitals_affected': [],
            'businesses_affected': [],
            'total_students': 0,
            'total_beds': 0,
            'has_university': False,
            'has_major_hospital': False
        }
        
        for county_info in affected_counties:
            state = county_info['state']
            county = county_info['county']
            
            # Add all schools in county
            if state in self.SCHOOLS and county in self.SCHOOLS[state]:
                schools = self.SCHOOLS[state][county]
                impact['schools_affected'].extend(schools)
                impact['total_students'] += sum(s.get('students', 0) for s in schools)
                if any(s['type'] == 'university' for s in schools):
                    impact['has_university'] = True
            
            # Add all hospitals in county
            if state in self.HOSPITALS and county in self.HOSPITALS[state]:
                hospitals = self.HOSPITALS[state][county]
                impact['hospitals_affected'].extend(hospitals)
                impact['total_beds'] += sum(h.get('beds', 0) for h in hospitals)
                if any('Level 1' in h.get('level', '') for h in hospitals):
                    impact['has_major_hospital'] = True
            
            # Add all businesses in county
            if state in self.BUSINESS_CENTERS and county in self.BUSINESS_CENTERS[state]:
                businesses = self.BUSINESS_CENTERS[state][county]
                impact['businesses_affected'].extend(businesses)
        
        return impact
    
    def format_infrastructure_announcement(self, impact: Dict, alert_type: str = "Weather Alert") -> Optional[str]:
        """
        Format infrastructure impact into natural language
        
        Args:
            impact: Impact analysis dictionary
            alert_type: Type of alert (for context)
            
        Returns:
            Formatted announcement or None
        """
        if not impact:
            return None
        
        schools = impact.get('schools_affected', [])
        hospitals = impact.get('hospitals_affected', [])
        businesses = impact.get('businesses_affected', [])
        
        # Only announce if significant infrastructure affected
        if not schools and not hospitals and not businesses:
            return None
        
        parts = []
        
        # Schools (highest priority)
        if schools:
            school_count = len(schools)
            student_count = impact.get('total_students', 0)
            has_uni = impact.get('has_university', False)
            
            if has_uni:
                # Mention university specifically
                uni_names = [s['name'] for s in schools if s['type'] == 'university']
                if uni_names:
                    parts.append(f"{uni_names[0]} is in the warning area")
            elif school_count == 1:
                parts.append(f"{schools[0]['name']} is in the warning area")
            elif school_count <= 3:
                parts.append(f"{school_count} schools are in the warning area")
            else:
                parts.append(f"Multiple schools including {schools[0]['name']} are in the warning area")
        
        # Hospitals
        if hospitals:
            hospital_count = len(hospitals)
            has_major = impact.get('has_major_hospital', False)
            
            if has_major:
                major_hospitals = [h['name'] for h in hospitals if 'Level 1' in h.get('level', '')]
                if major_hospitals:
                    parts.append(f"{major_hospitals[0]} is in the affected area")
            elif hospital_count == 1:
                parts.append(f"{hospitals[0]['name']} is in the affected area")
            elif hospital_count > 1:
                parts.append(f"{hospital_count} medical facilities are in the affected area")
        
        # Major businesses/landmarks
        if businesses:
            # Only mention most significant
            military = [b for b in businesses if b['type'] == 'military']
            if military:
                parts.append(f"{military[0]['name']} is in the warning area")
        
        if parts:
            return ". ".join(parts) + "."
        
        return None


# Singleton instance
_infrastructure_impact = None

def get_infrastructure_impact() -> InfrastructureImpact:
    """Get singleton InfrastructureImpact instance"""
    global _infrastructure_impact
    if _infrastructure_impact is None:
        _infrastructure_impact = InfrastructureImpact()
    return _infrastructure_impact


def get_infrastructure_announcement(alert: Dict) -> Optional[str]:
    """
    Convenience function to get infrastructure impact announcement
    
    Args:
        alert: Alert dictionary
        
    Returns:
        Formatted announcement or None
    """
    infrastructure = get_infrastructure_impact()
    impact = infrastructure.analyze_impact(alert)
    alert_type = alert.get('event', 'Weather Alert')
    return infrastructure.format_infrastructure_announcement(impact, alert_type)
