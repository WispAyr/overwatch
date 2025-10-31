import { memo, useState, useEffect, useRef } from 'react';
import { Handle, Position, useReactFlow } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';
import { apiBaseUrl } from '../config';

/**
 * Parking Violation Node
 * Detects vehicles parked illegally:
 * - Double yellow lines
 * - Restricted zones
 * - No parking zones
 * - Time-based restrictions
 * 
 * Features interactive zone drawing on camera frame
 */
const ParkingViolationNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [showZoneEditor, setShowZoneEditor] = useState(false);
  const [violations, setViolations] = useState([]);
  const [dwellTime, setDwellTime] = useState(data.dwellTime || 30);
  const [restrictionType, setRestrictionType] = useState(data.restrictionType || 'double_yellow');
  const [checkPlates, setCheckPlates] = useState(data.checkPlates !== false);
  const [timeRestricted, setTimeRestricted] = useState(data.timeRestricted || false);
  const [startHour, setStartHour] = useState(data.startHour || 8);
  const [endHour, setEndHour] = useState(data.endHour || 18);
  const [parkingZones, setParkingZones] = useState(data.parkingZones || []);
  const [violationCount, setViolationCount] = useState(0);
  const [frameImage, setFrameImage] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPolygon, setCurrentPolygon] = useState([]);
  const [selectedZoneIndex, setSelectedZoneIndex] = useState(null);
  const canvasRef = useRef(null);
  const { getEdges, getNodes } = useReactFlow();

  const config = data.config || data || {};

  const restrictionTypes = [
    { value: 'double_yellow', label: 'Double Yellow Lines', icon: '🟡', color: 'yellow' },
    { value: 'no_parking', label: 'No Parking Zone', icon: '🚫', color: 'red' },
    { value: 'restricted_zone', label: 'Restricted Zone', icon: '⚠️', color: 'orange' },
    { value: 'loading_only', label: 'Loading Bay Only', icon: '📦', color: 'blue' },
    { value: 'disabled_only', label: 'Disabled Parking Only', icon: '♿', color: 'blue' },
    { value: 'time_restricted', label: 'Time Restricted', icon: '⏰', color: 'purple' },
  ];

  const selectedType = restrictionTypes.find(t => t.value === restrictionType) || restrictionTypes[0];

  // Get camera ID from connected camera node (traverse graph backwards)
  const getConnectedCameraId = () => {
    const edges = getEdges();
    const nodes = getNodes();
    
    // Traverse backwards through the graph to find a camera node
    const findCameraUpstream = (nodeId, visited = new Set()) => {
      if (visited.has(nodeId)) return null; // Prevent cycles
      visited.add(nodeId);
      
      const node = nodes.find(n => n.id === nodeId);
      if (!node) return null;
      
      // If this is a camera node, return its ID
      if (node.type === 'camera') {
        return node.data?.cameraId;
      }
      
      // Otherwise, check all nodes feeding into this one
      const incomingEdges = edges.filter(edge => edge.target === nodeId);
      for (const edge of incomingEdges) {
        const cameraId = findCameraUpstream(edge.source, visited);
        if (cameraId) return cameraId;
      }
      
      return null;
    };
    
    return findCameraUpstream(id);
  };

  // Fetch first frame from connected camera
  const fetchCameraFrame = async () => {
    const cameraId = getConnectedCameraId();
    if (!cameraId) {
      console.log('No camera connected');
      return;
    }

    try {
      // Get snapshot from camera
      const response = await fetch(`${apiBaseUrl}/api/snapshots/${cameraId}/latest`);
      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setFrameImage(imageUrl);
      } else {
        // Fallback: try MJPEG stream
        const mjpegUrl = `${apiBaseUrl}/api/video/${cameraId}/mjpeg`;
        setFrameImage(mjpegUrl);
      }
    } catch (error) {
      console.error('Error fetching camera frame:', error);
    }
  };

  // Load frame when zone editor opens
  useEffect(() => {
    if (showZoneEditor && !frameImage) {
      fetchCameraFrame();
    }
  }, [showZoneEditor]);

  // Draw zones on canvas
  useEffect(() => {
    if (!canvasRef.current || !frameImage) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      // Set canvas size to image size
      canvas.width = img.width;
      canvas.height = img.height;

      // Draw image
      ctx.drawImage(img, 0, 0);

      // Draw existing zones
      parkingZones.forEach((zone, index) => {
        drawZone(ctx, zone, index === selectedZoneIndex);
      });

      // Draw current polygon being drawn
      if (currentPolygon.length > 0) {
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(currentPolygon[0].x, currentPolygon[0].y);
        currentPolygon.forEach(point => {
          ctx.lineTo(point.x, point.y);
        });
        ctx.stroke();

        // Draw points
        currentPolygon.forEach(point => {
          ctx.fillStyle = '#fbbf24';
          ctx.beginPath();
          ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
          ctx.fill();
        });
      }
    };

    img.src = frameImage;
  }, [frameImage, parkingZones, currentPolygon, selectedZoneIndex]);

  const drawZone = (ctx, zone, isSelected) => {
    const colors = {
      double_yellow: '#eab308',
      no_parking: '#ef4444',
      restricted_zone: '#f97316',
      loading_only: '#3b82f6',
      disabled_only: '#3b82f6',
      time_restricted: '#a855f7'
    };

    const color = colors[zone.type] || '#eab308';
    
    ctx.strokeStyle = isSelected ? '#ffffff' : color;
    ctx.fillStyle = isSelected ? `${color}40` : `${color}20`;
    ctx.lineWidth = isSelected ? 4 : 2;

    ctx.beginPath();
    ctx.moveTo(zone.polygon[0].x, zone.polygon[0].y);
    zone.polygon.forEach(point => {
      ctx.lineTo(point.x, point.y);
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw zone label
    const centerX = zone.polygon.reduce((sum, p) => sum + p.x, 0) / zone.polygon.length;
    const centerY = zone.polygon.reduce((sum, p) => sum + p.y, 0) / zone.polygon.length;
    
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px sans-serif';
    ctx.fillText(zone.name || zone.type, centerX - 30, centerY);
  };

  const handleCanvasClick = (e) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Calculate the scale between displayed size and actual canvas size
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    // Get click position relative to displayed canvas
    const displayX = e.clientX - rect.left;
    const displayY = e.clientY - rect.top;
    
    // Scale to actual canvas coordinates
    const x = displayX * scaleX;
    const y = displayY * scaleY;

    console.log('Click:', { displayX, displayY, x, y, scaleX, scaleY, canvasSize: [canvas.width, canvas.height], displaySize: [rect.width, rect.height] });

    // Add point to current polygon
    setCurrentPolygon(prev => [...prev, { x, y }]);
  };

  const finishPolygon = () => {
    if (currentPolygon.length < 3) {
      alert('Need at least 3 points to create a zone');
      return;
    }

    const newZone = {
      id: `zone_${Date.now()}`,
      name: `Zone ${parkingZones.length + 1}`,
      type: restrictionType,
      polygon: currentPolygon,
      dwellTime: dwellTime,
      timeRestricted: timeRestricted,
      startHour: startHour,
      endHour: endHour
    };

    const updatedZones = [...parkingZones, newZone];
    setParkingZones(updatedZones);
    setCurrentPolygon([]);
    
    // Update data
    if (data.onChange) {
      data.onChange({ config: { ...config, parkingZones: updatedZones } });
    }
  };

  const clearCurrentPolygon = () => {
    setCurrentPolygon([]);
  };

  const deleteZone = (index) => {
    const updatedZones = parkingZones.filter((_, i) => i !== index);
    setParkingZones(updatedZones);
    setSelectedZoneIndex(null);
    
    if (data.onChange) {
      data.onChange({ config: { ...config, parkingZones: updatedZones } });
    }
  };

  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };

  const isWithinRestrictedHours = () => {
    if (!timeRestricted) return true;
    const now = new Date();
    const currentHour = now.getHours();
    return currentHour >= startHour && currentHour < endHour;
  };

  return (
    <NodeWrapper nodeId={id}>
      <div className="bg-gray-800 border-2 border-amber-500 rounded-lg shadow-lg min-w-[300px] max-w-[800px]">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-600 to-orange-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🚗</span>
            <span className="font-semibold text-white">Parking Violation</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowZoneEditor(!showZoneEditor)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                showZoneEditor 
                  ? 'bg-white text-amber-600' 
                  : 'bg-amber-700 text-white hover:bg-amber-800'
              }`}
              title="Zone Editor"
            >
              📐 Zones ({parkingZones.length})
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-white hover:text-gray-200 transition-colors"
            >
              ⚙️
            </button>
          </div>
        </div>
        
        {/* Zone Editor */}
        {showZoneEditor && (
          <div className="p-4 bg-gray-900 border-b border-gray-700">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Zone Editor</h3>
              <button
                onClick={fetchCameraFrame}
                className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white"
              >
                🔄 Refresh Frame
              </button>
            </div>

            {/* Canvas for zone drawing */}
            {frameImage ? (
              <div className="space-y-3">
                <div className="relative bg-black rounded border border-gray-700 overflow-auto max-h-[400px]">
                  <canvas
                    ref={canvasRef}
                    onClick={handleCanvasClick}
                    className="cursor-crosshair max-w-full"
                    style={{ maxWidth: '100%', height: 'auto' }}
                  />
                  
                  {/* Drawing Instructions Overlay */}
                  {currentPolygon.length > 0 && currentPolygon.length < 3 && (
                    <div className="absolute top-2 left-2 bg-black/80 text-yellow-400 px-3 py-2 rounded text-xs">
                      Click {3 - currentPolygon.length} more point(s) to create zone
                    </div>
                  )}
                </div>

                {/* Drawing Controls */}
                <div className="flex gap-2">
                  <button
                    onClick={finishPolygon}
                    disabled={currentPolygon.length < 3}
                    className={`flex-1 px-3 py-2 rounded text-sm font-medium ${
                      currentPolygon.length >= 3
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    ✓ Finish Zone ({currentPolygon.length} pts)
                  </button>
                  <button
                    onClick={clearCurrentPolygon}
                    disabled={currentPolygon.length === 0}
                    className={`px-3 py-2 rounded text-sm ${
                      currentPolygon.length > 0
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    ✕ Clear
                  </button>
                </div>

                {/* Zone Type Selector for New Zone */}
                {currentPolygon.length > 0 && (
                  <div className="bg-gray-700 rounded p-2">
                    <label className="block text-xs text-gray-400 mb-1">Zone Type</label>
                    <select
                      value={restrictionType}
                      onChange={(e) => setRestrictionType(e.target.value)}
                      className="w-full bg-gray-600 text-white px-2 py-1 rounded text-sm"
                    >
                      {restrictionTypes.map(type => (
                        <option key={type.value} value={type.value}>
                          {type.icon} {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Existing Zones List */}
                {parkingZones.length > 0 && (
                  <div className="bg-gray-700 rounded p-3">
                    <div className="text-xs text-gray-400 font-semibold mb-2">
                      Defined Zones ({parkingZones.length})
                    </div>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {parkingZones.map((zone, index) => (
                        <div
                          key={zone.id}
                          className={`flex items-center justify-between p-2 rounded text-xs cursor-pointer ${
                            selectedZoneIndex === index
                              ? 'bg-amber-600 text-white'
                              : 'bg-gray-800 text-gray-300 hover:bg-gray-750'
                          }`}
                          onClick={() => setSelectedZoneIndex(index === selectedZoneIndex ? null : index)}
                        >
                          <div className="flex items-center gap-2">
                            <span>{restrictionTypes.find(t => t.value === zone.type)?.icon}</span>
                            <span className="font-medium">{zone.name}</span>
                            <span className="text-gray-500">({zone.polygon.length} pts)</span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteZone(index);
                            }}
                            className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-white"
                          >
                            🗑️
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-700 rounded p-4 text-center">
                <div className="text-gray-400 mb-2">📷 No camera frame available</div>
                <div className="text-xs text-gray-500 mb-3">
                  {getConnectedCameraId() 
                    ? 'Click refresh to load camera frame' 
                    : 'Connect a camera node to draw zones'}
                </div>
                {!getConnectedCameraId() && (
                  <div className="text-xs text-yellow-400 bg-yellow-900/20 rounded p-2">
                    ⚠️ No camera connected to this node
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Status Display */}
        <div className="p-4 space-y-3">
          {/* Zones Summary */}
          <div className="bg-gray-700 rounded p-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Defined Zones:</span>
              <span className="text-white font-bold">{parkingZones.length}</span>
            </div>
            {parkingZones.length === 0 && (
              <div className="text-xs text-yellow-400 mt-2">
                ⚠️ Click "Zones" to define restricted areas
              </div>
            )}
          </div>

          {/* Violation Counter */}
          <div className="bg-gray-700 rounded p-2 space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Violations Today:</span>
              <span className="text-red-400 font-bold">{violationCount}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Dwell Threshold:</span>
              <span className="text-white">{dwellTime}s</span>
            </div>
            {timeRestricted && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Active Hours:</span>
                <span className={isWithinRestrictedHours() ? 'text-green-400' : 'text-gray-500'}>
                  {startHour}:00 - {endHour}:00
                  {isWithinRestrictedHours() ? ' ✓' : ' (outside)'}
                </span>
              </div>
            )}
          </div>

          {/* Recent Violations */}
          {violations.length > 0 && (
            <div className="bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Recent Violations</div>
              <div className="space-y-1 max-h-24 overflow-y-auto">
                {violations.slice(0, 5).map((v, idx) => (
                  <div key={idx} className="text-xs bg-red-900/20 border border-red-900/50 rounded px-2 py-1">
                    <div className="flex justify-between">
                      <span className="text-red-400 font-mono">{v.plate || 'Unknown'}</span>
                      <span className="text-gray-400">{v.duration}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Configuration Panel */}
          {showConfig && (
            <div className="bg-gray-700 rounded p-3 space-y-3 text-xs">
              <div className="text-gray-400 font-semibold">Detection Settings</div>

              {/* Dwell Time Threshold */}
              <div>
                <label className="block text-gray-400 mb-1">
                  Dwell Time Threshold: {dwellTime}s
                </label>
                <input
                  type="range"
                  value={dwellTime}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    setDwellTime(value);
                    handleConfigChange('dwellTime', value);
                  }}
                  className="w-full"
                  min="5"
                  max="300"
                  step="5"
                />
                <div className="text-gray-500 text-xs mt-1">
                  Vehicle must be stationary for {dwellTime}s to trigger
                </div>
              </div>

              {/* License Plate Recognition */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-600">
                <label className="text-gray-400">Check License Plates</label>
                <input
                  type="checkbox"
                  checked={checkPlates}
                  onChange={(e) => {
                    setCheckPlates(e.target.checked);
                    handleConfigChange('checkPlates', e.target.checked);
                  }}
                  className="rounded"
                />
              </div>
              {checkPlates && (
                <div className="text-xs text-blue-400 bg-blue-900/20 rounded p-2">
                  💡 Requires ALPR/OCR model in workflow
                </div>
              )}

              {/* Time Restrictions */}
              <div className="pt-2 border-t border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-gray-400 font-semibold">Time Restrictions</label>
                  <input
                    type="checkbox"
                    checked={timeRestricted}
                    onChange={(e) => {
                      setTimeRestricted(e.target.checked);
                      handleConfigChange('timeRestricted', e.target.checked);
                    }}
                    className="rounded"
                  />
                </div>

                {timeRestricted && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-gray-400 mb-1">Start</label>
                      <input
                        type="number"
                        value={startHour}
                        onChange={(e) => {
                          const value = parseInt(e.target.value);
                          setStartHour(value);
                          handleConfigChange('startHour', value);
                        }}
                        className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500 text-sm"
                        min="0"
                        max="23"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 mb-1">End</label>
                      <input
                        type="number"
                        value={endHour}
                        onChange={(e) => {
                          const value = parseInt(e.target.value);
                          setEndHour(value);
                          handleConfigChange('endHour', value);
                        }}
                        className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500 text-sm"
                        min="0"
                        max="23"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Action on Violation */}
              <div className="pt-2 border-t border-gray-600">
                <label className="block text-gray-400 mb-2 font-semibold">On Violation</label>
                <div className="space-y-1">
                  <label className="flex items-center gap-2 text-gray-300">
                    <input
                      type="checkbox"
                      checked={config.createAlarm !== false}
                      onChange={(e) => handleConfigChange('createAlarm', e.target.checked)}
                      className="rounded"
                    />
                    <span>Create Alarm</span>
                  </label>
                  <label className="flex items-center gap-2 text-gray-300">
                    <input
                      type="checkbox"
                      checked={config.captureSnapshot !== false}
                      onChange={(e) => handleConfigChange('captureSnapshot', e.target.checked)}
                      className="rounded"
                    />
                    <span>Capture Snapshot</span>
                  </label>
                  <label className="flex items-center gap-2 text-gray-300">
                    <input
                      type="checkbox"
                      checked={config.notifyAuthorities}
                      onChange={(e) => handleConfigChange('notifyAuthorities', e.target.checked)}
                      className="rounded"
                    />
                    <span>Notify Authorities</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Detection Rules Display */}
          {!showConfig && (
            <div className="text-xs text-gray-400 space-y-1">
              <div>✓ Tracking vehicle dwell times ({dwellTime}s)</div>
              {parkingZones.map((zone, idx) => (
                <div key={zone.id} className="flex items-center gap-1">
                  <span>{restrictionTypes.find(t => t.value === zone.type)?.icon}</span>
                  <span>{zone.name}</span>
                </div>
              ))}
              {checkPlates && <div>✓ License plate recognition enabled</div>}
              {timeRestricted && (
                <div>
                  ⏰ Active {startHour}:00-{endHour}:00
                  {!isWithinRestrictedHours() && <span className="text-gray-600"> (inactive)</span>}
                </div>
              )}
            </div>
          )}
          
          {/* Quick Help */}
          {!showConfig && !showZoneEditor && parkingZones.length === 0 && (
            <div className="text-xs text-yellow-400 bg-yellow-900/20 rounded p-2">
              💡 Click "Zones" button to draw restricted parking areas on camera view
            </div>
          )}
        </div>

        {/* Handles */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-amber-500 border-2 border-white"
          title="Vehicle detections input"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-red-500 border-2 border-white"
          title="Violations output"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(ParkingViolationNode);

