#!/usr/bin/env python3
"""
Count active cooperative members per year based on shift.template.registration.line records.

A member is considered "active" on a given date if they have at least one
registration line where:
- date_begin <= target_date
- date_end is null/False OR date_end >= target_date
- state is not 'cancel'
"""

import sys
from datetime import date
from pathlib import Path
from typing import Dict, List

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from odoo_client import OdooClient
except ImportError:
    print("Error: Could not import odoo_client. Make sure backend/odoo_client.py exists.")
    sys.exit(1)


def parse_date(date_value) -> date | None:
    """Parse a date value from Odoo (can be string or False)."""
    if not date_value or date_value is False:
        return None
    if isinstance(date_value, str):
        return date.fromisoformat(date_value[:10])
    return date_value


def is_active_on_date(line: Dict, target_date: date) -> bool:
    """Check if a registration line was active on a specific date."""
    # Skip cancelled lines
    if line.get("state") == "cancel":
        return False

    date_begin = parse_date(line.get("date_begin"))
    date_end = parse_date(line.get("date_end"))

    if date_begin is None or date_begin > target_date:
        return False
    if date_end is not None and date_end < target_date:
        return False
    return True


def extract_partner_id(partner_field) -> int | None:
    """Extract partner ID from Many2one field [id, name] or int."""
    if isinstance(partner_field, list) and len(partner_field) > 0:
        return partner_field[0]
    if isinstance(partner_field, int):
        return partner_field
    return None


def count_active_members_on_date(lines: List[Dict], target_date: date) -> int:
    """Count unique members with active registration lines on a given date."""
    active_partner_ids = set()

    for line in lines:
        if is_active_on_date(line, target_date):
            partner_id = extract_partner_id(line.get("partner_id"))
            if partner_id:
                active_partner_ids.add(partner_id)

    return len(active_partner_ids)


def main():
    """Main script logic."""
    print("Connecting to Odoo...")
    odoo_client = OdooClient()

    if not odoo_client.authenticate():
        print("Error: Failed to authenticate with Odoo")
        return 1

    print("Fetching shift.template.registration.line records...")

    # Fetch all registration lines with date ranges
    fields = ["id", "partner_id", "date_begin", "date_end", "state"]
    lines = odoo_client.search_read("shift.template.registration.line", [], fields)

    print(f"Found {len(lines)} registration lines")

    # Determine year range from data
    years_with_data = set()
    for line in lines:
        date_begin = parse_date(line.get("date_begin"))
        if date_begin:
            years_with_data.add(date_begin.year)

    if not years_with_data:
        print("No registration lines found with valid dates")
        return 1

    min_year = min(years_with_data)
    current_year = date.today().year

    print()
    print("Active Members History (as of December 31st)")
    print("=" * 44)
    print(f"{'Year':<8}| Active Members")
    print("-" * 8 + "|" + "-" * 15)

    for year in range(min_year, current_year + 1):
        target_date = date(year, 12, 31)
        count = count_active_members_on_date(lines, target_date)
        print(f"{year:<8}| {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
