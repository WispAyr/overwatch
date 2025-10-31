# Alarm Manager GUI - Complete Feature Guide

## Overview

The Alarm Manager GUI provides comprehensive alarm lifecycle management through an intuitive Kanban-style interface with advanced features for filtering, bulk operations, and detailed alarm management.

## Features

### 1. Kanban Board View

The main interface displays alarms across all lifecycle states:

- **NEW** - Newly created alarms awaiting acknowledgment
- **TRIAGE** - Acknowledged alarms under initial investigation
- **SNOOZED** - Temporarily snoozed alarms
- **ACTIVE** - Alarms being actively worked on
- **CONTAINED** - Alarms where the immediate threat is contained
- **RESOLVED** - Resolved alarms pending closure
- **SUPPRESSED** - Suppressed/false positive alarms
- **CLOSED** - Permanently closed alarms

Each lane shows:
- Alarm count badge
- Real-time SLA timers
- Quick action buttons
- Severity color coding

### 2. Alarm Detail Modal

Click any alarm card to open a comprehensive detail modal with:

#### Information Panel
- Complete alarm metadata (ID, group key, tenant, site)
- Assignment details
- Confidence score
- Runbook reference
- Escalation policy
- Created/updated timestamps

#### State Management
- Valid state transitions based on current state
- Snooze capability (from TRIAGE state)
- Suppress capability (from any non-terminal state)
- Re-open capability (RESOLVED → ACTIVE)

#### Assignment
- Assign/reassign to users
- Current assignee display

#### Severity Management
- Manual severity escalation/de-escalation
- Dropdown selection: info, minor, major, critical
- Severity change history tracking

#### Runbook & Escalation
- Attach runbook IDs
- Set escalation policies
- Update or clear values

#### Watchers
- Add watchers (users to notify of updates)
- Remove watchers
- Visual watcher list with inline removal

#### Notes
- Add timestamped notes
- User attribution for each note
- Persistent note history

#### Correlated Events
- List of all events correlated to this alarm
- Event details: ID, type, timestamp, severity
- Direct event linking

#### History Timeline
- Complete audit trail
- All state transitions
- Assignment changes
- Note additions
- Severity changes
- Watcher modifications
- User attribution
- Timestamped entries

### 3. Bulk Operations

Enable bulk mode to select and operate on multiple alarms simultaneously:

#### Activation
- Click "Bulk Mode" button to enable
- Checkboxes appear on all alarm cards
- Bulk toolbar displays with action buttons

#### Selection
- Click checkboxes to select individual alarms
- "Select All" button to select all visible alarms
- "Deselect All" to clear selection
- Selection count display

#### Bulk Actions
- **Bulk Transition** - Move selected alarms to new state
- **Bulk Assign** - Assign all selected to a user
- **Bulk Severity** - Update severity for all selected
- Progress feedback during bulk operations

### 4. Search & Filtering

#### Quick Search
- Real-time text search across:
  - Alarm IDs
  - Group keys
  - Assignee names
  - Site names
- Results update as you type

#### Advanced Filters
Multiple filter criteria:

**State Filter**
- Multi-select checkbox for states
- Show only alarms in selected states

**Severity Filter**
- Multi-select checkbox for severities
- Filter by critical, major, minor, info

**Assignee Filter**
- Text search for assignee name
- Special "unassigned" keyword for unassigned alarms

**Date Range Filter**
- Date from (show alarms created after)
- Date to (show alarms created before)
- Supports date-time pickers

**Filter Actions**
- Apply filters button
- Clear all filters button
- Filter state persists during session

### 5. Export Functionality

Export alarms for external analysis:

#### Export Formats
- **JSON** - Full alarm data structure
- **CSV** - Tabular format for spreadsheets

#### Export Scope
- Export all alarms (if none selected)
- Export selected alarms (in bulk mode)

#### Exported Fields (CSV)
- Alarm ID
- State
- Severity
- Site
- Assignee
- Created timestamp
- Updated timestamp

### 6. Real-time Features

#### Live Updates
- WebSocket integration for instant alarm updates
- Auto-refresh on alarm creation
- Auto-refresh on state transitions
- Auto-refresh on assignment changes

#### SLA Timers
- Live countdown timers on each alarm
- Visual warnings (yellow) when approaching SLA
- Visual alerts (red) when SLA breached
- Update every second
- Different SLA targets per severity:
  - **Critical**: Triage 2min, Active 5min, Contained 15min
  - **Major**: Triage 5min, Active 15min, Contained 30min
  - **Minor**: Triage 15min, Active 60min, Contained 240min
  - **Info**: Triage 60min, Active 240min, Contained 480min

