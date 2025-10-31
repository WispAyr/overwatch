import { memo, useState, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import { wsBaseUrl } from '../config'
import NodeWrapper from '../components/NodeWrapper'

export default memo(({ data, id }) => {
  const [showDebug, setShowDebug] = useState(true)
  const [messages, setMessages] = useState([])
  const [messageCount, setMessageCount] = useState(0)
  const [maxMessages, setMaxMessages] = useState(10)
  const [filterMode, setFilterMode] = useState('connected') // 'connected' | 'all'
  const [showSystemMessages, setShowSystemMessages] = useState(false)
  const { getEdges, getNodes } = useReactFlow()

  // Check if this debug node has any incoming connections
  const hasConnections = () => {
    const edges = getEdges()
    return edges.some(edge => edge.target === id)
  }

  // Get IDs of nodes directly connected to this debug node
  const getConnectedNodeIds = () => {
    const edges = getEdges()
    return edges
      .filter(edge => edge.target === id)
      .map(edge => edge.source)
  }

  // Check if a message is from a connected node
  const isFromConnectedNode = (msg) => {
    if (filterMode === 'all') return true
    const connectedIds = getConnectedNodeIds()
    return connectedIds.includes(msg.node_id)
  }

  // Check if message is a system message
  const isSystemMessage = (msgType) => {
    const systemTypes = ['node_started', 'node_completed', 'node_processing', 'status_update', 'metrics_update']
    return systemTypes.includes(msgType)
  }

  // Connect to WebSocket for live debug data
  // Always connect - even if no connections yet (they might be added dynamically)
  useEffect(() => {
    console.log(`DebugNode ${id}: Setting up WebSocket connection...`)
    
    // Check if we have any edges targeting this node
    const edges = getEdges()
    const hasConn = edges.some(edge => edge.target === id)
    console.log(`DebugNode ${id}: Found ${edges.filter(e => e.target === id).length} incoming connections`)
    
    // Always connect to WebSocket regardless - filtering happens server-side
    // This ensures we don't miss messages if connections are added dynamically

    // Connect to WebSocket using configured base URL (points to backend on port 8000)
    const wsUrl = `${wsBaseUrl}/api/ws`
    console.log(`DebugNode ${id}: Attempting WebSocket connection to ${wsUrl}`)
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log(`DebugNode ${id}: WebSocket connected`)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        console.log(`🔔 DebugNode ${id}: RAW WebSocket message received:`, event.data)
        console.log(`🔔 DebugNode ${id}: Parsed data:`, data)
        console.log(`🔔 DebugNode ${id}: Message type: ${data.type}, Node ID: ${data.node_id}, My ID: ${id}`)
        console.log(`🔔 DebugNode ${id}: Match check: type=${data.type === 'debug_message'}, nodeId=${data.node_id === id}`)
        
        // Process messages
        if (data.type === 'debug_message' || data.type === 'detection_data' || data.type === 'node_error' || data.type === 'status_update') {
          console.log(`✅ DebugNode ${id}: PROCESSING message!`, data)
          
          const debugMsg = {
            timestamp: data.timestamp,
            source: data.workflow_id || 'workflow',
            type: data.type,
            message: data.message || JSON.stringify(data, null, 2),
            detections: data.detections || [],
            node_id: data.node_id,
            raw: data
          }
          
          setMessages(prev => {
            const newMessages = [debugMsg, ...prev].slice(0, maxMessages)
            console.log(`✅ DebugNode ${id}: Updated messages array, new count: ${newMessages.length}`)
            return newMessages
          })
          setMessageCount(prev => prev + 1)
        } else {
          console.log(`⏭️ DebugNode ${id}: Skipping message - type: ${data.type}`)
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error, event.data)
      }
    }
    
    ws.onerror = (error) => {
      console.error(`DebugNode ${id}: WebSocket error`, error)
    }
    
    ws.onclose = () => {
      console.log(`DebugNode ${id}: WebSocket disconnected`)
    }
    
    return () => {
      console.log(`DebugNode ${id}: Cleaning up WebSocket connection`)
      ws.close()
    }
  }, [maxMessages, id])  // Removed getEdges from dependencies to prevent reconnect loops

  const clearMessages = () => {
    setMessages([])
    setMessageCount(0)
  }

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-cyan-500 bg-gray-900 min-w-[300px] max-w-[400px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-cyan-500"
        style={{ top: '50%' }}
      />
      
      {/* Header */}
      <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🐛</span>
            <div className="font-bold text-sm text-cyan-400">Debug Console</div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-xs bg-cyan-900/50 text-cyan-300 px-2 py-1 rounded">
              {messageCount} msgs
            </div>
            <button
              onClick={() => setShowDebug(!showDebug)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
              title="Toggle debug view"
            >
              {showDebug ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={clearMessages}
              className="text-xs px-2 py-1 bg-red-900/50 text-red-300 rounded hover:bg-red-900/70"
            >
              Clear
            </button>
            <select
              value={maxMessages}
              onChange={(e) => setMaxMessages(parseInt(e.target.value))}
              className="text-xs px-2 py-1 bg-gray-800 border border-gray-700 rounded"
            >
              <option value="5">5 msgs</option>
              <option value="10">10 msgs</option>
              <option value="20">20 msgs</option>
              <option value="50">50 msgs</option>
            </select>
          </div>
          
          {/* Filter toggles */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilterMode(filterMode === 'connected' ? 'all' : 'connected')}
              className={`text-[10px] px-2 py-1 rounded transition-colors ${
                filterMode === 'connected'
                  ? 'bg-cyan-900/50 text-cyan-300 border border-cyan-700'
                  : 'bg-gray-800 text-gray-400 border border-gray-700'
              }`}
              title={filterMode === 'connected' ? 'Showing connected nodes only' : 'Showing all nodes'}
            >
              {filterMode === 'connected' ? '🔗 Connected Only' : '🌐 All Nodes'}
            </button>
            
            <button
              onClick={() => setShowSystemMessages(!showSystemMessages)}
              className={`text-[10px] px-2 py-1 rounded transition-colors ${
                showSystemMessages
                  ? 'bg-purple-900/50 text-purple-300 border border-purple-700'
                  : 'bg-gray-800 text-gray-400 border border-gray-700'
              }`}
              title={showSystemMessages ? 'Showing system messages' : 'Hiding system messages'}
            >
              {showSystemMessages ? '⚙️ System: ON' : '⚙️ System: OFF'}
            </button>
          </div>
        </div>
      </div>

      {/* Debug Output */}
      {showDebug && (
        <div className="p-3 bg-black font-mono text-xs max-h-[400px] overflow-y-auto">
          {!hasConnections() ? (
            <div className="text-gray-600 text-center py-8">
              <div className="text-2xl mb-2">🔌</div>
              <div className="text-xs">Connect a node to start debugging</div>
              <div className="text-[10px] text-gray-700 mt-2">
                Wire any node's output to this debug console
              </div>
            </div>
          ) : (() => {
            // Filter messages based on settings
            const filteredMessages = messages.filter(msg => {
              // Filter by connection
              if (!isFromConnectedNode(msg)) return false
              
              // Filter by system messages
              if (!showSystemMessages && isSystemMessage(msg.type)) return false
              
              return true
            })
            
            return filteredMessages.length === 0 ? (
              <div className="text-gray-600 text-center py-4">
                <div className="text-xs">Waiting for data...</div>
                <div className="text-[10px] text-gray-700 mt-1">
                  {filterMode === 'connected' ? 'Filtered: Connected nodes only' : 'Listening to all nodes'}
                </div>
                <div className="text-[10px] text-gray-700">
                  {!showSystemMessages && '(System messages hidden)'}
                </div>
                <div className="text-[10px] text-cyan-600 mt-2">
                  Total msgs: {messages.length} | Filtered: {filteredMessages.length}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredMessages.map((msg, idx) => {
                  const isSystem = isSystemMessage(msg.type)
                  return (
                    <div 
                      key={idx} 
                      className={`border-l-2 pl-2 pb-2 ${
                        isSystem ? 'border-purple-500' : 'border-cyan-500'
                      }`}
                    >
                      <div className="text-gray-500 text-[10px] mb-1 flex justify-between items-center">
                        <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                        <div className="flex items-center space-x-2">
                          {isSystem && <span className="text-purple-500 text-[9px]">⚙️</span>}
                          <span className={isSystem ? 'text-purple-600' : 'text-cyan-600'}>
                            ← {msg.node_id?.substring(0, 12) || msg.source}
                          </span>
                        </div>
                      </div>
                      <div className={`text-[11px] whitespace-pre-wrap break-words ${
                        isSystem ? 'text-purple-400' : 'text-cyan-400'
                      }`}>
                        {msg.message}
                      </div>
                      {msg.detections && msg.detections.length > 0 && (
                        <div className="mt-1 text-[10px] text-gray-500">
                          Detections: {msg.detections.length}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })()}
        </div>
      )}

        {/* Stats footer */}
        {!showDebug && (
          <div className="px-4 py-2 text-xs text-gray-500 text-center">
            Click 👁️ to view debug output
          </div>
        )}
      </div>
    </NodeWrapper>
  )
})

