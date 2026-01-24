import xmlrpc.client
import os
import logging
from typing import Optional, Dict, List, Any
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
            "barcode_base",
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
            "parent_id",
            "child_ids",
            "nb_associated_people",
            "category_id",  # Changed from category_ids to category_id (singular)
            "is_unsubscribed",
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
            "barcode_base",
            "cooperative_state",
            "is_worker_member",
            "shift_type",
            "is_unsubscribed",
            "customer",
            "parent_id",
            "child_ids",
            "nb_associated_people",
            "category_id",  # Changed from category_ids to category_id (singular)
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

    def get_member_share_information(self, partner_id: int) -> Dict:
        """
        Get member share information including first purchase date and total shares.

        Fetches the member's total shares owned and the date of their first share purchase
        by examining share ownership records and related subscription invoices.

        Args:
            partner_id: Member ID

        Returns:
            Dictionary with:
            - total_shares: Current total shares owned (int)
            - first_purchase_date: Date of first share purchase (YYYY-MM-DD string, or None)
            - share_purchases: List of share purchase events with details
            - join_date: Alias for first_purchase_date (for UI consistency)

        Raises:
            Exception: If authentication fails or models proxy not initialized
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")

        if self.models is None:
            raise Exception("Models proxy not initialized")

        try:
            # Step 1: Get total shares from res.partner
            partner_fields = ["total_partner_owned_share"]
            partner_data = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "res.partner",
                "read",
                [[partner_id]],
                {"fields": partner_fields},
            )

            total_shares = 0
            if partner_data and len(partner_data) > 0:
                total_shares = partner_data[0].get("total_partner_owned_share", 0)
            
            # Step 2: Get all share ownership records for this member
            share_domain = [("partner_id", "=", partner_id)]
            share_fields = [
                "id",
                "owned_share",
                "create_date",
                "related_invoice_ids"
            ]
            
            share_records = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "res.partner.owned.share",
                "search_read",
                [share_domain],
                {"fields": share_fields, "order": "create_date asc"},
            )

            # Step 3: Process share records and related invoices
            share_purchases = []
            first_purchase_date = None
            
            for share_record in share_records:
                share_id = share_record.get("id")
                owned_shares = share_record.get("owned_share", 0)
                create_date = share_record.get("create_date")
                invoice_ids = share_record.get("related_invoice_ids", [])
                
                # Extract invoice IDs (they come as [id, name] tuples)
                invoice_id_list = []
                if invoice_ids:
                    for inv in invoice_ids:
                        if isinstance(inv, list) and len(inv) > 0:
                            invoice_id_list.append(inv[0])
                        elif isinstance(inv, int):
                            invoice_id_list.append(inv)
                
                # Get invoice details for this share record
                invoice_details = []
                if invoice_id_list:
                    try:
                        invoice_data = self.models.execute_kw(
                            self.db,
                            self.uid,
                            self.password,
                            "account.invoice",
                            "read",
                            [invoice_id_list],
                            {"fields": ["id", "date", "number", "state", "amount_total"]},
                        )
                        
                        for inv in invoice_data:
                            invoice_details.append({
                                "invoice_id": inv.get("id"),
                                "invoice_number": inv.get("number"),
                                "invoice_date": inv.get("date"),
                                "state": inv.get("state"),
                                "amount": inv.get("amount_total"),
                            })
                            
                            # Track earliest invoice date as first purchase date
                            inv_date = inv.get("date")
                            if inv_date and (first_purchase_date is None or inv_date < first_purchase_date):
                                first_purchase_date = inv_date
                                
                    except Exception as invoice_error:
                        logger.warning(f"Error fetching invoice details for share {share_id}: {invoice_error}")
                        continue
                
                # Add share purchase event
                share_purchases.append({
                    "share_id": share_id,
                    "shares_purchased": owned_shares,
                    "purchase_date": create_date,
                    "invoices": invoice_details,
                })
                
                # If no invoices found, use share create_date as fallback for first purchase
                if not first_purchase_date and create_date:
                    first_purchase_date = create_date

            # Step 4: Return structured data
            result = {
                "total_shares": int(total_shares),
                "first_purchase_date": first_purchase_date,
                "join_date": first_purchase_date,  # Alias for UI consistency
                "share_purchases": share_purchases,
            }
            
            logger.info(f"Fetched share information for member {partner_id}: {total_shares} shares, first purchase: {first_purchase_date}")
            return result

        except Exception as e:
            logger.error(f"Error fetching share information for member {partner_id}: {e}", exc_info=True)
            raise Exception(f"Failed to fetch share information: {str(e)}")

    def detect_pair_relationship(self, member_data: Dict) -> Dict:
        """
        Detect if member is part of a pair (binôme).

        Example structure:
        - Main member "DOE, John" : NO tag, has child "DUPONT, Roger" (associated_people)
        - Associated member (DUPONT): TWO profiles with same name + tag
          - Classical: tag "Cooperateur associe", unsubscribed, no parent
          - Associated_people: tag "Cooperateur associe", parent = DOE

        Args:
            member_data: Dictionary containing member information with fields:
                id, name, category_ids, parent_id, child_ids

        Returns:
            Dictionary with:
            - is_pair: bool
            - pair_type: 'main' | 'associated_classical' | 'associated_shopping'
            - main_member_id: int
            - main_member_name: str
            - classical_profile_id: int (DUPONT classical)
            - shopping_profile_id: int (DUPONT associated_people)
            - other_profile_id: int (the other profile to display)
            - pair_member_id: int (alias for other_profile_id, for compatibility)
        """
        from utils import has_cooperateur_associe_tag, extract_id

        try:
            has_pair_tag = has_cooperateur_associe_tag(member_data.get("category_id"))
            member_name = member_data.get("name")
            member_id = member_data.get("id")

            logger.debug(f"Detecting pair for member {member_id} ({member_name}), has_pair_tag: {has_pair_tag}")

            # Case 1: Profile WITH tag (DUPONT)
            if has_pair_tag:
                parent_id = extract_id(member_data.get("parent_id"))

                if parent_id:
                    # This is DUPONT's associated_people profile (shopping profile)
                    # Search for DUPONT's classical profile (same name + tag, no parent)
                    logger.debug(f"Member {member_id} has tag and parent {parent_id}, searching for classical profile")
                    domain = [("name", "=", member_name), ("category_id", "in", [3])]
                    classical_profiles = self.search_read("res.partner", domain, ["id", "name", "parent_id"])

                    # Find the one without parent (classical profile)
                    classical_profile = next((p for p in classical_profiles if not p.get("parent_id")), None)

                    if classical_profile:
                        # Fetch parent name
                        parent_info = self.execute("res.partner", "read", [parent_id], ["name"])
                        parent_name = parent_info[0].get("name", "") if parent_info and len(parent_info) > 0 else ""

                        logger.info(f"Detected pair: {member_name} (shopping profile) paired with {parent_name} (main)")
                        return {
                            "is_pair": True,
                            "pair_type": "associated_shopping",
                            "main_member_id": parent_id,
                            "main_member_name": parent_name,
                            "classical_profile_id": classical_profile["id"],
                            "shopping_profile_id": member_id,
                            "other_profile_id": parent_id,
                            "pair_member_id": parent_id,  # Compatibility
                        }
                else:
                    # This is DUPONT's classical profile (owns shares, unsubscribed)
                    # Search for DUPONT's associated_people profile (same name + tag + has parent)
                    logger.debug(f"Member {member_id} has tag but no parent, searching for shopping profile")
                    domain = [("name", "=", member_name), ("category_id", "in", [3])]
                    shopping_profiles = self.search_read("res.partner", domain, ["id", "name", "parent_id"])

                    # Find the one WITH parent (associated_people profile)
                    shopping_profile = next((p for p in shopping_profiles if p.get("parent_id")), None)

                    if shopping_profile:
                        parent_id = extract_id(shopping_profile["parent_id"])
                        parent_name = shopping_profile["parent_id"][1] if isinstance(shopping_profile["parent_id"], list) else ""

                        logger.info(f"Detected pair: {member_name} (classical profile) paired with {parent_name} (main)")
                        return {
                            "is_pair": True,
                            "pair_type": "associated_classical",
                            "main_member_id": parent_id,
                            "main_member_name": parent_name,
                            "classical_profile_id": member_id,
                            "shopping_profile_id": shopping_profile["id"],
                            "other_profile_id": parent_id,
                            "pair_member_id": parent_id,  # Compatibility
                        }

            # Case 2: Profile WITHOUT tag (DOE - main member)
            else:
                child_ids = member_data.get("child_ids", [])
                if child_ids:
                    logger.debug(f"Member {member_id} has no tag but has {len(child_ids)} children, checking for pair")
                    # Check children for profiles with tag
                    children = self.execute("res.partner", "read", child_ids, ["id", "name", "category_id"])
                    logger.debug(f"Fetched {len(children)} children: {children}")

                    for child in children:
                        child_category_id = child.get("category_id")
                        logger.debug(f"Checking child {child.get('id')}: category_id={child_category_id}")
                        if has_cooperateur_associe_tag(child_category_id):
                            logger.debug(f"Child {child.get('id')} has cooperateur associe tag!")
                            child_name = child.get("name")
                            child_id = child.get("id")

                            logger.debug(f"Found tagged child {child_id} ({child_name}), searching for classical profile")
                            # Search for classical profile with same name as this child + tag
                            domain = [("name", "=", child_name), ("category_id", "in", [3])]
                            matching_profiles = self.search_read("res.partner", domain, ["id", "name", "parent_id"])

                            # Find classical profile (no parent)
                            classical_profile = next((p for p in matching_profiles if not p.get("parent_id")), None)

                            if classical_profile:
                                # This confirms it's a pair!
                                logger.info(f"Detected pair: {member_name} (main) paired with {child_name}")
                                return {
                                    "is_pair": True,
                                    "pair_type": "main",
                                    "main_member_id": member_id,
                                    "main_member_name": member_name,
                                    "classical_profile_id": classical_profile["id"],
                                    "shopping_profile_id": child_id,
                                    "other_profile_id": classical_profile["id"],
                                    "pair_member_id": classical_profile["id"],  # Compatibility
                                }

            logger.debug(f"Member {member_id} is not part of a pair")
            return {"is_pair": False}

        except Exception as e:
            logger.error(f"Error detecting pair relationship for member {member_data.get('id')}: {e}", exc_info=True)
            return {"is_pair": False}

    def get_pair_profiles(self, pair_info_list: List[Dict]) -> Dict[int, Dict]:
        """
        Batch fetch other profiles for detected pairs.

        This method optimizes API calls by fetching all other profiles in a single
        batch request instead of making individual requests for each pair.

        Args:
            pair_info_list: List of pair_info dicts with other_profile_id

        Returns:
            Dict mapping other_profile_id to profile data

        Example:
            >>> pair_info_list = [
            ...     {"is_pair": True, "other_profile_id": 100},
            ...     {"is_pair": True, "other_profile_id": 200},
            ...     {"is_pair": False}
            ... ]
            >>> profiles = odoo.get_pair_profiles(pair_info_list)
            >>> # Returns: {100: {...profile data...}, 200: {...profile data...}}
        """
        try:
            # Extract unique other_profile_ids from pairs
            other_profile_ids = list(set(
                p["other_profile_id"]
                for p in pair_info_list
                if p.get("is_pair") and p.get("other_profile_id")
            ))

            if not other_profile_ids:
                logger.debug("No pair profiles to fetch")
                return {}

            logger.info(f"Batch fetching {len(other_profile_ids)} pair profiles")

            # Batch fetch all profiles
            fields = [
                "id", "name", "barcode_base", "cooperative_state",
                "is_worker_member", "shift_type", "customer",
                "is_unsubscribed", "category_id"
            ]
            profiles = self.execute("res.partner", "read", other_profile_ids, fields)

            # Create lookup dict
            profile_map = {p["id"]: p for p in profiles}
            logger.debug(f"Fetched {len(profile_map)} pair profiles")

            return profile_map

        except Exception as e:
            logger.error(f"Error batch fetching pair profiles: {e}", exc_info=True)
            return {}
