// Alarm Management Module

// Load alarms from API
async function loadAlarms() {
    try {
        const severity = document.getElementById('alarm-filter-severity')?.value || '';
        const site = document.getElementById('alarm-filter-site')?.value || '';
        
        let url = `${API_BASE}/api/alarms?limit=100`;
        if (severity) url += `&severity=${severity}`;
        if (site) url += `&site=${site}`;
        
        const response = await fetch(url);
        const data = await response.json();
        app.alarms = data.alarms || [];
        
        renderAlarms();
        updateAlarmCounts();
        
    } catch (error) {
        console.error('Failed to load alarms:', error);
    }
}

// Render alarms in Kanban lanes
function renderAlarms() {
    const states = ['NEW', 'TRIAGE', 'SNOOZED', 'ACTIVE', 'CONTAINED', 'RESOLVED', 'SUPPRESSED', 'CLOSED'];
    
    states.forEach(state => {
        const laneId = `lane-${state.toLowerCase()}`;
        const lane = document.getElementById(laneId);
        if (!lane) return;
        
        // Filter alarms by state
        const stateAlarms = app.alarms.filter(a => a.state === state);
        
        // Clear lane
        lane.innerHTML = '';
        
        // Render alarm cards
        if (stateAlarms.length === 0) {
            lane.innerHTML = '<div class="text-gray-600 text-sm text-center py-8">No alarms</div>';
        } else {
            stateAlarms.forEach(alarm => {
                const card = createAlarmCard(alarm);
                lane.appendChild(card);
            });
        }
        
        // Update lane count
        const countId = `lane-count-${state.toLowerCase()}`;
        const countEl = document.getElementById(countId);
        if (countEl) {
            countEl.textContent = stateAlarms.length;
        }
    });
}

