import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@xyflow/react'
import { useState, useEffect } from 'react'

export default function AnimatedEdge({
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
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const [flowRate, setFlowRate] = useState(0)
  const [isActive, setIsActive] = useState(false)

  // Simulate data flow (would come from WebSocket in production)
  useEffect(() => {
    const interval = setInterval(() => {
      const shouldActivate = Math.random() > 0.3
      setIsActive(shouldActivate)
      if (shouldActivate) {
        setFlowRate(Math.floor(Math.random() * 30) + 1) // 1-30 fps
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  // Determine edge color based on data type
  const getEdgeColor = () => {
    if (data?.type === 'video') return '#3b82f6' // blue
    if (data?.type === 'detections') return '#10b981' // green
    if (data?.type === 'events') return '#f59e0b' // orange
    if (data?.type === 'zones') return '#8b5cf6' // purple
    return '#6b7280' // gray default
  }

  const edgeColor = getEdgeColor()

  return (
    <>
      {/* Base edge path */}
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: isActive ? 3 : 2,
          stroke: isActive ? edgeColor : '#4b5563',
          strokeDasharray: isActive ? '0' : '5,5',
          transition: 'all 0.3s ease',
        }}
      />
      
      {/* Animated pulse effect when active */}
      {isActive && (
        <>
          <path
            d={edgePath}
            fill="none"
            stroke={edgeColor}
            strokeWidth="3"
            strokeOpacity="0.4"
            className="animate-pulse"
          />
          
          {/* Flow particles */}
          <circle r="4" fill={edgeColor} className="opacity-80">
            <animateMotion
              dur="1.5s"
              repeatCount="indefinite"
              path={edgePath}
            />
          </circle>
          <circle r="4" fill={edgeColor} className="opacity-60">
            <animateMotion
              dur="1.5s"
              repeatCount="indefinite"
              path={edgePath}
              begin="0.5s"
            />
          </circle>
          <circle r="4" fill={edgeColor} className="opacity-40">
            <animateMotion
              dur="1.5s"
              repeatCount="indefinite"
              path={edgePath}
              begin="1s"
            />
          </circle>
        </>
      )}

      {/* Edge label showing flow rate */}
      {isActive && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              fontSize: 10,
              pointerEvents: 'all',
            }}
            className="nodrag nopan bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono"
          >
            <span style={{ color: edgeColor }}>⚡ {flowRate} fps</span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}


