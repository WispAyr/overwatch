// Alarm Hierarchy Management
// Provides organization and site-level alarm views

// Hierarchy state
let hierarchyData = null;
let currentView = 'global'; // 'global', 'organization', 'site'
let currentOrganization = null;
let currentSite = null;

// Load organizational hierarchy
async function loadHierarchy() {
    try {
        const response = await fetch(`${API_BASE}/api/hierarchy/tree`);
        hierarchyData = await response.json();
        
        renderHierarchySelector();
        updateHierarchyStats();
        
    } catch (error) {
        console.error('Failed to load hierarchy:', error);
    }
}

// Render hierarchy selector dropdown
function renderHierarchySelector() {
    const selector = document.getElementById('hierarchy-selector');
    if (!selector || !hierarchyData) return;
    
    const orgs = hierarchyData.organizations || [];
    
    let html = `
        <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold">View Scope</h3>
                <button onclick="resetHierarchyView()" class="text-xs text-blue-400 hover:text-blue-300">
                    Reset to Global
                </button>
            </div>
            
            <!-- View Level Tabs -->
            <div class="flex gap-2 mb-3">
                <button onclick="setViewLevel('global')" 
                        class="px-3 py-1 rounded text-sm ${currentView === 'global' ? 'bg-blue-600' : 'bg-gray-700'} hover:bg-blue-700">
                    🌍 Global
                </button>
                <button onclick="setViewLevel('organization')" 
                        class="px-3 py-1 rounded text-sm ${currentView === 'organization' ? 'bg-blue-600' : 'bg-gray-700'} hover:bg-blue-700"
                        ${orgs.length === 0 ? 'disabled' : ''}>
                    🏢 Organization
                </button>
                <button onclick="setViewLevel('site')" 
                        class="px-3 py-1 rounded text-sm ${currentView === 'site' ? 'bg-blue-600' : 'bg-gray-700'} hover:bg-blue-700"
                        ${orgs.length === 0 ? 'disabled' : ''}>
                    📍 Site
                </button>
            </div>
            
            ${currentView === 'global' ? renderGlobalViewInfo() : ''}
            ${currentView === 'organization' ? renderOrganizationSelector(orgs) : ''}
            ${currentView === 'site' ? renderSiteSelector(orgs) : ''}
        </div>
    `;
    
    selector.innerHTML = html;
}

// Render global view info
function renderGlobalViewInfo() {
    const orgCount = hierarchyData?.organizations?.length || 0;
    const siteCount = hierarchyData?.organizations?.reduce((acc, org) => 
        acc + (org.sites?.length || 0), 0) || 0;
    
    return `
        <div class="bg-gray-900 rounded p-3 text-sm">
            <div class="text-gray-400 mb-2">Viewing alarms across:</div>
            <div class="grid grid-cols-2 gap-2 text-xs">
                <div>🏢 <span class="font-semibold">${orgCount}</span> Organizations</div>
                <div>📍 <span class="font-semibold">${siteCount}</span> Sites</div>
            </div>
        </div>
    `;
}

// Render organization selector
function renderOrganizationSelector(orgs) {
    return `
        <div class="space-y-2">
            <label class="text-sm text-gray-400">Select Organization:</label>
            <select id="org-selector" onchange="selectOrganization(this.value)" 
                    class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                <option value="">-- Select Organization --</option>
                ${orgs.map(org => `
                    <option value="${org.id}" ${currentOrganization === org.id ? 'selected' : ''}>
                        ${org.name} (${org.sites?.length || 0} sites)
                    </option>
                `).join('')}
            </select>
            
            ${currentOrganization ? renderOrganizationInfo() : ''}
        </div>
    `;
}

// Render site selector
function renderSiteSelector(orgs) {
    const allSites = [];
    orgs.forEach(org => {
        (org.sites || []).forEach(site => {
            allSites.push({
                ...site,
                orgId: org.id,
                orgName: org.name
            });
        });
    });
    
    return `
        <div class="space-y-2">
            <label class="text-sm text-gray-400">Select Site:</label>
            <select id="site-selector" onchange="selectSite(this.value)" 
                    class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm">
                <option value="">-- Select Site --</option>
                ${allSites.map(site => `
                    <option value="${site.id}" ${currentSite === site.id ? 'selected' : ''}>
                        ${site.orgName} → ${site.name} (${site.site_type})
                    </option>
                `).join('')}
            </select>
            
            ${currentSite ? renderSiteInfo() : ''}
        </div>
    `;
}

// Render organization info
function renderOrganizationInfo() {
    const org = hierarchyData?.organizations?.find(o => o.id === currentOrganization);
    if (!org) return '';
    
    return `
        <div class="mt-3 bg-gray-900 rounded p-3 text-sm">
            <div class="font-semibold mb-2">${org.name}</div>
            <div class="text-gray-400 text-xs space-y-1">
                ${org.description ? `<div>${org.description}</div>` : ''}
                <div>📍 Sites: ${org.sites?.length || 0}</div>
                <div>📷 Cameras: ${countOrgCameras(org)}</div>
            </div>
        </div>
    `;
}

