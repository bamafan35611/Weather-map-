"""
impact_predictor.py - NorthBamaWX Alert Impact Predictions
Calculates population affected and infrastructure at risk for weather alerts
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

class ImpactPredictor:
    """Predicts impact of weather alerts on population and infrastructure"""
    
    # Population data for your 14 monitored counties (2020 Census estimates)
    COUNTY_POPULATIONS = {
        # North Alabama
        'AL': {
            'Colbert': 57227,
            'Cullman': 87866,
            'DeKalb': 71608,
            'Franklin': 32113,
            'Lauderdale': 93896,
            'Lawrence': 33073,
            'Limestone': 98915,
            'Madison': 388153,  # Largest - includes Huntsville
            'Marshall': 96774,
            'Morgan': 119679,
            'Blount': 59134
        },
        # Southern Tennessee
        'TN': {
            'Giles': 30346,
            'Lincoln': 35319,
            'Franklin': 42166
        }
    }
    
    # Major cities in your coverage area with populations
    CITIES = {
        'AL': {
            # Madison County
            'Huntsville': {'pop': 215006, 'lat': 34.7304, 'lon': -86.5861, 'county': 'Madison'},
            'Madison': {'pop': 56933, 'lat': 34.6993, 'lon': -86.7483, 'county': 'Madison'},
            'Harvest': {'pop': 6004, 'lat': 34.8565, 'lon': -86.7478, 'county': 'Madison'},
            'Triana': {'pop': 1200, 'lat': 34.5926, 'lon': -86.7461, 'county': 'Madison'},
            
            # Limestone County
            'Athens': {'pop': 25845, 'lat': 34.8023, 'lon': -86.9717, 'county': 'Limestone'},
            'Ardmore': {'pop': 1200, 'lat': 34.9898, 'lon': -86.8472, 'county': 'Limestone'},
            'Elkmont': {'pop': 434, 'lat': 34.9262, 'lon': -86.9828, 'county': 'Limestone'},
            
            # Morgan County
            'Decatur': {'pop': 57938, 'lat': 34.6059, 'lon': -86.9833, 'county': 'Morgan'},
            'Hartselle': {'pop': 15436, 'lat': 34.4431, 'lon': -86.9350, 'county': 'Morgan'},
            
            # Lauderdale County
            'Florence': {'pop': 40184, 'lat': 34.7998, 'lon': -87.6773, 'county': 'Lauderdale'},
            'Muscle Shoals': {'pop': 16043, 'lat': 34.7448, 'lon': -87.6675, 'county': 'Lauderdale'},
            
            # Colbert County
            'Tuscumbia': {'pop': 8445, 'lat': 34.7307, 'lon': -87.7025, 'county': 'Colbert'},
            'Sheffield': {'pop': 9403, 'lat': 34.7651, 'lon': -87.6989, 'county': 'Colbert'},
            
            # Marshall County
            'Albertville': {'pop': 22386, 'lat': 34.2676, 'lon': -86.2089, 'county': 'Marshall'},
            'Boaz': {'pop': 10020, 'lat': 34.2007, 'lon': -86.1661, 'county': 'Marshall'},
            'Guntersville': {'pop': 8531, 'lat': 34.3582, 'lon': -86.2947, 'county': 'Marshall'},
            
            # DeKalb County
            'Fort Payne': {'pop': 14877, 'lat': 34.4443, 'lon': -85.6797, 'county': 'DeKalb'},
            'Rainsville': {'pop': 5092, 'lat': 34.4937, 'lon': -85.8486, 'county': 'DeKalb'},
            
            # Cullman County
            'Cullman': {'pop': 18213, 'lat': 34.1748, 'lon': -86.8436, 'county': 'Cullman'},
        },
        'TN': {
            # Giles County
            'Pulaski': {'pop': 8397, 'lat': 35.1998, 'lon': -87.0306, 'county': 'Giles'},
            
            # Lincoln County
            'Fayetteville': {'pop': 7046, 'lat': 35.1520, 'lon': -86.5705, 'county': 'Lincoln'},
            
            # Franklin County
            'Winchester': {'pop': 9059, 'lat': 35.1859, 'lon': -86.1122, 'county': 'Franklin'},
        }
    }
    
    # Critical infrastructure types
    INFRASTRUCTURE_TYPES = {
        'schools': ['school', 'elementary', 'high school', 'university', 'college'],
        'hospitals': ['hospital', 'medical center', 'clinic', 'emergency'],
        'airports': ['airport', 'airfield'],
        'shopping': ['mall', 'shopping center'],
        'industrial': ['plant', 'factory', 'industrial']
    }
    
    def __init__(self):
        pass
    
    def predict_impact(self, alert: Dict) -> Optional[Dict]:
        """
        Predict the impact of a weather alert
        
        Args:
            alert: Alert dictionary with geometry/polygon data
            
        Returns:
            Impact prediction dictionary or None
        """
        try:
            # Extract alert info
            event = alert.get('event', '')
            area_desc = alert.get('areaDesc', '')
            
            # Get affected counties from area description
            affected_counties = self._parse_affected_counties(area_desc)
            
            # Get warning polygon if available
            polygon = self._extract_polygon(alert)
            
            # Calculate impacts
            impact = {
                'event': event,
                'affected_counties': affected_counties,
                'estimated_population': 0,
                'affected_cities': [],
                'major_cities': [],
                'infrastructure_at_risk': [],
                'severity_modifier': self._get_severity_modifier(event)
            }
            
            # Calculate population impact
            if polygon:
                # Use polygon for accurate calculation
                impact.update(self._calculate_polygon_impact(polygon))
            else:
                # Fallback to county-based estimate
                impact.update(self._calculate_county_impact(affected_counties))
            
            return impact
            
        except Exception as e:
            logger.error(f"Error predicting impact: {e}")
            return None
    
    def _parse_affected_counties(self, area_desc: str) -> List[Dict]:
        """Parse county names from area description"""
        affected = []
        
        # Split by semicolons and commas
        parts = area_desc.replace(';', ',').split(',')
        
        for part in parts:
            part = part.strip()
            
            # Check each state
            for state, counties in self.COUNTY_POPULATIONS.items():
                for county in counties.keys():
                    if county.lower() in part.lower():
                        affected.append({
                            'name': county,
                            'state': state,
                            'population': counties[county]
                        })
        
        return affected
    
    def _extract_polygon(self, alert: Dict) -> Optional[Polygon]:
        """Extract warning polygon from alert geometry"""
        try:
            geometry = alert.get('geometry')
            if not geometry:
                return None
            
            # Handle GeoJSON format
            if geometry.get('type') == 'Polygon':
                coords = geometry.get('coordinates', [[]])[0]
                # Coords are [lon, lat], need to swap for Shapely
                points = [(lon, lat) for lon, lat in coords]
                return Polygon(points)
            
            elif geometry.get('type') == 'MultiPolygon':
                polygons = []
                for poly_coords in geometry.get('coordinates', []):
                    points = [(lon, lat) for lon, lat in poly_coords[0]]
                    polygons.append(Polygon(points))
                return unary_union(polygons)
            
        except Exception as e:
            logger.error(f"Error extracting polygon: {e}")
        
        return None
    
    def _calculate_polygon_impact(self, polygon: Polygon) -> Dict:
        """Calculate impact using warning polygon geometry"""
        impact = {
            'estimated_population': 0,
            'affected_cities': [],
            'major_cities': []
        }
        
        # Check which cities are inside the polygon
        for state, cities in self.CITIES.items():
            for city_name, city_data in cities.items():
                city_point = Point(city_data['lon'], city_data['lat'])
                
                if polygon.contains(city_point):
                    city_info = {
                        'name': city_name,
                        'state': state,
                        'population': city_data['pop'],
                        'county': city_data['county']
                    }
                    
                    impact['affected_cities'].append(city_info)
                    impact['estimated_population'] += city_data['pop']
                    
                    # Major cities (>10,000 population)
                    if city_data['pop'] > 10000:
                        impact['major_cities'].append(city_name)
        
        # If no cities found in polygon, estimate based on area
        if impact['estimated_population'] == 0:
            # Rough estimate: assume 100 people per square mile in rural areas
            area_sq_miles = polygon.area * 3950  # Convert degrees² to miles² (approximate)
            impact['estimated_population'] = int(area_sq_miles * 100)
        
        return impact
    
    def _calculate_county_impact(self, affected_counties: List[Dict]) -> Dict:
        """Calculate impact based on affected counties (fallback method)"""
        impact = {
            'estimated_population': 0,
            'affected_cities': [],
            'major_cities': []
        }
        
        # Sum county populations
        for county in affected_counties:
            impact['estimated_population'] += county['population']
            
            # Find major cities in affected counties
            state = county['state']
            county_name = county['name']
            
            if state in self.CITIES:
                for city_name, city_data in self.CITIES[state].items():
                    if city_data['county'] == county_name:
                        if city_data['pop'] > 10000:
                            impact['major_cities'].append(city_name)
                        
                        impact['affected_cities'].append({
                            'name': city_name,
                            'state': state,
                            'population': city_data['pop'],
                            'county': county_name
                        })
        
        # For county-wide alerts, use ~70% of county population
        # (accounts for rural areas, not everyone directly impacted)
        impact['estimated_population'] = int(impact['estimated_population'] * 0.7)
        
        return impact
    
    def _get_severity_modifier(self, event: str) -> str:
        """Get severity level for different alert types"""
        event_lower = event.lower()
        
        if 'tornado' in event_lower and 'warning' in event_lower:
            return 'critical'
        elif 'severe thunderstorm' in event_lower and 'warning' in event_lower:
            return 'high'
        elif 'flash flood' in event_lower and 'warning' in event_lower:
            return 'high'
        elif 'warning' in event_lower:
            return 'moderate'
        elif 'watch' in event_lower:
            return 'low'
        else:
            return 'informational'
    
    def format_impact_announcement(self, impact: Dict) -> str:
        """
        Format impact prediction into natural language announcement
        
        Args:
            impact: Impact prediction dictionary
            
        Returns:
            Natural language impact description
        """
        if not impact:
            return ""
        
        parts = []
        
        # Population impact
        population = impact.get('estimated_population', 0)
        if population > 0:
            if population >= 1000000:
                pop_str = f"approximately {population // 1000000} million residents"
            elif population >= 100000:
                pop_str = f"approximately {population // 1000:,.0f} thousand residents"
            elif population >= 10000:
                # Round to nearest 5,000
                rounded = round(population / 5000) * 5000
                pop_str = f"approximately {rounded:,} residents"
            else:
                # Round to nearest 1,000
                rounded = round(population / 1000) * 1000
                pop_str = f"approximately {rounded:,} residents"
            
            parts.append(f"affecting {pop_str}")
        
        # Major cities
        major_cities = impact.get('major_cities', [])
        if major_cities:
            if len(major_cities) == 1:
                parts.append(f"including the city of {major_cities[0]}")
            elif len(major_cities) == 2:
                parts.append(f"including {major_cities[0]} and {major_cities[1]}")
            elif len(major_cities) >= 3:
                cities_list = ', '.join(major_cities[:3])
                if len(major_cities) > 3:
                    parts.append(f"including {cities_list}, and other areas")
                else:
                    # Last city with "and"
                    last_city = major_cities[2]
                    first_cities = ', '.join(major_cities[:2])
                    parts.append(f"including {first_cities}, and {last_city}")
        
        # Infrastructure
        infrastructure = impact.get('infrastructure_at_risk', [])
        if infrastructure:
            if 'schools' in infrastructure and 'hospitals' in infrastructure:
                parts.append("Multiple schools and medical facilities are in the affected area")
            elif 'schools' in infrastructure:
                parts.append("Several schools are in the affected area")
            elif 'hospitals' in infrastructure:
                parts.append("Medical facilities are in the affected area")
        
        # Combine all parts
        if parts:
            return ", ".join(parts) + "."
        else:
            return ""


# Singleton instance
_impact_predictor = None

def get_impact_predictor() -> ImpactPredictor:
    """Get singleton ImpactPredictor instance"""
    global _impact_predictor
    if _impact_predictor is None:
        _impact_predictor = ImpactPredictor()
    return _impact_predictor


def get_alert_impact(alert: Dict) -> Optional[str]:
    """
    Convenience function to get impact announcement for an alert
    
    Args:
        alert: Alert dictionary
        
    Returns:
        Formatted impact announcement or None
    """
    predictor = get_impact_predictor()
    impact = predictor.predict_impact(alert)
    
    if impact:
        return predictor.format_impact_announcement(impact)
    
    return None
