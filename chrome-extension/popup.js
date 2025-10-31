let ws = null;
let messages = [];
let isPaused = false;
let maxMessages = 100;
let filterType = 'all';
let searchQuery = '';
let messageCountTotal = 0;
let messageRateCounter = 0;
let lastRateUpdate = Date.now();

// DOM elements
const statusIndicator = document.getElementById('statusIndicator');
const messageCountEl = document.getElementById('messageCount');
const messageRateEl = document.getElementById('messageRate');
const consoleEl = document.getElementById('console');
const connectBtn = document.getElementById('connectBtn');
const clearBtn = document.getElementById('clearBtn');
const pauseBtn = document.getElementById('pauseBtn');
const overlayBtn = document.getElementById('overlayBtn');
const filterTypeEl = document.getElementById('filterType');
const searchInput = document.getElementById('searchInput');
const maxMessagesEl = document.getElementById('maxMessages');
const connectionInfoEl = document.getElementById('connectionInfo');
const settingsBtn = document.getElementById('settingsBtn');

// Load settings from storage
chrome.storage.local.get(['wsUrl', 'autoConnect'], (result) => {
  const wsUrl = result.wsUrl || 'ws://localhost:8000/api/ws';
  const autoConnect = result.autoConnect !== false; // default true
  
  if (autoConnect) {
    connectWebSocket(wsUrl);
  }
});

// Connect button
connectBtn.addEventListener('click', () => {
  chrome.storage.local.get(['wsUrl'], (result) => {
    const wsUrl = result.wsUrl || 'ws://localhost:8000/api/ws';
    if (ws && ws.readyState === WebSocket.OPEN) {
      disconnectWebSocket();
    } else {
      connectWebSocket(wsUrl);
    }
  });
});

// Clear button
clearBtn.addEventListener('click', () => {
  messages = [];
  messageCountTotal = 0;
  renderMessages();
  updateStats();
});

// Pause button
pauseBtn.addEventListener('click', () => {
  isPaused = !isPaused;
  pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
  pauseBtn.classList.toggle('active', isPaused);
});

// Overlay button
overlayBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'toggleOverlay' });
    }
  });
});

// Filter type
filterTypeEl.addEventListener('change', (e) => {
  filterType = e.target.value;
  renderMessages();
});

// Search
searchInput.addEventListener('input', (e) => {
  searchQuery = e.target.value.toLowerCase();
  renderMessages();
});

// Max messages
maxMessagesEl.addEventListener('change', (e) => {
  maxMessages = parseInt(e.target.value);
  messages = messages.slice(0, maxMessages);
  renderMessages();
});

// Settings button
settingsBtn.addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// Connect to WebSocket
function connectWebSocket(url) {
  try {
    connectionInfoEl.textContent = 'Connecting...';
    ws = new WebSocket(url);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      statusIndicator.classList.add('connected');
      connectBtn.textContent = 'Disconnect';
      connectionInfoEl.textContent = `Connected to ${url}`;
    };
    
    ws.onmessage = (event) => {
      if (isPaused) return;
      
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      connectionInfoEl.textContent = 'Connection error';
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      statusIndicator.classList.remove('connected');
      connectBtn.textContent = 'Connect';
      connectionInfoEl.textContent = 'Disconnected';
      ws = null;
    };
  } catch (error) {
    console.error('Error connecting to WebSocket:', error);
    connectionInfoEl.textContent = `Error: ${error.message}`;
  }
}

// Disconnect WebSocket
function disconnectWebSocket() {
  if (ws) {
    ws.close();
    ws = null;
  }
}

// Handle incoming message
function handleMessage(data) {
  // Track message rate
  messageRateCounter++;
  const now = Date.now();
  if (now - lastRateUpdate >= 1000) {
    const rate = messageRateCounter;
    messageRateEl.textContent = `${rate}/s`;
    messageRateCounter = 0;
    lastRateUpdate = now;
  }
  
  // Create message object
  const msg = {
    id: Date.now() + Math.random(),
    timestamp: data.timestamp || new Date().toISOString(),
    type: data.type || 'unknown',
    source: data.workflow_id || data.node_id || 'system',
    message: data.message || JSON.stringify(data, null, 2),
    detections: data.detections || [],
    raw: data
  };
  
  // Add to messages array
  messages.unshift(msg);
  
  // Limit message count
  if (messages.length > maxMessages) {
    messages = messages.slice(0, maxMessages);
  }
  
  messageCountTotal++;
  
  // Update UI
  renderMessages();
  updateStats();
  
  // Send to content script for overlay
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { 
        action: 'newMessage', 
        message: msg 
      }).catch(() => {}); // Ignore errors if content script not loaded
    }
  });
}

// Render messages
function renderMessages() {
  const filteredMessages = messages.filter(msg => {
    // Filter by type
    if (filterType !== 'all' && msg.type !== filterType) {
      return false;
    }
    
    // Filter by search query
    if (searchQuery) {
      const searchText = JSON.stringify(msg).toLowerCase();
      if (!searchText.includes(searchQuery)) {
        return false;
      }
    }
    
    return true;
  });
  
  if (filteredMessages.length === 0) {
    consoleEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <div>${messages.length === 0 ? 'No messages yet' : 'No messages match filters'}</div>
      </div>
    `;
    return;
  }
  
  consoleEl.innerHTML = filteredMessages.map(msg => {
    const typeClass = msg.type.replace('_', '-');
    const time = new Date(msg.timestamp).toLocaleTimeString();
    
    let detectionsHtml = '';
    if (msg.detections && msg.detections.length > 0) {
      detectionsHtml = `
        <div class="message-detections">
          <strong>Detections (${msg.detections.length}):</strong>
          ${msg.detections.map(d => `
            <div class="detection-item">
              ${d.class || d.label || 'Unknown'} 
              ${d.confidence ? `(${(d.confidence * 100).toFixed(1)}%)` : ''}
            </div>
          `).join('')}
        </div>
      `;
    }
    
    return `
      <div class="message ${typeClass}">
        <div class="message-header">
          <span class="message-type">${msg.type}</span>
          <span class="message-time">${time}</span>
        </div>
        <div class="message-source">Source: ${msg.source}</div>
        <div class="message-content">${escapeHtml(msg.message)}</div>
        ${detectionsHtml}
      </div>
    `;
  }).join('');
  
  // Auto-scroll to top (newest messages)
  consoleEl.scrollTop = 0;
}

// Update stats
function updateStats() {
  messageCountEl.textContent = messageCountTotal;
}

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Update message rate every second
setInterval(() => {
  if (messageRateCounter === 0 && messageRateEl.textContent !== '0/s') {
    messageRateEl.textContent = '0/s';
  }
}, 1000);

// Cleanup on unload
window.addEventListener('unload', () => {
  if (ws) {
    ws.close();
  }
});

