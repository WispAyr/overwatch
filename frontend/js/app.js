// Overwatch Dashboard Application

const API_BASE = 'http://localhost:8000';  // API server port
const WS_BASE = 'ws://localhost:8000';      // WebSocket on API server

class OverwatchApp {
    constructor() {
        this.ws = null;
        this.cameras = [];
        this.events = [];
        this.alarms = [];
        this.hierarchy = null;
        this.federationStatus = null;
        this.currentUser = 'operator';  // TODO: Replace with actual auth
        
        this.init();
    }
    
    async init() {
        console.log('Initializing Overwatch Dashboard...');
        
        // Load initial data
        await this.loadSystemStatus();
        await this.loadHierarchy();
        await this.loadCameras();
        await this.loadEvents();
        if (typeof loadAlarms === 'function') {
            await loadAlarms();
        }
        await this.loadFederationStatus();
        
        // Connect WebSocket for live updates
        this.connectWebSocket();
        
        // Start periodic updates
        setInterval(() => this.loadSystemStatus(), 5000);
        setInterval(() => this.loadEvents(), 10000);
        if (typeof loadAlarms === 'function') {
            setInterval(() => loadAlarms(), 15000);
        }
        if (typeof updateSLATimers === 'function') {
            setInterval(() => updateSLATimers(), 1000);
        }
        setInterval(() => this.loadWorkflows(), 30000);  // Refresh workflows every 30s
        
        // Setup alarm filters (defined in alarms.js)
        if (typeof setupAlarmFilters === 'function') {
            setupAlarmFilters();
        }
        
        // Load workflows
        await this.loadWorkflows();
        
        console.log('Dashboard initialized');
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch(`${API_BASE}/api/system/status`);
            const data = await response.json();
            
            document.getElementById('stat-cameras').textContent = data.active_streams || 0;
            document.getElementById('stat-events').textContent = data.total_events || 0;
            document.getElementById('stat-nodes').textContent = 
                this.federationStatus?.federated_nodes?.length || 0;
                
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }
    
    async loadHierarchy() {
        try {
            const response = await fetch(`${API_BASE}/api/hierarchy/tree`);
            this.hierarchy = await response.json();
            this.renderOrgTree();
        } catch (error) {
            console.error('Failed to load hierarchy:', error);
        }
    }
    
    async loadCameras() {
        try {
            const response = await fetch(`${API_BASE}/api/cameras/`);
            const data = await response.json();
            this.cameras = data.cameras || [];
            this.renderCameraGrid();
        } catch (error) {
            console.error('Failed to load cameras:', error);
        }
    }
    
