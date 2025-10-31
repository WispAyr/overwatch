import { useState } from 'react'

export default function DisplayModeToggle({ onToggle, isDisplayMode }) {
  return (
    <button
      onClick={onToggle}
      className={`px-4 py-2 rounded-lg border transition-all ${
        isDisplayMode
          ? 'bg-blue-600 border-blue-500 text-white'
          : 'bg-gray-900 border-gray-700 text-gray-300 hover:border-gray-500'
      }`}
      title={isDisplayMode ? 'Exit Display Mode' : 'Enter Display Mode'}
    >
      <div className="flex items-center space-x-2">
        <span>{isDisplayMode ? '✏️' : '📺'}</span>
        <span className="text-sm font-medium">
          {isDisplayMode ? 'Edit Mode' : 'Display Mode'}
        </span>
      </div>
    </button>
  )
}


