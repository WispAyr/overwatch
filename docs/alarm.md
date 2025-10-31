Awesome brief. Here’s a practical, end-to-end spec for a federated alarm centre that ingests AI detections and alerts from cameras/sensors, correlates them into events, and drives alarms with resolution, escalation, and rules-based automation.

1) High-level goals

Unify heterogeneous inputs (CCTV AI, VMD, ANPR, people counting, LoRa, access control, radio, 911/999 CAD feeds, weather, ICS, etc.).

Federate across agencies/sites/tenants with strict data sovereignty and selective sharing.

Correlate raw signals → events → alarms with deduplication, confidence scoring, and geo/time context.

Orchestrate responses using rules, runbooks, and automation (SOAR-style).

Case management: full lifecycle (open → triage → act → resolve → post-mortem) with audit.

Operate at the edge & cloud, tolerate loss, degrade gracefully, and meet clear SLOs.

2) Core architecture
2.1 Components

Edge Ingest Nodes (on-prem/vehicle/site)

Protocol adapters: RTSP/ONVIF, Webhooks, MQTT, AMQP, Syslog, SRT, NMEA/GPX, LoRaWAN (LNS), Modbus/TCP, OPC-UA.

Local CEP (complex event processing) for bandwidth/cost saving.

Buffered store-and-forward (e.g., RocksDB + WAL) for offline tolerance.

Message Fabric

Core bus: Kafka (or NATS JetStream) for ordered topics, replay, and back-pressure.

Topic taxonomy: tenant.site.device.{stream}, events.normalized, events.enriched, alarms.*, audit.*.

Normalization & Enrichment Service

Converts all inputs to a Canonical Event Model.

Enrich: geofence/POI, device metadata, floorplan/camera FOV, weather, watchlists, RBAC tags.

Correlation & CEP Engine

Sliding windows, spatial joins, dedupe, rule evaluation, ML-based clustering.

Rules/Automation Orchestrator

Deterministic rules (DSL) + Playbooks (human-in-the-loop) + Automation tasks (tickets, paging, PTZ presets, TTS to radios, signage, SMS).

Alarm Manager

Event→Alarm state machine, escalation ladders, SLA timers, on-call rotations.

Case Management

Investigations with timeline, evidence locker, tasking, approvals, post-incident review.

Media Services

DVR/NVR integration; event-bounded clips and snapshots, privacy masks, redaction.

Identity & Federation

Multi-tenant RBAC/ABAC, cross-org trust, scoped data sharing, attribute tagging.

APIs & UI

GraphQL + REST + WebSocket; Operator Console, Supervisor Console, Admin Console; Mobile/Tablet ops.

Observability & Audit

Metrics, traces, logs; tamper-evident audit ledger; config versioning.

Storage

Hot store: Postgres (metadata) + Elasticsearch/OpenSearch (search) + S3-compatible object store (media/artifacts).

Cold archive to S3/Glacier.

2.2 Deployment model

Hybrid: edge nodes (k3s) + regional clusters (K8s) + cloud control plane.

HA: ≥3 brokers, stateless services behind load balancers, ZK-less Kafka (KIP-500) if applicable.

SLOs: P95 end-to-alarm < 3 s on LAN; < 8 s cross-site; availability ≥ 99.9%.

3) Data models (canonical)
3.1 Event (normalized)
{
  "id": "evt_01HZY0...",
  "tenant": "advantage",
  "site": "dam-park",
  "source": {
    "type": "camera", "subtype": "ai/person",
    "device_id": "cam_g5_northgate",
    "vendor": "ubnt", "model": "G5"
  },
  "observed": "2025-10-30T19:22:13Z",
  "ingested": "2025-10-30T19:22:14Z",
  "location": { "lat": 55.4595, "lon": -4.6297, "floor": 0, "area_id": "North Gate" },
  "geometry": { "polygon": [[...]] },
  "attributes": {
    "confidence": 0.92,
    "count": 6,
    "direction": 184,
    "speed_kph": null,
    "label": "crowd_density_high"
  },
  "media": {
    "snapshot_url": "s3://.../evt_...jpg",
    "clip_url": "s3://.../evt_...mp4"
  },
  "raw": { "...": "vendor fields preserved" },
  "tags": ["GDPR:PublicArea", "SHARE:PoliceView"]
}

