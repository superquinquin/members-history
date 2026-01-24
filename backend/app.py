from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from typing import Dict, Optional, Any, Tuple
from odoo_client import OdooClient
from utils import (
    extract_id,
    validate_positive_int,
    get_last_n_cycles_date_range,
    strip_barcode_prefix,
)

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
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


@app.route("/api/config/cycles", methods=["GET"])
def get_cycle_config():
    """
    Get shift cycle configuration from Odoo.

    Returns the shift_weeks_per_cycle and shift_week_a_date configuration
    that the frontend can use to calculate cycles dynamically.

    NOTE: The week_a_date is adjusted to be one cycle earlier than the Odoo config
    to shift cycle numbering (current Cycle 12 becomes Cycle 13).

    Returns:
        JSON object with:
        - weeks_per_cycle (int): Number of weeks per cycle
        - week_a_date (str): Start date of initial Week A (YYYY-MM-DD) - adjusted
    """
    try:
        config = odoo.get_shift_config()

        # Adjust week_a_date to be one cycle earlier
        from datetime import datetime, timedelta

        weeks_per_cycle = config["weeks_per_cycle"]
        original_week_a = datetime.strptime(config["week_a_date"], "%Y-%m-%d")
        adjusted_week_a = (original_week_a - timedelta(weeks=weeks_per_cycle)).strftime(
            "%Y-%m-%d"
        )

        adjusted_config = {
            "weeks_per_cycle": weeks_per_cycle,
            "week_a_date": adjusted_week_a,
        }

        return jsonify(adjusted_config)
    except Exception as e:
        logger.error(f"Error fetching shift config: {e}", exc_info=True)
        # Return default configuration as fallback (also adjusted)
        return jsonify(
            {
                "weeks_per_cycle": 4,
                "week_a_date": "2024-12-16",  # One cycle before 2025-01-13
                "error": "Using default configuration due to error",
                "error_details": str(e),
            }
        ), 200  # Still return 200 with defaults


