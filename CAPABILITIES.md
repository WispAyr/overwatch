# Overwatch Capabilities Matrix

## ✅ Core Platform (Implemented)

### Event Processing
| Feature | Status | Notes |
|---------|--------|-------|
| Event storage (canonical schema) | ✅ Implemented | Unified schema with tenant/site/source/location |
| Event enrichment pipeline | ✅ Implemented | Automatic metadata attachment |
| Cursor-based pagination | ✅ Implemented | Efficient event querying with since_ts/before_ts |
| Multi-tenant filtering | ✅ Implemented | Filter by tenant, site, source_type |
| Event subscriptions | ✅ Implemented | Callback-based event distribution |

### Alarm Management
| Feature | Status | Notes |
|---------|--------|-------|
| Alarm state machine | ✅ Implemented | NEW → TRIAGE → ACTIVE → CONTAINED → RESOLVED → CLOSED |
| Event correlation | ✅ Implemented | Group by tenant:site:area:type |
| SLA tracking | ✅ Implemented | Per-severity SLA timers with deadlines |
| Alarm assignment | ✅ Implemented | Assign operators to alarms |
| Alarm history | ✅ Implemented | Full audit trail of state transitions |
| Alarm-event linking | ✅ Implemented | Track correlated events per alarm |
| REST API | ✅ Implemented | `/api/alarms/*` with list/detail/ack/assign/transition |

### Rules Engine
| Feature | Status | Notes |
|---------|--------|-------|
| YAML DSL parser | ✅ Implemented | Parse alarm.md-compliant YAML rules |
| Condition evaluation | ✅ Implemented | `all`, `any`, expression-based conditions |
| Alarm creation actions | ✅ Implemented | Integrated with AlarmManager |
| Notification actions | ✅ Implemented | Console, email, SMS, PagerDuty |
| Automation actions | ✅ Implemented | PTZ, signage, radio, webhooks |
| Cooldown/suppression | ✅ Implemented | Per-rule cooldown windows |
| Rule management API | ✅ Implemented | `/api/rules/*` CRUD operations |

### WebSocket & Real-time
| Feature | Status | Notes |
|---------|--------|-------|
| Topic-based subscriptions | ✅ Implemented | Subscribe to events, alarms, streams |
| Client filtering | ✅ Implemented | Filter by tenant/site/camera |
| Backpressure handling | ✅ Implemented | Bounded buffers (100 msg limit) |
| Idle connection cleanup | ✅ Implemented | 5-minute timeout |
| Alarm updates broadcast | ✅ Implemented | Live alarm state changes |

### Integrations
| Feature | Status | Notes |
|---------|--------|-------|
| Email notifications | ✅ Implemented | SMTP with snapshot attachments |
| SMS notifications | ✅ Implemented | Twilio integration |
| PagerDuty incidents | ✅ Implemented | Event-driven incident creation |
| Console notifications | ✅ Implemented | For testing/logging |
| Webhook sender | ✅ Implemented | Retry + exponential backoff |
| PTZ control | 🚧 Stub | ONVIF integration needed |
| Signage control | 🚧 Stub | PiSignage or similar needed |
| Radio TTS | 🚧 Stub | Radio gateway integration needed |
| Recording clips | 🚧 Basic | Needs StreamManager buffer integration |

### Workflow Engine
| Feature | Status | Notes |
|---------|--------|-------|
| YOLOv8 detection | ✅ Implemented | Object detection workflows |
| Event actions | ✅ Implemented | Create events from detections |
| Webhook actions | ✅ Implemented | HTTP POST with retries |
| Recording actions | 🚧 Basic | Single-frame placeholder |
| Alert actions | ✅ Implemented | High-priority events |
| FPS throttling | ✅ Implemented | Per-camera rate limiting |

### Federation
| Feature | Status | Notes |
|---------|--------|-------|
| Cross-site event sharing | ✅ Implemented | ZeroTier-based peering |
| Trust policies | ❌ Not Implemented | Comment 17 - OPA/ABAC needed |
| Tag-based sharing | ❌ Not Implemented | SHARE:PoliceView logic needed |

---

## 🚧 In Progress / Partially Complete