3.2 Alarm
{
  "id": "alm_01HZ...",
  "group_key": "geo:NorthGate:type:crowd_density",
  "severity": "major",           // info, minor, major, critical
  "state": "TRIAGE",             // NEW → TRIAGE → ACTIVE → CONTAINED → RESOLVED → CLOSED
  "created_at": "...",
  "current_sla_deadline": "...",
  "confidence": 0.88,
  "correlated_events": ["evt_...", "evt_..."],
  "assignee": "op_j.smith",
  "runbook_id": "rbk_crowd_high",
  "escalation_policy": "ep_site_safety",
  "watchers": ["sup_k.miller"],
  "links": {
    "case_id": "cas_...",
    "map_view": "/ui/map?alarm=alm_...",
    "live_feeds": [ "rtsp://...", "webrtc://..." ]
  }
}

4) Event → Alarm pipeline (logic)

Ingest & Normalize

Accept anything; reject nothing. Normalize to canonical schema, attach device/site/tenant.

Enrich

Add geo (inside geofence?), FOV intersection, nearest asset, weather, rosters/on-call, known hazards.

Correlate

Windowed aggregation: e.g., crowd_density_high in North Gate for ≥30s OR 3 detections in 60s.

Spatial rules: merge adjacent cameras’ detections if polygons overlap.

Deduplicate using group_key (site+area+type).

Score

Combine signal confidence, device health, model drift, historical false-positive rate → unified score.

Create/Update Alarm

If open alarm with same group_key exists, update (bump severity/state); else create.

Run Rules/Automation

Evaluate DSL: notifications, PTZ move, signage message, dispatch task, open radio PTT with TTS, open ticket.

Human Loop

Operator triage; can promote to ACTIVE, snooze, merge, split, suppress with reason.

Escalation

Timers per severity; if no action, escalate to role/rota; auto-repage with anti-spam.

Resolution & Learn

Close alarm with disposition (true/false positive, safety action taken). Update model retraining cues & per-device FP rates.

5) Federation & multi-tenancy

Tenants: logical isolation; separate topics, storage buckets, encryption keys.

Sites: sub-scopes with local edge nodes.

Sharing contracts (Trust Policies):

Attribute-based: e.g., SHARE:PoliceView lets Police tenant subscribe to derived alarms + redacted media.

Data minimization: share alarm summaries by default; media requires policy tag or on-demand secure fetch with watermarking.

Cross-org identity: OIDC federation (Entra/Okta). RBAC/ABAC with claims: role, org, event, zone.

Air-gapped mode: store-and-forward when inter-org link goes down; reconcile on re-connect.

6) Roles & permissions (examples)

Operator: triage/ack, launch runbooks, request resources, annotate.

Supervisor: change severity, merge/split, approve sharing, modify runbooks, override escalations.

Administrator: manage devices, rules, trust policies, retention, keys.

Observer (External): read-only alarms for shared scopes, view redacted media.

7) Rules & automation
7.1 Rule DSL (readable YAML)
rule: CrowdHigh_NorthGate
when:
  all:
    - event.type == "crowd_density_high"
    - event.location.area_id == "North Gate"
    - event.attributes.count >= 50
    - duration(event, within: "30s") >= "20s"
then:
  - correlate.by: ["site", "location.area_id", "event.type"]
  - alarm.create_or_update:
      severity: "major"
      runbook: "rbk_crowd_high"
  - notify:
      channels: ["console", "sms:+44XXXXXXXXX", "pagerduty"]
      message: "High crowd density at North Gate ({{count}} ppl)."
  - automation:
      - signage.push: "Please keep moving. Use Gate B."
      - ptz.preset: {camera: "cam_g5_overview", preset: "north_gate_wide"}
      - radio.tts: "Control to stewards, manage flow to Gate B."
