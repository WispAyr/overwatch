# Alarm Manager - Organizational Hierarchy Views

## Overview

The Alarm Manager supports **multi-level organizational hierarchy** for viewing and filtering alarms across global, organization, and site levels. This enables proper multi-tenant alarm management with data isolation and role-based views.

## Hierarchy Structure

```
Organizations (Tenants)
    ├── Sites
    │   ├── Sublocations (Areas/Zones)
    │   │   ├── Cameras
    │   │   └── Sensors
```

## View Levels

### 1. Global View 🌍

**Who**: System administrators, NOC operators with cross-org access  
**Scope**: All alarms across all organizations and sites

**Features**:
- Overview of all alarms in the system
- Per-organization statistics
- Quick identification of which orgs/sites need attention
- Alarm count by organization
- Severity distribution across organizations

**Use Cases**:
- Monitoring multiple organizations from central NOC
- System-wide incident awareness
- Resource allocation decisions
- Cross-organization pattern detection

**UI Elements**:
```
┌─────────────────────────────────────┐
│ 🌍 Global View                      │
├─────────────────────────────────────┤
│ Viewing alarms across:              │
│ 🏢 3 Organizations                  │
│ 📍 12 Sites                         │
│                                     │
│ Organization Statistics:            │
│ ┌───────────────────────────────┐  │
│ │ Local Connect      42 alarms  │  │
│ │ 🔴 5  🟠 12  🟡 18  🔵 7      │  │
│ │ 🆕 8 NEW  ⚡ 6 ACTIVE          │  │
│ └───────────────────────────────┘  │
│ ┌───────────────────────────────┐  │
│ │ City Police        18 alarms  │  │
│ │ 🔴 2  🟠 5  🟡 8  🔵 3        │  │
│ │ 🆕 3 NEW  ⚡ 2 ACTIVE          │  │
│ └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 2. Organization View 🏢

**Who**: Organization administrators, tenant SOC operators  
**Scope**: All alarms within a single organization across all sites

**Features**:
- Organization-wide alarm visibility
- Per-site breakdown
- Organization-specific statistics
- Site comparison
- Aggregate metrics for the organization

**Use Cases**:
- Corporate security monitoring all facilities
- Municipal monitoring all city sites
- Campus security across buildings
- Multi-site retail security

**Filtering**:
- Alarms filtered by `tenant = <organization_id>`
- Shows all sites within the organization
- Site-level drill-down available

**UI Elements**:
```
┌─────────────────────────────────────┐
│ 🏢 Organization View                │
│ [Local Connect ▼]                   │
├─────────────────────────────────────┤
│ Local Connect                       │
│ Main organization                   │
│ 📍 Sites: 4                         │
│ 📷 Cameras: 28                      │
│                                     │
│ Organization Statistics:            │
│ Total: 42 alarms                    │
│ 🔴 5  🟠 12  🟡 18  🔵 7           │
│ 🆕 8 NEW  ⚡ 6 ACTIVE               │
│                                     │
│ By Site:                            │
│ ┌───────────────────────┐          │
│ │ NOC Location      24  │          │
│ │ 3  8  10  3           │          │
│ ├───────────────────────┤          │
│ │ Warehouse North   12  │          │
│ │ 1  3  6  2            │          │
│ ├───────────────────────┤          │
│ │ Warehouse South   6   │          │
│ │ 1  1  3  1            │          │
│ └───────────────────────┘          │
└─────────────────────────────────────┘
```

### 3. Site View 📍

**Who**: Site security officers, facility managers  
**Scope**: All alarms within a single physical site

**Features**:
- Site-specific alarm view
- Location context (address, coordinates)
- Site type information (fixed, mobile, temporary)
- Camera count and areas
- Focused incident response

**Use Cases**:
- Individual facility monitoring
- Site security officer dashboard
- Specific location incident management
- Mobile unit operations

**Filtering**:
- Alarms filtered by `site = <site_id>`
- Shows only alarms from cameras/sensors at this site
- Sublocation context available

**UI Elements**:
```
┌─────────────────────────────────────┐
│ 📍 Site View                        │
│ [NOC Location ▼]                    │
├─────────────────────────────────────┤
│ NOC Location                        │
│ Local Connect                       │
│ 📌 Type: fixed                      │
│ 📍 NOC Facility                     │
│ 📷 Cameras: 8                       │
│ 🏠 Areas: 3                         │
│                                     │
│ Site Statistics:                    │
│ Total: 24 alarms                    │
│ 🔴 Critical: 3                      │
│ 🟠 Major: 8                         │
│ 🟡 Minor: 10                        │
│ 🔵 Info: 3                          │
│ 🆕 NEW: 5                           │
│ ⚡ ACTIVE: 4                        │
└─────────────────────────────────────┘
```

## Data Flow

### How Alarms Get Organization/Site Context

1. **Event Creation**: When cameras/sensors generate events, they include:
   ```json
   {
     "tenant": "local-connect",
     "site": "noc-site",
     "source": {
       "device_id": "noc-outdoor-cam-01"
     }
   }
   ```

2. **Alarm Creation**: When events are correlated into alarms:
   ```python
   alarm = {
       'tenant': event.get('tenant'),  # Inherited from event
       'site': event.get('site'),      # Inherited from event
       'group_key': 'tenant:site:area:type'
   }
   ```

3. **Event Correlation**: The `group_key` ensures events from the same:
   - Organization (tenant)
   - Site
   - Area
   - Event type
   
   ...are grouped into the same alarm.

## API Integration

### Endpoints

**Load Hierarchy**:
```
GET /api/hierarchy/tree
```

Response:
```json
{
  "organizations": [
    {
      "id": "local-connect",
      "name": "Local Connect",
      "description": "Main organization",
      "sites": [
        {
          "id": "noc-site",
          "name": "NOC Location",
          "site_type": "fixed",
          "location": {...},
          "sublocations": [...]
        }
      ]
    }
  ]
}
```

**Filter Alarms by Organization**:
```
GET /api/alarms?tenant=local-connect
```

**Filter Alarms by Site**:
```
GET /api/alarms?site=noc-site
```

**Filter by Both** (redundant but supported):
```
GET /api/alarms?tenant=local-connect&site=noc-site
```

## Implementation Details

### Frontend Components

**alarm-hierarchy.js**:
- Hierarchy state management
- View level switching (global/org/site)
- Organization/site selectors
- Statistics calculation
- Filter application

**Key Functions**:
```javascript
loadHierarchy()           // Load org/site structure
setViewLevel(level)       // Switch between global/org/site
selectOrganization(id)    // Filter by organization
selectSite(id)            // Filter by site
resetHierarchyView()      // Return to global view
applyHierarchyFilter()    // Apply current filters to alarms
updateHierarchyStats()    // Calculate and display stats
```

### Backend Support

**Already Implemented**:
- ✅ Alarms store `tenant` and `site` fields
- ✅ Database indices on `tenant` and `site`
- ✅ Query filtering by `tenant` and `site`
- ✅ Event correlation by tenant and site
- ✅ Hierarchy API endpoint

**Data Model**:
```sql
CREATE TABLE alarms (
    id TEXT PRIMARY KEY,
    tenant TEXT,        -- Organization ID
    site TEXT,          -- Site ID
    severity TEXT,
    state TEXT,
    ...
);

