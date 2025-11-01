import { memo, useState, useRef, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';

export default memo(({ data, id }) => {
  const { setNodes } = useReactFlow()
  const [showPreview, setShowPreview] = useState(true)
  const [showConfig, setShowConfig] = useState(false)
  const [showBrowser, setShowBrowser] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [serverPath, setServerPath] = useState(null)
  const [fileType, setFileType] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [loop, setLoop] = useState(data.loop !== false)
  const [fps, setFps] = useState(data.fps || 30)
  const [playbackSpeed, setPlaybackSpeed] = useState(data.playbackSpeed || 1.0)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [skipSimilar, setSkipSimilar] = useState(data.skipSimilar || false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [workflowRunning, setWorkflowRunning] = useState(false)
  const [serverFiles, setServerFiles] = useState([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const videoRef = useRef(null)
  const fileInputRef = useRef(null)
  
  // Listen for workflow execution state via WebSocket
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/ws')
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        // Track workflow state
        if (message.type === 'workflow_started' || message.event_type === 'workflow_started') {
          setWorkflowRunning(true)
        } else if (message.type === 'workflow_stopped' || message.event_type === 'workflow_stopped') {
          setWorkflowRunning(false)
        }
      } catch (err) {
        // Ignore parse errors
      }
    }
    
    return () => ws.close()
  }, [])
  
  // Auto-play video when workflow starts
  useEffect(() => {
    if (videoRef.current && uploadedFile && fileType === 'video') {
      if (workflowRunning && !isPlaying) {
        videoRef.current.play()
        setIsPlaying(true)
      } else if (!workflowRunning && isPlaying) {
        videoRef.current.pause()
        setIsPlaying(false)
      }
    }
  }, [workflowRunning, uploadedFile, fileType])
  
  // Update node data in ReactFlow whenever config changes
  useEffect(() => {
    if (serverPath) {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === id) {
            return {
              ...node,
              data: {
                ...node.data,
                videoPath: serverPath,
                fps,
                loop,
                playbackSpeed,
                skipSimilar
              }
            }
          }
          return node
        })
      )
    }
  }, [serverPath, fps, loop, playbackSpeed, skipSimilar, id, setNodes]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Create blob URL for local preview
    const url = URL.createObjectURL(file)
    const type = file.type.startsWith('video/') ? 'video' : 'image'
    
    setUploadedFile(url)
    setFileType(type)
    setIsPlaying(false)
    setCurrentTime(0)
    setUploading(true)
    setUploadError(null)
    
    try {
      // Upload file to server
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('http://localhost:8000/api/uploads/video', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }
      
      const result = await response.json()
      console.log('✅ Upload successful:', result)
      
      // Store server path for backend processing
      setServerPath(result.path)
      setUploading(false)  // Clear uploading state immediately
      
    } catch (error) {
      console.error('❌ Upload error:', error)
      setUploadError(error.message)
      setUploading(false)  // Ensure uploading clears on error too
    }
  }

  const handlePlayPause = () => {
    if (!videoRef.current) return
    
    if (isPlaying) {
      videoRef.current.pause()
    } else {
      videoRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const loadServerFiles = async () => {
    setLoadingFiles(true)
    try {
      const response = await fetch('http://localhost:8000/api/uploads/list')
      const result = await response.json()
      if (result.status === 'success') {
        setServerFiles(result.files)
      }
    } catch (error) {
      console.error('Failed to load server files:', error)
    } finally {
      setLoadingFiles(false)
    }
  }

  // Load server files when browser is opened
  useEffect(() => {
    if (showBrowser && serverFiles.length === 0) {
      loadServerFiles()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showBrowser])

  const selectServerFile = (file) => {
    // Set the server path for backend processing
    setServerPath(file.path)
    
    // Create HTTP URL for browser preview
    const previewUrl = `http://localhost:8000/uploads/${file.filename}`
    setUploadedFile(previewUrl)
    
    // Determine file type
    setFileType(file.filename.match(/\.(mp4|mov|avi|webm)$/i) ? 'video' : 'image')
    setShowBrowser(false)
    setIsPlaying(false)
    setCurrentTime(0)
  }

  const deleteServerFile = async (filename) => {
    if (!confirm(`Delete ${filename}?`)) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/uploads/video/${filename}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        await loadServerFiles() // Refresh list
      }
    } catch (error) {
      console.error('Failed to delete file:', error)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  // Apply playback speed
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
      videoRef.current.playbackRate = playbackSpeed
    }
  }
  
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  useEffect(() => {
    return () => {
      if (uploadedFile) {
        URL.revokeObjectURL(uploadedFile)
      }
    }
  }, [uploadedFile])

  return (
    <NodeWrapper nodeId={id}>
    <div className="shadow-lg rounded-lg border-2 border-purple-500 bg-gray-900 min-w-[280px] max-w-[350px]">
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-purple-500"
        id="video-output"
      />
      
      {/* Header */}
      <div className="px-4 py-3 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🎬</span>
            <div className="font-bold text-sm text-purple-400">Video Input</div>
            {workflowRunning && isPlaying && (
              <div className="flex items-center space-x-1 text-xs">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-400">Playing</span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs px-2 py-1 bg-gray-800 rounded hover:bg-gray-700"
              title="Toggle preview"
            >
              👁️
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="text-gray-400 hover:text-white"
            >
              ⚙️
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {/* Upload/Browse Buttons */}
        <div className="mb-3 flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*,image/*"
            onChange={handleFileUpload}
            className="hidden"
            disabled={uploading}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex-1 px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm font-medium transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            {uploading ? '⏳ Uploading...' : '📤 Upload'}
          </button>
          <button
            onClick={() => setShowBrowser(!showBrowser)}
            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors"
            title="Browse server files"
          >
            📁
          </button>
        </div>
        
        {/* File Browser */}
        {showBrowser && (
          <div className="mb-3 p-3 bg-gray-950 rounded border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-300">Server Files</span>
              <button
                onClick={loadServerFiles}
                disabled={loadingFiles}
                className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded"
              >
                {loadingFiles ? '⏳' : '🔄'}
              </button>
            </div>
            
            <div className="max-h-48 overflow-y-auto space-y-1">
              {serverFiles.length === 0 ? (
                <div className="text-xs text-gray-500 text-center py-4">
                  No files uploaded yet
                </div>
              ) : (
                serverFiles.map((file) => (
                  <div
                    key={file.filename}
                    className="p-2 bg-gray-900 rounded hover:bg-gray-800 cursor-pointer group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0" onClick={() => selectServerFile(file)}>
                        <div className="text-xs font-medium text-gray-200 truncate">
                          {file.filename}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {formatBytes(file.size)} • {formatDate(file.modified)}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteServerFile(file.filename)
                        }}
                        className="ml-2 text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete file"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Upload Status */}
        {uploadError && (
          <div className="mb-3 p-2 bg-red-900 border border-red-700 rounded text-xs text-red-200">
            ❌ {uploadError}
          </div>
        )}
        {serverPath && !uploadError && (
          <div className="mb-3 p-2 bg-green-900 border border-green-700 rounded text-xs text-green-200">
            ✅ Ready: {serverPath.split('/').pop()}
          </div>
        )}

        {/* File Info */}
        {uploadedFile && (
          <div className="mb-3 p-2 bg-gray-950 rounded border border-gray-800">
            <div className="text-xs text-gray-400 flex justify-between items-center">
              <span>Type: {fileType === 'video' ? '🎥 Video' : '🖼️ Image'}</span>
              {fileType === 'video' && (
                <span className="text-purple-400">{playbackSpeed}x speed</span>
              )}
            </div>
            {fileType === 'video' && duration > 0 && (
              <div className="text-xs text-gray-500 mt-1">
                Duration: {formatTime(duration)}
              </div>
            )}
          </div>
        )}

        {/* Preview */}
        {showPreview && uploadedFile && (
          <div className="mb-3">
            <div className="relative bg-black rounded overflow-hidden border border-gray-800">
              {fileType === 'video' ? (
                <video
                  ref={videoRef}
                  src={uploadedFile}
                  className="w-full h-auto"
                  loop={loop}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onEnded={() => setIsPlaying(false)}
                />
              ) : (
                <img
                  src={uploadedFile}
                  alt="Uploaded"
                  className="w-full h-auto"
                />
              )}
            </div>

            {/* Video Controls */}
            {fileType === 'video' && (
              <div className="mt-2 space-y-2">
                {/* Progress Bar */}
                <div className="relative h-1 bg-gray-800 rounded overflow-hidden cursor-pointer"
                  onClick={(e) => {
                    if (videoRef.current && duration > 0) {
                      const rect = e.currentTarget.getBoundingClientRect()
                      const x = e.clientX - rect.left
                      const percent = x / rect.width
                      videoRef.current.currentTime = percent * duration
                    }
                  }}
                >
                  <div 
                    className="absolute h-full bg-purple-500 transition-all"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  />
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handlePlayPause}
                      className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs"
                    >
                      {isPlaying ? '⏸️ Pause' : '▶️ Play'}
                    </button>
                    <button
                      onClick={() => setLoop(!loop)}
                      className={`px-2 py-1 rounded text-xs ${
                        loop ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400'
                      }`}
                      title="Loop video"
                    >
                      🔁
                    </button>
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Configuration Panel */}
        {showConfig && uploadedFile && fileType === 'video' && (
          <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
            {/* Processing FPS */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Processing FPS: {fps}
              </label>
              <input
                type="range"
                min="1"
                max="60"
                value={fps}
                onChange={(e) => setFps(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>1 fps</span>
                <span>60 fps</span>
              </div>
            </div>
            
            {/* Playback Speed */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">
                Playback Speed: {playbackSpeed}x
              </label>
              <select
                value={playbackSpeed}
                onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                <option value="0.25">0.25x (Slow)</option>
                <option value="0.5">0.5x</option>
                <option value="0.75">0.75x</option>
                <option value="1.0">1.0x (Normal)</option>
                <option value="1.25">1.25x</option>
                <option value="1.5">1.5x</option>
                <option value="2.0">2.0x (Fast)</option>
              </select>
            </div>
            
            {/* Skip Similar */}
            <div>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={skipSimilar}
                  onChange={(e) => setSkipSimilar(e.target.checked)}
                  className="w-3 h-3"
                />
                <span className="text-xs text-gray-300">Skip similar frames</span>
              </label>
              <div className="text-[10px] text-gray-600 ml-5">
                Skip processing when scene doesn't change
              </div>
            </div>
          </div>
        )}

        {/* No File Uploaded */}
        {!uploadedFile && (
          <div className="text-center py-6 text-gray-600">
            <div className="text-3xl mb-2">📁</div>
            <div className="text-xs">Upload a video or image</div>
            <div className="text-[10px] text-gray-700 mt-2">
              For testing AI models
            </div>
          </div>
        )}

        {/* Processing Status */}
        {uploadedFile && (
          <div className="mt-3 p-2 bg-green-900/20 border border-green-500/30 rounded">
            <div className="text-xs text-green-400 flex items-center">
              <span className="mr-2">✓</span>
              <span>Ready to process</span>
            </div>
          </div>
        )}
      </div>
    </div>
    </NodeWrapper>
  )
})
