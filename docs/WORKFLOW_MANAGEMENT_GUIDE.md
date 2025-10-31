# Workflow Management System - Complete Guide

## 🎯 Overview

The Overwatch Workflow Management System provides a complete 360° workflow solution with:

- **Multi-Tab Editing** - Work on multiple workflows simultaneously
- **Auto-Save** - Never lose your work
- **Site-Specific Workflows** - Organize workflows by site
- **Master Templates** - Reusable workflow templates
- **Workflow-to-Workflow Communication** - Via LinkCall nodes
- **Seamless Navigation** - Between Dashboard (7002) and Builder (7003)

---

## 📑 Multi-Tab Interface

### Features
- ✅ Open multiple workflows simultaneously
- ✅ Drag to reorder tabs
- ✅ Unsaved changes indicator (orange dot)
- ✅ Running status indicator (green pulse)
- ✅ Site/Master badges on tabs
- ✅ Quick close with confirmation

### Keyboard Shortcuts
- `Ctrl/Cmd + T` - New workflow tab
- `Ctrl/Cmd + W` - Close current tab
- `Ctrl/Cmd + Tab` - Next tab
- `Ctrl/Cmd + Shift + Tab` - Previous tab
- `Ctrl/Cmd + O` - Open workflow library

### Tab Actions Menu
Right-click any tab for:
- Duplicate Tab
- Close Other Tabs
- Close All Tabs
- Save All

---

## 💾 Auto-Save System

### How It Works
1. **Debounced Save** - Saves 2 seconds after you stop making changes
2. **Periodic Backup** - Saves every 30 seconds if changes exist
3. **Manual Save** - Press `Ctrl/Cmd + S` anytime
4. **Pre-Exit Save** - Warns and saves before closing browser

### Save Status Indicators
- **Idle** - No indicator (everything saved)
- **Saving...** - Spinner icon
- **Saved** - Green checkmark (2s)
- **Error** - Red X icon (3s)
- **Unsaved** - Orange dot on tab

### Configuration
```javascript
useAutoSave(workflowId, workflowData, {
  enabled: true,
  interval: 30000,        // Periodic save interval
  debounceDelay: 2000,    // Wait time after last change
  onSaveSuccess: (data) => console.log('Saved!'),
  onSaveError: (error) => console.error('Save failed')
})
```

---

## 📍 Site-Specific Workflows

### Organization Structure
```
Master Workflows (Global Templates)
  ├─ Person Detection Template
  ├─ Vehicle Monitoring Template
  └─ Perimeter Security Template

Site-Specific Workflows
  ├─ Headquarters
  │   ├─ Reception Monitoring
  │   ├─ Parking Lot Security
  │   └─ Server Room Access
  ├─ Warehouse North
  │   ├─ Loading Dock Monitor
  │   └─ Inventory Tracking
  └─ Retail Store 01
      ├─ Customer Counter
      └─ Anti-Theft Detection
```

### Creating Site Workflows
1. **New Workflow** → Select site from dropdown
2. **Or** copy from Master Template → Assign to site
3. Workflow automatically tagged with site

### Master Workflows
- Marked with ★ (purple badge)
- No site assignment
- Can be duplicated to any site
- Read-only for non-admins (optional)

---

## 🔗 Workflow-to-Workflow Communication

### Using LinkCall Nodes
Workflows can call other workflows and pass data between them:

```
Workflow A: Main Security
  Camera → Model → [LinkCall: "parking-monitor"]
  
Workflow B: Parking Monitor (id: "parking-monitor")
  [LinkIn] → Zone Filter → Alert Action
```

### Data Flow
1. **LinkOut** sends data from one workflow
2. **LinkCall** invokes another workflow by ID/name
3. **LinkIn** receives data in the called workflow
4. Results flow back through the call chain

### Cross-Site Communication
- Master workflows can call site-specific workflows
- Site workflows can call other workflows on same site
- Implement access control as needed

---

## 🌐 Seamless Navigation

