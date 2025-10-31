/**
 * Workflow Validation Dialog
 * Shows validation results before deploying a workflow
 */
import React, { useState } from 'react'
import { getSeverityColor } from '../utils/validateWorkflow'

const ValidationDialog = ({ 
  validationResult, 
  onClose, 
  onDeploy, 
  onFix,
  onAutoFix 
}) => {
  const [showDetails, setShowDetails] = useState(true)
  const [activeTab, setActiveTab] = useState('issues')

  if (!validationResult) return null

  const { valid, canDeploy, shouldWarn, issues, warnings, summary } = validationResult

  // Group issues by category
  const groupedIssues = issues.reduce((acc, issue) => {
    const cat = issue.category || 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(issue)
    return acc
  }, {})

  const groupedWarnings = warnings.reduce((acc, warning) => {
    const cat = warning.category || 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(warning)
    return acc
  }, {})

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">
              {canDeploy ? (shouldWarn ? '⚠️' : '✅') : '🚨'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                {canDeploy 
                  ? (shouldWarn ? 'Workflow Ready (with warnings)' : 'Workflow Ready')
                  : 'Workflow Has Issues'
                }
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {summary.critical > 0 && `${summary.critical} critical issue${summary.critical > 1 ? 's' : ''} `}
                {summary.high > 0 && `${summary.high} high priority issue${summary.high > 1 ? 's' : ''} `}
                {summary.warnings > 0 && `${summary.warnings} warning${summary.warnings > 1 ? 's' : ''}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Summary Stats */}
        <div className="px-6 py-3 bg-gray-800/50 border-b border-gray-800 grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-400">{summary.critical}</div>
            <div className="text-xs text-gray-400">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-400">{summary.high}</div>
            <div className="text-xs text-gray-400">High</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{summary.warnings}</div>
            <div className="text-xs text-gray-400">Warnings</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{canDeploy ? '✓' : '✗'}</div>
            <div className="text-xs text-gray-400">Can Deploy</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-3 flex gap-4 border-b border-gray-800">
          <button
            onClick={() => setActiveTab('issues')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'issues'
                ? 'border-red-500 text-red-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Issues ({issues.length})
          </button>
          <button
            onClick={() => setActiveTab('warnings')}
            className={`pb-3 px-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'warnings'
                ? 'border-yellow-500 text-yellow-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Warnings ({warnings.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'issues' && (
            <div className="space-y-4">
              {issues.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">✅</div>
                  <div className="font-medium">No issues found</div>
                  <div className="text-sm mt-1">Your workflow is ready to deploy</div>
                </div>
              ) : (
                Object.entries(groupedIssues).map(([category, categoryIssues]) => (
                  <div key={category}>
                    <h3 className="text-sm font-semibold text-gray-300 mb-2 capitalize">
                      {category} ({categoryIssues.length})
                    </h3>
                    <div className="space-y-2">
                      {categoryIssues.map((issue, idx) => (
                        <IssueCard 
                          key={idx} 
                          issue={issue} 
                          onFix={onFix}
                          onAutoFix={onAutoFix}
                        />
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'warnings' && (
            <div className="space-y-4">
              {warnings.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">✨</div>
                  <div className="font-medium">No warnings</div>
                  <div className="text-sm mt-1">Workflow looks great!</div>
                </div>
              ) : (
                Object.entries(groupedWarnings).map(([category, categoryWarnings]) => (
                  <div key={category}>
                    <h3 className="text-sm font-semibold text-gray-300 mb-2 capitalize">
                      {category} ({categoryWarnings.length})
                    </h3>
                    <div className="space-y-2">
                      {categoryWarnings.map((warning, idx) => (
                        <IssueCard key={idx} issue={warning} />
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between bg-gray-800/30">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>

          <div className="flex gap-3">
            {!canDeploy && issues.some(i => i.canAutoFix) && (
              <button
                onClick={() => {
                  const fixableIssues = issues.filter(i => i.canAutoFix)
                  fixableIssues.forEach(issue => onAutoFix?.(issue))
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
              >
                🔧 Auto-Fix Dependencies
              </button>
            )}

            <button
              onClick={onDeploy}
              disabled={!canDeploy}
              className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                canDeploy
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              {canDeploy 
                ? (shouldWarn ? '⚠️ Deploy Anyway' : '✅ Deploy Workflow')
                : '🚫 Cannot Deploy'
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Individual Issue Card
 */
const IssueCard = ({ issue, onFix, onAutoFix }) => {
  const [expanded, setExpanded] = useState(false)
  const severity = getSeverityColor(issue.severity)

  return (
    <div className={`border rounded-lg overflow-hidden ${severity.border} ${severity.bg}`}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="text-xl">{severity.icon}</div>
          <div className="flex-1 min-w-0">
            {/* Issue Header */}
            <div className="flex items-start justify-between gap-2 mb-1">
              <div>
                <div className={`font-semibold ${severity.text}`}>
                  {issue.message}
                </div>
                {issue.nodeName && (
                  <div className="text-xs text-gray-600 mt-0.5">
                    Node: {issue.nodeName}
                  </div>
                )}
              </div>
              {(issue.setupSteps?.length > 0 || issue.alternative) && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  {expanded ? 'Hide' : 'Show'} Details
                </button>
              )}
            </div>

            {/* Issue Description */}
            <div className="text-sm text-gray-700 mb-2">
              {issue.description}
            </div>

            {/* Expanded Details */}
            {expanded && (
              <div className="mt-3 space-y-2">
                {/* Dependencies */}
                {issue.dependencies && issue.dependencies.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-700 mb-1">
                      Required Dependencies:
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {issue.dependencies.map(dep => (
                        <span
                          key={dep}
                          className="inline-block bg-white border border-gray-400 rounded px-2 py-0.5 text-xs font-mono"
                        >
                          {dep}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Setup Steps */}
                {issue.setupSteps && issue.setupSteps.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-700 mb-1">
                      Setup Steps:
                    </div>
                    <ul className="space-y-1">
                      {issue.setupSteps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs">
                          <span className="text-blue-600 font-bold">{idx + 1}.</span>
                          <span className="flex-1 text-gray-700">
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

                {/* Alternative */}
                {issue.alternative && (
                  <div className="bg-blue-50 border border-blue-200 rounded p-2">
                    <div className="text-xs font-semibold text-blue-800 mb-1">
                      💡 Alternative:
                    </div>
                    <div className="text-xs text-blue-700">
                      {issue.alternative}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Fix Action */}
            <div className="mt-2 text-xs text-gray-600">
              <span className="font-semibold">Fix:</span> {issue.fix}
            </div>

            {/* Action Buttons */}
            {issue.canAutoFix && onAutoFix && (
              <div className="mt-3">
                <button
                  onClick={() => onAutoFix(issue)}
                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded font-medium"
                >
                  🔧 Auto-Install Dependencies
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ValidationDialog

