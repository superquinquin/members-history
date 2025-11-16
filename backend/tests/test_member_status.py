"""
Tests for member status endpoint.

Tests the /api/member/<id>/status endpoint that returns
member's cooperative_state and related status fields.
"""

import pytest
from unittest.mock import Mock, patch
from app import app


class TestMemberStatusAPI:
    """Test cases for member status endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @patch("app.odoo")
    def test_get_member_status_success(self, mock_odoo, client):
        """Test successful retrieval of member status."""
        # Mock Odoo response
        mock_odoo.get_member_status.return_value = {
            "id": 123,
            "name": "TEST, Member",
            "cooperative_state": "up_to_date",
            "is_worker_member": True,
            "shift_type": "standard",
            "is_unsubscribed": False,
            "customer": True,
        }

        response = client.get("/api/member/123/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["member_id"] == 123
        assert data["name"] == "TEST, Member"
        assert data["cooperative_state"] == "up_to_date"
        assert data["is_worker_member"] is True
        assert data["shift_type"] == "standard"
        assert data["is_unsubscribed"] is False
        assert data["customer"] is True

    @patch("app.odoo")
    def test_get_member_status_ftop_member(self, mock_odoo, client):
        """Test status for FTOP member."""
        mock_odoo.get_member_status.return_value = {
            "id": 456,
            "name": "FTOP, Member",
            "cooperative_state": "up_to_date",
            "is_worker_member": True,
            "shift_type": "ftop",
            "is_unsubscribed": False,
            "customer": True,
        }

        response = client.get("/api/member/456/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["shift_type"] == "ftop"

    @patch("app.odoo")
    def test_get_member_status_alert_state(self, mock_odoo, client):
        """Test member in alert state (behind on shifts)."""
        mock_odoo.get_member_status.return_value = {
            "id": 789,
            "name": "ALERT, Member",
            "cooperative_state": "alert",
            "is_worker_member": True,
            "shift_type": "standard",
            "is_unsubscribed": False,
            "customer": True,  # Still has shopping privileges in alert
        }

        response = client.get("/api/member/789/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["cooperative_state"] == "alert"
        assert data["customer"] is True

    @patch("app.odoo")
    def test_get_member_status_suspended(self, mock_odoo, client):
        """Test member in suspended state (shopping blocked)."""
        mock_odoo.get_member_status.return_value = {
            "id": 999,
            "name": "SUSPENDED, Member",
            "cooperative_state": "suspended",
            "is_worker_member": True,
            "shift_type": "standard",
            "is_unsubscribed": False,
            "customer": False,  # No shopping privileges
        }

        response = client.get("/api/member/999/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["cooperative_state"] == "suspended"
        assert data["customer"] is False

    @patch("app.odoo")
    def test_get_member_status_not_found(self, mock_odoo, client):
        """Test member not found."""
        mock_odoo.get_member_status.return_value = {}

        response = client.get("/api/member/99999/status")
        assert response.status_code == 404

        data = response.get_json()
        assert "error" in data

    @patch("app.odoo")
    def test_get_member_status_odoo_error(self, mock_odoo, client):
        """Test handling of Odoo errors."""
        mock_odoo.get_member_status.side_effect = Exception("Odoo connection failed")

        response = client.get("/api/member/123/status")
        assert response.status_code == 500

        data = response.get_json()
        assert "error" in data

    @patch("app.odoo")
    def test_get_member_status_unsubscribed(self, mock_odoo, client):
        """Test unsubscribed member status."""
        mock_odoo.get_member_status.return_value = {
            "id": 111,
            "name": "UNSUBSCRIBED, Member",
            "cooperative_state": "unsubscribed",
            "is_worker_member": True,
            "shift_type": False,  # No shift type when unsubscribed
            "is_unsubscribed": True,
            "customer": False,
        }

        response = client.get("/api/member/111/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["cooperative_state"] == "unsubscribed"
        assert data["is_unsubscribed"] is True
