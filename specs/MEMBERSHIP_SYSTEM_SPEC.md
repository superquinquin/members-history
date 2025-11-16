# Odoo Membership System Specification

**Generated:** 2025-11-15
**System:** Odoo-based Cooperative Management (Superquinquin)
**Purpose:** Comprehensive specification of how membership and shift systems work in Odoo

---

## 1. ODOO MODELS & FIELDS

### 1.1 res.partner (Members)

The `res.partner` model represents all members, contacts, and associated people in the cooperative.

**Identification & Contact Fields:**

```python
'id': int                          # Partner ID (unique identifier)
'name': str                        # Full name (format: "LASTNAME, Firstname")
'street': str                      # Street address line 1
'street2': str                     # Street address line 2 (optional)
'zip': str                         # Postal code
'city': str                        # City name
'phone': str                       # Primary phone number
'mobile': str                      # Mobile phone number
'email': str                       # Email address
'image': str (base64)              # Full-size profile picture
'image_small': str (base64)        # Small profile picture (32x32)
'image_medium': str (base64)       # Medium profile picture (128x128)
```

**Membership Status Fields:**

```python
'is_worker_member': bool (computed)     # True if owns worker capital shares
'cooperative_state': str (selection)    # Current membership status
'is_unsubscribed': bool (computed)      # True if not linked to shift template
'shift_type': str (selection)           # 'standard' or 'ftop'
'total_partner_owned_share': int (computed) # Total shares owned (all types)
```

**cooperative_state Selection Values:**
- `'not_concerned'` - Not a cooperative member
- `'unsubscribed'` - Unsubscribed from shift system
- `'exempted'` - Exempted from shifts (medical, age, etc.)
- `'vacation'` - On vacation status
- `'up_to_date'` - Current with shift obligations
- `'alert'` - Warning state (Behind on shift obligations)
- `'suspended'` - Temporarily suspended, shopping is not allowed
- `'delay'` - Temporary shopping derogation while member is doing make-up shifts
- `'blocked'` - Shopping privileges blocked
- `'unpayed'` - Unpaid share capital

**Shift-Related Fields:**

```python
'current_template_name': str (computed)     # Current shift template name
'leader_ids': Many2many → res.partner       # Shift team leaders
'tmpl_reg_ids': One2many → shift.template.registration  # Template registrations
'registration_ids': One2many → shift.registration       # Individual shift registrations
'leave_ids': One2many → shift.leave                     # Leave periods
```

**Family & Associations:**

```python
'parent_id': Many2one → res.partner        # Parent member (for associated people)
'child_ids': One2many → res.partner        # Associated people/children
'nb_associated_people': int (computed)     # Count of associated people
```

**Buying Access:**

```python
'customer': bool (computed)                # Can purchase at store
# True if: cooperative_state in ['up_to_date', 'alert', 'delay', 'exempted']
#       OR force_customer = True
```

**Code Reference:** `backend/odoo_client.py:86-104, 275-281`

---

### 1.2 shift.shift (Shift Instances)

Represents specific shift occurrences (e.g., "Monday 9am-12pm Team A on 2025-10-15").

**Core Fields:**

```python
'id': int                          # Shift instance ID
'name': str                        # Human-readable name (e.g., "Monday Morning Team A")
'date_begin': datetime             # Shift start date and time
'date_end': datetime               # Shift end date and time
'state': str (selection)           # 'draft', 'confirm', 'done', 'cancel'
```

**Type & Scheduling Fields:**

```python
'shift_type_id': Many2one → shift.type     # [id, name] - CRITICAL for type determination
                                           # Examples: [1, 'FTOP'], [2, 'Standard']
'week_number': int                         # Week number in cycle (1-4)
'week_name': str                           # Week letter ('A', 'B', 'C', 'D')
'shift_template_id': Many2one → shift.template  # Source template (if recurring)
```

**Important:** `shift_type_id` is the PRIMARY and most reliable source for determining whether a shift is FTOP vs Standard type. This field is **always populated** in production data.

**Code Reference:** `backend/odoo_client.py:166-183`

---

### 1.3 shift.registration (Shift Attendance Records)

Tracks individual member attendance at specific shift instances.

**Core Fields:**

```python
'id': int                          # Registration ID
'partner_id': Many2one → res.partner   # Member who (should have) attended
'shift_id': Many2one → shift.shift     # Which shift instance (stored as [id, name])
'date_begin': datetime                 # Shift start (copied from shift.shift)
'date_end': datetime                   # Shift end (copied from shift.shift)
'state': str (selection)               # Attendance state
'template_created': bool                # True if auto-created from template
'date_closed': datetime                # When marked done/absent/excused
```

**State Values & Meanings:**

| State | Meaning | Counter Event? | Point Change |
|-------|---------|----------------|--------------|
| `'done'` | Shift attended successfully | ✅ Yes | +1 |
| `'absent'` | Missed shift without excuse | ✅ Yes | -2 (+ holiday relief) |
| `'excused'` | Excused absence (approved) | ❌ No | 0 |
| `'open'` | Scheduled, not yet occurred | ❌ No | 0 |
| `'waiting'` | Shift exchanged away / during leave | ❌ No | 0 |
| `'replaced'` | Exchanged shift filled by another member | ❌ No | 0 |
| `'draft'` | Not confirmed | ❌ No | 0 |
| `'cancel'` | Cancelled shift | ❌ No | 0 |

**Special Indicators:**

```python
'is_late': bool                    # True if arrived late (still marked 'done')
'is_exchanged': bool               # True if shift was exchanged away
'is_exchange': bool                # True if this is a replacement shift
```

**Enriched Fields (joined from shift.shift):**

These fields are populated by joining with the related `shift.shift` record:

```python
'shift_name': str                  # From shift.shift.name
'week_number': int                 # From shift.shift.week_number
'week_name': str                   # From shift.shift.week_name
'shift_type_id': [id, name]       # From shift.shift.shift_type_id
```

**Query Domain Used:**
```python
[('partner_id', '=', member_id), ('state', 'in', ['done', 'absent', 'excused', 'open'])]
```

**Code Reference:** `backend/odoo_client.py:132-203`

---

### 1.4 shift.counter.event (Point Changes)

Records all changes to a member's shift counter (points system).

**Core Fields:**

```python
'id': int                          # Event ID
'partner_id': Many2one → res.partner   # Member whose counter changed
'shift_id': Many2one → shift.shift or False  # Related shift (None for manual events)
'create_date': datetime                # When event was created (CRITICAL for ordering)
'point_qty': int                       # Points added (+) or removed (-)
'sum_current_qty': int                 # DEPRECATED: Running total (unreliable)
'type': str (selection)                # 'ftop' or 'standard' - which counter
'is_manual': bool                      # True if manually created by admin
'name': str                            # Description/reason for event
```

**Critical Business Rules:**

1. **Dual Counter System:**
   - Each member has TWO independent counters
   - FTOP counter (`type='ftop'`) for flexible/vacation shifts
   - Standard counter (`type='standard'`) for regular ABCD shifts

2. **Counter Event Creation:**
   - **Automatic:** Created when shift.registration state changes to 'done' or 'absent'
     - `is_manual=False`
     - Has `shift_id` reference
   - **Manual:** Created by administrators for adjustments
     - `is_manual=True`
     - May or may not have `shift_id`

