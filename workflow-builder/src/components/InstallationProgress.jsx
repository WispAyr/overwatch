/**
 * Installation Progress Tracker
 * Shows real-time progress of package installations
 */
import React, { useState, useEffect } from 'react'
import { apiBaseUrl } from '../config'

const InstallationProgress = ({ installId, onComplete, onError }) => {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!installId) return

    // Poll for status updates
    const pollStatus = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/system/install-status/${installId}`)
        if (!response.ok) throw new Error('Failed to fetch status')

        const data = await response.json()
        setStatus(data)
        setLoading(false)

        // Check if complete
        if (data.status === 'completed') {
          onComplete?.(data)
        } else if (data.status === 'failed') {
          onError?.(data.error)
        }
      } catch (err) {
        console.error('Failed to fetch installation status:', err)
        setLoading(false)
      }
    }

    // Initial fetch
    pollStatus()

    // Poll every 2 seconds while installing
    const interval = setInterval(() => {
      if (status?.status === 'installing') {
        pollStatus()
      } else {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [installId, status?.status, onComplete, onError])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <div className="animate-spin">⏳</div>
        <span>Initializing installation...</span>
      </div>
    )
  }

  if (!status) return null

  return (
    <div className="space-y-3">
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="text-xl">
            {status.status === 'installing' && '⏳'}
            {status.status === 'completed' && '✅'}
            {status.status === 'failed' && '❌'}
          </div>
          <div>
            <div className="font-medium text-white">
              {status.status === 'installing' && `Installing ${status.package}...`}
              {status.status === 'completed' && `${status.package} installed successfully`}
              {status.status === 'failed' && `Installation of ${status.package} failed`}
            </div>
            <div className="text-xs text-gray-400">
              {status.status === 'installing' && 'This may take a few minutes'}
            </div>
          </div>
        </div>

        {status.progress !== undefined && (
          <div className="text-sm font-medium text-gray-300">
            {status.progress}%
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {status.status === 'installing' && (
        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${status.progress || 0}%` }}
          >
            <div className="w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
          </div>
        </div>
      )}

      {/* Output Log */}
      {status.output && status.output.length > 0 && (
        <details className="bg-gray-800 border border-gray-700 rounded">
          <summary className="px-3 py-2 text-sm text-gray-400 cursor-pointer hover:text-gray-300">
            📝 Installation Log ({status.output.length} lines)
          </summary>
          <div className="px-3 py-2 max-h-40 overflow-y-auto border-t border-gray-700">
            <pre className="text-xs text-gray-400 font-mono">
              {status.output.slice(-20).join('\n')}
            </pre>
          </div>
        </details>
      )}

      {/* Error Message */}
      {status.error && (
        <div className="bg-red-900/30 border border-red-700 rounded p-3">
          <div className="font-semibold text-red-300 mb-1">Error:</div>
          <div className="text-sm text-red-200">{status.error}</div>
        </div>
      )}

      {/* Success Actions */}
      {status.status === 'completed' && (
        <div className="bg-green-900/30 border border-green-700 rounded p-3">
          <div className="text-sm text-green-200">
            ✓ Package installed successfully. The page will refresh to update node status.
          </div>
        </div>
      )}
    </div>
  )
}

export default InstallationProgress

