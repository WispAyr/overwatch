/**
 * Setup Warning Component
 * Shows setup requirements and installation steps for nodes
 */
import React, { useState } from 'react'
import useComponentStatus from '../hooks/useComponentStatus'

const SetupWarning = ({ nodeType, nodeId, compact = false }) => {
  const { getNodeStatus } = useComponentStatus()
  const [showDetails, setShowDetails] = useState(!compact)

  const status = getNodeStatus(nodeType, nodeId)
  
  if (!status) {
    return null
  }

  // Only show if dependencies not met or setup steps exist
  if (status.dependenciesMet && (!status.setupSteps || status.setupSteps.length === 0)) {
    return null
  }

  const isWarning = status.status === 'needsConfig'
  const isBeta = status.status === 'beta'
  const isNotImplemented = status.status === 'notImplemented'

  if (isNotImplemented) {
    return (
      <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 mt-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">📋</span>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-800 mb-1">Coming Soon</h4>
            <p className="text-sm text-gray-600 mb-2">{status.message}</p>
            <div className="text-xs text-gray-500">
              This feature is planned but not yet implemented. Check back soon!
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`border rounded-lg p-4 mt-4 ${
      isBeta ? 'bg-orange-50 border-orange-300' : 'bg-yellow-50 border-yellow-300'
    }`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{isBeta ? '🚧' : '🔧'}</span>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-gray-800">
              {isBeta ? 'Beta Feature' : 'Setup Required'}
            </h4>
            {compact && (
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {showDetails ? 'Hide' : 'Show'} Details
              </button>
            )}
          </div>

          {showDetails && (
            <>
              {status.message && (
                <p className="text-sm text-gray-700 mb-3">{status.message}</p>
              )}

              {status.dependencies && status.dependencies.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-gray-700 mb-1">
                    Required Dependencies:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {status.dependencies.map(dep => (
                      <span
                        key={dep}
                        className="inline-block bg-white border border-gray-300 rounded px-2 py-0.5 text-xs font-mono"
                      >
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {status.setupSteps && status.setupSteps.length > 0 && (
                <div className="space-y-1">
                  <div className="text-xs font-semibold text-gray-700 mb-1">
                    Setup Steps:
                  </div>
                  <ul className="space-y-1">
                    {status.setupSteps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                        <span className="text-blue-600 font-bold">{idx + 1}.</span>
                        <span className="flex-1">
                          {step.startsWith('Install:') ? (
                            <code className="bg-gray-800 text-green-400 px-1.5 py-0.5 rounded font-mono text-xs">
                              {step.replace('Install: ', '')}
                            </code>
                          ) : (
                            step
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => window.open('/docs/NODE_STATUS_REPORT.md', '_blank')}
                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
                >
                  📚 Documentation
                </button>
                {status.setupSteps && status.setupSteps.some(s => s.startsWith('Install:')) && (
                  <button
                    onClick={() => {
                      const installCmd = status.setupSteps
                        .find(s => s.startsWith('Install:'))
                        ?.replace('Install: ', '')
                      if (installCmd) {
                        navigator.clipboard.writeText(installCmd)
                        alert('Install command copied to clipboard!')
                      }
                    }}
                    className="text-xs bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded"
                  >
                    📋 Copy Install Command
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default SetupWarning

