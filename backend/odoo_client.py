import xmlrpc.client
import os
import logging
from typing import Optional, Dict, List, Any, cast
from utils import extract_id, extract_name

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Configure logging
logger = logging.getLogger(__name__)


class OdooClient:
    def __init__(self):
        raw_url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USERNAME")
        self.password = os.getenv("ODOO_PASSWORD")
        self.uid: Optional[int] = None
        self.common: Optional[Any] = None
        self.models: Optional[Any] = None

        # Extract URL without credentials for XML-RPC
        if raw_url and "@" in raw_url:
            # Remove credentials from URL for XML-RPC endpoints
            # Example: https://user:pass@domain.com -> https://domain.com
            parts = raw_url.split("@")
            if len(parts) >= 2:
                self.url = parts[1]
                if not self.url.startswith("http"):
                    self.url = "https://" + self.url
            else:
                self.url = raw_url
        else:
            self.url = raw_url

    def authenticate(self) -> bool:
        try:
            # Ensure URL has proper protocol
            if self.url and not self.url.startswith("http"):
                self.url = "https://" + self.url

            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

            self.uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )
            return self.uid is not None

        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return False

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, list(args), kwargs
        )

    def search_read(self, model: str, domain: List, fields: List[str]) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            "search_read",
            [domain],
            {"fields": fields},
        )

    def search_members_by_name(self, name: str) -> List[Dict]:
        domain = [("name", "ilike", name)]
        fields = [
            "id",
            "name",
            "street",
            "street2",
            "city",
            "zip",
            "phone",
            "mobile",
            "email",
            "image",
            "image_small",
            "image_medium",
        ]
        results = self.search_read("res.partner", domain, fields)
        logger.info(f"Search members by name '{name}': found {len(results)} results")
        return results

    def get_member_status(self, partner_id: int) -> Dict:
        """
        Get member status and state information.

        Fetches cooperative_state, shift_type, and related fields
        that indicate member's current standing and participation type.

        Args:
            partner_id: Member ID

        Returns:
            Dictionary with status fields
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        fields = [
            "id",
            "name",
            "cooperative_state",
            "is_worker_member",
            "shift_type",
            "is_unsubscribed",
            "customer",
        ]

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "res.partner",
            "read",
            [[partner_id]],
            {"fields": fields},
        )

        if results:
            logger.info(f"Member status for partner {partner_id}: {results[0].get('cooperative_state')}")
            return results[0]

        logger.warning(f"Member {partner_id} not found")
        return {}

    def get_member_purchase_history(
        self, partner_id: int, limit: Optional[int] = None, start_date: Optional[str] = None
    ) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        domain = [("partner_id", "=", partner_id), ("state", "=", "done")]

        # Add date filter if start_date is provided
        if start_date:
            domain.append(("date_order", ">=", start_date))

        fields = ["id", "date_order", "name", "pos_reference"]

        query_options = {"fields": fields, "order": "date_order desc"}
        if limit:
            query_options["limit"] = limit

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "pos.order",
            "search_read",
            [domain],
            query_options,
        )

        logger.info(f"Purchase history for partner {partner_id}: {len(results)} orders")
        return results

    def get_member_shift_history(
        self, partner_id: int, limit: Optional[int] = None, start_date: Optional[str] = None
    ) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        domain = [
            ("partner_id", "=", partner_id),
            ("state", "in", ["done", "absent", "excused", "open", "waiting", "replaced"]),
        ]

        # Add date filter if start_date is provided
        if start_date:
            domain.append(("date_begin", ">=", start_date))

        fields = [
            "id",
            "date_begin",
            "date_end",
            "state",
            "shift_id",
            "is_late",
            "is_exchanged",
            "is_exchange",
            "exchange_state",
            "exchange_replacing_reg_id",
            "exchange_replaced_reg_id",
            "replaced_reg_id",  # Legacy field - might still contain data
        ]

        query_options = {"fields": fields, "order": "date_begin desc"}
        if limit:
            query_options["limit"] = limit

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "shift.registration",
            "search_read",
            [domain],
            query_options,
        )

        shift_ids = [
            extract_id(r.get("shift_id"))
            for r in results
            if r.get("shift_id")
        ]
        # Filter out None values
        shift_ids = [sid for sid in shift_ids if sid is not None]

        shifts = {}
        if shift_ids:
            shift_fields = [
                "id",
                "name",
                "date_begin",
                "week_number",
                "week_name",
                "shift_type_id",
            ]
            shift_results = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "shift.shift",
                "read",
                [shift_ids],
                {"fields": shift_fields},
            )
            shifts = {s["id"]: s for s in shift_results}

        for registration in results:
            shift_id = extract_id(registration.get("shift_id"))
            if shift_id and shift_id in shifts:
                registration["shift_name"] = shifts[shift_id]["name"]
                registration["week_number"] = shifts[shift_id].get("week_number")
                registration["week_name"] = shifts[shift_id].get("week_name")
                registration["shift_type_id"] = shifts[shift_id].get("shift_type_id")
            else:
                registration["shift_name"] = None
                registration["week_number"] = None
                registration["week_name"] = None
                registration["shift_type_id"] = None

        logger.info(f"Shift history for partner {partner_id}: {len(results)} registrations")
        return results

    def get_member_leaves(self, partner_id: int, start_date: Optional[str] = None) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        domain = [("partner_id", "=", partner_id), ("state", "=", "done")]

        # Add date filter if start_date is provided
        # Include leaves that were active during or after the start_date
        if start_date:
            domain.append(("stop_date", ">=", start_date))

        fields = ["id", "start_date", "stop_date", "type_id", "state"]

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "shift.leave",
            "search_read",
            [domain],
            {"fields": fields, "order": "start_date desc"},
        )

        for leave in results:
            leave["leave_type"] = extract_name(leave.get("type_id")) or "Leave"

        logger.info(f"Leave history for partner {partner_id}: {len(results)} leaves")
        return results

    def get_member_counter_events(self, partner_id: int, limit: int = 50) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        domain = [("partner_id", "=", partner_id)]
        fields = [
            "id",
            "create_date",
            "point_qty",
            "sum_current_qty",
            "shift_id",
            "is_manual",
            "name",
            "type",
        ]

        # Fetch ALL counter events (no limit) to calculate running totals correctly
        # The limit parameter is ignored here - we need all historical events for accurate totals
        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "shift.counter.event",
            "search_read",
            [domain],
            {"fields": fields, "order": "create_date desc"},
        )

        logger.info(f"Counter events for partner {partner_id}: {len(results)} events")
        return results

    def get_holidays(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get holiday periods (shift.holiday - "Assouplissement de présence").

        These holidays provide penalty relief for missed shifts.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of holiday records with relief information
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        # Fetch active/confirmed holidays
        domain = [("state", "in", ["confirmed", "done"])]

        # Add date filters if provided
        if start_date:
            domain.append(("date_end", ">=", start_date))
        if end_date:
            domain.append(("date_begin", "<=", end_date))

        fields = [
            "id",
            "name",
            "holiday_type",
            "date_begin",
            "date_end",
            "state",
            "make_up_type",
        ]

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "shift.holiday",
            "search_read",
            [domain],
            {"fields": fields, "order": "date_begin desc"},
        )

        logger.info(f"Found {len(results)} holidays")
        return results

    def get_holiday_for_date(self, date: str) -> Optional[Dict]:
        """
        Check if a specific date falls within a holiday period.

        Args:
            date: Date to check (ISO format YYYY-MM-DD)

        Returns:
            Holiday record if date is within a holiday, None otherwise
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        domain = [
            ("state", "in", ["confirmed", "done"]),
            ("date_begin", "<=", date),
            ("date_end", ">=", date),
        ]

        fields = [
            "id",
            "name",
            "holiday_type",
            "date_begin",
            "date_end",
            "make_up_type",
        ]

        results = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "shift.holiday",
            "search_read",
            [domain],
            {"fields": fields, "limit": 1},
        )

        if results:
            return results[0]
        return None

    def get_worker_members_addresses(self) -> List[Dict]:
        """Fetch addresses of worker members only (no personal data)"""
        domain = [
            ("is_worker_member", "=", True),
            ("cooperative_state", "!=", "unsubscribed"),
        ]
        fields = ["id", "street", "street2", "zip", "city"]
        results = self.search_read("res.partner", domain, fields)
        logger.info(f"Found {len(results)} worker members with addresses")
        return results

    def get_shift_config(self) -> Dict[str, any]:
        """
        Get shift cycle configuration from Odoo.

        Fetches shift_weeks_per_cycle and shift_week_a_date from res.config.settings.
        These values define the cycle calculation parameters.

        Returns:
            Dictionary with:
            - weeks_per_cycle (int): Number of weeks per cycle (typically 4)
            - week_a_date (str): Start date of initial Week A (YYYY-MM-DD)

        Raises:
            Exception: If authentication fails or models proxy not initialized
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        # res.config.settings is typically a singleton
        # Get the most recent configuration record
        domain = []
        fields = ["shift_weeks_per_cycle", "shift_week_a_date"]

        try:
            results = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "res.config.settings",
                "search_read",
                [domain],
                {"fields": fields, "limit": 1, "order": "id desc"},
            )

            if results and len(results) > 0:
                config = results[0]
                logger.info(
                    f"Fetched shift config from Odoo: "
                    f"weeks_per_cycle={config.get('shift_weeks_per_cycle')}, "
                    f"week_a_date={config.get('shift_week_a_date')}"
                )
                return {
                    "weeks_per_cycle": config.get("shift_weeks_per_cycle"),
                    "week_a_date": config.get("shift_week_a_date"),
                }
        except Exception as e:
            logger.warning(
                f"Failed to fetch shift config from Odoo: {e}. Using defaults."
            )

        # Fallback to hardcoded defaults if config not found or error
        logger.warning("Using default shift configuration (4 weeks, starting 2025-01-13)")
        return {
            "weeks_per_cycle": 4,
            "week_a_date": "2025-01-13",
        }
