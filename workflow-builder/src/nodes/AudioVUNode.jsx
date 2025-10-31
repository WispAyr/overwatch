import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [displayMode, setDisplayMode] = useState(data.displayMode || 'vu_meter')
  const [sensitivity, setSensitivity] = useState(data.sensitivity || 0.5)
  const [frequencyBands, setFrequencyBands] = useState(data.frequencyBands || 8)
  const [peakHold, setPeakHold] = useState(data.peakHold !== false)
  const [colorScheme, setColorScheme] = useState(data.colorScheme || 'gradient')
  const [enableThreshold, setEnableThreshold] = useState(data.enableThreshold || false)
  const [thresholdLevel, setThresholdLevel] = useState(data.thresholdLevel || 75)
  const [thresholdMode, setThresholdMode] = useState(data.thresholdMode || 'continuous')
  const [hysteresis, setHysteresis] = useState(data.hysteresis || 5)
  const [showConfig, setShowConfig] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [currentLevel, setCurrentLevel] = useState(0)
  const [currentSpectrum, setCurrentSpectrum] = useState([])
  const [isTriggered, setIsTriggered] = useState(false)
  const [isLiveConnected, setIsLiveConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('demo')

  // Connect to WebSocket for live audio data
  useEffect(() => {
    if (!showPreview) return
    
    // Try to connect to WebSocket for live data
    const wsUrl = 'ws://localhost:8000/ws'
    let ws = null
    let fallbackInterval = null
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('AudioVU WebSocket connected')
        setConnectionStatus('connecting...')
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          // Check if this message is for our node
          if (message.type === 'audioVU_update' && message.node_id === id) {
            setCurrentLevel(message.data.level_db)
            setCurrentSpectrum(message.data.spectrum)
            setIsTriggered(message.data.triggered)
            setIsLiveConnected(true)
            setConnectionStatus('live')
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }
      
      ws.onerror = () => {
        console.log('WebSocket error, falling back to demo mode')
        setIsLiveConnected(false)
        setConnectionStatus('demo (backend not running)')
      }
      
      ws.onclose = () => {
        setIsLiveConnected(false)
        setConnectionStatus('demo (backend not running)')
      }
    } catch (err) {
      console.log('Failed to connect WebSocket:', err)
      setIsLiveConnected(false)
      setConnectionStatus('demo (backend not running)')
    }
    
    // Fallback: Use demo data if WebSocket doesn't connect
    setTimeout(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        fallbackInterval = setInterval(() => {
          const level = Math.random() * 100
          setCurrentLevel(level)
          
          // Check threshold trigger
          if (enableThreshold) {
            if (level >= thresholdLevel) {
              setIsTriggered(true)
            } else if (level < (thresholdLevel - hysteresis)) {
              setIsTriggered(false)
            }
          }
          
          // Generate random spectrum
          const spectrum = Array.from({ length: frequencyBands }, () => Math.random() * 100)
          setCurrentSpectrum(spectrum)
        }, 100)
      }
    }, 1000)
    
    return () => {
      if (ws) ws.close()
      if (fallbackInterval) clearInterval(fallbackInterval)
    }
  }, [showPreview, id, frequencyBands, enableThreshold, thresholdLevel, hysteresis])

  const handleUpdate = (field, value) => {
    if (data.onChange) {
      data.onChange(id, { 
        ...data, 
        [field]: value 
      })
    }
  }

  const displayModes = [
    { value: 'vu_meter', label: 'VU Meter', icon: '📊' },
    { value: 'spectrum', label: 'Frequency Spectrum', icon: '📈' },
    { value: 'waveform', label: 'Waveform', icon: '〰️' },
    { value: 'spectrogram', label: 'Spectrogram', icon: '🎨' },
    { value: 'vu_and_spectrum', label: 'VU + Spectrum', icon: '📊📈' },
  ]

  const colorSchemes = [
    { value: 'gradient', label: 'Green → Yellow → Red' },
    { value: 'blue', label: 'Blue Gradient' },
    { value: 'purple', label: 'Purple Gradient' },
    { value: 'rainbow', label: 'Rainbow' },
    { value: 'monochrome', label: 'Monochrome' },
  ]

  const getLevelColor = (level) => {
    if (level < 33) return 'bg-green-500'
    if (level < 66) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const renderVUMeter = () => (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Level</span>
        <span>{currentLevel.toFixed(0)} dB</span>
        {enableThreshold && isTriggered && (
          <span className="text-red-400 font-bold animate-pulse">TRIGGERED</span>
        )}
      </div>
      <div className="relative h-3 bg-gray-800 rounded overflow-hidden">
        <div 
          className={`h-full transition-all duration-100 ${getLevelColor(currentLevel)}`}
          style={{ width: `${currentLevel}%` }}
        />
        {/* Threshold Line */}
        {enableThreshold && (
          <div 
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
            style={{ left: `${thresholdLevel}%` }}
            title={`Threshold: ${thresholdLevel}dB`}
          >
            <div className="absolute -top-1 -left-1 w-2 h-2 bg-red-500 rounded-full" />
            <div className="absolute -bottom-1 -left-1 w-2 h-2 bg-red-500 rounded-full" />
          </div>
        )}
      </div>
    </div>
  )

  const renderSpectrum = () => (
    <div className="space-y-1">
      <div className="text-xs text-gray-500">Frequency Spectrum</div>
      <div className="flex items-end justify-between space-x-0.5 h-12">
        {currentSpectrum.map((level, i) => (
          <div 
            key={i}
            className={`flex-1 ${getLevelColor(level)} transition-all duration-100 rounded-t`}
            style={{ height: `${level}%` }}
          />
        ))}
      </div>
    </div>
  )

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-purple-500 bg-gray-900 min-w-[280px] max-w-[320px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-purple-500"
        id="audio-input"
      />
      
      {/* Live Preview */}
      {showPreview && (
        <div className="bg-gray-950 border-b border-gray-800 p-3">
          {/* Connection Status Badge */}
          <div className="mb-2 flex items-center justify-between">
            <div className={`text-xs px-2 py-1 rounded ${
              isLiveConnected 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {isLiveConnected ? '🟢 Live Data' : '🟡 Demo Mode'}
            </div>
            <div className="text-xs text-gray-500">
              {connectionStatus}
            </div>
          </div>
          {displayMode === 'vu_meter' && renderVUMeter()}
          {displayMode === 'spectrum' && renderSpectrum()}
          {displayMode === 'vu_and_spectrum' && (
            <>
              {renderVUMeter()}
              <div className="mt-2">
                {renderSpectrum()}
              </div>
            </>
          )}
          {(displayMode === 'waveform' || displayMode === 'spectrogram') && (
            <div className="text-xs text-center text-gray-500 py-4">
              {displayMode === 'waveform' ? '〰️ Waveform' : '🎨 Spectrogram'} visualization
            </div>
          )}
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xl">📻</span>
            <div className="font-bold text-sm">Audio VU/Frequency</div>
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
            {/* Display Mode */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Display Mode</label>
              <select
                value={displayMode}
                onChange={(e) => {
                  setDisplayMode(e.target.value)
                  handleUpdate('displayMode', e.target.value)
                }}
                className="w-full bg-gray-800 text-sm px-2 py-1 rounded border border-gray-700 focus:border-purple-500 focus:outline-none"
              >
                {displayModes.map(mode => (
                  <option key={mode.value} value={mode.value}>
                    {mode.icon} {mode.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Sensitivity */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Sensitivity: {(sensitivity * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
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

            {/* Frequency Bands (for spectrum modes) */}
            {(displayMode === 'spectrum' || displayMode === 'vu_and_spectrum' || displayMode === 'spectrogram') && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Frequency Bands: {frequencyBands}
                </label>
                <input
                  type="range"
                  min="4"
                  max="32"
                  step="1"
                  value={frequencyBands}
                  onChange={(e) => {
                    const val = parseInt(e.target.value)
                    setFrequencyBands(val)
                    handleUpdate('frequencyBands', val)
                  }}
                  className="w-full"
                />
              </div>
            )}

            {/* Color Scheme */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Color Scheme</label>
              <select
                value={colorScheme}
                onChange={(e) => {
                  setColorScheme(e.target.value)
                  handleUpdate('colorScheme', e.target.value)
                }}
                className="w-full bg-gray-800 text-sm px-2 py-1 rounded border border-gray-700 focus:border-purple-500 focus:outline-none"
              >
                {colorSchemes.map(scheme => (
                  <option key={scheme.value} value={scheme.value}>
                    {scheme.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Peak Hold */}
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-400">Peak Hold</label>
              <input
                type="checkbox"
                checked={peakHold}
                onChange={(e) => {
                  setPeakHold(e.target.checked)
                  handleUpdate('peakHold', e.target.checked)
                }}
                className="rounded"
              />
            </div>

            {/* Threshold Trigger Section */}
            <div className="pt-3 border-t border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-400 font-bold">Threshold Trigger</label>
                <input
                  type="checkbox"
                  checked={enableThreshold}
                  onChange={(e) => {
                    setEnableThreshold(e.target.checked)
                    handleUpdate('enableThreshold', e.target.checked)
                  }}
                  className="rounded"
                />
              </div>

              {enableThreshold && (
                <div className="space-y-3 mt-2">
                  {/* Threshold Level */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Threshold Level: {thresholdLevel} dB
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="100"
                      step="1"
                      value={thresholdLevel}
                      onChange={(e) => {
                        const val = parseInt(e.target.value)
                        setThresholdLevel(val)
                        handleUpdate('thresholdLevel', val)
                      }}
                      className="w-full"
                    />
                    <div className="text-xs text-gray-600 mt-1">
                      Trigger when level exceeds {thresholdLevel} dB
                    </div>
                  </div>

                  {/* Trigger Mode */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Trigger Mode</label>
                    <select
                      value={thresholdMode}
                      onChange={(e) => {
                        setThresholdMode(e.target.value)
                        handleUpdate('thresholdMode', e.target.value)
                      }}
                      className="w-full bg-gray-800 text-sm px-2 py-1 rounded border border-gray-700 focus:border-purple-500 focus:outline-none"
                    >
                      <option value="continuous">Continuous (while above threshold)</option>
                      <option value="edge">Edge Trigger (once on crossing)</option>
                      <option value="pulse">Pulse (brief trigger on crossing)</option>
                    </select>
                  </div>

                  {/* Hysteresis */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Hysteresis: {hysteresis} dB
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      step="1"
                      value={hysteresis}
                      onChange={(e) => {
                        const val = parseInt(e.target.value)
                        setHysteresis(val)
                        handleUpdate('hysteresis', val)
                      }}
                      className="w-full"
                    />
                    <div className="text-xs text-gray-600 mt-1">
                      Prevents rapid on/off triggering. Trigger off at {thresholdLevel - hysteresis} dB
                    </div>
                  </div>

                  {/* Trigger Status */}
                  {showPreview && (
                    <div className={`text-xs p-2 rounded ${isTriggered ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-500'}`}>
                      <div className="flex items-center justify-between">
                        <span>Trigger Output:</span>
                        <span className="font-bold">
                          {isTriggered ? '🔴 ACTIVE' : '⚪ Inactive'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Info */}
            <div className="text-xs text-gray-500 pt-2 border-t border-gray-800">
              <div className="font-bold text-green-400 mb-1">✅ Ready for Live Audio</div>
              <div className="mb-2">
                Will automatically switch to live mode when:
              </div>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                <li>Workflow is running (click Execute)</li>
                <li>Backend is processing audio</li>
                <li>WebSocket connection established</li>
              </ul>
              <div className="mt-2">
                Shows <span className="text-yellow-400">demo data</span> when backend is not running.
              </div>
              {enableThreshold && (
                <div className="mt-2 text-purple-400">
                  ⚡ Trigger output activates downstream nodes when threshold is exceeded.
                </div>
              )}
            </div>
          </div>
        )}

        {!showConfig && (
          <div className="text-xs space-y-1">
            <div className="text-gray-500">Mode: {displayModes.find(m => m.value === displayMode)?.label}</div>
            {(displayMode === 'spectrum' || displayMode === 'vu_and_spectrum' || displayMode === 'spectrogram') && (
              <div className="text-gray-500">Bands: {frequencyBands}</div>
            )}
            <div className="text-gray-500">Sensitivity: {(sensitivity * 100).toFixed(0)}%</div>
            {enableThreshold && (
              <div className="text-purple-400 font-bold">
                ⚡ Threshold: {thresholdLevel} dB ({thresholdMode})
              </div>
            )}
            <div className="text-gray-400 text-xs mt-2">
              Click 👁️ to toggle live preview
            </div>
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-purple-500"
        id="output"
      />
      
        {/* Threshold Trigger Output */}
        {enableThreshold && (
          <Handle
            type="source"
            position={Position.Right}
            className={`w-3 h-3 transition-all ${isTriggered ? 'bg-red-500 animate-pulse' : 'bg-red-500/50'}`}
            id="trigger-output"
            style={{ top: '75%' }}
            title="Threshold Trigger Output"
          />
        )}
      </div>
    </NodeWrapper>
  )
})