// Render site info
function renderSiteInfo() {
    let site = null;
    let orgName = '';
    
    for (const org of (hierarchyData?.organizations || [])) {
        const foundSite = (org.sites || []).find(s => s.id === currentSite);
        if (foundSite) {
            site = foundSite;
            orgName = org.name;
            break;
        }
    }
    
    if (!site) return '';
    
    const cameraCount = site.sublocations?.reduce((acc, sl) => 
        acc + (sl.cameras?.length || 0), 0) || 0;
    
    return `
        <div class="mt-3 bg-gray-900 rounded p-3 text-sm">
            <div class="font-semibold mb-1">${site.name}</div>
            <div class="text-xs text-gray-500 mb-2">${orgName}</div>
            <div class="text-gray-400 text-xs space-y-1">
                <div>📌 Type: ${site.site_type}</div>
                ${site.location?.address ? `<div>📍 ${site.location.address}</div>` : ''}
                <div>📷 Cameras: ${cameraCount}</div>
                <div>🏠 Areas: ${site.sublocations?.length || 0}</div>
            </div>
        </div>
    `;
}

// Count cameras in organization
function countOrgCameras(org) {
    let count = 0;
    (org.sites || []).forEach(site => {
        (site.sublocations || []).forEach(sl => {
            count += (sl.cameras?.length || 0);
        });
    });
    return count;
}

// Set view level
function setViewLevel(level) {
    currentView = level;
    
    if (level === 'global') {
        currentOrganization = null;
        currentSite = null;
    } else if (level === 'organization') {
        currentSite = null;
    }
    
    renderHierarchySelector();
    applyHierarchyFilter();
}

// Select organization
function selectOrganization(orgId) {
    currentOrganization = orgId || null;
    currentSite = null;
    renderHierarchySelector();
    applyHierarchyFilter();
}

// Select site
function selectSite(siteId) {
    currentSite = siteId || null;
    
    // Also set the organization
    if (siteId) {
        for (const org of (hierarchyData?.organizations || [])) {
            if ((org.sites || []).some(s => s.id === siteId)) {
                currentOrganization = org.id;
                break;
            }
        }
    }
    
    renderHierarchySelector();
    applyHierarchyFilter();
}

// Reset to global view
function resetHierarchyView() {
    currentView = 'global';
    currentOrganization = null;
    currentSite = null;
    renderHierarchySelector();
    applyHierarchyFilter();
}

// Apply hierarchy filter to alarms
async function applyHierarchyFilter() {
    // Build query parameters based on current view
    let params = new URLSearchParams();
    params.append('limit', '1000');
    
    if (currentView === 'organization' && currentOrganization) {
        params.append('tenant', currentOrganization);
    } else if (currentView === 'site' && currentSite) {
        params.append('site', currentSite);
    }
    // Global view has no filters
    
    try {
        const response = await fetch(`${API_BASE}/api/alarms?${params}`);
        const data = await response.json();
        app.alarms = data.alarms || [];
        
        renderAlarms();
        updateAlarmCounts();
        updateHierarchyStats();
        
    } catch (error) {
        console.error('Failed to load alarms with hierarchy filter:', error);
    }
}

// Update hierarchy statistics
function updateHierarchyStats() {
    if (!app.alarms) return;
    
    const statsContainer = document.getElementById('hierarchy-stats');
    if (!statsContainer) return;
    
    // Calculate stats by organization and site
    const orgStats = {};
    const siteStats = {};
    
    app.alarms.forEach(alarm => {
        const tenant = alarm.tenant || 'unknown';
        const site = alarm.site || 'unknown';
        
        // Org stats
        if (!orgStats[tenant]) {
            orgStats[tenant] = {
                total: 0,
                critical: 0,
                major: 0,
                minor: 0,
                info: 0,
                new: 0,
                active: 0
            };
        }
        orgStats[tenant].total++;
        orgStats[tenant][alarm.severity]++;
        if (alarm.state === 'NEW') orgStats[tenant].new++;
        if (alarm.state === 'ACTIVE') orgStats[tenant].active++;
        
        // Site stats
        if (!siteStats[site]) {
            siteStats[site] = {
                total: 0,
                critical: 0,
                major: 0,
                minor: 0,
                info: 0,
                new: 0,
                active: 0
            };
        }
        siteStats[site].total++;
        siteStats[site][alarm.severity]++;
        if (alarm.state === 'NEW') siteStats[site].new++;
        if (alarm.state === 'ACTIVE') siteStats[site].active++;
    });
    
    // Render stats based on current view
    let html = '';
    
    if (currentView === 'global') {
        html = renderGlobalStats(orgStats, siteStats);
    } else if (currentView === 'organization' && currentOrganization) {
        html = renderOrganizationStats(currentOrganization, orgStats, siteStats);
    } else if (currentView === 'site' && currentSite) {
        html = renderSiteStats(currentSite, siteStats);
    }
    
    statsContainer.innerHTML = html;
}

