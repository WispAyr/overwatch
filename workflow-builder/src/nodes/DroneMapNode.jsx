import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import { wsBaseUrl } from '../config';
import NodeWrapper from '../components/NodeWrapper';

const DroneMapNode = ({ data, id }) => {
  const [drones, setDrones] = useState({});
  const [showConfig, setShowConfig] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const config = data.config || data || {};
  const centerLat = config.center_lat ?? 37.422;
  const centerLon = config.center_lon ?? -122.084;
  const initialZoom = config.initial_zoom ?? 13;
  const showGeofences = config.show_geofences !== false;
  const showOperators = config.show_operators !== false;
  
  // WebSocket connection for live drone positions
  useEffect(() => {
    let ws = null;
    
    try {
      ws = new WebSocket(`${wsBaseUrl}/api/ws`);
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'subscribe',
          topics: ['drone_detection', 'drone_detections']
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'drone_detection') {
            const droneData = message.data;
            const remoteId = droneData?.remote_id;
            
            if (remoteId) {
              setDrones(prev => {
                const updated = { ...prev };
                updated[remoteId] = {
                  ...droneData,
                  timestamp: new Date(message.timestamp)
                };
                return updated;
              });
            }
          }
        } catch (err) {
          console.error('Error processing drone message:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
    }
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);
  
  // Cleanup old drones
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      setDrones(prev => {
        const updated = { ...prev };
        Object.keys(updated).forEach(remoteId => {
          const drone = updated[remoteId];
          if (drone?.timestamp) {
            const age = now - drone.timestamp;
            if (age > 300000) { // 5 minutes
              delete updated[remoteId];
            }
          } else {
            // Remove drones without valid timestamps
            delete updated[remoteId];
          }
        });
        return updated;
      });
    }, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, []);
  
  const getDroneColor = (drone) => {
    if (drone.geofence_violations?.length > 0) return 'text-red-500';
    if (drone.position?.altitude > 120) return 'text-yellow-500';
    return 'text-green-500';
  };
  
  const mapSize = isExpanded ? 'w-[600px] h-[400px]' : 'w-full h-[200px]';
  
  return (
    <NodeWrapper nodeId={id}>
      <div className={`bg-gray-800 border-2 border-blue-500 rounded-lg shadow-lg ${isExpanded ? 'min-w-[620px]' : 'min-w-[320px]'}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🗺️</span>
          <span className="font-semibold text-white">Drone Map</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-white hover:text-gray-200 transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '⬇️' : '⬆️'}
          </button>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-white hover:text-gray-200 transition-colors"
          >
            ⚙️
          </button>
        </div>
      </div>
      
      {/* Map Placeholder */}
      <div className={`${mapSize} bg-gray-700 relative flex items-center justify-center`}>
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">🗺️</div>
          <div className="text-sm">Map Visualization</div>
          <div className="text-xs mt-1">
            Center: {centerLat.toFixed(4)}, {centerLon.toFixed(4)}
          </div>
          <div className="text-xs">Zoom: {initialZoom}</div>
        </div>
        
        {/* Drone Count Overlay */}
        <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
          🛸 {Object.keys(drones).length} active
        </div>
      </div>
      
      {/* Drone List */}
      <div className="p-3 bg-gray-700 max-h-32 overflow-y-auto">
        <div className="text-xs text-gray-400 mb-1 font-semibold">Active Drones:</div>
        {Object.keys(drones).length === 0 ? (
          <div className="text-xs text-gray-500 text-center py-2">No drones detected</div>
        ) : (
          <div className="space-y-1">
            {Object.entries(drones).map(([remoteId, drone]) => (
              <div key={remoteId} className="bg-gray-600 rounded px-2 py-1 text-xs flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className={`${getDroneColor(drone)} font-bold`}>●</span>
                  <span className="text-white font-mono">{remoteId.substring(0, 12)}</span>
                </div>
                <div className="text-gray-300">
                  {drone.position?.altitude?.toFixed(0)}m @ {drone.velocity?.speed?.toFixed(1)}m/s
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Configuration Panel */}
      {showConfig && (
        <div className="p-3 bg-gray-700 border-t border-gray-600 space-y-2 text-xs">
          <div className="text-gray-400 font-semibold">Map Configuration</div>
          
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-gray-400 mb-1">Center Lat</label>
              <input
                type="number"
                value={centerLat}
                onChange={(e) => data.onChange?.({ config: { ...config, center_lat: parseFloat(e.target.value) } })}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded text-xs"
                step="0.001"
              />
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Center Lon</label>
              <input
                type="number"
                value={centerLon}
                onChange={(e) => data.onChange?.({ config: { ...config, center_lon: parseFloat(e.target.value) } })}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded text-xs"
                step="0.001"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-gray-400 mb-1">Zoom Level</label>
            <input
              type="number"
              value={initialZoom}
              onChange={(e) => data.onChange?.({ config: { ...config, initial_zoom: parseInt(e.target.value) } })}
              className="w-full bg-gray-600 text-white px-2 py-1 rounded text-xs"
              min="1"
              max="20"
            />
          </div>
          
          <div className="flex gap-3">
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={showGeofences}
                onChange={(e) => data.onChange?.({ config: { ...config, show_geofences: e.target.checked } })}
              />
              <span className="text-gray-300">Show Geofences</span>
            </label>
            
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={showOperators}
                onChange={(e) => data.onChange?.({ config: { ...config, show_operators: e.target.checked } })}
              />
              <span className="text-gray-300">Show Operators</span>
            </label>
          </div>
          
          <div className="text-xs text-gray-500 italic mt-2">
            Note: Full map visualization with Leaflet will be enabled when backend is running
          </div>
        </div>
      )}
      
        {/* Handles */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-blue-500 border-2 border-white"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-blue-500 border-2 border-white"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(DroneMapNode);
