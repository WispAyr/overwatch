import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import { apiBaseUrl } from '../config'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [showPreview, setShowPreview] = useState(true)
  const [showConfig, setShowConfig] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [useFallback, setUseFallback] = useState(false)
  const [snapshotUrl, setSnapshotUrl] = useState(null)
  const [cameraStatus, setCameraStatus] = useState(null)
  const [isStale, setIsStale] = useState(false)
  
  // Configuration state
  const [fps, setFps] = useState(data.fps || 10)
  const [skipSimilar, setSkipSimilar] = useState(data.skipSimilar || false)
  const [streamQuality, setStreamQuality] = useState(data.streamQuality || 'medium')
  const [enableRecording, setEnableRecording] = useState(data.enableRecording || false)
  const [preBuffer, setPreBuffer] = useState(data.preBuffer || 5)
  
  // Update parent data when config changes
  useEffect(() => {
    if (data.onChange) {
      data.onChange({
        fps,
        skipSimilar,
        streamQuality,
        enableRecording,
        preBuffer
      });
    }
  }, [fps, skipSimilar, streamQuality, enableRecording, preBuffer]);
  
  // Check camera status every 5 seconds
  useEffect(() => {
    if (!data.cameraId) return
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/cameras/${data.cameraId}`)
        if (response.ok) {
          const status = await response.json()
          setCameraStatus(status)
          
          if (status.status.last_frame) {
            const lastFrame = new Date(status.status.last_frame)
            const now = new Date()
            const ageSeconds = (now - lastFrame) / 1000
            setIsStale(ageSeconds > 30)
          } else {
            setIsStale(true)
          }
        }
      } catch (err) {
        console.error(`Camera ${data.cameraId}: Status check failed`, err)
        setIsStale(true)
      }
    }
    
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [data.cameraId])
  
  // Fallback snapshot updater
  useEffect(() => {
    if (!useFallback || !showPreview || !data.cameraId) return
    
    const updateSnapshot = () => {
      const timestamp = Date.now()
      const url = `${apiBaseUrl}/api/video/${data.cameraId}/snapshot?t=${timestamp}`
      setSnapshotUrl(url)
    }
    
    updateSnapshot()
    const interval = setInterval(updateSnapshot, 2000)
    return () => clearInterval(interval)
  }, [useFallback, showPreview, data.cameraId])
  
  const mjpegUrl = data.cameraId ? `${apiBaseUrl}/api/video/${data.cameraId}/mjpeg` : null
  
  const forceRefresh = () => {
    if (useFallback) {
      const timestamp = Date.now()
      setSnapshotUrl(`${apiBaseUrl}/api/video/${data.cameraId}/snapshot?t=${timestamp}`)
    } else {
      setImageError(false)
      setUseFallback(false)
    }
  }

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-blue-500 bg-gray-900 min-w-[240px] max-w-[300px]">
      {/* Live Preview */}
      {showPreview && (
        <div className="relative bg-black rounded-t-lg overflow-hidden" style={{ height: '135px' }}>
          {isStale && (
            <div className="absolute top-0 left-0 right-0 bg-red-600/90 text-white text-xs px-2 py-1 z-10 flex items-center justify-center space-x-1">
              <span>⚠️</span>
              <span>Camera Disconnected</span>
            </div>
          )}
          
          {!useFallback && mjpegUrl ? (
            <img 
              src={mjpegUrl}
              alt={data.cameraName}
              className="w-full h-full object-contain"
              onError={() => {
                console.error(`Camera ${data.cameraId}: MJPEG failed, switching to snapshots`)
                setUseFallback(true)
              }}
            />
          ) : snapshotUrl ? (
            <img 
              key={snapshotUrl}
              src={snapshotUrl}
              alt={data.cameraName}
              className="w-full h-full object-contain"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
              No preview available
            </div>
          )}
          
          {/* Status indicators */}
          <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs text-white flex items-center space-x-1">
            {isStale ? (
              <>
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                <span>OFFLINE</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span>LIVE</span>
              </>
            )}
          </div>
          
          <div className="absolute bottom-2 left-2 px-1 py-0.5 bg-black/70 rounded text-[10px] text-gray-400">
            {useFallback ? 'Snapshot' : 'MJPEG'} 
            {cameraStatus && ` | ${cameraStatus.status.fps?.toFixed(1) || '0'} FPS`}
          </div>
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">📹</span>
            <div className="font-bold text-sm">{data.label || data.cameraName}</div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={forceRefresh}
              className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-white"
              title="Refresh now"
            >
              🔄
            </button>
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs text-gray-400 hover:text-white"
              title="Toggle preview"
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
        
        <div className="text-xs text-gray-400">
          <div>ID: {data.cameraId}</div>
        </div>
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
            {/* Processing FPS */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Processing FPS: {fps}
              </label>
              <input
                type="range"
                min="1"
                max="30"
                value={fps}
                onChange={(e) => setFps(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>1 fps</span>
                <span>30 fps</span>
              </div>
            </div>
            
            {/* Stream Quality */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">Stream Quality</label>
              <select
                value={streamQuality}
                onChange={(e) => setStreamQuality(e.target.value)}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                <option value="high">High (1080p+)</option>
                <option value="medium">Medium (720p)</option>
                <option value="low">Low (480p)</option>
              </select>
              <div className="text-[10px] text-gray-600 mt-1">
                Lower quality = less bandwidth
              </div>
            </div>
            
            {/* Skip Similar Frames */}
            <div>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={skipSimilar}
                  onChange={(e) => setSkipSimilar(e.target.checked)}
                  className="w-3 h-3"
                />
                <span className="text-xs text-gray-300">Skip similar frames</span>
              </label>
              <div className="text-[10px] text-gray-600 ml-5">
                Reduce processing of static scenes
              </div>
            </div>
            
            {/* Recording Options */}
            <div className="pt-2 border-t border-gray-700">
              <label className="flex items-center space-x-2 cursor-pointer mb-2">
                <input
                  type="checkbox"
                  checked={enableRecording}
                  onChange={(e) => setEnableRecording(e.target.checked)}
                  className="w-3 h-3"
                />
                <span className="text-xs text-gray-300">Enable pre-event buffer</span>
              </label>
              
              {enableRecording && (
                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Pre-buffer: {preBuffer}s
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="60"
                    step="5"
                    value={preBuffer}
                    onChange={(e) => setPreBuffer(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-[10px] text-gray-600">
                    Keep last {preBuffer}s in memory for recordings
                  </div>
                </div>
              )}
            </div>
            
            {/* Summary */}
            <div className="pt-2 border-t border-gray-700">
              <div className="text-[10px] text-gray-500 space-y-0.5">
                <div>⚡ {fps} fps @ {streamQuality}</div>
                <div>💾 Buffer: {enableRecording ? `${preBuffer}s` : 'Off'}</div>
                <div>🎞️ Skip similar: {skipSimilar ? 'On' : 'Off'}</div>
              </div>
            </div>
          </div>
        )}
      </div>
      
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-blue-500"
          id="video-output"
        />
      </div>
    </NodeWrapper>
  )
})
