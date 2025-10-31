import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const UniFiCameraDiscoveryNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const config = data.config || data || {};
  const credentialId = config.credentialId || '';
  const credentialName = config.credentialName || 'Select Credential';
  const filterState = config.filterState || 'all';
  const filterRecording = config.filterRecording;
  
  // Fetch available UniFi credentials
  useEffect(() => {
    const fetchCredentials = async () => {
      try {
        const response = await fetch('http://localhost:7001/api/unifi/credentials');
        const result = await response.json();
        setCredentials(result.credentials || []);
      } catch (error) {
        console.error('Failed to fetch UniFi credentials:', error);
      }
    };
    
    fetchCredentials();
  }, []);
  
  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border border-blue-500/50 bg-gray-900 min-w-[280px] max-w-[350px]">
        <Handle type="target" position={Position.Left} style={{ background: '#3b82f6' }} />
        
        <div className="px-4 py-3 bg-blue-950/30 border-b border-blue-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-xl">📡</span>
              <div className="font-bold text-sm text-blue-400">UniFi Camera Discovery</div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
            >
              {showConfig ? '▼' : '▶'}
            </button>
          </div>
          
          <div className="text-[10px] text-gray-400">
            Discover UniFi Protect cameras
          </div>
        </div>

        <div className="p-3 space-y-3">
          {/* Credential Selection */}
          <div>
            <label className="block text-[10px] text-gray-400 mb-1">UniFi Credential</label>
            <select
              value={credentialId}
              onChange={(e) => {
                const cred = credentials.find(c => c.id === e.target.value);
                handleConfigChange('credentialId', e.target.value);
                if (cred) {
                  handleConfigChange('credentialName', cred.name);
                }
              }}
              className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
            >
              <option value="">Select credential...</option>
              {credentials.map(cred => (
                <option key={cred.id} value={cred.id}>
                  {cred.name} ({cred.host})
                </option>
              ))}
            </select>
          </div>
          
          {showConfig && (
            <>
              {/* Filter State */}
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Filter State</label>
                <select
                  value={filterState}
                  onChange={(e) => handleConfigChange('filterState', e.target.value)}
                  className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
                >
                  <option value="all">All Cameras</option>
                  <option value="connected">Connected Only</option>
                  <option value="disconnected">Disconnected Only</option>
                </select>
              </div>
              
              {/* Filter Recording */}
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Filter Recording</label>
                <select
                  value={filterRecording === true ? 'recording' : filterRecording === false ? 'not-recording' : 'all'}
                  onChange={(e) => {
                    const val = e.target.value === 'recording' ? true : e.target.value === 'not-recording' ? false : null;
                    handleConfigChange('filterRecording', val);
                  }}
                  className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200"
                >
                  <option value="all">All Cameras</option>
                  <option value="recording">Recording Only</option>
                  <option value="not-recording">Not Recording</option>
                </select>
              </div>
            </>
          )}
          
          <div className="text-[10px] text-blue-400">
            ✓ {credentialName}
          </div>
        </div>

        <Handle 
          type="source" 
          position={Position.Right} 
          id="cameras-output"
          style={{ background: '#3b82f6' }}
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(UniFiCameraDiscoveryNode);

