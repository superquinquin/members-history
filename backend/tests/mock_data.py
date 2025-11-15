"""
Mock data for testing FTOP shift timeline feature.

This module provides realistic sample data representing different scenarios
with FTOP and standard shifts.
"""

# Sample FTOP member with mixed shift types
FTOP_MEMBER_MIXED_SHIFTS = {
    'shifts': [
        {
            'id': 1,
            'date_begin': '2025-01-15 09:00:00',
            'state': 'done',
            'shift_id': [101, 'FTOP Wednesday 09:00'],
            'shift_name': 'FTOP Wednesday 09:00',
            'is_late': False,
            'week_number': 1,
            'week_name': 'A',
            'shift_type_id': [1, 'FTOP']
        },
        {
            'id': 2,
            'date_begin': '2025-01-20 14:00:00',
            'state': 'done',
            'shift_id': [102, 'Standard Monday 14:00'],
            'shift_name': 'Standard Monday 14:00',
            'is_late': False,
            'week_number': 2,
            'week_name': 'B',
            'shift_type_id': [2, 'Standard']
        },
        {
            'id': 3,
            'date_begin': '2025-01-25 11:00:00',
            'state': 'absent',
            'shift_id': [103, 'FTOP Friday 11:00'],
            'shift_name': 'FTOP Friday 11:00',
            'is_late': False,
            'week_number': 3,
            'week_name': 'C',
            'shift_type_id': [1, 'FTOP']
        }
    ],
    'counter_events': [
        {
            'id': 201,
            'create_date': '2025-01-15 10:00:00',
            'point_qty': 1,
            'sum_current_qty': 5,
            'shift_id': [101, 'FTOP Wednesday 09:00'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'ftop'
        },
        {
            'id': 202,
            'create_date': '2025-01-20 15:00:00',
            'point_qty': 1,
            'sum_current_qty': 3,
            'shift_id': [102, 'Standard Monday 14:00'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'standard'
        },
        {
            'id': 203,
            'create_date': '2025-01-25 12:00:00',
            'point_qty': -1,
            'sum_current_qty': 4,
            'shift_id': [103, 'FTOP Friday 11:00'],
            'is_manual': False,
            'name': 'Shift missed',
            'type': 'ftop'
        }
    ]
}

# Standard ABCD member (no FTOP shifts)
STANDARD_MEMBER = {
    'shifts': [
        {
            'id': 10,
            'date_begin': '2025-01-10 09:00:00',
            'state': 'done',
            'shift_id': [110, 'Monday 09:00'],
            'shift_name': 'Monday 09:00',
            'is_late': False,
            'week_number': 1,
            'week_name': 'A',
            'shift_type_id': [2, 'Standard']
        },
        {
            'id': 11,
            'date_begin': '2025-01-17 09:00:00',
            'state': 'done',
            'shift_id': [111, 'Monday 09:00'],
            'shift_name': 'Monday 09:00',
            'is_late': False,
            'week_number': 2,
            'week_name': 'B',
            'shift_type_id': [2, 'Standard']
        }
    ],
    'counter_events': [
        {
            'id': 210,
            'create_date': '2025-01-10 10:00:00',
            'point_qty': 1,
            'sum_current_qty': 1,
            'shift_id': [110, 'Monday 09:00'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'standard'
        },
        {
            'id': 211,
            'create_date': '2025-01-17 10:00:00',
            'point_qty': 1,
            'sum_current_qty': 2,
            'shift_id': [111, 'Monday 09:00'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'standard'
        }
    ]
}

# Excused shift without counter event
EXCUSED_SHIFT_NO_COUNTER = {
    'shifts': [
        {
            'id': 20,
            'date_begin': '2025-02-01 09:00:00',
            'state': 'excused',
            'shift_id': [120, 'FTOP Friday 09:00'],
            'shift_name': 'FTOP Friday 09:00',
            'is_late': False,
            'week_number': 4,
            'week_name': 'D',
            'shift_type_id': [1, 'FTOP']
        }
    ],
    'counter_events': []
}

# Legacy shift without shift_type_id
LEGACY_SHIFT_NO_TYPE_ID = {
    'shifts': [
        {
            'id': 30,
            'date_begin': '2024-12-15 09:00:00',
            'state': 'done',
            'shift_id': [130, 'Old Shift Format'],
            'shift_name': 'Old Shift Format',
            'is_late': False,
            'week_number': 50,
            'week_name': 'B'
            # No shift_type_id field
        }
    ],
    'counter_events': []
}

# Shift with 'Service Volant' name
SERVICE_VOLANT_SHIFT = {
    'shifts': [
        {
            'id': 40,
            'date_begin': '2025-02-05 11:00:00',
            'state': 'done',
            'shift_id': [140, 'Service Volant Tuesday'],
            'shift_name': 'Service Volant Tuesday',
            'is_late': False,
            'week_number': 5,
            'week_name': 'A',
            'shift_type_id': [3, 'Service Volant']
        }
    ],
    'counter_events': [
        {
            'id': 240,
            'create_date': '2025-02-05 12:00:00',
            'point_qty': 1,
            'sum_current_qty': 6,
            'shift_id': [140, 'Service Volant Tuesday'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'ftop'
        }
    ]
}

# Type mismatch scenario
TYPE_MISMATCH = {
    'shifts': [
        {
            'id': 50,
            'date_begin': '2025-01-15 09:00:00',
            'state': 'done',
            'shift_id': [150, 'Mismatch Shift'],
            'shift_name': 'Mismatch Shift',
            'is_late': False,
            'week_number': 1,
            'week_name': 'A',
            'shift_type_id': [2, 'Standard']  # Says Standard
        }
    ],
    'counter_events': [
        {
            'id': 250,
            'create_date': '2025-01-15 10:00:00',
            'point_qty': 1,
            'sum_current_qty': 5,
            'shift_id': [150, 'Mismatch Shift'],
            'is_manual': False,
            'name': 'Shift attended',
            'type': 'ftop'  # But counter says FTOP
        }
    ]
}

# Expected API response structure for FTOP member with mixed shifts
EXPECTED_FTOP_MEMBER_RESPONSE = {
    'member_id': 123,
    'events': [
        {
            'type': 'shift',
            'id': 3,
            'date': '2025-01-25 11:00:00',
            'shift_name': 'FTOP Friday 11:00',
            'state': 'absent',
            'is_late': False,
            'week_number': 3,
            'week_name': 'C',
            'shift_type': 'ftop',
            'shift_type_id': [1, 'FTOP'],
            'counter': {
                'point_qty': -1,
                'create_date': '2025-01-25 12:00:00',
                'type': 'ftop',
                'ftop_total': 4,
                'standard_total': 3,
                'sum_current_qty': 4
            }
        },
        {
            'type': 'shift',
            'id': 2,
            'date': '2025-01-20 14:00:00',
            'shift_name': 'Standard Monday 14:00',
            'state': 'done',
            'is_late': False,
            'week_number': 2,
            'week_name': 'B',
            'shift_type': 'standard',
            'shift_type_id': [2, 'Standard'],
            'counter': {
                'point_qty': 1,
                'create_date': '2025-01-20 15:00:00',
                'type': 'standard',
                'ftop_total': 5,
                'standard_total': 3,
                'sum_current_qty': 3
            }
        },
        {
            'type': 'shift',
            'id': 1,
            'date': '2025-01-15 09:00:00',
            'shift_name': 'FTOP Wednesday 09:00',
            'state': 'done',
            'is_late': False,
            'week_number': 1,
            'week_name': 'A',
            'shift_type': 'ftop',
            'shift_type_id': [1, 'FTOP'],
            'counter': {
                'point_qty': 1,
                'create_date': '2025-01-15 10:00:00',
                'type': 'ftop',
                'ftop_total': 5,
                'standard_total': 2,
                'sum_current_qty': 5
            }
        }
    ],
    'leaves': []
}