CREATE INDEX idx_alarm_tenant ON alarms(tenant);
CREATE INDEX idx_alarm_site ON alarms(site);
```

## Usage Examples

### Example 1: Global NOC Monitoring

**Scenario**: Central NOC monitoring multiple organizations

1. Open Alarm Manager
2. Select "🌍 Global" view (default)
3. See all organizations with alarm counts
4. Identify "City Police" has 5 critical alarms
5. Click to switch to organization view
6. Drill down to specific sites

### Example 2: Municipal Operations

**Scenario**: City monitoring all municipal facilities

1. Select "🏢 Organization" view
2. Choose "City Municipal" from dropdown
3. See all city sites with alarm distribution
4. Notice "City Hall" has most critical alarms
5. Switch to "📍 Site" view
6. Select "City Hall" site
7. View only City Hall alarms

### Example 3: Facility Security Officer

**Scenario**: Security officer at specific warehouse

1. Select "📍 Site" view
2. Choose "Warehouse North" from dropdown
3. See only alarms from this warehouse
4. All alarms are from local cameras/sensors
5. Focus on facility-specific incidents

### Example 4: Multi-Tenant SaaS Deployment

**Scenario**: Security company serving multiple clients

1. Each client is an organization (tenant)
2. Data isolation enforced by tenant field
3. Each client sees only their alarms
4. System admins see global view
5. Clients can drill down to their sites

## Role-Based Access Control (RBAC)

**Suggested Role Mapping**:

| Role | Default View | Access Level |
|------|-------------|--------------|
| System Admin | Global | All orgs, all sites |
| NOC Operator | Global | All orgs, all sites |
| Org Admin | Organization | Single org, all sites |
| Site Manager | Site | Single site only |
| Security Officer | Site | Single site only |
| Viewer | Site | Read-only, single site |

**Implementation** (Future):
- User profile stores default organization/site
- Login automatically applies filters
- API enforces tenant isolation
- Permissions checked per request

## Statistics & Metrics

### Global View Metrics
- Total alarms across all organizations
- Alarms per organization
- Severity distribution per organization
- State distribution per organization
- Top organizations by alarm count

### Organization View Metrics
- Organization total alarms
- Severity distribution
- State distribution
- Alarms per site
- Site comparison
- Trending over time

### Site View Metrics
- Site total alarms
- Severity breakdown
- State breakdown
- NEW and ACTIVE counts
- Most active areas (sublocations)
- Camera/sensor alarm rates

## Configuration

### Hierarchy Configuration

Defined in `config/hierarchy.yaml`:

```yaml
organizations:
  - id: local-connect
    name: "Local Connect"
    description: "Main organization"
    
    sites:
      - id: noc-site
        name: "NOC Location"
        site_type: fixed
        location:
          address: "NOC Facility"
          lat: 51.5074
          lon: -0.1278
          
        sublocations:
          - id: noc-outdoors
            name: "Outdoors"
            sublocation_type: outdoor
            
            cameras:
              - id: noc-outdoor-cam-01
                name: "NOC Outdoor Camera 1"
                type: unifi
                enabled: true
