import { memo, useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeWrapper from '../components/NodeWrapper';

const ACTION_TYPES = [
  { value: 'alarm', label: 'Create Alarm', icon: '🚨' },
  { value: 'notify_authorities', label: 'Notify Authorities', icon: '📞' },
  { value: 'camera_slew', label: 'Camera Slew', icon: '📹' },
  { value: 'log_flight', label: 'Log Flight', icon: '📝' },
  { value: 'geofence_alert', label: 'Geofence Alert', icon: '⚠️' },
  { value: 'operator_notification', label: 'Operator Notification', icon: '📧' }
];

const DroneActionNode = ({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [triggerCount, setTriggerCount] = useState(0);
  const [lastTrigger, setLastTrigger] = useState(null);
  
  const config = data.config || data || {};
  const actionType = config.action_type || 'alarm';
  const selectedAction = ACTION_TYPES.find(a => a.value === actionType) || ACTION_TYPES[0];
  
  const handleConfigChange = (key, value) => {
    if (data.onChange) {
      data.onChange({ config: { ...config, [key]: value } });
    }
  };
  
  const handleNestedConfigChange = (parent, key, value) => {
    const parentObj = config[parent] || {};
    if (data.onChange) {
      data.onChange({
        config: { ...config, [parent]: { ...parentObj, [key]: value } }
      });
    }
  };
  
  return (
    <NodeWrapper nodeId={id}>
      <div className="bg-gray-800 border-2 border-red-500 rounded-lg shadow-lg min-w-[280px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-500 px-4 py-2 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{selectedAction.icon}</span>
          <span className="font-semibold text-white">Drone Action</span>
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
        {/* Action Type Selection */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Action Type</label>
          <select
            value={actionType}
            onChange={(e) => handleConfigChange('action_type', e.target.value)}
            className="w-full bg-gray-700 text-white px-2 py-1 rounded text-sm border border-gray-600 focus:border-red-500 focus:outline-none"
          >
            {ACTION_TYPES.map(action => (
              <option key={action.value} value={action.value}>
                {action.icon} {action.label}
              </option>
            ))}
          </select>
        </div>
        
        {/* Activity Monitor */}
        <div className="bg-gray-700 rounded p-2 space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Triggers:</span>
            <span className="text-white font-mono">{triggerCount}</span>
          </div>
          {lastTrigger && (
            <div className="flex justify-between">
              <span className="text-gray-400">Last:</span>
              <span className="text-white text-xs">
                {lastTrigger.toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="bg-gray-700 rounded p-3 space-y-3 text-xs">
            <div className="text-gray-400 font-semibold">Action Configuration</div>
            
            {/* Alarm Action Config */}
            {actionType === 'alarm' && (
              <>
                <div>
                  <label className="block text-gray-400 mb-1">Severity</label>
                  <select
                    value={config.alarm_severity || 'high'}
                    onChange={(e) => handleConfigChange('alarm_severity', e.target.value)}
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-gray-400 mb-1">Alarm Title</label>
                  <input
                    type="text"
                    value={config.alarm_title || 'Drone Detection Alert'}
                    onChange={(e) => handleConfigChange('alarm_title', e.target.value)}
                    placeholder="Use {remote_id}, {altitude}, {speed}"
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  />
                  <div className="text-gray-500 mt-1">
                    Variables: {'{remote_id}'}, {'{altitude}'}, {'{speed}'}
                  </div>
                </div>
              </>
            )}
            
            {/* Notify Authorities Config */}
            {actionType === 'notify_authorities' && (
              <>
                <div>
                  <label className="block text-gray-400 mb-1">Agency</label>
                  <input
                    type="text"
                    value={config.authority_contact?.agency || ''}
                    onChange={(e) => handleNestedConfigChange('authority_contact', 'agency', e.target.value)}
                    placeholder="FAA, Law Enforcement, etc."
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={config.authority_contact?.email || ''}
                    onChange={(e) => handleNestedConfigChange('authority_contact', 'email', e.target.value)}
                    placeholder="authority@example.com"
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-400 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={config.authority_contact?.phone || ''}
                    onChange={(e) => handleNestedConfigChange('authority_contact', 'phone', e.target.value)}
                    placeholder="+1-555-0100"
                    className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  />
                </div>
                
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.include_flight_path !== false}
                      onChange={(e) => handleConfigChange('include_flight_path', e.target.checked)}
                    />
                    <span className="text-gray-300">Include Flight Path</span>
                  </label>
                </div>
              </>
            )}
            
            {/* Camera Slew Config */}
            {actionType === 'camera_slew' && (
              <div>
                <label className="block text-gray-400 mb-1">Camera ID</label>
                <input
                  type="text"
                  value={config.camera_id || ''}
                  onChange={(e) => handleConfigChange('camera_id', e.target.value)}
                  placeholder="ptz-camera-01"
                  className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                />
                <div className="text-gray-500 mt-1">
                  PTZ camera to slew to drone coordinates
                </div>
              </div>
            )}
            
            {/* Log Flight Config */}
            {actionType === 'log_flight' && (
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.include_flight_path !== false}
                    onChange={(e) => handleConfigChange('include_flight_path', e.target.checked)}
                  />
                  <span className="text-gray-300">Include Complete Flight Path</span>
                </label>
              </div>
            )}
            
            {/* Geofence Alert Config */}
            {actionType === 'geofence_alert' && (
              <div>
                <label className="block text-gray-400 mb-1">Enforcement Level</label>
                <select
                  value={config.enforcement_level || 'warning'}
                  onChange={(e) => handleConfigChange('enforcement_level', e.target.value)}
                  className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                >
                  <option value="log_only">Log Only</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            )}
            
            {/* Operator Notification Config */}
            {actionType === 'operator_notification' && (
              <div>
                <label className="block text-gray-400 mb-1">Notification Template</label>
                <textarea
                  value={config.notification_template || ''}
                  onChange={(e) => handleConfigChange('notification_template', e.target.value)}
                  placeholder="Message template..."
                  className="w-full bg-gray-600 text-white px-2 py-1 rounded border border-gray-500"
                  rows="3"
                />
                <div className="text-gray-500 mt-1">
                  Attempt contact via Remote ID broadcast
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Action Description */}
        <div className="bg-gray-700 rounded p-2 text-xs text-gray-300">
          {actionType === 'alarm' && '🚨 Creates high-priority alarm in alarm management system'}
          {actionType === 'notify_authorities' && '📞 Sends automated report to configured authorities'}
          {actionType === 'camera_slew' && '📹 Commands PTZ camera to track drone position'}
          {actionType === 'log_flight' && '📝 Records complete flight path to database'}
          {actionType === 'geofence_alert' && '⚠️ Triggers specific alert for airspace violations'}
          {actionType === 'operator_notification' && '📧 Attempts to contact drone operator'}
        </div>
      </div>
      
        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-red-500 border-2 border-white"
        />
      </div>
    </NodeWrapper>
  );
};

export default memo(DroneActionNode);