3. **FTOP Member Behavior:**
   - ALL counter events for FTOP members have `type='ftop'`
   - This is true EVEN when they attend standard ABCD shifts
   - This is why `shift.shift_type_id` is needed to distinguish shift types

4. **Running Total Calculation:**
   - The `sum_current_qty` field from Odoo is UNRELIABLE
   - Must recalculate by:
     - Fetching ALL counter events (no limit)
     - Sorting chronologically by `create_date`
     - Maintaining separate running totals for FTOP and Standard
     - Each event should track BOTH counter totals at that point in time

**Computed Fields (added by application):**

```python
'ftop_total': int                  # Running total of FTOP counter at this event
'standard_total': int              # Running total of Standard counter at this event
```

**Query Domain Used:**
```python
[('partner_id', '=', member_id)]
# No limit - ALL events needed for accurate totals
```

**Code Reference:** `backend/odoo_client.py:235-270`, `backend/app.py:159-322`

---

### 1.5 shift.leave (Member Absences)

Represents approved absence periods (vacation, sick leave, etc.).

**Core Fields:**

```python
'id': int                          # Leave ID
'partner_id': Many2one → res.partner   # Member on leave
'type_id': Many2one → shift.leave.type # Type of leave (stored as [id, name])
'start_date': date                     # Leave start date
'stop_date': date                      # Leave end date (or False for open-ended)
'state': str (selection)               # Leave approval state
'non_defined_leave': bool              # True if open-ended (no stop_date)
```

**State Values:**

| State | Meaning |
|-------|---------|
| `'done'` | Approved and active |
| `'waiting'` | Pending approval |
| `'draft'` | Not yet submitted |
| `'cancel'` | Cancelled leave |

**Leave Types (shift.leave.type):**

Common types include:
- Vacation
- Sick leave
- Parental leave
- Other (configured in Odoo)

Each type has:
```python
'is_anticipated': bool             # Can be planned in advance
```

**Business Rules:**

1. Shifts during active leave (`state='done'` and date within range) that are marked 'excused' do NOT generate counter events
2. Leave periods are displayed as markers on the timeline
3. Open-ended leaves continue indefinitely until stopped

**Enriched Fields:**

```python
'leave_type': str                  # Extracted from type_id[1]
```

**Query Domain Used:**
```python
[('partner_id', '=', member_id), ('state', '=', 'done')]
```

**Code Reference:** `backend/odoo_client.py:205-233`

---

### 1.6 pos.order (Purchase History)

Tracks member purchases at the cooperative store.

**Fields Used:**

```python
'id': int                          # Order ID
'partner_id': Many2one → res.partner   # Member who purchased
'date_order': datetime                 # Purchase timestamp
'name': str                            # Order name/number
'pos_reference': str                   # Point-of-sale reference (e.g., "Commande 07291-004-0043")
'state': str (selection)               # Order state
'amount_total': float                  # Total purchase amount (available but not used)
```

**Query Domain Used:**
```python
[('partner_id', '=', member_id), ('state', '=', 'done')]
```

**Query Options:**
- **Limit:** 50 most recent orders
- **Sort:** `date_order desc`

**Code Reference:** `backend/odoo_client.py:106-130`

---

### 1.7 shift.type (Shift Categories)

Defines the types/categories of shifts available in the system.

**Core Fields:**

```python
'id': int                          # Shift type ID
'name': str                        # Shift type label (e.g., "FTOP", "Standard", "Service Volant")
'is_ftop': bool                    # True if this is an FTOP shift type (default: False)
'default_registration_min': int    # Default minimum seats
'default_registration_max': int    # Default maximum seats
'default_reply_to': str            # Default reply-to email for notifications
'prefix_name': str                 # Prefix added to shift/template names
```

**Usage:**
- Referenced by `shift.shift.shift_type_id` and `shift.template.shift_type_id`
- The `is_ftop` field is the authoritative indicator for FTOP vs Standard classification
- Typically 2-3 types configured: "Standard", "FTOP"/"Service Volant", and possibly others

---

### 1.8 shift.holiday (Holiday Relief - "Assouplissement de présence")

Defines holiday periods that provide penalty relief for missed shifts.

**Core Fields:**

```python
'id': int                          # Holiday ID
'name': str                        # Holiday name (e.g., "Christmas Period", "Summer Break")
'holiday_type': str (selection)    # 'long_period' or 'single_day'
'date_begin': date                 # Holiday start date
'date_end': date                   # Holiday end date
'state': str (selection)           # 'draft', 'confirmed', 'done', 'cancel'
'make_up_type': str (selection)    # '1_make_up' or '0_make_up'
                                   # Determines relief points: +1 or +2
'send_email_reminder': bool        # Send notifications to members
'reminder_template_id': Many2one → mail.template  # Email template
```

**Holiday Types:**
- `'long_period'`: Multi-day holiday (e.g., Christmas week, summer break)
- `'single_day'`: Single-day holiday (date_begin == date_end)

**Make-up Types:**
- `'1_make_up'`: Member needs **1 make-up shift** to pardon the absence
  - Relief: **+1 point**
  - Net penalty: -2 +1 = **-1 point**
  - Requires attending 1 additional shift to return to 0

- `'0_make_up'`: **No make-up shift needed** - absence fully pardoned
  - Relief: **+2 points** (full relief)
  - Net penalty: -2 +2 = **0 points**
  - No action required from member

**How It Works:**

When a member is absent during an active holiday period:
1. **Initial penalty:** -2 points (automatic counter event)
2. **Holiday relief:** +1 or +2 points (second counter event, based on `make_up_type`)
3. **Net result:** -1 point (requires 1 make-up) or 0 points (fully pardoned)

Both counter events reference the same `shift_id` and are aggregated together by the application.

**Business Logic:**
- Standard absence: -2 points = needs 2 make-up shifts to recover
- Holiday with `1_make_up`: -1 point = needs only 1 make-up shift
- Holiday with `0_make_up`: 0 points = no make-up needed, fully excused

---

### 1.9 shift.template (Recurring Shift Templates)

Defines recurring shift schedules that generate `shift.shift` instances.

**Core Fields:**

```python
'id': int                          # Template ID
'name': str (computed)             # Generated name (type + time + location)
'shift_type_id': Many2one → shift.type  # Shift category (required)
'start_datetime': datetime         # First occurrence date/time
'end_datetime': datetime           # End time of first occurrence
'duration': float                  # Shift length in hours (computed)
```

**Recurrence Fields:**

```python
'recurrency': bool                 # True if shift repeats
'rrule_type': str (selection)      # 'daily', 'weekly', 'monthly', 'yearly'
'interval': int                    # Repeat every N periods
'final_date': date                 # Last occurrence date
'rrule': str                       # iCalendar recurrence rule (computed)
```

**Seat Management:**

```python
'seats_max': int                   # Maximum capacity
'seats_min': int                   # Minimum required for confirmation
'seats_availability': str          # 'limited' or 'unlimited'
'seats_reserved': int (computed)   # Current reserved seats
'seats_available': int (computed)  # Remaining seats
'seats_used': int (computed)       # Confirmed participants
```

**Leadership:**

```python
'user_id': Many2one → res.partner  # Primary shift leader
'user_ids': Many2many → res.partner  # Multiple coordinators
```

**Relationships:**

