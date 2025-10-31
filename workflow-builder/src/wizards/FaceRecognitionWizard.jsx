/**
 * Face Recognition Setup Wizard
 * Guided setup for Face Recognition node
 */
import React, { useState } from 'react'
import SetupWizard from '../components/SetupWizard'
import { apiBaseUrl } from '../config'

/**
 * Step 1: Install DeepFace
 */
const InstallDeepFaceStep = ({ data, onChange }) => {
  const [installing, setInstalling] = useState(false)
  const [installed, setInstalled] = useState(data.deepfaceInstalled || false)
  const [error, setError] = useState(null)

  const checkInstallation = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/component-status/status`)
      const status = await response.json()
      const deepfaceInstalled = status.dependencies?.deepface || false
      
      setInstalled(deepfaceInstalled)
      onChange({ deepfaceInstalled })
      
      return deepfaceInstalled
    } catch (err) {
      console.error('Failed to check installation:', err)
      return false
    }
  }

  const installDeepFace = async () => {
    setInstalling(true)
    setError(null)

    try {
      const response = await fetch(`${apiBaseUrl}/api/system/install-dependency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: 'deepface' })
      })

      if (!response.ok) {
        throw new Error('Installation failed')
      }

      // Wait a moment then check installation
      setTimeout(async () => {
        const isInstalled = await checkInstallation()
        setInstalling(false)
        
        if (!isInstalled) {
          setError('Installation completed but package not detected. Try manual installation.')
        }
      }, 2000)

    } catch (err) {
      setInstalling(false)
      setError(err.message)
    }
  }

  React.useEffect(() => {
    checkInstallation()
  }, [])

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h4 className="font-semibold text-white mb-2">DeepFace Installation</h4>
        <p className="text-sm text-gray-400 mb-3">
          DeepFace is required for face recognition. This step will install the package.
        </p>

        {installed ? (
          <div className="bg-green-900/30 border border-green-700 rounded p-3 text-sm text-green-300">
            ✓ DeepFace is already installed
          </div>
        ) : (
          <div>
            <div className="bg-yellow-900/30 border border-yellow-700 rounded p-3 text-sm text-yellow-300 mb-3">
              ⚠️ DeepFace is not installed
            </div>

            <div className="space-y-2">
              <div className="text-sm text-gray-300 mb-2">Installation options:</div>
              
              <button
                onClick={installDeepFace}
                disabled={installing}
                className={`w-full px-4 py-2 text-sm font-medium rounded transition-colors ${
                  installing
                    ? 'bg-gray-700 text-gray-500 cursor-wait'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {installing ? '⏳ Installing...' : '🔧 Auto-Install DeepFace'}
              </button>

              <div className="text-xs text-center text-gray-500 my-2">OR</div>

              <div className="bg-gray-800 border border-gray-600 rounded p-3">
                <div className="text-xs text-gray-400 mb-2">Manual installation:</div>
                <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded font-mono text-xs">
                  pip install deepface
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText('pip install deepface')
                    alert('Copied to clipboard!')
                  }}
                  className="mt-2 text-xs text-blue-400 hover:text-blue-300"
                >
                  📋 Copy command
                </button>
              </div>

              <button
                onClick={checkInstallation}
                className="w-full px-4 py-2 text-sm font-medium bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
              >
                🔄 Check Installation
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 bg-red-900/30 border border-red-700 rounded p-3 text-sm text-red-300">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Step 2: Create Face Database
 */
const CreateDatabaseStep = ({ data, onChange }) => {
  const [dbPath, setDbPath] = useState(data.dbPath || 'data/faces')
  const [created, setCreated] = useState(data.dbCreated || false)
  const [error, setError] = useState(null)

  const createDatabase = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/face-recognition/create-database`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: dbPath })
      })

      if (!response.ok) {
        throw new Error('Failed to create database directory')
      }

      setCreated(true)
      onChange({ dbPath, dbCreated: true })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h4 className="font-semibold text-white mb-2">Face Database Location</h4>
        <p className="text-sm text-gray-400 mb-3">
          Choose where to store face images for recognition.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-300 mb-1">
              Database Path:
            </label>
            <input
              type="text"
              value={dbPath}
              onChange={(e) => {
                setDbPath(e.target.value)
                onChange({ dbPath: e.target.value, dbCreated: false })
                setCreated(false)
              }}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white text-sm"
              placeholder="data/faces"
            />
            <div className="text-xs text-gray-500 mt-1">
              Relative to backend directory
            </div>
          </div>

          {!created ? (
            <button
              onClick={createDatabase}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
            >
              📁 Create Directory
            </button>
          ) : (
            <div className="bg-green-900/30 border border-green-700 rounded p-3 text-sm text-green-300">
              ✓ Database directory created at: {dbPath}
            </div>
          )}

          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded p-3 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>
      </div>

      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
        <div className="font-semibold text-blue-300 mb-2">📖 How it works:</div>
        <ul className="text-sm text-blue-200 space-y-1 list-disc list-inside">
          <li>Create one folder per person inside {dbPath}</li>
          <li>Add face photos (JPG/PNG) to each person's folder</li>
          <li>Example: {dbPath}/john_doe/photo1.jpg</li>
          <li>The folder name becomes the person's identity</li>
        </ul>
      </div>
    </div>
  )
}

