import { memo, useState, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

// COCO dataset class names (80 classes)
const COCO_CLASSES = [
  { id: 0, name: 'person', category: 'People' },
  { id: 1, name: 'bicycle', category: 'Vehicles' },
  { id: 2, name: 'car', category: 'Vehicles' },
  { id: 3, name: 'motorcycle', category: 'Vehicles' },
  { id: 4, name: 'airplane', category: 'Vehicles' },
  { id: 5, name: 'bus', category: 'Vehicles' },
  { id: 6, name: 'train', category: 'Vehicles' },
  { id: 7, name: 'truck', category: 'Vehicles' },
  { id: 8, name: 'boat', category: 'Vehicles' },
  { id: 9, name: 'traffic light', category: 'Outdoor' },
  { id: 10, name: 'fire hydrant', category: 'Outdoor' },
  { id: 11, name: 'stop sign', category: 'Outdoor' },
  { id: 12, name: 'parking meter', category: 'Outdoor' },
  { id: 13, name: 'bench', category: 'Outdoor' },
  { id: 14, name: 'bird', category: 'Animals' },
  { id: 15, name: 'cat', category: 'Animals' },
  { id: 16, name: 'dog', category: 'Animals' },
  { id: 17, name: 'horse', category: 'Animals' },
  { id: 18, name: 'sheep', category: 'Animals' },
  { id: 19, name: 'cow', category: 'Animals' },
  { id: 20, name: 'elephant', category: 'Animals' },
  { id: 21, name: 'bear', category: 'Animals' },
  { id: 22, name: 'zebra', category: 'Animals' },
  { id: 23, name: 'giraffe', category: 'Animals' },
  { id: 24, name: 'backpack', category: 'Accessories' },
  { id: 25, name: 'umbrella', category: 'Accessories' },
  { id: 26, name: 'handbag', category: 'Accessories' },
  { id: 27, name: 'tie', category: 'Accessories' },
  { id: 28, name: 'suitcase', category: 'Accessories' },
  { id: 39, name: 'bottle', category: 'Kitchen' },
  { id: 40, name: 'wine glass', category: 'Kitchen' },
  { id: 41, name: 'cup', category: 'Kitchen' },
  { id: 42, name: 'fork', category: 'Kitchen' },
  { id: 43, name: 'knife', category: 'Kitchen' },
  { id: 44, name: 'spoon', category: 'Kitchen' },
  { id: 56, name: 'chair', category: 'Furniture' },
  { id: 57, name: 'couch', category: 'Furniture' },
  { id: 58, name: 'potted plant', category: 'Furniture' },
  { id: 59, name: 'bed', category: 'Furniture' },
  { id: 60, name: 'dining table', category: 'Furniture' },
  { id: 61, name: 'toilet', category: 'Furniture' },
  { id: 62, name: 'tv', category: 'Electronics' },
  { id: 63, name: 'laptop', category: 'Electronics' },
  { id: 64, name: 'mouse', category: 'Electronics' },
  { id: 65, name: 'remote', category: 'Electronics' },
  { id: 66, name: 'keyboard', category: 'Electronics' },
  { id: 67, name: 'cell phone', category: 'Electronics' },
];

// Common presets for quick selection
const CLASS_PRESETS = {
  'people': { label: '👥 People Only', classes: [0] },
  'vehicles': { label: '🚗 All Vehicles', classes: [2, 3, 5, 6, 7, 8] },
  'people-vehicles': { label: '🚶🚗 People & Vehicles', classes: [0, 1, 2, 3, 5, 7] },
  'animals': { label: '🐕 Animals', classes: [14, 15, 16, 17, 18, 19, 20, 21, 22, 23] },
  'bags': { label: '🎒 Bags & Luggage', classes: [24, 26, 28] },
  'all': { label: '🌐 All Classes', classes: [] }
};

export default memo(({ data, id }) => {
  const { setNodes } = useReactFlow()
  const [confidence, setConfidence] = useState(data.confidence || 0.7)
  const [selectedClasses, setSelectedClasses] = useState(data.classes || [])
  const [showConfig, setShowConfig] = useState(false)
  const [showClassSelector, setShowClassSelector] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [detectionCount, setDetectionCount] = useState(0)
  const [lastDetection, setLastDetection] = useState(null)
  const [fps, setFps] = useState(data.fps || 10)
  const [batchSize, setBatchSize] = useState(data.batchSize || 1)
  const [iou, setIou] = useState(data.iou || 0.45)
  const [searchTerm, setSearchTerm] = useState('')
  
  // X-RAY Mode settings
  const [enableXRay, setEnableXRay] = useState(data.enableXRay || false)
  const [xrayMode, setXrayMode] = useState(data.xrayMode || 'boxes')
  const [schematicMode, setSchematicMode] = useState(data.schematicMode || false)
  const [colorScheme, setColorScheme] = useState(data.colorScheme || 'default')
  const [xrayMaxFps, setXrayMaxFps] = useState(data.xrayMaxFps || 30)
  const [showXRayConfig, setShowXRayConfig] = useState(false)

  // Update node data in ReactFlow whenever config changes
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return {
            ...node,
            data: {
              ...node.data,
              confidence,
              classes: selectedClasses,
              fps,
              batchSize,
              iou,
              enableXRay,
              xrayMode,
              schematicMode,
              colorScheme,
              xrayMaxFps
            }
          }
        }
        return node
      })
    )
  }, [confidence, selectedClasses, fps, batchSize, iou, enableXRay, xrayMode, schematicMode, colorScheme, xrayMaxFps, id, setNodes]);

  const speedBadge = {
    'fast': 'bg-green-500/20 text-green-400',
    'medium': 'bg-yellow-500/20 text-yellow-400',
    'slow': 'bg-red-500/20 text-red-400'
  }

  const toggleClass = (classId) => {
    setSelectedClasses(prev => {
      if (prev.includes(classId)) {
        return prev.filter(id => id !== classId);
      } else {
        return [...prev, classId];
      }
    });
  };

  const applyPreset = (presetKey) => {
    const preset = CLASS_PRESETS[presetKey];
    setSelectedClasses(preset.classes);
  };

  // Filter classes by search term
  const filteredClasses = COCO_CLASSES.filter(cls =>
    cls.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cls.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group classes by category
  const groupedClasses = filteredClasses.reduce((acc, cls) => {
    if (!acc[cls.category]) acc[cls.category] = [];
    acc[cls.category].push(cls);
    return acc;
  }, {});

  const getSelectedClassNames = () => {
    if (selectedClasses.length === 0) return 'All classes';
    if (selectedClasses.length > 3) return `${selectedClasses.length} classes selected`;
    return selectedClasses.map(id => 
      COCO_CLASSES.find(c => c.id === id)?.name || id
    ).join(', ');
  };

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-green-500 bg-gray-900 min-w-[240px] max-w-[300px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-green-500"
        id="video-input"
      />
      
      {/* Detection Preview */}
      {showPreview && (
        <div className="bg-gray-950 border-b border-gray-800 p-3">
          <div className="text-xs text-gray-400 mb-2">Live Detections</div>
          <div className="flex items-center justify-between">
            <div className="text-sm font-mono text-green-400">
              {detectionCount} detected
            </div>
            <div className="text-xs text-gray-500">
              conf: {(confidence * 100).toFixed(0)}%+
            </div>
          </div>
          {lastDetection && (
            <div className="mt-2 text-xs text-gray-500">
              Last: {lastDetection}
            </div>
          )}
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🤖</span>
            <div className="font-bold text-sm">{data.label || data.modelName}</div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
              title="Toggle detection preview"
            >
              📊
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-gray-500">{data.modelId}</span>
          {data.speed && (
            <span className={`px-2 py-0.5 rounded ${speedBadge[data.speed]}`}>
              {data.speed}
            </span>
          )}
        </div>

        {showConfig && (
          <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
            {/* Confidence Threshold */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Confidence Threshold: {(confidence * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>Low (0%)</span>
                <span>High (100%)</span>
              </div>
            </div>
            
            {/* Class Selection */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs text-gray-400">Detect Classes</label>
                <button
                  onClick={() => setShowClassSelector(!showClassSelector)}
                  className="text-[10px] px-2 py-0.5 bg-blue-600 hover:bg-blue-700 rounded text-white"
                >
                  {showClassSelector ? 'Close' : 'Select'}
                </button>
              </div>
              <div className="text-xs text-gray-300 bg-gray-800 px-2 py-1.5 rounded border border-gray-700">
                {getSelectedClassNames()}
              </div>
              
              {/* Class Selector Panel */}
              {showClassSelector && (
                <div className="mt-2 p-2 bg-gray-800 rounded border border-gray-700 max-h-[300px] overflow-y-auto">
                  {/* Presets */}
                  <div className="mb-2 pb-2 border-b border-gray-700">
                    <div className="text-[10px] text-gray-400 mb-1">Quick Presets:</div>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(CLASS_PRESETS).map(([key, preset]) => (
                        <button
                          key={key}
                          onClick={() => applyPreset(key)}
                          className="text-[10px] px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Search */}
                  <input
                    type="text"
                    placeholder="Search classes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-2 py-1 mb-2 bg-gray-900 border border-gray-700 rounded text-xs text-white"
                  />
                  
                  {/* Class List by Category */}
                  <div className="space-y-2">
                    {Object.entries(groupedClasses).map(([category, classes]) => (
                      <div key={category}>
                        <div className="text-[10px] text-gray-500 font-semibold mb-1">
                          {category}
                        </div>
                        <div className="space-y-0.5">
                          {classes.map(cls => (
                            <label
                              key={cls.id}
                              className="flex items-center space-x-2 text-xs cursor-pointer hover:bg-gray-700 px-1 py-0.5 rounded"
                            >
                              <input
                                type="checkbox"
                                checked={selectedClasses.includes(cls.id)}
                                onChange={() => toggleClass(cls.id)}
                                className="w-3 h-3"
                              />
                              <span className="text-gray-300">{cls.name}</span>
                              <span className="text-gray-600 text-[10px]">#{cls.id}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Selection Summary */}
                  <div className="mt-2 pt-2 border-t border-gray-700 text-[10px] text-gray-400">
                    {selectedClasses.length === 0 ? (
                      'All classes enabled'
                    ) : (
                      `${selectedClasses.length} class${selectedClasses.length !== 1 ? 'es' : ''} selected`
                    )}
                  </div>
                </div>
              )}
            </div>
            
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
            
            {/* X-RAY Mode */}
            <div className="p-3 bg-purple-900/20 border border-purple-700 rounded">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-purple-300 font-semibold flex items-center gap-1">
                  🔍 X-RAY Mode
                </label>
                <button
                  onClick={() => setEnableXRay(!enableXRay)}
                  className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                    enableXRay 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-gray-700 text-gray-400'
                  }`}
                >
                  {enableXRay ? 'ON' : 'OFF'}
                </button>
              </div>
              
              {enableXRay && (
                <div className="space-y-2">
                  <button
                    onClick={() => setShowXRayConfig(!showXRayConfig)}
                    className="w-full text-xs px-2 py-1 bg-purple-800 hover:bg-purple-700 rounded text-white"
                  >
                    {showXRayConfig ? 'Hide Settings' : 'Show Settings'}
                  </button>
                  
                  {showXRayConfig && (
                    <div className="space-y-2 pt-2 border-t border-purple-800">
                      {/* Mode Selection */}
                      <div>
                        <label className="text-[10px] text-gray-400 block mb-1">Visualization Mode</label>
                        <select
                          value={xrayMode}
                          onChange={(e) => setXrayMode(e.target.value)}
                          className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                        >
                          <option value="boxes">📦 Bounding Boxes</option>
                          <option value="schematic">📐 Schematic (No Image)</option>
                          <option value="heatmap">🔥 Heatmap</option>
                          <option value="both">📦🔥 Boxes + Heatmap</option>
                        </select>
                      </div>
                      
                      {/* Color Scheme */}
                      <div>
                        <label className="text-[10px] text-gray-400 block mb-1">Color Scheme</label>
                        <select
                          value={colorScheme}
                          onChange={(e) => setColorScheme(e.target.value)}
                          className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                        >
                          <option value="default">🎨 Default</option>
                          <option value="confidence">📊 Confidence Gradient</option>
                          <option value="class_specific">🏷️ Class-Specific</option>
                          <option value="thermal">🌡️ Thermal</option>
                          <option value="neon">💡 Neon</option>
                        </select>
                      </div>
                      
                      {/* Max FPS Slider */}
                      <div>
                        <label className="text-[10px] text-gray-400 block mb-1">
                          Max X-RAY FPS: {xrayMaxFps}
                        </label>
                        <input
                          type="range"
                          min="10"
                          max="60"
                          step="5"
                          value={xrayMaxFps}
                          onChange={(e) => setXrayMaxFps(parseInt(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-[9px] text-gray-600">
                          <span>10 (CPU)</span>
                          <span>30 (Balanced)</span>
                          <span>60 (GPU)</span>
                        </div>
                        <div className="text-[9px] text-gray-500 mt-1">
                          ⚡ Higher FPS needs GPU for smooth performance
                        </div>
                      </div>
                      
                      {/* Schematic Toggle */}
                      <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
                        <label className="text-[10px] text-gray-300">Schematic Mode</label>
                        <button
                          onClick={() => setSchematicMode(!schematicMode)}
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            schematicMode 
                              ? 'bg-purple-600 text-white' 
                              : 'bg-gray-700 text-gray-400'
                          }`}
                        >
                          {schematicMode ? 'ON' : 'OFF'}
                        </button>
                      </div>
                      
                      <div className="text-[9px] text-gray-500 p-2 bg-gray-800 rounded">
                        💡 Connect an X-RAY View node to see live annotated frames
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {/* Batch Size (for performance) */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Batch Size: {batchSize}
              </label>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value))}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                <option value="1">1 (Real-time)</option>
                <option value="2">2</option>
                <option value="4">4</option>
                <option value="8">8</option>
                <option value="16">16 (Batch)</option>
              </select>
              <div className="text-[10px] text-gray-600 mt-1">
                Higher batch = better throughput, more latency
              </div>
            </div>
            
            {/* IOU Threshold (for NMS) */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                IOU Threshold: {iou.toFixed(2)}
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={iou}
                onChange={(e) => setIou(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="text-[10px] text-gray-600">
                Non-max suppression overlap threshold
              </div>
            </div>
            
            {/* Advanced Options Toggle */}
            <details className="text-xs">
              <summary className="text-gray-400 cursor-pointer hover:text-gray-300">
                Advanced Options
              </summary>
              <div className="mt-2 space-y-2 pl-2 border-l-2 border-gray-700">
                {/* Max Detections */}
                <div>
                  <label className="text-[10px] text-gray-400 block mb-1">Max Detections</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    defaultValue={data.maxDetections || 300}
                    onChange={(e) => {
                      if (data.onChange) {
                        data.onChange({ maxDetections: parseInt(e.target.value) });
                      }
                    }}
                    className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                  />
                </div>
                
                {/* Agnostic NMS */}
                <div>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      defaultChecked={data.agnostic !== false}
                      onChange={(e) => {
                        if (data.onChange) {
                          data.onChange({ agnostic: e.target.checked });
                        }
                      }}
                      className="w-3 h-3"
                    />
                    <span className="text-[10px] text-gray-300">Class-agnostic NMS</span>
                  </label>
                </div>
                
                {/* Half Precision */}
                <div>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      defaultChecked={data.half || false}
                      onChange={(e) => {
                        if (data.onChange) {
                          data.onChange({ half: e.target.checked });
                        }
                      }}
                      className="w-3 h-3"
                    />
                    <span className="text-[10px] text-gray-300">Half precision (FP16)</span>
                  </label>
                  <div className="text-[9px] text-gray-600 ml-5">
                    Faster inference, slightly lower accuracy
                  </div>
                </div>
              </div>
            </details>
            
            {/* Summary */}
            <div className="pt-2 border-t border-gray-700">
              <div className="text-[10px] text-gray-500 space-y-0.5">
                <div>🎯 Confidence: {(confidence * 100).toFixed(0)}%</div>
                <div>📊 Classes: {selectedClasses.length === 0 ? 'All (80)' : selectedClasses.length}</div>
                <div>⚡ Speed: {fps} fps × batch {batchSize}</div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-green-500"
        id="detections-output"
      />
      
        {/* Bottom handle for detection data */}
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 bg-gray-500"
          id="data-output"
          style={{ background: '#6b7280' }}
        />
      </div>
    </NodeWrapper>
  )
})
