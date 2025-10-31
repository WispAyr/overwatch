# Installation Guide - Overwatch Debug Console Chrome Extension

## Quick Start

### 1. Generate Icons (if needed)

Icons are already generated, but if you need to regenerate them:

```bash
cd chrome-extension
python3 generate_icons.py
# OR
./generate_icons.sh  # requires: brew install librsvg
```

### 2. Load Extension in Chrome

1. Open Chrome browser
2. Navigate to: `chrome://extensions/`
3. Enable **Developer mode** (toggle switch in top-right corner)
4. Click **"Load unpacked"** button
5. Navigate to and select: `/Users/ewanrichardson/Development/overwatch/chrome-extension/`
6. Click **"Select"**

The extension should now appear in your extensions list with a 🐛 bug icon!

### 3. Pin Extension to Toolbar (Optional)

1. Click the puzzle piece icon in Chrome toolbar
2. Find "Overwatch Debug Console"
3. Click the pin icon to keep it visible

### 4. Start Using

1. **Start Overwatch Backend:**
   ```bash
   cd /Users/ewanrichardson/Development/overwatch
   ./run.sh
   ```

2. **Click the extension icon** in your toolbar

3. **Click "Connect"** to start receiving debug messages

## Features Quick Tour

### Main Popup

- **Connect/Disconnect**: Toggle WebSocket connection
- **Clear**: Clear all messages
- **Pause/Resume**: Pause message updates
- **Filter**: Filter by message type (all, debug, detection, error, status)
- **Search**: Search through messages
- **Max Messages**: Limit message history (50-500)

### Floating Overlay

1. Click the **"Overlay"** button in popup
2. A draggable debug console appears on the current webpage
3. **Drag** the header to move it
4. **Resize** using bottom-right corner
5. **Minimize** using the − button
6. **Close** using the × button

### Settings

1. Click the **⚙️ Settings** button
2. Configure:
   - WebSocket URL (default: `ws://localhost:8000/api/ws`)
   - Auto-connect on popup open
   - Overlay preferences

## Troubleshooting

### Extension Won't Load

**Error: "Manifest file is missing or unreadable"**
- Ensure you selected the `chrome-extension` folder, not a parent folder
- Check that `manifest.json` exists in the selected folder

**Error: "Icons missing"**
- Run `python3 generate_icons.py` in the chrome-extension folder
- Or manually place 16x16, 48x48, and 128x128 PNG icons in the `icons/` folder

### Can't Connect to WebSocket

**"Connection error" or "Disconnected"**

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check WebSocket endpoint:
   ```bash
   # Install wscat if needed: npm install -g wscat
   wscat -c ws://localhost:8000/api/ws
   ```

3. Check Settings in extension - ensure URL is correct

### No Messages Appearing

1. Ensure workflows are **deployed and running**
2. Check that **Debug Console node** is connected in your workflow
3. Look at browser console (F12) for JavaScript errors
4. Try toggling filter to "All Messages"

### Overlay Not Working

1. **Refresh the webpage** after installing extension
2. Check that content script permissions are enabled
3. Some pages (like `chrome://` pages) block content scripts - try a regular webpage

## Updating the Extension

After making changes to the extension code:

1. Go to `chrome://extensions/`
2. Find "Overwatch Debug Console"
3. Click the **🔄 Reload** button
4. Close and reopen the popup to see changes

## Uninstalling

1. Go to `chrome://extensions/`
2. Find "Overwatch Debug Console"
3. Click **"Remove"**

## Advanced Usage

### Remote Backend

To connect to a remote Overwatch instance:

1. Open extension Settings (⚙️ button)
2. Change WebSocket URL to: `ws://your-server-ip:8000/api/ws`
3. Save settings
4. Click Connect in popup

### Multiple Instances

To monitor multiple Overwatch instances:
- Currently not supported, but you can install the extension multiple times with different IDs
- Or manually switch the WebSocket URL in Settings

## File Structure

```
chrome-extension/
├── manifest.json          # Extension configuration
├── popup.html            # Main UI
├── popup.js              # Popup logic
├── background.js         # Service worker
├── content.js            # Overlay/content script
├── options.html          # Settings page
├── options.js            # Settings logic
├── icons/
│   ├── icon16.png       # 16x16 toolbar icon
│   ├── icon48.png       # 48x48 management icon
│   └── icon128.png      # 128x128 store icon
├── generate_icons.py     # Icon generator (Python)
├── generate_icons.sh     # Icon generator (Shell)
├── README.md            # Documentation
└── INSTALL.md           # This file
```

## Next Steps

- Try the floating overlay feature
- Customize settings to your preference
- Set up custom filters for your workflows
- Explore the message details and detection data

Enjoy your direct debug console access! 🐛

