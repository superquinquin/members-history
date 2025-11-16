from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from typing import Dict, Optional, Any, Tuple
from odoo_client import OdooClient
from utils import extract_id, extract_name, is_valid_many2one, validate_positive_int

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

odoo = OdooClient()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/odoo/test-connection", methods=["GET"])
def test_odoo_connection():
    try:
        authenticated = odoo.authenticate()
        if authenticated:
            return jsonify(
                {
                    "status": "connected",
                    "odoo_url": odoo.url,
                    "odoo_db": odoo.db,
                    "authenticated": True,
                    "uid": odoo.uid,
                }
            )
        else:
            return jsonify(
                {
                    "status": "failed",
                    "error": "Authentication failed",
                    "authenticated": False,
                }
            ), 500
    except Exception as e:
        logger.error(f"Error testing Odoo connection: {e}", exc_info=True)
        return jsonify(
            {"status": "failed", "error": str(e), "authenticated": False}
        ), 500


@app.route("/api/members/search", methods=["GET"])
def search_members():
    name = request.args.get("name", "")
    if not name:
        return jsonify({"error": "Name parameter is required"}), 400

    # Validate name length
    if len(name) > 100:
        return jsonify({"error": "Name parameter too long (max 100 characters)"}), 400

    try:
        members = odoo.search_members_by_name(name)
        logger.info(f"Processing {len(members)} members for search query: {name}")
        result = []
        for member in members:
            logger.debug(f"Member data: {member}")
            address_parts = [
                member.get("street"),
                member.get("street2"),
                member.get("zip"),
                member.get("city"),
            ]
            address = ", ".join(filter(None, address_parts))

            image = (
                member.get("image_small")
                or member.get("image_medium")
                or member.get("image")
            )
            result.append(
                {
                    "id": member.get("id"),
                    "name": member.get("name"),
                    "address": address if address else None,
                    "phone": member.get("phone") or member.get("mobile") or None,
                    "image": image if image else None,
                    "raw": member,
                }
            )

        return jsonify({"members": result})
    except Exception as e:
        logger.error(f"Error searching members: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/member/<int:member_id>/status", methods=["GET"])
def get_member_status(member_id):
    """
    Get member status information.

    Returns cooperative_state, shift_type, and other status fields
    that indicate the member's current standing in the cooperative.
    """
    # Validate member_id
    try:
        member_id = validate_positive_int(member_id, "member_id")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        status = odoo.get_member_status(member_id)

        if not status:
            return jsonify({"error": "Member not found"}), 404

        return jsonify(
            {
                "member_id": member_id,
                "name": status.get("name"),
                "cooperative_state": status.get("cooperative_state"),
                "is_worker_member": status.get("is_worker_member", False),
                "shift_type": status.get("shift_type"),
                "is_unsubscribed": status.get("is_unsubscribed", False),
                "customer": status.get("customer", False),
            }
        )
    except Exception as e:
        logger.error(f"Error fetching member status for member {member_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def determine_shift_type(
    shift: Dict, shift_counter_map: Dict, shift_id: Optional[int]
) -> Tuple[str, Any]:
    """
    Determine shift type using hybrid approach.

    Primary source: shift_type_id field (what kind of shift it actually is)
    Fallback: counter event type (only if shift_type_id missing)

    Args:
        shift: Shift data from Odoo
        shift_counter_map: Map of shift_id → counter data
        shift_id: The shift ID to check

    Returns:
        tuple: (shift_type, shift_type_id)
            shift_type: 'ftop' | 'standard' | 'unknown'
            shift_type_id: Raw Odoo field for debugging
    """
    # Primary: Use shift's shift_type_id field
    shift_type_id = shift.get("shift_type_id")
    if shift_type_id:
        if isinstance(shift_type_id, list) and len(shift_type_id) > 1:
            # shift_type_id is [id, name] - check name
            type_name = shift_type_id[1].lower()
            if "ftop" in type_name or "volant" in type_name:
                return ("ftop", shift_type_id)
            else:
                return ("standard", shift_type_id)
        # If just ID, default to standard
        return ("standard", shift_type_id)

    # Fallback: Use counter event type (if shift_type_id missing)
    if shift_id and shift_id in shift_counter_map:
        counter_type = shift_counter_map[shift_id].get("type", "standard")
        logger.warning(f"Using counter type as fallback for shift {shift_id}")
        return (counter_type, None)

    # Last resort: Unknown
    logger.warning(f"Cannot determine shift type for shift {shift.get('id')}")
    return ("unknown", None)


