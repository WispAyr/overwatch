import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const UniFiAddCameraNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [sublocations, setSublocations] = useState([]);
  
  const config = data.config || data || {};
  const sublocationId = config.sublocationId || '';
  const sublocationName = config.sublocationName || 'Select Sublocation';
  const streamQuality = config.streamQuality || 'medium';
  const autoEnable = config.autoEnable !== false;
  
  useEffect(() => {
    const fetchSublocations = async () => {
      try {
        const response = await fetch('http://localhost:7001/api/sublocations');
        const result = await response.json();
        setSublocations(result.sublocations || []);
      } catch (error) {
        console.error('Failed to fetch sublocations:', error);
      }
    };
    
    fetchSublocations();
  }, []);
  
  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border border-green-500/50 bg-gray-900 min-w-[280px] max-w-[350px]">
        <Handle 
          type="target" 
          position={Position.Left}
          id="cameras-input"
          style={{ background: '#22c55e' }} 
        />
        
        <div className="px-4 py-3 bg-green-950/30 border-b border-green-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-xl">➕</span>
              <div className="font-bold text-sm text-green-400">Add UniFi Cameras</div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
            >
              {showConfig ? '▼' : '▶'}
            </button>
          </div>
          
          <div className="text-[10px] text-gray-400">
            Provision cameras to Overwatch
          </div>
        </div>

        <div className="p-3 space-y-3">
          {/* Sublocation Selection */}
          <div>
            <label className="block text-[10px] text-gray-400 mb-1">Target Sublocation</label>
            <select
              value={sublocationId}
              onChange={(e) => {
                const subloc = sublocations.find(s => s.id === e.target.value);
                handleConfigChange('sublocationId', e.target.value);
                if (subloc) {
                  handleConfigChange('sublocationName', subloc.name);
                }
              }}
              className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
            >
              <option value="">Select sublocation...</option>
              {sublocations.map(subloc => (
                <option key={subloc.id} value={subloc.id}>
                  {subloc.name}
                </option>
              ))}
            </select>
          </div>
          
          {showConfig && (
            <>
              {/* Stream Quality */}
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Stream Quality</label>
                <select
                  value={streamQuality}
                  onChange={(e) => handleConfigChange('streamQuality', e.target.value)}
                  className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
                >
                  <option value="high">High Quality</option>
                  <option value="medium">Medium Quality</option>
                  <option value="low">Low Quality</option>
                </select>
              </div>
              
              {/* Auto Enable */}
              <div>
                <label className="flex items-center space-x-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoEnable}
                    onChange={(e) => handleConfigChange('autoEnable', e.target.checked)}
                    className="w-3 h-3"
                  />
                  <span>Auto-enable cameras</span>
                </label>
              </div>
            </>
          )}
          
          <div className="text-[10px] text-green-400">
            ✓ {sublocationName}
          </div>
        </div>

        <Handle 
          type="source" 
          position={Position.Right} 
          id="result-output"
          style={{ background: '#22c55e' }}
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(UniFiAddCameraNode);