```python
'registration_ids': One2many → shift.template.registration
# Members registered to this recurring template
```

**Important:**
- FTOP members are registered to a special technical FTOP template
- This template generates technical FTOP shifts (not real work shifts)
- Standard ABCD members are registered to regular recurring templates

---

### 1.10 shift.template.registration (Template Assignments)

Links members to recurring shift templates.

**Core Fields:**

```python
'id': int                          # Registration ID
'partner_id': Many2one → res.partner  # Member assigned to template
'shift_template_id': Many2one → shift.template  # Which template
'date_begin': date                 # Assignment start date
'date_end': date                   # Assignment end date (or False for ongoing)
'state': str (selection)           # Registration status
'is_current': bool (computed)      # True if currently active
```

**State Values:**

| State | Meaning | Effect on Shifts |
|-------|---------|------------------|
| `'open'` | Active registration | Member expected to attend shifts |
| `'waiting'` | Suspended (during leave) | Member NOT expected to attend - absences don't create counter penalties |
| `'done'` | Completed/ended | No longer active |
| `'cancel'` | Cancelled | Void |

**Relationships:**

```python
'line_ids': One2many → shift.template.registration.line
# History of this template assignment (start/stop events)
```

**Important:**
- Standard ABCD members: Assigned to one specific template (e.g., "Monday 9am Week A")
- FTOP members: Assigned to technical FTOP template (not a real work shift)
- Multiple registrations possible if member changes shifts over time
- **"waiting" state** automatically created when leave is approved, suspends shift expectations

---

## 2. MEMBER TYPES & STATES

### 2.1 Member Categories

Members are categorized based on computed fields:

**Primary Categories:**

```python
is_member = total_partner_owned_share > 0
# Has purchased at least one cooperative share

is_former_member = was_member and total_partner_owned_share == 0
# Previously owned shares but sold them all

is_worker_member = has worker capital shares
# Owns "worker" type shares (requires shift participation)

is_associated_people = parent_id.is_member and not own_shares
# Linked to a member but doesn't own shares themselves
# Inherits parent's cooperative_state

is_interested_people = not member and not associated and not supplier
# Registered interest but not yet a member
```

**Purchase Rights:**

```python
customer = cooperative_state in ['up_to_date', 'alert', 'delay', 'exempted']
           OR force_customer == True
# Can make purchases if in good standing or force flag set
```

---

### 2.2 Shift Types

The cooperative supports two distinct shift participation systems:

#### Standard ABCD Shifts (`shift_type='standard'`)

**Characteristics:**
- Fixed recurring schedule
- 4-week rotating cycle (weeks A, B, C, D)
- Member assigned to specific shift template
- Must work same shift each cycle (e.g., "Monday 9am-12pm Team A every Week A")
- Counter type: `'standard'`
- Predictable, regular commitment

**Example:**
```
Member is assigned: "Monday Morning Team A, Week A"
Works: Week A of Cycle 1, Week A of Cycle 2, Week A of Cycle 3, ...
```

**Additional Shift Registration (Make-up and Extra Shifts):**

Standard ABCD members can register for shifts **outside their assigned week/time**. The registration type depends on their counter status:

**Case 1: Make-up Shifts (Counter < 0)**
```python
# Member needs to recover from absence
member.standard_counter = -2  # Missed their assigned shift

# Registers for additional Standard shift
registration.partner_id = member
registration.shift_id = [456, 'Tuesday Afternoon Team B']  # Not their assigned shift
registration.type = 'standard'  # Registration type
counter_event.type = 'standard'  # Points go to standard counter

# Attends the shift
registration.state = 'done'
counter_event.point_qty = +1
# Result: standard_counter = -2 + 1 = -1 (needs 1 more make-up)
```

**Case 2: Anticipatory Extra Shifts (Counter >= 0)**
```python
# Member wants to build buffer for future unavailability
member.standard_counter = 0  # Currently up_to_date

# Registers for additional Standard shift
registration.partner_id = member
registration.shift_id = [789, 'Wednesday Evening Team C']  # Not their assigned shift
registration.type = 'ftop'  # Registration type switches to FTOP!
counter_event.type = 'ftop'  # Points go to FTOP counter (not standard!)

# Attends the shift
registration.state = 'done'
counter_event.point_qty = +1
# Result: ftop_counter = 0 + 1 = +1 (accumulating in FTOP counter)
#         standard_counter = 0 (unchanged)
```

**Key Principles:**
- **Standard counter negative** → Extra shifts count toward standard counter (make-up)
- **Standard counter zero or positive** → Extra shifts count toward FTOP counter (anticipatory buffer)

This allows Standard ABCD members to build up an FTOP counter for planned absences, similar to FTOP members.

**Shift Exchange System:**

Standard ABCD members can exchange their regular assigned shift with another Standard shift when they know in advance they cannot attend.

**Exchange Process:**

```python
# Member A knows they can't attend their regular shift on Jan 15
# They choose a replacement shift on Jan 8 instead

# Step 1: Original registration status changes
original_registration = {
    'partner_id': member_A,
    'shift_id': [123, 'Monday 9am Week A - Jan 15'],  # Their regular shift
    'state': 'waiting',  # Changed from 'open' to 'waiting'
    'is_exchanged': True
}

# Step 2: New registration created for replacement shift
replacement_registration = {
    'partner_id': member_A,
    'shift_id': [456, 'Tuesday 2pm Week D - Jan 8'],  # Chosen replacement
    'type': 'standard',  # Same type as regular shift
    'state': 'open',
    'is_exchange': True
}

# Result: Member A will attend Jan 8 shift instead of Jan 15 shift
# No counter penalty if they attend the replacement
```

**Reciprocal Exchange (Cross-Exchange):**

When another member chooses the first member's freed shift as their replacement:

```python
# Member B needs to exchange their shift
# They choose Member A's freed shift (Jan 15) as replacement

# Member A's original registration gets reused
original_registration.state = 'replaced'  # Changed from 'waiting' to 'replaced'
original_registration.partner_id = member_B  # Now assigned to Member B

# Member B's original shift becomes available
member_b_registration.state = 'waiting'

# Result: Member A's Jan 15 shift is now covered by Member B
```

**Exchange States:**

| Registration State | Meaning |
|-------------------|---------|
| `'open'` | Normal assigned shift |
| `'waiting'` | Exchanged away, slot available for others |
| `'replaced'` | Exchanged away and filled by another member |

**Important Rules:**
- Exchange must be to another **Standard ABCD shift** (not FTOP technical shift)
- Registration type remains `'standard'` for exchanges
- Member fulfills shift obligation by attending replacement
- Both shifts count equally - no extra credit for difficult timing
- If replacement shift is attended → no penalty
- If replacement shift is missed → standard -2 point penalty (+ holiday relief if applicable)

#### FTOP Shifts (`shift_type='ftop'`)

**Characteristics:**
- Flexible scheduling system
- "Flying Time Off" / "Service Volant" in French
- Member chooses which shifts to attend from available Standard ABCD shifts
- Counter type: `'ftop'`
- Counter can go **positive** (encouraged to accumulate points for future absences)

**How FTOP System Works:**

1. **Technical Template Registration:**
   - FTOP members are registered to a special "FTOP template" (`shift_type_id='ftop'`)
   - This is a **technical shift** that does NOT correspond to a real working shift in the store
   - Used only for tracking and automatic point deduction