/**
 * Step 3: Configure Model Settings
 */
const ConfigureModelStep = ({ data, onChange }) => {
  const [modelName, setModelName] = useState(data.modelName || 'Facenet')
  const [detectorBackend, setDetectorBackend] = useState(data.detectorBackend || 'opencv')

  const handleChange = (key, value) => {
    const newData = { ...data, [key]: value }
    if (key === 'modelName') setModelName(value)
    if (key === 'detectorBackend') setDetectorBackend(value)
    onChange(newData)
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h4 className="font-semibold text-white mb-3">Model Configuration</h4>

        <div className="space-y-4">
          {/* Recognition Model */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">
              Recognition Model:
            </label>
            <select
              value={modelName}
              onChange={(e) => handleChange('modelName', e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white text-sm"
            >
              <option value="Facenet">Facenet (Fast, accurate)</option>
              <option value="VGG-Face">VGG-Face (Accurate, slower)</option>
              <option value="ArcFace">ArcFace (Best accuracy)</option>
              <option value="OpenFace">OpenFace (Lightweight)</option>
            </select>
            <div className="text-xs text-gray-500 mt-1">
              Facenet is recommended for most use cases
            </div>
          </div>

          {/* Detector Backend */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">
              Detector Backend:
            </label>
            <select
              value={detectorBackend}
              onChange={(e) => handleChange('detectorBackend', e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white text-sm"
            >
              <option value="opencv">OpenCV (Fast, CPU)</option>
              <option value="ssd">SSD (Balanced)</option>
              <option value="mtcnn">MTCNN (Accurate)</option>
              <option value="retinaface">RetinaFace (Best accuracy, GPU)</option>
            </select>
            <div className="text-xs text-gray-500 mt-1">
              OpenCV is fastest and works well for most scenarios
            </div>
          </div>
        </div>
      </div>

      <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
        <div className="font-semibold text-green-300 mb-2">✓ Ready to use!</div>
        <div className="text-sm text-green-200">
          Your face recognition node will be configured with these settings.
          You can change them later in the node configuration panel.
        </div>
      </div>
    </div>
  )
}

/**
 * Main Face Recognition Wizard
 */
const FaceRecognitionWizard = ({ onComplete, onCancel }) => {
  const steps = [
    {
      title: 'Install DeepFace',
      description: 'Install the required face recognition library',
      icon: '📦',
      component: InstallDeepFaceStep,
      validate: (data) => {
        if (!data?.deepfaceInstalled) {
          return { valid: false, error: 'Please install DeepFace before continuing' }
        }
        return { valid: true }
      },
      canProceed: (data) => data?.deepfaceInstalled === true
    },
    {
      title: 'Create Face Database',
      description: 'Set up the directory structure for face images',
      icon: '📁',
      component: CreateDatabaseStep,
      validate: (data) => {
        if (!data?.dbCreated) {
          return { valid: false, error: 'Please create the database directory' }
        }
        return { valid: true }
      },
      canProceed: (data) => data?.dbCreated === true
    },
    {
      title: 'Configure Model',
      description: 'Choose recognition model and detector settings',
      icon: '⚙️',
      component: ConfigureModelStep,
      canProceed: (data) => true // No validation needed
    }
  ]

  const handleComplete = (stepData) => {
    // Combine all step data
    const config = {
      faceDbPath: stepData[1]?.dbPath || 'data/faces',
      modelName: stepData[2]?.modelName || 'Facenet',
      detectorBackend: stepData[2]?.detectorBackend || 'opencv'
    }

    onComplete(config)
  }

  return (
    <SetupWizard
      title="Face Recognition Setup"
      steps={steps}
      onComplete={handleComplete}
      onCancel={onCancel}
      nodeType="model"
      nodeId="face-recognition-v1"
    />
  )
}

export default FaceRecognitionWizard

