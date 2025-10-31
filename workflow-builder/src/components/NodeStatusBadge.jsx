/**
 * Node Status Badge Component
 * Shows production/needsConfig/beta/notImplemented badges for workflow nodes
 */
import React from 'react'
import useComponentStatus from '../hooks/useComponentStatus'

const NodeStatusBadge = ({ nodeType, nodeId, size = 'sm', showText = false }) => {
  const { getNodeStatus, getBadgeConfig, loading } = useComponentStatus()

  if (loading) {
    return null
  }

  const status = getNodeStatus(nodeType, nodeId)
  if (!status) {
    return null // No status info = assume it's fine
  }

  const badge = getBadgeConfig(status.badge || 'production')

  const sizeClasses = {
    xs: 'text-xs px-1 py-0.5',
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5'
  }

  return (
    <div
      className={`inline-flex items-center gap-1 rounded ${badge.bgColor} ${badge.textColor} ${badge.borderColor} border ${sizeClasses[size]} font-medium`}
      title={status.message}
    >
      <span>{badge.icon}</span>
      {showText && <span>{badge.text}</span>}
    </div>
  )
}

export default NodeStatusBadge

