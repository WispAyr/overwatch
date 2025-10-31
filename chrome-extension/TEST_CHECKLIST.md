# Chrome Extension Testing Checklist

Quick checklist to verify the extension works correctly after installation.

## ✅ Installation Tests

- [ ] Extension loads without errors in `chrome://extensions/`
- [ ] Extension icon appears in toolbar
- [ ] No console errors when loading extension (check with F12)
- [ ] All icons display correctly (16x16, 48x48, 128x128)

## ✅ Popup Tests

### Basic UI
- [ ] Popup opens when clicking extension icon
- [ ] Dark mode UI renders correctly
- [ ] All buttons are visible and styled properly
- [ ] Header shows "Overwatch Debug" with status indicator
- [ ] Stats show "0 msgs" and "0/s" initially

### Connection
- [ ] "Connect" button works
- [ ] Status indicator turns green when connected
- [ ] Status indicator is red when disconnected
- [ ] Connection info shows correct WebSocket URL
- [ ] Reconnects automatically if backend restarts

### Messages
- [ ] Messages appear in real-time when backend sends them
- [ ] Messages display with correct colors:
  - `debug_message` = blue border
  - `detection_data` = cyan border
  - `node_error` = red border
  - `status_update` = orange border
- [ ] Timestamps show correct local time
- [ ] Source/node ID displays correctly
- [ ] Detection data shows in expandable section (if present)
- [ ] Messages auto-scroll to newest at top

### Controls
- [ ] "Clear" button clears all messages
- [ ] "Pause" button stops new messages from appearing
- [ ] "Resume" (after pause) starts showing messages again
- [ ] Filter dropdown filters by message type correctly
- [ ] Search box filters messages by content
- [ ] Max messages limit works (50/100/200/500)

### Stats
- [ ] Message count increments correctly
- [ ] Message rate shows messages/second
- [ ] Rate updates every second
- [ ] Rate shows "0/s" when no messages

## ✅ Floating Overlay Tests

### Basic Functionality
- [ ] "Overlay" button in popup works
- [ ] Overlay appears on current webpage
- [ ] Overlay has dark background with cyan border
- [ ] Header shows "🐛 Overwatch Debug"

### Interaction
- [ ] Overlay can be dragged by header
- [ ] Overlay can be resized from bottom-right corner
- [ ] "−" (minimize) button collapses overlay
- [ ] "×" (close) button hides overlay
- [ ] "🗑️" (clear) button clears overlay messages
- [ ] Messages appear in overlay when received

### Display
- [ ] Messages show in same format as popup
- [ ] Messages truncated to 200 chars in overlay
- [ ] Auto-scrolls to newest messages
- [ ] Stays on top of page content (z-index)

### Edge Cases
- [ ] Overlay works on regular websites
- [ ] Overlay doesn't work on `chrome://` pages (expected)
- [ ] Multiple clicks on "Overlay" toggle it on/off
- [ ] Overlay position persists when minimizing/maximizing

## ✅ Settings Page Tests

### Access
- [ ] "⚙️ Settings" button opens options page
- [ ] Options page renders correctly
- [ ] All form fields are visible and styled

### Configuration
- [ ] WebSocket URL field shows default `ws://localhost:8000/api/ws`
- [ ] Auto-connect checkbox works
- [ ] Overlay enabled checkbox works
- [ ] Overlay position dropdown has all options
- [ ] "Save Settings" saves and shows success message
- [ ] "Reset to Defaults" restores default values

### Persistence
- [ ] Close and reopen popup - settings persist
- [ ] Changed WebSocket URL is used on next connection
- [ ] Auto-connect setting works on popup open
- [ ] Settings survive browser restart

## ✅ Error Handling

### Network Errors
- [ ] Shows error if backend is not running
- [ ] Shows "Connection error" in footer
- [ ] Status indicator stays/turns red
- [ ] Can retry connection by clicking "Connect" again
- [ ] No JavaScript errors in console on connection failure

### Message Errors
- [ ] Handles malformed JSON messages gracefully
- [ ] Logs errors to console but doesn't crash
- [ ] Continues processing valid messages after error

### UI Errors
- [ ] No layout breaks with long messages
- [ ] No layout breaks with many messages (100+)
- [ ] No memory leaks with continuous streaming
- [ ] Handles rapid message bursts (10+ msg/sec)

## ✅ Performance Tests

### Popup
- [ ] Opens instantly (< 500ms)
- [ ] Scrolling is smooth with 100+ messages
- [ ] Filtering/search is responsive
- [ ] No lag when receiving messages at 5+ msg/sec

### Overlay
- [ ] Doesn't slow down webpage rendering
- [ ] Dragging is smooth (60fps)
- [ ] Resizing is smooth
- [ ] Doesn't interfere with page JavaScript

### Memory
- [ ] Memory usage stays reasonable (< 50MB for popup)
- [ ] No memory leaks after 1000+ messages
- [ ] Message limit prevents unbounded growth
- [ ] Closing popup releases memory

## ✅ Cross-Browser Compatibility

### Chrome
- [ ] Works on Chrome 119+
- [ ] All features functional
- [ ] No console warnings

### Edge
- [ ] Works on Edge (Chromium-based)
- [ ] All features functional

### Brave
- [ ] Works on Brave browser
- [ ] All features functional

## ✅ Integration Tests

### With Overwatch Backend
- [ ] Receives `debug_message` from Debug Console nodes
- [ ] Receives `detection_data` from AI model nodes
- [ ] Receives `node_error` from failed nodes
- [ ] Receives `status_update` from workflow execution
- [ ] Message format matches backend output

### With Multiple Workflows
- [ ] Shows messages from all running workflows
- [ ] Can distinguish messages by source/node_id
- [ ] No message loss with multiple workflows

### With Dashboard
- [ ] Extension and dashboard can connect simultaneously
- [ ] Both receive same messages
- [ ] No conflicts or race conditions

## ✅ Documentation Tests

- [ ] README.md is clear and accurate
- [ ] QUICKSTART.md actually takes 2 minutes
- [ ] INSTALL.md covers all installation steps
- [ ] Screenshots/examples match actual UI
- [ ] Troubleshooting section covers common issues

## 🐛 Known Issues / Limitations

Document any issues found during testing:

- Service workers can't maintain persistent WebSocket connections (Chromium limitation)
- Content scripts don't work on `chrome://` pages (browser security)
- Overlay may not work on some secure sites with strict CSP

## ✅ Sign-Off

Tested by: _______________  
Date: _______________  
Browser Version: _______________  
Overwatch Version: _______________  

Notes:
_______________________________________________
_______________________________________________
_______________________________________________

