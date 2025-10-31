import { memo, useState, useEffect } from 'react';
import { wsBaseUrl } from '../config';

/**
 * NodeStatusIndicator
 * Shows visual status indicators for workflow nodes
 * - Green: Active/Running
 * - Yellow: Warning
 * - Red: Error
 * - Gray: Idle
 */
const NodeStatusIndicator = ({ nodeId, workflowId }) => {
  const [status, setStatus] = useState('idle');
  const [lastError, setLastError] = useState(null);
  const [errorCount, setErrorCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    let ws = null;

    try {
      ws = new WebSocket(`${wsBaseUrl}/api/ws`);

      ws.onopen = () => {
        console.log(`NodeStatusIndicator ${nodeId}: Connected`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Only process events for this specific node
          if (data.node_id !== nodeId) {
            return;
          }

          // Handle different event types
          switch (data.event_type || data.type) {
            case 'node_started':
              setStatus('running');
              setIsProcessing(true);
              break;

            case 'node_completed':
              setStatus('idle');
              setIsProcessing(false);
              break;

            case 'node_error':
              setStatus('error');
              setLastError(data.data?.error_message || 'Unknown error');
              setErrorCount(prev => prev + 1);
              setIsProcessing(false);
              break;

            case 'node_processing':
              setIsProcessing(true);
              break;

            case 'status_update':
              const newStatus = data.data?.status || 'idle';
              setStatus(newStatus);
              break;

            default:
              // Ignore other events
              break;
          }
        } catch (err) {
          console.error('Error processing status message:', err);
        }
      };

      ws.onerror = () => {
        console.error(`NodeStatusIndicator ${nodeId}: WebSocket error`);
      };

      ws.onclose = () => {
        console.log(`NodeStatusIndicator ${nodeId}: Disconnected`);
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
    }

    return () => {
      if (ws) {
        try {
          ws.close();
        } catch (err) {
          console.error('Error closing WebSocket:', err);
        }
      }
    };
  }, [nodeId]);

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'idle':
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Running';
      case 'error':
        return `Error (${errorCount})`;
      case 'warning':
        return 'Warning';
      case 'idle':
      default:
        return 'Idle';
    }
  };

  return (
    <div className="relative inline-block">
      {/* Status Dot */}
      <div
        className="relative cursor-help"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div
          className={`w-2 h-2 rounded-full ${getStatusColor()} ${
            isProcessing ? 'animate-pulse' : ''
          }`}
        />

        {/* Error Badge */}
        {errorCount > 0 && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-600 rounded-full flex items-center justify-center">
            <span className="text-[8px] text-white font-bold">{errorCount > 9 ? '9+' : errorCount}</span>
          </div>
        )}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50 pointer-events-none">
          <div className="bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 whitespace-nowrap border border-gray-700">
            <div className="font-semibold mb-1">{getStatusText()}</div>
            {lastError && (
              <div className="text-red-400 text-[10px] max-w-xs">
                {lastError}
              </div>
            )}
            {/* Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px">
              <div className="border-4 border-transparent border-t-gray-900" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(NodeStatusIndicator);