// Create alarm card HTML element
function createAlarmCard(alarm) {
    const card = document.createElement('div');
    card.className = `alarm-card alarm-card-${alarm.severity}`;
    card.onclick = () => showAlarmDetail(alarm.id);
    
    // Calculate SLA status
    const slaStatus = calculateSLAStatus(alarm);
    
    // Checkbox for bulk selection
    const checkboxHtml = app.bulkMode ? `
        <input type="checkbox" 
               class="alarm-checkbox mr-2" 
               data-alarm-id="${alarm.id}"
               onclick="event.stopPropagation(); toggleAlarmSelection('${alarm.id}')"
               ${app.selectedAlarms?.includes(alarm.id) ? 'checked' : ''}>
    ` : '';
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-2">
            <div class="flex items-start flex-1">
                ${checkboxHtml}
            <div class="flex-1">
                <div class="text-xs text-gray-500 mb-1">${alarm.id.substring(0, 12)}</div>
                <div class="font-semibold text-sm mb-1">${alarm.group_key}</div>
                </div>
            </div>
            <span class="badge badge-${alarm.severity} text-xs">${alarm.severity.toUpperCase()}</span>
        </div>
        
        <div class="text-xs text-gray-400 space-y-1">
            ${alarm.site ? `<div>📍 ${alarm.site}</div>` : ''}
            ${alarm.assignee ? `<div>👤 ${alarm.assignee}</div>` : '<div class="text-yellow-400">⚠ Unassigned</div>'}
            <div class="flex items-center justify-between mt-2">
                <span class="text-gray-500">${new Date(alarm.created_at).toLocaleTimeString()}</span>
                <span class="sla-timer ${slaStatus.class}" data-alarm-id="${alarm.id}">
                    ${slaStatus.text}
                </span>
            </div>
        </div>
        
        ${!app.bulkMode ? `
        <div class="flex gap-2 mt-3">
            ${alarm.state === 'NEW' ? `
                <button onclick="event.stopPropagation(); acknowledgeAlarm('${alarm.id}')" 
                        class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded">
                    Acknowledge
                </button>
            ` : ''}
            ${alarm.state === 'TRIAGE' && !alarm.assignee ? `
                <button onclick="event.stopPropagation(); assignAlarmToMe('${alarm.id}')" 
                        class="text-xs bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded">
                    Assign to Me
                </button>
            ` : ''}
            ${alarm.state === 'TRIAGE' || alarm.state === 'ACTIVE' ? `
                <button onclick="event.stopPropagation(); transitionAlarm('${alarm.id}', '${getNextState(alarm.state)}')" 
                        class="text-xs bg-orange-600 hover:bg-orange-700 text-white px-2 py-1 rounded">
                    ${getNextState(alarm.state)}
                </button>
            ` : ''}
        </div>
        ` : ''}
    `;
    
    return card;
}

// Calculate SLA status
function calculateSLAStatus(alarm) {
    if (!alarm.current_sla_deadline) {
        return { text: '--', class: 'sla-ok' };
    }
    
    const deadline = new Date(alarm.current_sla_deadline);
    const now = new Date();
    const diff = deadline - now;
    
    if (diff < 0) {
        const overdue = Math.abs(Math.floor(diff / 60000));
        return { 
            text: `SLA BREACH -${overdue}m`, 
            class: 'sla-breach' 
        };
    }
    
    const minutes = Math.floor(diff / 60000);
    if (minutes < 5) {
        return { 
            text: `${minutes}m`, 
            class: 'sla-warning' 
        };
    }
    
    return { 
        text: `${minutes}m`, 
        class: 'sla-ok' 
    };
}

// Update SLA timers every second
function updateSLATimers() {
    document.querySelectorAll('.sla-timer').forEach(el => {
        const alarmId = el.dataset.alarmId;
        const alarm = app.alarms.find(a => a.id === alarmId);
        if (alarm) {
            const status = calculateSLAStatus(alarm);
            el.textContent = status.text;
            el.className = `sla-timer ${status.class}`;
        }
    });
}

// Get next state in workflow
function getNextState(currentState) {
    const transitions = {
        'TRIAGE': 'ACTIVE',
        'ACTIVE': 'CONTAINED',
        'CONTAINED': 'RESOLVED'
    };
    return transitions[currentState] || 'RESOLVED';
}

// Update alarm count widgets
function updateAlarmCounts() {
    const states = ['NEW', 'TRIAGE', 'SNOOZED', 'ACTIVE', 'CONTAINED', 'RESOLVED', 'SUPPRESSED', 'CLOSED'];
    
    let total = 0;
    states.forEach(state => {
        const count = app.alarms.filter(a => a.state === state).length;
        total += count;
        
        const el = document.getElementById(`alarm-count-${state.toLowerCase()}`);
        if (el) el.textContent = count;
    });
    
    const totalEl = document.getElementById('alarm-count-total');
    if (totalEl) totalEl.textContent = total;
}

// Bulk operations
function toggleBulkMode() {
    app.bulkMode = !app.bulkMode;
    app.selectedAlarms = [];
    renderAlarms();
    updateBulkToolbar();
}

function toggleAlarmSelection(alarmId) {
    if (!app.selectedAlarms) app.selectedAlarms = [];
    
    const index = app.selectedAlarms.indexOf(alarmId);
    if (index === -1) {
        app.selectedAlarms.push(alarmId);
    } else {
        app.selectedAlarms.splice(index, 1);
    }
    updateBulkToolbar();
}

function selectAllAlarms() {
    app.selectedAlarms = app.alarms.map(a => a.id);
    renderAlarms();
    updateBulkToolbar();
}

function deselectAllAlarms() {
    app.selectedAlarms = [];
    renderAlarms();
    updateBulkToolbar();
}

function updateBulkToolbar() {
    const toolbar = document.getElementById('bulk-toolbar');
    const count = document.getElementById('bulk-count');
    
    if (toolbar && app.bulkMode) {
        toolbar.classList.remove('hidden');
        if (count) count.textContent = app.selectedAlarms?.length || 0;
    } else if (toolbar) {
        toolbar.classList.add('hidden');
    }
}

async function bulkTransition(toState) {
    if (!app.selectedAlarms || app.selectedAlarms.length === 0) {
        alert('No alarms selected');
        return;
    }
    
    const note = prompt(`Note for bulk transition to ${toState}:`) || `Bulk transitioned to ${toState}`;
    
    try {
        const promises = app.selectedAlarms.map(alarmId =>
            fetch(`${API_BASE}/api/alarms/${alarmId}/transition`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    to_state: toState,
                    user: app.currentUser,
                    note: note
                })
            })
        );
        
        await Promise.all(promises);
        app.selectedAlarms = [];
        await loadAlarms();
        
    } catch (error) {
        console.error('Failed to bulk transition:', error);
        alert('Failed to bulk transition alarms');
    }
}

async function bulkAssign() {
    if (!app.selectedAlarms || app.selectedAlarms.length === 0) {
        alert('No alarms selected');
        return;
    }
    
    const assignee = prompt('Assign to user:');
    if (!assignee) return;
    
    try {
        const promises = app.selectedAlarms.map(alarmId =>
            fetch(`${API_BASE}/api/alarms/${alarmId}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    assignee: assignee,
                    user: app.currentUser 
                })
            })
        );
        
        await Promise.all(promises);
        app.selectedAlarms = [];
        await loadAlarms();
        
    } catch (error) {
        console.error('Failed to bulk assign:', error);
        alert('Failed to bulk assign alarms');
    }
}