2. **Actual Shift Participation:**
   - FTOP members register for and attend **Standard ABCD shifts** (real working shifts)
   - Their registrations are marked as `type='ftop'` (counter bucket)
   - The shifts themselves are `shift_type_id='standard'` (actual shift type)

3. **Counter Mechanics:**

   **Earning Points (Attendance):**
   ```python
   # FTOP member attends a Standard shift
   shift.shift_type_id = [2, 'Standard']  # It's a standard shift
   registration.state = 'done'
   counter_event.type = 'ftop'             # Goes to FTOP counter
   counter_event.point_qty = +1            # Earns 1 point
   ```

   **Losing Points (Cycle Deduction):**
   ```python
   # Once per cycle: Technical FTOP shift closed
   # All FTOP members automatically marked present
   shift.shift_type_id = [1, 'FTOP']      # Technical FTOP shift
   registration.state = 'done'
   counter_event.type = 'ftop'
   counter_event.point_qty = -1            # Automatic -1 EVERY cycle
   # This happens regardless of how many Standard shifts attended
   ```

   **Losing Points (Missed Shift):**
   ```python
   # FTOP member registers but doesn't attend Standard shift
   shift.shift_type_id = [2, 'Standard']
   registration.state = 'absent'
   counter_event.type = 'ftop'
   counter_event.point_qty = -2            # Same penalty as ABCD members
   # Plus holiday relief if applicable (+1 or +2)
   ```

4. **Counter Accumulation Strategy:**
   - FTOP counters **can and should go positive**
   - Members are encouraged to accumulate points (buffer)
   - Allows for long periods of unavailability without penalty

   **Example Scenario:**
   ```
   Cycle 1: Member attends 2 Standard shifts
     +1 (shift 1) +1 (shift 2) -1 (cycle closing) = Counter: +1

   Cycle 2: Member attends 0 Standard shifts
     -1 (cycle closing) = Counter: 0 (still up_to_date)

   Cycle 3: Member attends 0 Standard shifts
     -1 (cycle closing) = Counter: -1 (moves to alert state)

   Cycle 4: Member attends 1 Standard shift
     +1 (shift) -1 (cycle closing) = Counter: -1 (still alert)

   Cycle 5: Member attends 2 Standard shifts
     +1 (shift 1) +1 (shift 2) -1 (cycle closing) = Counter: +1 (back to up_to_date)
   ```

   **Key Point:** The -1 cycle deduction happens **every cycle** regardless of attendance. Members must maintain positive net activity over time.

**Important Notes:**
- FTOP members attend the same physical shifts as Standard members
- All counter events for FTOP members have `type='ftop'`
- The `shift.shift_type_id` field distinguishes the actual shift type (FTOP technical vs Standard working shift)

**Terminology:**
- English: "FTOP" (Flying Time Off)
- French: "Vacation", "Service Volant", or "Volant"

**Code Reference:** `specs/odoo.md`, `FTOP_SHIFT_ANALYSIS.md:138-158`

---

### 2.3 Cooperative State Workflow

The `cooperative_state` field represents a member's current standing.

**State Computation Logic:**

```python
def compute_cooperative_state(member):
    if member.is_associated_people:
        # Inherit parent's state
        return member.parent_id.cooperative_state

    elif member.is_worker_member:
        if member.is_unsubscribed:
            return 'unsubscribed'
        elif member.is_unpayed:  # Unpaid shares
            return 'unpayed'
        else:
            # Based on shift counter and participation
            return member.working_state

    else:
        return 'not_concerned'
```

**State Meanings:**

| State | Meaning | Shopping Rights | Counter Status |
|-------|---------|----------------|----------------|
| `up_to_date` | Current with obligations | ✅ Yes | Positive |
| `alert` | Counter getting low | ✅ Yes | Near threshold |
| `delay` | Behind on shifts | ✅ Yes | Below threshold |
| `suspended` | Temporarily suspended | ❌ No | Very low |
| `blocked` | Shopping blocked | ❌ No | Critical |
| `exempted` | Exempt from shifts | ✅ Yes | N/A |
| `vacation` | On vacation | ✅ Yes | Varies |
| `unsubscribed` | No shift assignment | Varies | N/A |
| `unpayed` | Unpaid shares | ❌ No | N/A |

**State Transitions:**

1. **When shares reach 0:**
   ```python
   # Triggered automatically
   - Unsubscribe from all shift templates
   - Set opt_out = True (no marketing emails)
   - Transition: member → former_member
   ```

2. **When counter changes:**
   ```python
   # Updated based on counter thresholds
   if counter >= threshold_1:
       state = 'up_to_date'
   elif counter >= threshold_2:
       state = 'alert'
   elif counter >= threshold_3:
       state = 'delay'
   else:
       state = 'suspended' or 'blocked'
   ```

3. **When unsubscribed:**
   ```python
   # Updated nightly by cron
   is_unsubscribed = no active template registration lines
   if is_worker_member and is_unsubscribed:
       cooperative_state = 'unsubscribed'
   ```

**Code Reference:** `specs/odoo.md:244-256`, `specs/odoo.md:91-111`

---

## 3. SHIFT SYSTEM

### 3.1 Shift Lifecycle

**Complete Flow:**

```
1. shift.template (Recurring Schedule)
   ↓ generates instances

2. shift.shift (Specific Date Instance)
   Example: "Monday Morning Team A - Oct 15, 2025 9:00-12:00"
   ↓ member signs up OR auto-assigned from template

3. shift.registration (Member's Attendance Record)
   State: draft → open → [done|absent|excused|cancel]
   ↓ when closed with done/absent state

4. shift.counter.event (Point Change)
   Point change recorded (±1 or ±2)
   ↓ affects

5. res.partner.cooperative_state (Member Status)
   State updated based on new counter total
```

**Key Moments:**

- **Template Generation:** Recurring shifts generated X weeks in advance
- **Registration Creation:** Auto-created for template members, or manual signup
- **Shift Opening:** State changes to 'open' when shift time approaches
- **Shift Closing:** State changes to 'done'/'absent'/'excused' after shift ends
- **Counter Update:** Counter event created immediately when shift closed

---

### 3.2 Shift Type Determination

**Critical Logic for Determining Shift Type:**

The application uses a **hybrid approach** with clear priority:

```python
def determine_shift_type(shift, shift_counter_map, shift_id):
    """
    Determines if a shift is FTOP or Standard type.

    Returns:
        tuple of (shift_type, shift_type_id_raw)
        where shift_type is 'ftop' | 'standard' | 'unknown'
    """

    # PRIORITY 1: shift.shift_type_id field (MOST RELIABLE)
    shift_type_id = shift.get('shift_type_id')
    if shift_type_id:
        # shift_type_id format: [id, name]
        # Example: [1, 'FTOP'] or [2, 'Standard'] or [3, 'Service Volant']
        if isinstance(shift_type_id, list) and len(shift_type_id) > 1:
            type_name = shift_type_id[1].lower()

            # Case-insensitive matching for FTOP variations
            if 'ftop' in type_name or 'volant' in type_name:
                return ('ftop', shift_type_id)
            else:
                return ('standard', shift_type_id)

        # If just ID, default to standard
        return ('standard', shift_type_id)

    # PRIORITY 2: Counter event type (FALLBACK only)
    # Used only when shift_type_id is missing (legacy data)
    if shift_id and shift_id in shift_counter_map:
        counter_type = shift_counter_map[shift_id].get('type', 'standard')
        print(f"Warning: Using counter type as fallback for shift {shift_id}")
        return (counter_type, None)

    # PRIORITY 3: Unknown (no reliable source)
    print(f"Warning: Cannot determine shift type for shift {shift.get('id')}")
    return ('unknown', None)
```

