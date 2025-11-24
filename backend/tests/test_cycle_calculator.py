"""
Tests for cycle_calculator module.

Tests the dynamic cycle calculation logic based on Odoo configuration.
"""

import pytest
from datetime import datetime, timedelta
from cycle_calculator import (
    calculate_cycle_info,
    get_cycle_start_date,
    get_cycle_date_range,
    validate_shift_config,
)


class TestValidateShiftConfig:
    """Tests for configuration validation."""

    def test_valid_config(self):
        """Test validation with valid configuration."""
        assert validate_shift_config("2025-01-13", 4) is True

    def test_invalid_date_format(self):
        """Test validation with invalid date format."""
        with pytest.raises(ValueError, match="Invalid week_a_date format"):
            validate_shift_config("invalid-date", 4)

    def test_weeks_per_cycle_too_low(self):
        """Test validation with weeks_per_cycle < 1."""
        with pytest.raises(ValueError, match="weeks_per_cycle must be between 1 and 12"):
            validate_shift_config("2025-01-13", 0)

    def test_weeks_per_cycle_too_high(self):
        """Test validation with weeks_per_cycle > 12."""
        with pytest.raises(ValueError, match="weeks_per_cycle must be between 1 and 12"):
            validate_shift_config("2025-01-13", 13)

    def test_non_monday_warning(self, caplog):
        """Test that non-Monday week_a_date logs a warning."""
        # 2025-01-14 is a Tuesday
        validate_shift_config("2025-01-14", 4)
        assert "not a Monday" in caplog.text


