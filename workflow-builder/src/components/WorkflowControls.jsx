import React, { useState } from 'react'

const WorkflowControls = ({ onSave, onClear, onExecute, nodeCount, edgeCount, isExecuting }) => {
  return (
    <div className="bg-gray-900/90 backdrop-blur-sm border border-gray-800 rounded-lg p-4">
      <div className="flex items-center space-x-4 mb-3">
        <div className="text-sm">
          <span className="text-gray-400">Nodes:</span>{' '}
          <span className="font-medium">{nodeCount}</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">Connections:</span>{' '}
          <span className="font-medium">{edgeCount}</span>
        </div>
        {isExecuting && (
          <div className="text-sm flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-400 font-medium">Running</span>
          </div>
        )}
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={onExecute}
          disabled={nodeCount === 0}
          className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
            isExecuting
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-green-600 hover:bg-green-700 text-white disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed'
          }`}
        >
          {isExecuting ? '⏹ Stop' : '▶️ Execute'}
        </button>
        <button
          onClick={onSave}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
        >
          💾 Save
        </button>
        <button
          onClick={onClear}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded text-sm font-medium transition-colors"
        >
          🗑️ Clear
        </button>
      </div>
    </div>
  )
}

export default WorkflowControls

