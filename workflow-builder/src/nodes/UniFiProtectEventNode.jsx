import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const EVENT_TYPES = [
  { value: 'motion', label: 'Motion', icon: '👋' },
  { value: 'smart', label: 'Smart Detection', icon: '🧠' },
  { value: 'ring', label: 'Doorbell Ring', icon: '🔔' }
];

const DETECTION_TYPES = [
  { value: 'person', label: 'Person' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'animal', label: 'Animal' }
];

const UniFiProtectEventNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [credentials, setCredentials] = useState([]);
  
  const config = data.config || data || {};
  const credentialId = config.credentialId || '';
  const credentialName = config.credentialName || 'Select Credential';
  const eventTypes = config.eventTypes || ['motion'];
  const detectionTypes = config.detectionTypes || [];
  const cameraFilter = config.cameraFilter || [];
  const pollInterval = config.pollInterval || 10;
  
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
  
  const toggleEventType = (type) => {
    const updated = eventTypes.includes(type)
      ? eventTypes.filter(t => t !== type)
      : [...eventTypes, type];
    handleConfigChange('eventTypes', updated);
  };
  
  const toggleDetectionType = (type) => {
    const updated = detectionTypes.includes(type)
      ? detectionTypes.filter(t => t !== type)
      : [...detectionTypes, type];
    handleConfigChange('detectionTypes', updated);
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border border-purple-500/50 bg-gray-900 min-w-[280px] max-w-[350px]">
        <div className="px-4 py-3 bg-purple-950/30 border-b border-purple-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-xl">🎥</span>
              <div className="font-bold text-sm text-purple-400">UniFi Protect Events</div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
            >
              {showConfig ? '▼' : '▶'}
            </button>
          </div>
          
          <div className="text-[10px] text-gray-400">
            Monitor Protect events
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
              {/* Event Types */}
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">Event Types</label>
                <div className="space-y-1">
                  {EVENT_TYPES.map(type => (
                    <label key={type.value} className="flex items-center space-x-2 text-xs cursor-pointer">
                      <input
                        type="checkbox"
                        checked={eventTypes.includes(type.value)}
                        onChange={() => toggleEventType(type.value)}
                        className="w-3 h-3"
                      />
                      <span>{type.icon} {type.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Detection Types (for smart events) */}
              {eventTypes.includes('smart') && (
                <div>
                  <label className="block text-[10px] text-gray-400 mb-1">Smart Detection Types</label>
                  <div className="space-y-1">
                    {DETECTION_TYPES.map(type => (
                      <label key={type.value} className="flex items-center space-x-2 text-xs cursor-pointer">
                        <input
                          type="checkbox"
                          checked={detectionTypes.includes(type.value)}
                          onChange={() => toggleDetectionType(type.value)}
                          className="w-3 h-3"
                        />
                        <span>{type.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Poll Interval */}
              <div>
                <label className="block text-[10px] text-gray-400 mb-1">
                  Poll Interval: {pollInterval}s
                </label>
                <input
                  type="range"
                  min="5"
                  max="60"
                  step="5"
                  value={pollInterval}
                  onChange={(e) => handleConfigChange('pollInterval', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            </>
          )}
          
          <div className="text-[10px] text-purple-400">
            ✓ {credentialName}
          </div>
        </div>

        <Handle 
          type="source" 
          position={Position.Right} 
          id="events-output"
          style={{ background: '#a855f7' }}
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(UniFiProtectEventNode);