**Why This Order?**

1. **shift_type_id is authoritative** - It describes what TYPE of shift it is (FTOP template vs Standard template)
2. **counter.type is misleading** - It only indicates which counter was affected
   - FTOP members have ALL events marked `type='ftop'`, even for standard shifts
   - This makes counter type unreliable for determining shift type
3. **Unknown handling** - Legacy data may lack both fields

**Important Edge Cases:**

- **FTOP member attends Standard ABCD shift:**
  - `shift.shift_type_id` = [2, 'Standard'] ← Use this!
  - `counter.event.type` = 'ftop' ← Don't use for shift type

- **Standard member attends FTOP shift:**
  - `shift.shift_type_id` = [1, 'FTOP'] ← Use this!
  - `counter.event.type` = 'standard' ← Don't use for shift type

**Code Reference:** `backend/app.py:98-138`

---

### 3.3 Week/Cycle System

**4-Week Rotating Cycle:**

The cooperative operates on a 4-week cycle with labeled weeks:

```
Cycle N:
  Week A (Week 1) - e.g., Jan 6-12, 2025
  Week B (Week 2) - e.g., Jan 13-19, 2025
  Week C (Week 3) - e.g., Jan 20-26, 2025
  Week D (Week 4) - e.g., Jan 27-Feb 2, 2025

Cycle N+1:
  Week A (Week 1) - e.g., Feb 3-9, 2025
  ...and so on
```

**Data Source:** `data/cycles_2025.json`

**Structure:**
```json
{
  "cycles": [
    {
      "cycle_number": 1,
      "start_date": "2025-01-06",
      "end_date": "2025-02-02",
      "weeks": [
        {
          "week_letter": "A",
          "start_date": "2025-01-06",
          "end_date": "2025-01-12"
        },
        {
          "week_letter": "B",
          "start_date": "2025-01-13",
          "end_date": "2025-01-19"
        },
        ...
      ]
    }
  ]
}
```

**How It Works:**

- Standard ABCD members are assigned to ONE week letter (e.g., "Week A")
- They work the same shift during that week of every cycle
- FTOP members can choose shifts from any week
- Week letters used for shift identification and scheduling

**Fields on shift.shift:**
```python
'week_number': int        # 1, 2, 3, or 4
'week_name': str          # 'A', 'B', 'C', or 'D'
```

**Code Reference:** `specs/features.md:235-247`

---

### 3.4 Shift States & Counter Impact

**State Transition Flow:**

```
draft → open → done
              ↓ absent
              ↓ excused
              ↓ cancel
```

**Counter Event Creation Matrix:**

| Registration State | Counter Event Created? | Point Change | Display Color | Icon |
|-------------------|------------------------|--------------|---------------|------|
| `done` | ✅ Yes | **+1** (attended) | Green | 🎯 |
| `absent` | ✅ Yes | **-1** or **-2** (missed) | Red | ❌ |
| `excused` | ❌ **No** | **0** (neutral) | Blue | ✓ |
| `open` | ❌ No (not yet) | **0** (pending) | Gray | 📋 |
| `draft` | ❌ No | **0** | Gray | - |
| `cancel` | ❌ No | **0** | Gray | - |

**Special Cases:**

1. **Late Arrival:**
   ```python
   state = 'done'           # Still counted as attended
   is_late = True           # Flag set to true
   counter_event.point_qty = +1  # Still earns positive points
   display = "Late" badge shown
   ```

2. **Excused During Leave:**
   ```python
   state = 'excused'
   # Shift falls within active leave period (leave.state='done')
   # No counter event created
   # No penalty applied
   display = "Covered by leave" indicator
   ```

3. **FTOP Shift Closing:**
   ```python
   # For FTOP shifts, use counter event date for timeline
   # (not shift.date_begin)

   if shift_type == 'ftop' and has_counter_event:
       timeline_date = counter_event.create_date
   else:
       timeline_date = shift.date_begin

   # This represents when FTOP shift was actually validated/closed
   ```

**Code Reference:** `backend/odoo_client.py:140-144`, `backend/app.py:350-356`

---

## 4. COUNTER/POINTS SYSTEM

### 4.1 Dual-Counter Architecture

**Fundamental Design:**

Each member maintains **TWO completely independent counters**:

```python
member.counters = {
    'ftop': {
        'type': 'ftop',
        'current_total': 0,      # Recalculated by application
        'events': [...]           # All events with type='ftop'
    },
    'standard': {
        'type': 'standard',
        'current_total': 0,      # Recalculated by application
        'events': [...]           # All events with type='standard'
    }
}
```

**Counter Usage by Member Type:**

| Member Type | Primary Counter | Secondary Counter | Usage Rules |
|-------------|----------------|-------------------|-------------|
| Standard ABCD | `standard` | `ftop` | Standard counter for assigned shifts + make-ups when counter < 0. FTOP counter for extra shifts when counter >= 0 |
| FTOP | `ftop` | N/A | All activity goes to FTOP counter only |

**Key Principles:**

1. **Registration Type Determines Counter:**
   The `type` field on `shift.registration` (and resulting `shift.counter.event`) indicates **which counter bucket the points go into**.

2. **Standard ABCD Members - Dynamic Counter Assignment:**
   ```python
   # When Standard ABCD member registers for extra shift:
   if member.standard_counter < 0:
       registration.type = 'standard'  # Make-up shift
       counter_event.type = 'standard'  # Points restore standard counter
   elif member.standard_counter >= 0:
       registration.type = 'ftop'       # Anticipatory extra shift
       counter_event.type = 'ftop'      # Points accumulate in FTOP counter
   ```

3. **FTOP Members - Always FTOP Counter:**
   ```python
   # FTOP members always use FTOP counter, regardless of shift type
   registration.type = 'ftop'
   counter_event.type = 'ftop'
   ```

**Important:** The shift's `shift_type_id` describes what TYPE of shift it is (FTOP technical vs Standard working shift), while the registration's `type` field determines which counter receives the points.

**Example Scenarios:**

**Scenario 1: FTOP Member Attends Standard Shift**
```python
member.shift_type = 'ftop'
shift.shift_type_id = [2, 'Standard']    # It's a standard working shift
registration.type = 'ftop'                # Registration type
counter_event.type = 'ftop'               # Points go to FTOP counter
```

**Scenario 2: Standard ABCD Member - Make-up Shift**
```python
member.shift_type = 'standard'
member.standard_counter = -2              # Needs make-up
shift.shift_type_id = [2, 'Standard']    # Standard working shift
registration.type = 'standard'            # Make-up registration
counter_event.type = 'standard'           # Points restore standard counter
```