suppress:
  - cooldown: "2m"

7.2 Playbook / Runbook (SOAR-style)

rbk_crowd_high

Confirm live feeds (auto-open 3 nearest cameras).

Check egress routes (GIS overlay).

If density > threshold for 60s, escalate to Site Safety.

Trigger one-way signage preset and send steward tasking.

Mark CONTAINED when density decreases < threshold for 2 min.

Add note + snapshots; auto-compile incident report PDF.

8) Operator experience (UI)

Common Operating Picture (COP)

Live map with layers: cameras (FOV cones), sensors, geofences, weather, road closures, generator status.

Alarm banners with severity color, SLA timer, and one-click runbook.

Alarm Desk

Kanban by state; filters by site/role; bulk actions; escalation status; assignment.

Timeline

Event and media strip; scrub to auto-sync relevant feeds; side-by-side compare.

Case View

Tasks, notes, evidence (hash-locked), related alarms, comms log (radio/phone), decision journal.

Privacy controls

Live/recorded redaction toggles, privacy zones, watermarking, audit trail visibility.

Mobile

Push acks, offline notes, attach photos, location share, quick actions (e.g., “Arrived on scene”).

9) Integrations

Video: ONVIF, RTSP/WebRTC, UniFi Protect API, Milestone, Genetec, 3rd-party AI (YOLO, Ultralytics, Hailo, OpenVINO, NVIDIA DeepStream).

IoT: MQTT (Sparkplug B), LoRaWAN (TTN/ChirpStack), BLE beacons, Modbus/OPC-UA for generators/SCADA.

Comms: SIP/VoIP, Zello/TAK/PTT gateways, Twilio/SMS, Email, Slack/Teams.

CAD/911/999: read-only incident feed + push alarm summaries.

ITSM/Tickets: Jira, ServiceNow.

Signage: PiSignage/HTML endpoints for emergency messaging.

GIS: GeoServer, WFS/WMS, Mapbox/Leaflet; import CAD/KMZ shape layers.

10) Security & compliance

Encryption: TLS 1.3 in transit; per-tenant envelope keys at rest; field-level encryption for PII.

AuthZ: RBAC+ABAC, SCIM provisioning, hardware-key MFA for admins.

GDPR/DPA: configurable retention (e.g., alarms 2 years, media 30 days default), data subject request workflow, access logging.

Audit: append-only event log with hash chain; exportable for regulators.

Safety: explicit allow-lists for automation capable of physical actions (e.g., signage/PA).

11) Reliability & performance

RTO/RPO: RTO 15 min region; RPO 5 min (WAL + async replicate).

Back-pressure: auto-throttle high-volume streams; degrade to snapshots; drop non-critical enrichment first.

Health: device heartbeat, model drift metrics, FP/FN tracking per source.

12) Analytics & ML

KPIs: mean time to acknowledge (MTTA), to contain (MTTC), to resolve (MTTR), alarm volume, true-positive rate, per-device FP rate, operator workload.

Model feedback: label from dispositions feeds training set; active learning suggestions.

Forecasting: crowd flows, generator failures, weather-risk overlays.

13) Example lifecycle (state machine)
NEW → TRIAGE → ACTIVE → CONTAINED → RESOLVED → CLOSED
       |            |         |
       |            └─(Escalate)→ ACTIVE (higher sev)
       └─(Snooze)→ SNOOZED (timer) → TRIAGE
Any state → SUPPRESSED (policy) → AUTO-CLOSE (with reason)

14) API sketches
14.1 Ingest (Webhook)
POST /api/v1/ingest
Authorization: Bearer <token>
Content-Type: application/json
{
  "source": {"type":"camera","subtype":"ai/person","device_id":"cam_123"},
  "observed":"2025-10-30T19:22:13Z",
  "location":{"lat":..., "lon":...},
  "attributes":{"label":"person","confidence":0.93,"bbox":[...]}
}

