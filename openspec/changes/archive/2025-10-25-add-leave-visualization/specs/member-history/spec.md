## ADDED Requirements

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
The system SHALL display member history as a vertical timeline organized by cycles and weeks, with all events (purchases, shifts, and leaves) displayed chronologically.

#### Scenario: Timeline structure
- **WHEN** displaying member history
- **THEN** events SHALL be grouped by 4-week cycles
- **AND** within each cycle, events SHALL be grouped by weeks (A, B, C, D)
- **AND** each cycle SHALL have a unified gray background
- **AND** all event types SHALL be displayed in reverse chronological order (newest first)

#### Scenario: Event card display
- **WHEN** rendering events on the timeline
- **THEN** all events (purchases, shifts, leaves) SHALL be displayed as cards in document flow
- **AND** events SHALL be sorted by date in reverse chronological order within each week
- **AND** leave events SHALL use yellow styling with appropriate icons

#### Scenario: Date formatting
- **WHEN** displaying dates on the timeline
- **THEN** event dates SHALL use full format with year (e.g., "Oct 4, 2025")
- **AND** cycle date ranges SHALL use short format without year (e.g., "Oct 4 - Nov 1")
- **AND** leave event cards SHALL show start or end date with contextual information

#### Scenario: Empty timeline
- **WHEN** a member has no events or leaves
- **THEN** display empty state message
- **AND** provide guidance on what events would appear

#### Scenario: Loading state
- **WHEN** fetching history data including leaves
- **THEN** display loading indicator
- **AND** prevent interaction until data is loaded

#### Scenario: Error handling
- **WHEN** fetching leaves fails
- **THEN** display other events successfully fetched
- **AND** log error for debugging but don't block timeline display
