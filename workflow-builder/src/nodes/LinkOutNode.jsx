import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  return (
    <div className="shadow-lg rounded-lg border-2 border-purple-500 bg-gray-900 min-w-[180px]">
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-purple-500"
        id="link-input"
      />
      
      <div className="px-4 py-3">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xl">📤</span>
          <div className="font-bold text-sm text-purple-400">Link Out</div>
        </div>
        
        <div className="text-xs text-gray-400">
          {data.linkName || 'Unnamed Link'}
        </div>
      </div>
    </div>
  )
})


