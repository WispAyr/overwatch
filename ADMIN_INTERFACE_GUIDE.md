# Admin Interface Guide

## Overview

The Admin Interface allows you to manage the complete organizational hierarchy:
- **Organizations** - Top-level entities (e.g., companies, clients)
- **Sites** - Physical locations within organizations (e.g., headquarters, branches)
- **Sublocations** - Specific areas within sites (e.g., entrances, parking lots)
- **Cameras** - Individual cameras within sublocations

## Accessing the Admin Panel

1. Open your browser to http://localhost:7002
2. Click the **"Admin"** button in the top navigation
3. The admin panel will load with four tabs

## Creating the Hierarchy

### Step 1: Create an Organization

1. Click the **"Organizations"** tab
2. Click **"+ Create Organization"** button
3. Fill in the form:
   - **Organization Name** (required): e.g., "Acme Corporation"
   - **Description** (optional): Brief description
   - **Type**: Select from Enterprise, Business, or Residential
4. Click **"Create Organization"**
5. You'll see a success message and the organization appears in the list

### Step 2: Create a Site

1. Click the **"Sites"** tab
2. Click **"+ Create Site"** button
3. Fill in the form:
   - **Organization**: Select from the dropdown (organizations you created)
   - **Site Name** (required): e.g., "Downtown Office"
   - **Description** (optional): Details about the site
   - **Site Type**: Select type (Headquarters, Branch, Warehouse, etc.)
   - **Location**: Optional address
4. Click **"Create Site"**
5. The site appears in the list with organization details

### Step 3: Create a Sublocation

1. Click the **"Sublocations"** tab
2. Click **"+ Create Sublocation"** button
3. Fill in the form:
   - **Site**: Select from the dropdown (sites you created)
   - **Sublocation Name** (required): e.g., "Main Entrance", "Parking Lot A"
   - **Description** (optional)
   - **Area Type**: Select from Entrance, Exit, Parking, Lobby, etc.
4. Click **"Create Sublocation"**
5. The sublocation appears with site details

### Step 4: Add a Camera

1. Click the **"Cameras"** tab
2. Click **"+ Create Camera"** button
3. Fill in the form:
   - **Sublocation**: Select where the camera is located
   - **Camera Name** (required): Descriptive name
   - **Camera Type**: UniFi Protect, Generic RTSP, ONVIF, Hikvision, or Dahua
   - **RTSP URL** (required): Full RTSP stream URL with credentials
     - Format: `rtsp://username:password@ip:port/stream`
     - Example: `rtsp://admin:pass123@192.168.1.100:554/stream1`
   - **Enable camera**: Check to activate immediately
4. Click **"Create Camera"**
5. Camera appears in the list with location hierarchy

## RTSP URL Examples

### UniFi Protect
```
rtsps://10.10.10.1:7441/[stream-key]?enableSrtp
```

### Generic IP Camera
```
rtsp://admin:password@192.168.1.100:554/stream1
```

### Hikvision
```
rtsp://admin:password@192.168.1.101:554/Streaming/Channels/101
```

### Dahua
```
rtsp://admin:password@192.168.1.102:554/cam/realmonitor?channel=1&subtype=0
```

## Troubleshooting

### "No organizations available" in Site modal

**Problem**: Trying to create a site but dropdown shows "No organizations available"

**Solution**: 
1. Close the modal
2. Go to Organizations tab
3. Create an organization first
4. Return to Sites tab and try again

### "No sites available" in Sublocation modal

**Problem**: Trying to create a sublocation but no sites in dropdown

**Solution**:
1. Close the modal
2. Create a site in the Sites tab first
3. Return to Sublocations tab

### "No sublocations available" in Camera modal

**Problem**: Cannot add camera - no sublocations

**Solution**:
1. Complete the hierarchy: Organization → Site → Sublocation
2. Then add cameras

### Camera not appearing in main dashboard

**Problem**: Created camera doesn't show up

**Solution**:
1. Check camera is enabled (green dot in Cameras list)
2. Verify RTSP URL is correct
3. Check network connectivity to camera
4. Look at browser console for errors

### Form submission not working

**Problem**: Click "Create" but nothing happens

**Solution**:
1. Open browser console (F12)
2. Look for error messages
3. Check backend is running: http://localhost:8000/api/system/status
4. Verify all required fields are filled

## Deleting Entities

**⚠️ Warning**: Deletions cascade down the hierarchy!

- Delete **Organization** → Deletes all sites, sublocations, and cameras
- Delete **Site** → Deletes all sublocations and cameras
- Delete **Sublocation** → Deletes all cameras in that area
- Delete **Camera** → Only removes that camera

Always confirm carefully when deleting!

## Browser Console Logging

For debugging, the admin panel logs to console:
- `Creating organization: {...}` - Data being sent
- `Create organization response: {...}` - Server response
- Similar logs for sites, sublocations, and cameras

Open console (F12) to see detailed information.

## API Endpoints Used

The admin panel interacts with these endpoints:

```
GET    /api/organizations/     - List organizations
POST   /api/organizations/     - Create organization
DELETE /api/organizations/{id} - Delete organization

GET    /api/sites/             - List sites
POST   /api/sites/             - Create site
DELETE /api/sites/{id}         - Delete site

GET    /api/sublocations/      - List sublocations
POST   /api/sublocations/      - Create sublocation
DELETE /api/sublocations/{id}  - Delete sublocation

GET    /api/cameras/           - List cameras
POST   /api/cameras/           - Create camera
DELETE /api/cameras/{id}       - Delete camera
```

## Testing the Setup

1. Create a test organization
2. Create a test site
3. Create a test sublocation
4. Add a camera with a public RTSP stream for testing:
   ```
   Name: Test Camera
   Type: Generic RTSP
   URL: rtsp://rtsp.stream/pattern
   ```
5. Check the main Dashboard view to see the hierarchy
6. Verify the camera appears in the Cameras view

## Complete Example Flow

```
1. Organization: "My Company"
   └─ 2. Site: "Head Office - NYC"
       └─ 3. Sublocation: "Lobby"
           └─ 4. Camera: "Lobby Entrance Cam"
                  RTSP: rtsp://admin:pass@192.168.1.50:554/stream1
```

This creates a complete hierarchy visible throughout the dashboard.

## Future Enhancements

Coming soon:
- Edit functionality for all entities
- Bulk camera import
- Camera health monitoring
- ONVIF auto-discovery
- Camera stream preview in admin panel
- Export/import configuration

