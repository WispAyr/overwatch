# Admin Panel Fixes

## Issues Fixed

### 1. Admin View Not Loading
**Problem**: The admin panel HTML wasn't being loaded when clicking the Admin tab.

**Root Cause**: The `showView` function wrapper was trying to access `window.showView` but the function was defined as a global function, not a property of window.

**Fix**: 
- Modified `frontend/index.html` to properly wrap the global `showView` function
- Added console logging for debugging
- Ensured the wrapper runs after DOM is ready

### 2. Backend/Frontend Data Mismatches

#### Organizations
**Problem**: Frontend sends `organization_type` field, but backend model uses `extra_data`.

**Fix**: Updated `backend/api/routes/organizations.py` to:
- Accept `organization_type` in the API models
- Store it in the `extra_data` JSON field
- Return it when listing/getting organizations

#### Sites
**Problem**: Frontend sends `location` as a string, backend expects a dict/JSON object.

**Fix**: Updated `frontend/js/admin.js` to convert location string to `{address: string}` format.

#### Sublocations
**Problem**: Frontend sends `area_type`, backend expects `sublocation_type`.

**Fix**: Updated `frontend/js/admin.js` to send `sublocation_type` instead of `area_type`.

### 3. App Initialization Errors

**Problem**: App.js was calling alarm functions as methods but they're defined as global functions in alarms.js.

**Fix**: Updated `frontend/js/app.js` to:
- Call `loadAlarms()`, `setupAlarmFilters()`, and `updateSLATimers()` as global functions
- Added existence checks to prevent errors if alarms.js isn't loaded

## Testing

### Start the Dashboard
```bash
# Terminal 1 - Start backend (if not already running)
cd /Users/ewanrichardson/Development/overwatch
source venv/bin/activate
python backend/main.py

# Terminal 2 - Start dashboard
./scripts/start_dashboard.sh
```

### Test Admin Functionality
1. Open http://localhost:7002 in your browser
2. Click on the "Admin" tab in the navigation
3. You should see the admin panel with four tabs:
   - Organizations
   - Sites
   - Sublocations
   - Cameras

### Create Test Data
1. **Create an Organization**:
   - Click "Create Organization"
   - Fill in name, description, and type
   - Submit

2. **Create a Site**:
   - Click "Sites" tab
   - Click "Create Site"
   - Select the organization
   - Fill in details
   - Submit

3. **Create a Sublocation**:
   - Click "Sublocations" tab
   - Click "Create Sublocation"
   - Select a site
   - Fill in details
   - Submit

4. **Create a Camera**:
   - Click "Cameras" tab
   - Click "Create Camera"
   - Select a sublocation
   - Fill in camera details and RTSP URL
   - Submit

## Files Modified

1. `frontend/index.html` - Fixed admin view loading
2. `frontend/js/admin.js` - Fixed data format mismatches
3. `frontend/js/app.js` - Fixed alarm function calls
4. `backend/api/routes/organizations.py` - Added organization_type support

## Console Debugging

Open browser console (F12) to see debug logs:
- "Setting up admin view loader..."
- "showView called with: admin"
- "Loading admin view HTML..."
- "Admin view HTML loaded, initializing AdminPanel..."
- "AdminPanel initialized successfully"

If you see errors, they will help identify the issue.

