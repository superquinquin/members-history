"""
Utility functions for backend operations.

Provides helper functions for common operations like extracting IDs from
Odoo Many2one fields and validating inputs.
"""

import json
import os
from datetime import datetime
from typing import Any, Optional, Union, Dict


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
    DEPRECATED: Load cycle data from the cycles JSON file.

    This function is deprecated. Use get_shift_config_dict() and cycle_calculator
    module instead for dynamic cycle calculation.

    Args:
        year: Year to load cycle data for (default: 2025)

    Returns:
        Dictionary containing cycle data, or None if file not found

    Examples:
        >>> data = load_cycle_data(2025)
        >>> data['year']
        2025
    """
    import warnings
    warnings.warn(
        "load_cycle_data() is deprecated. Use get_shift_config_dict() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Get the path to the data directory (relative to backend directory)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(backend_dir)
    cycles_file = os.path.join(project_dir, "data", f"cycles_{year}.json")

    try:
        with open(cycles_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_shift_config_dict() -> Dict[str, any]:
    """
    Get shift configuration dictionary.

    This is a simple wrapper that returns the default shift configuration.
    In production, this is fetched from Odoo via odoo_client.get_shift_config().

    Returns:
        Dictionary with weeks_per_cycle and week_a_date

    Examples:
        >>> config = get_shift_config_dict()
        >>> config['weeks_per_cycle']
        4
    """
    # Default configuration
    # In app.py, this is overridden by calling odoo.get_shift_config()
    return {
        "weeks_per_cycle": 4,
        "week_a_date": "2025-01-13"
    }


def get_last_n_cycles_date_range(
    n: int = 13,
    today: Optional[str] = None,
    shift_config: Optional[Dict[str, any]] = None
) -> tuple[str, str]:
    """
    Calculate the date range for the last N complete cycles.

    Uses dynamic cycle calculation based on shift configuration rather than
    loading from JSON files. This allows the function to work indefinitely
    without needing year-specific cycle files.

    Args:
        n: Number of cycles to look back (default: 13, approximately 12 months)
        today: Today's date in ISO format (YYYY-MM-DD), defaults to actual today
        shift_config: Optional dict with 'weeks_per_cycle' and 'week_a_date'.
                     If not provided, uses default configuration.

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> # If today is 2025-11-24 (Cycle 12, Week B)
        >>> get_last_n_cycles_date_range(13)
        ('2025-01-13', '2025-11-24')
    """
    from cycle_calculator import get_cycle_date_range

    # Get shift configuration
    if shift_config is None:
        shift_config = get_shift_config_dict()

    # Use the cycle calculator to get the date range
    return get_cycle_date_range(
        n_cycles=n,
        week_a_start=shift_config["week_a_date"],
        weeks_per_cycle=shift_config["weeks_per_cycle"],
        end_date=today
    )
