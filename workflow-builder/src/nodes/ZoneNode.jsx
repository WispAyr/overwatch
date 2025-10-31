import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

const ZONE_TYPES = [
  { value: 'polygon', label: 'Polygon Zone', icon: '📐', description: 'Multi-point area' },
  { value: 'rectangle', label: 'Rectangle', icon: '▭', description: 'Simple rectangle' },
  { value: 'line', label: 'Line Crossing', icon: '↔️', description: 'Directional line' },
];

const FILTER_TYPES = [
  { value: 'include', label: 'Include', description: 'Only detections inside zone' },
  { value: 'exclude', label: 'Exclude', description: 'Only detections outside zone' },
];

export default memo(({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [polygon, setPolygon] = useState(data.polygon || '[[100,100],[300,100],[300,300],[100,300]]')
  const [zoneLabel, setZoneLabel] = useState(data.label || 'Zone 1')
  const [zoneType, setZoneType] = useState(data.zoneType || 'polygon')
  const [filterType, setFilterType] = useState(data.filterType || 'include')
  const [cooldown, setCooldown] = useState(data.cooldown || 0)
  const [minDwellTime, setMinDwellTime] = useState(data.minDwellTime || 0)
  
  // Update parent data
  useEffect(() => {
    if (data.onChange) {
      data.onChange({
        polygon: zoneType === 'polygon' ? polygon : undefined,
        zoneType,
        label: zoneLabel,
        filterType,
        cooldown,
        minDwellTime
      });
    }
  }, [polygon, zoneType, zoneLabel, filterType, cooldown, minDwellTime]);

  const zoneIcons = {
    polygon: '📐',
    rectangle: '▭',
    line: '↔️',
  }

  // Parse and visualize polygon
  const renderPolygonPreview = () => {
    try {
      const points = JSON.parse(polygon)
      if (!Array.isArray(points) || points.length < 3) return null
      
      const maxX = Math.max(...points.map(p => p[0]))
      const maxY = Math.max(...points.map(p => p[1]))
      const minX = Math.min(...points.map(p => p[0]))
      const minY = Math.min(...points.map(p => p[1]))
      
      const width = maxX - minX
      const height = maxY - minY
      const scale = Math.min(120 / width, 90 / height)
      
      const scaledPoints = points.map(p => 
        `${(p[0] - minX) * scale},${(p[1] - minY) * scale}`
      ).join(' ')
      
      return (
        <svg width="140" height="100" className="bg-gray-950 rounded border border-gray-700">
          <polygon
            points={scaledPoints}
            fill={filterType === 'include' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}
            stroke={filterType === 'include' ? '#22c55e' : '#ef4444'}
            strokeWidth="2"
          />
          {/* Draw point markers */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={(p[0] - minX) * scale}
              cy={(p[1] - minY) * scale}
              r="3"
              fill="#eab308"
            />
          ))}
        </svg>
      )
    } catch {
      return <div className="text-xs text-red-400">Invalid polygon format</div>
    }
  }

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-yellow-500 bg-gray-900 min-w-[260px] max-w-[320px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-yellow-500"
        id="detections-input"
      />
      
      {/* Zone Preview */}
      {showPreview && zoneType === 'polygon' && (
        <div className="p-3 border-b border-gray-800 flex justify-center bg-gray-950">
          {renderPolygonPreview()}
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">{zoneIcons[zoneType] || '📐'}</span>
            <div className="font-bold text-sm text-yellow-400">Zone Filter</div>
          </div>
          <div className="flex items-center space-x-1">
            {zoneType === 'polygon' && (
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
                title="Toggle zone preview"
              >
                👁️
              </button>
            )}
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
        </div>
        
        <div className="text-xs text-gray-500 mb-2">
          {zoneLabel} ({filterType})
        </div>

        {showConfig && (
        <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
          {/* Zone Label */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">Zone Label</label>
            <input
              type="text"
              value={zoneLabel}
              onChange={(e) => setZoneLabel(e.target.value)}
              placeholder="Entry Zone"
              className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
            />
          </div>
          
          {/* Zone Type */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">Zone Type</label>
            <select
              value={zoneType}
              onChange={(e) => setZoneType(e.target.value)}
              className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
            >
              {ZONE_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.icon} {type.label}
                </option>
              ))}
            </select>
            <div className="text-[10px] text-gray-600 mt-1">
              {ZONE_TYPES.find(t => t.value === zoneType)?.description}
            </div>
          </div>
          
          {/* Filter Type */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">Filter Type</label>
            <div className="grid grid-cols-2 gap-2">
              {FILTER_TYPES.map(type => (
                <button
                  key={type.value}
                  onClick={() => setFilterType(type.value)}
                  className={`px-3 py-2 rounded text-xs ${
                    filterType === type.value
                      ? 'bg-yellow-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
            <div className="text-[10px] text-gray-600 mt-1">
              {FILTER_TYPES.find(t => t.value === filterType)?.description}
            </div>
          </div>
          
          {/* Polygon Points */}
          {zoneType === 'polygon' && (
            <div>
              <label className="text-xs text-gray-400 block mb-1">Polygon Points</label>
              <textarea
                value={polygon}
                onChange={(e) => setPolygon(e.target.value)}
                placeholder="[[x1,y1],[x2,y2],[x3,y3],...]"
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white font-mono h-20 resize-none"
              />
              <div className="text-[10px] text-gray-600 mt-1">
                Format: [[x,y],[x,y],...] Min 3 points
              </div>
              {/* Quick presets */}
              <div className="mt-2 flex gap-1">
                <button
                  onClick={() => setPolygon('[[100,100],[300,100],[300,300],[100,300]]')}
                  className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
                >
                  Rectangle
                </button>
                <button
                  onClick={() => setPolygon('[[200,50],[350,200],[200,350],[50,200]]')}
                  className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
                >
                  Diamond
                </button>
                <button
                  onClick={() => setPolygon('[[200,50],[300,150],[250,300],[150,300],[100,150]]')}
                  className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
                >
                  Pentagon
                </button>
              </div>
            </div>
          )}
          
          {/* Cooldown */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Cooldown: {cooldown}s
            </label>
            <input
              type="range"
              min="0"
              max="300"
              step="5"
              value={cooldown}
              onChange={(e) => setCooldown(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="text-[10px] text-gray-600">
              Minimum time between triggers
            </div>
          </div>
          
          {/* Min Dwell Time */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Min Dwell Time: {minDwellTime}s
            </label>
            <input
              type="range"
              min="0"
              max="60"
              value={minDwellTime}
              onChange={(e) => setMinDwellTime(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="text-[10px] text-gray-600">
              Object must stay in zone this long
            </div>
          </div>
          
          {/* Summary */}
          <div className="pt-2 border-t border-gray-700">
            <div className="text-[10px] text-gray-500 space-y-0.5">
              <div>🏷️ {zoneLabel}</div>
              <div>📍 Type: {zoneType}</div>
              <div>🔁 {filterType === 'include' ? 'Inside only' : 'Outside only'}</div>
              {cooldown > 0 && <div>⏱️ Cooldown: {cooldown}s</div>}
              {minDwellTime > 0 && <div>⏲️ Dwell: {minDwellTime}s</div>}
            </div>
          </div>
        </div>
        )}
      </div>
      
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-yellow-500"
          id="filtered-output"
        />
      </div>
    </NodeWrapper>
  )
})
