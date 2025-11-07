# member-history Specification

## Purpose
TBD - created by archiving change add-leave-visualization. Update Purpose after archive.
## Requirements
### Requirement: Leave Period Visualization
The system SHALL display member leave periods as timeline events showing leave start and end dates.

#### Scenario: Member with leave period
- **WHEN** a member has done leaves in their history
- **THEN** "Leave Started" events SHALL appear at the start_date position in the timeline
- **AND** "Leave Ended" events SHALL appear at the stop_date position in the timeline
- **AND** each leave event SHALL display the leave type name
- **AND** leave start events SHALL show the end date with "Until: <date>"
- **AND** leave end events SHALL show the start date with "Since: <date>"
- **AND** leave events SHALL use yellow styling with 🏖️ icon for start and 🔙 icon for end

#### Scenario: Leave spanning multiple weeks
- **WHEN** a leave period spans multiple weeks within a cycle
- **THEN** the leave start event SHALL appear in its week
- **AND** the leave end event SHALL appear in its week
- **AND** both events SHALL be sorted chronologically with other events

#### Scenario: Leave spanning multiple cycles
- **WHEN** a leave period spans multiple cycles
- **THEN** the leave start event SHALL appear in the cycle containing start_date
- **AND** the leave end event SHALL appear in the cycle containing stop_date
- **AND** events SHALL be sorted chronologically within their respective cycles

#### Scenario: Member with no leaves
- **WHEN** a member has no leave records with state='done'
- **THEN** no leave events SHALL be displayed
- **AND** the timeline SHALL display normally without leave context

### Requirement: Leave Data Fetching
The backend SHALL fetch member leave data from Odoo and include it in the history API response.

#### Scenario: Fetch done leaves
- **WHEN** the history endpoint is called for a member
- **THEN** the system SHALL query the `shift.leave` model
- **AND** filter by partner_id matching the member
- **AND** filter by state='done'
- **AND** fetch fields: id, start_date, stop_date, type_id (with name), state

#### Scenario: Include leaves in API response
- **WHEN** leaves are fetched successfully
- **THEN** the response SHALL include a leaves array
- **AND** each leave SHALL have: id, start_date, stop_date, leave_type, state

#### Scenario: No limit on leave records
- **WHEN** fetching leave history
- **THEN** ALL done leaves SHALL be returned
- **AND** no pagination or limit SHALL be applied

### Requirement: Events During Leave Context
The system SHALL identify and visually indicate events that occurred during leave periods.

#### Scenario: Detect purchases during leave
- **WHEN** a purchase event date falls within a leave period
- **THEN** the purchase card SHALL display normally
- **AND** the system SHALL track that this event occurred during leave

#### Scenario: Detect shifts during leave
- **WHEN** a shift event date falls within a leave period
- **THEN** the shift card SHALL display normally
- **AND** the system SHALL indicate this shift was during a leave period

#### Scenario: Visual indicator for events during leave
- **WHEN** rendering an event that occurred during a leave period
- **THEN** the event card SHALL include a subtle visual indicator
- **AND** the indicator SHALL not obscure the event's primary information

### Requirement: Leave-Covered Shift Styling
The system SHALL apply distinct styling to shift events that were excused or absent during leave periods.

#### Scenario: Excused shift during leave
- **WHEN** a shift with state='excused' occurred during a leave period
- **THEN** the shift card SHALL use a muted or dimmed styling
- **AND** the card SHALL indicate the absence was covered by leave

#### Scenario: Absent shift during leave
- **WHEN** a shift with state='absent' occurred during a leave period
- **THEN** the shift card SHALL indicate this was covered by leave
- **AND** the styling SHALL differ from regular absent shifts

#### Scenario: Attended shift during leave
- **WHEN** a shift with state='done' occurred during a leave period
- **THEN** the shift card SHALL display normally with done styling
- **AND** a note SHALL indicate this was attended despite leave

### Requirement: Timeline UI with Leave Events
The system SHALL display member history as a vertical timeline organized by cycles and weeks, with all events (purchases, shifts, leaves, and counter changes) displayed chronologically.

#### Scenario: Timeline structure
- **WHEN** displaying member history
- **THEN** events SHALL be grouped by 4-week cycles
- **AND** within each cycle, events SHALL be grouped by weeks (A, B, C, D)
- **AND** each cycle SHALL have a unified gray background
- **AND** all event types (purchases, shifts, leaves, manual counter changes) SHALL be displayed in reverse chronological order (newest first)

#### Scenario: Event card display
- **WHEN** rendering events on the timeline
- **THEN** all events (purchases, shifts, leaves, manual counter changes) SHALL be displayed as cards in document flow
- **AND** events SHALL be sorted by date in reverse chronological order within each week
- **AND** leave events SHALL use yellow styling with appropriate icons
- **AND** manual counter events SHALL use green/red styling based on point direction

#### Scenario: Date formatting
- **WHEN** displaying dates on the timeline
- **THEN** event dates SHALL use full format with year (e.g., "Oct 4, 2025")
- **AND** cycle date ranges SHALL use short format without year (e.g., "Oct 4 - Nov 1")
- **AND** leave event cards SHALL show start or end date with contextual information
- **AND** counter event cards SHALL show the create_date

#### Scenario: Empty timeline
- **WHEN** a member has no events or leaves or counter changes
- **THEN** display empty state message
- **AND** provide guidance on what events would appear

#### Scenario: Loading state
- **WHEN** fetching history data including leaves and counter events
- **THEN** display loading indicator
- **AND** prevent interaction until data is loaded

