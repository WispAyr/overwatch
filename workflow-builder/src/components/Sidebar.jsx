import React, { useState } from 'react'
import useComponentStatus from '../hooks/useComponentStatus'
import NodeStatusBadge from './NodeStatusBadge'

const Sidebar = ({ cameras, models, actions, filters }) => {
  const [activeCategory, setActiveCategory] = useState('inputs')
  const { getNodeStatus, getModelsByStatus, loading: statusLoading } = useComponentStatus()
  const [showComingSoon, setShowComingSoon] = useState(false)
  
  // Debug logging
  console.log('Sidebar received:', { 
    cameras: cameras?.length, 
    models: models?.length, 
    actions: actions?.length, 
    filters: filters?.length 
  })

  const onDragStart = (event, nodeType, nodeData = {}) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.setData('application/json', JSON.stringify(nodeData))
    event.dataTransfer.effectAllowed = 'move'
  }

  // Filter models by status
  const filteredModels = React.useMemo(() => {
    if (statusLoading) return models
    
    return models.filter(model => {
      const status = getNodeStatus('model', model.id)
      if (!status) return true // Show if no status info
      
      // Hide notImplemented unless user toggles to show them
      if (status.status === 'notImplemented' && !showComingSoon) {
        return false
      }
      
      return true
    })
  }, [models, statusLoading, getNodeStatus, showComingSoon])

  const categories = {
    inputs: {
      name: 'Input Sources',
      icon: '📹',
      items: [
        { type: 'camera', label: 'Camera Feed', icon: '📹', description: 'Live camera stream' },
        { type: 'videoInput', label: 'Video File', icon: '🎥', description: 'Upload video file' },
        { type: 'youtube', label: 'YouTube', icon: '▶️', description: 'YouTube video stream' },
      ]
    },
    models: {
      name: 'AI Models',
      icon: '🤖',
      items: filteredModels.map(model => ({
        type: 'model',
        label: model.name || model.id,
        icon: '🤖',
        description: model.type || 'Detection model',
        data: { modelId: model.id, modelName: model.name },
        modelId: model.id // For status lookup
      }))
    },
    processing: {
      name: 'Processing',
      icon: '⚙️',
      items: [
        { type: 'zone', label: 'Zone Filter', icon: '📍', description: 'Define detection zones' },
        { type: 'detectionFilter', label: 'Detection Filter', icon: '🔍', description: 'Filter by count, class, confidence' },
        { type: 'parkingViolation', label: 'Parking Violation', icon: '🚗', description: 'Detect illegal parking' },
        { type: 'audioExtractor', label: 'Audio Extractor', icon: '🎵', description: 'Extract audio from video' },
        { type: 'dayNightDetector', label: 'Day/Night/IR Detector', icon: '🌓', description: 'Detect lighting conditions & IR mode' },
      ]
    },
    audio: {
      name: 'Audio AI',
      icon: '🎤',
      items: [
        { type: 'audioAI', label: 'Whisper (Tiny)', icon: '🎙️', description: 'Fast speech transcription', data: { modelId: 'whisper-tiny', modelName: 'Whisper Tiny', modelType: 'transcription' } },
        { type: 'audioAI', label: 'Whisper (Base)', icon: '🎙️', description: 'Balanced transcription', data: { modelId: 'whisper-base', modelName: 'Whisper Base', modelType: 'transcription' } },
        { type: 'audioAI', label: 'Whisper (Small)', icon: '🎙️', description: 'High quality transcription', data: { modelId: 'whisper-small', modelName: 'Whisper Small', modelType: 'transcription' } },
        { type: 'audioAI', label: 'Sound Classifier', icon: '🔊', description: 'Detect gunshots, alarms, etc.', data: { modelId: 'yamnet', modelName: 'YAMNet', modelType: 'sound_classification' } },
        { type: 'audioVU', label: 'VU/Frequency Meter', icon: '📻', description: 'Audio visualization with triggers', data: {} },
      ]
    },
    actions: {
      name: 'Actions',
      icon: '⚡',
      items: actions.map(action => ({
        type: 'action',
        label: action.name || action.id,
        icon: '⚡',
        description: action.description || 'Trigger action',
        data: { actionId: action.id, actionType: action.type }
      }))
    },
    config: {
      name: 'Configuration',
      icon: '⚙️',
      items: [
        { type: 'config', label: 'Config Node', icon: '⚙️', description: 'Reusable configuration', data: { configType: 'generic' } },
        { type: 'config', label: 'Model Config', icon: '🤖', description: 'AI model settings', data: { configType: 'model', configName: 'Model Settings', config: { confidence: 0.7, classes: [0] } } },
        { type: 'config', label: 'Webhook Config', icon: '🔗', description: 'Webhook settings', data: { configType: 'webhook', configName: 'Webhook', config: { method: 'POST', timeout: 10 } } },
        { type: 'config', label: 'Recording Config', icon: '🎬', description: 'Recording settings', data: { configType: 'record', configName: 'Recording', config: { duration: 30, preBuffer: 5 } } },
      ]
    },
    debug: {
      name: 'Debug & Output',
      icon: '🔍',
      items: [
        { type: 'dataPreview', label: 'Data Preview', icon: '👁️', description: 'View detection data' },
        { type: 'videoPreview', label: 'X-RAY View', icon: '🔍', description: 'See what the AI sees (Coming Soon)' },
        { type: 'debug', label: 'Debug Console', icon: '🐛', description: 'All workflow messages' },
      ]
    },
    drone: {
      name: 'Drone Detection',
      icon: '🛸',
      items: [
        { type: 'droneInput', label: 'Drone Input', icon: '🛸', description: 'Meshtastic receiver input' },
        { type: 'droneFilter', label: 'Drone Filter', icon: '📐', description: 'Altitude/speed/geofence filtering' },
        { type: 'droneMap', label: 'Drone Map', icon: '🗺️', description: 'Real-time map visualization' },
        { type: 'droneAction', label: 'Drone Action', icon: '🚨', description: 'Drone-specific response actions' },
        { type: 'droneAnalytics', label: 'Drone Analytics', icon: '📊', description: 'Statistical analysis' },
      ]
    },
    unifi: {
      name: 'UniFi Integration',
      icon: '📡',
      items: [
        { type: 'unifiCameraDiscovery', label: 'Camera Discovery', icon: '📡', description: 'Discover UniFi Protect cameras' },
        { type: 'unifiProtectEvent', label: 'Protect Events', icon: '🎥', description: 'Monitor motion & smart detections' },
        { type: 'unifiAddCamera', label: 'Add Cameras', icon: '➕', description: 'Auto-provision cameras to Overwatch' },
      ]
    },
    advanced: {
      name: 'Advanced',
      icon: '🔧',
      items: [
        { type: 'linkIn', label: 'Link In', icon: '📥', description: 'Subflow entry point' },
        { type: 'linkOut', label: 'Link Out', icon: '📤', description: 'Subflow exit point' },
        { type: 'linkCall', label: 'Link Call', icon: '🔗', description: 'Call subflow' },
        { type: 'catch', label: 'Catch Error', icon: '🚨', description: 'Error handler' },
      ]
    }
  }

  return (
    <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-lg font-semibold text-white">Components</h2>
        <p className="text-xs text-gray-400 mt-1">Drag items onto the canvas</p>
      </div>

      {/* Category Tabs */}
      <div className="flex overflow-x-auto border-b border-gray-800 bg-gray-900/50">
        {Object.entries(categories).map(([key, category]) => (
          <button
            key={key}
            onClick={() => setActiveCategory(key)}
            className={`flex-1 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeCategory === key
                ? 'border-blue-500 text-blue-400 bg-gray-800/50'
                : 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-800/30'
            }`}
          >
            <div className="flex flex-col items-center space-y-1">
              <span className="text-base">{category.icon}</span>
              <span>{category.name.split(' ')[0]}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Show/Hide Coming Soon toggle for models */}
        {activeCategory === 'models' && !statusLoading && (
          <div className="mb-3 flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showComingSoon}
                onChange={(e) => setShowComingSoon(e.target.checked)}
                className="rounded"
              />
              Show "Coming Soon" models
            </label>
          </div>
        )}

        <div className="space-y-2">
          {categories[activeCategory]?.items?.map((item, idx) => {
            const nodeStatus = getNodeStatus(item.type, item.modelId || item.type)
            const showWarning = nodeStatus && !nodeStatus.dependenciesMet && nodeStatus.status === 'needsConfig'
            
            return (
              <div
                key={idx}
                draggable
                onDragStart={(e) => onDragStart(e, item.type, item.data)}
                className={`bg-gray-800 hover:bg-gray-750 border rounded-lg p-3 cursor-move transition-all active:scale-95 ${
                  showWarning ? 'border-yellow-500' : 'border-gray-700 hover:border-gray-600'
                }`}
                title={nodeStatus?.message || item.description}
              >
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{item.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="font-medium text-white text-sm">{item.label}</div>
                      {!statusLoading && (
                        <NodeStatusBadge 
                          nodeType={item.type} 
                          nodeId={item.modelId || item.type}
                          size="xs"
                        />
                      )}
                    </div>
                    <div className="text-xs text-gray-400">{item.description}</div>
                    {showWarning && (
                      <div className="mt-1 text-xs text-yellow-400">
                        ⚠️ Setup required
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
          
          {/* Empty state */}
          {(!categories[activeCategory]?.items || categories[activeCategory]?.items.length === 0) && (
            <div className="text-center py-8 text-gray-500 text-sm">
              <div className="text-2xl mb-2">📭</div>
              <div>No items available</div>
              <div className="text-xs mt-1">
                {activeCategory === 'models' && !showComingSoon 
                  ? 'Enable "Show Coming Soon" to see planned models'
                  : 'Configure models/actions in settings'}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Camera List (if cameras available) */}
      {cameras.length > 0 && activeCategory === 'inputs' && (
        <div className="border-t border-gray-800 p-4">
          <div className="text-xs font-medium text-gray-400 mb-2">Available Cameras</div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {cameras.map((camera, idx) => (
              <div
                key={idx}
                draggable
                onDragStart={(e) => onDragStart(e, 'camera', { 
                  cameraId: camera.id, 
                  cameraName: camera.name 
                })}
                className="text-xs bg-gray-800/50 hover:bg-gray-700 border border-gray-700/50 rounded px-2 py-1 cursor-move transition-colors"
              >
                <div className="font-medium text-gray-300">{camera.name}</div>
                <div className="text-gray-500">{camera.id}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer hint */}
      <div className="p-3 border-t border-gray-800 bg-gray-900/50">
        <div className="text-xs text-gray-500 text-center">
          💡 Drag and drop to build your workflow
        </div>
      </div>
    </div>
  )
}

export default Sidebar
