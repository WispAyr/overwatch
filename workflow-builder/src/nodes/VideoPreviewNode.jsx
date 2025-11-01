import { memo, useState, useEffect, useRef } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper'
import { wsBaseUrl } from '../config'

export default memo(({ data, id }) => {
  const { getEdges } = useReactFlow()
  const [frame, setFrame] = useState(null)
  const [stats, setStats] = useState({ fps: 0, detections: 0, latency: 0 })
  const [showStats, setShowStats] = useState(true)
  const canvasRef = useRef(null)
  
  // Check if node has connections
  const hasConnections = () => {
    const edges = getEdges()
    return edges.some(edge => edge.target === id)
  }
  
  // Get connected node IDs
  const getConnectedNodeIds = () => {
    const edges = getEdges()
    return edges
      .filter(edge => edge.target === id)
      .map(edge => edge.source)
  }
  
  // WebSocket connection for live frames
  useEffect(() => {
    if (!hasConnections()) return
    
    const ws = new WebSocket(`${wsBaseUrl}/api/ws`)
    
    ws.onopen = () => {
      console.log(`VideoPreview ${id}: WebSocket connected`)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        console.log(`X-RAY View ${id}: Received message`, data.type, data.node_id)
        
        // Handle X-RAY frame data meant for THIS node
        if (data.type === 'xray_frame' && data.node_id === id && data.frame_data) {
          console.log(`X-RAY View ${id}: Processing X-RAY frame!`)
          setFrame(data.frame_data)  // Base64 encoded image
          setStats({
            fps: data.fps || 0,
            detections: data.detections_count || 0,
            latency: data.processing_time_ms || 0
          })
        }
      } catch (error) {
        console.error('Error parsing frame data:', error)
      }
    }
    
    return () => ws.close()
  }, [id])
  
  // Draw frame to canvas
  useEffect(() => {
    if (!frame || !canvasRef.current) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      ctx.drawImage(img, 0, 0)
    }
    
    img.src = `data:image/jpeg;base64,${frame}`
  }, [frame])
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-purple-500 bg-gray-900 min-w-[320px] max-w-[640px]">
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-purple-500"
        />
        
        {/* Header */}
        <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xl">🔍</span>
              <div className="font-bold text-sm text-purple-400">X-RAY View (WebSocket)</div>
            </div>
            <div className="flex items-center space-x-2">
              {stats.fps > 0 && (
                <div className="text-xs bg-green-900/50 text-green-300 px-2 py-1 rounded font-mono">
                  {stats.fps} fps
                </div>
              )}
              <button
                onClick={() => setShowStats(!showStats)}
                className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
                title="Toggle stats"
              >
                📊
              </button>
            </div>
          </div>
        </div>
        
        {/* Video Canvas */}
        <div className="relative bg-black">
          {!hasConnections() ? (
            <div className="text-gray-600 text-center py-16">
              <div className="text-3xl mb-3">🔍</div>
              <div className="text-sm">Connect an AI model</div>
              <div className="text-xs text-gray-700 mt-2">
                Enable X-RAY mode in model settings
              </div>
            </div>
          ) : !frame ? (
            <div className="text-xs text-gray-600 text-center py-16">
              <div className="animate-pulse">Waiting for frames...</div>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              className="w-full h-auto"
            />
          )}
          
          {/* Stats Overlay */}
          {showStats && frame && (
            <div className="absolute bottom-2 left-2 right-2 bg-black/70 rounded p-2">
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-gray-400">FPS</div>
                  <div className="text-green-400 font-mono">{stats.fps}</div>
                </div>
                <div>
                  <div className="text-gray-400">Detections</div>
                  <div className="text-cyan-400 font-mono">{stats.detections}</div>
                </div>
                <div>
                  <div className="text-gray-400">Latency</div>
                  <div className="text-yellow-400 font-mono">{stats.latency}ms</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </NodeWrapper>
  )
})

