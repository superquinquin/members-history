"""
Cycle and week calculation module.

Provides functions to dynamically calculate shift cycles and weeks based on
Odoo configuration (shift_week_a_date and shift_weeks_per_cycle) rather than
using hardcoded JSON files.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Week letter mapping
WEEK_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']


def validate_shift_config(week_a_date: str, weeks_per_cycle: int) -> bool:
    """
    Validate shift configuration parameters.

    Args:
        week_a_date: Week A start date in ISO format (YYYY-MM-DD)
        weeks_per_cycle: Number of weeks per cycle

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    try:
        week_a = datetime.strptime(week_a_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid week_a_date format: {week_a_date}") from e

    # Check if it's a Monday (weekday() returns 0 for Monday)
    if week_a.weekday() != 0:
        logger.warning(
            f"Week A date {week_a_date} is not a Monday (weekday={week_a.weekday()}). "
            f"This may cause inconsistencies with expected week boundaries."
        )

    # Check weeks_per_cycle is reasonable
    if not 1 <= weeks_per_cycle <= 12:
        raise ValueError(
            f"weeks_per_cycle must be between 1 and 12, got {weeks_per_cycle}"
        )

    return True


def calculate_cycle_info(
    target_date: str,
    week_a_start: str,
    weeks_per_cycle: int
) -> Dict[str, any]:
    """
    Calculate cycle number and week letter for a given date.

    Args:
        target_date: Date to check (YYYY-MM-DD)
        week_a_start: Initial Week A start date (YYYY-MM-DD)
        weeks_per_cycle: Number of weeks per cycle (typically 4)

    Returns:
        Dictionary with cycle and week information:
        {
            'cycle_number': int,      # 1-indexed cycle number
            'week_letter': str,       # 'A', 'B', 'C', 'D', etc.
            'week_number': int,       # 0-indexed week within cycle
            'week_start': str,        # Week start date (YYYY-MM-DD)
            'week_end': str,          # Week end date (YYYY-MM-DD)
            'cycle_start': str,       # Cycle start date (YYYY-MM-DD)
            'cycle_end': str          # Cycle end date (YYYY-MM-DD)
        }

    Raises:
        ValueError: If target_date is before week_a_start
    """
    # Validate configuration
    validate_shift_config(week_a_start, weeks_per_cycle)

    target = datetime.strptime(target_date, "%Y-%m-%d")
    week_a = datetime.strptime(week_a_start, "%Y-%m-%d")

    # Calculate days since Week A start
    days_diff = (target - week_a).days

    if days_diff < 0:
        raise ValueError(
            f"Target date {target_date} is before Week A start date {week_a_start}"
        )

    # Calculate total weeks since Week A
    total_weeks = days_diff // 7

    # Calculate cycle number (1-indexed)
    cycle_number = (total_weeks // weeks_per_cycle) + 1

    # Calculate week within cycle (0-indexed)
    week_number = total_weeks % weeks_per_cycle

    # Map to week letter
    week_letter = WEEK_LETTERS[week_number]

    # Calculate week boundaries
    week_offset_days = total_weeks * 7
    week_start = week_a + timedelta(days=week_offset_days)
    week_end = week_start + timedelta(days=6)

    # Calculate cycle boundaries
    cycle_week_offset = (cycle_number - 1) * weeks_per_cycle * 7
    cycle_start = week_a + timedelta(days=cycle_week_offset)
    cycle_end = cycle_start + timedelta(days=(weeks_per_cycle * 7) - 1)

    return {
        'cycle_number': cycle_number,
        'week_letter': week_letter,
        'week_number': week_number,
        'week_start': week_start.strftime("%Y-%m-%d"),
        'week_end': week_end.strftime("%Y-%m-%d"),
        'cycle_start': cycle_start.strftime("%Y-%m-%d"),
        'cycle_end': cycle_end.strftime("%Y-%m-%d")
    }


def get_cycle_start_date(
    cycle_number: int,
    week_a_start: str,
    weeks_per_cycle: int
) -> str:
    """
    Get the start date of a specific cycle.

    Args:
        cycle_number: Cycle number (1-indexed)
        week_a_start: Initial Week A start date (YYYY-MM-DD)
        weeks_per_cycle: Number of weeks per cycle

    Returns:
        Cycle start date in ISO format (YYYY-MM-DD)

    Examples:
        >>> get_cycle_start_date(1, "2025-01-13", 4)
        "2025-01-13"
        >>> get_cycle_start_date(2, "2025-01-13", 4)
        "2025-02-10"
    """
    validate_shift_config(week_a_start, weeks_per_cycle)

    if cycle_number < 1:
        raise ValueError(f"cycle_number must be >= 1, got {cycle_number}")

    week_a = datetime.strptime(week_a_start, "%Y-%m-%d")
    cycle_offset_days = (cycle_number - 1) * weeks_per_cycle * 7
    cycle_start = week_a + timedelta(days=cycle_offset_days)

    return cycle_start.strftime("%Y-%m-%d")


def get_cycle_date_range(
    n_cycles: int,
    week_a_start: str,
    weeks_per_cycle: int,
    end_date: Optional[str] = None
) -> Tuple[str, str]:
    """
    Calculate the date range for the last N cycles.

    Args:
        n_cycles: Number of cycles to look back
        week_a_start: Initial Week A start date (YYYY-MM-DD)
        weeks_per_cycle: Number of weeks per cycle
        end_date: End date (defaults to today)

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> # If today is 2025-11-24 (Cycle 12)
        >>> get_cycle_date_range(13, "2025-01-13", 4)
        ('2025-01-13', '2025-11-24')
    """
    validate_shift_config(week_a_start, weeks_per_cycle)

    if n_cycles < 1:
        raise ValueError(f"n_cycles must be >= 1, got {n_cycles}")

    # Default end_date to today
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Calculate what cycle we're currently in
    current_cycle_info = calculate_cycle_info(end_date, week_a_start, weeks_per_cycle)
    current_cycle_number = current_cycle_info['cycle_number']

    # Calculate start cycle number (n cycles back)
    start_cycle_number = max(1, current_cycle_number - n_cycles + 1)

    # Get start date of the start cycle
    start_date = get_cycle_start_date(start_cycle_number, week_a_start, weeks_per_cycle)

    logger.info(
        f"Calculated {n_cycles}-cycle range: {start_date} to {end_date} "
        f"(Cycles {start_cycle_number} to {current_cycle_number})"
    )

    return (start_date, end_date)