### 7. Keyboard Shortcuts

(To be implemented)
- `Ctrl/Cmd + F` - Focus search
- `Ctrl/Cmd + B` - Toggle bulk mode
- `Ctrl/Cmd + A` - Select all (in bulk mode)
- `Escape` - Close modal/clear selection

## Usage Workflows

### Quick Alarm Triage
1. View NEW lane
2. Click alarm to see details
3. Review correlated events
4. Click "Acknowledge" to move to TRIAGE
5. Click "Assign to Me" to take ownership
6. Transition to ACTIVE when starting work

### Bulk State Transition
1. Enable "Bulk Mode"
2. Select multiple alarms
3. Click "Bulk Transition"
4. Choose target state
5. Enter note for audit trail
6. Confirm action

### Snoozing False Positives
1. Open alarm detail
2. Click "SNOOZE" button
3. Enter snooze duration in minutes
4. Alarm moves to SNOOZED lane
5. Auto-returns to TRIAGE after timeout

### Suppressing Invalid Alarms
1. Open alarm detail
2. Click "SUPPRESS" button
3. Enter reason for suppression
4. Alarm moves to SUPPRESSED (terminal state)

### Re-opening Resolved Alarms
1. Find alarm in RESOLVED lane
2. Click to open details
3. Click "ACTIVE" transition button
4. Enter note explaining re-opening
5. Alarm returns to ACTIVE state

### Escalating Severity
1. Open alarm detail
2. Use severity dropdown
3. Select higher severity
4. Click "Update"
5. History records severity change
6. SLA timers adjust automatically

### Adding Watchers
1. Open alarm detail
2. Scroll to Watchers section
3. Enter username
4. Click "Add"
5. Watcher receives notifications on updates

### Exporting for Reports
1. (Optional) Apply filters for specific date range/severity
2. (Optional) Enter bulk mode and select specific alarms
3. Click "Export" button
4. Choose format (JSON or CSV)
5. File downloads with timestamp

## API Integration

All GUI operations call backend REST APIs:

- `GET /api/alarms` - List alarms with filters
- `GET /api/alarms/{id}?include_history=true` - Get alarm details
- `POST /api/alarms/{id}/ack` - Acknowledge alarm
- `POST /api/alarms/{id}/assign` - Assign alarm
- `POST /api/alarms/{id}/transition` - State transition
- `POST /api/alarms/{id}/notes` - Add note
- `POST /api/alarms/{id}/severity` - Update severity
- `POST /api/alarms/{id}/runbook` - Update runbook
- `POST /api/alarms/{id}/escalation` - Update escalation policy
- `POST /api/alarms/{id}/watchers` - Add watcher
- `DELETE /api/alarms/{id}/watchers/{user}` - Remove watcher

## Technical Details

### State Machine
The GUI enforces valid state transitions:

```
NEW → [TRIAGE, SUPPRESSED]
TRIAGE → [ACTIVE, SNOOZED, SUPPRESSED, RESOLVED]
SNOOZED → [TRIAGE, SUPPRESSED]
ACTIVE → [CONTAINED, RESOLVED, SUPPRESSED]
CONTAINED → [RESOLVED, ACTIVE, SUPPRESSED]
RESOLVED → [CLOSED, ACTIVE, SUPPRESSED]
CLOSED → [] (terminal)
SUPPRESSED → [] (terminal)
```

### Event Correlation
- Alarms automatically correlate events by group key
- Group key format: `tenant:site:area:event_type`
- Correlated events shown in alarm detail
- Event count displayed

### Auto-escalation
- Backend automatically escalates severity when confidence > 85%
- GUI reflects auto-escalations in real-time
- History tracks auto-escalation events

## Configuration

No configuration required - all features work out of the box.

Optional customization:
- SLA timers (backend: `alarms/state_machine.py`)
- Severity levels (backend: `alarms/manager.py`)
- Escalation policies (future feature)

## Future Enhancements

Planned features:
- Keyboard shortcuts
- Custom views/dashboards
- Alarm templates
- Notification preferences per user
- Mobile-responsive layout
- Dark/light theme toggle
- Alarm metrics/analytics dashboard
- Integration with external ticketing systems
- Automated escalation policies
- SLA violation alerts
- Alarm routing rules


