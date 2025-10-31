import { useState, useEffect } from 'react'
import { apiBaseUrl } from '../config'

export default function ConfigPanel({ isOpen, onClose }) {
  const [config, setConfig] = useState(null)
  const [requirements, setRequirements] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('models')

  useEffect(() => {
    if (isOpen) {
      loadConfig()
      checkRequirements()
    }
  }, [isOpen])

  const loadConfig = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/config/`)
      const data = await response.json()
      setConfig(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load config:', error)
      setLoading(false)
    }
  }

  const checkRequirements = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/config/check-requirements`, {
        method: 'POST'
      })
      const data = await response.json()
      setRequirements(data)
    } catch (error) {
      console.error('Failed to check requirements:', error)
    }
  }

  const toggleItem = async (type, id) => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/config/${type}/${id}/toggle`, {
        method: 'POST'
      })
      const result = await response.json()
      
      if (result.status === 'success') {
        loadConfig()
      }
    } catch (error) {
      console.error('Failed to toggle item:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-[800px] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Workflow Configuration</h2>
            <p className="text-sm text-gray-400 mt-1">Manage available models and nodes</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-4 flex space-x-4 border-b border-gray-800">
          <button
            onClick={() => setActiveTab('models')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'models'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            🤖 AI Models ({config?.models?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('nodes')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'nodes'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            🔧 Input Nodes ({config?.nodes?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            ⚙️ Settings
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12 text-gray-400">Loading configuration...</div>
          ) : (
            <>
              {/* Models Tab */}
              {activeTab === 'models' && (
                <div className="space-y-3">
                  {config?.models?.map((model) => {
                    const reqStatus = requirements?.models?.[model.id]
                    return (
                      <div
                        key={model.id}
                        className={`p-4 rounded-lg border ${
                          model.enabled
                            ? 'bg-gray-800 border-gray-700'
                            : 'bg-gray-900/50 border-gray-800 opacity-60'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h3 className="font-semibold text-white">{model.id}</h3>
                              <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded">
                                v{model.version}
                              </span>
                              {reqStatus && !reqStatus.all_met && (
                                <span className="text-xs bg-red-900/50 text-red-300 px-2 py-0.5 rounded">
                                  ⚠️ Requirements missing
                                </span>
                              )}
                            </div>
                            {model.notes && (
                              <p className="text-xs text-gray-400 mt-1">{model.notes}</p>
                            )}
                            {model.requirements && model.requirements.length > 0 && (
                              <div className="mt-2">
                                <div className="text-xs text-gray-500 mb-1">Requirements:</div>
                                <div className="flex flex-wrap gap-2">
                                  {model.requirements.map((req, idx) => {
                                    const reqMet = reqStatus?.requirements?.[idx]?.installed
                                    return (
                                      <span
                                        key={idx}
                                        className={`text-xs px-2 py-0.5 rounded font-mono ${
                                          reqMet === false
                                            ? 'bg-red-900/30 text-red-400'
                                            : 'bg-gray-700 text-gray-300'
                                        }`}
                                      >
                                        {reqMet === false && '❌ '}
                                        {req}
                                      </span>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => toggleItem('models', model.id)}
                            className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
                              model.enabled
                                ? 'bg-green-600 hover:bg-green-700 text-white'
                                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                            }`}
                          >
                            {model.enabled ? '✓ Enabled' : 'Disabled'}
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Nodes Tab */}
              {activeTab === 'nodes' && (
                <div className="space-y-3">
                  {config?.nodes?.map((node) => {
                    const reqStatus = requirements?.nodes?.[node.id]
                    return (
                      <div
                        key={node.id}
                        className={`p-4 rounded-lg border ${
                          node.enabled
                            ? 'bg-gray-800 border-gray-700'
                            : 'bg-gray-900/50 border-gray-800 opacity-60'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h3 className="font-semibold text-white capitalize">{node.id}</h3>
                              <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded">
                                v{node.version}
                              </span>
                              {reqStatus && !reqStatus.all_met && (
                                <span className="text-xs bg-red-900/50 text-red-300 px-2 py-0.5 rounded">
                                  ⚠️ Requirements missing
                                </span>
                              )}
                            </div>
                            {node.notes && (
                              <p className="text-xs text-gray-400 mt-1">{node.notes}</p>
                            )}
                            {node.requirements && node.requirements.length > 0 && (
                              <div className="mt-2">
                                <div className="text-xs text-gray-500 mb-1">Requirements:</div>
                                <div className="flex flex-wrap gap-2">
                                  {node.requirements.map((req, idx) => {
                                    const reqMet = reqStatus?.requirements?.[idx]?.installed
                                    return (
                                      <span
                                        key={idx}
                                        className={`text-xs px-2 py-0.5 rounded font-mono ${
                                          reqMet === false
                                            ? 'bg-red-900/30 text-red-400'
                                            : 'bg-gray-700 text-gray-300'
                                        }`}
                                      >
                                        {reqMet === false && '❌ '}
                                        {req}
                                      </span>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => toggleItem('nodes', node.id)}
                            className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
                              node.enabled
                                ? 'bg-green-600 hover:bg-green-700 text-white'
                                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                            }`}
                          >
                            {node.enabled ? '✓ Enabled' : 'Disabled'}
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Settings Tab */}
              {activeTab === 'settings' && (
                <div className="space-y-4">
                  <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
                    <h3 className="font-semibold text-white mb-3">Global Settings</h3>
                    {config?.global_settings && Object.entries(config.global_settings).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                        <span className="text-sm text-gray-300 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-sm text-gray-400 font-mono">{value.toString()}</span>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="text-sm font-medium text-blue-400 mb-2">💡 Coming Soon</div>
                    <ul className="text-xs text-gray-400 space-y-1">
                      <li>• Per-user model assignments</li>
                      <li>• Model usage quotas</li>
                      <li>• Performance monitoring</li>
                      <li>• Auto-update settings</li>
                    </ul>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between">
          <button
            onClick={checkRequirements}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white"
          >
            🔄 Check Requirements
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}

