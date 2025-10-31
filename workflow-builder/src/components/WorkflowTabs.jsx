import { useState, useCallback } from 'react'

export default function WorkflowTabs({ 
  tabs, 
  activeTabId, 
  onTabChange, 
  onTabClose, 
  onTabNew,
  onTabDuplicate,
  hasUnsavedChanges 
}) {
  const [draggedTab, setDraggedTab] = useState(null)

  const handleDragStart = (e, tabId) => {
    setDraggedTab(tabId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, targetTabId) => {
    e.preventDefault()
    if (draggedTab && draggedTab !== targetTabId) {
      // Reorder tabs
      const draggedIndex = tabs.findIndex(t => t.id === draggedTab)
      const targetIndex = tabs.findIndex(t => t.id === targetTabId)
      
      const newTabs = [...tabs]
      const [removed] = newTabs.splice(draggedIndex, 1)
      newTabs.splice(targetIndex, 0, removed)
      
      // Notify parent of reorder (you'd implement this)
      console.log('Reordered tabs:', newTabs.map(t => t.name))
    }
    setDraggedTab(null)
  }

  const handleTabClose = (e, tabId) => {
    e.stopPropagation()
    
    const tab = tabs.find(t => t.id === tabId)
    if (tab?.hasUnsavedChanges) {
      if (!confirm(`"${tab.name}" has unsaved changes. Close anyway?`)) {
        return
      }
    }
    
    onTabClose(tabId)
  }

  return (
    <div className="flex items-center bg-gray-900 border-b border-gray-800 overflow-x-auto">
      {/* Tab List */}
      <div className="flex items-center flex-1 min-w-0">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            draggable
            onDragStart={(e) => handleDragStart(e, tab.id)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, tab.id)}
            onClick={() => onTabChange(tab.id)}
            className={`
              group relative flex items-center space-x-2 px-4 py-3 border-r border-gray-800
              cursor-pointer transition-colors min-w-[140px] max-w-[200px]
              ${tab.id === activeTabId 
                ? 'bg-gray-950 text-white border-b-2 border-b-blue-500' 
                : 'bg-gray-900 text-gray-400 hover:bg-gray-850 hover:text-gray-300'
              }
              ${draggedTab === tab.id ? 'opacity-50' : ''}
            `}
          >
            {/* Site Badge */}
            {tab.siteId && (
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                tab.isMaster 
                  ? 'bg-purple-500/20 text-purple-400' 
                  : 'bg-blue-500/20 text-blue-400'
              }`}>
                {tab.isMaster ? '★' : tab.siteName?.substring(0, 3).toUpperCase() || 'SIT'}
              </span>
            )}
            
            {/* Tab Name */}
            <span className="flex-1 truncate text-sm font-medium">
              {tab.name || 'Untitled'}
            </span>
            
            {/* Unsaved Indicator */}
            {tab.hasUnsavedChanges && (
              <div className="w-2 h-2 bg-orange-500 rounded-full" title="Unsaved changes" />
            )}
            
            {/* Running Indicator */}
            {tab.isRunning && (
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Running" />
            )}
            
            {/* Close Button */}
            <button
              onClick={(e) => handleTabClose(e, tab.id)}
              className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-700 rounded p-0.5"
              title="Close tab (Ctrl+W)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Right-click Menu Trigger */}
            <div className="absolute inset-0" onContextMenu={(e) => {
              e.preventDefault()
              // Show context menu: duplicate, close others, close all, etc.
            }} />
          </div>
        ))}
      </div>
      
      {/* New Tab Button */}
      <button
        onClick={onTabNew}
        className="flex items-center space-x-1 px-3 py-3 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors border-r border-gray-800"
        title="New workflow (Ctrl+T)"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
      
      {/* Tab Actions Dropdown */}
      <div className="relative group">
        <button
          className="px-3 py-3 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          title="Tab actions"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>
        
        {/* Dropdown Menu (implement on click/hover) */}
        <div className="hidden group-hover:block absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
          <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
            📋 Duplicate Tab
          </button>
          <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
            🗑️ Close Other Tabs
          </button>
          <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
            💾 Save All
          </button>
        </div>
      </div>
    </div>
  )
}


