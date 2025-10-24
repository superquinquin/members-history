# Members Geocoding Script Specification

## Overview
Script to geocode all cooperative worker members (`is_worker_member=true`) using the French government geocoding API, with strict rate limiting and privacy-compliant output.

## Directory Structure
```
project/
├── backend/
│   ├── odoo_client.py (extend existing)
│   └── requirements.txt (update)
├── scripts/
│   ├── __init__.py
│   ├── geocoding_client.py
│   ├── geocode_members.py
│   └── README.md
└── data/
    └── geocoded_members/ (output directory)
        ├── members_geocoded.json
        └── members_geocoded.csv
```

## API Reference
- **Service**: French Government Geocoding API
- **Base URL**: `https://data.geopf.fr/geocodage`
- **Endpoint**: `/search`
- **Documentation**: https://data.geopf.fr/geocodage/openapi
- **Rate Limit**: 50 requests/second maximum

## Core Components

### 1. OdooClient Extension (`backend/odoo_client.py`)
Add method to fetch worker member addresses only:

```python
def get_worker_members_addresses(self) -> List[Dict]:
    """Fetch addresses of worker members only (no personal data)"""
    domain = [('is_worker_member', '=', True)]
    fields = ['id', 'street', 'street2', 'zip', 'city']  # Privacy-compliant
    return self.search_read('res.partner', domain, fields)
```

### 2. Geocoding Client (`scripts/geocoding_client.py`)
Async HTTP client with rate limiting:

**Features:**
- Rate limiting: 40 req/s (safety margin under 50 req/s limit)
- Async requests with `aiohttp`
- Semaphore-based concurrency control
- Exponential backoff retry logic
- Connection pooling

**Key Methods:**
```python
async def geocode_address(self, address: str) -> Optional[Dict]:
    """Geocode single address with rate limiting"""
    
async def geocode_batch(self, addresses: List[Tuple[int, str]]) -> List[Dict]:
    """Geocode multiple addresses concurrently"""
```

### 3. Main Script (`scripts/geocode_members.py`)
Orchestrates the geocoding workflow:

**Workflow:**
1. Load environment variables
2. Fetch worker members from Odoo
3. Format addresses for French geocoding
4. Batch geocode with rate limiting
5. Generate output files
6. Report statistics

## Address Formatting Logic

### French Address Format
```python
def format_address(member: Dict) -> str:
    """Format French address for geocoding API"""
    parts = []
    if member.get('street'):
        parts.append(member['street'])
    if member.get('street2'):
        parts.append(member['street2'])
    if member.get('zip'):
        parts.append(member['zip'])
    if member.get('city'):
        parts.append(member['city'])
    return ', '.join(parts)
```

### Examples
- Input: `{'street': '123 Rue de la République', 'zip': '75001', 'city': 'Paris'}`
- Output: `"123 Rue de la République, 75001 Paris"`

## Rate Limiting Strategy

### Implementation
- **Target Rate**: 40 requests/second (20% safety margin)
- **Method**: `asyncio.Semaphore(40)` for concurrent control
- **Token Bucket**: Optional for precise rate control
- **Backoff**: Exponential (1s, 2s, 4s, 8s max) for HTTP 429

### Performance Estimates
- **Throughput**: ~144,000 addresses/hour
- **Concurrent Requests**: 40 maximum
- **Memory**: Efficient streaming for large datasets

## Error Handling & Resilience

### Network Errors
- Connection timeout: 10 seconds
- Read timeout: 30 seconds
- Retry with exponential backoff
- Failed request logging for manual retry

### API Errors
- HTTP 429: Automatic backoff and retry
- HTTP 400/500: Log and continue with next address
- Invalid responses: Mark as failed, continue processing

### Data Validation
- Empty addresses: Skip with warning
- Invalid French addresses: Log and continue
- Missing coordinates: Mark as failed

## Output Formats

### JSON Output (`members_geocoded.json`)
```json
{
  "total_members": 1234,
  "successfully_geocoded": 1201,
  "failed_geocoding": 33,
  "processing_time": "45.2 seconds",
  "members": [
    {
      "member_id": 12345,
      "address": "123 Rue de la République, 75001 Paris",
      "coordinates": {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "score": 0.95,
        "label": "123 Rue de la République 75001 Paris"
      },
      "geocoding_status": "success"
    }
  ]
}
```

### CSV Output (`members_geocoded.csv`)
```csv
member_id,address,latitude,longitude,score,geocoding_status
12345,"123 Rue de la République, 75001 Paris",48.8566,2.3522,0.95,success
```

### Privacy Compliance
- **No personal data**: Names, emails, phone numbers excluded
- **Member ID only**: Numeric identifier for reference
- **Address only**: Geographic information necessary for geocoding
- **GDPR compliant**: Minimal data collection and storage

## Dependencies

### New Requirements
```txt
aiohttp>=3.8.0          # Async HTTP client
asyncio-throttle>=1.0.2  # Rate limiting utilities
tqdm>=4.64.0            # Progress bars
```

### Existing Dependencies
- `xmlrpc.client` (Odoo integration)
- `python-dotenv` (Environment variables)
- `typing` (Type hints)

## Usage Instructions

### Environment Setup
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables in .env
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

### Running the Script
```bash
cd scripts/
python geocode_members.py --output ../data/geocoded_members/
```

### Command Line Options
- `--output`: Output directory path (default: `../data/geocoded_members/`)
- `--format`: Output format `json|csv|both` (default: `both`)
- `--limit`: Maximum number of members to process (default: all)
- `--rate`: Request rate per second (default: 40)

## Monitoring & Logging

### Progress Tracking
- Real-time progress bar with `tqdm`
- ETA calculation based on current rate
- Success/failure counters
- Processing time statistics

### Logging Levels
- **INFO**: Progress updates, summary statistics
- **WARNING**: Skipped addresses, API warnings
- **ERROR**: Failed requests, network issues
- **DEBUG**: Detailed request/response data (optional)

### Log Files
- `geocoding.log`: Main processing log
- `failed_addresses.log`: Addresses that failed geocoding
- `debug.log`: Detailed debugging (if enabled)

## Testing Strategy

### Unit Tests
- Address formatting logic
- Rate limiting behavior
- Error handling scenarios
- Output format validation

### Integration Tests
- Odoo connection and authentication
- API endpoint connectivity
- End-to-end workflow with sample data

### Performance Tests
- Rate limiting compliance
- Memory usage with large datasets
- Concurrent request handling

## Security Considerations

### API Key Management
- No API keys required (public service)
- Environment variables for Odoo credentials
- No sensitive data in output files

### Data Privacy
- GDPR-compliant data handling
- Minimal data collection
- Secure storage of geocoding results

### Network Security
- HTTPS-only API calls
- Certificate validation
- Request timeout configuration

## Future Enhancements

### Batch Processing
- CSV file upload to API for large batches
- Asynchronous job processing
- Result polling and notification

### Caching
- Local address coordinate cache
- Redis integration for distributed caching
- Cache invalidation strategies

### Advanced Features
- Address standardization
- Coordinate precision validation
- Geographic clustering analysis
- Integration with mapping services

## Troubleshooting

### Common Issues
1. **Rate Limit Exceeded**: Reduce concurrent requests or increase delays
2. **Invalid Addresses**: Check address formatting and French postal codes
3. **Network Timeouts**: Increase timeout values or check connectivity
4. **Odoo Authentication**: Verify credentials and database access

### Debug Mode
```bash
python geocode_members.py --debug --limit 10
```

### Performance Tuning
- Adjust semaphore size based on network conditions
- Monitor API response times
- Optimize batch sizes for memory efficiency