**Scenario 3: Standard ABCD Member - Anticipatory Extra Shift**
```python
member.shift_type = 'standard'
member.standard_counter = 0               # Up to date, building buffer
shift.shift_type_id = [2, 'Standard']    # Standard working shift
registration.type = 'ftop'                # Extra shift registration
counter_event.type = 'ftop'               # Points accumulate in FTOP counter
```

**Scenario 4: FTOP Member - Technical FTOP Shift Closing**
```python
member.shift_type = 'ftop'
shift.shift_type_id = [1, 'FTOP']        # Technical FTOP shift (not real work)
registration.type = 'ftop'                # Automatic registration
registration.state = 'done'               # Auto-marked present
counter_event.type = 'ftop'
counter_event.point_qty = -1              # Cycle deduction
```

---

### 4.2 Counter Event Aggregation Algorithm

**The Problem:**

Multiple counter events can exist for a single shift:
- Initial event when shift closed: +1
- Admin adjustment for late arrival: -0.5
- Admin correction: +0.5
- Result: Multiple events for one shift instance

Additionally, Odoo's `sum_current_qty` field is unreliable and cannot be trusted.

**The Solution:**

The application implements a **chronological aggregation algorithm**:

```python
# STEP 1: Fetch ALL counter events (no limit)
all_events = odoo.get_member_counter_events(member_id)

# STEP 2: Sort chronologically (oldest first)
events_sorted = sorted(all_events, key=lambda x: x.get('create_date', ''))

# STEP 3: Separate into FTOP and Standard buckets
ftop_shift_map = {}       # shift_id → aggregated ftop data
standard_shift_map = {}   # shift_id → aggregated standard data
ftop_manual_events = []   # Manual events affecting ftop counter
standard_manual_events = []  # Manual events affecting standard counter

for event in events_sorted:
    shift_id = extract_shift_id(event.get('shift_id'))
    counter_type = event.get('type', 'standard')

    if shift_id:
        # Event has shift_id - aggregate with other events for same shift
        shift_map = ftop_shift_map if counter_type == 'ftop' else standard_shift_map

        if shift_id in shift_map:
            # Add to existing aggregate
            shift_map[shift_id]['point_qty'] += event.get('point_qty', 0)
            # Keep latest create_date
            if event['create_date'] > shift_map[shift_id]['create_date']:
                shift_map[shift_id]['create_date'] = event['create_date']
        else:
            # First event for this shift
            shift_map[shift_id] = {
                'point_qty': event.get('point_qty', 0),
                'create_date': event.get('create_date', ''),
                'type': counter_type
            }
    else:
        # Manual event with no shift_id
        if counter_type == 'ftop':
            ftop_manual_events.append(event)
        else:
            standard_manual_events.append(event)

# STEP 4: Combine all items chronologically
all_items = []

# Add aggregated shift events
for shift_id, data in ftop_shift_map.items():
    all_items.append({
        'type': 'shift',
        'counter_type': 'ftop',
        'shift_id': shift_id,
        'create_date': data['create_date'],
        'point_qty': data['point_qty']
    })

for shift_id, data in standard_shift_map.items():
    all_items.append({
        'type': 'shift',
        'counter_type': 'standard',
        'shift_id': shift_id,
        'create_date': data['create_date'],
        'point_qty': data['point_qty']
    })

# Add manual events
for event in ftop_manual_events:
    all_items.append({
        'type': 'manual',
        'counter_type': 'ftop',
        'create_date': event['create_date'],
        'point_qty': event['point_qty'],
        'original_event': event
    })

for event in standard_manual_events:
    all_items.append({
        'type': 'manual',
        'counter_type': 'standard',
        'create_date': event['create_date'],
        'point_qty': event['point_qty'],
        'original_event': event
    })

# STEP 5: Sort all items chronologically
all_items.sort(key=lambda x: x['create_date'])

# STEP 6: Calculate running totals for BOTH counters
ftop_running_total = 0
standard_running_total = 0

for item in all_items:
    # Update appropriate counter
    if item['counter_type'] == 'ftop':
        ftop_running_total += item['point_qty']
    else:
        standard_running_total += item['point_qty']

    # Store BOTH running totals at this point in time
    item['ftop_total'] = int(ftop_running_total)
    item['standard_total'] = int(standard_running_total)

    # For backward compatibility
    item['sum_current_qty'] = (
        int(ftop_running_total) if item['counter_type'] == 'ftop'
        else int(standard_running_total)
    )

# STEP 7: Map totals back to shift maps
# (So shifts can display their counter totals)
for item in all_items:
    if item['type'] == 'shift':
        shift_id = item['shift_id']
        if item['counter_type'] == 'ftop':
            ftop_shift_map[shift_id]['ftop_total'] = item['ftop_total']
            ftop_shift_map[shift_id]['standard_total'] = item['standard_total']
        else:
            standard_shift_map[shift_id]['standard_total'] = item['standard_total']
            standard_shift_map[shift_id]['ftop_total'] = item['ftop_total']
```

**Why This Works:**

1. **Chronological ordering** ensures totals are calculated in correct sequence
2. **Aggregation by shift_id** combines multiple events for same shift
3. **Separate buckets** maintain independence of FTOP vs Standard counters
4. **Dual totals** allow any event to show both counter values
5. **Manual event handling** preserves admin adjustments without shift_id

**Code Reference:** `backend/app.py:159-322`

---

### 4.3 Point Calculation Rules

**Standard Point Values:**

| Event Type | Points |
|------------|--------|
| Shift attended (`state='done'`) | **+1** |
| Shift missed (`state='absent'`) | **-2** (default penalty) |
| Shift excused (`state='excused'`) | **0** (no event created) |
| Manual adjustment | Variable (set by admin) |

**Absence Penalty with Holiday Relief:**

When a shift is missed (`state='absent'`), the system creates **two counter events**:

1. **Initial penalty:** `-2 points` (automatic)
2. **Holiday relief:** `+1` or `+2 points` (if `shift.holiday` active at shift time)

**Net result:** Effective penalty can be `-2`, `-1`, or `0` depending on holiday configuration.

**Holiday System (`shift.holiday` - "Assouplissement de présence"):**

```python
# Example: Christmas holiday configured
{
    'model': 'shift.holiday',
    'name': 'Christmas Period',
    'start_date': '2025-12-20',
    'end_date': '2025-12-27',
    'relief_points': 2  # Or 1, configurable per holiday
}

# Member misses shift on 2025-12-24
# Counter events created:
Event 1: {
    'shift_id': [123, 'Christmas Eve Shift'],
    'point_qty': -2,  # Base absence penalty
    'type': 'standard',
    'is_manual': False
}

Event 2: {
    'shift_id': [123, 'Christmas Eve Shift'],  # Same shift
    'point_qty': +2,  # Holiday relief (configured amount)
    'type': 'standard',
    'is_manual': False,
    'name': 'Holiday relief: Christmas Period'
}

# Net effect: -2 + 2 = 0 (no penalty during holiday)
```

**Important Notes:**
- Both events reference the same `shift_id`
- These events are aggregated together by the application's counter algorithm
- The holiday relief amount (+1 or +2) is configured per holiday
- Not all absences qualify - only those during active `shift.holiday` periods

**Display Format:**

```python
# Format: {sign}{point_qty} → {counter_total}

if point_qty > 0:
    display = f"+{point_qty} → {counter_total}"
    # Example: "+1 → 5"
else:
    display = f"{point_qty} → {counter_total}"
    # Example: "-2 → 3"
```

