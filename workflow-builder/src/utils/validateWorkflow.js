/**
 * Workflow Validation Utility
 * Validates workflows before deployment to catch issues early
 */

/**
 * Validate a workflow for deployment
 * Checks for missing dependencies, invalid configurations, and common issues
 * 
 * @param {Array} nodes - Workflow nodes
 * @param {Array} edges - Workflow edges
 * @param {Object} componentStatus - Status from useComponentStatus hook
 * @returns {Object} Validation result with issues array
 */
export const validateWorkflow = (nodes, edges, componentStatus) => {
  const issues = []
  const warnings = []

  // Check for empty workflow
  if (!nodes || nodes.length === 0) {
    issues.push({
      type: 'error',
      severity: 'critical',
      category: 'workflow',
      message: 'Workflow is empty',
      description: 'Add at least one node to create a workflow',
      fix: 'Drag nodes from the sidebar to build your workflow'
    })
    return { valid: false, issues, warnings }
  }

  // Check for disconnected nodes
  const connectedNodeIds = new Set()
  edges.forEach(edge => {
    connectedNodeIds.add(edge.source)
    connectedNodeIds.add(edge.target)
  })

  nodes.forEach(node => {
    if (!connectedNodeIds.has(node.id) && node.type !== 'default') {
      warnings.push({
        type: 'warning',
        severity: 'low',
        category: 'connectivity',
        nodeId: node.id,
        nodeName: node.data?.label || node.id,
        message: `Node "${node.data?.label || node.id}" is not connected`,
        description: 'Disconnected nodes will not be executed',
        fix: 'Connect this node to other nodes or remove it'
      })
    }
  })

  // Check for input sources
  const inputTypes = ['camera', 'videoInput', 'youtube', 'droneInput']
  const hasInput = nodes.some(node => inputTypes.includes(node.type))
  
  if (!hasInput) {
    issues.push({
      type: 'error',
      severity: 'high',
      category: 'workflow',
      message: 'No input source defined',
      description: 'Workflows need at least one input source (camera, video, etc.)',
      fix: 'Add a Camera, Video Input, or YouTube node from the sidebar'
    })
  }

  // Check each node for dependency issues
  nodes.forEach(node => {
    const nodeType = node.type
    const nodeId = node.data?.modelId || node.data?.actionType || nodeType
    const nodeName = node.data?.label || node.data?.cameraName || nodeId
    
    // Skip default/welcome nodes
    if (nodeType === 'default') return

    // Get status from component status
    const status = getNodeStatusFromComponent(nodeType, nodeId, componentStatus)

    if (status) {
      // Check for not implemented nodes
      if (status.status === 'notImplemented') {
        issues.push({
          type: 'error',
          severity: 'critical',
          category: 'implementation',
          nodeId: node.id,
          nodeName,
          message: `"${nodeName}" is not yet implemented`,
          description: status.message,
          fix: 'Remove this node or use an alternative',
          alternative: getAlternative(nodeId)
        })
      }

      // Check for missing dependencies
      if (status.status === 'needsConfig' && !status.dependenciesMet) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'dependencies',
          nodeId: node.id,
          nodeName,
          nodeType,
          nodeDataId: nodeId,
          message: `"${nodeName}" requires setup`,
          description: status.message,
          dependencies: status.dependencies || [],
          setupSteps: status.setupSteps || [],
          fix: 'Complete setup steps before deploying',
          canAutoFix: status.setupSteps?.some(step => step.startsWith('Install:'))
        })
      }

      // Check for beta nodes
      if (status.status === 'beta') {
        warnings.push({
          type: 'warning',
          severity: 'medium',
          category: 'stability',
          nodeId: node.id,
          nodeName,
          message: `"${nodeName}" is in beta`,
          description: status.message,
          fix: 'Use with caution - functionality may be incomplete'
        })
      }
    }

    // Validate node-specific configuration
    validateNodeConfiguration(node, issues, warnings)
  })

  // Check for cycles (circular dependencies)
  const cycles = detectCycles(nodes, edges)
  if (cycles.length > 0) {
    cycles.forEach(cycle => {
      warnings.push({
        type: 'warning',
        severity: 'medium',
        category: 'flow',
        message: 'Circular connection detected',
        description: `Nodes form a cycle: ${cycle.join(' → ')}`,
        fix: 'Remove or reorganize connections to avoid loops'
      })
    })
  }

  // Determine if workflow is valid
  const criticalIssues = issues.filter(i => i.severity === 'critical')
  const highIssues = issues.filter(i => i.severity === 'high')
  const valid = criticalIssues.length === 0

  return {
    valid,
    canDeploy: criticalIssues.length === 0,
    shouldWarn: highIssues.length > 0 || warnings.length > 0,
    issues,
    warnings,
    summary: {
      total: issues.length + warnings.length,
      critical: criticalIssues.length,
      high: highIssues.length,
      warnings: warnings.length
    }
  }
}

/**
 * Get node status from component status object
 */
