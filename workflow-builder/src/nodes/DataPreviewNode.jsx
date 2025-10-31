import { memo, useState, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';
import { wsBaseUrl } from '../config'

/**
 * Data Preview Node
 * Shows live detection data in structured format
 */
export default memo(({ data, id }) => {
  const [detectionData, setDetectionData] = useState(null)
  const [expanded, setExpanded] = useState(true)
  const [stats, setStats] = useState({ total: 0, fps: 0 })
  const { getEdges } = useReactFlow()

  // Check if this node has any incoming connections
  const hasConnections = () => {
    const edges = getEdges()
    return edges.some(edge => edge.target === id)
  }

  // Get source node IDs
  const getConnectedNodeIds = () => {
    const edges = getEdges()
    return edges
      .filter(edge => edge.target === id)
      .map(edge => edge.source)
  }

  // Get source node info
  const getSourceInfo = () => {
    const edges = getEdges().filter(edge => edge.target === id)
    if (edges.length === 0) return null
    return {
      nodeId: edges[0].source,
      type: edges[0].data?.type || 'unknown'
    }
  }

  // Check if message is from a connected node
  const isFromConnectedNode = (msg) => {
    const connectedIds = getConnectedNodeIds()
    return connectedIds.includes(msg.node_id)
  }

  // Connect to WebSocket for live detection data
  useEffect(() => {
    if (!hasConnections()) {
      setDetectionData(null)
      return
    }

    // Connect to WebSocket using configured base URL (points to backend on port 8000)
    const wsUrl = `${wsBaseUrl}/api/ws`
    console.log(`DataPreviewNode ${id}: Attempting WebSocket connection to ${wsUrl}`)
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log(`DataPreviewNode ${id}: WebSocket connected`)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        console.log(`DataPreviewNode ${id}: Received WebSocket message`, data)
        
        // Process detection data from connected nodes OR data meant for this node
        const isRelevant = (data.type === 'detection_data' || data.type === 'node_completed') && 
                          (isFromConnectedNode(data) || data.node_id === id)
        
        if (isRelevant) {
          console.log(`DataPreviewNode ${id}: Processing detection data`, data)
          
          // Extract detections from the data
          const detections = data.detections || data.data?.detections || []
          const count = data.count || data.data?.detections_count || detections.length || 0
          
          setDetectionData({
            timestamp: data.timestamp || new Date().toISOString(),
            source: data.node_id || getSourceInfo()?.nodeId || 'unknown',
            frame_id: data.frame_id || data.data?.frame_id || 0,
            resolution: data.resolution || data.data?.frame_shape || { width: 1920, height: 1080 },
            detections: detections,
            count: count,
            processing_time_ms: data.processing_time_ms || data.data?.processing_time_ms || 0,
            zone_violations: data.zone_violations || 0
          })
          
          setStats(prev => ({
            total: prev.total + count,
            fps: data.fps || prev.fps
          }))
        } else {
          console.log(`DataPreviewNode ${id}: Skipping message - type: ${data.type}, node_id: ${data.node_id}`)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error(`DataPreviewNode ${id}: WebSocket error`, error)
    }
    
    ws.onclose = () => {
      console.log(`DataPreviewNode ${id}: WebSocket disconnected`)
    }
    
    return () => {
      console.log(`DataPreviewNode ${id}: Cleaning up WebSocket`)
      ws.close()
    }
  }, [id])  // Removed getEdges from dependencies to prevent reconnect loops

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-indigo-500 bg-gray-900 min-w-[320px] max-w-[450px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-indigo-500"
      />
      
      {/* Header */}
      <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">📊</span>
            <div className="font-bold text-sm text-indigo-400">Detection Data</div>
          </div>
          <div className="flex items-center space-x-2">
            {hasConnections() && stats.fps > 0 && (
              <div className="text-xs bg-green-900/50 text-green-300 px-2 py-1 rounded font-mono">
                {stats.fps} fps
              </div>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
            >
              {expanded ? '▼' : '▶'}
            </button>
          </div>
        </div>
        {hasConnections() && stats.total > 0 && (
          <div className="text-xs text-gray-500">
            Total detected: {stats.total}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3 max-h-[500px] overflow-y-auto">
        {!hasConnections() ? (
          <div className="text-gray-600 text-center py-8">
            <div className="text-2xl mb-2">🔌</div>
            <div className="text-xs">Connect a detection node</div>
            <div className="text-[10px] text-gray-700 mt-2">
              Wire a model or filter output here
            </div>
          </div>
        ) : !detectionData ? (
          <div className="text-xs text-gray-600 text-center py-4">
            <div className="animate-pulse">Waiting for detections...</div>
            <div className="text-[10px] text-gray-700 mt-1">
              Connected to {getSourceInfo()?.nodeId}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Summary */}
            <div className="bg-gray-950 rounded p-3 border border-gray-800">
              <div className="flex justify-between items-center mb-2">
                <div className="text-xs text-gray-400">
                  Frame #{detectionData.frame_id}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(detectionData.timestamp).toLocaleTimeString()}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Objects:</span>
                  <span className="text-white ml-2 font-bold">{detectionData.count}</span>
                </div>
                <div>
                  <span className="text-gray-500">Process:</span>
                  <span className="text-green-400 ml-2">{detectionData.processing_time_ms}ms</span>
                </div>
                <div>
                  <span className="text-gray-500">Resolution:</span>
                  <span className="text-gray-400 ml-2">{detectionData.resolution.width}x{detectionData.resolution.height}</span>
                </div>
                {detectionData.zone_violations > 0 && (
                  <div>
                    <span className="text-gray-500">Violations:</span>
                    <span className="text-red-400 ml-2 font-bold">{detectionData.zone_violations}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Detections */}
            {expanded && detectionData.detections.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs text-gray-400 font-semibold">Detected Objects:</div>
                {detectionData.detections.map((det, idx) => (
                  <div key={idx} className="bg-gray-950 rounded p-2 border border-gray-800">
                    <div className="flex justify-between items-start mb-1">
                      <div className="text-sm font-semibold text-indigo-400">
                        {det.class}
                      </div>
                      <div className="text-xs bg-green-900/50 text-green-300 px-2 py-0.5 rounded">
                        {(det.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 space-y-0.5 font-mono">
                      <div>BBox: [{det.bbox.x}, {det.bbox.y}, {det.bbox.width}, {det.bbox.height}]</div>
                      <div className="flex justify-between">
                        <span>Track ID: {det.track_id}</span>
                        {det.speed && <span className="text-yellow-500">Speed: {det.speed} km/h</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {expanded && detectionData.detections.length === 0 && (
              <div className="text-xs text-gray-600 text-center py-2">
                No objects detected in this frame
              </div>
            )}

            {/* Raw JSON (collapsed by default) */}
            {expanded && (
              <details className="text-xs">
                <summary className="text-gray-500 cursor-pointer hover:text-gray-400 mb-2">
                  View Raw JSON
                </summary>
                <pre className="bg-black rounded p-2 text-indigo-400 font-mono text-[10px] overflow-x-auto border border-gray-800">
                  {JSON.stringify(detectionData, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}
      </div>
      </div>
    </NodeWrapper>
  )
})

