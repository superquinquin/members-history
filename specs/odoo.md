## **AwesomeFoodCoops Odoo Modules - Technical Documentation**

### **Repository Information**
- **GitHub**: https://github.com/AwesomeFoodCoops/odoo-production
- **Current Branch**: 12.0 (Superquinquin is likely using this)
- **Alternative Branch**: 9.0 (analyzed for this documentation)
- **License**: AGPL-3.0

---

## **Module 1: coop_membership**

### **Purpose**
Manages cooperative membership, member states, share ownership, and associated people (family members). This is the core membership management module for food cooperatives.

### **Key Models & Fields**

#### **res.partner (Extended)**

**Membership Type Fields:**
- `is_member` (Boolean, computed): Partner has shares > 0
- `is_former_member` (Boolean, computed): Had shares but now 0
- `is_associated_people` (Boolean, computed): Family member of a member (via `parent_id`)
- `is_former_associated_people` (Boolean, computed): Was associated with a former member
- `is_interested_people` (Boolean, computed): Not member, not associated, not supplier
- `is_worker_member` (Boolean, computed): Has worker capital shares
- `is_designated_buyer` (Boolean): Can be a designated buyer
- `is_minor_child` (Boolean): Child under 18 years old

**Share & Capital Fields:**
- `partner_owned_share_ids` (One2many → `res.partner.owned.share`): All owned shares
- `total_partner_owned_share` (Integer, computed, stored): Total number of shares owned
- `fundraising_partner_type_ids` (Many2many): Fundraising categories

**State & Status Fields:**
- `cooperative_state` (Selection): Member status - values include:
  - `'not_concerned'`: Not a member
  - `'unsubscribed'`: Unsubscribed from shifts
  - `'exempted'`: Exempted from shifts
  - `'vacation'`: On vacation
  - `'up_to_date'`: Up to date with shifts
  - `'alert'`: Alert status
  - `'suspended'`: Suspended
  - `'delay'`: Delayed
  - `'blocked'`: Blocked
  - `'unpayed'`: Unpayed shares
- `working_state` (Selection): Same selection as `cooperative_state`
- `is_unpayed` (Boolean): Has late payments for capital subscriptions
- `is_unsubscribed` (Boolean, computed): Not linked to shift template registration
- `unsubscription_date` (Date, computed): When unsubscribed from shifts

**Family & Associated People:**
- `parent_id` (Many2one → `res.partner`): Parent member (for associated people)
- `child_ids` (One2many): Children/associated people
- `nb_associated_people` (Integer, computed): Number of associated people
- `parent_member_num` (Integer): Parent's barcode number

**Personal Information:**
- `sex` (Selection): `'m'`, `'f'`, `'o'`
- `birthdate` (Date): Birth date
- `age` (Integer, computed): Calculated age
- `is_deceased` (Boolean)
- `date_of_death` (Date)
- `is_underclass_population` (Boolean, computed): From fundraising types

**Badge & Identification:**
- `temp_coop_number` (Char): Temporary cooperative number
- `barcode_base` (Integer): Member number
- `badge_distribution_date` (Date)
- `badge_print_date` (Date)
- `badge_to_distribute` (Boolean, computed)

**Shift Information** (from coop_shift integration):
- `shift_type` (Selection, computed): `'standard'` or from parent
- `current_template_name` (Char, computed): Current shift template name
- `leader_ids` (Many2many → `res.partner`): Shift team leaders
- `tmpl_reg_ids` (One2many): Template registrations
- `tmpl_reg_line_ids` (One2many): Template registration lines
- `registration_ids` (One2many): Shift registrations
- `leave_ids` (One2many): Shift leaves

**Other Fields:**
- `welcome_email` (Boolean): Welcome email sent
- `deactivated_date` (Date): When account deactivated
- `force_customer` (Boolean): Force customer access
- `contact_origin_id` (One2many → `event.registration`): Contact origin events
- `contact_us_message` (Html): Contact message
- `inform_ids` (Many2many → `res.partner.inform`): Informations

### **Key Methods**

**Computed Field Methods:**
- `_compute_is_member()`: Checks if `total_partner_owned_share > 0`
- `_compute_is_associated_people()`: Checks `parent_id.is_member` and not own shares
- `_compute_is_unsubscribed()`: Checks active template registration lines
- `_compute_cooperative_state()`: Determines state from working_state, unpayed, unsubscribed
- `_compute_customer()`: Sets customer=True if state in allowed list or force_customer

