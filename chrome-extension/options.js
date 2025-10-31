// DOM elements
const wsUrlInput = document.getElementById('wsUrl');
const autoConnectInput = document.getElementById('autoConnect');
const overlayEnabledInput = document.getElementById('overlayEnabled');
const overlayPositionInput = document.getElementById('overlayPosition');
const saveBtn = document.getElementById('saveBtn');
const resetBtn = document.getElementById('resetBtn');
const statusEl = document.getElementById('status');

// Load settings
function loadSettings() {
  chrome.storage.local.get(null, (settings) => {
    wsUrlInput.value = settings.wsUrl || 'ws://localhost:8000/api/ws';
    autoConnectInput.checked = settings.autoConnect !== false;
    overlayEnabledInput.checked = settings.overlayEnabled || false;
    overlayPositionInput.value = settings.overlayPosition || 'bottom-right';
  });
}

// Save settings
function saveSettings() {
  const settings = {
    wsUrl: wsUrlInput.value,
    autoConnect: autoConnectInput.checked,
    overlayEnabled: overlayEnabledInput.checked,
    overlayPosition: overlayPositionInput.value
  };
  
  chrome.storage.local.set(settings, () => {
    // Show success message
    statusEl.classList.add('show');
    setTimeout(() => {
      statusEl.classList.remove('show');
    }, 3000);
  });
}

// Reset to defaults
function resetSettings() {
  const defaults = {
    wsUrl: 'ws://localhost:8000/api/ws',
    autoConnect: true,
    overlayEnabled: false,
    overlayPosition: 'bottom-right'
  };
  
  chrome.storage.local.set(defaults, () => {
    loadSettings();
    statusEl.textContent = 'Settings reset to defaults';
    statusEl.classList.add('show');
    setTimeout(() => {
      statusEl.classList.remove('show');
      statusEl.textContent = 'Settings saved successfully!';
    }, 3000);
  });
}

// Event listeners
saveBtn.addEventListener('click', saveSettings);
resetBtn.addEventListener('click', resetSettings);

// Load settings on page load
loadSettings();

