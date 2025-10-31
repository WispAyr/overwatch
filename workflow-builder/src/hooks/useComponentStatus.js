/**
 * Hook to fetch and manage component status
 * Provides real-time node status, dependencies, and setup requirements
 */
import { useState, useEffect } from 'react'
import { apiBaseUrl } from '../config'

export const useComponentStatus = () => {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true)
        const response = await fetch(`${apiBaseUrl}/api/component-status/status`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch component status: ${response.statusText}`)
        }
        
        const data = await response.json()
        setStatus(data)
        setError(null)
      } catch (err) {
        console.error('Error fetching component status:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()

    // Refresh every 5 minutes to catch dependency changes
    const interval = setInterval(fetchStatus, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [])

  /**
   * Get status for a specific model
   */
  const getModelStatus = (modelId) => {
    if (!status?.models) return null
    return status.models[modelId]
  }

  /**
   * Get status for a specific input type
   */
  const getInputStatus = (inputType) => {
    if (!status?.inputs) return null
    return status.inputs[inputType]
  }

  /**
   * Get status for a specific processing node
   */
  const getProcessingStatus = (nodeType) => {
    if (!status?.processing) return null
    return status.processing[nodeType]
  }

  /**
   * Get status for a specific action
   */
  const getActionStatus = (actionType) => {
    if (!status?.actions) return null
    return status.actions[actionType]
  }

  /**
   * Get status for any node type
   */
  const getNodeStatus = (nodeType, nodeId) => {
    if (!status) return null

    // Try each category
    const categories = ['models', 'inputs', 'processing', 'actions', 'outputs', 'advanced', 'drone']
    
    for (const category of categories) {
      const categoryData = status[category]
      if (!categoryData) continue

      // Check by nodeId first (for models)
      if (nodeId && categoryData[nodeId]) {
        return categoryData[nodeId]
      }

      // Check by nodeType
      if (categoryData[nodeType]) {
        return categoryData[nodeType]
      }
    }

    return null
  }

  /**
   * Check if a node is ready to use
   */
  const isNodeReady = (nodeType, nodeId) => {
    const nodeStatus = getNodeStatus(nodeType, nodeId)
    if (!nodeStatus) return true // Unknown nodes assumed ready

    return nodeStatus.status === 'ready' && nodeStatus.dependenciesMet !== false
  }

  /**
   * Get badge configuration
   */
  const getBadgeConfig = (badge) => {
    const badges = {
      production: {
        icon: '✅',
        color: 'green',
        bgColor: 'bg-green-900/30',
        textColor: 'text-green-400',
        borderColor: 'border-green-700/50',
        text: 'Ready'
      },
      needsConfig: {
        icon: '🔧',
        color: 'yellow',
        bgColor: 'bg-yellow-900/30',
        textColor: 'text-yellow-400',
        borderColor: 'border-yellow-700/50',
        text: 'Setup Required'
      },
      beta: {
        icon: '🚧',
        color: 'orange',
        bgColor: 'bg-orange-900/30',
        textColor: 'text-orange-400',
        borderColor: 'border-orange-700/50',
        text: 'Beta'
      },
      notImplemented: {
        icon: '📋',
        color: 'gray',
        bgColor: 'bg-gray-800/50',
        textColor: 'text-gray-400',
        borderColor: 'border-gray-600/50',
        text: 'Coming Soon'
      }
    }

    return badges[badge] || badges.production
  }

  /**
   * Get all models grouped by status
   */
  const getModelsByStatus = () => {
    if (!status?.models) return { ready: [], needsConfig: [], beta: [], notImplemented: [] }

    const grouped = {
      ready: [],
      needsConfig: [],
      beta: [],
      notImplemented: []
    }

    Object.entries(status.models).forEach(([id, modelStatus]) => {
      const statusKey = modelStatus.status === 'ready' ? 'ready' : 
                       modelStatus.status === 'needsConfig' ? 'needsConfig' :
                       modelStatus.status === 'beta' ? 'beta' : 'notImplemented'
      
      grouped[statusKey].push({ id, ...modelStatus })
    })

    return grouped
  }

  return {
    status,
    loading,
    error,
    getModelStatus,
    getInputStatus,
    getProcessingStatus,
    getActionStatus,
    getNodeStatus,
    isNodeReady,
    getBadgeConfig,
    getModelsByStatus,
    dependencies: status?.dependencies || {},
    summary: status?.summary || {}
  }
}

export default useComponentStatus