def merge_pair_profiles(members, pair_info_list, pair_profiles):
    """
    Merge profiles that belong to the same pair into single results.

    - Groups profiles by pair identity (main_member_id for associated members)
    - Creates merged name with both members (e.g., "DOE & DUPONT")
    - Deduplicates so each pair appears only once
    - Non-pairs pass through unchanged

    Args:
        members: List of member dicts from search
        pair_info_list: List of pair_info dicts (parallel to members)
        pair_profiles: Dict of other_profile data (from odoo.get_pair_profiles)

    Returns:
        List of tuples (member, pair_info) - deduplicated with merged names
    """
    # Group by pair identity
    pairs_seen = {}  # Maps pair_identity -> (member_index, pair_info, member_data)
    results = []

    for i, (member, pair_info) in enumerate(zip(members, pair_info_list)):
        # Get pair identity - use main_member_id if associated, else own id
        if pair_info.get("is_pair"):
            pair_identity = pair_info.get("main_member_id")
        else:
            pair_identity = member.get("id")

        # If we haven't seen this pair, add it
        if pair_identity not in pairs_seen:
            pairs_seen[pair_identity] = (i, pair_info, member)
            results.append((i, pair_info, member))

    return results


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

        # Detect pairs for all members
        pair_info_list = []
        for member in members:
            try:
                pair_info = odoo.detect_pair_relationship(member)
                pair_info_list.append(pair_info)
            except Exception as e:
                logger.warning(f"Pair detection failed for member {member.get('id')}: {e}")
                pair_info_list.append({"is_pair": False})

        # Batch fetch other profiles for pairs
        pair_profiles = odoo.get_pair_profiles(pair_info_list)

        # Merge paired profiles to deduplicate results
        merged_results = merge_pair_profiles(members, pair_info_list, pair_profiles)
        logger.info(f"After merging pairs: {len(members)} members -> {len(merged_results)} results")

        # Build results with pair info
        result = []
        for i, pair_info, member in merged_results:
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

            # Build merged name if this is a pair
            name = member.get("name")
            if pair_info.get("is_pair"):
                main_name = pair_info.get("main_member_name", "")
                pair_type = pair_info.get("pair_type")

                # Determine which name to use for the associated member
                if pair_type == "main":
                    # Viewing main member: other_profile is classical profile
                    other_profile_id = pair_info.get("other_profile_id")
                    if other_profile_id and other_profile_id in pair_profiles:
                        associated_name = pair_profiles[other_profile_id].get("name", "")
                    else:
                        associated_name = ""
                else:
                    # Viewing associated member (classical or shopping): use current member's name
                    associated_name = member.get("name")

                if main_name and associated_name:
                    # Strip barcode prefix from both names before merging
                    main_name = strip_barcode_prefix(main_name)
                    associated_name = strip_barcode_prefix(associated_name)
                    name = f"{main_name} & {associated_name}"

            result_item = {
                "id": member.get("id"),
                "name": name,
                "barcode_base": member.get("barcode_base"),
                "address": address if address else None,
                "phone": member.get("phone") or member.get("mobile") or None,
                "image": image if image else None,
                "raw": member,
                "pair_info": pair_info,
            }

            # Add other profile data if this is a pair
            if pair_info.get("is_pair"):
                other_profile_id = pair_info.get("other_profile_id")
                if other_profile_id and other_profile_id in pair_profiles:
                    result_item["other_profile"] = pair_profiles[other_profile_id]

            result.append(result_item)

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
        logger.error(
            f"Error fetching member status for member {member_id}: {e}", exc_info=True
        )
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
        # Detect pair relationship
        try:
            member_status = odoo.get_member_status(member_id)
            pair_info = odoo.detect_pair_relationship(member_status)
        except Exception as e:
            logger.warning(f"Pair detection failed: {e}")
            pair_info = {"is_pair": False}

        # Build profile ID lists for different data types
        # For pairs, data is stored differently:
        # - Shifts: Only on master member profile
        # - Counter events: Only on master member profile
        # - Purchases: Master classical + Associated shopping profiles
        # - Leaves: Both classical profiles (master + associated classical)

        # Determine master member profile ID
        if pair_info.get("is_pair"):
            master_profile_id = pair_info["main_member_id"]
            classical_profile_id = pair_info["classical_profile_id"]
            shopping_profile_id = pair_info["shopping_profile_id"]
        else:
            master_profile_id = member_id
            classical_profile_id = None
            shopping_profile_id = None

        # Shifts and counters: Only master member
        shift_profile_ids = [master_profile_id]
        counter_profile_ids = [master_profile_id]

        # Purchases: Master classical + Associated shopping (if pair)
        if pair_info.get("is_pair"):
            purchase_profile_ids = [master_profile_id, shopping_profile_id]
        else:
            purchase_profile_ids = [member_id]

        # Leaves: Both classical profiles (if pair)
        if pair_info.get("is_pair"):
            leave_profile_ids = [master_profile_id, classical_profile_id]
        else:
            leave_profile_ids = [member_id]

        # Build profile_names dict for all relevant profiles (for display)
        all_profile_ids = set(shift_profile_ids + purchase_profile_ids + leave_profile_ids + counter_profile_ids)
        profile_names = {}
        profile_barcodes = {}
        for pid in all_profile_ids:
            status = odoo.get_member_status(pid)
            profile_names[pid] = status.get("name")
            profile_barcodes[pid] = status.get("barcode_base")

        logger.info(f"Fetching history - Shifts/Counters: {shift_profile_ids}, Purchases: {purchase_profile_ids}, Leaves: {leave_profile_ids}")

        # Fetch shift configuration from Odoo
        shift_config = odoo.get_shift_config()

        # Adjust week_a_date to be one cycle earlier so Cycle 1 starts earlier
        # This shifts all cycle numbering by +1 (current Cycle 12 becomes Cycle 13)
        from datetime import datetime, timedelta

        weeks_per_cycle = shift_config["weeks_per_cycle"]
        original_week_a = datetime.strptime(shift_config["week_a_date"], "%Y-%m-%d")
        adjusted_week_a = (original_week_a - timedelta(weeks=weeks_per_cycle)).strftime(
            "%Y-%m-%d"
        )

        # Create adjusted config with earlier week_a_date
        adjusted_config = {
            "weeks_per_cycle": shift_config["weeks_per_cycle"],
            "week_a_date": adjusted_week_a,
        }

        # Calculate date range for last 13 cycles using adjusted config
        start_date, end_date = get_last_n_cycles_date_range(
            n=13, shift_config=adjusted_config
        )

        logger.info(
            f"Fetching member {member_id} history from {start_date} to {end_date} (Cycle 1 starts {adjusted_week_a})"
        )

        # Store adjusted config for use in event processing
        shift_config = adjusted_config

        # Fetch history using appropriate profile IDs for each data type
        all_purchases = []
        all_shifts = []
        all_leaves = []
        all_counter_events = []
        holidays = []

        # Fetch purchases (master classical + associated shopping for pairs)
        for profile_id in purchase_profile_ids:
            logger.info(f"Fetching purchases for profile {profile_id} ({profile_names.get(profile_id)})")
            try:
                purchases = odoo.get_member_purchase_history(profile_id, start_date=start_date)
                for p in purchases:
                    p["_profile_id"] = profile_id
                all_purchases.extend(purchases)
            except Exception as e:
                logger.warning(f"Error fetching purchases for profile {profile_id}: {e}")

        # Fetch shifts (only master member for pairs)
        for profile_id in shift_profile_ids:
            logger.info(f"Fetching shifts for profile {profile_id} ({profile_names.get(profile_id)})")
            try:
                shifts = odoo.get_member_shift_history(profile_id, start_date=start_date)
                for s in shifts:
                    s["_profile_id"] = profile_id
                all_shifts.extend(shifts)
            except Exception as e:
                logger.warning(f"Error fetching shifts for profile {profile_id}: {e}")

        # Fetch leaves (both classical profiles for pairs)
        for profile_id in leave_profile_ids:
            logger.info(f"Fetching leaves for profile {profile_id} ({profile_names.get(profile_id)})")
            try:
                leaves = odoo.get_member_leaves(profile_id, start_date=start_date)
                for l in leaves:
                    l["_profile_id"] = profile_id
                all_leaves.extend(leaves)
            except Exception as e:
                logger.warning(f"Error fetching leaves for profile {profile_id}: {e}")

        # Fetch counter events (only master member for pairs)
        for profile_id in counter_profile_ids:
            logger.info(f"Fetching counter events for profile {profile_id} ({profile_names.get(profile_id)})")
            try:
                # Fetch ALL counter events (no date filter) for accurate running totals
                counter_events = odoo.get_member_counter_events(profile_id)
                for c in counter_events:
                    c["_profile_id"] = profile_id
                all_counter_events.extend(counter_events)
            except Exception as counter_error:
                logger.warning(
                    f"Error fetching counter events for profile {profile_id} (continuing without): {counter_error}",
                    exc_info=True,
                )

        # Re-assign to original variable names for compatibility with existing code
        purchases = all_purchases
        shifts = all_shifts
        leaves = all_leaves
        counter_events = all_counter_events

        try:
            # Fetch holidays for the date range (only once)
            holidays = odoo.get_holidays(start_date=start_date, end_date=end_date)
        except Exception as holiday_error:
            logger.warning(
                f"Error fetching holidays (continuing without): {holiday_error}",
                exc_info=True,
            )

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
                if data.get("create_date", "") > shift_counter_map[shift_id].get(
                    "create_date", ""
                ):
                    shift_counter_map[shift_id]["create_date"] = data["create_date"]
            else:
                shift_counter_map[shift_id] = data

        events = []

        # Collect all exchange-related registration IDs that need to be fetched
        exchange_reg_ids = set()
        if shifts:
            for shift in shifts:
                # Try new exchange fields first
                replacing_id = extract_id(shift.get("exchange_replacing_reg_id"))
                replaced_id = extract_id(shift.get("exchange_replaced_reg_id"))

                # Fall back to legacy field if new fields are empty
                legacy_replaced_id = extract_id(shift.get("replaced_reg_id"))

                if replacing_id:
                    exchange_reg_ids.add(replacing_id)
                if replaced_id:
                    exchange_reg_ids.add(replaced_id)
                if legacy_replaced_id and not replaced_id:
                    exchange_reg_ids.add(legacy_replaced_id)

        # Batch fetch all exchange-related registrations
        logger.info(f"Exchange reg IDs to fetch: {exchange_reg_ids}")
        exchange_registrations = {}
        if exchange_reg_ids:
            try:
                # Fetch specific fields for all registrations
                reg_data = odoo.execute(
                    "shift.registration",
                    "read",
                    list(exchange_reg_ids),
                    fields=[
                        "id",
                        "date_begin",
                        "date_end",
                        "shift_id",
                        "partner_id",
                        "state",
                    ],
                )

                # Also fetch shift details for these registrations
                exchange_shift_ids = [
                    extract_id(r.get("shift_id")) for r in reg_data if r.get("shift_id")
                ]
                exchange_shift_ids = [
                    sid for sid in exchange_shift_ids if sid is not None
                ]

                exchange_shift_data = {}
                if exchange_shift_ids:
                    shift_results = odoo.execute(
                        "shift.shift",
                        "read",
                        exchange_shift_ids,
                        fields=["id", "name", "date_begin", "week_number", "week_name"],
                    )
                    exchange_shift_data = {s["id"]: s for s in shift_results}

                # Map registration data with shift info
                for reg in reg_data:
                    shift_id = extract_id(reg.get("shift_id"))
                    if shift_id and shift_id in exchange_shift_data:
                        reg["shift_name"] = exchange_shift_data[shift_id]["name"]
                        reg["shift_date"] = exchange_shift_data[shift_id]["date_begin"]
                        reg["week_number"] = exchange_shift_data[shift_id].get(
                            "week_number"
                        )
                        reg["week_name"] = exchange_shift_data[shift_id].get(
                            "week_name"
                        )
                    exchange_registrations[reg["id"]] = reg
            except Exception as e:
                logger.warning(f"Failed to fetch exchange registration details: {e}")

        if purchases:
            for purchase in purchases:
                events.append(
                    {
                        "type": "purchase",
                        "id": purchase.get("id"),
                        "date": purchase.get("date_order"),
                        "reference": purchase.get("pos_reference")
                        or purchase.get("name"),
                        "_profile_id": purchase.get("_profile_id"),
                    }
                )

        if shifts:
            for shift in shifts:
                # Debug: log exchange fields for waiting/replaced shifts
                if shift.get("state") in ["waiting", "replaced"]:
                    logger.info(
                        f"Shift {shift.get('id')} state={shift.get('state')}: "
                        f"replaced_reg_id={shift.get('replaced_reg_id')}, "
                        f"exchange_replacing_reg_id={shift.get('exchange_replacing_reg_id')}, "
                        f"exchange_replaced_reg_id={shift.get('exchange_replaced_reg_id')}"
                    )

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
                if (
                    shift_type_id
                    and isinstance(shift_type_id, list)
                    and len(shift_type_id) > 1
                ):
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
                    # Don't set is_exchanged/is_exchange yet - will set later if exchange_details exists
                    "week_number": shift.get("week_number"),
                    "week_name": shift.get("week_name"),
                    "shift_type": shift_type,
                    "shift_type_id": shift_type_id,
                    "_profile_id": shift.get("_profile_id"),
                }

                if shift_id and shift_id in shift_counter_map:
                    shift_event["counter"] = shift_counter_map[shift_id]

                # Add exchange details if this shift is part of an exchange
                exchange_details = {}

                # exchange_replacing_reg_id = The registration that REPLACED this shift
                # (i.e., the new shift that the member chose to replace this one)
                replacement_reg_id = extract_id(shift.get("exchange_replacing_reg_id"))
                if not replacement_reg_id:
                    # Fall back to legacy field
                    replacement_reg_id = extract_id(shift.get("replaced_reg_id"))

                if replacement_reg_id and replacement_reg_id in exchange_registrations:
                    replacement_reg = exchange_registrations[replacement_reg_id]
                    exchange_details["replacement_shift"] = {
                        "date": replacement_reg.get("shift_date")
                        or replacement_reg.get("date_begin"),
                        "shift_name": replacement_reg.get("shift_name"),
                        "week_number": replacement_reg.get("week_number"),
                        "week_name": replacement_reg.get("week_name"),
                    }

                # exchange_replaced_reg_id = The original registration that THIS shift is replacing
                # (i.e., this is a replacement shift covering the original)
                original_reg_id = extract_id(shift.get("exchange_replaced_reg_id"))
                if original_reg_id and original_reg_id in exchange_registrations:
                    original_reg = exchange_registrations[original_reg_id]
                    exchange_details["original_shift"] = {
                        "date": original_reg.get("shift_date")
                        or original_reg.get("date_begin"),
                        "shift_name": original_reg.get("shift_name"),
                        "week_number": original_reg.get("week_number"),
                        "week_name": original_reg.get("week_name"),
                    }

                # Add counter impact explanation
                if shift.get("is_exchange") and shift.get("state") == "done":
                    exchange_details["counter_impact"] = (
                        "no_penalty_attended_replacement"
                    )
                elif (
                    shift.get("is_exchanged")
                    and replacement_reg_id
                    and replacement_reg_id in exchange_registrations
                ):
                    replacement_reg = exchange_registrations[replacement_reg_id]
                    # Check if replacement was attended (would need to check the registration state)
                    exchange_details["counter_impact"] = "exchanged_for_replacement"

                # Add exchange state ONLY if we have actual exchange relationship data or counter impact
                # This prevents showing exchange details for "waiting" shifts that are just during leave
                if (
                    "replacement_shift" in exchange_details
                    or "original_shift" in exchange_details
                    or "counter_impact" in exchange_details
                ):
                    exchange_state = shift.get("exchange_state")
                    if exchange_state:
                        exchange_details["exchange_state"] = exchange_state
                    # Fallback: infer exchange state from flags if not explicitly set
                    elif shift.get("is_exchanged"):
                        exchange_details["exchange_state"] = "replaced"
                    elif shift.get("is_exchange"):
                        exchange_details["exchange_state"] = "replacing"

                # Only add exchange_details if we have meaningful exchange information
                # Don't show exchange details for "waiting" shifts that are just during leave
                if exchange_details:
                    shift_event["exchange_details"] = exchange_details
                    # Only set these flags when we have actual exchange data
                    shift_event["is_exchanged"] = bool(shift.get("is_exchanged"))
                    shift_event["is_exchange"] = bool(shift.get("is_exchange"))
                else:
                    # No exchange details, so definitely not an exchange
                    shift_event["is_exchanged"] = False
                    shift_event["is_exchange"] = False

                # Debug logging for waiting/replaced shifts
                if shift.get("state") in ["waiting", "replaced"]:
                    logger.info(
                        f"Shift {shift.get('id')} ({shift.get('shift_name')}) state={shift.get('state')}: "
                        f"is_exchanged={shift.get('is_exchanged')}, "
                        f"exchange_state={shift.get('exchange_state')}, "
                        f"has_exchange_details={bool(exchange_details)}, "
                        f"exchange_details_keys={list(exchange_details.keys()) if exchange_details else []}, "
                        f"sent_is_exchanged={shift_event.get('is_exchanged')}"
                    )

                events.append(shift_event)

        if counter_events:
            for counter_event in counter_events:
                shift_id = extract_id(counter_event.get("shift_id"))

                is_manual = counter_event.get("is_manual", False)
                if is_manual or not shift_id:
                    # Filter counter events for display - only include events within date range
                    event_date = counter_event.get("create_date", "")
                    if event_date and event_date >= start_date:
                        events.append(
                            {
                                "type": "counter",
                                "id": counter_event.get("id"),
                                "date": event_date,
                                "point_qty": counter_event.get("point_qty", 0),
                                "sum_current_qty": counter_event.get(
                                    "sum_current_qty", 0
                                ),
                                "ftop_total": counter_event.get("ftop_total", 0),
                                "standard_total": counter_event.get(
                                    "standard_total", 0
                                ),
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
                            "_profile_id": leave.get("_profile_id"),
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
                            "_profile_id": leave.get("_profile_id"),
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

        # Get the final counter totals (after all events have been processed)
        final_ftop_total = ftop_running_total
        final_standard_total = standard_running_total

        return jsonify(
            {
                "member_id": member_id,
                "events": events,
                "leaves": leave_periods,
                "holidays": holidays,
                "counter_totals": {
                    "ftop": int(final_ftop_total),
                    "standard": int(final_standard_total),
                },
                "pair_info": pair_info,
                "profiles": {
                    pid: {"id": pid, "name": profile_names[pid], "barcode_base": profile_barcodes[pid]}
                    for pid in all_profile_ids
                },
            }
        )
    except Exception as e:
        logger.error(
            f"Error fetching member history for member {member_id}: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/member/<int:member_id>/shares", methods=["GET"])
def get_member_shares(member_id):
    """
    Get member share information including join date and total shares.

    Returns:
        JSON with share data for frontend display:
        - total_shares: Current total shares owned
        - join_date: Date of first share purchase (YYYY-MM-DD)
        - first_purchase_date: Same as join_date
        - share_purchases: List of share purchase events
    """
    # Validate member_id
    try:
        member_id = validate_positive_int(member_id, "member_id")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        # Fetch share information from Odoo
        share_data = odoo.get_member_share_information(member_id)

        # Format the response for frontend
        response = {
            "member_id": member_id,
            "total_shares": share_data.get("total_shares", 0),
            "join_date": share_data.get("join_date"),
            "first_purchase_date": share_data.get("first_purchase_date"),
            "share_purchases": share_data.get("share_purchases", []),
        }

        logger.info(f"Successfully fetched share data for member {member_id}")
        return jsonify(response)

    except Exception as e:
        logger.error(
            f"Error fetching share data for member {member_id}: {e}", exc_info=True
        )
        return jsonify(
            {
                "error": str(e),
                "member_id": member_id,
                "total_shares": 0,
                "join_date": None,
                "first_purchase_date": None,
                "share_purchases": [],
            }
        ), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the React frontend for all non-API routes"""
    # If requesting a static file (has extension), try to serve it
    if path and '.' in path:
        static_file_path = os.path.join(app.static_folder, path)
        if os.path.exists(static_file_path):
            return app.send_static_file(path)
    # Otherwise serve index.html (SPA routing)
    return app.send_static_file('index.html')


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
