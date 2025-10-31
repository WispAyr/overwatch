import { memo, useState } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [showEditor, setShowEditor] = useState(false)
  const [configJson, setConfigJson] = useState(data.config || {})
  const [configName, setConfigName] = useState(data.configName || 'Untitled Config')
  const [isValid, setIsValid] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')

  const handleConfigChange = (e) => {
    const value = e.target.value
    
    try {
      const parsed = JSON.parse(value)
      setConfigJson(parsed)
      setIsValid(true)
      setErrorMsg('')
      
      // Update node data
      data.config = parsed
    } catch (err) {
      setIsValid(false)
      setErrorMsg(err.message)
    }
  }

  const applyTemplate = (template) => {
    setConfigJson(template)
    data.config = template
    setIsValid(true)
    setErrorMsg('')
  }

  // Pre-built templates
  const templates = {
    'YOLOv8 - Person Detection': {
      confidence: 0.7,
      classes: [0],  // person
      iou: 0.45,
      maxDetections: 100
    },
    'YOLOv8 - Vehicle Detection': {
      confidence: 0.6,
      classes: [2, 3, 5, 7],  // car, motorcycle, bus, truck
      iou: 0.5,
      maxDetections: 50
    },
    'YOLOv8 - High Accuracy': {
      confidence: 0.85,
      classes: [0, 1, 2, 15, 16],  // person, bicycle, car, cat, dog
      iou: 0.4,
      maxDetections: 200,
      agnostic: false
    },
    'Webhook - Standard POST': {
      method: 'POST',
      timeout: 10,
      retries: 3,
      headers: {
        'Content-Type': 'application/json'
      }
    },
    'Recording - Standard': {
      duration: 30,
      preBuffer: 5,
      postBuffer: 5,
      format: 'mp4',
      quality: 'medium'
    },
    'Email - Alert Template': {
      includeSnapshot: true,
      includeDetections: true,
      subject: 'Detection Alert - {{camera_name}}'
    }
  }

  const configTypes = {
    'model': 'AI Model Config',
    'webhook': 'Webhook Config',
    'record': 'Recording Config',
    'email': 'Email Config',
    'generic': 'Generic Config'
  }

  const currentType = data.configType || 'generic'

  return (
    <div className="shadow-lg rounded-lg border-2 border-yellow-500 bg-gray-900 min-w-[280px] max-w-[400px]">
      <div className="px-4 py-3 bg-yellow-950/30 border-b border-yellow-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">⚙️</span>
            <div className="font-bold text-sm text-yellow-400">Config Node</div>
          </div>
          <button
            onClick={() => setShowEditor(!showEditor)}
            className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
          >
            {showEditor ? '📝' : '👁️'}
          </button>
        </div>
        
        <input
          type="text"
          value={configName}
          onChange={(e) => {
            setConfigName(e.target.value)
            data.configName = e.target.value
          }}
          className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
          placeholder="Configuration name..."
        />
        
        <div className="mt-2 text-[10px] text-yellow-600">
          {configTypes[currentType]}
        </div>
      </div>

      {showEditor && (
        <div className="p-3 border-b border-gray-800">
          {/* Template Selector */}
          <div className="mb-3">
            <label className="text-xs text-gray-400 block mb-1">Load Template:</label>
            <select
              onChange={(e) => {
                if (e.target.value) {
                  applyTemplate(templates[e.target.value])
                }
              }}
              className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
            >
              <option value="">-- Select Template --</option>
              {Object.keys(templates).map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>

          {/* JSON Editor */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">Configuration JSON:</label>
            <textarea
              defaultValue={JSON.stringify(configJson, null, 2)}
              onChange={handleConfigChange}
              className={`w-full px-2 py-2 bg-black border ${isValid ? 'border-gray-700' : 'border-red-500'} rounded text-xs font-mono text-gray-200`}
              rows={12}
              spellCheck={false}
            />
            {!isValid && (
              <div className="text-xs text-red-400 mt-1">
                ❌ {errorMsg}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="mt-2 flex space-x-2">
            <button
              onClick={() => {
                const formatted = JSON.stringify(configJson, null, 2)
                navigator.clipboard.writeText(formatted)
                alert('Config copied to clipboard!')
              }}
              className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded"
            >
              📋 Copy
            </button>
            <button
              onClick={() => {
                setConfigJson({})
                data.config = {}
              }}
              className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded"
            >
              🗑️ Clear
            </button>
          </div>
        </div>
      )}

      {/* Config Summary */}
      <div className="px-3 py-2 bg-gray-950">
        <div className="text-xs text-gray-500 mb-1">Active Config:</div>
        <div className="text-xs font-mono text-yellow-400">
          {Object.keys(configJson).length} parameter(s)
        </div>
        <div className="text-[10px] text-gray-600 mt-1">
          {Object.keys(configJson).slice(0, 3).join(', ')}
          {Object.keys(configJson).length > 3 && '...'}
        </div>
      </div>
      
      {/* Output Handle - connects to other nodes */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-yellow-500"
        id="config-output"
      />
    </div>
  )
})