**Business Logic:**
- `check_designated_buyer()`: Sets deactivation date based on company settings
- `send_welcome_email()`: Sends welcome email template
- `get_next_shift()` / `get_next_shift_date()`: Find upcoming shifts
- `_generate_associated_barcode()`: Auto-generate barcode for associated people
- `_update_when_number_of_shares_reaches_0()`: Handles member → former member transition

**CRON Jobs:**
- `update_is_unsubscribed()`: Updates unsubscription status nightly
- `send_welcome_emails()`: Sends welcome emails to new worker members
- `deactivate_designated_buyer()`: Deactivates expired designated buyers
- `cron_update_mirror_children()`: Converts minor children to adults at 18
- `cron_send_notify_mirror_children_email()`: Notifies before 18th birthday

### **Related Models**

#### **res.partner.owned.share**
- `partner_id` (Many2one → `res.partner`)
- `owned_share` (Integer): Number of shares owned
- `category_id` (Many2one): Share category
- `related_invoice_ids` (One2many): Associated invoices

#### **capital_fundraising_category**
- Categories for share types (A, B, C shares, etc.)
- `is_worker_capital_category` (Boolean): Marks worker shares

---

## **Module 2: coop_shift**

### **Purpose**
Manages cooperative member shift scheduling, shift templates, attendance tracking, and shift counter (credit/debit) system. Members must work shifts to maintain good standing.

### **Key Models**

#### **shift.template**
Represents recurring shift schedules (e.g., "Monday 9-12 Team A")

**Fields:**
- `name` (Char): Template name
- `shift_type_id` (Many2one → `shift.type`): Shift type
- `user_ids` (Many2many → `res.partner`): Shift leaders/coordinators
- `removed_user_ids` (Many2many): Former leaders
- `registration_ids` (One2many → `shift.template.registration`): Member registrations
- `week_number` (Integer): Which week(s) in cycle (for rotating schedules)
- `start_datetime` (Datetime): Template start time
- `end_datetime` (Datetime): Template end time
- `seats_max` (Integer): Maximum participants
- `seats_available` (Integer, computed): Available spots

#### **shift.template.registration**
Links members to recurring shift templates

**Fields:**
- `partner_id` (Many2one → `res.partner`): The member
- `shift_template_id` (Many2one → `shift.template`): The shift template
- `date_begin` (Date): Registration start date
- `date_end` (Date): Registration end date (if leaving team)
- `is_current` (Boolean, computed): Currently active
- `is_future` (Boolean, computed): Starts in future
- `line_ids` (One2many → `shift.template.registration.line`): History of registrations

#### **shift.template.registration.line**
Historical record of template membership periods

**Fields:**
- `shift_template_id` (Many2one)
- `partner_id` (Many2one)
- `date_begin` (Date)
- `date_end` (Date)

#### **shift.shift**
Individual shift instances (generated from templates)

**Fields:**
- `name` (Char): Shift name
- `shift_template_id` (Many2one → `shift.template`): Source template
- `date_begin` (Datetime): Shift start
- `date_end` (Datetime): Shift end
- `shift_ticket_ids` (One2many → `shift.ticket`): Shift tickets
- `registration_ids` (One2many → `shift.registration`): Registrations
- `state` (Selection): `'draft'`, `'confirm'`, `'done'`, `'cancel'`
- `seats_max` (Integer)
- `seats_available` (Integer, computed)
- `user_ids` (Many2many): Shift leaders

#### **shift.registration**
Member registration for specific shift instance

**Fields:**
- `partner_id` (Many2one → `res.partner`)
- `shift_id` (Many2one → `shift.shift`)
- `shift_ticket_id` (Many2one → `shift.ticket`)
- `template_created` (Boolean): Auto-created from template
- `date_begin` (Datetime)
- `date_end` (Datetime)
- `state` (Selection): `'draft'`, `'open'`, `'done'`, `'cancel'`, `'absent'`, `'excused'`
- `is_late` (Boolean): Arrived late
- `date_closed` (Datetime): When marked done/absent