    async loadEvents() {
        try {
            const filter = document.getElementById('event-filter')?.value || '';
            let url = `${API_BASE}/api/events/?limit=50`;  // Added trailing slash
            if (filter) url += `&severity=${filter}`;
            
            const response = await fetch(url);
            const data = await response.json();
            this.events = data.events || [];
            this.renderEvents();
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    }
    
    async loadFederationStatus() {
        try {
            const response = await fetch(`${API_BASE}/api/federation/cluster/status`);
            this.federationStatus = await response.json();
            this.renderFederationStatus();
            
            // Try to load ZeroTier status
            try {
                const ztResponse = await fetch(`${API_BASE}/api/zerotier/status`);
                if (ztResponse.ok) {
                    const ztData = await ztResponse.json();
                    this.renderZeroTierStatus(ztData);
                }
            } catch (e) {
                // ZeroTier not enabled
            }
        } catch (error) {
            console.error('Failed to load federation status:', error);
        }
    }
    
    renderOrgTree() {
        const container = document.getElementById('org-tree');
        if (!this.hierarchy || !this.hierarchy.organizations) {
            container.innerHTML = '<p class="text-gray-500">No organizations configured</p>';
            return;
        }
        
        container.innerHTML = this.hierarchy.organizations.map(org => `
            <div class="mb-4">
                <div class="org-node-title text-lg">${org.name}</div>
                <div class="org-node mt-2">
                    ${org.sites.map(site => `
                        <div class="mb-3">
                            <div class="flex items-center space-x-2">
                                <span class="org-node-title">${site.name}</span>
                                <span class="badge badge-${site.site_type === 'mobile' ? 'warning' : 'info'}">
                                    ${site.site_type}
                                </span>
                            </div>
                            <div class="org-node mt-2">
                                ${site.sublocations.map(sl => `
                                    <div class="mb-2">
                                        <div class="text-sm text-gray-400">${sl.name}</div>
                                        <div class="text-xs text-gray-500 mt-1">
                                            ${sl.cameras.length} camera${sl.cameras.length !== 1 ? 's' : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }
    
    renderCameraGrid() {
        const container = document.getElementById('camera-grid');
        
        if (this.cameras.length === 0) {
            container.innerHTML = '<p class="text-gray-500 col-span-full text-center py-12">No cameras configured</p>';
            return;
        }
        
        container.innerHTML = this.cameras.map(camera => `
            <div class="camera-card" onclick="expandCamera('${camera.id}', '${camera.name}', '${camera.status?.fps || 0}')">
                <div class="camera-video cursor-pointer" id="video-container-${camera.id}">
                    ${camera.status?.running ? `
                        <img id="video-${camera.id}" 
                             src="${API_BASE}/api/video/${camera.id}/mjpeg"
                             class="w-full h-full object-contain bg-black" 
                             alt="${camera.name}">
                    ` : `
                        <div class="flex items-center justify-center h-full text-gray-600">
                            <div class="text-center">
                                <div>Camera Offline</div>
                                <div class="text-xs mt-2">${camera.name}</div>
                            </div>
                        </div>
                    `}
                </div>
                <div class="p-4">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="font-medium">${camera.name}</h3>
                        <span class="badge badge-${camera.status?.running ? 'success' : 'warning'}">
                            ${camera.status?.running ? 'Online' : 'Offline'}
                        </span>
                    </div>
                    <div class="flex items-center justify-between text-xs mb-2">
                        <span class="text-gray-500">
                            ${camera.status?.fps ? `${camera.status.fps} FPS` : 'No signal'}
                        </span>
                        ${camera.streams && Object.keys(camera.streams).length > 0 ? `
                            <select class="text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1"
                                    onchange="changeStreamQuality('${camera.id}', this.value)"
                                    onclick="event.stopPropagation()">
                                ${Object.keys(camera.streams).map(quality => `
                                    <option value="${quality}" ${camera.active_stream === quality ? 'selected' : ''}>
                                        ${quality.toUpperCase()}
                                    </option>
                                `).join('')}
                            </select>
                        ` : ''}
                    </div>
                    ${camera.workflows && camera.workflows.length > 0 ? `
                        <div class="mt-2 flex flex-wrap gap-1">
                            ${camera.workflows.map(w => `
                                <span class="badge badge-info text-xs">${w}</span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        // MJPEG streams are loaded automatically via img src
        // No additional player initialization needed
    }
    
    renderEvents() {
        const container = document.getElementById('events-list');
        const liveContainer = document.getElementById('live-events');
        
        if (this.events.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-12">No events recorded</p>';
            liveContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No recent events</p>';
            return;
        }
        
        const eventHTML = this.events.map(event => this.renderEvent(event)).join('');
        container.innerHTML = eventHTML;
        
        // Show last 5 events in live feed
        liveContainer.innerHTML = this.events.slice(0, 5).map(event => 
            this.renderEvent(event, true)
        ).join('');
    }
    
    renderEvent(event, compact = false) {
        const timestamp = new Date(event.timestamp).toLocaleString();
        const detectionCount = event.detections?.length || 0;
        const hasSnapshot = event.snapshot_path || event.id;
        
        if (compact) {
            return `
                <div class="event-card py-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="badge badge-${event.severity}">${event.severity}</span>
                            <span class="text-sm">${event.workflow_id}</span>
                        </div>
                        <span class="text-xs text-gray-500">${timestamp}</span>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="event-card">
                ${hasSnapshot ? `
                    <div class="mb-3">
                        <img src="${API_BASE}/api/snapshots/${event.id}" 
                             alt="Detection snapshot"
                             class="w-full rounded-lg border border-gray-700"
                             onerror="this.style.display='none'">
                    </div>
                ` : ''}
                
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-3">
                        <span class="badge badge-${event.severity}">${event.severity}</span>
                        <span class="font-medium">${event.workflow_id}</span>
                    </div>
                    <span class="text-sm text-gray-500">${timestamp}</span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm mb-3">
                    <div>
                        <span class="text-gray-500">Camera:</span>
                        <span class="text-gray-300 ml-2">${event.camera_id}</span>
                    </div>
                    <div>
                        <span class="text-gray-500">Detections:</span>
                        <span class="text-gray-300 ml-2">${detectionCount}</span>
                    </div>
                </div>
                
                ${event.detections && event.detections.length > 0 ? `
                    <div class="mt-3 pt-3 border-t border-gray-800">
                        <div class="flex flex-wrap gap-2">
                            ${event.detections.map(det => `
                                <span class="text-xs px-2 py-1 bg-gray-800 rounded">
                                    ${det.class_name} (${(det.confidence * 100).toFixed(0)}%)
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderFederationStatus() {
        const container = document.getElementById('federation-nodes');
        
        if (!this.federationStatus) {
            container.innerHTML = '<p class="text-gray-500">Federation not enabled</p>';
            return;
        }
        
        const nodes = [
            {
                ...this.federationStatus.local_node,
                isLocal: true
            },
            ...(this.federationStatus.federated_nodes || [])
        ];
        
        container.innerHTML = nodes.map(node => `
            <div class="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center space-x-3">
                        <h4 class="font-medium">${node.id}</h4>
                        ${node.isLocal ? '<span class="badge badge-info">Local</span>' : ''}
                    </div>
                    <span class="badge badge-${node.status === 'online' ? 'success' : 'warning'}">
                        ${node.status}
                    </span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm text-gray-400">
                    <div>Type: <span class="text-gray-300">${node.type}</span></div>
                    ${node.url ? `<div>URL: <span class="text-gray-300 text-xs">${node.url}</span></div>` : ''}
                    ${node.last_seen ? `<div class="col-span-2">Last seen: <span class="text-gray-300">${new Date(node.last_seen).toLocaleString()}</span></div>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    renderZeroTierStatus(data) {
        const container = document.getElementById('zerotier-status');
        
        // Enhanced status with health indicators (Comment 8)
        const statusBadge = data.online 
            ? '<span class="badge badge-success">Online</span>'
            : '<span class="badge badge-warning">Offline</span>';
        
        const healthIcon = data.last_error 
            ? '<span class="text-red-500">⚠️</span>'
            : '<span class="text-green-500">✓</span>';
        
        container.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                    <div class="text-sm text-gray-400 mb-1">Status</div>
                    <div>${statusBadge}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">Health</div>
                    <div class="flex items-center space-x-2">
                        ${healthIcon}
                        <span class="text-sm">${data.last_error || 'Healthy'}</span>
                    </div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">Peers</div>
                    <div class="text-lg font-semibold">${data.peer_count || 0}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">Members</div>
                    <div class="text-lg font-semibold">${data.member_count || 0}</div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-800">
                <div>
                    <div class="text-sm text-gray-400 mb-1">Node ID</div>
                    <div class="font-mono text-xs bg-gray-900/50 p-2 rounded">${data.node_id || 'N/A'}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">Network ID</div>
                    <div class="font-mono text-xs bg-gray-900/50 p-2 rounded">${data.network_id || 'N/A'}</div>
                </div>
                ${data.assigned_addresses && data.assigned_addresses.length > 0 ? `
                    <div class="col-span-2">
                        <div class="text-sm text-gray-400 mb-1">Assigned IPs</div>
                        <div class="font-mono text-sm text-blue-400">${data.assigned_addresses.join(', ')}</div>
                    </div>
                ` : ''}
            </div>
            
            ${data.member_count > 0 ? `
                <div class="mt-4">
                    <button onclick="app.showMemberList()" class="btn-secondary text-sm">
                        View Members & Authorize
                    </button>
                    <button onclick="app.copyNetworkConfig()" class="btn-secondary text-sm ml-2">
                        Copy Join Command
                    </button>
                </div>
            ` : ''}
        `;
        
        // Show mesh connectivity if available (Comment 12)
        if (this.federationStatus?.mesh_connectivity) {
            this.renderMeshConnectivity(this.federationStatus.mesh_connectivity);
        }
    }
    
    renderMeshConnectivity(meshStatus) {
        const container = document.getElementById('mesh-connectivity-status');
        const card = document.getElementById('mesh-connectivity-card');
        
        if (!meshStatus) {
            card.style.display = 'none';
            return;
        }
        
        card.style.display = 'block';
        
        const meshBadge = meshStatus.using_mesh
            ? '<span class="badge badge-success">Using Mesh</span>'
            : '<span class="badge badge-warning">Using Public URL</span>';
        
        container.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <div class="text-sm text-gray-400 mb-1">Active Connection</div>
                    <div>${meshBadge}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">Mesh URL</div>
                    <div class="font-mono text-xs text-blue-400">${meshStatus.mesh_url || 'N/A'}</div>
                </div>
                <div class="col-span-2">
                    <div class="text-sm text-gray-400 mb-1">Fallback URL</div>
                    <div class="font-mono text-xs text-gray-500">${meshStatus.public_url || 'N/A'}</div>
                </div>
            </div>
            <div class="mt-2 text-sm text-gray-400">
                ${meshStatus.using_mesh 
                    ? '✓ Federation traffic is using encrypted mesh network' 
                    : '⚠ Using public URL - mesh unavailable'}
            </div>
        `;
    }
    
    async showZeroTierWizard() {
        const wizard = document.getElementById('zerotier-wizard');
        wizard.style.display = 'block';
        
        const wizardContent = document.getElementById('wizard-content');
        wizardContent.innerHTML = `
            <div class="space-y-6">
                <div class="wizard-step">
                    <div class="flex items-start space-x-3 mb-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-semibold">
                            1
                        </div>
                        <div class="flex-1">
                            <h4 class="font-semibold mb-2">Enable Overlay Network</h4>
                            <p class="text-sm text-gray-400 mb-3">
                                ZeroTier provides encrypted P2P networking for your federated nodes.
                            </p>
                            <label class="flex items-center space-x-2">
                                <input type="checkbox" id="wizard-enable-zt" class="rounded">
                                <span class="text-sm">Enable ZeroTier overlay network</span>
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-step">
                    <div class="flex items-start space-x-3 mb-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-semibold">
                            2
                        </div>
                        <div class="flex-1">
                            <h4 class="font-semibold mb-2">Network Configuration</h4>
                            <div class="space-y-3">
                                <div>
                                    <label class="text-sm text-gray-400 mb-1 block">ZeroTier API Token (Central Only)</label>
                                    <input type="password" id="wizard-api-token" 
                                           class="w-full bg-gray-900/50 border border-gray-800 rounded px-3 py-2 text-sm"
                                           placeholder="Get from my.zerotier.com">
                                </div>
                                <div>
                                    <label class="text-sm text-gray-400 mb-1 block">Network ID (Leave empty to create new)</label>
                                    <input type="text" id="wizard-network-id" 
                                           class="w-full bg-gray-900/50 border border-gray-800 rounded px-3 py-2 text-sm font-mono"
                                           placeholder="Leave empty for auto-creation">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-step">
                    <div class="flex items-start space-x-3 mb-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-semibold">
                            3
                        </div>
                        <div class="flex-1">
                            <h4 class="font-semibold mb-2">Create/Verify Network</h4>
                            <button onclick="app.createZeroTierNetwork()" class="btn-primary text-sm">
                                Create Network
                            </button>
                            <div id="wizard-network-result" class="mt-3"></div>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-step">
                    <div class="flex items-start space-x-3 mb-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-semibold">
                            4
                        </div>
                        <div class="flex-1">
                            <h4 class="font-semibold mb-2">Edge Node Setup</h4>
                            <p class="text-sm text-gray-400 mb-3">Copy this command for edge nodes:</p>
                            <div id="wizard-join-command" class="bg-gray-900/50 p-3 rounded font-mono text-xs">
                                Waiting for network creation...
                            </div>
                            <button onclick="app.copyJoinCommand()" class="btn-secondary text-sm mt-2">
                                Copy to Clipboard
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-step">
                    <div class="flex items-start space-x-3 mb-4">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-semibold">
                            5
                        </div>
                        <div class="flex-1">
                            <h4 class="font-semibold mb-2">Authorize Members</h4>
                            <div id="wizard-pending-members"></div>
                            <button onclick="app.refreshPendingMembers()" class="btn-secondary text-sm mt-2">
                                Refresh Pending
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="flex items-center justify-end space-x-3 pt-4 border-t border-gray-800">
                    <button onclick="app.closeZeroTierWizard()" class="btn-secondary">
                        Close
                    </button>
                </div>
            </div>
        `;
    }
    
    closeZeroTierWizard() {
        document.getElementById('zerotier-wizard').style.display = 'none';
    }
    
    async createZeroTierNetwork() {
        const resultDiv = document.getElementById('wizard-network-result');
        resultDiv.innerHTML = '<div class="text-sm text-gray-400">Creating network...</div>';
        
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/network/create`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                resultDiv.innerHTML = `
                    <div class="text-sm text-green-400">
                        ✓ Network created: <span class="font-mono">${data.network_id}</span>
                    </div>
                `;
                
                // Load network config for join command
                await this.loadNetworkConfig();
            } else {
                const error = await response.json();
                resultDiv.innerHTML = `<div class="text-sm text-red-400">Failed: ${error.detail}</div>`;
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="text-sm text-red-400">Error: ${error.message}</div>`;
        }
    }
    
    async loadNetworkConfig() {
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/network-config`);
            if (response.ok) {
                const data = await response.json();
                this.networkConfig = data;
                
                const joinCmd = document.getElementById('wizard-join-command');
                if (joinCmd) {
                    joinCmd.textContent = data.join_command;
                }
            }
        } catch (error) {
            console.error('Failed to load network config:', error);
        }
    }
    
    async copyJoinCommand() {
        const cmd = this.networkConfig?.join_command || '';
        if (cmd) {
            await navigator.clipboard.writeText(cmd);
            alert('Join command copied to clipboard!');
        }
    }
    
    async copyNetworkConfig() {
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/network-config`);
            if (response.ok) {
                const data = await response.json();
                await navigator.clipboard.writeText(data.join_command);
                alert('Join command copied to clipboard!');
            }
        } catch (error) {
            console.error('Failed to copy network config:', error);
        }
    }
    
    async showMemberList() {
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/members`);
            if (response.ok) {
                const data = await response.json();
                
                const modal = document.createElement('div');
                modal.className = 'video-modal';
                modal.innerHTML = `
                    <div class="video-modal-content max-w-2xl">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-xl font-semibold">ZeroTier Members</h3>
                            <button onclick="this.closest('.video-modal').remove()" class="text-gray-400 hover:text-white">
                                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                                </svg>
                            </button>
                        </div>
                        <div class="space-y-3">
                            ${data.members.map(m => `
                                <div class="bg-gray-900/50 p-4 rounded border border-gray-800">
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="font-mono text-sm">${m.nodeId}</div>
                                        <span class="badge badge-${m.authorized ? 'success' : 'warning'}">
                                            ${m.authorized ? 'Authorized' : 'Pending'}
                                        </span>
                                    </div>
                                    <div class="text-sm text-gray-400">
                                        ${m.name || 'Unnamed'} • 
                                        ${m.ipAssignments?.join(', ') || 'No IP'} • 
                                        ${m.online ? 'Online' : 'Offline'}
                                    </div>
                                    ${!m.authorized ? `
                                        <button onclick="app.authorizeMember('${m.nodeId}', '${m.name || m.nodeId}')" 
                                                class="btn-primary text-sm mt-2">
                                            Authorize
                                        </button>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                modal.style.display = 'flex';
            }
        } catch (error) {
            console.error('Failed to load members:', error);
        }
    }
    
    async authorizeMember(address, name) {
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/members/authorize`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({zerotier_address: address, node_name: name})
            });
            
            if (response.ok) {
                alert(`Authorized ${name}`);
                this.loadFederationStatus();
            } else {
                alert('Failed to authorize member');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }
    
    async refreshPendingMembers() {
        const container = document.getElementById('wizard-pending-members');
        container.innerHTML = '<div class="text-sm text-gray-400">Loading...</div>';
        
        try {
            const response = await fetch(`${API_BASE}/api/zerotier/members`);
            if (response.ok) {
                const data = await response.json();
                const pending = data.members.filter(m => !m.authorized);
                
                if (pending.length === 0) {
                    container.innerHTML = '<div class="text-sm text-gray-400">No pending members</div>';
                } else {
                    container.innerHTML = pending.map(m => `
                        <div class="bg-gray-900/50 p-3 rounded mb-2">
                            <div class="flex items-center justify-between">
                                <span class="font-mono text-sm">${m.nodeId}</span>
                                <button onclick="app.authorizeMember('${m.nodeId}', '${m.name || m.nodeId}')" 
                                        class="btn-primary text-xs">
                                    Authorize
                                </button>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            container.innerHTML = `<div class="text-sm text-red-400">Error: ${error.message}</div>`;
        }
    }
    
    connectWebSocket() {
        this.ws = new WebSocket(`${WS_BASE}/api/ws`);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            // Subscribe to events and alarms topics
            this.ws.send(JSON.stringify({ 
                type: 'subscribe', 
                topics: ['events', 'alarms', 'streams']
            }));
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('WebSocket message error:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'event':
            case 'detection':
                // Add new event to the beginning
                this.events.unshift(data);
                this.events = this.events.slice(0, 100); // Keep last 100
                this.renderEvents();
                break;
                
            case 'alarms':
                // Handle alarm updates
                if (typeof handleAlarmUpdate === 'function') {
                    handleAlarmUpdate(data);
                }
                break;
                
            case 'stream_status':
            case 'streams':
                // Update camera status
                this.loadCameras();
                break;
        }
    }
    
    async loadWorkflows() {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder`);
            const data = await response.json();
            this.workflows = data.workflows || [];
            this.renderWorkflows();
        } catch (error) {
            console.error('Failed to load workflows:', error);
        }
    }
    
    renderWorkflows() {
        const activeContainer = document.getElementById('active-workflows');
        const savedContainer = document.getElementById('saved-workflows');
        const siteContainer = document.getElementById('workflows-by-site');
        
        if (!activeContainer || !savedContainer) return;
        
        // Filter active vs saved workflows
        const activeWorkflows = this.workflows.filter(w => w.status === 'running');
        const savedWorkflows = this.workflows.filter(w => w.status !== 'running');
        
        // Render active workflows
        if (activeWorkflows.length === 0) {
            activeContainer.innerHTML = '<div class="text-gray-500 text-sm">No workflows currently running</div>';
        } else {
            activeContainer.innerHTML = activeWorkflows.map(workflow => `
                <div class="border border-green-500/30 bg-green-500/5 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center space-x-3">
                            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <h4 class="font-semibold text-white">${workflow.name || 'Unnamed Workflow'}</h4>
                        </div>
                        <div class="flex items-center space-x-2">
                            <a href="http://localhost:7003?workflow=${workflow.id}" target="_blank"
                               class="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white transition-colors">
                                Edit
                            </a>
                            <button onclick="app.stopWorkflow('${workflow.id}')"
                                    class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white transition-colors">
                                Stop
                            </button>
                        </div>
                    </div>
                    <div class="text-xs text-gray-400">
                        ${workflow.nodes?.length || 0} nodes | ${workflow.edges?.length || 0} connections
                    </div>
                    ${workflow.description ? `<div class="text-xs text-gray-500 mt-2">${workflow.description}</div>` : ''}
                </div>
            `).join('');
        }
        
        // Render workflows organized by site
        if (siteContainer) {
            const masterWorkflows = savedWorkflows.filter(w => w.is_master);
            const siteWorkflows = savedWorkflows.filter(w => !w.is_master && w.site_id);
            const ungrouped = savedWorkflows.filter(w => !w.is_master && !w.site_id);
            
            let siteHTML = '';
            
            // Master workflows
            if (masterWorkflows.length > 0) {
                siteHTML += `
                    <div class="card border-purple-500/20">
                        <h3 class="text-lg font-semibold mb-4 text-purple-400 flex items-center">
                            <span class="mr-2">⭐</span> Master Templates (${masterWorkflows.length})
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            ${masterWorkflows.map(w => this.renderWorkflowCard(w)).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Group site workflows
            const bySite = {};
            siteWorkflows.forEach(w => {
                const key = w.site_id || 'unknown';
                if (!bySite[key]) bySite[key] = [];
                bySite[key].push(w);
            });
            
            // Render each site
            Object.keys(bySite).forEach(siteId => {
                const workflows = bySite[siteId];
                const siteName = workflows[0]?.site_name || 'Unknown Site';
                siteHTML += `
                    <div class="card border-blue-500/20">
                        <h3 class="text-lg font-semibold mb-4 text-blue-400 flex items-center">
                            <span class="mr-2">📍</span> ${siteName} (${workflows.length})
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            ${workflows.map(w => this.renderWorkflowCard(w)).join('')}
                        </div>
                    </div>
                `;
            });
            
            siteContainer.innerHTML = siteHTML;
            
            // Render ungrouped in saved section
            if (ungrouped.length === 0) {
                savedContainer.innerHTML = `
                    <div class="col-span-full text-center py-12 border-2 border-dashed border-gray-700 rounded-lg">
                        <div class="text-gray-500 mb-4">
                            <svg class="w-16 h-16 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            <div class="font-medium">No saved workflows yet</div>
                            <div class="text-sm mt-1">Create your first workflow in the builder</div>
                        </div>
                        <a href="http://localhost:7003" target="_blank" 
                           class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors">
                            <span class="mr-2">+</span> Open Workflow Builder
                        </a>
                    </div>
                `;
            } else {
                savedContainer.innerHTML = `
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${ungrouped.map(w => this.renderWorkflowCard(w)).join('')}
                    </div>
                `;
            }
        }
    }
    
    renderWorkflowCard(workflow) {
        return `
            <div class="border border-gray-700 bg-gray-800/50 rounded-lg p-4 hover:border-gray-600 hover:bg-gray-800 transition-all">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2 flex-1 min-w-0">
                        ${workflow.is_master ? '<span class="text-purple-400 text-lg">⭐</span>' : ''}
                        <h4 class="font-semibold text-white truncate">${workflow.name || 'Untitled'}</h4>
                    </div>
                    <span class="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded ml-2">${workflow.version || '1.0.0'}</span>
                </div>
                
                ${workflow.description ? `<p class="text-xs text-gray-400 mb-3 line-clamp-2">${workflow.description}</p>` : ''}
                
                <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                    <span>${workflow.nodes?.length || 0} nodes</span>
                    <span>${workflow.edges?.length || 0} connections</span>
                </div>
                
                ${workflow.updated_at ? `<div class="text-xs text-gray-600 mb-3">Updated: ${new Date(workflow.updated_at).toLocaleDateString()}</div>` : ''}
                
                <div class="flex items-center space-x-2">
                    <a href="http://localhost:7003?workflow=${workflow.id}" target="_blank"
                       class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white text-center transition-colors font-medium">
                        ✏️ Edit
                    </a>
                    <button onclick="app.executeWorkflow('${workflow.id}')"
                            class="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-xs text-white transition-colors font-medium">
                        ▶️ Start
                    </button>
                </div>
            </div>
        `;
    }
    
    async executeWorkflow(workflowId) {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder/execute`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ workflow_id: workflowId })
            });
            
            if (response.ok) {
                alert('Workflow started successfully!');
                await this.loadWorkflows();
            } else {
                alert('Failed to start workflow');
            }
        } catch (error) {
            console.error('Error executing workflow:', error);
            alert('Error starting workflow');
        }
    }
    
    async stopWorkflow(workflowId) {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder/${workflowId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert('Workflow stopped');
                await this.loadWorkflows();
            } else {
                alert('Failed to stop workflow');
            }
        } catch (error) {
            console.error('Error stopping workflow:', error);
        }
    }
}

// View switching
function showView(viewName) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const viewElement = document.getElementById(`${viewName}-view`);
    const navElement = document.querySelector(`[data-view="${viewName}"]`);
    
    if (viewElement) {
        viewElement.classList.add('active');
    }
    if (navElement) {
        navElement.classList.add('active');
    }
}

// Camera fullscreen expansion
function expandCamera(cameraId, cameraName, fps) {
    const modal = document.getElementById('video-modal');
    const modalVideo = document.getElementById('modal-video');
    const modalName = document.getElementById('modal-camera-name');
    const modalInfo = document.getElementById('modal-camera-info');
    
    // Set camera info
    modalName.textContent = cameraName;
    modalInfo.textContent = `${fps} FPS • Click anywhere to close`;
    
    // Set video source
    modalVideo.src = `${API_BASE}/api/video/${cameraId}/mjpeg`;
    
    // Show modal
    modal.classList.add('active');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeVideoModal(event) {
    // Close if clicking on backdrop or close button
    if (event.target.id === 'video-modal' || event.target.closest('button')) {
        const modal = document.getElementById('video-modal');
        const modalVideo = document.getElementById('modal-video');
        
        // Stop video
        modalVideo.src = '';
        
        // Hide modal
        modal.classList.remove('active');
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

// Change camera stream quality
async function changeStreamQuality(cameraId, quality) {
    try {
        const response = await fetch(`${API_BASE}/api/camera-control/${cameraId}/quality`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ quality })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Changed to ${quality}: ${data.resolution}`);
            
            // Reload camera grid after short delay
            setTimeout(() => {
                window.app.loadCameras();
            }, 2000);
        } else {
            console.error('Failed to change quality');
        }
    } catch (error) {
        console.error('Error changing quality:', error);
    }
}

// Keyboard shortcut - ESC to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('video-modal');
        if (modal.classList.contains('active')) {
            const modalVideo = document.getElementById('modal-video');
            modalVideo.src = '';
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new OverwatchApp();
    
    // Event filter change handler
    const eventFilter = document.getElementById('event-filter');
    if (eventFilter) {
        eventFilter.addEventListener('change', () => {
            window.app.loadEvents();
        });
    }
});

