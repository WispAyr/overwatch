import { useState, useEffect } from 'react'
import { apiBaseUrl } from '../config'

export default function ExamplesPanel({ isOpen, onClose, onApplyExample }) {
  const [examples, setExamples] = useState([])
  const [actionExamples, setActionExamples] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('models')
  const [selectedExample, setSelectedExample] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadExamples()
    }
  }, [isOpen])

  const loadExamples = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/workflow-components/examples`)
      const data = await response.json()
      setExamples(data.examples || [])
      setActionExamples(data.action_examples || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to load examples:', error)
      setLoading(false)
    }
  }

  const createConfigNode = (example) => {
    // Create a ConfigNode with this example's config
    const configData = {
      configType: activeTab === 'models' ? 'model' : 'action',
      configName: example.name,
      config: example.config,
      description: example.description
    }
    
    onApplyExample('config', configData)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-[900px] max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Configuration Examples</h2>
            <p className="text-sm text-gray-400 mt-1">Working configurations for AI models and actions</p>
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
            🤖 AI Models ({examples.length})
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'actions'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            ⚡ Actions ({actionExamples.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Examples List */}
          <div className="w-1/2 border-r border-gray-800 overflow-y-auto p-4">
            {loading ? (
              <div className="text-center py-12 text-gray-400">Loading examples...</div>
            ) : (
              <div className="space-y-2">
                {(activeTab === 'models' ? examples : actionExamples).map((example, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedExample(example)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedExample === example
                        ? 'bg-blue-900/30 border-blue-500'
                        : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="font-semibold text-white text-sm mb-1">
                      {example.name}
                    </div>
                    <div className="text-xs text-gray-400 mb-2">
                      {example.description}
                    </div>
                    {example.modelId && (
                      <div className="text-xs text-blue-400 mb-1">
                        Model: {example.modelId}
                      </div>
                    )}
                    {example.useCase && (
                      <div className="text-xs text-gray-500">
                        💡 {example.useCase}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Preview Pane */}
          <div className="w-1/2 overflow-y-auto p-4 bg-gray-950">
            {selectedExample ? (
              <>
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {selectedExample.name}
                  </h3>
                  <p className="text-sm text-gray-400 mb-3">
                    {selectedExample.description}
                  </p>
                  
                  {selectedExample.modelId && (
                    <div className="mb-2 text-sm">
                      <span className="text-gray-500">Recommended Model:</span>
                      <span className="ml-2 text-blue-400 font-mono">{selectedExample.modelId}</span>
                    </div>
                  )}
                  
                  {selectedExample.useCase && (
                    <div className="mb-3 p-2 bg-blue-900/20 border border-blue-800/30 rounded">
                      <div className="text-xs text-blue-400 font-medium mb-1">Use Case</div>
                      <div className="text-xs text-gray-300">{selectedExample.useCase}</div>
                    </div>
                  )}
                </div>

                {/* Configuration Preview */}
                <div className="mb-4">
                  <label className="text-xs text-gray-400 block mb-2">Configuration:</label>
                  <pre className="bg-black border border-gray-700 rounded p-3 text-xs font-mono text-green-400 overflow-x-auto">
                    {JSON.stringify(selectedExample.config, null, 2)}
                  </pre>
                </div>

                {/* Apply Button */}
                <button
                  onClick={() => createConfigNode(selectedExample)}
                  className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white font-medium transition-colors"
                >
                  🎯 Create Config Node
                </button>

                <div className="mt-3 text-xs text-gray-500 text-center">
                  A new ConfigNode will be added to your canvas with these settings.
                  <br />
                  Connect it to a Model or Action node to apply the configuration.
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-3">👈</div>
                <div className="text-sm">Select an example to preview</div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between bg-gray-900/50">
          <div className="text-xs text-gray-500">
            💡 Tip: Connect Config nodes to Model/Action nodes to apply settings
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