const getNodeStatusFromComponent = (nodeType, nodeId, componentStatus) => {
  if (!componentStatus) return null

  const categories = ['models', 'inputs', 'processing', 'actions', 'outputs', 'advanced', 'drone']
  
  for (const category of categories) {
    const categoryData = componentStatus[category]
    if (!categoryData) continue

    if (nodeId && categoryData[nodeId]) {
      return categoryData[nodeId]
    }
    if (categoryData[nodeType]) {
      return categoryData[nodeType]
    }
  }

  return null
}

/**
 * Validate node-specific configuration
 */
const validateNodeConfiguration = (node, issues, warnings) => {
  const { type, data } = node

  switch (type) {
    case 'model':
      if (!data.modelId) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: data.label || 'Model',
          message: 'Model not selected',
          description: 'AI model node must have a model selected',
          fix: 'Configure the node and select a model'
        })
      }
      if (data.confidence !== undefined && (data.confidence < 0 || data.confidence > 1)) {
        warnings.push({
          type: 'warning',
          severity: 'low',
          category: 'configuration',
          nodeId: node.id,
          nodeName: data.label || 'Model',
          message: 'Invalid confidence threshold',
          description: `Confidence must be between 0 and 1, got ${data.confidence}`,
          fix: 'Set confidence between 0.0 and 1.0'
        })
      }
      break

    case 'camera':
      if (!data.cameraId) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: 'Camera',
          message: 'Camera not selected',
          description: 'Camera node must have a camera selected',
          fix: 'Configure the node and select a camera'
        })
      }
      break

    case 'zone':
      if (!data.polygon || data.polygon.length < 3) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: data.label || 'Zone',
          message: 'Invalid zone polygon',
          description: 'Zone must have at least 3 points',
          fix: 'Define a valid polygon with at least 3 coordinate pairs'
        })
      }
      break

    case 'action':
      if (!data.actionType) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: 'Action',
          message: 'Action type not selected',
          description: 'Action node must have an action type',
          fix: 'Configure the node and select an action type'
        })
      }
      // Validate action-specific config
      if (data.actionType === 'email' && !data.config?.to) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: data.label || 'Email',
          message: 'Email recipient not set',
          description: 'Email action requires a recipient address',
          fix: 'Configure the email recipient'
        })
      }
      if (data.actionType === 'webhook' && !data.config?.url) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: data.label || 'Webhook',
          message: 'Webhook URL not set',
          description: 'Webhook action requires a URL',
          fix: 'Configure the webhook URL'
        })
      }
      break

    case 'youtube':
      if (!data.youtubeUrl) {
        issues.push({
          type: 'error',
          severity: 'high',
          category: 'configuration',
          nodeId: node.id,
          nodeName: 'YouTube',
          message: 'YouTube URL not set',
          description: 'YouTube input requires a valid URL',
          fix: 'Configure the YouTube video URL'
        })
      }
      break
  }
}

/**
 * Detect cycles in workflow graph
 */
const detectCycles = (nodes, edges) => {
  const cycles = []
  const visited = new Set()
  const recStack = new Set()
  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  const dfs = (nodeId, path = []) => {
    if (recStack.has(nodeId)) {
      // Found a cycle
      const cycleStart = path.indexOf(nodeId)
      const cycle = path.slice(cycleStart).map(id => {
        const node = nodeMap.get(id)
        return node?.data?.label || id
      })
      cycles.push(cycle)
      return
    }

    if (visited.has(nodeId)) return

    visited.add(nodeId)
    recStack.add(nodeId)

    const outgoingEdges = edges.filter(e => e.source === nodeId)
    outgoingEdges.forEach(edge => {
      dfs(edge.target, [...path, nodeId])
    })

    recStack.delete(nodeId)
  }

  nodes.forEach(node => {
    if (!visited.has(node.id)) {
      dfs(node.id)
    }
  })

  return cycles
}

/**
 * Get alternative node for not implemented features
 */
const getAlternative = (nodeId) => {
  const alternatives = {
    'crowd-counter-v1': 'Use YOLOv8 person detection with zone counting',
    'age-gender-v1': 'Use face recognition with custom attributes',
    'vehicle-classifier-v1': 'Use YOLOv8 with vehicle classes (car=2, bus=5, truck=7)',
    'traffic-flow-v1': 'Use YOLOv8 tracking with line crossing detection',
    'fall-detector-v1': 'Use YOLOv8 pose estimation to detect falls',
    'loitering-detector-v1': 'Use object tracking with dwell time monitoring',
    'queue-management-v1': 'Use YOLOv8 person detection with zone counting'
  }

  return alternatives[nodeId] || 'Use YOLOv8 base models with custom training'
}

/**
 * Get severity color for UI
 */
export const getSeverityColor = (severity) => {
  const colors = {
    critical: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: '🚨' },
    high: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300', icon: '⚠️' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', icon: '⚡' },
    low: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300', icon: 'ℹ️' }
  }

  return colors[severity] || colors.low
}

export default validateWorkflow

