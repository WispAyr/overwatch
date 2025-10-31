import { memo, useState } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const [sampleRate, setSampleRate] = useState(data.sampleRate || 16000)
  const [channels, setChannels] = useState(data.channels || 1)
  const [format, setFormat] = useState(data.format || 'wav')
  const [bufferDuration, setBufferDuration] = useState(data.bufferDuration || 5)

  const updateData = (key, value) => {
    data[key] = value
  }

  const sampleRates = [8000, 16000, 22050, 44100, 48000]
  const formats = ['wav', 'mp3', 'flac', 'pcm']

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-pink-500 bg-gray-900 min-w-[280px]">
      <div className="px-4 py-3 bg-pink-950/30 border-b border-pink-800">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xl">🎵</span>
          <div className="font-bold text-sm text-pink-400">Audio Extractor</div>
        </div>
        <div className="text-[10px] text-pink-600">Extract audio from video streams</div>
      </div>

      <div className="p-4 space-y-3">
        {/* Sample Rate */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Sample Rate</label>
          <select
            value={sampleRate}
            onChange={(e) => {
              const value = parseInt(e.target.value)
              setSampleRate(value)
              updateData('sampleRate', value)
            }}
            className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
          >
            {sampleRates.map(rate => (
              <option key={rate} value={rate}>{rate} Hz</option>
            ))}
          </select>
        </div>

        {/* Channels */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Channels</label>
          <select
            value={channels}
            onChange={(e) => {
              const value = parseInt(e.target.value)
              setChannels(value)
              updateData('channels', value)
            }}
            className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
          >
            <option value={1}>Mono</option>
            <option value={2}>Stereo</option>
          </select>
        </div>

        {/* Format */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Audio Format</label>
          <select
            value={format}
            onChange={(e) => {
              setFormat(e.target.value)
              updateData('format', e.target.value)
            }}
            className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
          >
            {formats.map(fmt => (
              <option key={fmt} value={fmt}>{fmt.toUpperCase()}</option>
            ))}
          </select>
        </div>

        {/* Buffer Duration */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Buffer Duration (seconds)
          </label>
          <input
            type="number"
            min="1"
            max="60"
            value={bufferDuration}
            onChange={(e) => {
              const value = parseInt(e.target.value)
              setBufferDuration(value)
              updateData('bufferDuration', value)
            }}
            className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
          />
          <div className="text-[10px] text-gray-600 mt-1">
            Audio chunk size for processing
          </div>
        </div>

        {/* Status */}
        <div className="pt-2 border-t border-gray-800 text-xs text-gray-500">
          Output: {sampleRate}Hz, {channels}ch, {format}
        </div>
      </div>

        {/* Handles */}
        <Handle
          type="target"
          position={Position.Left}
          id="video-input"
          className="w-3 h-3 bg-blue-500"
          style={{ top: '25%' }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="audio-output"
          className="w-3 h-3 bg-pink-500"
        />
      </div>
    </NodeWrapper>
  )
})

