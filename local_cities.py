"""
local_cities.py - Database of cities/towns in NorthBamaWX monitored area
North Alabama (11 counties) + Southern Tennessee (3 counties)
"""

from typing import Dict, List
import random

# City database with coordinates for NWS API calls
MONITORED_CITIES = {
    # NORTH ALABAMA
    
    # Colbert County, AL
    'Tuscumbia': {'lat': 34.7309, 'lon': -87.7025, 'county': 'Colbert', 'state': 'AL'},
    'Sheffield': {'lat': 34.7651, 'lon': -87.6989, 'county': 'Colbert', 'state': 'AL'},
    'Muscle Shoals': {'lat': 34.7448, 'lon': -87.6675, 'county': 'Colbert', 'state': 'AL'},
    
    # Cullman County, AL
    'Cullman': {'lat': 34.1748, 'lon': -86.8436, 'county': 'Cullman', 'state': 'AL'},
    'Good Hope': {'lat': 34.1129, 'lon': -86.8661, 'county': 'Cullman', 'state': 'AL'},
    'Hanceville': {'lat': 34.0593, 'lon': -86.7678, 'county': 'Cullman', 'state': 'AL'},
    
    # DeKalb County, AL
    'Fort Payne': {'lat': 34.4443, 'lon': -85.6797, 'county': 'DeKalb', 'state': 'AL'},
    'Rainsville': {'lat': 34.4943, 'lon': -85.8486, 'county': 'DeKalb', 'state': 'AL'},
    'Henagar': {'lat': 34.6323, 'lon': -85.7644, 'county': 'DeKalb', 'state': 'AL'},
    
    # Franklin County, AL
    'Russellville': {'lat': 34.5079, 'lon': -87.7286, 'county': 'Franklin', 'state': 'AL'},
    'Red Bay': {'lat': 34.4398, 'lon': -88.1414, 'county': 'Franklin', 'state': 'AL'},
    'Phil Campbell': {'lat': 34.3487, 'lon': -87.7067, 'county': 'Franklin', 'state': 'AL'},
    
    # Jackson County, AL
    'Scottsboro': {'lat': 34.6723, 'lon': -86.0342, 'county': 'Jackson', 'state': 'AL'},
    'Bridgeport': {'lat': 34.9476, 'lon': -85.7144, 'county': 'Jackson', 'state': 'AL'},
    'Stevenson': {'lat': 34.8687, 'lon': -85.8397, 'county': 'Jackson', 'state': 'AL'},
    'Pisgah': {'lat': 34.6851, 'lon': -85.8516, 'county': 'Jackson', 'state': 'AL'},
    
    # Lawrence County, AL
    'Moulton': {'lat': 34.4812, 'lon': -87.2928, 'county': 'Lawrence', 'state': 'AL'},
    'Courtland': {'lat': 34.6698, 'lon': -87.3142, 'county': 'Lawrence', 'state': 'AL'},
    'Town Creek': {'lat': 34.6812, 'lon': -87.4064, 'county': 'Lawrence', 'state': 'AL'},
    
    # Lauderdale County, AL
    'Florence': {'lat': 34.7998, 'lon': -87.6773, 'county': 'Lauderdale', 'state': 'AL'},
    'Rogersville': {'lat': 34.8257, 'lon': -87.2892, 'county': 'Lauderdale', 'state': 'AL'},
    'Killen': {'lat': 34.8618, 'lon': -87.5370, 'county': 'Lauderdale', 'state': 'AL'},
    'Lexington': {'lat': 34.9718, 'lon': -87.3736, 'county': 'Lauderdale', 'state': 'AL'},
    
    # Limestone County, AL
    'Athens': {'lat': 34.8026, 'lon': -86.9719, 'county': 'Limestone', 'state': 'AL'},
    'Ardmore': {'lat': 34.9907, 'lon': -86.8464, 'county': 'Limestone', 'state': 'AL'},
    'Elkmont': {'lat': 34.9257, 'lon': -86.9833, 'county': 'Limestone', 'state': 'AL'},
    'Tanner': {'lat': 34.6876, 'lon': -87.0019, 'county': 'Limestone', 'state': 'AL'},
    'Lester': {'lat': 34.9857, 'lon': -87.1308, 'county': 'Limestone', 'state': 'AL'},
    
    # Madison County, AL
    'Huntsville': {'lat': 34.7304, 'lon': -86.5861, 'county': 'Madison', 'state': 'AL'},
    'Madison': {'lat': 34.6993, 'lon': -86.7483, 'county': 'Madison', 'state': 'AL'},
    'New Market': {'lat': 34.9048, 'lon': -86.4244, 'county': 'Madison', 'state': 'AL'},
    'Harvest': {'lat': 34.8487, 'lon': -86.7514, 'county': 'Madison', 'state': 'AL'},
    'Hazel Green': {'lat': 34.9304, 'lon': -86.5719, 'county': 'Madison', 'state': 'AL'},
    'Gurley': {'lat': 34.7021, 'lon': -86.3730, 'county': 'Madison', 'state': 'AL'},
    
    # Marshall County, AL
    'Guntersville': {'lat': 34.3581, 'lon': -86.2947, 'county': 'Marshall', 'state': 'AL'},
    'Albertville': {'lat': 34.2676, 'lon': -86.2089, 'county': 'Marshall', 'state': 'AL'},
    'Boaz': {'lat': 34.2007, 'lon': -86.1661, 'county': 'Marshall', 'state': 'AL'},
    'Arab': {'lat': 34.3184, 'lon': -86.4958, 'county': 'Marshall', 'state': 'AL'},
    
    # Morgan County, AL
    'Decatur': {'lat': 34.6059, 'lon': -86.9833, 'county': 'Morgan', 'state': 'AL'},
    'Hartselle': {'lat': 34.4426, 'lon': -86.9356, 'county': 'Morgan', 'state': 'AL'},
    'Priceville': {'lat': 34.5301, 'lon': -86.8947, 'county': 'Morgan', 'state': 'AL'},
    'Falkville': {'lat': 34.3693, 'lon': -86.9089, 'county': 'Morgan', 'state': 'AL'},
    
    # SOUTHERN TENNESSEE
    
    # Franklin County, TN
    'Winchester': {'lat': 35.1859, 'lon': -86.1122, 'county': 'Franklin', 'state': 'TN'},
    'Cowan': {'lat': 35.1662, 'lon': -86.0122, 'county': 'Franklin', 'state': 'TN'},
    'Decherd': {'lat': 35.2092, 'lon': -86.0764, 'county': 'Franklin', 'state': 'TN'},
    
    # Lincoln County, TN
    'Fayetteville': {'lat': 35.1520, 'lon': -86.5705, 'county': 'Lincoln', 'state': 'TN'},
    'Ardmore': {'lat': 35.0009, 'lon': -86.8464, 'county': 'Lincoln', 'state': 'TN'},
    
    # Moore County, TN
    'Lynchburg': {'lat': 35.2831, 'lon': -86.3742, 'county': 'Moore', 'state': 'TN'},
}


