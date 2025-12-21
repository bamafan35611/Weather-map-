"""
backup_grids.py - Backup NWS Grid Points for Forecast Reliability
Provides fallback grid points when primary location fails
"""

from typing import Dict, List, Optional, Tuple

class BackupGridSystem:
    """Manages backup grid points for forecast reliability"""
    
    def __init__(self):
        # Primary and backup grid points for North Alabama cities
        # Format: (latitude, longitude, city_name, state)
        self.grid_points = {
            'athens': [
                (34.8023, -86.9719, 'Athens', 'AL'),      # Primary
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Backup 1
                (34.6059, -86.9833, 'Decatur', 'AL'),     # Backup 2
                (34.8315, -87.6773, 'Florence', 'AL'),    # Backup 3
            ],
            'huntsville': [
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Primary
                (34.8023, -86.9719, 'Athens', 'AL'),      # Backup 1
                (34.6059, -86.9833, 'Decatur', 'AL'),     # Backup 2
                (34.9889, -86.0083, 'Scottsboro', 'AL'),  # Backup 3
            ],
            'decatur': [
                (34.6059, -86.9833, 'Decatur', 'AL'),     # Primary
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Backup 1
                (34.8023, -86.9719, 'Athens', 'AL'),      # Backup 2
                (34.4640, -87.0211, 'Cullman', 'AL'),     # Backup 3
            ],
            'florence': [
                (34.8315, -87.6773, 'Florence', 'AL'),    # Primary
                (34.9748, -87.6081, 'Muscle Shoals', 'AL'),# Backup 1
                (34.8023, -86.9719, 'Athens', 'AL'),      # Backup 2
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Backup 3
            ],
            'scottsboro': [
                (34.9889, -86.0083, 'Scottsboro', 'AL'),  # Primary
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Backup 1
                (34.8023, -86.9719, 'Athens', 'AL'),      # Backup 2
            ],
            'cullman': [
                (34.4640, -87.0211, 'Cullman', 'AL'),     # Primary
                (34.6059, -86.9833, 'Decatur', 'AL'),     # Backup 1
                (34.7304, -86.5861, 'Huntsville', 'AL'),  # Backup 2
            ],
        }
    
    def get_grid_points_with_backups(self, location_key: str) -> List[Tuple[float, float, str, str]]:
        """
        Get primary and backup grid points for a location
        
        Args:
            location_key: Location identifier (e.g., 'athens', 'huntsville')
        
        Returns:
            List of (lat, lon, city, state) tuples in priority order
        """
        location_key = location_key.lower()
        
        if location_key in self.grid_points:
            return self.grid_points[location_key]
        
        # Default fallback: Huntsville area
        return self.grid_points['huntsville']
    
    def try_all_grids(self, location_key: str, fetch_function, *args, **kwargs):
        """
        Try primary grid, then backups until one succeeds
        
        Args:
            location_key: Location identifier
            fetch_function: Function to call with (lat, lon, city, state, *args, **kwargs)
            *args, **kwargs: Additional arguments for fetch_function
        
        Returns:
            Result from first successful fetch, or None
        """
        grids = self.get_grid_points_with_backups(location_key)
        
        for i, (lat, lon, city, state) in enumerate(grids):
            try:
                if i == 0:
                    print(f"🎯 Trying primary grid: {city}, {state}")
                else:
                    print(f"🔄 Trying backup grid {i}: {city}, {state}")
                
                result = fetch_function(lat, lon, city, state, *args, **kwargs)
                
                # Check if result indicates failure
                if result and "unavailable" not in result.lower() and "error" not in result.lower():
                    if i > 0:
                        print(f"✅ Success with backup grid: {city}, {state}")
                    else:
                        print(f"✅ Success with primary grid: {city}, {state}")
                    return result
                else:
                    print(f"⚠️ Grid failed: {city}, {state}")
            
            except Exception as e:
                print(f"⚠️ Error with grid {city}, {state}: {e}")
                continue
        
        print(f"❌ All grids failed for {location_key}")
        return None


# Singleton instance
_backup_grid_system = None

def get_backup_grid_system():
    """Get singleton backup grid system"""
    global _backup_grid_system
    if _backup_grid_system is None:
        _backup_grid_system = BackupGridSystem()
    return _backup_grid_system


def get_forecast_with_backup(location_key: str, fetch_function, *args, **kwargs):
    """
    Fetch forecast with automatic backup fallback
    
    Args:
        location_key: Location identifier (e.g., 'athens')
        fetch_function: Function to fetch forecast
        *args, **kwargs: Additional arguments
    
    Returns:
        Forecast result or None
    """
    system = get_backup_grid_system()
    return system.try_all_grids(location_key, fetch_function, *args, **kwargs)


if __name__ == '__main__':
    # Test the backup grid system
    print("=" * 70)
    print("BACKUP GRID SYSTEM TEST")
    print("=" * 70)
    
    system = BackupGridSystem()
    
    # Test getting grids for Athens
    print("\n1. Athens grid points:")
    print("-" * 70)
    grids = system.get_grid_points_with_backups('athens')
    for i, (lat, lon, city, state) in enumerate(grids):
        priority = "Primary" if i == 0 else f"Backup {i}"
        print(f"  {priority}: {city}, {state} ({lat:.4f}, {lon:.4f})")
    
    # Test getting grids for Huntsville
    print("\n2. Huntsville grid points:")
    print("-" * 70)
    grids = system.get_grid_points_with_backups('huntsville')
    for i, (lat, lon, city, state) in enumerate(grids):
        priority = "Primary" if i == 0 else f"Backup {i}"
        print(f"  {priority}: {city}, {state} ({lat:.4f}, {lon:.4f})")
    
    # Test fallback for unknown location
    print("\n3. Unknown location fallback:")
    print("-" * 70)
    grids = system.get_grid_points_with_backups('unknown_city')
    print(f"Falls back to: {grids[0][2]}, {grids[0][3]}")
    
    print("\n" + "=" * 70)
    print("✓ Backup grid system working!")
    print("=" * 70)
