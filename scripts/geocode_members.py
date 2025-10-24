#!/usr/bin/env python3
"""
Geocode cooperative worker members using French government API.

This script fetches all worker members from Odoo, formats their addresses,
and geocodes them using the French government geocoding API with rate limiting.
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from odoo_client import OdooClient
except ImportError:
    print(
        "Error: Could not import odoo_client. Make sure backend/odoo_client.py exists."
    )
    sys.exit(1)

try:
    from geocoding_client import GeocodingClient
except ImportError:
    print(
        "Error: Could not import geocoding_client. Make sure scripts/geocoding_client.py exists."
    )
    sys.exit(1)


def format_address(member: Dict) -> str:
    """Format French address for geocoding API."""
    parts = []
    if member.get("street"):
        parts.append(member["street"])
    if member.get("street2"):
        parts.append(member["street2"])
    if member.get("zip"):
        parts.append(member["zip"])
    if member.get("city"):
        parts.append(member["city"])
    return ", ".join(parts)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("geocoding.log")],
    )
    return logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Geocode cooperative worker members")
    parser.add_argument(
        "--output",
        type=str,
        default="data/geocoded_members/",
        help="Output directory path (default: data/geocoded_members/)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum number of members to process (default: all)"
    )
    parser.add_argument(
        "--rate", type=int, default=40, help="Request rate per second (default: 40)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


async def main():
    """Main geocoding workflow."""
    args = parse_arguments()
    logger = setup_logging(args.debug)

    # Create output directory
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory resolved to: {output_dir}")

    logger.info("Starting members geocoding")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Output format: {args.format}")
    logger.info(f"Rate limit: {args.rate} requests/second")

    start_time = time.time()

    try:
        # Initialize Odoo client and fetch members
        logger.info("Connecting to Odoo...")
        odoo_client = OdooClient()

        if not odoo_client.authenticate():
            logger.error("Failed to authenticate with Odoo")
            return 1

        logger.info("Fetching worker members...")
        members = odoo_client.get_worker_members_addresses()

        if args.limit:
            members = members[: args.limit]
            logger.info(f"Limited to {args.limit} members")

        logger.info(f"Found {len(members)} worker members to geocode")

        # Prepare addresses for geocoding
        addresses = []
        for member in members:
            address = format_address(member)
            addresses.append((member["id"], address))

        # Filter out empty addresses
        valid_addresses = [
            (mid, addr) for mid, addr in addresses if addr and addr.strip()
        ]
        empty_count = len(addresses) - len(valid_addresses)

        if empty_count > 0:
            logger.warning(f"Skipping {empty_count} members with empty addresses")

        logger.info(f"Geocoding {len(valid_addresses)} valid addresses...")

        # Geocode addresses
        async with GeocodingClient(max_requests_per_second=args.rate) as geo_client:
            results = await geo_client.geocode_batch(valid_addresses)

        # Process results
        successful = sum(1 for r in results if r.get("geocoding_status") == "success")
        failed = sum(1 for r in results if r.get("geocoding_status") == "failed")
        skipped = sum(1 for r in results if r.get("geocoding_status") == "skipped")
        errors = sum(1 for r in results if r.get("geocoding_status") == "error")

        processing_time = time.time() - start_time

        # Create summary
        summary = {
            "total_members": len(members),
            "valid_addresses": len(valid_addresses),
            "empty_addresses": empty_count,
            "successfully_geocoded": successful,
            "failed_geocoding": failed,
            "skipped_addresses": skipped,
            "processing_errors": errors,
            "processing_time": f"{processing_time:.2f} seconds",
            "timestamp": datetime.now().isoformat(),
            "members": results,
        }

        logger.info(f"Geocoding completed in {processing_time:.2f} seconds")
        logger.info(f"Successfully geocoded: {successful}")
        logger.info(f"Failed geocoding: {failed}")
        logger.info(f"Skipped addresses: {skipped}")
        logger.info(f"Processing errors: {errors}")

        # Save results
        if args.format in ["json", "both"]:
            json_file = output_dir / "members_geocoded.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON results saved to {json_file}")

        if args.format in ["csv", "both"]:
            csv_file = output_dir / "members_geocoded.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                if results:
                    # Use keys from first result for CSV headers
                    fieldnames = ["member_id", "address", "geocoding_status"]

                    # Add coordinate fields if present
                    if results and "coordinates" in results[0]:
                        coord_fields = ["latitude", "longitude", "score", "label"]
                        fieldnames.extend(
                            [f"coordinates.{field}" for field in coord_fields]
                        )

                    # Add error field if present
                    if any("error" in r for r in results):
                        fieldnames.append("error")

                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for result in results:
                        # Flatten nested coordinates for CSV
                        row = {}
                        for field in fieldnames:
                            if field.startswith("coordinates."):
                                coord_field = field.replace("coordinates.", "")
                                if "coordinates" in result and result["coordinates"]:
                                    row[field] = result["coordinates"].get(coord_field)
                                else:
                                    row[field] = None
                            else:
                                row[field] = result.get(field)
                        writer.writerow(row)

            logger.info(f"CSV results saved to {csv_file}")

        # Save failed addresses for retry
        failed_results = [
            r for r in results if r.get("geocoding_status") in ["failed", "error"]
        ]
        if failed_results:
            failed_file = output_dir / "failed_addresses.json"
            with open(failed_file, "w", encoding="utf-8") as f:
                json.dump(failed_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Failed addresses saved to {failed_file}")

        logger.info("Geocoding script completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        if args.debug:
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

