import { memo, useState, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper'

// Common COCO classes from YOLOv8
const COMMON_CLASSES = [
  'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
  'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
  'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
  'backpack', 'umbrella', 'handbag', 'tie', 'suitcase',
  'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
  'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
  'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
  'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
  'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
  'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
  'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

export default memo(({ data, id }) => {
  const { setNodes } = useReactFlow()
  const [showConfig, setShowConfig] = useState(false)
  
  // Filter settings
  const [filterMode, setFilterMode] = useState(data.filterMode || 'count') // 'count', 'class', 'confidence', 'advanced'
  const [minDetections, setMinDetections] = useState(data.minDetections ?? 1)
  const [maxDetections, setMaxDetections] = useState(data.maxDetections ?? 999)
  const [selectedClasses, setSelectedClasses] = useState(data.selectedClasses || [])
  const [classMode, setClassMode] = useState(data.classMode || 'include') // 'include' or 'exclude'
  const [minConfidence, setMinConfidence] = useState(data.minConfidence ?? 0.25)
  const [onlyWhenDetections, setOnlyWhenDetections] = useState(data.onlyWhenDetections ?? true)
  
  // Statistics
  const [stats, setStats] = useState({ total: 0, passed: 0, filtered: 0 })
  
  // Update node data in ReactFlow
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return {
            ...node,
            data: {
              ...node.data,
              filterMode,
              minDetections,
              maxDetections,
              selectedClasses,
              classMode,
              minConfidence,
              onlyWhenDetections
            }
          }
        }
        return node
      })
    )
  }, [filterMode, minDetections, maxDetections, selectedClasses, classMode, minConfidence, onlyWhenDetections, id, setNodes])

  const toggleClass = (className) => {
    setSelectedClasses(prev => 
      prev.includes(className)
        ? prev.filter(c => c !== className)
        : [...prev, className]
    )
  }

  const resetStats = () => {
    setStats({ total: 0, passed: 0, filtered: 0 })
  }

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-yellow-500 bg-gray-900 min-w-[280px] max-w-[350px]">
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-yellow-500"
          id="detections-input"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-yellow-500"
          id="detections-output"
        />
        
        {/* Header */}
        <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-xl">🔍</span>
              <div className="font-bold text-sm text-yellow-400">Detection Filter</div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
          
          {/* Stats */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex space-x-3">
              <span className="text-gray-400">Total: <span className="text-cyan-400">{stats.total}</span></span>
              <span className="text-gray-400">Passed: <span className="text-green-400">{stats.passed}</span></span>
              <span className="text-gray-400">Blocked: <span className="text-red-400">{stats.filtered}</span></span>
            </div>
            <button
              onClick={resetStats}
              className="text-[10px] px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Quick Settings */}
        <div className="px-4 py-3">
          <div className="space-y-3">
            {/* Quick toggle */}
            <div className="flex items-center justify-between p-2 bg-gray-950 rounded border border-gray-800">
              <label className="text-xs text-gray-300 flex-1">Only when detections found</label>
              <button
                onClick={() => setOnlyWhenDetections(!onlyWhenDetections)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  onlyWhenDetections 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {onlyWhenDetections ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Filter Mode Selector */}
            <div>
              <label className="text-xs text-gray-400 block mb-2">Filter Mode</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setFilterMode('count')}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    filterMode === 'count'
                      ? 'bg-yellow-600 text-white border border-yellow-500'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  📊 Count
                </button>
                <button
                  onClick={() => setFilterMode('class')}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    filterMode === 'class'
                      ? 'bg-yellow-600 text-white border border-yellow-500'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  🏷️ Class
                </button>
                <button
                  onClick={() => setFilterMode('confidence')}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    filterMode === 'confidence'
                      ? 'bg-yellow-600 text-white border border-yellow-500'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  💯 Confidence
                </button>
                <button
                  onClick={() => setFilterMode('advanced')}
                  className={`px-3 py-2 rounded text-xs transition-colors ${
                    filterMode === 'advanced'
                      ? 'bg-yellow-600 text-white border border-yellow-500'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  ⚡ Advanced
                </button>
              </div>
            </div>

            {/* Active Filter Summary */}
            {!showConfig && (
              <div className="p-2 bg-gray-950 rounded border border-gray-800 text-xs">
                <div className="text-gray-400 mb-1">Active Filters:</div>
                <div className="space-y-1">
                  {onlyWhenDetections && (
                    <div className="text-green-400">✓ Only when detections found</div>
                  )}
                  {filterMode === 'count' && (
                    <div className="text-yellow-400">✓ Count: {minDetections}-{maxDetections}</div>
                  )}
                  {filterMode === 'class' && selectedClasses.length > 0 && (
                    <div className="text-yellow-400">
                      ✓ Classes ({classMode}): {selectedClasses.slice(0, 3).join(', ')}
                      {selectedClasses.length > 3 && ` +${selectedClasses.length - 3} more`}
                    </div>
                  )}
                  {filterMode === 'confidence' && (
                    <div className="text-yellow-400">✓ Min confidence: {(minConfidence * 100).toFixed(0)}%</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Panel */}
        {showConfig && (
          <div className="px-4 py-3 border-t border-gray-800 space-y-3 max-h-[400px] overflow-y-auto">
            
            {/* Count Filter */}
            {filterMode === 'count' && (
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Min Detections: {minDetections}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={minDetections}
                    onChange={(e) => setMinDetections(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Max Detections: {maxDetections === 999 ? '∞' : maxDetections}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={maxDetections === 999 ? 50 : maxDetections}
                    onChange={(e) => setMaxDetections(parseInt(e.target.value) === 50 ? 999 : parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {/* Class Filter */}
            {filterMode === 'class' && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <button
                    onClick={() => setClassMode('include')}
                    className={`flex-1 px-3 py-2 rounded text-xs ${
                      classMode === 'include'
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-800 text-gray-400'
                    }`}
                  >
                    ✓ Include Only
                  </button>
                  <button
                    onClick={() => setClassMode('exclude')}
                    className={`flex-1 px-3 py-2 rounded text-xs ${
                      classMode === 'exclude'
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-800 text-gray-400'
                    }`}
                  >
                    ✗ Exclude
                  </button>
                </div>

                <div className="text-xs text-gray-400 mb-2">
                  Select classes ({selectedClasses.length} selected):
                </div>
                
                <div className="flex gap-2 mb-2">
                  <button
                    onClick={() => setSelectedClasses(['person', 'car', 'truck', 'bus', 'motorcycle'])}
                    className="flex-1 px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-[10px] hover:bg-blue-900/70"
                  >
                    Vehicles + People
                  </button>
                  <button
                    onClick={() => setSelectedClasses([])}
                    className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-[10px] hover:bg-gray-700"
                  >
                    Clear
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-1 max-h-[200px] overflow-y-auto">
                  {COMMON_CLASSES.slice(0, 30).map((className) => (
                    <button
                      key={className}
                      onClick={() => toggleClass(className)}
                      className={`px-2 py-1 rounded text-[10px] text-left transition-colors ${
                        selectedClasses.includes(className)
                          ? 'bg-yellow-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {selectedClasses.includes(className) ? '✓ ' : '  '}{className}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence Filter */}
            {filterMode === 'confidence' && (
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Minimum Confidence: {(minConfidence * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={minConfidence * 100}
                    onChange={(e) => setMinConfidence(parseInt(e.target.value) / 100)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </div>
                <div className="p-2 bg-blue-900/20 border border-blue-700 rounded text-xs text-blue-300">
                  💡 Higher confidence = fewer false positives
                </div>
              </div>
            )}

            {/* Advanced Filter */}
            {filterMode === 'advanced' && (
              <div className="space-y-3">
                <div className="text-xs text-gray-400">
                  Combine multiple filter types:
                </div>
                
                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Min Confidence: {(minConfidence * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={minConfidence * 100}
                    onChange={(e) => setMinConfidence(parseInt(e.target.value) / 100)}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">
                    Detection Count: {minDetections}-{maxDetections === 999 ? '∞' : maxDetections}
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="0"
                      max="50"
                      value={minDetections}
                      onChange={(e) => setMinDetections(parseInt(e.target.value) || 0)}
                      className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    />
                    <input
                      type="number"
                      min="1"
                      max="999"
                      value={maxDetections}
                      onChange={(e) => setMaxDetections(parseInt(e.target.value) || 999)}
                      className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-2">Quick Class Presets:</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setSelectedClasses(['person'])}
                      className="px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded text-[10px]"
                    >
                      👤 People Only
                    </button>
                    <button
                      onClick={() => setSelectedClasses(['car', 'truck', 'bus'])}
                      className="px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded text-[10px]"
                    >
                      🚗 Vehicles
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="px-4 py-2 bg-gray-950 border-t border-gray-800 text-center">
          <div className="text-[10px] text-gray-600">
            {onlyWhenDetections ? '🟢 Active filtering' : '🔴 Passing all'}
          </div>
        </div>
      </div>
    </NodeWrapper>
  )
})

