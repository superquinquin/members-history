import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

class GeocodingClient:
    """Async French geocoding API client with rate limiting."""
    
    def __init__(self, max_requests_per_second: int = 40):
        """
        Initialize geocoding client.
        
        Args:
            max_requests_per_second: Maximum requests per second (default: 40)
        """
        self.base_url = "https://data.geopf.fr/geocodage"
        self.max_requests_per_second = max_requests_per_second
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting with token bucket
        self.tokens = max_requests_per_second
        self.last_refill = time.time()
        self.bucket_size = max_requests_per_second
        self.refill_rate = max_requests_per_second  # tokens per second
        
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")
            
        connector = aiohttp.TCPConnector(
            limit=self.max_requests_per_second * 2,
            limit_per_host=self.max_requests_per_second,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,  # Total timeout
            connect=10,  # Connection timeout
            sock_read=20  # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Members-Geocoding/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limit using token bucket."""
        now = time.time()
        
        # Refill tokens based on time elapsed
        time_elapsed = now - self.last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        self.last_refill = now
        
        # Wait if we don't have enough tokens
        while self.tokens < 1:
            await asyncio.sleep(0.1)  # Small delay
            now = time.time()
            time_elapsed = now - self.last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
            self.last_refill = now
        
        # Consume one token
        self.tokens -= 1
    
    async def geocode_address(self, address: str) -> Optional[Dict]:
        """
        Geocode a single address.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Dictionary with coordinates or None if failed
        """
        if not address or not address.strip():
            return None
            
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
            
        async with self.semaphore:
            await self._wait_for_rate_limit()
            
            try:
                # Prepare request parameters
                params = {
                    'q': address.strip(),
                    'limit': 1,
                    'index': 'address',
                    'autocomplete': '0'  # Disable autocomplete for exact matching
                }
                
                url = f"{self.base_url}/search"
                encoded_params = '&'.join(f"{k}={quote(str(v))}" for k, v in params.items())
                full_url = f"{url}?{encoded_params}"
                
                async with self.session.get(full_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('features') and len(data['features']) > 0:
                            feature = data['features'][0]
                            props = feature.get('properties', {})
                            geometry = feature.get('geometry', {})
                            
                            return {
                                'latitude': geometry.get('coordinates', [])[1] if len(geometry.get('coordinates', [])) > 1 else None,
                                'longitude': geometry.get('coordinates', [])[0] if len(geometry.get('coordinates', [])) > 0 else None,
                                'score': props.get('_score', 0),
                                'label': props.get('label', ''),
                                'id': props.get('id', ''),
                                'type': props.get('type', ''),
                                'housenumber': props.get('housenumber'),
                                'street': props.get('street'),
                                'postcode': props.get('postcode'),
                                'city': props.get('city'),
                                'context': props.get('context', '')
                            }
                        else:
                            self.logger.warning(f"No results found for address: {address}")
                            return None
                    else:
                        self.logger.error(f"API error {response.status} for address: {address}")
                        return None
                        
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout geocoding address: {address}")
                return None
            except Exception as e:
                # Handle aiohttp errors gracefully
                if "ClientError" in str(type(e)) or "aiohttp" in str(type(e)):
                    self.logger.error(f"Network error geocoding address {address}: {e}")
                else:
                    self.logger.error(f"Unexpected error geocoding address {address}: {e}")
                return None
    
    async def geocode_batch(self, addresses: List[Tuple[int, str]]) -> List[Dict]:
        """
        Geocode multiple addresses sequentially with rate limiting.
        
        Args:
            addresses: List of (member_id, address) tuples
            
        Returns:
            List of geocoding results with member_id
        """
        results = []
        
        for member_id, address in addresses:
            if address and address.strip():
                result = await self._geocode_with_id(member_id, address)
                results.append(result)
            else:
                # Handle empty addresses
                result = await self._return_empty_result(member_id, address)
                results.append(result)
        
        return results
    
    async def _geocode_with_id(self, member_id: int, address: str) -> Dict:
        """Geocode address and include member_id in result."""
        geocoded = await self.geocode_address(address)
        
        if geocoded:
            return {
                'member_id': member_id,
                'address': address,
                'coordinates': {
                    'latitude': geocoded['latitude'],
                    'longitude': geocoded['longitude'],
                    'score': geocoded['score'],
                    'label': geocoded['label']
                },
                'geocoding_status': 'success'
            }
        else:
            return {
                'member_id': member_id,
                'address': address,
                'geocoding_status': 'failed',
                'error': 'No results found'
            }
    
    async def _return_empty_result(self, member_id: int, address: str) -> Dict:
        """Return result for empty address."""
        return {
            'member_id': member_id,
            'address': address,
            'geocoding_status': 'skipped',
            'error': 'Empty address'
        }
    
    def get_stats(self) -> Dict:
        """Get client statistics."""
        return {
            'max_requests_per_second': self.max_requests_per_second,
            'available_tokens': self.tokens,
            'session_active': self.session is not None and not self.session.closed
        }