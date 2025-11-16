"""
Utility functions for backend operations.

Provides helper functions for common operations like extracting IDs from
Odoo Many2one fields and validating inputs.
"""

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