**Counter Type Indicators:**

```python
if counter_type == 'ftop':
    icon = '⏱️'
    label = 'FTOP' (English) or 'Vacation' (French)
else:
    icon = '📅'
    label = 'ABCD'

display = f"{icon} {label} {point_change}"
# Example: "⏱️ FTOP +1 → 5"
```

**Code Reference:** `frontend/src/App.jsx:557-567`

---

### 4.4 Manual Counter Events

**Characteristics:**

```python
{
    'is_manual': True,
    'shift_id': None or [id, name],  # May or may not reference shift
    'name': 'Manual adjustment - late arrival',  # Descriptive reason
    'point_qty': -2,  # Admin-specified value
    'type': 'ftop' or 'standard',
    'create_date': '2025-10-15 14:30:00'
}
```

**Use Cases:**

1. **Late arrival penalty** (beyond normal is_late flag)
2. **Exceptional circumstances** (emergency, technical issue)
3. **Administrative corrections** (data entry errors)
4. **Special bonuses** (extra shifts during holiday)

**Display Requirements:**

Manual events that appear as standalone timeline items:
- Must have `is_manual=True`
- AND must NOT be already aggregated into a shift
- Show with ⚖️ icon and "Manual Point Adjustment" title
- Display both counter totals at that moment

**Timeline Position:**

Manual events are inserted chronologically based on `create_date`, which may be:
- Same date as shift (concurrent adjustment)
- Different date (later correction)

**Code Reference:** `backend/app.py:375-395`

---

## 5. LEAVE SYSTEM

### 5.1 Leave Types

Defined in `shift.leave.type` model:

**Common Types:**

```python
{
    'name': 'Vacation',
    'is_anticipated': True  # Can be planned in advance
}

{
    'name': 'Sick Leave',
    'is_anticipated': False  # Emergency/unplanned
}

{
    'name': 'Parental Leave',
    'is_anticipated': True
}

# Additional types configured per cooperative
```

**Type Attributes:**

```python
'is_anticipated': bool              # Whether leave can be requested in advance
'state': str (selection)            # Leave type status
                                    # Special: 'On vacation' state affects counter behavior
```

**Important Leave Type States:**

- **Standard Leave Types:** When member is absent during leave, **no penalty applied**
- **"On vacation" Leave Type:** When member is absent during leave, **-1 point from FTOP counter** (if available)

---

### 5.2 Leave States & Workflow

**State Machine:**

```
draft
  ↓ (member submits)
waiting
  ↓ (admin approves)
done ←─────────────┐ (active)
  ↓ (or)           │
cancel ────────────┘ (cancelled)
```

**State Definitions:**

| State | Description | Affects Shifts? |
|-------|-------------|----------------|
| `draft` | Not yet submitted | ❌ No |
| `waiting` | Pending approval | ❌ No |
| `done` | Approved and active | ✅ Yes |
| `cancel` | Cancelled | ❌ No |

**Active Leave Criteria:**

```python
def is_active_leave(leave, current_date):
    return (
        leave.state == 'done' and
        leave.start_date <= current_date <= (leave.stop_date or date.max)
    )
```

---

### 5.3 Leave Impact on Shifts & Template Registration

**Automatic Template Registration Suspension:**

When a leave is approved (`state='done'`), the system automatically manages the member's shift template registration:

```python
# Leave approval triggers automatic action
leave.state = 'done'

# System creates new shift.template.registration
new_registration = {
    'partner_id': member.id,
    'shift_template_id': member.current_template_id,
    'date_begin': leave.start_date,
    'date_end': leave.stop_date,
    'state': 'waiting'  # Special "waiting" status
}

# "waiting" status = member not expected to participate
```

**Shift Closure Behavior During Leave:**

When a member's assigned shift is closed during an active leave:

**Standard Leave Types (Sick Leave, Parental Leave, etc.):**
```python
# Member marked absent for their regular shift
shift_registration.state = 'absent'

# But because template_registration.state = 'waiting':
# NO counter event created
# NO penalty points applied
# Absence is covered by leave
```

**"On Vacation" Leave Type:**
```python
# Member marked absent for their regular shift
shift_registration.state = 'absent'

# Special vacation behavior:
if member.ftop_counter > 0:
    # Counter event created
    counter_event.type = 'ftop'
    counter_event.point_qty = -1  # Uses one FTOP point
    # This allows member to "use" accumulated FTOP points for vacation
else:
    # No FTOP points available
    # NO counter event created
    # Absence still covered
```

**Member Workflow:**

1. **Before leave:** Member requests leave (creates `shift.leave` in `draft` state)
2. **Approval:** Admin approves leave (state → `done`)
3. **Automatic action:** System creates "waiting" template registration
4. **During leave:**
   - Regular shifts happen without member
   - Member marked absent but no standard counter penalty
   - "On vacation" type: -1 FTOP point if available
5. **After leave:** Template registration ends, member resumes normal participation

**Open-Ended Leaves:**

```python
{
    'non_defined_leave': True,
    'start_date': '2025-01-01',
    'stop_date': False,  # No defined end
    'state': 'done'
}

# All shifts excused until leave is manually stopped
```

---

### 5.4 Leave Timeline Events

The application creates **two timeline markers** for each leave:

**Leave Start Event:**

```json
{
  "type": "leave_start",
  "date": "2025-07-01",
  "leave_type": "Vacation",
  "leave_end": "2025-07-14",
  "leave_id": 123,
  "weekLetter": "A",
  "duringLeave": false
}
```

Display:
```
🏖️ Leave Started
Type: Vacation
Until: Jul 14, 2025
```

**Leave End Event:**

```json
{
  "type": "leave_end",
  "date": "2025-07-14",
  "leave_type": "Vacation",
  "leave_start": "2025-07-01",
  "leave_id": 123,
  "weekLetter": "B",
  "duringLeave": false
}
```

Display:
```
🔙 Leave Ended
Type: Vacation
Since: Jul 1, 2025
```

**Visual Styling:**

- Yellow/amber gradient background
- Yellow border
- Shows date range and leave type
- Inserted chronologically with other events

**Code Reference:** `backend/app.py:399-410`

---

## 6. BUSINESS RULES & LOGIC

### 6.1 Validation Rules

**Member Constraints:**

```python
# Associated people cannot own shares
if is_associated_people and total_partner_owned_share > 0:
    raise ValidationError("Associated people cannot own shares")

# Maximum associated people per member
if len(child_ids) > max_associated_people:
    raise ValidationError(f"Cannot exceed {max_associated_people} associated people")

# Minors must be under 18
if is_associated_people and age >= 18:
    raise ValidationError("Associated people must be under 18")
```

**Shift Registration Constraints:**

```python
# Cannot register for full shift
if shift.seats_available <= 0:
    raise ValidationError("Shift is full")

# Must be member in good standing
if not customer:  # Cannot purchase = cannot register
    raise ValidationError("Shopping privileges required to register for shifts")

# Respect max seats limit
if shift.seats_taken >= shift.seats_max:
    raise ValidationError("Maximum capacity reached")
```

**Share Constraints:**

```python
# When shares reach 0
if total_partner_owned_share == 0 and was_member:
    auto_unsubscribe_from_shifts()
    set_opt_out_marketing(True)
    cooperative_state = 'not_concerned'
```

