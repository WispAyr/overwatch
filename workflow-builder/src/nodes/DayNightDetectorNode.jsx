import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import { wsBaseUrl } from '../config'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [detectionMode, setDetectionMode] = useState(data.detectionMode || 'all')
  const [sensitivity, setSensitivity] = useState(data.sensitivity || 0.5)
  const [irThreshold, setIrThreshold] = useState(data.irThreshold || 0.7)
  const [brightnessThreshold, setBrightnessThreshold] = useState(data.brightnessThreshold || 0.3)
  const [checkInterval, setCheckInterval] = useState(data.checkInterval || 5)
  const [enableActions, setEnableActions] = useState(data.enableActions !== false)
  const [showConfig, setShowConfig] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [currentState, setCurrentState] = useState('day')
  const [currentBrightness, setCurrentBrightness] = useState(0.8)
  const [isIR, setIsIR] = useState(false)
  const [isLiveConnected, setIsLiveConnected] = useState(false)

  // Connect to WebSocket for live lighting data
  useEffect(() => {
    if (!showPreview) return
    
    // Try to connect to WebSocket for live data
    const wsUrl = `${wsBaseUrl}/api/ws`
    let ws = null
    let fallbackInterval = null
    
    console.log(`DayNight node ${id}: Connecting to WebSocket: ${wsUrl}`)
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log(`DayNight node ${id}: WebSocket connected`)
        setIsLiveConnected(true)
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          console.log(`DayNight node ${id}: Received message:`, message.type, message.node_id)
          
          // Check if this message is for our node
          if (message.type === 'dayNight_update' && message.node_id === id) {
            console.log(`DayNight node ${id}: Processing update:`, message.data)
            setCurrentState(message.data.state)
            setCurrentBrightness(message.data.brightness)
            setIsIR(message.data.is_ir)
            setIsLiveConnected(true)
          }
        } catch (err) {
          console.error(`DayNight node ${id}: Error parsing WebSocket message:`, err)
        }
      }
      
      ws.onerror = (err) => {
        console.log(`DayNight node ${id}: WebSocket error, falling back to demo mode`, err)
        setIsLiveConnected(false)
      }
      
      ws.onclose = () => {
        console.log(`DayNight node ${id}: WebSocket closed`)
        setIsLiveConnected(false)
      }
    } catch (err) {
      console.log(`DayNight node ${id}: Failed to connect WebSocket:`, err)
      setIsLiveConnected(false)
    }
    
    // Fallback: Use demo data if WebSocket doesn't connect
    setTimeout(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        fallbackInterval = setInterval(() => {
          // Simulate day/night cycle
          const hour = new Date().getHours()
          const brightness = Math.max(0, Math.min(1, (Math.sin((hour - 6) * Math.PI / 12) + 1) / 2))
          setCurrentBrightness(brightness)
          
          if (brightness < brightnessThreshold) {
            setCurrentState('night')
            setIsIR(Math.random() > 0.3) // 70% chance of IR in night mode
          } else if (brightness < 0.5) {
            setCurrentState('dusk')
            setIsIR(Math.random() > 0.7)
          } else {
            setCurrentState('day')
            setIsIR(false)
          }
        }, 2000)
      }
    }, 1000)
    
    return () => {
      if (ws) ws.close()
      if (fallbackInterval) clearInterval(fallbackInterval)
    }
  }, [showPreview, id, brightnessThreshold])

  const handleUpdate = (field, value) => {
    if (data.onChange) {
      data.onChange(id, { 
        ...data, 
        [field]: value 
      })
    }
  }

  const detectionModes = [
    { value: 'all', label: 'Day/Night/IR Detection', icon: '☀️🌙' },
    { value: 'brightness', label: 'Brightness Only', icon: '💡' },
    { value: 'ir', label: 'IR Mode Only', icon: '🔦' },
    { value: 'time_based', label: 'Time-Based (Sunset/Sunrise)', icon: '⏰' },
  ]

  const getStateColor = () => {
    if (isIR) return 'text-purple-400'
    switch (currentState) {
      case 'day': return 'text-yellow-400'
      case 'dusk': return 'text-orange-400'
      case 'night': return 'text-blue-400'
      default: return 'text-gray-400'
    }
  }

  const getStateIcon = () => {
    if (isIR) return '🔦'
    switch (currentState) {
      case 'day': return '☀️'
      case 'dusk': return '🌅'
      case 'night': return '🌙'
      default: return '❓'
    }
  }

  const getStateLabel = () => {
    if (isIR) return 'IR Mode'
    switch (currentState) {
      case 'day': return 'Daytime'
      case 'dusk': return 'Dusk/Dawn'
      case 'night': return 'Nighttime'
      default: return 'Unknown'
    }
  }

  return (
    <div className="shadow-lg rounded-lg border-2 border-yellow-500 bg-gray-900 min-w-[280px] max-w-[320px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-yellow-500"
        id="video-input"
      />
      
      {/* Live Preview */}
      {showPreview && (
        <div className="bg-gray-950 border-b border-gray-800 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-gray-400">Current Detection</div>
            <div className={`text-xs px-2 py-1 rounded ${
              isLiveConnected 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {isLiveConnected ? '🟢 Live' : '🟡 Demo'}
            </div>
          </div>
          <div className="flex items-center justify-between mb-2">
            <div className={`flex items-center space-x-2 text-lg font-bold ${getStateColor()}`}>
              <span>{getStateIcon()}</span>
              <span>{getStateLabel()}</span>
            </div>
          </div>
          
          {/* Brightness Bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Brightness</span>
              <span>{(currentBrightness * 100).toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-gray-800 rounded overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 via-yellow-500 to-orange-500 transition-all duration-300"
                style={{ width: `${currentBrightness * 100}%` }}
              />
            </div>
          </div>

          {/* IR Indicator */}
          {isIR && (
            <div className="mt-2 flex items-center space-x-2 text-xs text-purple-400">
              <span className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
              <span>Infrared Mode Active</span>
            </div>
          )}

          {/* Detection Indicators */}
          <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
            <div className={`text-center py-1 rounded ${currentState === 'day' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-gray-800 text-gray-600'}`}>
              ☀️ Day
            </div>
            <div className={`text-center py-1 rounded ${currentState === 'dusk' ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-800 text-gray-600'}`}>
              🌅 Dusk
            </div>
            <div className={`text-center py-1 rounded ${currentState === 'night' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-800 text-gray-600'}`}>
              🌙 Night
            </div>
          </div>
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🌓</span>
            <div className="font-bold text-sm">Day/Night/IR Detector</div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
              title="Toggle live preview"
            >
              {showPreview ? '👁️' : '👁️‍🗨️'}
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
        </div>

        {showConfig && (
          <div className="space-y-3 mt-3 pt-3 border-t border-gray-800">
            {/* Detection Mode */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Detection Mode</label>
              <select
                value={detectionMode}
                onChange={(e) => {
                  setDetectionMode(e.target.value)
                  handleUpdate('detectionMode', e.target.value)
                }}
                className="w-full bg-gray-800 text-sm px-2 py-1 rounded border border-gray-700 focus:border-yellow-500 focus:outline-none"
              >
                {detectionModes.map(mode => (
                  <option key={mode.value} value={mode.value}>
                    {mode.icon} {mode.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Brightness Threshold */}
            {(detectionMode === 'all' || detectionMode === 'brightness') && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Day/Night Threshold: {(brightnessThreshold * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={brightnessThreshold}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value)
                    setBrightnessThreshold(val)
                    handleUpdate('brightnessThreshold', val)
                  }}
                  className="w-full"
                />
                <div className="text-xs text-gray-600 mt-1">
                  Below {(brightnessThreshold * 100).toFixed(0)}% = Night
                </div>
              </div>
            )}

            {/* IR Threshold */}
            {(detectionMode === 'all' || detectionMode === 'ir') && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  IR Detection Sensitivity: {(irThreshold * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.95"
                  step="0.05"
                  value={irThreshold}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value)
                    setIrThreshold(val)
                    handleUpdate('irThreshold', val)
                  }}
                  className="w-full"
                />
                <div className="text-xs text-gray-600 mt-1">
                  Detects low color saturation (monochrome IR images)
                </div>
              </div>
            )}

            {/* Check Interval */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Check Interval: {checkInterval}s
              </label>
              <input
                type="range"
                min="1"
                max="60"
                step="1"
                value={checkInterval}
                onChange={(e) => {
                  const val = parseInt(e.target.value)
                  setCheckInterval(val)
                  handleUpdate('checkInterval', val)
                }}
                className="w-full"
              />
            </div>

            {/* Sensitivity */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Overall Sensitivity: {(sensitivity * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.05"
                value={sensitivity}
                onChange={(e) => {
                  const val = parseFloat(e.target.value)
                  setSensitivity(val)
                  handleUpdate('sensitivity', val)
                }}
                className="w-full"
              />
            </div>

            {/* Enable Actions */}
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-400">Trigger Actions on Change</label>
              <input
                type="checkbox"
                checked={enableActions}
                onChange={(e) => {
                  setEnableActions(e.target.checked)
                  handleUpdate('enableActions', e.target.checked)
                }}
                className="rounded"
              />
            </div>

            {/* Info */}
            <div className="text-xs text-gray-500 pt-2 border-t border-gray-800">
              <div className="font-bold mb-1">Detection Methods:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Brightness: Analyzes average luminance</li>
                <li>IR Mode: Detects low color saturation</li>
                <li>Time-based: Uses sunset/sunrise times</li>
              </ul>
              <div className="mt-2">
                Outputs: state (day/dusk/night), brightness (0-1), is_ir (bool)
              </div>
            </div>
          </div>
        )}

        {!showConfig && (
          <div className="text-xs space-y-1">
            <div className="text-gray-500">Mode: {detectionModes.find(m => m.value === detectionMode)?.label}</div>
            <div className="text-gray-500">Check every: {checkInterval}s</div>
            <div className="text-gray-500">Actions: {enableActions ? 'Enabled' : 'Disabled'}</div>
            <div className="text-gray-400 text-xs mt-2">
              Click 👁️ to toggle live preview
            </div>
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-yellow-500"
        id="output"
      />
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-purple-500"
        id="ir-output"
        style={{ top: '60%' }}
      />
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-blue-500"
        id="night-output"
        style={{ top: '80%' }}
      />
    </div>
  )
})

