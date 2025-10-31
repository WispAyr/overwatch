// Content script for floating overlay on any webpage

let overlay = null;
let overlayMessages = [];
let overlayVisible = false;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'toggleOverlay') {
    toggleOverlay();
    sendResponse({ success: true });
  }
  
  if (message.action === 'newMessage') {
    if (overlayVisible && overlay) {
      addMessageToOverlay(message.message);
    }
    sendResponse({ success: true });
  }
  
  return true;
});

// Toggle overlay
function toggleOverlay() {
  if (overlayVisible) {
    hideOverlay();
  } else {
    showOverlay();
  }
}

// Show overlay
function showOverlay() {
  if (overlay) {
    overlay.style.display = 'block';
    overlayVisible = true;
    return;
  }
  
  // Create overlay
  overlay = document.createElement('div');
  overlay.id = 'overwatch-debug-overlay';
  overlay.innerHTML = `
    <div class="overwatch-overlay-header">
      <div class="overwatch-overlay-title">🐛 Overwatch Debug</div>
      <div class="overwatch-overlay-controls">
        <button id="overwatch-clear-btn" title="Clear messages">🗑️</button>
        <button id="overwatch-minimize-btn" title="Minimize">−</button>
        <button id="overwatch-close-btn" title="Close">×</button>
      </div>
    </div>
    <div class="overwatch-overlay-content" id="overwatch-overlay-content">
      <div class="overwatch-overlay-empty">Waiting for debug messages...</div>
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    #overwatch-debug-overlay {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 400px;
      max-height: 500px;
      background: #0a0e14;
      border: 2px solid #22d3ee;
      border-radius: 8px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
      z-index: 999999;
      font-family: 'Courier New', monospace;
      display: flex;
      flex-direction: column;
      resize: both;
      overflow: hidden;
    }
    
    .overwatch-overlay-header {
      background: #0d1117;
      padding: 10px 12px;
      border-bottom: 1px solid #30363d;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: move;
      user-select: none;
    }
    
    .overwatch-overlay-title {
      color: #22d3ee;
      font-size: 13px;
      font-weight: 600;
    }
    
    .overwatch-overlay-controls {
      display: flex;
      gap: 6px;
    }
    
    .overwatch-overlay-controls button {
      background: transparent;
      border: 1px solid #30363d;
      color: #8b949e;
      width: 24px;
      height: 24px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    
    .overwatch-overlay-controls button:hover {
      background: #21262d;
      color: #e6e6e6;
      border-color: #22d3ee;
    }
    
    .overwatch-overlay-content {
      flex: 1;
      overflow-y: auto;
      padding: 10px;
      background: #0a0e14;
    }
    
    .overwatch-overlay-content::-webkit-scrollbar {
      width: 6px;
    }
    
    .overwatch-overlay-content::-webkit-scrollbar-track {
      background: #161b22;
    }
    
    .overwatch-overlay-content::-webkit-scrollbar-thumb {
      background: #30363d;
      border-radius: 3px;
    }
    
    .overwatch-overlay-empty {
      text-align: center;
      color: #6e7681;
      font-size: 12px;
      padding: 20px;
    }
    
    .overwatch-overlay-message {
      margin-bottom: 8px;
      padding: 8px;
      background: #161b22;
      border-left: 3px solid #30363d;
      border-radius: 2px;
      font-size: 11px;
      animation: slideIn 0.2s ease-out;
    }
    
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(10px); }
      to { opacity: 1; transform: translateX(0); }
    }
    
    .overwatch-overlay-message.debug { border-left-color: #3b82f6; }
    .overwatch-overlay-message.detection { border-left-color: #22d3ee; }
    .overwatch-overlay-message.error { border-left-color: #ef4444; }
    .overwatch-overlay-message.status { border-left-color: #f59e0b; }
    
    .overwatch-message-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      font-size: 10px;
    }
    
    .overwatch-message-type {
      color: #22d3ee;
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .overwatch-message-time {
      color: #6e7681;
    }
    
    .overwatch-message-content {
      color: #e6e6e6;
      white-space: pre-wrap;
      word-break: break-word;
    }
    
    #overwatch-debug-overlay.minimized .overwatch-overlay-content {
      display: none;
    }
    
    #overwatch-debug-overlay.minimized {
      max-height: 44px;
      resize: none;
    }
  `;
  
  document.head.appendChild(style);
  document.body.appendChild(overlay);
  
  // Make draggable
  makeDraggable(overlay);
  
  // Add event listeners
  document.getElementById('overwatch-close-btn').addEventListener('click', hideOverlay);
  document.getElementById('overwatch-minimize-btn').addEventListener('click', () => {
    overlay.classList.toggle('minimized');
  });
  document.getElementById('overwatch-clear-btn').addEventListener('click', () => {
    overlayMessages = [];
    renderOverlayMessages();
  });
  
  overlayVisible = true;
}

// Hide overlay
function hideOverlay() {
  if (overlay) {
    overlay.style.display = 'none';
  }
  overlayVisible = false;
}

// Add message to overlay
function addMessageToOverlay(msg) {
  overlayMessages.unshift(msg);
  
  // Limit to 50 messages
  if (overlayMessages.length > 50) {
    overlayMessages = overlayMessages.slice(0, 50);
  }
  
  renderOverlayMessages();
}

// Render overlay messages
function renderOverlayMessages() {
  const content = document.getElementById('overwatch-overlay-content');
  if (!content) return;
  
  if (overlayMessages.length === 0) {
    content.innerHTML = '<div class="overwatch-overlay-empty">Waiting for debug messages...</div>';
    return;
  }
  
  content.innerHTML = overlayMessages.map(msg => {
    const typeClass = msg.type.replace('_', '-');
    const time = new Date(msg.timestamp).toLocaleTimeString();
    
    return `
      <div class="overwatch-overlay-message ${typeClass}">
        <div class="overwatch-message-header">
          <span class="overwatch-message-type">${msg.type}</span>
          <span class="overwatch-message-time">${time}</span>
        </div>
        <div class="overwatch-message-content">${escapeHtml(msg.message.substring(0, 200))}</div>
      </div>
    `;
  }).join('');
  
  content.scrollTop = 0;
}

// Make element draggable
function makeDraggable(element) {
  let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  const header = element.querySelector('.overwatch-overlay-header');
  
  header.onmousedown = dragMouseDown;
  
  function dragMouseDown(e) {
    e.preventDefault();
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    document.onmousemove = elementDrag;
  }
  
  function elementDrag(e) {
    e.preventDefault();
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    element.style.top = (element.offsetTop - pos2) + 'px';
    element.style.left = (element.offsetLeft - pos1) + 'px';
    element.style.right = 'auto';
    element.style.bottom = 'auto';
  }
  
  function closeDragElement() {
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

