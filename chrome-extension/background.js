// Service worker for persistent WebSocket connection
// Note: Service workers can't maintain WebSocket connections indefinitely
// We'll use the popup as the main connection point, but keep this for future features

chrome.runtime.onInstalled.addListener(() => {
  console.log('Overwatch Debug Console extension installed');
  
  // Set default settings
  chrome.storage.local.set({
    wsUrl: 'ws://localhost:8000/api/ws',
    autoConnect: true,
    overlayEnabled: false,
    overlayPosition: 'bottom-right'
  });
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getSettings') {
    chrome.storage.local.get(null, (settings) => {
      sendResponse(settings);
    });
    return true; // Keep channel open for async response
  }
  
  if (message.action === 'saveSettings') {
    chrome.storage.local.set(message.settings, () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

// Badge to show connection status
function updateBadge(connected) {
  chrome.action.setBadgeText({ 
    text: connected ? '●' : '' 
  });
  chrome.action.setBadgeBackgroundColor({ 
    color: connected ? '#22c55e' : '#ef4444' 
  });
}

// Export for use in other scripts
self.updateBadge = updateBadge;

