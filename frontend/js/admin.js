/**
 * Admin Panel - Manage Organizations, Sites, Sublocations, and Cameras
 */

class AdminPanel {
    constructor() {
        this.organizations = []
        this.sites = []
        this.sublocations = []
        this.cameras = []
        this.unifiCredentials = []
        this.activeTab = 'organizations'
    }
    
    async init() {
        console.log('Initializing Admin Panel...')
        await this.loadAll()
    }
    
    async loadAll() {
        await this.loadOrganizations()
        await this.loadSites()
        await this.loadSublocations()
        await this.loadCameras()
        await this.loadUniFiCredentials()
    }
    
    // ==================== ORGANIZATIONS ====================
    
    async loadOrganizations() {
        try {
            const response = await fetch(`${API_BASE}/api/organizations/`)
            const data = await response.json()
            this.organizations = data.organizations || []
            this.renderOrganizations()
        } catch (error) {
            console.error('Failed to load organizations:', error)
        }
    }
    
    renderOrganizations() {
        const container = document.getElementById('organizations-list')
        if (!container) return
        
        if (this.organizations.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-4xl mb-3">🏢</div>
                    <div class="text-gray-400">No organizations yet</div>
                    <div class="text-sm text-gray-500 mt-1">Create your first organization to get started</div>
                </div>
            `
            return
        }
        
        container.innerHTML = this.organizations.map(org => `
            <div class="entity-card">
                <div class="entity-card-header">
                    <h4 class="entity-card-title">${org.name}</h4>
                    <div class="entity-card-actions">
                        <button onclick="admin.editOrganization('${org.id}')" class="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white">
                            Edit
                        </button>
                        <button onclick="admin.deleteOrganization('${org.id}')" class="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white">
                            Delete
                        </button>
                    </div>
                </div>
                ${org.description ? `<p class="text-sm text-gray-400 mb-2">${org.description}</p>` : ''}
                <div class="text-xs text-gray-500">
                    Type: ${org.organization_type || 'Not specified'}
                </div>
            </div>
        `).join('')
    }
    
    async createOrganization(formData) {
        try {
            console.log('Creating organization:', formData)
            const response = await fetch(`${API_BASE}/api/organizations/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            
            const result = await response.json()
            console.log('Create organization response:', result)
            
            if (response.ok) {
                await this.loadOrganizations()
                closeModal('create-organization-modal')
                alert('Organization created successfully!')
            } else {
                throw new Error(result.detail || 'Failed to create organization')
            }
        } catch (error) {
            console.error('Error creating organization:', error)
            alert('Failed to create organization: ' + error.message)
        }
    }
    
    async deleteOrganization(id) {
        if (!confirm('Are you sure you want to delete this organization? This will also delete all associated sites, sublocations, and cameras.')) {
            return
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/organizations/${id}`, {
                method: 'DELETE'
            })
            
            if (response.ok) {
                await this.loadAll()
                alert('Organization deleted successfully')
            } else {
                throw new Error('Failed to delete organization')
            }
        } catch (error) {
            console.error('Error deleting organization:', error)
            alert('Failed to delete organization: ' + error.message)
        }
    }
    
    // ==================== SITES ====================
    
    async loadSites() {
        try {
            const response = await fetch(`${API_BASE}/api/sites/`)
            const data = await response.json()
            this.sites = data.sites || []
            this.renderSites()
            this.populateSiteSelects()
        } catch (error) {
            console.error('Failed to load sites:', error)
        }
    }
    
    renderSites() {
        const container = document.getElementById('sites-list')
        if (!container) return
        
        if (this.sites.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-4xl mb-3">📍</div>
                    <div class="text-gray-400">No sites yet</div>
                    <div class="text-sm text-gray-500 mt-1">Create a site to organize your cameras</div>
                </div>
            `
            return
        }
        
        container.innerHTML = this.sites.map(site => {
            const org = this.organizations.find(o => o.id === site.organization_id)
            const locationStr = site.location?.address || site.location
            return `
                <div class="entity-card">
                    <div class="entity-card-header">
                        <h4 class="entity-card-title">${site.name}</h4>
                        <div class="entity-card-actions">
                            <button onclick="admin.editSite('${site.id}')" class="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white">
                                Edit
                            </button>
                            <button onclick="admin.deleteSite('${site.id}')" class="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white">
                                Delete
                            </button>
                        </div>
                    </div>
                    ${site.description ? `<p class="text-sm text-gray-400 mb-2">${site.description}</p>` : ''}
                    <div class="text-xs text-gray-500">
                        <div>Organization: ${org?.name || 'Unknown'}</div>
                        <div>Type: ${site.site_type || 'Not specified'}</div>
                        ${locationStr ? `<div>📍 ${locationStr}</div>` : ''}
                    </div>
                </div>
            `
        }).join('')
    }
    