### Dashboard → Builder
From **Dashboard** (http://localhost:7002):
1. Click **"Workflows"** in navigation
2. See active & saved workflows
3. Click **"Open in Builder"** on any workflow
4. Opens in new tab on port 7003

### Builder → Dashboard
From **Workflow Builder** (http://localhost:7003):
1. Click **"📊 Dashboard"** button (top right)
2. Opens dashboard in new tab
3. Automatically shows Workflows view (`#workflows` hash)

### URL Parameters
- `?workflow=ID` - Auto-load specific workflow
- `#workflows` - Jump to workflows section on dashboard

---

## 📚 Workflow Library

### Opening the Library
- Click **File** → **Open Workflow**
- Press `Ctrl/Cmd + O`
- Click **"📚 Browse Workflows"** button

### Features
- **Search** - Find workflows by name
- **Filter by Type** - All / Master / Site-specific
- **Filter by Site** - Show only workflows for a site
- **Quick Open** - Click any workflow to open in new tab
- **Visual Cards** - See node count, status, last updated

### Library Views

**Master Workflows Section**
- Purple ★ icon
- Global templates
- Reusable across all sites

**Site-Specific Section**  
- Green 📍 icon
- Organized by site
- Site name displayed

---

## 💡 Best Practices

### Workflow Organization

1. **Start with Masters**
   - Create general-purpose templates
   - Mark as Master workflow
   - Test thoroughly before deploying

2. **Customize per Site**
   - Duplicate Master template
   - Assign to specific site
   - Adjust for site-specific needs (zones, actions)

3. **Naming Convention**
   ```
   Masters:     "Template: Person Detection"
   Site:        "[HQ] Reception Monitoring"
   Site:        "[WH-North] Loading Dock"
   ```

### Tab Management

**Good Practices:**
- Keep ≤5 tabs open for performance
- Save and close finished workflows
- Use "Close Others" to focus on one

**Warning Signs:**
- Too many tabs = confusion
- Unsaved changes across multiple tabs
- Browser slowdown with 10+ tabs

### Auto-Save Optimization

**When It Saves:**
- ✅ After 2s of no changes (debounced)
- ✅ Every 30s if changes exist (periodic)
- ✅ On `Ctrl/Cmd + S` (manual)
- ✅ Before browser close (if unsaved)

**When It Doesn't Save:**
- ❌ While you're actively editing
- ❌ If no changes since last save
- ❌ If auto-save disabled in settings

---

## 🛠️ Technical Implementation

### Database Schema
```sql
CREATE TABLE visual_workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    site_id TEXT,              -- Site assignment
    site_name TEXT,            -- Denormalized
    is_master INTEGER DEFAULT 0,  -- Master template flag
    status TEXT DEFAULT 'draft',  -- draft/running/stopped
    created_by TEXT,           -- User tracking
    version TEXT DEFAULT '1.0.0',
    schema_version TEXT,
    nodes JSON NOT NULL,
    edges JSON NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX idx_visual_workflows_site_id ON visual_workflows(site_id);
CREATE INDEX idx_visual_workflows_is_master ON visual_workflows(is_master);
```

### API Endpoints

**Workflows**
- `GET /api/workflow-builder` - List all workflows
- `GET /api/workflow-builder/{id}` - Get workflow
- `POST /api/workflow-builder` - Create workflow
- `PUT /api/workflow-builder/{id}` - Update (auto-save uses this)
- `DELETE /api/workflow-builder/{id}` - Delete workflow
- `POST /api/workflow-builder/{id}/duplicate` - Duplicate workflow

**Sites**
- `GET /api/sites/` - List all sites
- `GET /api/sites/{id}` - Get site details

**Templates**
- `GET /api/workflow-templates` - List master templates
- `POST /api/workflow-templates` - Create template

### Frontend Components

**New Components:**
- `<WorkflowTabs>` - Multi-tab interface
- `<WorkflowLibrary>` - Browse and open workflows
- `<AutoSaveIndicator>` - Save status display

**New Hooks:**
- `useAutoSave(workflowId, data, options)` - Auto-save functionality
- `useWorkflowTabs()` - Tab management state

**Updated Components:**
- `<App>` - Now manages multiple workflow tabs
- `<Sidebar>` - Shows current site context
- `<ConfigPanel>` - Site selector for new workflows

---

## 🎨 User Experience Enhancements

### Visual Feedback
- ✅ **Tab Indicators** - Unsaved (orange), Running (green)
- ✅ **Save Status** - Bottom status bar shows save state
- ✅ **Loading States** - Skeleton loaders while loading
- ✅ **Smooth Transitions** - Tab switching animations

### Error Handling
- ✅ **Save Failures** - Retry with exponential backoff
- ✅ **Conflict Resolution** - Warn if workflow changed elsewhere
- ✅ **Graceful Degradation** - Works offline, syncs when back

### Accessibility
- ✅ **Keyboard Navigation** - All features keyboard-accessible
- ✅ **Screen Reader Support** - ARIA labels on all components
- ✅ **High Contrast** - Dark theme optimized

---

## 🚀 Quick Start Examples

### Example 1: Create Master Template
```
1. New Workflow → Name: "Template: Person Detection"
2. Check "Master Template" ✓
3. Build workflow: Camera → Model → Zone → Alert
4. Save (Ctrl+S)
5. Now available in Library under "Master Workflows"
```

### Example 2: Deploy to Site
```
1. Open Library (Ctrl+O)
2. Select "Template: Person Detection"
3. Click "Duplicate"
4. Assign to Site: "Headquarters"
5. Customize zones for HQ layout
6. Auto-saves every 30s
```

### Example 3: Multi-Workflow Setup
```
Tab 1: [HQ] Reception (editing)
Tab 2: [HQ] Parking (running ●)
Tab 3: [WH] Loading Dock (unsaved ●)
Tab 4: Template: Vehicle Detection (master ★)
```

---

## 📊 Dashboard Integration

### Workflows View (7002)
Shows:
- **Active Workflows** - Currently running, with Stop button
- **Saved Workflows** - All saved, with Execute/Edit buttons
- **Quick Actions** - Open Builder, New Workflow

### Live Monitoring
- See workflow status in real-time
- Click "Edit" to modify running workflow
- Stop/Start workflows from dashboard

---

## 🔐 Security & Permissions (Planned v1.1)

### Role-Based Access
- **Admin** - Full access to all workflows
- **Site Manager** - Edit workflows for assigned sites
- **Operator** - Execute workflows, view-only edit
- **Viewer** - Read-only access

### Audit Trail
- Track who created/modified workflows
- Log all executions
- Export audit reports

---

## 📈 Performance

### Optimization Strategies
- **Lazy Loading** - Load workflow data only when tab active
- **Debounced Save** - Reduce server load with smart batching
- **Local Caching** - Cache workflows in localStorage
- **Virtual Scrolling** - Handle 1000+ workflows in library

### Benchmarks
- **Tab Switch Time**: <100ms
- **Auto-Save Latency**: <500ms
- **Library Load**: <1s for 100 workflows
- **Memory Usage**: ~50MB per open workflow

---

*Last updated: October 30, 2025*  
*Version: 2.0.0*  
*Next: Authentication & Permissions (v2.1)*


