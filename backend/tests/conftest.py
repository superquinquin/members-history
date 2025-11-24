"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
from app import app as flask_app
from odoo_client import OdooClient


@pytest.fixture
def app():
    """Create and configure a test Flask app instance."""
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def mock_odoo_client(mocker):
    """Create a mock OdooClient for testing."""
    mock = mocker.MagicMock(spec=OdooClient)
    mock.uid = 1
    mock.authenticate.return_value = True
    # Default empty holidays for tests that don't explicitly mock it
    mock.get_holidays.return_value = []
    # Default shift config
    mock.get_shift_config.return_value = {
        "weeks_per_cycle": 4,
        "week_a_date": "2025-01-13"
    }
    return mock


@pytest.fixture
def mock_shift_config():
    """Mock shift configuration from Odoo."""
    return {
        "weeks_per_cycle": 4,
        "week_a_date": "2025-01-13"
    }


@pytest.fixture
def sample_shift_with_ftop_counter():
    """Sample shift registration with FTOP counter event."""
    return {
        'id': 101,
        'date_begin': '2025-01-15 09:00:00',
        'state': 'done',
        'shift_id': [201, 'FTOP Wednesday 09:00'],
        'is_late': False,
        'shift_name': 'FTOP Wednesday 09:00',
        'week_number': 1,
        'week_name': 'A',
        'shift_type_id': [1, 'FTOP']
    }


@pytest.fixture
def sample_shift_with_standard_counter():
    """Sample shift registration with standard ABCD counter event."""
    return {
        'id': 102,
        'date_begin': '2025-01-20 14:00:00',
        'state': 'done',
        'shift_id': [202, 'Standard Monday 14:00'],
        'is_late': False,
        'shift_name': 'Standard Monday 14:00',
        'week_number': 2,
        'week_name': 'B',
        'shift_type_id': [2, 'Standard']
    }


@pytest.fixture
def sample_shift_without_shift_type_id():
    """Sample shift without shift_type_id (legacy data)."""
    return {
        'id': 103,
        'date_begin': '2025-01-25 09:00:00',
        'state': 'done',
        'shift_id': [203, 'Unknown Shift'],
        'is_late': False,
        'shift_name': 'Unknown Shift',
        'week_number': 3,
        'week_name': 'C'
        # No shift_type_id field
    }


@pytest.fixture
def sample_excused_shift():
    """Sample excused shift (no counter event expected)."""
    return {
        'id': 104,
        'date_begin': '2025-02-01 09:00:00',
        'state': 'excused',
        'shift_id': [204, 'FTOP Friday 09:00'],
        'is_late': False,
        'shift_name': 'FTOP Friday 09:00',
        'week_number': 4,
        'week_name': 'D',
        'shift_type_id': [1, 'FTOP']
    }


@pytest.fixture
def sample_ftop_counter_event():
    """Sample FTOP counter event."""
    return {
        'id': 301,
        'create_date': '2025-01-15 10:00:00',
        'point_qty': 1,
        'sum_current_qty': 5,
        'shift_id': [201, 'FTOP Wednesday 09:00'],
        'is_manual': False,
        'name': 'Shift attended',
        'type': 'ftop'
    }


@pytest.fixture
def sample_standard_counter_event():
    """Sample standard ABCD counter event."""
    return {
        'id': 302,
        'create_date': '2025-01-20 15:00:00',
        'point_qty': 1,
        'sum_current_qty': 3,
        'shift_id': [202, 'Standard Monday 14:00'],
        'is_manual': False,
        'name': 'Shift attended',
        'type': 'standard'
    }


@pytest.fixture
def sample_shift_with_volant_name():
    """Sample shift with 'volant' in shift_type_id name."""
    return {
        'id': 105,
        'date_begin': '2025-02-05 11:00:00',
        'state': 'done',
        'shift_id': [205, 'Service Volant Tuesday'],
        'is_late': False,
        'shift_name': 'Service Volant Tuesday',
        'week_number': 5,
        'week_name': 'A',
        'shift_type_id': [3, 'Service Volant']
    }
