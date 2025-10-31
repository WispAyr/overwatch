import { BaseEdge, EdgeLabelRenderer, getStraightPath } from '@xyflow/react'
import { useState, useEffect } from 'react'

// Specialized edge for raw data outputs (JSON, stats, etc.)
export default function DataEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}) {
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  })

  const [dataCount, setDataCount] = useState(0)
  const [isTransmitting, setIsTransmitting] = useState(false)

  // Simulate data packets
  useEffect(() => {
    const interval = setInterval(() => {
      const shouldTransmit = Math.random() > 0.5
      setIsTransmitting(shouldTransmit)
      if (shouldTransmit) {
        setDataCount(prev => prev + 1)
      }
    }, 1500)
    return () => clearInterval(interval)
  }, [])

  return (
    <>
      {/* Dotted line for data connections */}
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: 2,
          stroke: '#6366f1',
          strokeDasharray: '8,4',
          strokeDashoffset: isTransmitting ? '0' : '12',
          animation: isTransmitting ? 'dash 1s linear infinite' : 'none',
        }}
      />

      {/* Packet animation */}
      {isTransmitting && (
        <circle r="3" fill="#6366f1">
          <animateMotion
            dur="1s"
            repeatCount="1"
            path={edgePath}
          />
          <animate
            attributeName="opacity"
            values="1;0"
            dur="1s"
            repeatCount="1"
          />
        </circle>
      )}

      {/* Data packet counter */}
      {dataCount > 0 && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              fontSize: 9,
              pointerEvents: 'all',
            }}
            className="nodrag nopan bg-indigo-900/80 border border-indigo-600 rounded-full px-2 py-0.5 text-xs font-mono text-indigo-200"
          >
            {dataCount}
          </div>
        </EdgeLabelRenderer>
      )}

      <style>{`
        @keyframes dash {
          to {
            stroke-dashoffset: 0;
          }
        }
      `}</style>
    </>
  )
}


