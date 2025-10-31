/**
 * Workflow Monitor - Live production workflow monitoring
 * Real-time status, errors, logs, and controls
 */

class WorkflowMonitor {
    constructor() {
        this.workflows = []
        this.errorLog = []
        this.systemMetrics = {
            cpu: [],
            memory: [],
            fps: []
        }
        this.selectedWorkflow = null
        this.ws = null
        this.autoRefresh = true
        
        this.init()
    }
    
    async init() {
        console.log('Initializing Workflow Monitor...')
        
        // Load initial data
        await this.loadWorkflows()
        await this.loadSystemMetrics()
        
        // Connect WebSocket for live updates
        this.connectWebSocket()
        
        // Start auto-refresh if enabled
        setInterval(() => {
            if (this.autoRefresh) {
                this.loadWorkflows()
                this.loadSystemMetrics()
            }
        }, 5000) // Refresh every 5 seconds
        
        // Auto-refresh toggle
        document.getElementById('auto-refresh-toggle')?.addEventListener('change', (e) => {
            this.autoRefresh = e.target.checked
        })
    }
    
    async loadWorkflows() {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder`)
            const data = await response.json()
            this.workflows = data.workflows || []
            
            // Get execution status for each
            await this.enrichWorkflowStatus()
            
            this.renderWorkflows()
            this.updateStats()
        } catch (error) {
            console.error('Failed to load workflows:', error)
            this.addErrorLog('Failed to load workflows: ' + error.message, 'error')
        }
    }
    
    async enrichWorkflowStatus() {
        // Get real-time status from backend
        for (let workflow of this.workflows) {
            try {
                const response = await fetch(`${API_BASE}/api/workflow-builder/${workflow.id}/status`)
                if (response.ok) {
                    const status = await response.json()
                    workflow.runtime_status = status
                }
            } catch (error) {
                console.warn(`Failed to get status for ${workflow.id}`)
            }
        }
    }
    
    renderWorkflows() {
        const container = document.getElementById('running-workflows-container')
        if (!container) return
        
        const filtered = this.getFilteredWorkflows()
        
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <div class="text-4xl mb-3">📭</div>
                    <div>No workflows match your filter</div>
                </div>
            `
            return
        }
        