```

### Multi-Tenant Configuration

For SaaS deployments, configure multiple organizations:

```yaml
organizations:
  - id: client-a
    name: "Client A Corp"
    sites: [...]
    
  - id: client-b
    name: "Client B Inc"
    sites: [...]
    
  - id: client-c
    name: "Client C Ltd"
    sites: [...]
```

## Performance Considerations

1. **Indexing**: Database indices on `tenant` and `site` fields ensure fast filtering
2. **Caching**: Hierarchy data cached on frontend (refreshes periodically)
3. **Pagination**: Large alarm lists paginated (limit 1000 by default)
4. **Lazy Loading**: Site statistics calculated on-demand
5. **Efficient Queries**: Filters pushed to database level

## Migration Notes

### Existing Alarms

If alarms exist without `tenant`/`site`:
- They appear under "unknown" in global view
- Backfill script can assign based on device IDs
- Future events will populate correctly

### Backfill Script

```python
# Example backfill for existing alarms
async def backfill_alarm_hierarchy():
    alarms = await storage.query_alarms()
    for alarm in alarms:
        if not alarm.get('tenant'):
            # Look up from device ID
            device_id = alarm['attributes']['initial_event_id']
            # ... lookup and update
```

## Future Enhancements

1. **Hierarchy Permissions**: RBAC based on org/site
2. **Cross-Org Sharing**: Share specific alarms between orgs
3. **Federated Views**: Multi-region global view
4. **Custom Groupings**: Virtual sites, regions, zones
5. **Alarm Routing**: Auto-assign based on org/site
6. **Escalation Trees**: Different policies per org/site
7. **Analytics**: Comparative analysis across organizations
8. **Notifications**: Org/site-specific notification rules

## Troubleshooting

**Q: Alarms not showing in organization view?**  
A: Check that events include `tenant` field. Verify camera/device mapping in hierarchy.yaml.

**Q: Site selector is empty?**  
A: Ensure hierarchy is loaded (`GET /api/hierarchy/tree` returns data).

**Q: Alarms appear in wrong organization?**  
A: Check event `tenant` field. Verify camera is in correct organization in hierarchy.yaml.

**Q: Statistics not updating?**  
A: Statistics refresh every 30 seconds. Manual refresh: click "Reset to Global" then reselect view.

## Summary

The hierarchical alarm views provide:

✅ **Multi-tenancy support** - Isolate alarms by organization  
✅ **Flexible viewing** - Global, org, and site levels  
✅ **Rich statistics** - Per-level metrics and breakdowns  
✅ **Fast filtering** - Indexed database queries  
✅ **Real-time updates** - Live alarm counts and stats  
✅ **Role-ready** - Foundation for RBAC implementation  

This enables professional multi-tenant SOC operations with proper data isolation and context-aware alarm management.