// Render global statistics
function renderGlobalStats(orgStats, siteStats) {
    const orgs = Object.entries(orgStats);
    if (orgs.length === 0) return '<div class="text-gray-500 text-sm">No alarms</div>';
    
    return `
        <div class="bg-gray-800 rounded-lg p-4">
            <h3 class="font-semibold mb-3">Global Alarm Statistics</h3>
            <div class="space-y-2">
                ${orgs.map(([tenant, stats]) => `
                    <div class="bg-gray-900 rounded p-3 text-sm">
                        <div class="flex items-center justify-between mb-2">
                            <div class="font-medium">${tenant}</div>
                            <div class="text-xs text-gray-400">${stats.total} alarms</div>
                        </div>
                        <div class="grid grid-cols-4 gap-2 text-xs">
                            <div class="text-red-400">🔴 ${stats.critical}</div>
                            <div class="text-orange-400">🟠 ${stats.major}</div>
                            <div class="text-yellow-400">🟡 ${stats.minor}</div>
                            <div class="text-blue-400">🔵 ${stats.info}</div>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-xs mt-2">
                            <div class="text-green-400">🆕 ${stats.new} NEW</div>
                            <div class="text-purple-400">⚡ ${stats.active} ACTIVE</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Render organization statistics
function renderOrganizationStats(orgId, orgStats, siteStats) {
    const stats = orgStats[orgId];
    if (!stats) return '<div class="text-gray-500 text-sm">No alarms for this organization</div>';
    
    // Get sites for this org
    const org = hierarchyData?.organizations?.find(o => o.id === orgId);
    const sites = org?.sites || [];
    
    return `
        <div class="bg-gray-800 rounded-lg p-4">
            <h3 class="font-semibold mb-3">Organization Statistics</h3>
            
            <!-- Overall stats -->
            <div class="bg-gray-900 rounded p-3 mb-3">
                <div class="text-sm font-medium mb-2">Total: ${stats.total} alarms</div>
                <div class="grid grid-cols-4 gap-2 text-xs mb-2">
                    <div class="text-red-400">🔴 ${stats.critical}</div>
                    <div class="text-orange-400">🟠 ${stats.major}</div>
                    <div class="text-yellow-400">🟡 ${stats.minor}</div>
                    <div class="text-blue-400">🔵 ${stats.info}</div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="text-green-400">🆕 ${stats.new} NEW</div>
                    <div class="text-purple-400">⚡ ${stats.active} ACTIVE</div>
                </div>
            </div>
            
            <!-- Per-site breakdown -->
            <div class="text-sm font-medium mb-2">By Site:</div>
            <div class="space-y-2">
                ${sites.map(site => {
                    const siteData = siteStats[site.id] || { total: 0, critical: 0, major: 0, minor: 0, info: 0 };
                    return `
                        <div class="bg-gray-900 rounded p-2 text-xs">
                            <div class="flex items-center justify-between mb-1">
                                <div class="font-medium">${site.name}</div>
                                <div class="text-gray-400">${siteData.total}</div>
                            </div>
                            <div class="flex gap-2">
                                <span class="text-red-400">${siteData.critical}</span>
                                <span class="text-orange-400">${siteData.major}</span>
                                <span class="text-yellow-400">${siteData.minor}</span>
                                <span class="text-blue-400">${siteData.info}</span>
                            </div>
                        </div>
                    `;
                }).join('') || '<div class="text-gray-500 text-xs">No sites configured</div>'}
            </div>
        </div>
    `;
}

// Render site statistics
function renderSiteStats(siteId, siteStats) {
    const stats = siteStats[siteId];
    if (!stats) return '<div class="text-gray-500 text-sm">No alarms for this site</div>';
    
    return `
        <div class="bg-gray-800 rounded-lg p-4">
            <h3 class="font-semibold mb-3">Site Statistics</h3>
            
            <div class="bg-gray-900 rounded p-3">
                <div class="text-sm font-medium mb-2">Total: ${stats.total} alarms</div>
                <div class="grid grid-cols-4 gap-2 text-xs mb-2">
                    <div class="text-red-400">🔴 Critical: ${stats.critical}</div>
                    <div class="text-orange-400">🟠 Major: ${stats.major}</div>
                    <div class="text-yellow-400">🟡 Minor: ${stats.minor}</div>
                    <div class="text-blue-400">🔵 Info: ${stats.info}</div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="text-green-400">🆕 NEW: ${stats.new}</div>
                    <div class="text-purple-400">⚡ ACTIVE: ${stats.active}</div>
                </div>
            </div>
        </div>
    `;
}

// Initialize hierarchy on page load
async function initializeHierarchy() {
    await loadHierarchy();
    
    // Set up periodic refresh
    setInterval(() => {
        if (currentView !== 'global' || currentOrganization || currentSite) {
            applyHierarchyFilter();
        }
    }, 30000); // Refresh every 30 seconds
}

// Make functions globally available
window.loadHierarchy = loadHierarchy;
window.setViewLevel = setViewLevel;
window.selectOrganization = selectOrganization;
window.selectSite = selectSite;
window.resetHierarchyView = resetHierarchyView;
window.applyHierarchyFilter = applyHierarchyFilter;
window.updateHierarchyStats = updateHierarchyStats;
window.initializeHierarchy = initializeHierarchy;