    populateSiteSelects() {
        const select = document.getElementById('site-org-select')
        if (select) {
            if (this.organizations.length === 0) {
                select.innerHTML = '<option value="">No organizations available - Create one first</option>'
            } else {
                select.innerHTML = this.organizations.map(org => 
                    `<option value="${org.id}">${org.name}</option>`
                ).join('')
            }
        }
    }
    
    async createSite(formData) {
        try {
            console.log('Creating site:', formData)
            const response = await fetch(`${API_BASE}/api/sites/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            
            const result = await response.json()
            console.log('Create site response:', result)
            
            if (response.ok) {
                await this.loadAll()  // Reload all to update hierarchy
                closeModal('create-site-modal')
                alert('Site created successfully!')
            } else {
                throw new Error(result.detail || 'Failed to create site')
            }
        } catch (error) {
            console.error('Error creating site:', error)
            alert('Failed to create site: ' + error.message)
        }
    }
    
    async deleteSite(id) {
        if (!confirm('Are you sure you want to delete this site? This will also delete all associated sublocations and cameras.')) {
            return
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/sites/${id}`, {
                method: 'DELETE'
            })
            
            if (response.ok) {
                await this.loadAll()
                alert('Site deleted successfully')
            } else {
                throw new Error('Failed to delete site')
            }
        } catch (error) {
            console.error('Error deleting site:', error)
            alert('Failed to delete site: ' + error.message)
        }
    }
    
    // ==================== SUBLOCATIONS ====================
    
    async loadSublocations() {
        try {
            const response = await fetch(`${API_BASE}/api/sublocations/`)
            const data = await response.json()
            this.sublocations = data.sublocations || []
            this.renderSublocations()
            this.populateSublocationSelects()
        } catch (error) {
            console.error('Failed to load sublocations:', error)
        }
    }
    
    renderSublocations() {
        const container = document.getElementById('sublocations-list')
        if (!container) return
        
        if (this.sublocations.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-4xl mb-3">📌</div>
                    <div class="text-gray-400">No sublocations yet</div>
                    <div class="text-sm text-gray-500 mt-1">Create areas within your sites to place cameras</div>
                </div>
            `
            return
        }
        
        container.innerHTML = this.sublocations.map(sub => {
            const site = this.sites.find(s => s.id === sub.site_id)
            return `
                <div class="entity-card">
                    <div class="entity-card-header">
                        <h4 class="entity-card-title">${sub.name}</h4>
                        <div class="entity-card-actions">
                            <button onclick="admin.editSublocation('${sub.id}')" class="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white">
                                Edit
                            </button>
                            <button onclick="admin.deleteSublocation('${sub.id}')" class="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white">
                                Delete
                            </button>
                        </div>
                    </div>
                    ${sub.description ? `<p class="text-sm text-gray-400 mb-2">${sub.description}</p>` : ''}
                    <div class="text-xs text-gray-500">
                        <div>Site: ${site?.name || 'Unknown'}</div>
                        <div>Type: ${sub.sublocation_type || sub.area_type || 'Not specified'}</div>
                    </div>
                </div>
            `
        }).join('')
    }
    
    populateSublocationSelects() {
        const siteSelect = document.getElementById('sublocation-site-select')
        if (siteSelect) {
            if (this.sites.length === 0) {
                siteSelect.innerHTML = '<option value="">No sites available - Create one first</option>'
            } else {
                siteSelect.innerHTML = this.sites.map(site => 
                    `<option value="${site.id}">${site.name}</option>`
                ).join('')
            }
        }
        
        const cameraSelect = document.getElementById('camera-sublocation-select')
        if (cameraSelect) {
            if (this.sublocations.length === 0) {
                cameraSelect.innerHTML = '<option value="">No sublocations available - Create one first</option>'
            } else {
                cameraSelect.innerHTML = this.sublocations.map(sub => {
                    const site = this.sites.find(s => s.id === sub.site_id)
                    return `<option value="${sub.id}">${site?.name || 'Unknown'} - ${sub.name}</option>`
                }).join('')
            }
        }
    }
    
    async createSublocation(formData) {
        try {
            console.log('Creating sublocation:', formData)
            const response = await fetch(`${API_BASE}/api/sublocations/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            
            const result = await response.json()
            console.log('Create sublocation response:', result)
            
            if (response.ok) {
                await this.loadAll()  // Reload all to update selects
                closeModal('create-sublocation-modal')
                alert('Sublocation created successfully!')
            } else {
                throw new Error(result.detail || 'Failed to create sublocation')
            }
        } catch (error) {
            console.error('Error creating sublocation:', error)
            alert('Failed to create sublocation: ' + error.message)
        }
    }
    
