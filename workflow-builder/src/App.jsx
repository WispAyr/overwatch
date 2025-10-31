import { useState, useCallback, useEffect } from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  Panel,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { endpoints } from './config'

import CameraNode from './nodes/CameraNode'
import VideoInputNode from './nodes/VideoInputNode'
import YouTubeNode from './nodes/YouTubeNode'
import ModelNode from './nodes/ModelNode'
import ZoneNode from './nodes/ZoneNode'
import ActionNode from './nodes/ActionNode'
import DataPreviewNode from './nodes/DataPreviewNode'
import VideoPreviewNode from './nodes/VideoPreviewNode'
import DebugNode from './nodes/DebugNode'
import LinkInNode from './nodes/LinkInNode'
import LinkOutNode from './nodes/LinkOutNode'
import LinkCallNode from './nodes/LinkCallNode'
import CatchNode from './nodes/CatchNode'
import ConfigNode from './nodes/ConfigNode'
import AudioExtractorNode from './nodes/AudioExtractorNode'
import AudioAINode from './nodes/AudioAINode'
import AudioVUNode from './nodes/AudioVUNode'
import DayNightDetectorNode from './nodes/DayNightDetectorNode'
import DroneInputNode from './nodes/DroneInputNode'
import DroneFilterNode from './nodes/DroneFilterNode'
import DroneMapNode from './nodes/DroneMapNode'
import DroneActionNode from './nodes/DroneActionNode'
import DroneAnalyticsNode from './nodes/DroneAnalyticsNode'
import ParkingViolationNode from './nodes/ParkingViolationNode'
import DetectionFilterNode from './nodes/DetectionFilterNode'
import UniFiCameraDiscoveryNode from './nodes/UniFiCameraDiscoveryNode'
import UniFiProtectEventNode from './nodes/UniFiProtectEventNode'
import UniFiAddCameraNode from './nodes/UniFiAddCameraNode'
import AnimatedEdge from './edges/AnimatedEdge'
import DataEdge from './edges/DataEdge'
import Sidebar from './components/Sidebar'
import WorkflowControls from './components/WorkflowControls'
import BackgroundControl from './components/BackgroundControl'
import CustomBackground from './components/CustomBackground'
import DisplayModeToggle from './components/DisplayModeToggle'
import ConfigPanel from './components/ConfigPanel'
import ExamplesPanel from './components/ExamplesPanel'

const nodeTypes = {
  camera: CameraNode,
  videoInput: VideoInputNode,
  youtube: YouTubeNode,
  model: ModelNode,
  zone: ZoneNode,
  detectionFilter: DetectionFilterNode,
  action: ActionNode,
  dataPreview: DataPreviewNode,
  videoPreview: VideoPreviewNode,
  debug: DebugNode,
  linkIn: LinkInNode,
  linkOut: LinkOutNode,
  linkCall: LinkCallNode,
  catch: CatchNode,
  config: ConfigNode,
  audioExtractor: AudioExtractorNode,
  audioAI: AudioAINode,
  audioVU: AudioVUNode,
  dayNightDetector: DayNightDetectorNode,
  droneInput: DroneInputNode,
  droneFilter: DroneFilterNode,
  droneMap: DroneMapNode,
  droneAction: DroneActionNode,
  droneAnalytics: DroneAnalyticsNode,
  parkingViolation: ParkingViolationNode,
  unifiCameraDiscovery: UniFiCameraDiscoveryNode,
  unifiProtectEvent: UniFiProtectEventNode,
  unifiAddCamera: UniFiAddCameraNode,
}

const edgeTypes = {
  animated: AnimatedEdge,
  data: DataEdge,
}