### Workflow Builder
| Feature | Status | Notes |
|---------|--------|-------|
| Visual graph editor | ✅ Implemented | React Flow-based builder |
| Standard workflow nodes | ✅ Implemented | Detection, filter, action nodes |
| Alarm Centre nodes | ❌ Not Implemented | Comment 3 - needs CorrelatorNode, GeoFenceNode, etc. |
| Builder→DSL compiler | ❌ Not Implemented | Comment 4 - graph to YAML translation |
| Deploy workflow | ❌ Not Implemented | Persist and activate from builder |

### Operations UI
| Feature | Status | Notes |
|---------|--------|-------|
| Live camera grid | ✅ Implemented | Multi-camera monitoring |
| Event timeline | ✅ Implemented | Real-time event feed |
| Alarm Desk | ❌ Not Implemented | Comment 9 - Kanban lanes for triage |
| Map view (COP) | ❌ Not Implemented | Comment 18 - Leaflet/Mapbox with camera/geofence overlay |
| Runbook panel | ❌ Not Implemented | Checklist and action links |

### Access Control & Security
| Feature | Status | Notes |
|---------|--------|-------|
| JWT authentication | ❌ Not Implemented | Comment 8 - REST and WS auth needed |
| Role-based access (RBAC) | ❌ Not Implemented | Operator/Supervisor/Admin roles |
| Tenant scoping | ❌ Not Implemented | Enforce tenant access boundaries |
| Snapshot access control | ❌ Not Implemented | Comment 14 - protect media endpoints |
| Watermarking | ❌ Not Implemented | On-the-fly user/time watermarks |
| Audit logging | 🚧 Partial | Alarm history exists; media access not logged |

### Observability
| Feature | Status | Notes |
|---------|--------|-------|
| Prometheus metrics | ❌ Not Implemented | Comment 15 - frames, detections, latency |
| Structured logging | 🚧 Partial | Basic logging present, needs correlation IDs |
| `/api/system/status` | ✅ Basic | Needs richer stats (queue depths, node health) |

---

## ❌ Not Yet Implemented

### Media Management
- DVR/NVR clip extraction from buffer
- Privacy mask persistence per camera
- On-demand redaction for exports
- Evidence bundle creation (ZIP with hash)

### Case Management
- Investigation workflows
- Evidence locker
- Task assignment
- Post-incident review

### Advanced CEP
- ML-based deduplication
- Confidence scoring fusion
- Model drift detection
- Active learning suggestions

### Deployment & Ops
- Kubernetes manifests
- HA/failover configuration
- Backup/restore procedures
- Config-as-code CI validation

---

## 📋 Phased Delivery Plan

### ✅ Phase 1 Complete (MVP)
- ✅ Event ingestion & normalization
- ✅ Alarm state machine
- ✅ Basic rules engine
- ✅ WebSocket live updates
- ✅ YOLO detection workflows
- ✅ Email/SMS/PagerDuty notifications

### 🚧 Phase 2 (In Progress)
- 🚧 Alarm Desk UI
- 🚧 Builder→DSL compiler
- 🚧 Alarm Centre workflow nodes
- 🚧 JWT authentication
- 🚧 Map view (COP)
- 🚧 Snapshot access control
- 🚧 Prometheus metrics

### ⏳ Phase 3 (Planned)
- Federation trust policies
- Advanced CEP & ML scoring
- Case management
- DVR clip extraction
- Evidence export & watermarking
- Mobile app
- CAD/911 integration

---

## 📝 Notes

**What's Production-Ready:**
- Core event pipeline (ingestion → correlation → alarms)
- Alarm lifecycle management
- Rules engine for automation
- Live dashboards

**What Needs Work Before Production:**
- Authentication and authorization (critical)
- Snapshot access control
- Trust policies for federation
- Prometheus metrics and health checks
- Comprehensive error handling
- Deployment automation

**Documentation Status:**
- `docs/alarm.md`: North star specification ✅
- `docs/ARCHITECTURE.md`: Core architecture ✅
- `docs/API.md`: API reference 🚧 (needs alarm/rule endpoints)
- `docs/WORKFLOW_BUILDER.md`: Builder guide 🚧 (needs Alarm Centre nodes)

---

**Last Updated:** 2025-10-31

For detailed API specs, see `docs/API.md`  
For architecture diagrams, see `docs/ARCHITECTURE.md`  
For rule DSL syntax, see `docs/alarm.md` section 7