async function bulkUpdateSeverity() {
    if (!app.selectedAlarms || app.selectedAlarms.length === 0) {
        alert('No alarms selected');
        return;
    }
    
    const severity = prompt('New severity (info, minor, major, critical):');
    if (!severity) return;
    
    try {
        const promises = app.selectedAlarms.map(alarmId =>
            fetch(`${API_BASE}/api/alarms/${alarmId}/severity`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    severity: severity,
                    user: app.currentUser
                })
            })
        );
        
        await Promise.all(promises);
        app.selectedAlarms = [];
        await loadAlarms();
        
    } catch (error) {
        console.error('Failed to bulk update severity:', error);
        alert('Failed to bulk update severity');
    }
}

// Search and filter
function searchAlarms() {
    const query = document.getElementById('alarm-search')?.value?.toLowerCase();
    if (!query) {
        renderAlarms();
        return;
    }
    
    // Filter alarms by search query
    const filtered = app.alarms.filter(alarm => 
        alarm.id.toLowerCase().includes(query) ||
        alarm.group_key.toLowerCase().includes(query) ||
        alarm.assignee?.toLowerCase().includes(query) ||
        alarm.site?.toLowerCase().includes(query)
    );
    
    // Render filtered results
    renderFilteredAlarms(filtered);
}

function renderFilteredAlarms(filteredAlarms) {
    const states = ['NEW', 'TRIAGE', 'SNOOZED', 'ACTIVE', 'CONTAINED', 'RESOLVED', 'SUPPRESSED', 'CLOSED'];
    
    states.forEach(state => {
        const laneId = `lane-${state.toLowerCase()}`;
        const lane = document.getElementById(laneId);
        if (!lane) return;
        
        const stateAlarms = filteredAlarms.filter(a => a.state === state);
        
        lane.innerHTML = '';
        
        if (stateAlarms.length === 0) {
            lane.innerHTML = '<div class="text-gray-600 text-sm text-center py-8">No alarms</div>';
        } else {
            stateAlarms.forEach(alarm => {
                const card = createAlarmCard(alarm);
                lane.appendChild(card);
            });
        }
    });
}

// Export alarms
async function exportAlarms(format = 'json') {
    try {
        const alarms = app.selectedAlarms && app.selectedAlarms.length > 0
            ? app.alarms.filter(a => app.selectedAlarms.includes(a.id))
            : app.alarms;
            
        let content, filename, mimeType;
        
        if (format === 'json') {
            content = JSON.stringify(alarms, null, 2);
            filename = `alarms-${new Date().toISOString()}.json`;
            mimeType = 'application/json';
        } else if (format === 'csv') {
            // Convert to CSV
            const headers = ['ID', 'State', 'Severity', 'Site', 'Assignee', 'Created', 'Updated'];
            const rows = alarms.map(a => [
                a.id,
                a.state,
                a.severity,
                a.site || '',
                a.assignee || '',
                a.created_at,
                a.updated_at
            ]);
            
            content = [headers, ...rows]
                .map(row => row.map(cell => `"${cell}"`).join(','))
                .join('\n');
                
            filename = `alarms-${new Date().toISOString()}.csv`;
            mimeType = 'text/csv';
        }
        
        // Create download link
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Failed to export alarms:', error);
        alert('Failed to export alarms');
    }
}