    async deleteSublocation(id) {
        if (!confirm('Are you sure you want to delete this sublocation? This will also delete all cameras in this area.')) {
            return
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/sublocations/${id}`, {
                method: 'DELETE'
            })
            
            if (response.ok) {
                await this.loadAll()
                alert('Sublocation deleted successfully')
            } else {
                throw new Error('Failed to delete sublocation')
            }
        } catch (error) {
            console.error('Error deleting sublocation:', error)
            alert('Failed to delete sublocation: ' + error.message)
        }
    }
    
    // ==================== CAMERAS ====================
    
    async loadCameras() {
        try {
            const response = await fetch(`${API_BASE}/api/cameras/`)
            const data = await response.json()
            this.cameras = data.cameras || []
            this.renderCameras()
        } catch (error) {
            console.error('Failed to load cameras:', error)
        }
    }
    
    renderCameras() {
        const container = document.getElementById('cameras-list')
        if (!container) return
        
        if (this.cameras.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-4xl mb-3">📹</div>
                    <div class="text-gray-400">No cameras yet</div>
                    <div class="text-sm text-gray-500 mt-1">Add cameras to start monitoring</div>
                </div>
            `
            return
        }
        
        container.innerHTML = this.cameras.map(camera => {
            const sub = this.sublocations.find(s => s.id === camera.sublocation_id)
            const site = this.sites.find(s => s.id === sub?.site_id)
            return `
                <div class="entity-card">
                    <div class="entity-card-header">
                        <div class="flex items-center space-x-2">
                            <h4 class="entity-card-title">${camera.name}</h4>
                            ${camera.enabled ? '<span class="w-2 h-2 bg-green-500 rounded-full"></span>' : '<span class="w-2 h-2 bg-gray-500 rounded-full"></span>'}
                        </div>
                        <div class="entity-card-actions">
                            <button onclick="admin.editCamera('${camera.id}')" class="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white">
                                Edit
                            </button>
                            <button onclick="admin.deleteCamera('${camera.id}')" class="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white">
                                Delete
                            </button>
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 space-y-1">
                        <div>Type: ${camera.type || 'rtsp'}</div>
                        <div>Location: ${site?.name || 'Unknown'} - ${sub?.name || 'Unknown'}</div>
                        <div class="font-mono text-[10px] truncate">📡 ${camera.rtsp_url || 'No URL'}</div>
                        <div>Status: ${camera.enabled ? '<span class="text-green-400">Enabled</span>' : '<span class="text-gray-400">Disabled</span>'}</div>
                    </div>
                </div>
            `
        }).join('')
    }
    
    async createCamera(formData) {
        try {
            console.log('Creating camera:', formData)
            const response = await fetch(`${API_BASE}/api/cameras/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            
            const result = await response.json()
            console.log('Create camera response:', result)
            
            if (response.ok) {
                await this.loadAll()  // Reload all
                closeModal('create-camera-modal')
                alert('Camera created successfully!')
            } else {
                throw new Error(result.detail || 'Failed to create camera')
            }
        } catch (error) {
            console.error('Error creating camera:', error)
            alert('Failed to create camera: ' + error.message)
        }
    }
    
    async deleteCamera(id) {
        if (!confirm('Are you sure you want to delete this camera?')) {
            return
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/cameras/${id}`, {
                method: 'DELETE'
            })
            
            if (response.ok) {
                await this.loadCameras()
                alert('Camera deleted successfully')
            } else {
                throw new Error('Failed to delete camera')
            }
        } catch (error) {
            console.error('Error deleting camera:', error)
            alert('Failed to delete camera: ' + error.message)
        }
    }
    
    // Placeholder edit methods (implement as needed)
    editOrganization(id) { alert('Edit organization: ' + id) }
    editSite(id) { alert('Edit site: ' + id) }
    editSublocation(id) { alert('Edit sublocation: ' + id) }
    editCamera(id) { alert('Edit camera: ' + id) }
    
    // ==================== UNIFI CREDENTIALS ====================
    
