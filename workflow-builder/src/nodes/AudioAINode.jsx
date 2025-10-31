import { memo, useState, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import NodeWrapper from '../components/NodeWrapper';
import { apiBaseUrl } from '../config'

export default memo(({ data, id }) => {
  const [audioModels, setAudioModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(data.modelId || '')
  const [modelName, setModelName] = useState(data.modelName || '')
  const [modelType, setModelType] = useState(data.modelType || 'transcription')
  const [language, setLanguage] = useState(data.language || 'auto')
  const [confidence, setConfidence] = useState(data.confidence || 0.7)
  const [detectKeywords, setDetectKeywords] = useState(data.detectKeywords || [])
  const [keywordInput, setKeywordInput] = useState('')

  useEffect(() => {
    loadAudioModels()
  }, [])

  const loadAudioModels = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/workflow-components/audio-models`)
      if (response.ok) {
        const data = await response.json()
        setAudioModels(data.models || getDefaultModels())
      } else {
        setAudioModels(getDefaultModels())
      }
    } catch (error) {
      console.error('Failed to load audio models:', error)
      setAudioModels(getDefaultModels())
    }
  }

  const getDefaultModels = () => [
    { id: 'whisper-tiny', name: 'Whisper Tiny', type: 'transcription', speed: 'very fast' },
    { id: 'whisper-base', name: 'Whisper Base', type: 'transcription', speed: 'fast' },
    { id: 'whisper-small', name: 'Whisper Small', type: 'transcription', speed: 'medium' },
    { id: 'whisper-medium', name: 'Whisper Medium', type: 'transcription', speed: 'slow' },
    { id: 'whisper-large', name: 'Whisper Large', type: 'transcription', speed: 'very slow' },
    { id: 'yamnet', name: 'YAMNet', type: 'sound_classification', speed: 'fast' },
    { id: 'audio-spectrogram-transformer', name: 'AST', type: 'sound_classification', speed: 'medium' },
    { id: 'panns-cnn14', name: 'PANNs CNN14', type: 'sound_classification', speed: 'medium' },
  ]

  const handleModelChange = (modelId) => {
    const model = audioModels.find(m => m.id === modelId)
    if (model) {
      setSelectedModel(modelId)
      setModelName(model.name)
      setModelType(model.type)
      data.modelId = modelId
      data.modelName = model.name
      data.modelType = model.type
    }
  }

  const addKeyword = () => {
    if (keywordInput.trim()) {
      const newKeywords = [...detectKeywords, keywordInput.trim()]
      setDetectKeywords(newKeywords)
      data.detectKeywords = newKeywords
      setKeywordInput('')
    }
  }

  const removeKeyword = (index) => {
    const newKeywords = detectKeywords.filter((_, i) => i !== index)
    setDetectKeywords(newKeywords)
    data.detectKeywords = newKeywords
  }

  const languages = [
    { code: 'auto', name: 'Auto Detect' },
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
  ]

  return (
    <NodeWrapper nodeId={id}>
      <div className="shadow-lg rounded-lg border-2 border-pink-500 bg-gray-900 min-w-[300px] max-w-[340px]">
      <div className="px-4 py-3 bg-pink-950/30 border-b border-pink-800">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xl">🎤</span>
          <div className="font-bold text-sm text-pink-400">Audio AI</div>
        </div>
        <div className="text-[10px] text-pink-600">
          {modelType === 'transcription' ? 'Speech-to-text transcription' : 'Sound classification & detection'}
        </div>
      </div>

      <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
        {/* Model Selection */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">AI Model *</label>
          <select
            value={selectedModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
          >
            <option value="">Select Model...</option>
            <optgroup label="🎙️ Transcription (Whisper)">
              {audioModels.filter(m => m.type === 'transcription').map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.speed})
                </option>
              ))}
            </optgroup>
            <optgroup label="🔊 Sound Classification">
              {audioModels.filter(m => m.type === 'sound_classification').map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.speed})
                </option>
              ))}
            </optgroup>
          </select>
        </div>

        {/* Transcription Settings */}
        {modelType === 'transcription' && (
          <>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Language</label>
              <select
                value={language}
                onChange={(e) => {
                  setLanguage(e.target.value)
                  data.language = e.target.value
                }}
                className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-white"
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            {/* Keyword Detection */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Trigger Keywords (optional)
              </label>
              <div className="flex space-x-1 mb-2">
                <input
                  type="text"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                  placeholder="help, emergency, gun..."
                  className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                />
                <button
                  onClick={addKeyword}
                  className="px-2 py-1 bg-pink-600 hover:bg-pink-700 rounded text-xs text-white"
                >
                  +
                </button>
              </div>
              <div className="flex flex-wrap gap-1">
                {detectKeywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1 px-2 py-1 bg-pink-900/30 border border-pink-700/50 rounded text-xs text-pink-300"
                  >
                    <span>{keyword}</span>
                    <button
                      onClick={() => removeKeyword(idx)}
                      className="text-pink-500 hover:text-pink-300"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="text-[10px] text-gray-600 mt-1">
                Alert when these words are detected in speech
              </div>
            </div>
          </>
        )}

        {/* Sound Classification Settings */}
        {modelType === 'sound_classification' && (
          <>
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Detection Confidence
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={confidence}
                onChange={(e) => {
                  const value = parseFloat(e.target.value)
                  setConfidence(value)
                  data.confidence = value
                }}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0%</span>
                <span className="text-pink-400 font-medium">{(confidence * 100).toFixed(0)}%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Sound Classes */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Detect Sounds
              </label>
              <div className="text-[10px] text-gray-600 space-y-0.5">
                <div>🔫 Gunshots</div>
                <div>💥 Explosions</div>
                <div>🚨 Alarms</div>
                <div>🔨 Glass Breaking</div>
                <div>😱 Screaming</div>
                <div>🐕 Dog Barking</div>
                <div>🚗 Vehicle Engine</div>
                <div>🔊 Loud Noise</div>
              </div>
            </div>
          </>
        )}

        {/* Common Settings */}
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
            Process audio in {bufferDuration}s chunks
          </div>
        </div>
      </div>

      <div className="px-4 py-2 bg-gray-950 border-t border-gray-800 text-xs text-gray-500">
        {selectedModel ? (
          <span className="text-pink-400">
            {modelType === 'transcription' ? '🎙️ Transcribing...' : '🔊 Classifying...'}
          </span>
        ) : (
          <span>Select a model to begin</span>
        )}
      </div>

      {/* Input: Audio or Video */}
      <Handle
        type="target"
        position={Position.Left}
        id="audio-input"
        className="w-3 h-3 bg-pink-500"
        style={{ top: '50%' }}
      />
      
        {/* Output: Transcription or Classifications */}
        <Handle
          type="source"
          position={Position.Right}
          id="transcript-output"
          className="w-3 h-3 bg-purple-500"
        />
      </div>
    </NodeWrapper>
  )
})

