"""
ml_bridge.py - Bridge to fetch ML data from local PC via ngrok
Add this file to your Render project
"""

import os
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Get ngrok URL from environment variable
LOCAL_ML_URL = os.environ.get('LOCAL_ML_URL', '')

# Cache ML data for 5 minutes to reduce requests
ml_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)
}

def get_ml_predictions():
    """Fetch ML predictions from local PC via ngrok"""
    
    # Check if we have cached data that's still fresh
    if ml_cache['data'] and ml_cache['timestamp']:
        age = datetime.now() - ml_cache['timestamp']
        if age < ml_cache['cache_duration']:
            logger.info("Using cached ML data")
            return ml_cache['data']
    
    # No LOCAL_ML_URL configured
    if not LOCAL_ML_URL:
        logger.warning("LOCAL_ML_URL not configured")
        return {
            'success': False,
            'error': 'Local ML not configured',
            'message': 'Set LOCAL_ML_URL environment variable'
        }
    
    # Fetch from local PC
    try:
        url = f"{LOCAL_ML_URL}/api/ml/predictions-external"
        logger.info(f"Fetching ML data from: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.ok:
            data = response.json()
            
            # Cache the successful response
            ml_cache['data'] = data
            ml_cache['timestamp'] = datetime.now()
            
            logger.info("Successfully fetched ML data from local PC")
            return data
        else:
            logger.error(f"Local ML returned status {response.status_code}")
            return {
                'success': False,
                'error': f'Local ML returned {response.status_code}',
                'message': 'Check if your PC weather system is running'
            }
    
    except requests.exceptions.Timeout:
        logger.error("Timeout connecting to local ML")
        return {
            'success': False,
            'error': 'Connection timeout',
            'message': 'Local ML did not respond in time'
        }
    
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to local ML")
        return {
            'success': False,
            'error': 'Connection failed',
            'message': 'Cannot reach local ML - is ngrok running?'
        }
    
    except Exception as e:
        logger.error(f"Error fetching ML data: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Unexpected error fetching ML data'
        }

def clear_ml_cache():
    """Clear the ML data cache"""
    ml_cache['data'] = None
    ml_cache['timestamp'] = None
    logger.info("ML cache cleared")
