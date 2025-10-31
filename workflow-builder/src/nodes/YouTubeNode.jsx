import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

const QUALITY_OPTIONS = [
  { value: 'best', label: 'Best (Auto)', description: 'Highest available quality' },
  { value: '1080p', label: '1080p (Full HD)', description: '1920x1080' },
  { value: '720p', label: '720p (HD)', description: '1280x720' },
  { value: '480p', label: '480p (SD)', description: '854x480' },
  { value: '360p', label: '360p', description: '640x360' },
  { value: 'worst', label: 'Lowest', description: 'Lowest quality (fastest)' },
];

export default memo(({ data, id }) => {
  const [youtubeUrl, setYoutubeUrl] = useState(data.youtubeUrl || '')
  const [quality, setQuality] = useState(data.quality || 'best')
  const [fps, setFps] = useState(data.fps || 10)
  const [extractAudio, setExtractAudio] = useState(data.extractAudio || false)
  const [showConfig, setShowConfig] = useState(false)
  const [isValidUrl, setIsValidUrl] = useState(false)
  const [videoId, setVideoId] = useState('')

  // Update parent data
  useEffect(() => {
    if (data.onChange) {
      data.onChange({
        youtubeUrl,
        quality,
        fps,
        extractAudio
      });
    }
  }, [youtubeUrl, quality, fps, extractAudio]);

  // Validate and extract video ID
  useEffect(() => {
    if (!youtubeUrl) {
      setIsValidUrl(false)
      setVideoId('')
      return
    }

    try {
      const url = new URL(youtubeUrl)
      let id = ''
      
      if (url.hostname.includes('youtube.com')) {
        id = url.searchParams.get('v')
      } else if (url.hostname.includes('youtu.be')) {
        id = url.pathname.slice(1)
      }
      
      setVideoId(id)
      setIsValidUrl(!!id)
    } catch {
      setIsValidUrl(false)
      setVideoId('')
    }
  }, [youtubeUrl])

  const getThumbnailUrl = () => {
    if (!videoId) return null
    return `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
  }

  return (
    <NodeWrapper nodeId={id}>
    <div className="shadow-lg rounded-lg border-2 border-red-500 bg-gray-900 min-w-[280px] max-w-[350px]">
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-red-500"
        id="video-output"
      />
      
      {/* Thumbnail Preview */}
      {isValidUrl && videoId && (
        <div className="relative bg-black rounded-t-lg overflow-hidden" style={{ height: '135px' }}>
          <img
            src={getThumbnailUrl()}
            alt="YouTube Thumbnail"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <div className="text-6xl text-white/90">▶️</div>
          </div>
          <div className="absolute top-2 right-2 px-2 py-1 bg-red-600 rounded text-xs text-white font-bold">
            LIVE
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">▶️</span>
            <div className="font-bold text-sm text-red-400">YouTube Stream</div>
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-gray-400 hover:text-white"
          >
            ⚙️
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {/* URL Input */}
        <div className="mb-3">
          <label className="text-xs text-gray-400 block mb-1">YouTube URL</label>
          <input
            type="url"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://youtube.com/watch?v=..."
            className={`w-full px-2 py-1.5 bg-gray-800 border rounded text-xs text-white font-mono ${
              youtubeUrl && !isValidUrl ? 'border-red-500' : 'border-gray-700'
            }`}
          />
          {youtubeUrl && !isValidUrl && (
            <div className="text-[10px] text-red-400 mt-1">Invalid YouTube URL</div>
          )}
          {isValidUrl && (
            <div className="text-[10px] text-green-400 mt-1">✓ Valid URL</div>
          )}
        </div>
        
        {/* Configuration Panel */}
        {showConfig && (
          <div className="space-y-3 pt-3 border-t border-gray-700">
            {/* Quality Selection */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">Video Quality</label>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                {QUALITY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <div className="text-[10px] text-gray-600 mt-1">
                {QUALITY_OPTIONS.find(o => o.value === quality)?.description}
              </div>
            </div>
            
            {/* Processing FPS */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Processing FPS: {fps}
              </label>
              <input
                type="range"
                min="1"
                max="30"
                value={fps}
                onChange={(e) => setFps(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>1 fps</span>
                <span>30 fps</span>
              </div>
            </div>
            
            {/* Extract Audio */}
            <div>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={extractAudio}
                  onChange={(e) => setExtractAudio(e.target.checked)}
                  className="w-3 h-3"
                />
                <span className="text-xs text-gray-300">Also extract audio</span>
              </label>
              <div className="text-[10px] text-gray-600 ml-5">
                Enable for audio AI analysis
              </div>
            </div>
            
            {/* Summary */}
            <div className="pt-2 border-t border-gray-700">
              <div className="text-[10px] text-gray-500 space-y-0.5">
                <div>🎬 Quality: {quality}</div>
                <div>⚡ Processing: {fps} fps</div>
                <div>🎵 Audio: {extractAudio ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>
        )}

        {/* No URL */}
        {!youtubeUrl && (
          <div className="text-center py-4 text-gray-600">
            <div className="text-2xl mb-2">▶️</div>
            <div className="text-xs">Enter a YouTube URL</div>
            <div className="text-[10px] text-gray-700 mt-1">
              Supports live streams & videos
            </div>
          </div>
        )}
        
        {/* Status */}
        {isValidUrl && (
          <div className="mt-3 p-2 bg-green-900/20 border border-green-500/30 rounded">
            <div className="text-xs text-green-400 flex items-center">
              <span className="mr-2">✓</span>
              <span>Ready to stream</span>
            </div>
          </div>
        )}
      </div>
    </div>
    </NodeWrapper>
  )
})