#### Scenario: Error handling
- **WHEN** fetching leaves or counter events fails
- **THEN** display other events successfully fetched
- **AND** log error for debugging but don't block timeline display

### Requirement: Counter Event Data Fetching
The backend SHALL fetch member shift counter events from Odoo and include them in the history API response.

#### Scenario: Fetch counter events for member
- **WHEN** the history endpoint is called for a member
- **THEN** the system SHALL query the `shift.counter.event` model
- **AND** filter by partner_id matching the member
- **AND** fetch fields: id, create_date, point_qty, sum_current_qty, shift_id, is_manual, name, type
- **AND** fetch ALL counter events without limit
- **AND** order by create_date ascending for calculation purposes

#### Scenario: Calculate running totals with separate counter types
- **WHEN** counter events are fetched from Odoo
- **THEN** the system SHALL recognize that members have TWO separate counters:
  - FTOP counter (type='ftop')
  - ABCD/Standard counter (type='standard')
- **AND** calculate running totals separately for each counter type
- **AND** start each counter with an initial balance of 0
- **AND** process events chronologically by create_date
- **AND** update only the counter matching the event's type field
- **AND** each event SHALL store both counter totals at that point in time:
  - ftop_total: The FTOP counter balance after this event
  - standard_total: The ABCD counter balance after this event
  - sum_current_qty: The active counter's total (for backward compatibility)
- **AND** handle both automatic and manual counter events in the calculation

#### Scenario: Member transitions between counter types
- **WHEN** a member has counter events of both types (ftop and standard)
- **THEN** the system SHALL maintain separate running totals for each type
- **AND** FTOP events SHALL only affect the ftop_total
- **AND** Standard events SHALL only affect the standard_total
- **AND** display the counter type with a visual indicator:
  - ⏱️ for FTOP counter events
  - 📅 for ABCD/Standard counter events
- **AND** show the relevant total based on the event's counter type

#### Scenario: Link counter events to shifts
- **WHEN** a counter event has a shift_id
- **THEN** the system SHALL identify it as an automatic shift-related counter change
- **AND** associate it with the corresponding shift event
- **AND** include the calculated running total

#### Scenario: Identify manual counter events
- **WHEN** a counter event has is_manual=True or has no shift_id
- **THEN** the system SHALL identify it as a manual intervention
- **AND** treat it as an independent timeline event
- **AND** include the calculated running total

### Requirement: Counter Display in Shift Events
The system SHALL display automatic counter changes inline within shift event cards when the counter change is linked to a shift.

#### Scenario: Shift with automatic counter change
- **WHEN** displaying a shift event that has an associated counter event
- **THEN** the shift card SHALL display the counter change information right-aligned
- **AND** show the point quantity with +/- sign (e.g., "+2" or "-2")
- **AND** show the running total in parentheses (e.g., "(Total: 5)")
- **AND** use green styling for positive point_qty
- **AND** use red styling for negative point_qty

#### Scenario: Shift without counter event
- **WHEN** displaying a shift event with no associated counter event
- **THEN** the shift card SHALL display normally without counter information

#### Scenario: Counter change display format
- **WHEN** rendering counter information in a shift card
- **THEN** the display SHALL show: "[icon] {+/-}X → Y"
- **AND** icon is ⏱️ for FTOP or 📅 for ABCD/Standard
- **AND** X is the point_qty value
- **AND** Y is the appropriate counter total (ftop_total for FTOP events, standard_total for Standard events)
- **AND** the text SHALL be aligned to the right side of the card

### Requirement: Manual Counter Events Timeline Display
The system SHALL display manual counter interventions as dedicated timeline events grouped by cycles and weeks.

#### Scenario: Manual counter event display
- **WHEN** a manual counter event is displayed on the timeline
- **THEN** it SHALL appear as a dedicated event card
- **AND** use a distinctive icon (⚖️ for manual adjustment)
- **AND** display the counter type icon (⏱️ for FTOP or 📅 for ABCD)
- **AND** display the point quantity with +/- sign
- **AND** display the running total after the change for the appropriate counter type
- **AND** display the event name/description
- **AND** use green gradient styling for positive point_qty
- **AND** use red gradient styling for negative point_qty

#### Scenario: Manual counter event grouping
- **WHEN** organizing manual counter events in the timeline
- **THEN** they SHALL be grouped by cycle and week like other events
- **AND** sorted chronologically by create_date within their week
- **AND** mixed with other event types (purchases, shifts, leaves) in date order

#### Scenario: Counter event date formatting
- **WHEN** displaying the date for a counter event
- **THEN** use the create_date field for timeline positioning
- **AND** format using the standard event date format with year

### Requirement: Counter Event Styling
The system SHALL apply distinct visual styling to counter events based on whether points were added or removed.

#### Scenario: Positive counter change styling
- **WHEN** a counter event has point_qty > 0
- **THEN** the point display SHALL use green text color
- **AND** manual counter event cards SHALL use green gradient background/border
- **AND** the icon or indicator SHALL suggest positive change

#### Scenario: Negative counter change styling
- **WHEN** a counter event has point_qty < 0
- **THEN** the point display SHALL use red text color
- **AND** manual counter event cards SHALL use red gradient background/border
- **AND** the icon or indicator SHALL suggest negative change

#### Scenario: Zero counter change
- **WHEN** a counter event has point_qty = 0
- **THEN** the point display SHALL use neutral gray styling
- **AND** display the event without positive/negative indicators