def get_random_city() -> Dict:
    """Get a random city from the monitored area"""
    city_name = random.choice(list(MONITORED_CITIES.keys()))
    city_data = MONITORED_CITIES[city_name].copy()
    city_data['name'] = city_name
    return city_data


def get_cities_by_county(county: str) -> List[Dict]:
    """Get all cities in a specific county"""
    cities = []
    for name, data in MONITORED_CITIES.items():
        if data['county'] == county:
            city_data = data.copy()
            city_data['name'] = name
            cities.append(city_data)
    return cities


def get_cities_by_state(state: str) -> List[Dict]:
    """Get all cities in a specific state"""
    cities = []
    for name, data in MONITORED_CITIES.items():
        if data['state'] == state:
            city_data = data.copy()
            city_data['name'] = name
            cities.append(city_data)
    return cities


def get_city_info(city_name: str) -> Dict:
    """Get info for a specific city"""
    if city_name in MONITORED_CITIES:
        city_data = MONITORED_CITIES[city_name].copy()
        city_data['name'] = city_name
        return city_data
    return None


def format_city_location(city_data: Dict) -> str:
    """Format city location for broadcast"""
    return f"{city_data['name']}, {city_data['state']}"


if __name__ == '__main__':
    # Test the city database
    print("=" * 70)
    print("NORTHBAMAWX CITY DATABASE TEST")
    print("=" * 70)
    
    print(f"\nTotal cities/towns monitored: {len(MONITORED_CITIES)}")
    
    # Count by state
    al_cities = get_cities_by_state('AL')
    tn_cities = get_cities_by_state('TN')
    print(f"  Alabama: {len(al_cities)} cities")
    print(f"  Tennessee: {len(tn_cities)} cities")
    
    # Count by county
    print("\nCities by county:")
    counties = set(data['county'] for data in MONITORED_CITIES.values())
    for county in sorted(counties):
        county_cities = get_cities_by_county(county)
        print(f"  {county} County: {len(county_cities)} cities")
    
    # Random city examples
    print("\n5 Random City Selections:")
    for i in range(5):
        city = get_random_city()
        print(f"  {i+1}. {format_city_location(city)} ({city['county']} County)")
    
    print("\n" + "=" * 70)
