import { useState, useEffect } from 'react'
import { apiBaseUrl } from '../config'

export default function WorkflowLibrary({ isOpen, onClose, onOpenWorkflow, currentSiteId }) {
  const [workflows, setWorkflows] = useState([])
  const [sites, setSites] = useState([])
  const [filter, setFilter] = useState('all') // all, site, master
  const [selectedSite, setSelectedSite] = useState(currentSiteId || 'all')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadWorkflows()
      loadSites()
    }
  }, [isOpen])

  const loadWorkflows = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBaseUrl}/api/workflow-builder`)
      const data = await response.json()
      setWorkflows(data.workflows || [])
    } catch (error) {
      console.error('Failed to load workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSites = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/hierarchy/sites`)
      const data = await response.json()
      setSites(data.sites || [])
    } catch (error) {
      console.error('Failed to load sites:', error)
    }
  }

  const filteredWorkflows = workflows.filter(wf => {
    // Search filter
    if (searchTerm && !wf.name?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    
    // Type filter
    if (filter === 'master' && !wf.is_master) return false
    if (filter === 'site' && wf.is_master) return false
    
    // Site filter
    if (selectedSite !== 'all' && wf.site_id !== selectedSite) return false
    
    return true
  })

  const groupedWorkflows = {
    master: filteredWorkflows.filter(wf => wf.is_master),
    site: filteredWorkflows.filter(wf => !wf.is_master)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-[1000px] max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Workflow Library</h2>
            <p className="text-sm text-gray-400 mt-1">Browse and open existing workflows</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b border-gray-800 space-y-3">
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search workflows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            
            {/* Type Filter */}
            <div className="flex space-x-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  filter === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                All ({workflows.length})
              </button>
              <button
                onClick={() => setFilter('master')}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  filter === 'master'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                ★ Master ({groupedWorkflows.master.length})
              </button>
              <button
                onClick={() => setFilter('site')}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  filter === 'site'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                📍 Site ({groupedWorkflows.site.length})
              </button>
            </div>
          </div>

          {/* Site Selector */}
          <div className="flex items-center space-x-3">
            <label className="text-sm text-gray-400">Filter by Site:</label>
            <select
              value={selectedSite}
              onChange={(e) => setSelectedSite(e.target.value)}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white"
            >
              <option value="all">All Sites</option>
              {sites.map(site => (
                <option key={site.id} value={site.id}>{site.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Workflow List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12 text-gray-400">Loading workflows...</div>
          ) : filteredWorkflows.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-3">📭</div>
              <div>No workflows found</div>
              <div className="text-sm mt-1">Try adjusting your filters</div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Master Workflows */}
              {groupedWorkflows.master.length > 0 && filter !== 'site' && (
                <div>
                  <h3 className="text-sm font-semibold text-purple-400 mb-3 flex items-center">
                    <span className="mr-2">★</span>
                    Master Workflows ({groupedWorkflows.master.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groupedWorkflows.master.map(wf => (
                      <WorkflowCard key={wf.id} workflow={wf} onOpen={onOpenWorkflow} isMaster />
                    ))}
                  </div>
                </div>
              )}

              {/* Site Workflows */}
              {groupedWorkflows.site.length > 0 && filter !== 'master' && (
                <div>
                  <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center">
                    <span className="mr-2">📍</span>
                    Site-Specific Workflows ({groupedWorkflows.site.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groupedWorkflows.site.map(wf => (
                      <WorkflowCard key={wf.id} workflow={wf} onOpen={onOpenWorkflow} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between bg-gray-900/50">
          <div className="text-xs text-gray-500">
            💡 Tip: Cmd/Ctrl+O to open library | Cmd/Ctrl+T for new tab
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function WorkflowCard({ workflow, onOpen, isMaster }) {
  return (
    <div 
      onClick={() => onOpen(workflow)}
      className="border border-gray-700 bg-gray-800/50 rounded-lg p-4 hover:border-gray-600 hover:bg-gray-800 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            {isMaster && <span className="text-purple-400">★</span>}
            <h4 className="font-semibold text-white truncate">{workflow.name || 'Untitled'}</h4>
          </div>
          {workflow.description && (
            <p className="text-xs text-gray-400 line-clamp-2">{workflow.description}</p>
          )}
        </div>
        
        {workflow.status === 'running' && (
          <span className="ml-2 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
            Running
          </span>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mt-3">
        <div className="flex items-center space-x-3">
          <span>{workflow.nodes?.length || 0} nodes</span>
          <span>{workflow.edges?.length || 0} connections</span>
        </div>
        {workflow.updated_at && (
          <span>{new Date(workflow.updated_at).toLocaleDateString()}</span>
        )}
      </div>

      {!isMaster && workflow.site_name && (
        <div className="mt-2 text-xs text-blue-400">
          📍 {workflow.site_name}
        </div>
      )}

      <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <button className="w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white">
          Open in New Tab
        </button>
      </div>
    </div>
  )
}


