import { memo, useState } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [showConfig, setShowConfig] = useState(false)
  
  return (
    <div className="shadow-lg rounded-lg border-2 border-red-500 bg-gray-900 min-w-[200px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-red-500"
        id="error-input"
      />
      
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🚨</span>
            <div className="font-bold text-sm text-red-400">Catch Error</div>
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-gray-400 hover:text-white text-xs"
          >
            ⚙️
          </button>
        </div>
        
        <div className="text-xs text-gray-400">
          {data.scope === 'specific' ? 'Specific Nodes' : 'All Errors'}
        </div>
        
        {showConfig && data.scope === 'specific' && data.nodeIds && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <div className="text-xs text-gray-500 mb-1">Watching:</div>
            <div className="text-xs text-gray-400">
              {data.nodeIds.length} node(s)
            </div>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-red-500"
        id="handled-output"
      />
    </div>
  )
})


