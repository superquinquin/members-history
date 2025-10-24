#!/usr/bin/env python3
"""
Calculate distances from cooperative worker members to the store.

This script reads the geocoded members JSON output from geocode_members.py,
geocodes the store address, and calculates distances using the Haversine formula.
"""

import argparse
import asyncio
import csv
import json
import logging
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from geocoding_client import GeocodingClient
except ImportError:
    print(
        "Error: Could not import geocoding_client. Make sure scripts/geocoding_client.py exists."
    )
    sys.exit(1)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Latitude and longitude of point 1 in decimal degrees
        lat2, lon2: Latitude and longitude of point 2 in decimal degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371.0
    return c * r


def setup_logging(debug: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("distance_calculation.log")],
    )
    return logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Calculate distances from members to store")
    parser.add_argument(
        "--input",
        type=str,
        default="data/geocoded_members/members_geocoded.json",
        help="Input JSON file from geocode_members.py (default: data/geocoded_members/members_geocoded.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/distances/",
        help="Output directory path (default: data/distances/)",
    )
    parser.add_argument(
        "--store-address",
        type=str,
        default="55 rue pierre legrand 59800 lille",
        help="Store address (default: '55 rue pierre legrand 59800 lille')",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


async def geocode_store_address(address: str, logger: logging.Logger) -> Optional[Tuple[float, float]]:
    """Geocode the store address and return coordinates."""
    logger.info(f"Geocoding store address: {address}")
    
    async with GeocodingClient(max_requests_per_second=10) as geo_client:
        results = await geo_client.geocode_batch([(0, address)])
        
        if results and results[0].get("geocoding_status") == "success":
            coords = results[0]["coordinates"]
            lat = coords["latitude"]
            lon = coords["longitude"]
            logger.info(f"Store coordinates: {lat}, {lon}")
            return lat, lon
        else:
            error = results[0].get("error", "Unknown error") if results else "No results"
            logger.error(f"Failed to geocode store address: {error}")
            return None


def load_geocoded_members(input_file: Path, logger: logging.Logger) -> Dict:
    """Load and validate the geocoded members JSON file."""
    logger.info(f"Loading geocoded members from: {input_file}")
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate structure
        if "members" not in data:
            logger.error("Invalid JSON structure: missing 'members' key")
            sys.exit(1)
        
        logger.info(f"Loaded {data.get('total_members', 0)} total members")
        logger.info(f"Successfully geocoded: {data.get('successfully_geocoded', 0)}")
        
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        sys.exit(1)


def calculate_distances_for_members(
    members: List[Dict], 
    store_lat: float, 
    store_lon: float,
    logger: logging.Logger
) -> List[Dict]:
    """Calculate distances for all members with valid coordinates."""
    logger.info("Calculating distances for members...")
    
    distance_results = []
    processed = 0
    skipped = 0
    
    for member in members:
        processed += 1
        
        # Skip members without successful geocoding
        if member.get("geocoding_status") != "success" or "coordinates" not in member:
            skipped += 1
            continue
        
        coords = member["coordinates"]
        if not coords or "latitude" not in coords or "longitude" not in coords:
            skipped += 1
            continue
        
        member_lat = coords["latitude"]
        member_lon = coords["longitude"]
        
        # Calculate distance
        distance_km = haversine_distance(member_lat, member_lon, store_lat, store_lon)
        
        # Create result entry
        result = {
            "member_id": member["member_id"],
            "address": member["address"],
            "distance_km": round(distance_km, 3),
            "coordinates": {
                "latitude": member_lat,
                "longitude": member_lon,
                "label": coords.get("label", "")
            }
        }
        
        distance_results.append(result)
        
        if processed % 100 == 0:
            logger.info(f"Processed {processed} members...")
    
    logger.info(f"Distance calculation complete: {len(distance_results)} distances calculated, {skipped} skipped")
    return distance_results


def calculate_statistics(distances: List[Dict]) -> Dict:
    """Calculate distance statistics."""
    if not distances:
        return {}
    
    distance_values = [d["distance_km"] for d in distances]
    
    stats = {
        "total_members": len(distances),
        "min_distance_km": round(min(distance_values), 3),
        "max_distance_km": round(max(distance_values), 3),
        "avg_distance_km": round(sum(distance_values) / len(distance_values), 3),
        "median_distance_km": round(sorted(distance_values)[len(distance_values) // 2], 3),
    }
    
    # Add distance distribution
    stats["distance_distribution"] = {
        "under_1km": len([d for d in distance_values if d < 1]),
        "1_to_5km": len([d for d in distance_values if 1 <= d < 5]),
        "5_to_10km": len([d for d in distance_values if 5 <= d < 10]),
        "10_to_20km": len([d for d in distance_values if 10 <= d < 20]),
        "over_20km": len([d for d in distance_values if d >= 20]),
    }
    
    return stats


async def main():
    """Main distance calculation workflow."""
    args = parse_arguments()
    logger = setup_logging(args.debug)
    
    # Create output directory
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    start_time = time.time()
    
    try:
        # Load geocoded members
        input_file = Path(args.input).resolve()
        geocoded_data = load_geocoded_members(input_file, logger)
        
        # Geocode store address
        store_coords = await geocode_store_address(args.store_address, logger)
        if store_coords is None:
            logger.error("Failed to geocode store address. Exiting.")
            return 1
        
        store_lat, store_lon = store_coords
        
        # Calculate distances
        distance_results = calculate_distances_for_members(
            geocoded_data["members"], store_lat, store_lon, logger
        )
        
        # Calculate statistics
        stats = calculate_statistics(distance_results)
        
        processing_time = time.time() - start_time
        
        # Create final output
        output_data = {
            "store_address": args.store_address,
            "store_coordinates": {
                "latitude": store_lat,
                "longitude": store_lon
            },
            "statistics": stats,
            "processing_time": f"{processing_time:.2f} seconds",
            "timestamp": datetime.now().isoformat(),
            "members": distance_results
        }
        
        logger.info(f"Distance calculation completed in {processing_time:.2f} seconds")
        logger.info(f"Average distance: {stats.get('avg_distance_km', 'N/A')} km")
        logger.info(f"Distance range: {stats.get('min_distance_km', 'N/A')} - {stats.get('max_distance_km', 'N/A')} km")
        
        # Save results
        if args.format in ["json", "both"]:
            json_file = output_dir / "member_distances.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON results saved to {json_file}")
        
        if args.format in ["csv", "both"]:
            csv_file = output_dir / "member_distances.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                if distance_results:
                    fieldnames = ["member_id", "address", "distance_km", "latitude", "longitude", "label"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for result in distance_results:
                        row = {
                            "member_id": result["member_id"],
                            "address": result["address"],
                            "distance_km": result["distance_km"],
                            "latitude": result["coordinates"]["latitude"],
                            "longitude": result["coordinates"]["longitude"],
                            "label": result["coordinates"]["label"]
                        }
                        writer.writerow(row)
            
            logger.info(f"CSV results saved to {csv_file}")
        
        logger.info("Distance calculation script completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        if args.debug:
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)