// Advanced filtering
function applyAdvancedFilters() {
    const stateFilter = Array.from(document.querySelectorAll('input[name="state-filter"]:checked'))
        .map(el => el.value);
    const severityFilter = Array.from(document.querySelectorAll('input[name="severity-filter"]:checked'))
        .map(el => el.value);
    const assigneeFilter = document.getElementById('assignee-filter')?.value?.toLowerCase();
    const dateFrom = document.getElementById('date-from')?.value;
    const dateTo = document.getElementById('date-to')?.value;
    
    let filtered = app.alarms;
    
    // Filter by state
    if (stateFilter.length > 0) {
        filtered = filtered.filter(a => stateFilter.includes(a.state));
    }
    
    // Filter by severity
    if (severityFilter.length > 0) {
        filtered = filtered.filter(a => severityFilter.includes(a.severity));
    }
    
    // Filter by assignee
    if (assigneeFilter) {
        filtered = filtered.filter(a => 
            a.assignee?.toLowerCase().includes(assigneeFilter) ||
            (!a.assignee && assigneeFilter === 'unassigned')
        );
    }
    
    // Filter by date range
    if (dateFrom) {
        const fromDate = new Date(dateFrom);
        filtered = filtered.filter(a => new Date(a.created_at) >= fromDate);
    }
    
    if (dateTo) {
        const toDate = new Date(dateTo);
        filtered = filtered.filter(a => new Date(a.created_at) <= toDate);
    }
    
    renderFilteredAlarms(filtered);
}

function clearAdvancedFilters() {
    // Uncheck all checkboxes
    document.querySelectorAll('input[name="state-filter"], input[name="severity-filter"]')
        .forEach(el => el.checked = false);
    
    // Clear text inputs
    const assigneeFilter = document.getElementById('assignee-filter');
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    
    if (assigneeFilter) assigneeFilter.value = '';
    if (dateFrom) dateFrom.value = '';
    if (dateTo) dateTo.value = '';
    
    renderAlarms();
}

// Acknowledge alarm
async function acknowledgeAlarm(alarmId) {
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/ack`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user: app.currentUser })
        });
        
        if (response.ok) {
            console.log('Alarm acknowledged');
            await loadAlarms();
        }
    } catch (error) {
        console.error('Failed to acknowledge alarm:', error);
        alert('Failed to acknowledge alarm');
    }
}

// Assign alarm to current user
async function assignAlarmToMe(alarmId) {
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                assignee: app.currentUser,
                user: app.currentUser 
            })
        });
        
        if (response.ok) {
            console.log('Alarm assigned');
            await loadAlarms();
        }
    } catch (error) {
        console.error('Failed to assign alarm:', error);
        alert('Failed to assign alarm');
    }
}

// Transition alarm to new state
async function transitionAlarm(alarmId, toState) {
    try {
        const note = prompt(`Note for transition to ${toState}:`) || `Transitioned to ${toState}`;
        
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/transition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                to_state: toState,
                user: app.currentUser,
                note: note
            })
        });
        
        if (response.ok) {
            console.log('Alarm transitioned');
            await loadAlarms();
        } else {
            const error = await response.json();
            alert(`Failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Failed to transition alarm:', error);
        alert('Failed to transition alarm');
    }
}

