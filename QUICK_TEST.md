# 🚀 Quick Test Guide - Alarm Centre

## What's Been Built

The complete **Alarm Centre** is now functional with:
- ✅ **Alarm Desk UI** - Kanban board with live SLA timers
- ✅ **Rules Engine** - YAML-based automation
- ✅ **Full API** - REST + WebSocket
- ✅ **Metrics** - Prometheus endpoint
- ✅ **Integrations** - Email, SMS, PagerDuty, webhooks

## Start the System

```bash
cd /Users/ewanrichardson/Development/overwatch

# Install new dependencies
source venv/bin/activate
pip install prometheus-client aiosmtplib twilio

# Start backend
python backend/main.py &

# Start dashboard (separate terminal)
cd frontend
python3 -m http.server 7001
```

## Access the GUI

**Dashboard:** http://localhost:7001

Click the **"Alarms"** tab in the navigation to see the Alarm Desk!

## Test It Out

### 1. View the Alarm Desk

Go to http://localhost:7001 → Click **"Alarms"**

You'll see 5 Kanban lanes:
- 🔴 NEW
- 🟡 TRIAGE  
- 🟠 ACTIVE
- 🔵 CONTAINED
- 🟢 RESOLVED

### 2. Create a Test Alarm

```bash
# Create an event (auto-creates alarm)
curl -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-'$(date +%s)'",
    "tenant": "test-org",
    "site": "headquarters",
    "source": {
      "type": "camera",
      "subtype": "person_detected",
      "device_id": "cam-north-gate"
    },
    "observed": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "ingested": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "location": {
      "area_id": "NorthGate",
      "lat": 55.4595,
      "lon": -4.6297
    },
    "attributes": {
      "confidence": 0.92,
      "count": 5
    },
    "severity": "major"
  }'
```

**Watch the dashboard!** The alarm should appear in the NEW lane within seconds.

### 3. Interact with the Alarm

In the UI:
1. Click **"Acknowledge"** button → moves to TRIAGE lane
2. Click **"Assign to Me"** → assigns to you
3. Click **"ACTIVE"** → transitions state
4. See the **SLA timer** counting down (green → yellow → red)

### 4. Check the API

```bash
# List all alarms
curl http://localhost:8000/api/alarms | jq

# Get alarm details
curl http://localhost:8000/api/alarms/<alarm-id> | jq

# View metrics
curl http://localhost:8000/metrics | grep overwatch_alarms
```

### 5. Test Rules Engine

Create a rule that sends console notifications:

```bash
curl -X POST http://localhost:8000/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_content": "rule: high_confidence_alert\nwhen:\n  all:\n    - event.attributes.confidence >= 0.9\n    - event.severity == \"major\"\nthen:\n  - notify:\n      channels: [\"console\"]\n      message: \"High confidence detection: {{attributes.count}} people\"\n  - alarm.create_or_update:\n      severity: \"critical\"\n      runbook: \"crowd_response\""
  }'
```

Now create another test event with confidence > 0.9 and watch the console logs!

### 6. WebSocket Live Updates

Open browser console on http://localhost:7001 and watch:

```javascript
// Messages like:
{type: 'alarms', action: 'created', id: 'alm_...', state: 'NEW', ...}
{type: 'alarms', action: 'transitioned', id: 'alm_...', state: 'TRIAGE', ...}
```

## What You Can Do

### In the Alarm Desk UI:
- ✅ See alarms organized by state
- ✅ Watch SLA timers count down in real-time
- ✅ Acknowledge new alarms
- ✅ Assign alarms to operators
- ✅ Transition between states
- ✅ Filter by severity or site
- ✅ See live updates when alarms change

### Via API:
- ✅ Create/list/get alarms
- ✅ Acknowledge, assign, transition
- ✅ Add notes to alarms
- ✅ View alarm history
- ✅ Create/manage rules
- ✅ Subscribe to WebSocket topics

## Architecture

```
Event → EventManager → RulesEngine → AlarmManager → Storage
                   ↓                      ↓
              WebSocket                Database
                   ↓                      ↓
            Dashboard UI            Alarm Desk
```

## Metrics Dashboard

View metrics at http://localhost:8000/metrics

Key metrics:
- `overwatch_alarms_created_total{severity, site}`
- `overwatch_alarms_by_state{state, severity}`
- `overwatch_alarm_sla_breaches_total{severity}`
- `overwatch_rules_triggered_total{rule_id}`
- `overwatch_websocket_connections`

## Files to Explore

**Backend:**
- `backend/alarms/` - Alarm management core
- `backend/rules/` - Rules engine
- `backend/integrations/` - External integrations
- `backend/api/routes/alarms.py` - Alarm API
- `backend/api/routes/rules.py` - Rules API

**Frontend:**
- `frontend/js/alarms.js` - Alarm Desk logic
- `frontend/index.html` - UI layout (search for "alarms-view")
- `frontend/css/input.css` - Alarm styles

**Documentation:**
- `CAPABILITIES.md` - Feature matrix
- `IMPLEMENTATION_COMPLETE.md` - Full implementation summary
- `docs/alarm.md` - Original specification

## Troubleshooting

**No alarms showing?**
- Check API: `curl http://localhost:8000/api/alarms`
- Check browser console for errors
- Verify WebSocket connection (look for "WebSocket connected")

**SLA timers not updating?**
- Should update every second automatically
- Check browser console for errors

**Can't transition alarm?**
- Some transitions require notes
- Check browser alert for error message
- Verify state machine allows the transition

## Next Steps

To make this production-ready:

1. **Add authentication** - Currently no auth (security risk!)
2. **Configure integrations:**
   - Set SMTP credentials for email
   - Set Twilio credentials for SMS
   - Set PagerDuty integration key
3. **Connect real cameras** - Add UniFi cameras to hierarchy.yaml
4. **Create runbooks** - Define response procedures
5. **Set up Grafana** - Visualize metrics
6. **Load test** - Test with 50+ cameras

## Success!

You now have a working Alarm Centre that:
- Correlates events into alarms
- Tracks SLAs
- Executes rules
- Notifies operators
- Provides a modern triage UI

**Enjoy your Alarm Centre! 🎉**


