import { memo, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import { apiBaseUrl, wsBaseUrl } from '../config';
import NodeWrapper from '../components/NodeWrapper';

const DroneInputNode = ({ data, id }) => {
  const [receivers, setReceivers] = useState([]);
  const [selectedReceiver, setSelectedReceiver] = useState(data.receiver_id || '');
  const [detectionCount, setDetectionCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  
  // Fetch available receivers
  useEffect(() => {
    const fetchReceivers = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/drone-components/receivers`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setReceivers(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching receivers:', error);
        setReceivers([]);
      }
    };
    
    fetchReceivers();
    // Refresh receiver status every 10 seconds
    const interval = setInterval(fetchReceivers, 10000);
    return () => clearInterval(interval);
  }, []);
  
  // WebSocket connection for live drone detections
  useEffect(() => {
    let ws = null;
    
    try {
      ws = new WebSocket(`${wsBaseUrl}/api/ws`);
      
      ws.onopen = () => {
        setIsConnected(true);
        // Subscribe to drone detections
        try {
          ws.send(JSON.stringify({
            type: 'subscribe',
            topics: ['drone_detection', 'drone_detections']
          }));
        } catch (err) {
          console.error('Error sending subscribe message:', err);
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'drone_detection') {
            // Filter by receiver if configured
            if (!selectedReceiver || message.data?.receiver_id === selectedReceiver) {
              setDetectionCount(prev => prev + 1);
              setLastUpdate(new Date());
            }
          }
        } catch (err) {
          console.error('Error processing drone detection:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        setIsConnected(false);
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setIsConnected(false);
    }
    
    return () => {
      if (ws) {
        try {
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
          }
        } catch (err) {
          console.error('Error closing WebSocket:', err);
        }
      }
    };
  }, [selectedReceiver]);
  
  const handleReceiverChange = (e) => {
    try {
      const receiverId = e.target.value;
      setSelectedReceiver(receiverId);
      if (data.onChange) {
        data.onChange({ config: { ...(data.config || {}), receiver_id: receiverId } });
      }
    } catch (err) {
      console.error('Error changing receiver:', err);
    }
  };
  
  const selectedReceiverData = Array.isArray(receivers) 
    ? receivers.find(r => r?.id === selectedReceiver)
    : null;
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="bg-gray-800 border-2 border-orange-500 rounded-lg shadow-lg min-w-[280px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-orange-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🛸</span>
          <span className="font-semibold text-white">Drone Input</span>
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
        {/* Receiver Selection */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Receiver</label>
          <select
            value={selectedReceiver}
            onChange={handleReceiverChange}
            className="w-full bg-gray-700 text-white px-2 py-1 rounded text-sm border border-gray-600 focus:border-orange-500 focus:outline-none"
          >
            <option value="">All Receivers</option>
            {Array.isArray(receivers) && receivers.map(receiver => (
              <option key={receiver.id} value={receiver.id}>
                {receiver.name} {receiver.connected ? '🟢' : '🔴'}
              </option>
            ))}
          </select>
        </div>
        
        {/* Status Display */}
        <div className="bg-gray-700 rounded p-2 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">Status:</span>
            <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">Detections:</span>
            <span className="text-white font-mono">{detectionCount}</span>
          </div>
          
          {lastUpdate && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Last Update:</span>
              <span className="text-white text-xs">
                {lastUpdate.toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
        
        {/* Receiver Details (when selected) */}
        {selectedReceiverData && (
          <div className="bg-gray-700 rounded p-2 space-y-1 text-xs">
            <div className="text-gray-400 font-semibold mb-1">Receiver Info</div>
            <div className="flex justify-between">
              <span className="text-gray-400">Port:</span>
              <span className="text-white">{selectedReceiverData.port}</span>
            </div>
            {selectedReceiverData.location && (
              <>
                <div className="flex justify-between">
                  <span className="text-gray-400">Lat:</span>
                  <span className="text-white font-mono">
                    {selectedReceiverData.location.latitude?.toFixed(6)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Lon:</span>
                  <span className="text-white font-mono">
                    {selectedReceiverData.location.longitude?.toFixed(6)}
                  </span>
                </div>
              </>
            )}
            <div className="flex justify-between">
              <span className="text-gray-400">Total:</span>
              <span className="text-white">
                {selectedReceiverData.stats?.detection_count || 0}
              </span>
            </div>
          </div>
        )}
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="bg-gray-700 rounded p-2 space-y-2 text-xs">
            <div className="text-gray-400 font-semibold">Configuration</div>
            
            <div>
              <label className="block text-gray-400 mb-1">Min RSSI (dBm)</label>
              <input
                type="number"
                defaultValue={(data.config || data)?.min_rssi ?? -100}
                onChange={(e) => {
                  try {
                    const value = parseInt(e.target.value);
                    if (!isNaN(value)) {
                      data.onChange?.({ config: { ...(data.config || {}), min_rssi: value } });
                    }
                  } catch (err) {
                    console.error('Error updating min_rssi:', err);
                  }
                }}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="-120"
                max="-20"
              />
            </div>
            
            <div>
              <label className="block text-gray-400 mb-1">Update Rate (Hz)</label>
              <input
                type="number"
                defaultValue={(data.config || data)?.update_rate ?? 1.0}
                onChange={(e) => {
                  try {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                      data.onChange?.({ config: { ...(data.config || {}), update_rate: value } });
                    }
                  } catch (err) {
                    console.error('Error updating update_rate:', err);
                  }
                }}
                className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                min="0.1"
                max="10"
                step="0.1"
              />
            </div>
          </div>
        )}
      </div>
      
        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-orange-500 border-2 border-white"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(DroneInputNode);