const initialNodes = [
  {
    id: 'welcome',
    type: 'default',
    position: { x: 250, y: 100 },
    data: { 
      label: (
        <div className="text-center">
          <div className="font-bold mb-2">🎬 Overwatch Workflow Builder</div>
          <div className="text-xs text-gray-400">
            Drag components from the left to build your workflow
          </div>
        </div>
      ) 
    },
  },
]

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [cameras, setCameras] = useState([])
  const [models, setModels] = useState([])
  const [actions, setActions] = useState([])
  const [filters, setFilters] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)
  const [backgroundConfig, setBackgroundConfig] = useState({ type: 'none' })
  const [isDisplayMode, setIsDisplayMode] = useState(false)
  const [showConfigPanel, setShowConfigPanel] = useState(false)
  const [showExamplesPanel, setShowExamplesPanel] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [workflowId, setWorkflowId] = useState(null)

  // Cleanup workflows on page unload
  useEffect(() => {
    const cleanup = async () => {
      if (workflowId) {
        try {
          await fetch(endpoints.workflowStop(workflowId), {
            method: 'POST',
            keepalive: true  // Important for unload events
          })
        } catch (err) {
          console.error('Cleanup error:', err)
        }
      }
    }

    window.addEventListener('beforeunload', cleanup)
    return () => {
      window.removeEventListener('beforeunload', cleanup)
      cleanup()  // Also cleanup when component unmounts
    }
  }, [workflowId])

  useEffect(() => {
    console.log('🔄 DATA LOADING USEEFFECT TRIGGERED')
    
    // Load cameras from API
    fetch(endpoints.cameras)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setCameras(data.cameras || [])
      })
      .catch(err => {
        console.error('Failed to load cameras:', err)
        setCameras([])
      })

    // Load available models dynamically from backend
    fetch(endpoints.workflowComponents.models)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setModels(data.models || [])
      })
      .catch(err => {
        console.error('Failed to load models:', err)
        setModels([])
      })

    // Load available actions
    fetch(endpoints.workflowComponents.actions)
      .then(res => res.json())
      .then(data => {
        setActions(data.actions || [])
      })
      .catch(err => {
        console.error('Failed to load actions:', err)
        setActions([])
      })

    // Load available filters
    fetch(endpoints.workflowComponents.filters)
      .then(res => res.json())
      .then(data => {
        setFilters(data.filters || [])
      })
      .catch(err => {
        console.error('Failed to load filters:', err)
        setFilters([])
      })
  }, [])

  const onConnect = useCallback(
    (params) => {
      // Determine edge type and data based on connection
      const sourceNode = nodes.find(n => n.id === params.source)
      const targetNode = nodes.find(n => n.id === params.target)
      
      let edgeType = 'animated'
      let edgeData = {}
      
      // Set edge type and data based on source/target types
      if (sourceNode?.type === 'camera' || sourceNode?.type === 'videoInput' || sourceNode?.type === 'youtube') {
        edgeType = 'animated'
        edgeData = { type: 'video' }
      } else if (sourceNode?.type === 'model') {
        // Check if connecting to data preview/debug (use data edge) or action (use animated)
        if (targetNode?.type === 'dataPreview' || targetNode?.type === 'debug') {
          edgeType = 'data'
          edgeData = { type: 'raw_data' }
        } else {
          edgeType = 'animated'
          edgeData = { type: 'detections' }
        }
      } else if (sourceNode?.type === 'zone') {
        edgeType = 'animated'
        edgeData = { type: 'zones' }
      }
      
      // Debug node can accept any connection
      if (targetNode?.type === 'debug') {
        edgeType = 'data'
        edgeData = { type: 'debug' }
      }
      
      // Config nodes connect to models/actions to provide configuration
      if (sourceNode?.type === 'config') {
        edgeType = 'data'
        edgeData = { type: 'config' }
      }
      
      // Audio extractor connects with audio type
      if (sourceNode?.type === 'audioExtractor') {
        edgeType = 'data'
        edgeData = { type: 'audio' }
      }
      
      // Audio AI connects with transcript/sound data
      if (sourceNode?.type === 'audioAI') {
        edgeType = 'data'
        edgeData = { type: 'audio_data' }
      }
      
      const newEdge = {
        ...params,
        type: edgeType,
        data: edgeData,
        animated: true,
        style: { 
          strokeWidth: 2,
          stroke: edgeData.type === 'audio' ? '#ec4899' : edgeData.type === 'audio_data' ? '#a855f7' : undefined
        },
      }
      
      setEdges((eds) => addEdge(newEdge, eds))
    },
    [setEdges, nodes],
  )

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()

      const type = event.dataTransfer.getData('application/reactflow')
      const nodeData = JSON.parse(event.dataTransfer.getData('application/json') || '{}')

      if (typeof type === 'undefined' || !type) {
        return
      }

      const position = {
        x: event.clientX - 250,
        y: event.clientY - 40,
      }

      const newNode = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: { ...nodeData },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes],
  )

  const saveWorkflow = useCallback(() => {
    const workflow = {
      nodes,
      edges,
      site: selectedSite,
      timestamp: new Date().toISOString(),
    }
    
    // Save to backend
    console.log('Saving workflow:', workflow)
    
    // Download as JSON for now
    const blob = new Blob([JSON.stringify(workflow, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-${selectedSite || 'default'}-${Date.now()}.json`
    a.click()
  }, [nodes, edges, selectedSite])

  const loadWorkflow = useCallback((workflowData) => {
    setNodes(workflowData.nodes || [])
    setEdges(workflowData.edges || [])
    setSelectedSite(workflowData.site)
  }, [setNodes, setEdges])

  const clearWorkflow = useCallback(() => {
    setNodes([])
    setEdges([])
  }, [setNodes, setEdges])

  const applyExample = useCallback((nodeType, nodeData) => {
    // Add config node from example at a nice position
    const newNode = {
      id: `${nodeType}-${Date.now()}`,
      type: nodeType,
      position: { x: 400, y: 200 },
      data: nodeData
    }
    
    setNodes((nds) => nds.concat(newNode))
  }, [setNodes])

  const executeWorkflow = useCallback(async () => {
    console.log('🎬 Execute button clicked!', { isExecuting, nodeCount: nodes.length, edgeCount: edges.length })
    
    if (isExecuting) {
      // Stop workflow
      console.log('⏹️ Stopping workflow:', workflowId)
      try {
        if (workflowId) {
          const stopUrl = endpoints.workflowStop(workflowId)
          console.log('Calling stop endpoint:', stopUrl)
          await fetch(stopUrl, {
            method: 'POST'
          })
        }
        setIsExecuting(false)
        setWorkflowId(null)
        console.log('✅ Workflow stopped')
      } catch (err) {
        console.error('❌ Failed to stop workflow:', err)
        alert(`Failed to stop workflow: ${err.message}`)
      }
    } else {
      // Start workflow
      const wfId = `workflow-${Date.now()}`
      console.log('▶️ Starting workflow:', wfId)
      console.log('Nodes:', nodes.length, 'Edges:', edges.length)
      
      try {
        setWorkflowId(wfId)
        
        const executeUrl = endpoints.workflowExecuteRealtime
        console.log('Calling execute endpoint:', executeUrl)
        
        const payload = {
          id: wfId,
          name: 'Test Workflow',
          nodes: nodes,
          edges: edges
        }
        console.log('Payload:', JSON.stringify(payload, null, 2))
        
        const response = await fetch(executeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })
        
        console.log('Response status:', response.status)
        const responseText = await response.text()
        console.log('Response body:', responseText)
        
        if (response.ok) {
          setIsExecuting(true)
          console.log('✅ Workflow execution started successfully')
          alert('Workflow started! Check the Debug Console for messages.')
        } else {
          console.error('❌ Failed to start workflow:', responseText)
          alert(`Failed to start workflow: ${responseText}`)
        }
      } catch (err) {
        console.error('❌ Failed to execute workflow:', err)
        alert(`Error executing workflow: ${err.message}\n\nCheck browser console for details.`)
        setWorkflowId(null)
      }
    }
  }, [isExecuting, workflowId, nodes, edges])

  // Handle viewport changes for map syncing
  const onMove = useCallback((event, viewport) => {
    if (backgroundConfig.type === 'map' && backgroundConfig.syncWithViewport) {
      // Convert viewport to map coordinates (simplified)
      // In production, you'd do proper coordinate transformation
      setBackgroundConfig(prev => ({
        ...prev,
        // Viewport follows are handled by React Flow
      }))
    }
  }, [backgroundConfig])

  return (
    <div className="h-screen w-screen flex bg-gray-950">
      {/* Sidebar - Hidden in Display Mode */}
      {!isDisplayMode && (
        <Sidebar 
          cameras={cameras} 
          models={models}
          actions={actions}
          filters={filters}
        />
      )}

      {/* Main Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onMove={onMove}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          className="bg-gray-950"
          nodesDraggable={!isDisplayMode}
          nodesConnectable={!isDisplayMode}
          elementsSelectable={!isDisplayMode}
        >
          {/* Custom Background (Image or Map) */}
          <CustomBackground config={backgroundConfig} />
          
          {/* Controls - Hidden in Display Mode */}
          {!isDisplayMode && (
            <>
              <Controls className="bg-gray-900 border-gray-700" />
              <MiniMap 
                className="bg-gray-900 border-gray-700" 
                nodeColor="#374151"
                maskColor="rgba(0, 0, 0, 0.6)"
              />
            </>
          )}
          
          <Background 
            variant={backgroundConfig.type === 'none' ? BackgroundVariant.Dots : BackgroundVariant.Lines} 
            gap={12} 
            size={1} 
            color={backgroundConfig.type === 'none' ? '#374151' : '#1f2937'}
            style={{ opacity: backgroundConfig.type === 'none' ? 1 : 0.3 }}
          />
          
          {/* Header - Always visible but different in display mode */}
          <Panel position="top-left" className={`${isDisplayMode ? 'bg-black/80' : 'bg-gray-900/50'} backdrop-blur-sm border border-gray-800 rounded-lg p-4`}>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
              OVERWATCH
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              {isDisplayMode ? 'Live Monitoring' : 'Workflow Builder'}
            </p>
          </Panel>

          {/* Controls Panel - Hidden in Display Mode */}
          <Panel position="top-right" className="space-y-2">
            <a
              href="http://localhost:7002/#workflows"
              target="_blank"
              className="px-3 py-2 bg-gray-900 border border-blue-700 rounded-lg hover:border-blue-500 transition-colors text-sm flex items-center space-x-2 w-full"
              title="View Dashboard"
            >
              <span>📊</span>
              <span className="text-gray-300">Dashboard</span>
            </a>
            
            <DisplayModeToggle 
              isDisplayMode={isDisplayMode}
              onToggle={() => setIsDisplayMode(!isDisplayMode)}
            />
            {!isDisplayMode && (
              <>
                <button
                  onClick={() => setShowConfigPanel(true)}
                  className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg hover:border-gray-500 transition-colors text-sm flex items-center space-x-2 w-full"
                  title="Configuration"
                >
                  <span>⚙️</span>
                  <span className="text-gray-300">Configuration</span>
                </button>
                <button
                  onClick={() => setShowExamplesPanel(true)}
                  className="px-3 py-2 bg-gray-900 border border-yellow-700 rounded-lg hover:border-yellow-500 transition-colors text-sm flex items-center space-x-2 w-full"
                  title="Configuration Examples"
                >
                  <span>📚</span>
                  <span className="text-gray-300">Examples</span>
                </button>
                <BackgroundControl 
                  onBackgroundChange={setBackgroundConfig}
                  currentBackground={backgroundConfig}
                />
                <WorkflowControls 
                  onSave={saveWorkflow}
                  onClear={clearWorkflow}
                  onExecute={executeWorkflow}
                  nodeCount={nodes.length}
                  edgeCount={edges.length}
                  isExecuting={isExecuting}
                />
              </>
            )}
          </Panel>
        </ReactFlow>
      </div>
      
      {/* Configuration Panel */}
      <ConfigPanel 
        isOpen={showConfigPanel}
        onClose={() => setShowConfigPanel(false)}
      />
      
      {/* Examples Panel */}
      <ExamplesPanel
        isOpen={showExamplesPanel}
        onClose={() => setShowExamplesPanel(false)}
        onApplyExample={applyExample}
      />
    </div>
  )
}

export default App