// Show alarm detail modal
async function showAlarmDetail(alarmId) {
    try {
        // Fetch full alarm details with history
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}?include_history=true`);
        const alarm = await response.json();
        
        // Get correlated events
        const eventsResponse = await fetch(`${API_BASE}/api/events?alarm_id=${alarmId}`);
        const eventsData = await eventsResponse.json();
        
        // Show modal
        displayAlarmDetailModal(alarm, eventsData.events || []);
        
    } catch (error) {
        console.error('Failed to load alarm details:', error);
        alert('Failed to load alarm details');
    }
}

// Display alarm detail modal
function displayAlarmDetailModal(alarm, events) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4';
    modal.onclick = (e) => {
        if (e.target === modal) closeAlarmModal();
    };
    
    const slaStatus = calculateSLAStatus(alarm);
    const watchers = alarm.watchers || [];
    const history = alarm.history || [];
    
    modal.innerHTML = `
        <div class="bg-gray-900 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col" onclick="event.stopPropagation()">
            <!-- Header -->
            <div class="bg-gray-800 px-6 py-4 flex items-center justify-between border-b border-gray-700">
                <div class="flex items-center gap-4">
                    <h2 class="text-xl font-bold">Alarm ${alarm.id}</h2>
                    <span class="badge badge-${alarm.severity}">${alarm.severity.toUpperCase()}</span>
                    <span class="px-3 py-1 rounded text-sm font-medium bg-blue-600">${alarm.state}</span>
                    <span class="sla-timer ${slaStatus.class}">${slaStatus.text}</span>
                </div>
                <button onclick="closeAlarmModal()" class="text-gray-400 hover:text-white text-2xl">&times;</button>
            </div>
            
            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-6">
                <div class="grid grid-cols-3 gap-6">
                    <!-- Left Column: Details & Actions -->
                    <div class="col-span-2 space-y-6">
                        <!-- Info -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Details</h3>
                            <div class="grid grid-cols-2 gap-3 text-sm">
                                <div><span class="text-gray-400">Group Key:</span> ${alarm.group_key}</div>
                                <div><span class="text-gray-400">Tenant:</span> ${alarm.tenant || 'N/A'}</div>
                                <div><span class="text-gray-400">Site:</span> ${alarm.site || 'N/A'}</div>
                                <div><span class="text-gray-400">Assignee:</span> ${alarm.assignee || 'Unassigned'}</div>
                                <div><span class="text-gray-400">Created:</span> ${new Date(alarm.created_at).toLocaleString()}</div>
                                <div><span class="text-gray-400">Updated:</span> ${new Date(alarm.updated_at).toLocaleString()}</div>
                                <div><span class="text-gray-400">Confidence:</span> ${Math.round((alarm.confidence || 0) * 100)}%</div>
                                <div><span class="text-gray-400">Runbook:</span> ${alarm.runbook_id || 'None'}</div>
                                <div class="col-span-2"><span class="text-gray-400">Escalation Policy:</span> ${alarm.escalation_policy || 'Default'}</div>
                            </div>
                        </div>
                        
                        <!-- State Transitions -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">State Transitions</h3>
                            <div class="flex flex-wrap gap-2">
                                ${getAvailableTransitions(alarm.state).map(state => `
                                    <button onclick="transitionAlarmFromModal('${alarm.id}', '${state}')" 
                                            class="px-3 py-1 rounded text-sm bg-blue-600 hover:bg-blue-700">
                                        ${state}
                                    </button>
                                `).join('')}
                                ${alarm.state === 'TRIAGE' ? `
                                    <button onclick="snoozeAlarmFromModal('${alarm.id}')" 
                                            class="px-3 py-1 rounded text-sm bg-yellow-600 hover:bg-yellow-700">
                                        SNOOZE
                                    </button>
                                ` : ''}
                                ${alarm.state !== 'SUPPRESSED' && alarm.state !== 'CLOSED' ? `
                                    <button onclick="suppressAlarmFromModal('${alarm.id}')" 
                                            class="px-3 py-1 rounded text-sm bg-red-600 hover:bg-red-700">
                                        SUPPRESS
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                        
                        <!-- Assignment -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Assignment</h3>
                            <div class="flex gap-2">
                                <input type="text" id="assign-user-input" 
                                       placeholder="Enter username" 
                                       class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                                <button onclick="assignAlarmFromModal('${alarm.id}')" 
                                        class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm">
                                    Assign
                                </button>
                            </div>
                        </div>
                        
                        <!-- Severity -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Severity Management</h3>
                            <div class="flex gap-2">
                                <select id="severity-select" class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                                    <option value="info" ${alarm.severity === 'info' ? 'selected' : ''}>Info</option>
                                    <option value="minor" ${alarm.severity === 'minor' ? 'selected' : ''}>Minor</option>
                                    <option value="major" ${alarm.severity === 'major' ? 'selected' : ''}>Major</option>
                                    <option value="critical" ${alarm.severity === 'critical' ? 'selected' : ''}>Critical</option>
                                </select>
                                <button onclick="updateSeverityFromModal('${alarm.id}')" 
                                        class="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded text-sm">
                                    Update
                                </button>
                            </div>
                        </div>
                        
                        <!-- Runbook & Policy -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Runbook & Escalation</h3>
                            <div class="space-y-2">
                                <div class="flex gap-2">
                                    <input type="text" id="runbook-input" 
                                           placeholder="Runbook ID" 
                                           value="${alarm.runbook_id || ''}"
                                           class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                                    <button onclick="updateRunbookFromModal('${alarm.id}')" 
                                            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm">
                                        Update
                                    </button>
                                </div>
                                <div class="flex gap-2">
                                    <input type="text" id="escalation-input" 
                                           placeholder="Escalation Policy" 
                                           value="${alarm.escalation_policy || ''}"
                                           class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                                    <button onclick="updateEscalationFromModal('${alarm.id}')" 
                                            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm">
                                        Update
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Watchers -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Watchers</h3>
                            <div class="space-y-2">
                                <div class="flex flex-wrap gap-2 mb-2">
                                    ${watchers.map(w => `
                                        <span class="px-2 py-1 bg-gray-700 rounded text-sm flex items-center gap-2">
                                            ${w}
                                            <button onclick="removeWatcherFromModal('${alarm.id}', '${w}')" 
                                                    class="text-red-400 hover:text-red-300">&times;</button>
                                        </span>
                                    `).join('') || '<span class="text-gray-500 text-sm">No watchers</span>'}
                                </div>
                                <div class="flex gap-2">
                                    <input type="text" id="watcher-input" 
                                           placeholder="Add watcher" 
                                           class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                                    <button onclick="addWatcherFromModal('${alarm.id}')" 
                                            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm">
                                        Add
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Notes -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Add Note</h3>
                            <div class="space-y-2">
                                <textarea id="note-input" 
                                          placeholder="Enter note..." 
                                          rows="3"
                                          class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"></textarea>
                                <button onclick="addNoteFromModal('${alarm.id}')" 
                                        class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm">
                                    Add Note
                                </button>
                            </div>
                        </div>
                        
                        <!-- Correlated Events -->
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">Correlated Events (${events.length})</h3>
                            <div class="space-y-2 max-h-64 overflow-y-auto">
                                ${events.map(evt => `
                                    <div class="bg-gray-700 rounded p-3 text-sm">
                                        <div class="flex items-start justify-between">
                                            <div class="flex-1">
                                                <div class="font-medium">${evt.id}</div>
                                                <div class="text-gray-400 text-xs mt-1">
                                                    ${evt.source?.subtype || evt.source?.type || 'Unknown'} - 
                                                    ${new Date(evt.timestamp).toLocaleString()}
                                                </div>
                                                ${evt.attributes?.description ? `
                                                    <div class="text-gray-300 text-xs mt-1">${evt.attributes.description}</div>
                                                ` : ''}
                                            </div>
                                            <span class="badge badge-${evt.severity} text-xs">${evt.severity}</span>
                                        </div>
                                    </div>
                                `).join('') || '<div class="text-gray-500 text-sm">No correlated events</div>'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right Column: History -->
                    <div class="space-y-6">
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h3 class="font-semibold mb-3">History Timeline</h3>
                            <div class="space-y-3 max-h-[calc(90vh-200px)] overflow-y-auto">
                                ${history.reverse().map(h => `
                                    <div class="border-l-2 border-blue-600 pl-3 pb-3">
                                        <div class="text-xs text-gray-400">${new Date(h.timestamp).toLocaleString()}</div>
                                        <div class="font-medium text-sm mt-1">${formatHistoryAction(h)}</div>
                                        ${h.user ? `<div class="text-xs text-gray-500 mt-1">by ${h.user}</div>` : ''}
                                        ${h.note ? `<div class="text-xs text-gray-300 mt-1 italic">"${h.note}"</div>` : ''}
                                    </div>
                                `).join('') || '<div class="text-gray-500 text-sm">No history</div>'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentAlarmModal = modal;
}

// Format history action for display
function formatHistoryAction(entry) {
    const actions = {
        'created': '🆕 Alarm Created',
        'transition': `🔄 ${entry.from_state} → ${entry.to_state}`,
        'assigned': '👤 Assigned',
        'note_added': '📝 Note Added',
        'event_correlated': '🔗 Event Correlated',
        'watcher_added': '👁️ Watcher Added',
        'watcher_removed': '👁️ Watcher Removed',
        'severity_changed': '⚠️ Severity Changed',
        'runbook_updated': '📋 Runbook Updated',
        'escalation_updated': '📢 Escalation Policy Updated'
    };
    return actions[entry.action] || entry.action;
}

// Get available state transitions
function getAvailableTransitions(currentState) {
    const transitions = {
        'NEW': ['TRIAGE'],
        'TRIAGE': ['ACTIVE', 'RESOLVED'],
        'SNOOZED': ['TRIAGE'],
        'ACTIVE': ['CONTAINED', 'RESOLVED'],
        'CONTAINED': ['RESOLVED', 'ACTIVE'],
        'RESOLVED': ['CLOSED', 'ACTIVE'],
        'CLOSED': [],
        'SUPPRESSED': []
    };
    return transitions[currentState] || [];
}

// Close alarm modal
function closeAlarmModal() {
    if (window.currentAlarmModal) {
        window.currentAlarmModal.remove();
        window.currentAlarmModal = null;
    }
}

// Transition alarm from modal
async function transitionAlarmFromModal(alarmId, toState) {
    const note = prompt(`Note for transition to ${toState}:`) || `Transitioned to ${toState}`;
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/transition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                to_state: toState,
                user: app.currentUser,
                note: note
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId); // Reopen with updated data
        } else {
            const error = await response.json();
            alert(`Failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Failed to transition alarm:', error);
        alert('Failed to transition alarm');
    }
}