---

### 6.2 Thresholds & Limits

**Counter Thresholds for Standard ABCD Members:**

Standard ABCD members can only have a counter value of **0 or negative**. The counter starts at 0 and decreases when shifts are missed.

```python
# State logic for Standard ABCD members
if counter == 0:
    cooperative_state = 'up_to_date'
elif counter < 0:
    # Counter is negative - determine state based on time and actions
    if just_went_negative or in_first_cycle_of_negative:
        cooperative_state = 'alert'
    elif counter < 0 and one_cycle_elapsed_since_alert:
        cooperative_state = 'suspended'  # Shopping privileges revoked
    elif suspended_and_requested_delay:
        cooperative_state = 'delay'  # Temporary shopping derogation during make-up shifts
```

**State Progression for Negative Counter:**

1. **Counter goes negative** → `alert` state (first cycle)
   - Member receives warning
   - Shopping privileges maintained
   - Must schedule make-up shift

2. **After one full cycle in alert** → `suspended` state
   - Shopping privileges **blocked**
   - Must resolve negative counter

3. **Member requests delay** → `delay` state (from suspended)
   - **Temporary shopping derogation** granted
   - Member has additional time to schedule make-up shifts
   - Returns to shopping privileges while catching up

4. **Counter returns to 0** → `up_to_date` state
   - Normal status restored

**Note:** The `blocked` state exists in the system but is not actively used in practice.

**FTOP Member Thresholds:**

FTOP members have a different counter system that allows positive values:

```python
# FTOP counter can be positive, zero, or negative
# Counter starts at 0 for new FTOP members
# Members encouraged to accumulate positive balance

# State logic for FTOP members (similar progression to Standard)
if counter >= 0:
    cooperative_state = 'up_to_date'  # Can be 0 or positive
elif counter < 0:
    # Same progression as Standard members
    if just_went_negative or in_first_cycle_of_negative:
        cooperative_state = 'alert'
    elif counter < 0 and one_cycle_elapsed_since_alert:
        cooperative_state = 'suspended'
    elif suspended_and_requested_delay:
        cooperative_state = 'delay'
```

**Key Differences from Standard:**
- FTOP counter can be **positive** (Standard: only 0)
- Positive balance encouraged for flexibility
- Same penalty structure (-2 for absence, holiday relief applies)
- Automatic -1 per cycle from technical FTOP shift closing

**API Query Limits:**

```python
# Purchases
limit = 50  # Most recent orders only
order = 'date_order desc'

# Shift registrations
limit = 50  # Most recent shifts only
order = 'date_begin desc'

# Counter events
limit = None  # ALL events required for accurate totals
order = 'create_date desc'

# Leaves
limit = None  # All approved leaves
filter = state == 'done'
```

**Code Reference:** `backend/odoo_client.py:107, 132, 235-256`

---

### 6.3 Special Handling

**Late Arrivals:**

```python
{
    'state': 'done',         # Still counted as attended
    'is_late': True,         # Late flag set
    'counter_event': {
        'point_qty': +1      # Still earns positive point
    }
}

# Display
"🎯 Shift Attended"
"⏰ Late"  # Additional badge
```

**FTOP Shift Closing:**

```python
# FTOP shifts use counter event date for timeline
# (not shift.date_begin)

if shift_type == 'ftop' and shift_id in shift_counter_map:
    counter_date = shift_counter_map[shift_id].get('create_date')
    if counter_date:
        event_date = counter_date  # When shift was validated/closed
    else:
        event_date = shift.date_begin  # Fallback
else:
    event_date = shift.date_begin  # Standard shifts use shift start

# Rationale: FTOP shifts are closed manually by coordinator
# The closing date is more meaningful than scheduled date
```

**Excused Absences During Leave:**

```python
# Shift registration
{
    'state': 'excused',
    'date_begin': '2025-07-05'  # Within leave period
}

# Leave record
{
    'state': 'done',
    'start_date': '2025-07-01',
    'stop_date': '2025-07-14'
}

# Result
- NO counter event created
- NO point penalty
- Display shows "🏖️ Covered by leave" badge
```

**Code Reference:**
- Late arrivals: `backend/odoo_client.py:144`
- FTOP closing: `backend/app.py:350-356`
- Excused during leave: Frontend display logic

---

## 7. DATA MODEL RELATIONSHIPS

### 7.1 Entity Relationship Diagram

```
res.partner (Member)
│
├─── 1:N → shift.registration (Shift Attendance Records)
│    │
│    └─── N:1 → shift.shift (Shift Instance)
│         │
│         ├─── N:1 → shift.template (Recurring Schedule)
│         │
│         └─── N:1 → shift.type (FTOP/Standard Type)
│
├─── 1:N → shift.counter.event (Point Changes)
│    │
│    └─── N:1 → shift.shift (Optional - None for manual)
│
├─── 1:N → shift.leave (Leave Periods)
│    │
│    └─── N:1 → shift.leave.type (Leave Type)
│
├─── 1:N → pos.order (Purchase History)
│
├─── 1:N → shift.template.registration (Template Assignments)
│    │
│    ├─── N:1 → shift.template (Recurring Schedule)
│    │
│    └─── 1:N → shift.template.registration.line (Assignment History)
│
└─── N:1 → res.partner (Parent Member)
     │
     └─── 1:N → res.partner (Associated People/Children)
```

### 7.2 Many2one Field Format

**Odoo Convention:**

Many2one fields are returned as tuples: `[id, name]`

**Examples:**

```python
shift_type_id = [1, 'FTOP']
shift_id = [11986, 'Monday Morning Team A']
type_id = [5, 'Vacation']
parent_id = [267, 'NIVET, Rémi']
```

**Handling in Code:**

```python
# Extract ID
if isinstance(shift_id, list):
    shift_id_int = shift_id[0]
else:
    shift_id_int = shift_id

# Extract name
if isinstance(type_id, list) and len(type_id) > 1:
    type_name = type_id[1]
else:
    type_name = None

# Check if field is set
if shift_id and shift_id != False:
    # Field has value
    pass
else:
    # Field is empty
    pass
```

### 7.3 Computed Field Dependencies

**Dependency Chain:**

```
total_partner_owned_share (from account.invoice.line)
  ↓
is_member (total > 0)
  ↓
is_worker_member (has worker shares)
  ↓
tmpl_reg_line_ids (active template registration lines)
  ↓
is_unsubscribed (no active lines)
  ↓
working_state (computed from counter)
  ↓
cooperative_state (combines is_unsubscribed, is_unpayed, working_state)
  ↓
customer (based on cooperative_state)
```

**Recomputation Triggers:**

- Share purchase/sale → recompute member status fields
- Template registration change → recompute is_unsubscribed
- Counter event → recompute working_state → cooperative_state
- State change → recompute customer flag

**Cron Jobs:**

```python
# Daily cron (typically 3am)
- Recompute is_unsubscribed for all members
- Update cooperative_state based on counters
- Generate upcoming shift instances
- Send reminder emails
```

---

**End of Membership System Specification**

This document provides a comprehensive reference for understanding how the Odoo membership and shift systems work at Superquinquin cooperative. For information about implementation details, API usage, and application architecture, refer to `CLAUDE.md`. For unknown areas requiring clarification, see `KNOWLEDGE_GAPS.md`.
