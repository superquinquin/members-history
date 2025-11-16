"""
Integration tests for /api/member/<id>/history endpoint with FTOP shifts.

Tests the complete flow of fetching member history including shift type
determination and proper data structure in API responses.
"""

import pytest
import json


class TestMemberHistoryAPI:
    """Test suite for member history API endpoint."""

    def test_ftop_member_with_mixed_shift_types(self, client, mock_odoo_client, mocker):
        """
        Test FTOP member with both FTOP and standard shifts in history.

        FTOP members can participate in both FTOP shifts (Service Volants)
        and standard ABCD shifts.

        Expected:
        - Response includes shift_type field for each shift
        - FTOP shifts have shift_type='ftop'
        - Standard shifts have shift_type='standard'
        """
        # Mock data: FTOP member with mixed shifts
        mock_shifts = [
            {
                "id": 1,
                "date_begin": "2025-01-15 09:00:00",
                "state": "done",
                "shift_id": [101, "FTOP Wed 09:00"],
                "shift_name": "FTOP Wed 09:00",
                "is_late": False,
                "week_number": 1,
                "week_name": "A",
                "shift_type_id": [1, "FTOP"],
            },
            {
                "id": 2,
                "date_begin": "2025-01-20 14:00:00",
                "state": "done",
                "shift_id": [102, "Standard Mon 14:00"],
                "shift_name": "Standard Mon 14:00",
                "is_late": False,
                "week_number": 2,
                "week_name": "B",
                "shift_type_id": [2, "Standard"],
            },
        ]

        mock_counter_events = [
            {
                "id": 201,
                "create_date": "2025-01-15 10:00:00",
                "point_qty": 1,
                "sum_current_qty": 5,
                "shift_id": [101, "FTOP Wed 09:00"],
                "is_manual": False,
                "name": "Shift attended",
                "type": "ftop",
            },
            {
                "id": 202,
                "create_date": "2025-01-20 15:00:00",
                "point_qty": 1,
                "sum_current_qty": 3,
                "shift_id": [102, "Standard Mon 14:00"],
                "is_manual": False,
                "name": "Shift attended",
                "type": "standard",
            },
        ]

        # Setup mocks
        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = mock_counter_events

        mocker.patch("app.odoo", mock_odoo_client)

        # Make request
        response = client.get("/api/member/123/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure
        assert "events" in data
        assert len(data["events"]) == 2

        # Find shift events
        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 2

        # Verify FTOP shift
        ftop_shift = next(e for e in shift_events if e["id"] == 1)
        assert "shift_type" in ftop_shift, "FTOP shift should have shift_type field"
        assert ftop_shift["shift_type"] == "ftop", (
            "FTOP shift should have shift_type='ftop'"
        )
        assert "shift_type_id" in ftop_shift, (
            "Should include shift_type_id for debugging"
        )

        # Verify standard shift
        standard_shift = next(e for e in shift_events if e["id"] == 2)
        assert "shift_type" in standard_shift, (
            "Standard shift should have shift_type field"
        )
        assert standard_shift["shift_type"] == "standard", (
            "Standard shift should have shift_type='standard'"
        )

    def test_standard_member_with_only_standard_shifts(
        self, client, mock_odoo_client, mocker
    ):
        """
        Test standard ABCD member with only standard shifts.

        Expected: All shifts should have shift_type='standard'
        """
        mock_shifts = [
            {
                "id": 3,
                "date_begin": "2025-01-10 09:00:00",
                "state": "done",
                "shift_id": [103, "Monday 09:00"],
                "shift_name": "Monday 09:00",
                "is_late": False,
                "week_number": 1,
                "week_name": "A",
                "shift_type_id": [2, "Standard"],
            }
        ]

        mock_counter_events = [
            {
                "id": 203,
                "create_date": "2025-01-10 10:00:00",
                "point_qty": 1,
                "sum_current_qty": 3,
                "shift_id": [103, "Monday 09:00"],
                "is_manual": False,
                "name": "Shift attended",
                "type": "standard",
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = mock_counter_events

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/124/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1
        assert shift_events[0]["shift_type"] == "standard"

    def test_excused_shift_without_counter_event(
        self, client, mock_odoo_client, mocker
    ):
        """
        Test excused shift that has no counter event.

        Excused shifts don't generate counter events, so shift_type must be
        determined from shift_type_id field.

        Expected: shift_type should be correctly determined from shift_type_id
        """
        mock_shifts = [
            {
                "id": 4,
                "date_begin": "2025-02-01 09:00:00",
                "state": "excused",
                "shift_id": [104, "FTOP Fri 09:00"],
                "shift_name": "FTOP Fri 09:00",
                "is_late": False,
                "week_number": 4,
                "week_name": "D",
                "shift_type_id": [1, "FTOP"],
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = []  # No counter events

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/125/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1
        assert shift_events[0]["shift_type"] == "ftop", (
            "Excused FTOP shift should have correct type"
        )
        assert "counter" not in shift_events[0], (
            "Excused shift should not have counter data"
        )

    def test_shift_with_missing_shift_type_id(self, client, mock_odoo_client, mocker):
        """
        Test shift with missing shift_type_id field (legacy data).

        Expected: shift_type should be 'unknown' and trigger warning
        """
        mock_shifts = [
            {
                "id": 5,
                "date_begin": "2025-01-25 09:00:00",
                "state": "done",
                "shift_id": [105, "Unknown Shift"],
                "shift_name": "Unknown Shift",
                "is_late": False,
                "week_number": 3,
                "week_name": "C",
                # No shift_type_id field
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = []

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/126/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1
        assert shift_events[0]["shift_type"] == "unknown", (
            "Missing shift_type_id should result in 'unknown'"
        )

    def test_counter_data_unchanged(self, client, mock_odoo_client, mocker):
        """
        Test that adding shift_type doesn't break existing counter functionality.

        Expected: Counter data (point_qty, totals) should remain correct
        """
        mock_shifts = [
            {
                "id": 6,
                "date_begin": "2025-01-15 09:00:00",
                "state": "done",
                "shift_id": [106, "FTOP Shift"],
                "shift_name": "FTOP Shift",
                "is_late": False,
                "week_number": 1,
                "week_name": "A",
                "shift_type_id": [1, "FTOP"],
            }
        ]

        mock_counter_events = [
            {
                "id": 204,
                "create_date": "2025-01-15 10:00:00",
                "point_qty": 1,
                "sum_current_qty": 5,
                "shift_id": [106, "FTOP Shift"],
                "is_manual": False,
                "name": "Shift attended",
                "type": "ftop",
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = mock_counter_events

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/127/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1

        shift = shift_events[0]
        assert "counter" in shift, "Counter data should still be present"
        assert shift["counter"]["point_qty"] == 1
        assert shift["counter"]["type"] == "ftop"
        assert "ftop_total" in shift["counter"]
        assert "standard_total" in shift["counter"]

    def test_future_shift_not_yet_closed(self, client, mock_odoo_client, mocker):
        """
        Test future shift that hasn't been closed yet (no counter event).

        Expected: shift_type determined from shift_type_id
        """
        mock_shifts = [
            {
                "id": 7,
                "date_begin": "2025-12-31 09:00:00",  # Future date
                "state": "done",  # But marked done for some reason
                "shift_id": [107, "FTOP Future"],
                "shift_name": "FTOP Future",
                "is_late": False,
                "week_number": 52,
                "week_name": "D",
                "shift_type_id": [1, "FTOP"],
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = []  # No counter yet

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/128/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1
        assert shift_events[0]["shift_type"] == "ftop"

    def test_type_mismatch_counter_vs_shift_type_id(
        self, client, mock_odoo_client, mocker
    ):
        """
        Test edge case where counter type doesn't match shift_type_id.

        This is the real-world case: FTOP members have ALL counter events marked as type='ftop',
        even when they attend standard ABCD shifts. The shift_type_id tells us what kind of
        shift it actually is.

        Expected: shift_type_id takes precedence (it's the source of truth for shift type)
        """
        mock_shifts = [
            {
                "id": 8,
                "date_begin": "2025-01-15 09:00:00",
                "state": "done",
                "shift_id": [108, "Mismatch Shift"],
                "shift_name": "Mismatch Shift",
                "is_late": False,
                "week_number": 1,
                "week_name": "A",
                "shift_type_id": [2, "Standard"],  # Says Standard
            }
        ]

        mock_counter_events = [
            {
                "id": 205,
                "create_date": "2025-01-15 10:00:00",
                "point_qty": 1,
                "sum_current_qty": 5,
                "shift_id": [108, "Mismatch Shift"],
                "is_manual": False,
                "name": "Shift attended",
                "type": "ftop",  # Counter is FTOP (member is FTOP)
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = mock_shifts
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = mock_counter_events

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/129/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        shift_events = [e for e in data["events"] if e["type"] == "shift"]
        assert len(shift_events) == 1
        assert shift_events[0]["shift_type"] == "standard", (
            "shift_type_id should take precedence"
        )

    def test_leave_timeline_events(self, client, mock_odoo_client, mocker):
        """
        Test that leave periods generate timeline start/end events.

        Per spec Section 5.4, each leave should create two timeline events:
        - leave_start with reference to end date
        - leave_end with reference to start date
        """
        mock_leaves = [
            {
                "id": 301,
                "start_date": "2025-07-01",
                "stop_date": "2025-07-14",
                "type_id": [1, "Vacation"],
                "leave_type": "Vacation",
                "state": "done",
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = []
        mock_odoo_client.get_member_leaves.return_value = mock_leaves
        mock_odoo_client.get_member_counter_events.return_value = []
        mock_odoo_client.get_holidays.return_value = []

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/130/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check for leave_start event
        leave_start_events = [e for e in data["events"] if e["type"] == "leave_start"]
        assert len(leave_start_events) == 1
        assert leave_start_events[0]["date"] == "2025-07-01"
        assert leave_start_events[0]["leave_type"] == "Vacation"
        assert leave_start_events[0]["leave_end"] == "2025-07-14"
        assert leave_start_events[0]["leave_id"] == 301

        # Check for leave_end event
        leave_end_events = [e for e in data["events"] if e["type"] == "leave_end"]
        assert len(leave_end_events) == 1
        assert leave_end_events[0]["date"] == "2025-07-14"
        assert leave_end_events[0]["leave_type"] == "Vacation"
        assert leave_end_events[0]["leave_start"] == "2025-07-01"
        assert leave_end_events[0]["leave_id"] == 301

        # Check that raw leave periods are still included for backward compatibility
        assert "leaves" in data
        assert len(data["leaves"]) == 1

    def test_open_ended_leave(self, client, mock_odoo_client, mocker):
        """
        Test open-ended leave (no stop_date).

        Should only create leave_start event, not leave_end.
        """
        mock_leaves = [
            {
                "id": 302,
                "start_date": "2025-08-01",
                "stop_date": False,  # Open-ended
                "type_id": [2, "Sick Leave"],
                "leave_type": "Sick Leave",
                "state": "done",
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = []
        mock_odoo_client.get_member_leaves.return_value = mock_leaves
        mock_odoo_client.get_member_counter_events.return_value = []
        mock_odoo_client.get_holidays.return_value = []

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/131/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have leave_start but no leave_end
        leave_start_events = [e for e in data["events"] if e["type"] == "leave_start"]
        assert len(leave_start_events) == 1
        assert leave_start_events[0]["leave_end"] is False

        leave_end_events = [e for e in data["events"] if e["type"] == "leave_end"]
        assert len(leave_end_events) == 0

    def test_holidays_included_in_response(self, client, mock_odoo_client, mocker):
        """
        Test that holidays are included in member history response.

        Holidays provide context for penalty variations.
        """
        mock_holidays = [
            {
                "id": 401,
                "name": "Christmas Period",
                "holiday_type": "long_period",
                "date_begin": "2025-12-20",
                "date_end": "2025-12-27",
                "state": "confirmed",
                "make_up_type": "0_make_up",  # Full relief
            }
        ]

        mock_odoo_client.get_member_purchase_history.return_value = []
        mock_odoo_client.get_member_shift_history.return_value = []
        mock_odoo_client.get_member_leaves.return_value = []
        mock_odoo_client.get_member_counter_events.return_value = []
        mock_odoo_client.get_holidays.return_value = mock_holidays

        mocker.patch("app.odoo", mock_odoo_client)

        response = client.get("/api/member/132/history")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Holidays should be included in response
        assert "holidays" in data
        assert len(data["holidays"]) == 1
        assert data["holidays"][0]["name"] == "Christmas Period"
        assert data["holidays"][0]["make_up_type"] == "0_make_up"