// Snooze alarm
async function snoozeAlarmFromModal(alarmId) {
    const minutes = prompt('Snooze for how many minutes?', '30');
    if (!minutes) return;
    
    await transitionAlarmFromModal(alarmId, 'SNOOZED');
    
    // Set timer to auto-wake
    setTimeout(async () => {
        try {
            await fetch(`${API_BASE}/api/alarms/${alarmId}/transition`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    to_state: 'TRIAGE',
                    user: 'system',
                    note: `Auto-woken after ${minutes} minutes`
                })
            });
            await loadAlarms();
        } catch (error) {
            console.error('Failed to auto-wake alarm:', error);
        }
    }, parseInt(minutes) * 60 * 1000);
}

// Suppress alarm
async function suppressAlarmFromModal(alarmId) {
    const reason = prompt('Reason for suppression:');
    if (!reason) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/transition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                to_state: 'SUPPRESSED',
                user: app.currentUser,
                note: `Suppressed: ${reason}`
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
        } else {
            const error = await response.json();
            alert(`Failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Failed to suppress alarm:', error);
        alert('Failed to suppress alarm');
    }
}

// Assign alarm from modal
async function assignAlarmFromModal(alarmId) {
    const assignee = document.getElementById('assign-user-input')?.value;
    if (!assignee) {
        alert('Please enter a username');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                assignee: assignee,
                user: app.currentUser 
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to assign alarm:', error);
        alert('Failed to assign alarm');
    }
}

// Update severity from modal
async function updateSeverityFromModal(alarmId) {
    const severity = document.getElementById('severity-select')?.value;
    if (!severity) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/severity`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                severity: severity,
                user: app.currentUser
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to update severity:', error);
        alert('Failed to update severity');
    }
}