    async loadUniFiCredentials() {
        try {
            const response = await fetch(`${API_BASE}/api/unifi/credentials`)
            const data = await response.json()
            this.unifiCredentials = data.credentials || []
            this.renderUniFiCredentials()
            this.populateUniFiSelects()
        } catch (error) {
            console.error('Failed to load UniFi credentials:', error)
        }
    }
    
    renderUniFiCredentials() {
        const container = document.getElementById('unifi-list')
        if (!container) return
        
        if (this.unifiCredentials.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-4xl mb-3">📡</div>
                    <div class="text-gray-400">No UniFi credentials yet</div>
                    <div class="text-sm text-gray-500 mt-1">Add UniFi credentials to integrate with UniFi Protect</div>
                </div>
            `
            return
        }
        
        container.innerHTML = this.unifiCredentials.map(cred => {
            const statusBadge = cred.last_test_status === 'success' 
                ? '<span class="px-2 py-1 bg-green-900/50 text-green-400 text-xs rounded">✓ Connected</span>'
                : cred.last_test_status === 'failed'
                ? '<span class="px-2 py-1 bg-red-900/50 text-red-400 text-xs rounded">✗ Failed</span>'
                : '<span class="px-2 py-1 bg-gray-700 text-gray-400 text-xs rounded">Not tested</span>'
            
            return `
                <div class="entity-card">
                    <div class="entity-card-header">
                        <h4 class="entity-card-title">${cred.name}</h4>
                        <div class="entity-card-actions">
                            <button onclick="admin.testUniFiCredential('${cred.id}')" class="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white">
                                Test
                            </button>
                            <button onclick="admin.deleteUniFiCredential('${cred.id}')" class="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white">
                                Delete
                            </button>
                        </div>
                    </div>
                    <div class="space-y-2 mb-3">
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-gray-400">Type:</span>
                            <span class="text-white">${cred.credential_type}</span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-gray-400">Host:</span>
                            <span class="text-white font-mono text-xs">${cred.host}:${cred.port}</span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-gray-400">Site:</span>
                            <span class="text-white">${cred.unifi_site}</span>
                        </div>
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-gray-400">Status:</span>
                            ${statusBadge}
                        </div>
                    </div>
                    ${cred.last_test ? `<div class="text-xs text-gray-500">Last tested: ${new Date(cred.last_test).toLocaleString()}</div>` : ''}
                </div>
            `
        }).join('')
    }
    
    async createUniFiCredential(formData) {
        try {
            console.log('Creating UniFi credential:', formData)
            const response = await fetch(`${API_BASE}/api/unifi/credentials`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            
            const result = await response.json()
            console.log('Create UniFi credential response:', result)
            
            if (response.ok) {
                await this.loadUniFiCredentials()
                closeModal('create-unifi-modal')
                
                // Ask if user wants to test the credential
                if (confirm('UniFi credential created! Would you like to test the connection now?')) {
                    await this.testUniFiCredential(result.credential.id)
                }
            } else {
                throw new Error(result.detail || 'Failed to create UniFi credential')
            }
        } catch (error) {
            console.error('Error creating UniFi credential:', error)
            alert('Failed to create UniFi credential: ' + error.message)
        }
    }
    
    async testUniFiCredential(id) {
        const button = event?.target
        const originalText = button?.textContent
        
        if (button) {
            button.textContent = 'Testing...'
            button.disabled = true
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/unifi/credentials/${id}/test`, {
                method: 'POST'
            })
            
            const result = await response.json()
            
            if (result.success) {
                const details = result.type === 'protect' 
                    ? `Connected to UniFi Protect!\n\nNVR: ${result.nvr_name}\nVersion: ${result.nvr_version}\nCameras: ${result.camera_count}`
                    : `Connected to UniFi Controller!\n\nSite: ${result.site_name}\nDevices: ${result.device_count}\nVersion: ${result.controller_version}`
                
                alert(details)
                await this.loadUniFiCredentials()
            } else {
                alert('Connection failed:\n\n' + (result.error || 'Unknown error'))
            }
        } catch (error) {
            console.error('Error testing UniFi credential:', error)
            alert('Failed to test credential: ' + error.message)
        } finally {
            if (button) {
                button.textContent = originalText
                button.disabled = false
            }
        }
    }
    
    async deleteUniFiCredential(id) {
        if (!confirm('Are you sure you want to delete this UniFi credential?')) {
            return
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/unifi/credentials/${id}`, {
                method: 'DELETE'
            })
            
            if (response.ok) {
                await this.loadUniFiCredentials()
                alert('UniFi credential deleted successfully')
            } else {
                throw new Error('Failed to delete UniFi credential')
            }
        } catch (error) {
            console.error('Error deleting UniFi credential:', error)
            alert('Failed to delete UniFi credential: ' + error.message)
        }
    }
    
    populateUniFiSelects() {
        // Populate organization selects in UniFi modal
        const orgSelect = document.getElementById('unifi-org-select')
        if (orgSelect) {
            orgSelect.innerHTML = '<option value="">None (Global)</option>' + 
                this.organizations.map(org => 
                    `<option value="${org.id}">${org.name}</option>`
                ).join('')
        }
        
        // Populate site selects in UniFi modal
        const siteSelect = document.getElementById('unifi-site-select')
        if (siteSelect) {
            siteSelect.innerHTML = '<option value="">None</option>' + 
                this.sites.map(site => 
                    `<option value="${site.id}">${site.name}</option>`
                ).join('')
        }
    }
}

// Global admin instance
let admin = null

// Tab switching
function showAdminTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active')
    })
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active')
    
    // Update tab content
    document.querySelectorAll('.admin-tab-content').forEach(content => {
        content.classList.remove('active')
    })
    document.getElementById(`admin-${tabName}`)?.classList.add('active')
}

// Modal management
function showCreateOrganizationModal() {
    const modal = document.getElementById('create-organization-modal')
    if (modal) {
        modal.classList.remove('hidden')
    }
}

async function showCreateSiteModal() {
    const modal = document.getElementById('create-site-modal')
    if (modal) {
        modal.classList.remove('hidden')
        // Populate organization dropdown
        if (admin) {
            // Ensure data is loaded first
            if (admin.organizations.length === 0) {
                await admin.loadOrganizations()
            }
            admin.populateSiteSelects()
        }
    }
}

async function showCreateSublocationModal() {
    const modal = document.getElementById('create-sublocation-modal')
    if (modal) {
        modal.classList.remove('hidden')
        // Populate site dropdown
        if (admin) {
            // Ensure data is loaded first
            if (admin.sites.length === 0) {
                await admin.loadSites()
            }
            admin.populateSublocationSelects()
        }
    }
}

async function showCreateCameraModal() {
    const modal = document.getElementById('create-camera-modal')
    if (modal) {
        modal.classList.remove('hidden')
        // Populate sublocation dropdown
        if (admin) {
            // Ensure data is loaded first
            if (admin.sublocations.length === 0) {
                await admin.loadSublocations()
            }
            admin.populateSublocationSelects()
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId)
    if (modal) {
        modal.classList.add('hidden')
    }
}

// Form handlers
async function createOrganization(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
        id: 'org-' + Date.now(),
        name: formData.get('name'),
        description: formData.get('description'),
        organization_type: formData.get('organization_type')
    }
    await admin.createOrganization(data)
    event.target.reset()
}

async function createSite(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const locationStr = formData.get('location')
    const data = {
        id: 'site-' + Date.now(),
        organization_id: formData.get('organization_id'),
        name: formData.get('name'),
        description: formData.get('description'),
        site_type: formData.get('site_type'),
        location: locationStr ? { address: locationStr } : {}
    }
    await admin.createSite(data)
    event.target.reset()
}

async function createSublocation(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
        id: 'sub-' + Date.now(),
        site_id: formData.get('site_id'),
        name: formData.get('name'),
        description: formData.get('description'),
        sublocation_type: formData.get('area_type')
    }
    await admin.createSublocation(data)
    event.target.reset()
}

async function createCamera(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
        id: 'cam-' + Date.now(),
        sublocation_id: formData.get('sublocation_id'),
        name: formData.get('name'),
        type: formData.get('type'),
        rtsp_url: formData.get('rtsp_url'),
        enabled: formData.get('enabled') === 'on'
    }
    await admin.createCamera(data)
    event.target.reset()
}

async function createUniFiCredential(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
        name: formData.get('name'),
        credential_type: formData.get('credential_type'),
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        username: formData.get('username'),
        password: formData.get('password'),
        unifi_site: formData.get('unifi_site') || 'default',
        verify_ssl: formData.get('verify_ssl') === 'on',
        organization_id: formData.get('organization_id') || null,
        site_id: formData.get('site_id') || null,
        enabled: true
    }
    await admin.createUniFiCredential(data)
    event.target.reset()
}

function showCreateUniFiModal() {
    admin.populateUniFiSelects()
    showModal('create-unifi-modal')
}