@app.route("/api/member/<int:member_id>/history", methods=["GET"])
def get_member_history(member_id):
    # Validate member_id
    try:
        member_id = validate_positive_int(member_id, "member_id")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        purchases = odoo.get_member_purchase_history(member_id)
        shifts = odoo.get_member_shift_history(member_id)
        leaves = odoo.get_member_leaves(member_id)
        counter_events = []
        holidays = []

        try:
            counter_events = odoo.get_member_counter_events(member_id)
        except Exception as counter_error:
            logger.warning(
                f"Error fetching counter events for member {member_id} (continuing without): {counter_error}",
                exc_info=True
            )

        try:
            # Fetch holidays for context (helps explain penalty variations)
            holidays = odoo.get_holidays()
        except Exception as holiday_error:
            logger.warning(f"Error fetching holidays (continuing without): {holiday_error}", exc_info=True)

        # Sort counter events chronologically (oldest first) for proper aggregation
        # Handle missing create_date gracefully
        counter_events_sorted = sorted(
            counter_events, key=lambda x: x.get("create_date") or "1900-01-01"
        )

        # Step 1: Aggregate counter events by shift_id AND counter type
        # Members have two separate counters: ftop and standard (ABCD)
        ftop_shift_map = {}
        standard_shift_map = {}
        ftop_manual_events = []
        standard_manual_events = []

        for counter_event in counter_events_sorted:
            shift_id = extract_id(counter_event.get("shift_id"))
            counter_type = counter_event.get("type", "standard")

            if shift_id:

                # Choose the right map based on counter type
                shift_map = (
                    ftop_shift_map if counter_type == "ftop" else standard_shift_map
                )

                counter_data = {
                    "point_qty": counter_event.get("point_qty", 0),
                    "create_date": counter_event.get("create_date", ""),
                    "type": counter_type,
                }

                if shift_id in shift_map:
                    shift_map[shift_id]["point_qty"] += counter_data["point_qty"]
                    # Keep the latest create_date for this shift's aggregated events
                    if counter_data["create_date"] > shift_map[shift_id]["create_date"]:
                        shift_map[shift_id]["create_date"] = counter_data["create_date"]
                else:
                    shift_map[shift_id] = counter_data
            else:
                # Manual counter event with no shift_id
                event_data = {
                    "type": "manual",
                    "create_date": counter_event.get("create_date", ""),
                    "point_qty": counter_event.get("point_qty", 0),
                    "counter_type": counter_type,
                    "original_event": counter_event,
                }

                if counter_type == "ftop":
                    ftop_manual_events.append(event_data)
                else:
                    standard_manual_events.append(event_data)

        # Step 2: Merge all counter items and calculate running totals for both counter types
        # Each event needs to know BOTH counter totals at that point in time
        all_counter_items = []

        # Add FTOP items
        for shift_id, data in ftop_shift_map.items():
            all_counter_items.append(
                {
                    "type": "shift",
                    "counter_type": "ftop",
                    "shift_id": shift_id,
                    "create_date": data["create_date"],
                    "point_qty": data["point_qty"],
                }
            )
        for manual_event in ftop_manual_events:
            all_counter_items.append(
                {
                    "type": "manual",
                    "counter_type": "ftop",
                    "create_date": manual_event["create_date"],
                    "point_qty": manual_event["point_qty"],
                    "original_event": manual_event["original_event"],
                }
            )

        # Add Standard items
        for shift_id, data in standard_shift_map.items():
            all_counter_items.append(
                {
                    "type": "shift",
                    "counter_type": "standard",
                    "shift_id": shift_id,
                    "create_date": data["create_date"],
                    "point_qty": data["point_qty"],
                }
            )
        for manual_event in standard_manual_events:
            all_counter_items.append(
                {
                    "type": "manual",
                    "counter_type": "standard",
                    "create_date": manual_event["create_date"],
                    "point_qty": manual_event["point_qty"],
                    "original_event": manual_event["original_event"],
                }
            )

        # Sort all items chronologically
        all_counter_items.sort(key=lambda x: x["create_date"])

        # Calculate running totals for both counters as we go through chronologically
        ftop_running_total = 0
        standard_running_total = 0

        for item in all_counter_items:
            # Update the appropriate counter
            if item["counter_type"] == "ftop":
                ftop_running_total += item["point_qty"]
            else:
                standard_running_total += item["point_qty"]

            # Store both running totals at this point in time
            item["ftop_total"] = int(ftop_running_total)
            item["standard_total"] = int(standard_running_total)
            # For backward compatibility, sum_current_qty is the active counter's total
            item["sum_current_qty"] = (
                int(ftop_running_total)
                if item["counter_type"] == "ftop"
                else int(standard_running_total)
            )

        # Step 3: Map totals back to shift maps and manual events
        for item in all_counter_items:
            if item["type"] == "shift":
                if item["counter_type"] == "ftop":
                    ftop_shift_map[item["shift_id"]]["ftop_total"] = item["ftop_total"]
                    ftop_shift_map[item["shift_id"]]["standard_total"] = item[
                        "standard_total"
                    ]
                    ftop_shift_map[item["shift_id"]]["sum_current_qty"] = item[
                        "sum_current_qty"
                    ]
                else:
                    standard_shift_map[item["shift_id"]]["standard_total"] = item[
                        "standard_total"
                    ]
                    standard_shift_map[item["shift_id"]]["ftop_total"] = item[
                        "ftop_total"
                    ]
                    standard_shift_map[item["shift_id"]]["sum_current_qty"] = item[
                        "sum_current_qty"
                    ]
            elif item["type"] == "manual":
                item["original_event"]["ftop_total"] = item["ftop_total"]
                item["original_event"]["standard_total"] = item["standard_total"]
                item["original_event"]["sum_current_qty"] = item["sum_current_qty"]

        # Step 4: Combine the maps into a single shift_counter_map
        shift_counter_map = {}
        for shift_id, data in ftop_shift_map.items():
            shift_counter_map[shift_id] = data
        for shift_id, data in standard_shift_map.items():
            if shift_id in shift_counter_map:
                # Shouldn't happen (a shift should only have one counter type), but handle it
                logger.warning(
                    f"Shift {shift_id} has both ftop and standard counter events - merging data"
                )
                # Merge point quantities instead of overwriting
                shift_counter_map[shift_id]["point_qty"] += data.get("point_qty", 0)
                # Keep the later create_date
                if data.get("create_date", "") > shift_counter_map[shift_id].get("create_date", ""):
                    shift_counter_map[shift_id]["create_date"] = data["create_date"]
            else:
                shift_counter_map[shift_id] = data

        events = []

        if purchases:
            for purchase in purchases:
                events.append(
                    {
                        "type": "purchase",
                        "id": purchase.get("id"),
                        "date": purchase.get("date_order"),
                        "reference": purchase.get("pos_reference")
                        or purchase.get("name"),
                    }
                )

        if shifts:
            for shift in shifts:
                shift_id = extract_id(shift.get("shift_id"))

                # Determine shift type
                shift_type, shift_type_id = determine_shift_type(
                    shift, shift_counter_map, shift_id
                )

                # Determine the date to use for this shift
                event_date = shift.get("date_begin")

                # For technical FTOP shifts (cycle closing), use counter event date (when shift was closed)
                # Check shift_type_id to distinguish technical FTOP from Standard shifts attended by FTOP members
                is_technical_ftop = False
                if shift_type_id and isinstance(shift_type_id, list) and len(shift_type_id) > 1:
                    type_name = shift_type_id[1].lower()
                    is_technical_ftop = "ftop" in type_name or "volant" in type_name

                if is_technical_ftop and shift_id and shift_id in shift_counter_map:
                    counter_date = shift_counter_map[shift_id].get("create_date")
                    if counter_date:
                        event_date = counter_date

                shift_event = {
                    "type": "shift",
                    "id": shift.get("id"),
                    "date": event_date,
                    "shift_name": shift.get("shift_name"),
                    "state": shift.get("state"),
                    "is_late": shift.get("is_late", False),
                    "is_exchanged": shift.get("is_exchanged", False),
                    "is_exchange": shift.get("is_exchange", False),
                    "week_number": shift.get("week_number"),
                    "week_name": shift.get("week_name"),
                    "shift_type": shift_type,
                    "shift_type_id": shift_type_id,
                }

                if shift_id and shift_id in shift_counter_map:
                    shift_event["counter"] = shift_counter_map[shift_id]

                events.append(shift_event)

        if counter_events:
            for counter_event in counter_events:
                shift_id = extract_id(counter_event.get("shift_id"))

                is_manual = counter_event.get("is_manual", False)
                if is_manual or not shift_id:
                    events.append(
                        {
                            "type": "counter",
                            "id": counter_event.get("id"),
                            "date": counter_event.get("create_date"),
                            "point_qty": counter_event.get("point_qty", 0),
                            "sum_current_qty": counter_event.get("sum_current_qty", 0),
                            "ftop_total": counter_event.get("ftop_total", 0),
                            "standard_total": counter_event.get("standard_total", 0),
                            "name": counter_event.get("name", ""),
                            "counter_type": counter_event.get("type", ""),
                        }
                    )

        # Generate leave timeline events (start and end markers)
        # Per spec Section 5.4: two events per leave
        leave_periods = []
        if leaves:
            for leave in leaves:
                leave_id = leave.get("id")
                leave_type = leave.get("leave_type", "Leave")
                start_date = leave.get("start_date")
                stop_date = leave.get("stop_date")

                # Create leave_start event
                if start_date:
                    events.append(
                        {
                            "type": "leave_start",
                            "id": leave_id,
                            "date": start_date,
                            "leave_type": leave_type,
                            "leave_end": stop_date,  # Reference to end date
                            "leave_id": leave_id,
                        }
                    )

                # Create leave_end event (if not open-ended)
                if stop_date:
                    events.append(
                        {
                            "type": "leave_end",
                            "id": leave_id,
                            "date": stop_date,
                            "leave_type": leave_type,
                            "leave_start": start_date,  # Reference to start date
                            "leave_id": leave_id,
                        }
                    )

                # Keep raw leave periods for backward compatibility
                leave_periods.append(
                    {
                        "id": leave_id,
                        "start_date": start_date,
                        "stop_date": stop_date,
                        "leave_type": leave_type,
                        "state": leave.get("state"),
                    }
                )

        # Sort all events chronologically (most recent first)
        events.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)

        return jsonify(
            {
                "member_id": member_id,
                "events": events,
                "leaves": leave_periods,
                "holidays": holidays,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching member history for member {member_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=True, port=port)
