import { memo, useState, useEffect } from 'react';
import { wsBaseUrl } from '../config';
import NodeStatusIndicator from './NodeStatusIndicator';

/**
 * NodeWrapper
 * Wraps nodes to add visual error/status indicators
 */
const NodeWrapper = ({ children, nodeId, className = '' }) => {
  const [hasError, setHasError] = useState(false);
  const [hasWarning, setHasWarning] = useState(false);
  const [errorPulse, setErrorPulse] = useState(false);

  useEffect(() => {
    let ws = null;
    let pulseTimeout = null;

    try {
      ws = new WebSocket(`${wsBaseUrl}/api/ws`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Only process events for this specific node
          if (data.node_id !== nodeId) {
            return;
          }

          // Handle error events
          if (data.event_type === 'node_error' || data.type === 'node_error') {
            setHasError(true);
            setErrorPulse(true);

            // Stop pulse animation after 2 seconds
            pulseTimeout = setTimeout(() => {
              setErrorPulse(false);
            }, 2000);
          }

          // Clear error on successful completion
          if (data.event_type === 'node_completed' && data.data?.passed) {
            setHasError(false);
            setHasWarning(false);
          }

          // Handle warnings (filtered out detections, etc.)
          if (data.event_type === 'node_completed' && data.data?.passed === false) {
            setHasWarning(true);
          }
        } catch (err) {
          console.error('Error processing node status:', err);
        }
      };
    } catch (err) {
      console.error('Error creating WebSocket for node wrapper:', err);
    }

    return () => {
      if (pulseTimeout) clearTimeout(pulseTimeout);
      if (ws) {
        try {
          ws.close();
        } catch (err) {
          // Ignore
        }
      }
    };
  }, [nodeId]);

  const getBorderClass = () => {
    if (hasError) {
      return errorPulse
        ? 'border-red-500 shadow-red-500/50 shadow-lg animate-pulse'
        : 'border-red-500';
    }
    if (hasWarning) {
      return 'border-yellow-500';
    }
    return '';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Status Indicator in top-right corner */}
      <div className="absolute -top-1 -right-1 z-10">
        <NodeStatusIndicator nodeId={nodeId} />
      </div>

      {/* Border overlay for errors */}
      {(hasError || hasWarning) && (
        <div
          className={`absolute inset-0 pointer-events-none rounded-lg border-2 ${getBorderClass()}`}
          style={{ margin: '-2px' }}
        />
      )}

      {/* Children (actual node content) */}
      {children}
    </div>
  );
};

export default memo(NodeWrapper);