class TestCalculateCycleInfo:
    """Tests for calculate_cycle_info function."""

    def test_week_a_first_day(self):
        """Test calculation for first day of Week A."""
        result = calculate_cycle_info("2025-01-13", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "A"
        assert result["week_number"] == 0
        assert result["week_start"] == "2025-01-13"
        assert result["week_end"] == "2025-01-19"
        assert result["cycle_start"] == "2025-01-13"
        assert result["cycle_end"] == "2025-02-09"

    def test_week_a_last_day(self):
        """Test calculation for last day of Week A."""
        result = calculate_cycle_info("2025-01-19", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "A"
        assert result["week_start"] == "2025-01-13"
        assert result["week_end"] == "2025-01-19"

    def test_week_b(self):
        """Test calculation for Week B."""
        result = calculate_cycle_info("2025-01-20", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "B"
        assert result["week_number"] == 1
        assert result["week_start"] == "2025-01-20"
        assert result["week_end"] == "2025-01-26"

    def test_week_c(self):
        """Test calculation for Week C."""
        result = calculate_cycle_info("2025-01-27", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "C"
        assert result["week_number"] == 2
        assert result["week_start"] == "2025-01-27"
        assert result["week_end"] == "2025-02-02"

    def test_week_d(self):
        """Test calculation for Week D."""
        result = calculate_cycle_info("2025-02-03", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "D"
        assert result["week_number"] == 3
        assert result["week_start"] == "2025-02-03"
        assert result["week_end"] == "2025-02-09"

    def test_cycle_2_week_a(self):
        """Test calculation for Cycle 2, Week A."""
        result = calculate_cycle_info("2025-02-10", "2025-01-13", 4)
        assert result["cycle_number"] == 2
        assert result["week_letter"] == "A"
        assert result["week_number"] == 0
        assert result["week_start"] == "2025-02-10"
        assert result["week_end"] == "2025-02-16"
        assert result["cycle_start"] == "2025-02-10"
        assert result["cycle_end"] == "2025-03-09"

    def test_year_boundary(self):
        """Test calculation across year boundary."""
        # Assuming Week A starts 2025-01-13, calculate a date in 2026
        result = calculate_cycle_info("2026-01-05", "2025-01-13", 4)
        # Should be around cycle 13
        assert result["cycle_number"] == 13
        assert result["week_letter"] in ["A", "B", "C", "D"]

    def test_date_before_week_a(self):
        """Test that date before week_a_start raises error."""
        with pytest.raises(ValueError, match="before Week A start date"):
            calculate_cycle_info("2025-01-01", "2025-01-13", 4)

    def test_three_weeks_per_cycle(self):
        """Test calculation with 3 weeks per cycle."""
        result = calculate_cycle_info("2025-01-13", "2025-01-13", 3)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "A"

        result = calculate_cycle_info("2025-02-03", "2025-01-13", 3)
        assert result["cycle_number"] == 2
        assert result["week_letter"] == "A"


class TestGetCycleStartDate:
    """Tests for get_cycle_start_date function."""

    def test_cycle_1(self):
        """Test start date of Cycle 1."""
        result = get_cycle_start_date(1, "2025-01-13", 4)
        assert result == "2025-01-13"

    def test_cycle_2(self):
        """Test start date of Cycle 2."""
        result = get_cycle_start_date(2, "2025-01-13", 4)
        assert result == "2025-02-10"  # 4 weeks * 7 days = 28 days later

    def test_cycle_13(self):
        """Test start date of Cycle 13."""
        result = get_cycle_start_date(13, "2025-01-13", 4)
        # 12 cycles * 4 weeks * 7 days = 336 days
        expected = datetime(2025, 1, 13) + timedelta(days=336)
        assert result == expected.strftime("%Y-%m-%d")

    def test_invalid_cycle_number(self):
        """Test that cycle_number < 1 raises error."""
        with pytest.raises(ValueError, match="cycle_number must be >= 1"):
            get_cycle_start_date(0, "2025-01-13", 4)


class TestGetCycleDateRange:
    """Tests for get_cycle_date_range function."""

    def test_last_13_cycles_from_cycle_12(self):
        """Test getting last 13 cycles when currently in Cycle 12."""
        # If today is in Cycle 12, Week B (2025-11-24)
        result = get_cycle_date_range(13, "2025-01-13", 4, end_date="2025-11-24")
        assert result[0] == "2025-01-13"  # Start of Cycle 1
        assert result[1] == "2025-11-24"  # Today

    def test_last_5_cycles(self):
        """Test getting last 5 cycles."""
        # From Cycle 6 (2025-06-02)
        result = get_cycle_date_range(5, "2025-01-13", 4, end_date="2025-06-02")
        assert result[0] == "2025-02-10"  # Start of Cycle 2
        assert result[1] == "2025-06-02"

    def test_defaults_to_today(self):
        """Test that end_date defaults to today if not provided."""
        result = get_cycle_date_range(1, "2025-01-13", 4)
        # end_date should be today (can't assert exact date, but should be recent)
        end_date = datetime.strptime(result[1], "%Y-%m-%d")
        assert end_date >= datetime(2025, 1, 13)

        # start_date should be the start of the current cycle (1 cycle back from today)
        start_date = datetime.strptime(result[0], "%Y-%m-%d")
        # Start date should be before or equal to end date
        assert start_date <= end_date
        # Start date should be recent (within last year)
        assert start_date >= datetime(2024, 1, 1)

    def test_first_cycle_only(self):
        """Test getting just 1 cycle when in Cycle 1."""
        result = get_cycle_date_range(1, "2025-01-13", 4, end_date="2025-01-20")
        assert result[0] == "2025-01-13"  # Start of Cycle 1
        assert result[1] == "2025-01-20"

    def test_more_cycles_than_exist(self):
        """Test requesting more cycles than have occurred."""
        # If we're in Cycle 2 but request last 5 cycles
        result = get_cycle_date_range(5, "2025-01-13", 4, end_date="2025-02-15")
        # Should start from Cycle 1 (max(1, 2 - 5 + 1) = 1)
        assert result[0] == "2025-01-13"
        assert result[1] == "2025-02-15"

    def test_invalid_n_cycles(self):
        """Test that n_cycles < 1 raises error."""
        with pytest.raises(ValueError, match="n_cycles must be >= 1"):
            get_cycle_date_range(0, "2025-01-13", 4)


class TestCycleCalculatorMatchesJSON:
    """Tests to verify dynamic calculation matches existing 2025 JSON data."""

    def test_matches_known_cycle_1_week_a(self):
        """Verify Cycle 1, Week A matches JSON data."""
        # From cycles_2025.json: Cycle 1, Week A is 2025-01-13 to 2025-01-19
        result = calculate_cycle_info("2025-01-15", "2025-01-13", 4)
        assert result["cycle_number"] == 1
        assert result["week_letter"] == "A"
        assert result["week_start"] == "2025-01-13"
        assert result["week_end"] == "2025-01-19"

    def test_matches_known_cycle_2_week_b(self):
        """Verify Cycle 2, Week B matches JSON data."""
        # From cycles_2025.json: Cycle 2, Week B is 2025-02-17 to 2025-02-23
        result = calculate_cycle_info("2025-02-20", "2025-01-13", 4)
        assert result["cycle_number"] == 2
        assert result["week_letter"] == "B"
        assert result["week_start"] == "2025-02-17"
        assert result["week_end"] == "2025-02-23"

    def test_matches_known_cycle_12_week_d(self):
        """Verify Cycle 12, Week D matches JSON data."""
        # From cycles_2025.json: Cycle 12, Week D is 2025-12-08 to 2025-12-14
        result = calculate_cycle_info("2025-12-10", "2025-01-13", 4)
        assert result["cycle_number"] == 12
        assert result["week_letter"] == "D"
        assert result["week_start"] == "2025-12-08"
        assert result["week_end"] == "2025-12-14"

    def test_matches_known_cycle_13_week_c(self):
        """Verify Cycle 13, Week C (partial cycle into 2026)."""
        # From cycles_2025.json: Cycle 13, Week C is 2025-12-29 to 2026-01-04
        result = calculate_cycle_info("2026-01-01", "2025-01-13", 4)
        assert result["cycle_number"] == 13
        assert result["week_letter"] == "C"
        assert result["week_start"] == "2025-12-29"
        assert result["week_end"] == "2026-01-04"