// Update runbook from modal
async function updateRunbookFromModal(alarmId) {
    const runbookId = document.getElementById('runbook-input')?.value;
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/runbook`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                runbook_id: runbookId,
                user: app.currentUser
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to update runbook:', error);
        alert('Failed to update runbook');
    }
}

// Update escalation policy from modal
async function updateEscalationFromModal(alarmId) {
    const policy = document.getElementById('escalation-input')?.value;
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/escalation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                escalation_policy: policy,
                user: app.currentUser
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to update escalation policy:', error);
        alert('Failed to update escalation policy');
    }
}

// Add watcher
async function addWatcherFromModal(alarmId) {
    const watcher = document.getElementById('watcher-input')?.value;
    if (!watcher) {
        alert('Please enter a username');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/watchers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                watcher: watcher,
                user: app.currentUser
            })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to add watcher:', error);
        alert('Failed to add watcher');
    }
}

// Remove watcher
async function removeWatcherFromModal(alarmId, watcher) {
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/watchers/${watcher}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user: app.currentUser })
        });
        
        if (response.ok) {
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to remove watcher:', error);
        alert('Failed to remove watcher');
    }
}

// Add note from modal
async function addNoteFromModal(alarmId) {
    const note = document.getElementById('note-input')?.value;
    if (!note) {
        alert('Please enter a note');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms/${alarmId}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                note: note,
                user: app.currentUser
            })
        });
        
        if (response.ok) {
            document.getElementById('note-input').value = '';
            closeAlarmModal();
            await loadAlarms();
            showAlarmDetail(alarmId);
        }
    } catch (error) {
        console.error('Failed to add note:', error);
        alert('Failed to add note');
    }
}

// Setup alarm filter change handlers
function setupAlarmFilters() {
    const severityFilter = document.getElementById('alarm-filter-severity');
    const siteFilter = document.getElementById('alarm-filter-site');
    
    if (severityFilter) {
        severityFilter.addEventListener('change', () => loadAlarms());
    }
    
    if (siteFilter) {
        siteFilter.addEventListener('change', () => loadAlarms());
    }
}

// Handle WebSocket alarm updates
function handleAlarmUpdate(message) {
    const { action, ...alarm } = message;
    
    console.log('Alarm update:', action, alarm.id);
    
    // Update local alarm list
    const index = app.alarms.findIndex(a => a.id === alarm.id);
    
    if (action === 'created') {
        if (index === -1) {
            app.alarms.push(alarm);
        }
    } else if (action === 'updated' || action === 'transitioned' || action === 'assigned') {
        if (index !== -1) {
            app.alarms[index] = alarm;
        } else {
            app.alarms.push(alarm);
        }
    }
    
    // Re-render
    renderAlarms();
    updateAlarmCounts();
}

// Make functions globally available
window.loadAlarms = loadAlarms;
window.acknowledgeAlarm = acknowledgeAlarm;
window.assignAlarmToMe = assignAlarmToMe;
window.transitionAlarm = transitionAlarm;
window.showAlarmDetail = showAlarmDetail;
window.setupAlarmFilters = setupAlarmFilters;
window.updateSLATimers = updateSLATimers;
window.handleAlarmUpdate = handleAlarmUpdate;

// Bulk operations
window.toggleBulkMode = toggleBulkMode;
window.toggleAlarmSelection = toggleAlarmSelection;
window.selectAllAlarms = selectAllAlarms;
window.deselectAllAlarms = deselectAllAlarms;
window.bulkTransition = bulkTransition;
window.bulkAssign = bulkAssign;
window.bulkUpdateSeverity = bulkUpdateSeverity;

// Search and filter
window.searchAlarms = searchAlarms;
window.applyAdvancedFilters = applyAdvancedFilters;
window.clearAdvancedFilters = clearAdvancedFilters;

// Export
window.exportAlarms = exportAlarms;

// Modal functions
window.closeAlarmModal = closeAlarmModal;
window.transitionAlarmFromModal = transitionAlarmFromModal;
window.snoozeAlarmFromModal = snoozeAlarmFromModal;
window.suppressAlarmFromModal = suppressAlarmFromModal;
window.assignAlarmFromModal = assignAlarmFromModal;
window.updateSeverityFromModal = updateSeverityFromModal;
window.updateRunbookFromModal = updateRunbookFromModal;
window.updateEscalationFromModal = updateEscalationFromModal;
window.addWatcherFromModal = addWatcherFromModal;
window.removeWatcherFromModal = removeWatcherFromModal;
window.addNoteFromModal = addNoteFromModal;

