"""
Unit tests for determine_shift_type() helper function.

This module tests the shift type determination logic that identifies whether
a shift is FTOP (Service Volants) or Standard (ABCD) based on counter events
and shift_type_id field.
"""

import pytest


class TestDetermineShiftType:
    """Test suite for determine_shift_type() function."""

    def test_shift_with_ftop_counter_event(
        self, sample_shift_with_ftop_counter, sample_ftop_counter_event
    ):
        """
        Test shift type determination when counter event exists with type='ftop'.

        Expected: shift_type should be 'ftop'
        """
        from app import determine_shift_type

        shift = sample_shift_with_ftop_counter
        shift_id = shift["shift_id"][0]

        # Create counter map with FTOP counter
        shift_counter_map = {
            shift_id: {
                "point_qty": sample_ftop_counter_event["point_qty"],
                "create_date": sample_ftop_counter_event["create_date"],
                "type": "ftop",
                "ftop_total": 5,
                "standard_total": 0,
                "sum_current_qty": 5,
            }
        }

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "ftop", (
            "Shift with FTOP counter event should return 'ftop'"
        )

    def test_shift_with_standard_counter_event(
        self, sample_shift_with_standard_counter, sample_standard_counter_event
    ):
        """
        Test shift type determination when counter event exists with type='standard'.

        Expected: shift_type should be 'standard'
        """
        from app import determine_shift_type

        shift = sample_shift_with_standard_counter
        shift_id = shift["shift_id"][0]

        # Create counter map with standard counter
        shift_counter_map = {
            shift_id: {
                "point_qty": sample_standard_counter_event["point_qty"],
                "create_date": sample_standard_counter_event["create_date"],
                "type": "standard",
                "ftop_total": 0,
                "standard_total": 3,
                "sum_current_qty": 3,
            }
        }

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "standard", (
            "Shift with standard counter event should return 'standard'"
        )

    def test_shift_without_counter_with_ftop_shift_type_id(self, sample_excused_shift):
        """
        Test shift type determination when no counter exists but shift_type_id indicates FTOP.

        This happens with excused shifts that don't generate counter events.

        Expected: shift_type should be 'ftop'
        """
        from app import determine_shift_type

        shift = sample_excused_shift
        shift_id = shift["shift_id"][0]
        shift_counter_map = {}  # No counter event for excused shift

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "ftop", (
            "Excused FTOP shift should use shift_type_id to determine type"
        )

    def test_shift_without_counter_with_standard_shift_type_id(self):
        """
        Test shift type determination when no counter exists but shift_type_id indicates Standard.

        Expected: shift_type should be 'standard'
        """
        from app import determine_shift_type

        shift = {
            "id": 110,
            "shift_id": [210, "Standard Shift"],
            "shift_type_id": [2, "Standard"],
            "state": "excused",
        }
        shift_counter_map = {}
        shift_id = 210

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "standard", (
            "Excused standard shift should use shift_type_id"
        )

    def test_shift_with_volant_in_shift_type_name(self, sample_shift_with_volant_name):
        """
        Test shift type determination when shift_type_id name contains 'volant'.

        'Service Volant' is another name for FTOP shifts.

        Expected: shift_type should be 'ftop'
        """
        from app import determine_shift_type

        shift = sample_shift_with_volant_name
        shift_id = shift["shift_id"][0]
        shift_counter_map = {}

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "ftop", (
            "Shift with 'volant' in name should be identified as FTOP"
        )

    def test_shift_without_counter_and_without_shift_type_id(
        self, sample_shift_without_shift_type_id
    ):
        """
        Test shift type determination when neither counter nor shift_type_id exists.

        This can happen with legacy data or incomplete records.

        Expected: shift_type should be 'unknown'
        """
        from app import determine_shift_type

        shift = sample_shift_without_shift_type_id
        shift_id = shift["shift_id"][0]
        shift_counter_map = {}

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "unknown", (
            "Shift without counter or shift_type_id should return 'unknown'"
        )

    def test_shift_with_null_shift_type_id(self):
        """
        Test shift type determination when shift_type_id is False (Odoo's null value).

        Expected: shift_type should be 'unknown'
        """
        from app import determine_shift_type

        shift = {
            "id": 111,
            "shift_id": [211, "Shift"],
            "shift_type_id": False,  # Odoo returns False for null many2one fields
        }
        shift_counter_map = {}
        shift_id = 211

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "unknown", (
            "Shift with null shift_type_id should return 'unknown'"
        )

    def test_shift_type_case_insensitive_volant(self):
        """
        Test that 'volant' detection is case-insensitive.

        Expected: Both 'Volant' and 'VOLANT' should be recognized as FTOP
        """
        from app import determine_shift_type

        test_cases = [
            [4, "Volant"],
            [5, "VOLANT"],
            [6, "service volant"],
            [7, "SERVICE VOLANT"],
        ]

        for shift_type_id in test_cases:
            shift = {
                "id": 112,
                "shift_id": [212, "Test"],
                "shift_type_id": shift_type_id,
            }
            shift_counter_map = {}
            shift_id = 212

            shift_type, shift_type_id_result = determine_shift_type(
                shift, shift_counter_map, shift_id
            )

            assert shift_type == "ftop", (
                f"'{shift_type_id[1]}' should be recognized as FTOP"
            )

    def test_shift_type_id_takes_precedence_over_counter_event(self):
        """
        Test that shift_type_id takes precedence over counter event type.

        This is the correct behavior: shift_type_id tells us what kind of shift it actually is,
        while counter type just tells us which counter was affected (FTOP members have all
        counter events marked as type='ftop', even for standard ABCD shifts they attend).

        Expected: shift_type_id should be used
        """
        from app import determine_shift_type

        # Shift has shift_type_id='Standard' and counter type='ftop'
        # This is the real-world case: FTOP member attending a standard ABCD shift
        shift = {
            "id": 113,
            "shift_id": [213, "Test Shift"],
            "shift_type_id": [2, "Standard"],
        }
        shift_id = 213

        shift_counter_map = {213: {"type": "ftop", "point_qty": 1}}

        shift_type, shift_type_id = determine_shift_type(
            shift, shift_counter_map, shift_id
        )

        assert shift_type == "standard", (
            "shift_type_id should take precedence over counter event type"
        )

    def test_shift_id_as_integer(self):
        """
        Test that function handles shift_id as both list and integer.

        Expected: Both formats should work correctly
        """
        from app import determine_shift_type

        # shift_id as list (normal Odoo format)
        shift_list = {
            "id": 114,
            "shift_id": [214, "Test"],
            "shift_type_id": [1, "FTOP"],
        }

        # shift_id as integer (after extraction)
        shift_int = {"id": 115, "shift_id": 215, "shift_type_id": [1, "FTOP"]}

        shift_counter_map = {}

        type_list, _ = determine_shift_type(shift_list, shift_counter_map, 214)
        type_int, _ = determine_shift_type(shift_int, shift_counter_map, 215)

        assert type_list == "ftop", "Function should handle shift_id as list"
        assert type_int == "ftop", "Function should handle shift_id as integer"
