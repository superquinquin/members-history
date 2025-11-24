"""
Utility functions for backend operations.

Provides helper functions for common operations like extracting IDs from
Odoo Many2one fields and validating inputs.
"""

import json
import os
from datetime import datetime
from typing import Any, Optional, Union


def extract_id(many2one_field: Any) -> Optional[int]:
    """
    Extract ID from Odoo Many2one field.

    Many2one fields in Odoo are returned as [id, name] tuples, or False for null.

    Args:
        many2one_field: Field value from Odoo (can be [id, name], int, or False)

    Returns:
        Integer ID if present, None otherwise

    Examples:
        >>> extract_id([123, "Test Name"])
        123
        >>> extract_id(456)
        456
        >>> extract_id(False)
        None
        >>> extract_id(None)
        None
    """
    if not many2one_field:
        return None

    if isinstance(many2one_field, list) and len(many2one_field) > 0:
        return many2one_field[0]

    if isinstance(many2one_field, int):
        return many2one_field

    return None


def extract_name(many2one_field: Any) -> Optional[str]:
    """
    Extract name from Odoo Many2one field.

    Args:
        many2one_field: Field value from Odoo (can be [id, name] or False)

    Returns:
        String name if present, None otherwise

    Examples:
        >>> extract_name([123, "Test Name"])
        "Test Name"
        >>> extract_name(False)
        None
        >>> extract_name([123])
        None
    """
    if not many2one_field:
        return None

    if isinstance(many2one_field, list) and len(many2one_field) > 1:
        return many2one_field[1]

    return None


def is_valid_many2one(field: Any) -> bool:
    """
    Check if field is a valid Many2one with both ID and name.

    Args:
        field: Field value to check

    Returns:
        True if field is [id, name] format, False otherwise

    Examples:
        >>> is_valid_many2one([123, "Test"])
        True
        >>> is_valid_many2one([123])
        False
        >>> is_valid_many2one(False)
        False
    """
    return isinstance(field, list) and len(field) >= 2


def validate_positive_int(value: Any, field_name: str = "value") -> int:
    """
    Validate that a value is a positive integer.

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        Integer value if valid

    Raises:
        ValueError: If value is not a positive integer

    Examples:
        >>> validate_positive_int(123, "member_id")
        123
        >>> validate_positive_int("abc", "member_id")
        ValueError: member_id must be a positive integer
        >>> validate_positive_int(-5, "member_id")
        ValueError: member_id must be a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        return int_value
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a positive integer")


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with a default.

    Similar to dict.get() but logs when default is used.

    Args:
        dictionary: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    return dictionary.get(key, default)


def load_cycle_data(year: int = 2025) -> Optional[dict]:
    """
    Load cycle data from the cycles JSON file.

    Args:
        year: Year to load cycle data for (default: 2025)

    Returns:
        Dictionary containing cycle data, or None if file not found

    Examples:
        >>> data = load_cycle_data(2025)
        >>> data['year']
        2025
    """
    # Get the path to the data directory (relative to backend directory)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(backend_dir)
    cycles_file = os.path.join(project_dir, "data", f"cycles_{year}.json")

    try:
        with open(cycles_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_last_n_cycles_date_range(n: int = 13, today: Optional[str] = None) -> tuple[str, str]:
    """
    Calculate the date range for the last N complete cycles.

    Args:
        n: Number of cycles to look back (default: 13, approximately 12 months)
        today: Today's date in ISO format (YYYY-MM-DD), defaults to actual today

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> # If today is 2025-11-24 (Cycle 12, Week B)
        >>> get_last_n_cycles_date_range(13)
        ('2025-01-13', '2025-11-23')  # From Cycle 1 start to end of Cycle 12 Week A
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    today_date = datetime.strptime(today, "%Y-%m-%d")
    current_year = today_date.year

    # Load cycle data for current year
    cycle_data = load_cycle_data(current_year)
    if not cycle_data:
        # Fallback: if no cycle data, use simple 12-month calculation
        # This is approximately 365 days back
        fallback_start = datetime(today_date.year - 1, today_date.month, today_date.day)
        return (fallback_start.strftime("%Y-%m-%d"), today)

    cycles = cycle_data.get("cycles", [])
    if not cycles:
        # Fallback if cycles list is empty
        fallback_start = datetime(today_date.year - 1, today_date.month, today_date.day)
        return (fallback_start.strftime("%Y-%m-%d"), today)

    # Find the current cycle (the cycle that contains today)
    current_cycle_index = None
    for i, cycle in enumerate(cycles):
        cycle_start = datetime.strptime(cycle["start_date"], "%Y-%m-%d")
        cycle_end = datetime.strptime(cycle["end_date"], "%Y-%m-%d")

        if cycle_start <= today_date <= cycle_end:
            current_cycle_index = i
            break

    # If we're not in any defined cycle (e.g., between years), use the last cycle
    if current_cycle_index is None:
        # Check if we're past all cycles
        last_cycle_end = datetime.strptime(cycles[-1]["end_date"], "%Y-%m-%d")
        if today_date > last_cycle_end:
            # We're past the last cycle of the year, try next year's data
            next_year_data = load_cycle_data(current_year + 1)
            if next_year_data and next_year_data.get("cycles"):
                # Use the first cycle of next year
                next_cycles = next_year_data["cycles"]
                # Find current cycle in next year
                for i, cycle in enumerate(next_cycles):
                    cycle_start = datetime.strptime(cycle["start_date"], "%Y-%m-%d")
                    cycle_end = datetime.strptime(cycle["end_date"], "%Y-%m-%d")
                    if cycle_start <= today_date <= cycle_end:
                        current_cycle_index = i
                        # Extend cycles list with next year
                        cycles = cycles + next_cycles
                        break

        # If still not found, use last cycle as current
        if current_cycle_index is None:
            current_cycle_index = len(cycles) - 1

    # Calculate the start cycle index (n cycles back)
    start_cycle_index = max(0, current_cycle_index - n + 1)

    # Get start date from the start cycle
    start_date = cycles[start_cycle_index]["start_date"]

    # End date is today (we want all data up to now, not just complete cycles)
    end_date = today

    return (start_date, end_date)
