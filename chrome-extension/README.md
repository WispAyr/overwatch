# Overwatch Debug Console - Chrome Extension

Direct access to your Overwatch monitoring system's debug console from your browser.

## Features

- 🔌 **Real-time WebSocket Connection** - Live debug messages from your Overwatch backend
- 🎯 **Smart Filtering** - Filter by message type (debug, detection, error, status)
- 🔍 **Search** - Search through debug messages
- 📊 **Stats** - Message count and rate monitoring
- 🎨 **Clean UI** - Dark mode SpaceX-inspired interface
- 🪟 **Floating Overlay** - Optional draggable debug console on any webpage
- ⚙️ **Configurable** - Customize WebSocket URL and auto-connect behavior

## Installation

### Method 1: Load Unpacked (Development)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder from your Overwatch directory
5. The extension icon should appear in your toolbar

### Method 2: Pack Extension (Production)

1. Navigate to `chrome://extensions/`
2. Click "Pack extension"
3. Select the `chrome-extension` folder
4. Chrome will create a `.crx` file you can distribute

## Usage

### Basic Usage

1. **Start Overwatch Backend**
   ```bash
   cd /path/to/overwatch
   ./run.sh
   ```
   Backend should be running on port 8000

2. **Click Extension Icon**
   The popup will open with the debug console

3. **Click "Connect"**
   Connects to `ws://localhost:8000/api/ws`

4. **View Live Debug Messages**
   All workflow debug messages will stream in real-time

### Floating Overlay

1. Open the extension popup
2. Click the "Overlay" button
3. A draggable debug console will appear on the current webpage
4. Drag it anywhere, resize it, minimize it
5. Messages from the popup will also appear in the overlay

### Filtering

- **Type Filter**: Select message type (All, Debug, Detections, Errors, Status)
- **Search**: Type in search box to filter messages by content
- **Max Messages**: Limit how many messages are stored (50-500)

### Settings

Click the ⚙️ Settings button to configure:

- **WebSocket URL**: Change if backend is on different host/port
- **Auto-connect**: Automatically connect when popup opens
- **Overlay Settings**: Enable/disable and set default position

## Features in Detail

### Message Types

- **Debug Messages** (`debug_message`) - General debug output
- **Detection Data** (`detection_data`) - AI model detections
- **Errors** (`node_error`) - Node execution errors
- **Status Updates** (`status_update`) - Workflow status changes

### Stats Display

- **Message Count**: Total messages received
- **Message Rate**: Messages per second

### Connection Indicator

- 🔴 **Red dot**: Disconnected
- 🟢 **Green dot** (pulsing): Connected

## Keyboard Shortcuts

While popup is focused:
- Press `Escape` to close popup
- `Ctrl+K` / `Cmd+K` to focus search (browser default)

## Troubleshooting

### "Connection Failed"

1. Ensure Overwatch backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check WebSocket endpoint:
   ```bash
   wscat -c ws://localhost:8000/api/ws
   ```

3. Verify URL in Settings matches your backend

### "No Messages"

1. Ensure workflows are running
2. Check that workflow nodes are configured correctly
3. Verify Debug Console node is connected in workflow builder

### "Overlay Not Showing"

1. Check that content script permissions are enabled
2. Try refreshing the webpage
3. Check browser console for errors (`F12`)

## Development

### File Structure

```
chrome-extension/
├── manifest.json       # Extension manifest (v3)
├── popup.html         # Main popup UI
├── popup.js           # Popup logic
├── background.js      # Service worker
├── content.js         # Content script for overlay
├── options.html       # Settings page
├── options.js         # Settings logic
├── icons/            # Extension icons
└── README.md         # This file
```

### Building Icons

You need to create icons in three sizes:
- 16x16 (`icons/icon16.png`)
- 48x48 (`icons/icon48.png`)
- 128x128 (`icons/icon128.png`)

Use the Overwatch logo or a debug/bug icon.

### Testing

1. Make changes to source files
2. Click "Reload" button on extension card in `chrome://extensions/`
3. Open/reopen popup to test changes

## Permissions

- `storage`: Store user settings
- `activeTab`: Access current tab for overlay
- `http://localhost/*`: Connect to local backend
- `ws://localhost/*`: WebSocket connection

## Future Enhancements

- [ ] Export messages to JSON/CSV
- [ ] Message bookmarking/starring
- [ ] Custom message alerts/notifications
- [ ] Multiple backend connections
- [ ] Persistent connection in service worker
- [ ] Message replay/history
- [ ] Advanced filtering (regex, custom rules)
- [ ] Performance graphs/charts

## License

Same as Overwatch project

## Support

For issues or questions, check the main Overwatch documentation or create an issue in the repository.

