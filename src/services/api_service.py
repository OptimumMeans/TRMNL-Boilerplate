from datetime import datetime, UTC
import logging
import requests
from typing import Optional, Dict, Any
from ..config import Config
from urllib.parse import urlparse, urlunparse
import random

logger = logging.getLogger(__name__)

class APIService:
    '''Service for handling FBI Most Wanted API interactions.'''
    
    BASE_URL = 'https://api.fbi.gov/wanted/v1/list'
    
    def __init__(self):
        self.last_update = None
        self._cached_data = None
        self._cache_timestamp = None
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        '''Get data from FBI Most Wanted API.'''
        try:
            # Check cache first
            if self._is_cache_valid():
                return self._cached_data
            
            # Fetch new data
            data = self._fetch_data()
            
            # Update cache
            self._update_cache(data)
            self.last_update = datetime.now(UTC)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching FBI data: {str(e)}")
            return None
    
    def _fetch_data(self) -> Dict[str, Any]:
        '''Fetch data from FBI Most Wanted API with maximum available results.'''
        # First make a request to get the total count
        initial_response = requests.get(self.BASE_URL, params={'page': 1, 'per_page': 1})
        
        if initial_response.status_code != 200:
            raise Exception(f"FBI API returned status code {initial_response.status_code}")
        
        initial_data = initial_response.json()
        total_wanted = initial_data['total']
        
        # Now fetch all results in one request
        response = requests.get(self.BASE_URL, params={
            'page': 1,
            'per_page': total_wanted  # Request maximum available
        })
        
        if response.status_code != 200:
            raise Exception(f"FBI API returned status code {response.status_code}")
        
        api_data = response.json()
        
        # Process the data for display
        processed_data = {
            'timestamp': datetime.now(UTC).isoformat(),
            'total_wanted': total_wanted,
            'wanted_list': []
        }
        
        # Process all available items
        wanted_persons = []
        for item in api_data['items']:
            # Get and process the image URL
            image_url = None
            images = item.get('images', [])
            if images:
                try:
                    raw_url = images[0].get('original', '')
                    if raw_url:
                        parsed = urlparse(raw_url)
                        cleaned_url = urlunparse((
                            'https',
                            'www.fbi.gov',
                            parsed.path.replace('//', '/'),
                            '', '', ''
                        ))
                        image_url = cleaned_url
                except Exception as e:
                    logger.error(f"Error processing image URL: {str(e)}")
                    image_url = None
            
            wanted_person = {
                'title': item.get('title', 'Unknown'),
                'description': item.get('description', ''),
                'reward_text': item.get('reward_text', 'No reward information'),
                'images': image_url,
                'details': item.get('details', ''),
                'status': item.get('status', 'WANTED')
            }
            wanted_persons.append(wanted_person)
        
        # Log the total number of persons processed
        logger.info(f"Processed {len(wanted_persons)} wanted persons out of {total_wanted} total")
        
        # Randomly select one person from all available
        if wanted_persons:
            processed_data['wanted_list'] = [random.choice(wanted_persons)]
        
        return processed_data
    
    def _update_cache(self, data: Dict[str, Any]) -> None:
        '''Update the cache with new data.'''
        self._cached_data = data
        self._cache_timestamp = datetime.now(UTC)
    
    def _is_cache_valid(self) -> bool:
        '''Check if cached data is still valid.'''
        if not self._cache_timestamp:
            return False
            
        cache_age = (datetime.now(UTC) - self._cache_timestamp).total_seconds()
        return cache_age < Config.CACHE_TIMEOUT