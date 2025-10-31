# Admin Panel Test Checklist

## Quick Test Steps

### 1. Start the Backend
```bash
cd /Users/ewanrichardson/Development/overwatch
source venv/bin/activate
python backend/main.py
```

You should see:
- `✓ API server starting...`
- `✓ Database initialized`
- `✓ Uvicorn running on http://0.0.0.0:8000`

### 2. Start the Dashboard (New Terminal)
```bash
cd /Users/ewanrichardson/Development/overwatch
./scripts/start_dashboard.sh
```

You should see:
- `Building Tailwind CSS...`
- `Done in XXXms`
- `Starting dashboard on http://localhost:7002`

### 3. Open Browser
1. Go to: http://localhost:7002
2. Open browser console (F12 → Console tab)

### 4. Test Admin Panel

#### Navigate to Admin
1. Click "Admin" in the top navigation
2. Check console for these logs:
   ```
   showView called with: admin
   Loading admin view...
   Loading admin view HTML...
   Admin view HTML loaded, initializing AdminPanel...
   AdminPanel initialized successfully
   ```

#### Create Organization
1. Click "Create Organization" button
2. Fill in:
   - Name: "Test Organization"
   - Description: "Testing admin panel"
   - Type: "Enterprise"
3. Click "Create Organization"
4. You should see:
   - Success alert
   - Organization appears in the list

#### Create Site
1. Click "Sites" tab
2. Click "Create Site"
3. Fill in:
   - Organization: Select "Test Organization"
   - Name: "Test Site"
   - Site Type: "Branch Office"
   - Location: "123 Test Street"
4. Click "Create Site"
5. Site should appear in the list

#### Create Sublocation
1. Click "Sublocations" tab
2. Click "Create Sublocation"
3. Fill in:
   - Site: Select "Test Site"
   - Name: "Reception"
   - Area Type: "Lobby"
4. Click "Create Sublocation"
5. Sublocation should appear

#### Create Camera
1. Click "Cameras" tab
2. Click "Create Camera"
3. Fill in:
   - Sublocation: "Test Site - Reception"
   - Name: "Reception Camera"
   - Type: "Generic RTSP"
   - RTSP URL: "rtsp://test:test@192.168.1.100:554/stream"
4. Click "Create Camera"
5. Camera should appear in the list

## Troubleshooting

### Admin panel doesn't load
- **Check console for errors**
- Verify `/views/admin.html` exists
- Check network tab for failed requests

### "Failed to load admin panel" error
- Backend might not be running
- Check backend logs for errors
- Verify database is accessible

### Form submissions fail
- Check network tab for API responses
- Verify backend is running on port 8000
- Check backend logs for errors

### Organizations don't appear after creation
- Check API response in network tab
- Verify the organization was saved (check backend database)
- Try refreshing the page

## Expected API Endpoints

The following should be accessible:
- GET http://localhost:8000/api/organizations/
- POST http://localhost:8000/api/organizations/
- GET http://localhost:8000/api/sites/
- POST http://localhost:8000/api/sites/
- GET http://localhost:8000/api/sublocations/
- POST http://localhost:8000/api/sublocations/
- GET http://localhost:8000/api/cameras/
- POST http://localhost:8000/api/cameras/

## Success Criteria

✅ Admin tab loads without errors
✅ All four tabs (Organizations, Sites, Sublocations, Cameras) are visible
✅ Can create an organization
✅ Can create a site under the organization
✅ Can create a sublocation under the site
✅ Can create a camera in the sublocation
✅ All created items appear in their respective lists
✅ No console errors
✅ No backend errors

If all success criteria are met, the admin panel is working correctly!

