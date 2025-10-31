import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const DroneFilterNode = ({ data, id }) => {
  const [geofences, setGeofences] = useState([]);
  const [showConfig, setShowConfig] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  
  // Fetch available geofences
  useEffect(() => {
    const fetchGeofences = async () => {
      try {
        const response = await fetch('/api/drone-components/geofences');
        const result = await response.json();
        setGeofences(result.geofences || []);
      } catch (error) {
        console.error('Error fetching geofences:', error);
      }
    };
    
    fetchGeofences();
  }, []);
  
  const config = data.config || data || {};
  const altitudeMin = config.altitude_min ?? 0;
  const altitudeMax = config.altitude_max ?? 10000;
  const speedMin = config.speed_min ?? 0;
  const speedMax = config.speed_max ?? 300;
  const selectedGeofences = config.geofence_ids || [];
  
  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="bg-gray-800 border-2 border-yellow-500 rounded-lg shadow-lg min-w-[280px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-600 to-yellow-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📐</span>
          <span className="font-semibold text-white">Drone Filter</span>
        </div>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-white hover:text-gray-200 transition-colors"
        >
          ⚙️
        </button>
      </div>
      
      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Filter Summary */}
        <div className="bg-gray-700 rounded p-2 space-y-1 text-xs">
          <div className="text-gray-400 font-semibold mb-1">Active Filters</div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Altitude:</span>
            <span className="text-white font-mono">
              {altitudeMin}-{altitudeMax}m
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Speed:</span>
            <span className="text-white font-mono">
              {speedMin}-{speedMax} m/s
            </span>
          </div>
          
          {selectedGeofences.length > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Geofences:</span>
              <span className="text-white">{selectedGeofences.length} selected</span>
            </div>
          )}
        </div>
        
        {/* Statistics */}
        <div className="bg-gray-700 rounded p-2">
          <div className="text-xs text-center">
            <span className="text-green-400 font-bold text-lg">{matchCount}</span>
            <span className="text-gray-400"> of </span>
            <span className="text-gray-300">{totalCount}</span>
            <div className="text-gray-400 mt-1">drones match filters</div>
          </div>
        </div>
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="bg-gray-700 rounded p-3 space-y-3 text-xs">
            <div className="text-gray-400 font-semibold">Filter Configuration</div>
            
            {/* Altitude Range */}
            <div className="space-y-1">
              <label className="block text-gray-400">Altitude Range (m)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={altitudeMin}
                  onChange={(e) => handleConfigChange('altitude_min', parseFloat(e.target.value))}
                  className="w-1/2 bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  min="0"
                  max="10000"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={altitudeMax}
                  onChange={(e) => handleConfigChange('altitude_max', parseFloat(e.target.value))}
                  className="w-1/2 bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  min="0"
                  max="10000"
                />
              </div>
            </div>
            
            {/* Speed Range */}
            <div className="space-y-1">
              <label className="block text-gray-400">Speed Range (m/s)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={speedMin}
                  onChange={(e) => handleConfigChange('speed_min', parseFloat(e.target.value))}
                  className="w-1/2 bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  min="0"
                  max="300"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={speedMax}
                  onChange={(e) => handleConfigChange('speed_max', parseFloat(e.target.value))}
                  className="w-1/2 bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  min="0"
                  max="300"
                />
              </div>
            </div>
            
            {/* Geofence Selection */}
            <div className="space-y-1">
              <label className="block text-gray-400">Geofence Zones</label>
              <select
                multiple
                value={selectedGeofences}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  handleConfigChange('geofence_ids', selected);
                }}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                size="4"
              >
                {geofences.map(gf => (
                  <option key={gf.id} value={gf.id}>
                    {gf.name} ({gf.restriction_type})
                  </option>
                ))}
              </select>
              <div className="text-gray-500 text-xs mt-1">
                Hold Ctrl/Cmd to select multiple
              </div>
            </div>
            
            {/* Filter Mode */}
            <div className="space-y-1">
              <label className="block text-gray-400">Filter Mode</label>
              <select
                value={config.filter_mode || 'pass_matching'}
                onChange={(e) => handleConfigChange('filter_mode', e.target.value)}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
              >
                <option value="pass_matching">Pass Matching Criteria</option>
                <option value="pass_violations">Pass Violations Only</option>
              </select>
            </div>
            
            {/* RSSI Filter */}
            <div className="space-y-1">
              <label className="block text-gray-400">Min RSSI (dBm)</label>
              <input
                type="number"
                value={config.rssi_min || -100}
                onChange={(e) => handleConfigChange('rssi_min', parseInt(e.target.value))}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="-120"
                max="-20"
              />
            </div>
            
            {/* Operator Distance */}
            <div className="space-y-1">
              <label className="block text-gray-400">Max Operator Distance (m)</label>
              <input
                type="number"
                value={config.operator_distance_max || ''}
                onChange={(e) => handleConfigChange('operator_distance_max', parseFloat(e.target.value))}
                placeholder="No limit"
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="0"
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-yellow-500 border-2 border-white"
      />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-yellow-500 border-2 border-white"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(DroneFilterNode);