#### **shift.counter.event**
Tracks shift credits/debits for members

**Fields:**
- `partner_id` (Many2one → `res.partner`)
- `type` (Selection): `'standard'`, `'ftop'`, etc.
- `point_qty` (Integer): Points added/removed
- `shift_id` (Many2one): Related shift
- `registration_id` (Many2one): Related registration
- `date` (Datetime)
- `notes` (Text)

#### **shift.leave**
Member absences/leaves from shifts

**Fields:**
- `partner_id` (Many2one → `res.partner`)
- `type_id` (Many2one → `shift.leave.type`): Leave type
- `start_date` (Date)
- `stop_date` (Date)
- `state` (Selection): `'draft'`, `'waiting'`, `'done'`, `'cancel'`
- `non_defined_leave` (Boolean): Open-ended leave

#### **shift.leave.type**
Types of leaves (vacation, sick, parental, etc.)

**Fields:**
- `name` (Char)
- `is_anticipated` (Boolean): Can be planned in advance

#### **shift.extension**
Temporary exemptions from shifts

**Fields:**
- `partner_id` (Many2one)
- `type_id` (Many2one → `shift.extension.type`)
- `start_date` (Date)
- `stop_date` (Date)
- `extension_qty` (Integer): Number of weeks/months

---

## **Key Relationships & Business Logic**

### **Member State Computation**

```python
cooperative_state logic:
- If is_associated_people → inherit parent's cooperative_state
- If is_worker_member:
  - If is_unsubscribed → 'unsubscribed'
  - If is_unpayed → 'unpayed'  
  - Else → working_state value
- Else → 'not_concerned'

customer (buying access):
- True if cooperative_state in ['up_to_date', 'alert', 'delay', 'exempted']
- OR force_customer = True
```

### **Shift Counter System**
- Members earn/lose shift points based on attendance
- `shift.counter.event` records all point changes
- Attendance states affect working_state:
  - `'done'`: Shift completed (+points)
  - `'absent'`: Missed shift (-points)
  - `'excused'`: Excused absence (no penalty)

### **Template → Shift Generation**
- Shift templates generate actual `shift.shift` instances
- Templates create `shift.registration` records with `template_created=True`
- Cron jobs likely generate future shifts from templates

### **Important Constraints**
1. Associated people cannot have shares (`total_partner_owned_share > 0`)
2. Minor children must be under 18 (validated on birthdate)
3. Maximum number of associated people per member (configurable)
4. When shares reach 0: auto-unsubscribe from shifts, set `opt_out=True`

---

## **Database Tables Summary**

**From your odoo_schema.sql:**
- `res_partner`: Extended with all membership fields
- `pos_order`: Point of sale orders (already used for purchase history)
  - `partner_id`: Customer
  - `date_order`: Order date
  - `state`: Order state
  - `amount_total`: Total amount

**Additional tables from modules:**
- `res_partner_owned_share`
- `shift_template`
- `shift_template_registration`  
- `shift_template_registration_line`
- `shift_shift`
- `shift_registration`
- `shift_counter_event`
- `shift_leave`
- `shift_leave_type`
- `shift_extension`
- `shift_extension_type`
- `shift_ticket`
- `shift_type`

---

## **For Future Feature Implementation**

### **Shift History Timeline Events**
To add shift participation to the timeline:

```python
# In odoo_client.py
def get_member_shift_history(self, partner_id: int, limit: int = 50):
    domain = [
        ('partner_id', '=', partner_id),
        ('state', 'in', ['done', 'absent', 'excused'])
    ]
    fields = ['id', 'date_begin', 'date_end', 'state', 'shift_id', 'is_late']
    results = self.search_read('shift.registration', domain, {
        'fields': fields,
        'limit': limit,
        'order': 'date_begin desc'
    })
    return results
```

Event types for timeline:
- **Shift Attended**: `state='done'`, icon 🎯
- **Shift Missed**: `state='absent'`, icon ❌
- **Shift Excused**: `state='excused'`, icon ✓

### **Member Status Information**
For member details display:
- `cooperative_state`: Display current status badge
- `shift_type`: Show if member is standard shift or other type
- `current_template_name`: Show which team/shift they're on
- `total_partner_owned_share`: Show number of shares
- `nb_associated_people`: Show family members count