        container.innerHTML = filtered.map(wf => this.renderWorkflowCard(wf)).join('')
    }
    
    renderWorkflowCard(workflow) {
        const status = workflow.runtime_status || {}
        const state = status.state || workflow.status || 'stopped'
        const isRunning = state === 'running'
        const hasError = status.error_count > 0 || state === 'error'
        
        const statusClass = isRunning ? 'running' : hasError ? 'error' : 'stopped'
        const statusColor = isRunning ? 'text-green-400' : hasError ? 'text-red-400' : 'text-gray-500'
        const statusIcon = isRunning ? '●' : hasError ? '⚠️' : '○'
        
        return `
            <div class="workflow-item ${statusClass} mb-3" data-workflow-id="${workflow.id}">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2 mb-1">
                            <span class="${statusColor} text-lg">${statusIcon}</span>
                            <h4 class="font-semibold text-white truncate">${workflow.name || 'Untitled'}</h4>
                            ${workflow.is_master ? '<span class="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded">MASTER</span>' : ''}
                        </div>
                        <div class="text-xs text-gray-500">ID: ${workflow.id}</div>
                        ${workflow.site_name ? `<div class="text-xs text-blue-400 mt-1">📍 ${workflow.site_name}</div>` : ''}
                    </div>
                    
                    <div class="flex items-center space-x-2">
                        ${isRunning ? `
                            <button onclick="workflowMonitor.stopWorkflow('${workflow.id}')" 
                                    class="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded text-xs text-white transition-colors">
                                ⏹️ Stop
                            </button>
                        ` : `
                            <button onclick="workflowMonitor.startWorkflow('${workflow.id}')" 
                                    class="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-xs text-white transition-colors">
                                ▶️ Start
                            </button>
                        `}
                        <button onclick="workflowMonitor.showWorkflowDetail('${workflow.id}')" 
                                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white transition-colors">
                            📊 Details
                        </button>
                        <button onclick="window.open('http://localhost:7003?workflow=${workflow.id}', '_blank')" 
                                class="px-3 py-1.5 bg-gray-600 hover:bg-gray-700 rounded text-xs text-white transition-colors">
                            ✏️ Edit
                        </button>
                    </div>
                </div>
                
                <!-- Metrics -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                    <div class="bg-gray-900/50 rounded p-2">
                        <div class="text-gray-500">Status</div>
                        <div class="${statusColor} font-medium mt-1">${state.toUpperCase()}</div>
                    </div>
                    <div class="bg-gray-900/50 rounded p-2">
                        <div class="text-gray-500">Uptime</div>
                        <div class="text-white font-medium mt-1">${this.formatUptime(status.uptime)}</div>
                    </div>
                    <div class="bg-gray-900/50 rounded p-2">
                        <div class="text-gray-500">FPS</div>
                        <div class="text-white font-medium mt-1">${status.fps || '--'}</div>
                    </div>
                    <div class="bg-gray-900/50 rounded p-2">
                        <div class="text-gray-500">Detections</div>
                        <div class="text-white font-medium mt-1">${status.total_detections || 0}</div>
                    </div>
                    <div class="bg-gray-900/50 rounded p-2">
                        <div class="text-gray-500">Errors</div>
                        <div class="${status.error_count > 0 ? 'text-red-400' : 'text-white'} font-medium mt-1">${status.error_count || 0}</div>
                    </div>
                </div>
                
                <!-- Latest Error (if any) -->
                ${status.latest_error ? `
                    <div class="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded">
                        <div class="text-xs text-red-400 font-mono">${status.latest_error}</div>
                        <div class="text-xs text-gray-500 mt-1">${new Date(status.error_timestamp).toLocaleString()}</div>
                    </div>
                ` : ''}
            </div>
        `
    }
    
    getFilteredWorkflows() {
        const statusFilter = document.getElementById('monitor-status-filter')?.value || 'all'
        const siteFilter = document.getElementById('monitor-site-filter')?.value || 'all'
        const searchTerm = document.getElementById('monitor-search')?.value?.toLowerCase() || ''
        
        return this.workflows.filter(wf => {
            // Status filter
            if (statusFilter !== 'all') {
                const state = wf.runtime_status?.state || wf.status || 'stopped'
                if (statusFilter === 'running' && state !== 'running') return false
                if (statusFilter === 'error' && state !== 'error') return false
                if (statusFilter === 'stopped' && state !== 'stopped') return false
            }
            
            // Site filter
            if (siteFilter !== 'all' && wf.site_id !== siteFilter) return false
            
            // Search filter
            if (searchTerm && !wf.name?.toLowerCase().includes(searchTerm)) return false
            
            return true
        })
    }
    
    updateStats() {
        const running = this.workflows.filter(wf => wf.runtime_status?.state === 'running').length
        const healthy = this.workflows.filter(wf => 
            wf.runtime_status?.state === 'running' && 
            (wf.runtime_status?.error_count || 0) === 0
        ).length
        const warnings = this.workflows.filter(wf => 
            (wf.runtime_status?.warning_count || 0) > 0
        ).length
        const errors = this.workflows.filter(wf => 
            (wf.runtime_status?.error_count || 0) > 0
        ).length
        
        const totalDetections = this.workflows.reduce((sum, wf) => 
            sum + (wf.runtime_status?.detections_per_minute || 0), 0
        )
        
        document.getElementById('monitor-stat-running').textContent = running
        document.getElementById('monitor-stat-healthy').textContent = healthy
        document.getElementById('monitor-stat-warnings').textContent = warnings
        document.getElementById('monitor-stat-errors').textContent = errors
        document.getElementById('monitor-stat-detections').textContent = Math.round(totalDetections)
    }
    
    async startWorkflow(workflowId) {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workflow_id: workflowId })
            })
            
            if (response.ok) {
                this.addErrorLog(`Started workflow: ${workflowId}`, 'info')
                await this.loadWorkflows()
            } else {
                throw new Error('Failed to start workflow')
            }
        } catch (error) {
            this.addErrorLog(`Failed to start workflow: ${error.message}`, 'error')
        }
    }
    
    async stopWorkflow(workflowId) {
        try {
            const response = await fetch(`${API_BASE}/api/workflow-builder/${workflowId}/stop`, {
                method: 'POST'
            })
            
            if (response.ok) {
                this.addErrorLog(`Stopped workflow: ${workflowId}`, 'info')
                await this.loadWorkflows()
            } else {
                throw new Error('Failed to stop workflow')
            }
        } catch (error) {
            this.addErrorLog(`Failed to stop workflow: ${error.message}`, 'error')
        }
    }
    
    async restartWorkflow(workflowId) {
        await this.stopWorkflow(workflowId)
        setTimeout(() => this.startWorkflow(workflowId), 2000)
    }
    
    showWorkflowDetail(workflowId) {
        this.selectedWorkflow = this.workflows.find(wf => wf.id === workflowId)
        if (!this.selectedWorkflow) return
        
        const modal = document.getElementById('workflow-detail-modal')
        modal.classList.remove('hidden')
        
        // Populate modal
        document.getElementById('detail-workflow-name').textContent = this.selectedWorkflow.name
        document.getElementById('detail-workflow-id').textContent = `ID: ${this.selectedWorkflow.id}`
        
        const status = this.selectedWorkflow.runtime_status || {}
        document.getElementById('detail-status').textContent = status.state || 'stopped'
        document.getElementById('detail-uptime').textContent = this.formatUptime(status.uptime)
        document.getElementById('detail-fps').textContent = status.fps || '--'
        document.getElementById('detail-detections').textContent = status.total_detections || 0
        
        // Start live log streaming
        this.streamWorkflowLogs(workflowId)
    }
    
    closeWorkflowDetail() {
        document.getElementById('workflow-detail-modal').classList.add('hidden')
        this.selectedWorkflow = null
    }
    
    streamWorkflowLogs(workflowId) {
        // Subscribe to workflow logs via WebSocket
        const logsContainer = document.getElementById('detail-logs')
        logsContainer.innerHTML = '<div class="text-gray-500">Connecting to log stream...</div>'
        
        // Simulate log streaming (replace with actual WebSocket)
        setTimeout(() => {
            logsContainer.innerHTML = `
                <div>[${new Date().toISOString()}] Workflow started</div>
                <div>[${new Date().toISOString()}] Initializing camera stream...</div>
                <div>[${new Date().toISOString()}] Model loaded: YOLOv8n</div>
                <div>[${new Date().toISOString()}] Processing frames at 10 FPS</div>
                <div class="text-green-400">[${new Date().toISOString()}] ✓ Workflow running</div>
            `
        }, 500)
    }
    
    addErrorLog(message, level = 'info') {
        const entry = {
            timestamp: new Date(),
            message,
            level
        }
        
        this.errorLog.unshift(entry)
        if (this.errorLog.length > 100) {
            this.errorLog = this.errorLog.slice(0, 100)
        }
        
        this.renderErrorLog()
    }
    
    renderErrorLog() {
        const container = document.getElementById('error-log')
        if (!container) return
        
        if (this.errorLog.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-center py-4">No errors or warnings</div>'
            return
        }
        
        container.innerHTML = this.errorLog.map(entry => `
            <div class="log-entry ${entry.level}">
                <span class="text-gray-600">[${entry.timestamp.toLocaleTimeString()}]</span>
                <span class="ml-2">${entry.message}</span>
            </div>
        `).join('')
    }
    
    clearErrorLog() {
        if (confirm('Clear all error logs?')) {
            this.errorLog = []
            this.renderErrorLog()
        }
    }
    
    exportErrorLog() {
        const text = this.errorLog.map(e => 
            `[${e.timestamp.toISOString()}] [${e.level.toUpperCase()}] ${e.message}`
        ).join('\n')
        
        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `workflow-errors-${Date.now()}.log`
        a.click()
        URL.revokeObjectURL(url)
    }
    
    async loadSystemMetrics() {
        try {
            const response = await fetch(`${API_BASE}/api/system/metrics`)
            const data = await response.json()
            
            // Update metrics arrays (keep last 10 samples)
            this.systemMetrics.cpu.push(data.cpu_percent || 0)
            this.systemMetrics.memory.push(data.memory_percent || 0)
            this.systemMetrics.fps.push(data.avg_fps || 0)
            
            if (this.systemMetrics.cpu.length > 10) {
                this.systemMetrics.cpu.shift()
                this.systemMetrics.memory.shift()
                this.systemMetrics.fps.shift()
            }
            
            this.renderMetrics()
        } catch (error) {
            console.error('Failed to load system metrics:', error)
        }
    }
    
    renderMetrics() {
        this.renderMetricBars('cpu-bars', 'cpu-current', this.systemMetrics.cpu, '%')
        this.renderMetricBars('memory-bars', 'memory-current', this.systemMetrics.memory, '%')
        this.renderMetricBars('fps-bars', 'fps-current', this.systemMetrics.fps, ' FPS')
    }
    
    renderMetricBars(containerId, currentId, data, unit) {
        const container = document.getElementById(containerId)
        const currentEl = document.getElementById(currentId)
        
        if (!container || !currentEl) return
        
        const maxValue = Math.max(...data, 1)
        const latest = data[data.length - 1] || 0
        
        container.innerHTML = data.map(value => {
            const height = (value / maxValue) * 100
            const colorClass = value > 80 ? 'high' : value > 50 ? 'medium' : 'low'
            return `<div class="metric-bar ${colorClass}" style="height: ${height}%"></div>`
        }).join('')
        
        currentEl.textContent = `${latest.toFixed(1)}${unit}`
    }
    
    connectWebSocket() {
        if (this.ws) {
            this.ws.close()
        }
        
        this.ws = new WebSocket(`${WS_BASE}/api/ws`)
        
        this.ws.onopen = () => {
            console.log('Workflow Monitor WebSocket connected')
        }
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            this.handleWebSocketMessage(data)
        }
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error)
            this.addErrorLog('WebSocket connection error', 'error')
        }
        
        this.ws.onclose = () => {
            console.log('WebSocket closed, reconnecting...')
            setTimeout(() => this.connectWebSocket(), 5000)
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'workflow_status':
                this.updateWorkflowStatus(data)
                break
            case 'workflow_error':
                this.handleWorkflowError(data)
                break
            case 'detection_data':
                this.handleDetection(data)
                break
            case 'system_metrics':
                this.handleSystemMetrics(data)
                break
        }
    }
    
    updateWorkflowStatus(data) {
        const workflow = this.workflows.find(wf => wf.id === data.workflow_id)
        if (workflow) {
            workflow.runtime_status = data.status
            this.renderWorkflows()
            this.updateStats()
        }
    }
    
    handleWorkflowError(data) {
        this.addErrorLog(`Workflow ${data.workflow_id}: ${data.error}`, 'error')
        this.loadWorkflows() // Refresh to show updated error counts
    }
    
    handleDetection(data) {
        // Update detection counts
        const workflow = this.workflows.find(wf => wf.id === data.workflow_id)
        if (workflow && workflow.runtime_status) {
            workflow.runtime_status.total_detections = (workflow.runtime_status.total_detections || 0) + 1
            this.updateStats()
        }
    }
    
    handleSystemMetrics(data) {
        this.systemMetrics.cpu.push(data.cpu_percent)
        this.systemMetrics.memory.push(data.memory_percent)
        this.systemMetrics.fps.push(data.avg_fps)
        
        if (this.systemMetrics.cpu.length > 10) {
            this.systemMetrics.cpu.shift()
            this.systemMetrics.memory.shift()
            this.systemMetrics.fps.shift()
        }
        
        this.renderMetrics()
    }
    
    formatUptime(seconds) {
        if (!seconds) return '--'
        
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`
        }
        return `${minutes}m`
    }
}

// Global functions for onclick handlers
function refreshWorkflowMonitor() {
    if (window.workflowMonitor) {
        window.workflowMonitor.loadWorkflows()
        window.workflowMonitor.loadSystemMetrics()
    }
}

function filterWorkflows() {
    if (window.workflowMonitor) {
        window.workflowMonitor.renderWorkflows()
    }
}

function clearErrorLog() {
    if (window.workflowMonitor) {
        window.workflowMonitor.clearErrorLog()
    }
}

function exportErrorLog() {
    if (window.workflowMonitor) {
        window.workflowMonitor.exportErrorLog()
    }
}

function closeWorkflowDetail() {
    if (window.workflowMonitor) {
        window.workflowMonitor.closeWorkflowDetail()
    }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if monitor element exists
    if (document.getElementById('workflow-monitor')) {
        window.workflowMonitor = new WorkflowMonitor()
    }
})