14.2 Subscribe (WebSocket)

wss://.../stream?topics=alarms.updates,events.enriched&tenant=...

14.3 Rules API
PUT /api/v1/rules/{id}
Content-Type: application/x-yaml
<DSL as above>

14.4 Alarm actions
POST /api/v1/alarms/{id}/ack
POST /api/v1/alarms/{id}/assign { "assignee": "op_j.smith" }
POST /api/v1/alarms/{id}/transition { "to": "CONTAINED", "note": "Flow restored" }

15) Redaction & evidence handling

On-ingest privacy masks persisted per camera.

On-demand redaction for exports; exports are watermarked with time/user and hashed (SHA-256) into audit ledger.

Evidence bundle = JSON manifest + media + hash file; one-click ZIP creation.

16) Config, versioning, testing

Config-as-code: rules/runbooks in Git; CI for static validation & simulation.

Scenario simulator: play recorded event streams to test correlation/escalation.

Staging tenants for soak tests; chaos testing for bus/DB failures.

17) Implementation tech (suggested)

Back end: TypeScript/Node or Go; gRPC for internal, REST/GraphQL external.

Stream: Kafka (Confluent/Redpanda) or NATS JetStream.

Datastores: Postgres + PostGIS; OpenSearch; MinIO/S3.

UI: React + Leaflet/Mapbox GL; WebRTC for live.

Edge: k3s, containerized adapters.

Auth: Keycloak/ORY; OPA for ABAC.

18) Phased delivery

Phase 1 (MVP):

Ingest (MQTT/Webhook/ONVIF AI), normalization, basic correlation, alarm state machine, console UI, manual runbooks, SMS/email alerts.

Phase 2:

Federation policies, GIS overlays, PTZ/signage automations, redaction, evidence export, PagerDuty/Jira integrations.

Phase 3:

Advanced CEP, ML-assisted dedupe/scoring, active learning, CAD integration, full analytics, mobile offline.

19) Example federation policy (pseudo-OPA)
package share

default allow = false

allow {
  input.requesting_org == "police"
  input.resource.kind == "alarm_summary"
  "SHARE:PoliceView" in input.resource.tags
}

20) SLOs, alerts & runbooks (ops)

SLOs: P99 ingest latency < 2s edge→core; P95 UI alarm render < 1.5s.

Ops alerts: bus lag > threshold, consumer crashes, error rate spikes, rule eval backlog.

Ops runbooks: rotate tokens, drain topics, replay partition, promote standby region.

---

## Implementation Status

### Overwatch Alarm System - Production Ready

The Overwatch implementation includes a fully-featured alarm management system with:

**Backend Components** (Python/FastAPI):
- Complete alarm lifecycle state machine (8 states)
- Event correlation and deduplication
- SLA tracking with severity-based timers
- Automatic severity escalation
- Full audit trail and history
- WebSocket real-time updates

**GUI Components** (Pure HTML/CSS/JavaScript):
- Kanban-style alarm board
- Comprehensive alarm detail modal
- Bulk operations (multi-select, bulk actions)
- Advanced search and filtering
- Export capabilities (JSON/CSV)
- Real-time SLA timers
- Complete history timeline

**State Machine**:
```
NEW → TRIAGE → ACTIVE → CONTAINED → RESOLVED → CLOSED
          ↓
      SNOOZED
          ↓
      SUPPRESSED
```

**Key Features**:
- ✅ Full alarm lifecycle management
- ✅ Assignment and escalation
- ✅ Runbook integration
- ✅ Watcher notifications
- ✅ Severity management
- ✅ Event correlation
- ✅ Bulk operations
- ✅ Advanced filtering
- ✅ Export functionality
- ✅ Complete audit trail

For detailed GUI documentation, see:
- [Alarm GUI Features Guide](ALARM_GUI_FEATURES.md)
- [Alarm Expansion Summary](ALARM_EXPANSION_SUMMARY.md)

For API documentation, see:
- [API Reference](API.md) - Alarm endpoints section