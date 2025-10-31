import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const DroneAnalyticsNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [stats, setStats] = useState({
    totalDrones: 0,
    uniqueDrones: 0,
    violations: 0,
    complianceRate: 100,
    avgAltitude: 0,
    avgSpeed: 0
  });
  
  const config = data.config || data || {};
  const timeWindow = config.time_window ?? 3600; // seconds
  const enableHotspot = config.enable_hotspot_detection !== false;
  const enablePattern = config.enable_pattern_analysis !== false;
  const enableCompliance = config.enable_compliance_scoring !== false;
  const enableTemporal = config.enable_temporal_analysis !== false;
  
  // Simulated statistics (would be real-time in production)
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        totalDrones: prev.totalDrones + Math.floor(Math.random() * 2),
        uniqueDrones: Math.floor(prev.totalDrones * 0.7),
        violations: prev.violations + (Math.random() > 0.9 ? 1 : 0),
        complianceRate: ((prev.totalDrones - prev.violations) / Math.max(prev.totalDrones, 1) * 100).toFixed(1),
        avgAltitude: (Math.random() * 200 + 50).toFixed(1),
        avgSpeed: (Math.random() * 15 + 5).toFixed(1)
      }));
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="bg-gray-800 border-2 border-purple-500 rounded-lg shadow-lg min-w-[300px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📊</span>
          <span className="font-semibold text-white">Drone Analytics</span>
        </div>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-white hover:text-gray-200 transition-colors"
        >
          ⚙️
        </button>
      </div>
      
      {/* Statistics Display */}
      <div className="p-4 space-y-3">
        {/* Time Window Info */}
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-xs text-gray-400">Analysis Window</div>
          <div className="text-white font-bold">
            {timeWindow >= 3600 
              ? `${(timeWindow / 3600).toFixed(1)}h` 
              : `${timeWindow / 60}m`
            }
          </div>
        </div>
        
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-gray-700 rounded p-2">
            <div className="text-xs text-gray-400">Total Detections</div>
            <div className="text-xl font-bold text-white">{stats.totalDrones}</div>
          </div>
          
          <div className="bg-gray-700 rounded p-2">
            <div className="text-xs text-gray-400">Unique Drones</div>
            <div className="text-xl font-bold text-white">{stats.uniqueDrones}</div>
          </div>
          
          <div className="bg-gray-700 rounded p-2">
            <div className="text-xs text-gray-400">Violations</div>
            <div className="text-xl font-bold text-red-400">{stats.violations}</div>
          </div>
          
          <div className="bg-gray-700 rounded p-2">
            <div className="text-xs text-gray-400">Compliance</div>
            <div className="text-xl font-bold text-green-400">{stats.complianceRate}%</div>
          </div>
        </div>
        
        {/* Average Metrics */}
        <div className="bg-gray-700 rounded p-2 space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Avg Altitude:</span>
            <span className="text-white font-mono">{stats.avgAltitude}m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Avg Speed:</span>
            <span className="text-white font-mono">{stats.avgSpeed} m/s</span>
          </div>
        </div>
        
        {/* Enabled Analysis Features */}
        <div className="bg-gray-700 rounded p-2 space-y-1 text-xs">
          <div className="text-gray-400 font-semibold mb-1">Active Analysis</div>
          {enableHotspot && (
            <div className="flex items-center gap-1 text-green-400">
              <span>✓</span>
              <span>Hotspot Detection</span>
            </div>
          )}
          {enablePattern && (
            <div className="flex items-center gap-1 text-green-400">
              <span>✓</span>
              <span>Pattern Analysis</span>
            </div>
          )}
          {enableCompliance && (
            <div className="flex items-center gap-1 text-green-400">
              <span>✓</span>
              <span>Compliance Scoring</span>
            </div>
          )}
          {enableTemporal && (
            <div className="flex items-center gap-1 text-green-400">
              <span>✓</span>
              <span>Temporal Analysis</span>
            </div>
          )}
        </div>
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="bg-gray-700 rounded p-3 space-y-3 text-xs">
            <div className="text-gray-400 font-semibold">Analytics Configuration</div>
            
            {/* Time Window */}
            <div>
              <label className="block text-gray-400 mb-1">
                Time Window (seconds)
              </label>
              <input
                type="number"
                value={timeWindow}
                onChange={(e) => handleConfigChange('time_window', parseInt(e.target.value))}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="60"
                max="604800"
              />
              <div className="text-gray-500 mt-1">
                {timeWindow >= 3600 
                  ? `${(timeWindow / 3600).toFixed(1)} hours` 
                  : `${timeWindow / 60} minutes`
                }
              </div>
            </div>
            
            {/* Aggregation Interval */}
            <div>
              <label className="block text-gray-400 mb-1">
                Aggregation Interval (seconds)
              </label>
              <input
                type="number"
                value={config.aggregation_interval || 300}
                onChange={(e) => handleConfigChange('aggregation_interval', parseInt(e.target.value))}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="60"
                max="86400"
              />
            </div>
            
            {/* Analysis Features Toggles */}
            <div className="space-y-2">
              <div className="text-gray-400 font-semibold">Analysis Features</div>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={enableHotspot}
                  onChange={(e) => handleConfigChange('enable_hotspot_detection', e.target.checked)}
                />
                <span className="text-gray-300">Hotspot Detection</span>
              </label>
              
              {enableHotspot && (
                <div className="ml-6">
                  <label className="block text-gray-400 mb-1">
                    Hotspot Radius (m)
                  </label>
                  <input
                    type="number"
                    value={config.hotspot_radius || 100}
                    onChange={(e) => handleConfigChange('hotspot_radius', parseFloat(e.target.value))}
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded"
                    min="10"
                    max="10000"
                  />
                </div>
              )}
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={enablePattern}
                  onChange={(e) => handleConfigChange('enable_pattern_analysis', e.target.checked)}
                />
                <span className="text-gray-300">Pattern Analysis</span>
              </label>
              
              {enablePattern && (
                <div className="ml-6">
                  <label className="block text-gray-400 mb-1">
                    Min Detections for Pattern
                  </label>
                  <input
                    type="number"
                    value={config.min_detections_for_pattern || 5}
                    onChange={(e) => handleConfigChange('min_detections_for_pattern', parseInt(e.target.value))}
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded"
                    min="3"
                    max="100"
                  />
                </div>
              )}
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={enableCompliance}
                  onChange={(e) => handleConfigChange('enable_compliance_scoring', e.target.checked)}
                />
                <span className="text-gray-300">Compliance Scoring</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={enableTemporal}
                  onChange={(e) => handleConfigChange('enable_temporal_analysis', e.target.checked)}
                />
                <span className="text-gray-300">Temporal Analysis</span>
              </label>
            </div>
            
            {/* Violation Threshold */}
            <div>
              <label className="block text-gray-400 mb-1">
                Violation Rate Threshold
              </label>
              <input
                type="number"
                value={config.violation_threshold || 0.1}
                onChange={(e) => handleConfigChange('violation_threshold', parseFloat(e.target.value))}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="0"
                max="1"
                step="0.01"
              />
              <div className="text-gray-500 mt-1">
                Alert if violations exceed {((config.violation_threshold || 0.1) * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-purple-500 border-2 border-white"
      />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-purple-500 border-2 border-white"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(DroneAnalyticsNode);

