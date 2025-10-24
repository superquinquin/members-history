# Members Geocoding Scripts

This directory contains utilities for geocoding cooperative member addresses using the French government geocoding API.

## Files

- `geocoding_client.py` - Async HTTP client with rate limiting for the French geocoding API
- `geocode_members.py` - Main script to geocode all worker members from Odoo
- `__init__.py` - Python package initialization

## Prerequisites

1. Install dependencies:
```bash
cd ../backend
pip install -r requirements.txt
```

2. Set up environment variables in `../backend/.env`:
```
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

## Usage

### Basic Usage
```bash
cd scripts/
python geocode_members.py
```

### Advanced Options
```bash
# Custom output directory
python geocode_members.py --output /path/to/output/

# Limit number of members (for testing)
python geocode_members.py --limit 100

# Adjust rate limit (default: 40 req/s, max: 50 req/s)
python geocode_members.py --rate 30

# Choose output format
python geocode_members.py --format json
python geocode_members.py --format csv
python geocode_members.py --format both

# Enable debug logging
python geocode_members.py --debug
```

### Command Line Arguments

- `--output`: Output directory path (default: `../data/geocoded_members/`)
- `--format`: Output format `json|csv|both` (default: `both`)
- `--limit`: Maximum number of members to process (default: all)
- `--rate`: Request rate per second (default: 40, max: 50)
- `--debug`: Enable debug logging

## Output Files

### JSON Format (`members_geocoded.json`)
```json
{
  "total_members": 1234,
  "valid_addresses": 1200,
  "empty_addresses": 34,
  "successfully_geocoded": 1150,
  "failed_geocoding": 50,
  "skipped_addresses": 34,
  "processing_errors": 0,
  "processing_time": "45.2 seconds",
  "timestamp": "2024-01-15T10:30:00",
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

### CSV Format (`members_geocoded.csv`)
```csv
member_id,address,geocoding_status,coordinates.latitude,coordinates.longitude,coordinates.score,coordinates.label
12345,"123 Rue de la République, 75001 Paris",success,48.8566,2.3522,0.95,"123 Rue de la République 75001 Paris"
```

### Failed Addresses (`failed_addresses.json`)
Contains all addresses that failed geocoding for manual review or retry.

## Rate Limiting

The script respects the French API rate limit of 50 requests/second:
- Default rate: 40 requests/second (20% safety margin)
- Configurable via `--rate` argument
- Automatic backoff and retry on HTTP 429 errors

## Privacy & Security

- **GDPR Compliant**: Only member IDs and addresses are processed
- **No Personal Data**: Names, emails, phone numbers are excluded
- **Secure Storage**: Results contain minimal necessary information
- **HTTPS Only**: All API calls use encrypted connections

## Logging

- Console output with progress information
- `geocoding.log`: Detailed processing log
- Debug mode available with `--debug`

## Performance

- **Throughput**: ~144,000 addresses/hour at 40 req/s
- **Memory Efficient**: Streaming processing for large datasets
- **Concurrent**: Async processing with connection pooling

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure dependencies are installed and paths are correct
2. **Authentication Failures**: Check Odoo credentials in `.env` file
3. **Rate Limit Errors**: Reduce `--rate` argument below 50
4. **Network Timeouts**: Check internet connection and API availability

### Debug Mode
```bash
python geocode_members.py --debug --limit 10
```

### Test with Small Dataset
```bash
python geocode_members.py --limit 50 --format both
```

## API Reference

- **Service**: French Government Geocoding API
- **Documentation**: https://data.geopf.fr/geocodage/openapi
- **Base URL**: https://data.geopf.fr/geocodage
- **Rate Limit**: 50 requests/second
- **Authentication**: None required (public service)

## Development

### Running Tests
```bash
cd scripts/
python -m pytest tests/  # If tests exist
```

### Code Style
Follow the project's existing code style:
- Type hints required
- Async/await for network operations
- Comprehensive error handling
- Detailed logging

## License

This script follows the same license as the main project.