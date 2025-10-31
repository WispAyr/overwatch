import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

const ACTION_TYPES = [
  { value: 'email', label: 'Email', icon: '📧', color: 'purple' },
  { value: 'webhook', label: 'Webhook', icon: '🔗', color: 'blue' },
  { value: 'record', label: 'Record Video', icon: '🎥', color: 'red' },
  { value: 'snapshot', label: 'Snapshot', icon: '📸', color: 'pink' },
  { value: 'alert', label: 'Alert', icon: '🚨', color: 'red' },
  { value: 'sms', label: 'SMS', icon: '📱', color: 'green' },
  { value: 'pagerduty', label: 'PagerDuty', icon: '📟', color: 'orange' },
];

export default memo(({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false)
  const [showActivity, setShowActivity] = useState(false)
  const [activityCount, setActivityCount] = useState(0)
  
  // Email config
  const [emailTo, setEmailTo] = useState(data.to || '')
  const [emailCc, setEmailCc] = useState(data.cc || '')
  const [emailSubject, setEmailSubject] = useState(data.subject || 'Detection Alert')
  const [includeSnapshot, setIncludeSnapshot] = useState(data.includeSnapshot !== false)
  const [includeDetections, setIncludeDetections] = useState(data.includeDetections !== false)
  
  // Webhook config
  const [webhookUrl, setWebhookUrl] = useState(data.url || '')
  const [webhookMethod, setWebhookMethod] = useState(data.method || 'POST')
  const [webhookTimeout, setWebhookTimeout] = useState(data.timeout || 10)
  const [webhookRetries, setWebhookRetries] = useState(data.retries || 3)
  
  // Record config
  const [recordDuration, setRecordDuration] = useState(data.duration || 30)
  const [recordPreBuffer, setRecordPreBuffer] = useState(data.preBuffer || 5)
  const [recordPostBuffer, setRecordPostBuffer] = useState(data.postBuffer || 5)
  const [recordFormat, setRecordFormat] = useState(data.format || 'mp4')
  const [recordQuality, setRecordQuality] = useState(data.quality || 'medium')
  
  // Snapshot config
  const [drawBoxes, setDrawBoxes] = useState(data.drawBoxes !== false)
  const [drawZones, setDrawZones] = useState(data.drawZones || false)
  const [snapshotFormat, setSnapshotFormat] = useState(data.snapshotFormat || 'jpg')
  const [snapshotQuality, setSnapshotQuality] = useState(data.snapshotQuality || 90)
  
  // Alert config
  const [alertSeverity, setAlertSeverity] = useState(data.severity || 'warning')
  const [alertMessage, setAlertMessage] = useState(data.message || '')
  const [notifyChannels, setNotifyChannels] = useState(data.notify || [])
  
  // SMS config
  const [smsTo, setSmsTo] = useState(data.smsTo || '')
  const [smsMessage, setSmsMessage] = useState(data.smsMessage || '')
  
  const actionType = data.actionType || 'alert'
  const selectedAction = ACTION_TYPES.find(a => a.value === actionType) || ACTION_TYPES[4]
  
  // Update parent data
  useEffect(() => {
    if (data.onChange) {
      const config = { actionType };
      
      if (actionType === 'email') {
        Object.assign(config, { to: emailTo, cc: emailCc, subject: emailSubject, includeSnapshot, includeDetections });
      } else if (actionType === 'webhook') {
        Object.assign(config, { url: webhookUrl, method: webhookMethod, timeout: webhookTimeout, retries: webhookRetries });
      } else if (actionType === 'record') {
        Object.assign(config, { duration: recordDuration, preBuffer: recordPreBuffer, postBuffer: recordPostBuffer, format: recordFormat, quality: recordQuality });
      } else if (actionType === 'snapshot') {
        Object.assign(config, { drawBoxes, drawZones, format: snapshotFormat, quality: snapshotQuality });
      } else if (actionType === 'alert') {
        Object.assign(config, { severity: alertSeverity, message: alertMessage, notify: notifyChannels });
      } else if (actionType === 'sms') {
        Object.assign(config, { to: smsTo, message: smsMessage });
      }
      
      data.onChange(config);
    }
  }, [emailTo, emailCc, emailSubject, includeSnapshot, includeDetections, webhookUrl, webhookMethod, webhookTimeout, webhookRetries, recordDuration, recordPreBuffer, recordPostBuffer, recordFormat, recordQuality, drawBoxes, drawZones, snapshotFormat, snapshotQuality, alertSeverity, alertMessage, notifyChannels, smsTo, smsMessage]);

  const borderColor = `border-${selectedAction.color}-500`

  return (
    <NodeWrapper nodeId={id}>
      <div className={`shadow-lg rounded-lg border-2 ${borderColor} bg-gray-900 min-w-[240px] max-w-[320px]`}>
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-purple-500"
        id="trigger-input"
      />
      
      {/* Activity Preview */}
      {showActivity && (
        <div className="bg-gray-950 border-b border-gray-800 px-4 py-2">
          <div className="text-xs text-gray-400 mb-1">Triggers</div>
          <div className="text-sm font-mono text-purple-400">
            {activityCount} times
          </div>
        </div>
      )}
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xl">{selectedAction.icon}</span>
            <div className="font-bold text-sm">{selectedAction.label}</div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setShowActivity(!showActivity)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
              title="Toggle activity monitor"
            >
              📊
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
        </div>

        {showConfig && (
          <div className="space-y-3">
            {/* Action Type Selector */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">Action Type</label>
              <select
                value={actionType}
                onChange={(e) => {
                  if (data.onChange) {
                    data.onChange({ actionType: e.target.value });
                  }
                }}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                {ACTION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="pt-2 border-t border-gray-700 space-y-3">
              {/* EMAIL Configuration */}
              {actionType === 'email' && (
                <>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">To (Required)</label>
                    <input
                      type="email"
                      value={emailTo}
                      onChange={(e) => setEmailTo(e.target.value)}
                      placeholder="security@company.com"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">CC (Optional)</label>
                    <input
                      type="text"
                      value={emailCc}
                      onChange={(e) => setEmailCc(e.target.value)}
                      placeholder="manager@company.com"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Subject</label>
                    <input
                      type="text"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={includeSnapshot}
                        onChange={(e) => setIncludeSnapshot(e.target.checked)}
                        className="w-3 h-3"
                      />
                      <span className="text-xs text-gray-300">Include snapshot</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={includeDetections}
                        onChange={(e) => setIncludeDetections(e.target.checked)}
                        className="w-3 h-3"
                      />
                      <span className="text-xs text-gray-300">Include detections</span>
                    </label>
                  </div>
                </>
              )}

              {/* WEBHOOK Configuration */}
              {actionType === 'webhook' && (
                <>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">URL (Required)</label>
                    <input
                      type="url"
                      value={webhookUrl}
                      onChange={(e) => setWebhookUrl(e.target.value)}
                      placeholder="https://api.example.com/webhook"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white font-mono"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Method</label>
                      <select
                        value={webhookMethod}
                        onChange={(e) => setWebhookMethod(e.target.value)}
                        className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                      >
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Timeout (s)</label>
                      <input
                        type="number"
                        value={webhookTimeout}
                        onChange={(e) => setWebhookTimeout(parseInt(e.target.value))}
                        min="1"
                        max="60"
                        className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Retries: {webhookRetries}</label>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      value={webhookRetries}
                      onChange={(e) => setWebhookRetries(parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </>
              )}

              {/* RECORD Configuration */}
              {actionType === 'record' && (
                <>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">
                      Duration: {recordDuration}s
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="300"
                      step="10"
                      value={recordDuration}
                      onChange={(e) => setRecordDuration(parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Pre-buffer: {recordPreBuffer}s</label>
                      <input
                        type="range"
                        min="0"
                        max="60"
                        step="5"
                        value={recordPreBuffer}
                        onChange={(e) => setRecordPreBuffer(parseInt(e.target.value))}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Post-buffer: {recordPostBuffer}s</label>
                      <input
                        type="range"
                        min="0"
                        max="60"
                        step="5"
                        value={recordPostBuffer}
                        onChange={(e) => setRecordPostBuffer(parseInt(e.target.value))}
                        className="w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Format</label>
                      <select
                        value={recordFormat}
                        onChange={(e) => setRecordFormat(e.target.value)}
                        className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                      >
                        <option value="mp4">MP4</option>
                        <option value="mkv">MKV</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Quality</label>
                      <select
                        value={recordQuality}
                        onChange={(e) => setRecordQuality(e.target.value)}
                        className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                      >
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>
                  </div>
                  <div className="text-[10px] text-gray-600 bg-gray-800/50 p-2 rounded">
                    Total: {recordPreBuffer + recordDuration + recordPostBuffer}s clip
                  </div>
                </>
              )}

              {/* SNAPSHOT Configuration */}
              {actionType === 'snapshot' && (
                <>
                  <div className="space-y-1">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={drawBoxes}
                        onChange={(e) => setDrawBoxes(e.target.checked)}
                        className="w-3 h-3"
                      />
                      <span className="text-xs text-gray-300">Draw bounding boxes</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={drawZones}
                        onChange={(e) => setDrawZones(e.target.checked)}
                        className="w-3 h-3"
                      />
                      <span className="text-xs text-gray-300">Draw zones</span>
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Format</label>
                      <select
                        value={snapshotFormat}
                        onChange={(e) => setSnapshotFormat(e.target.value)}
                        className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                      >
                        <option value="jpg">JPEG</option>
                        <option value="png">PNG</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 block mb-1">Quality: {snapshotQuality}</label>
                      <input
                        type="range"
                        min="50"
                        max="100"
                        value={snapshotQuality}
                        onChange={(e) => setSnapshotQuality(parseInt(e.target.value))}
                        className="w-full"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* ALERT Configuration */}
              {actionType === 'alert' && (
                <>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Severity</label>
                    <select
                      value={alertSeverity}
                      onChange={(e) => setAlertSeverity(e.target.value)}
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                    >
                      <option value="info">ℹ️ Info</option>
                      <option value="warning">⚠️ Warning</option>
                      <option value="critical">🚨 Critical</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Message</label>
                    <textarea
                      value={alertMessage}
                      onChange={(e) => setAlertMessage(e.target.value)}
                      placeholder="Alert message..."
                      rows="2"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white resize-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Notify via:</label>
                    <div className="space-y-1">
                      {['email', 'sms', 'pagerduty', 'webhook'].map(channel => (
                        <label key={channel} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifyChannels.includes(channel)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setNotifyChannels([...notifyChannels, channel]);
                              } else {
                                setNotifyChannels(notifyChannels.filter(c => c !== channel));
                              }
                            }}
                            className="w-3 h-3"
                          />
                          <span className="text-xs text-gray-300 capitalize">{channel}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* SMS Configuration */}
              {actionType === 'sms' && (
                <>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Phone Number</label>
                    <input
                      type="tel"
                      value={smsTo}
                      onChange={(e) => setSmsTo(e.target.value)}
                      placeholder="+1234567890"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Message (160 chars)</label>
                    <textarea
                      value={smsMessage}
                      onChange={(e) => setSmsMessage(e.target.value)}
                      placeholder="Detection alert..."
                      maxLength="160"
                      rows="3"
                      className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white resize-none"
                    />
                    <div className="text-[10px] text-gray-600 text-right">
                      {smsMessage.length}/160
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
        
        {!showConfig && (
          <div className="text-xs text-gray-500">
            {actionType === 'email' && emailTo && `To: ${emailTo}`}
            {actionType === 'webhook' && webhookUrl && `URL: ${webhookUrl.substring(0, 30)}...`}
            {actionType === 'record' && `${recordDuration}s recording`}
            {actionType === 'alert' && alertSeverity && `${alertSeverity.toUpperCase()} alert`}
            {actionType === 'sms' && smsTo && `To: ${smsTo}`}
          </div>
        )}
      </div>
      </div>
    </NodeWrapper>
  )
})
