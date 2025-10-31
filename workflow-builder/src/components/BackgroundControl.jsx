import { useState, useRef } from 'react'

export default function BackgroundControl({ onBackgroundChange, currentBackground }) {
  const [showPanel, setShowPanel] = useState(false)
  const [backgroundType, setBackgroundType] = useState('none') // 'none', 'image', 'map'
  const [backgroundImage, setBackgroundImage] = useState(null)
  const [opacity, setOpacity] = useState(0.85)
  const [mapCenter, setMapCenter] = useState({ lat: 51.505, lng: -0.09 })
  const [mapZoom, setMapZoom] = useState(15)
  const [mapBounds, setMapBounds] = useState({
    north: 51.51,
    south: 51.50,
    east: -0.08,
    west: -0.10
  })
  const [gettingLocation, setGettingLocation] = useState(false)
  const [syncWithViewport, setSyncWithViewport] = useState(false)
  const [mapStyle, setMapStyle] = useState('standard') // 'standard', 'dark', 'satellite', 'terrain'
  const fileInputRef = useRef(null)

  // Get user's location on component mount
  const getUserLocation = () => {
    setGettingLocation(true)
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude
          const lng = position.coords.longitude
          setMapCenter({ lat, lng })
          setGettingLocation(false)
          console.log('User location:', lat, lng)
          
          // Update map immediately with new location
          if (backgroundType === 'map') {
            onBackgroundChange({
              type: 'map',
              center: { lat, lng },
              zoom: mapZoom,
              bounds: mapBounds,
              opacity: opacity
            })
          }
        },
        (error) => {
          console.error('Error getting location:', error)
          setGettingLocation(false)
          // Fallback to default location
        }
      )
    } else {
      console.error('Geolocation not supported')
      setGettingLocation(false)
    }
  }

  const handleImageUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const imageUrl = e.target.result
      setBackgroundImage(imageUrl)
      setBackgroundType('image')
      onBackgroundChange({
        type: 'image',
        url: imageUrl,
        opacity: opacity
      })
    }
    reader.readAsDataURL(file)
  }

  const handleRemoveBackground = () => {
    setBackgroundType('none')
    setBackgroundImage(null)
    onBackgroundChange({ type: 'none' })
  }

  const handleOpacityChange = (newOpacity) => {
    setOpacity(newOpacity)
    if (backgroundType === 'image' && backgroundImage) {
      onBackgroundChange({
        type: 'image',
        url: backgroundImage,
        opacity: newOpacity
      })
    } else if (backgroundType === 'map') {
      onBackgroundChange({
        type: 'map',
        center: mapCenter,
        zoom: mapZoom,
        bounds: mapBounds,
        opacity: newOpacity
      })
    }
  }

  const enableMapMode = () => {
    // Get user location first if we haven't already
    if (mapCenter.lat === 51.505 && mapCenter.lng === -0.09) {
      getUserLocation()
    }
    
    setBackgroundType('map')
    onBackgroundChange({
      type: 'map',
      center: mapCenter,
      zoom: mapZoom,
      bounds: mapBounds,
      opacity: opacity,
      syncWithViewport: syncWithViewport,
      style: mapStyle
    })
  }

  // Update map when settings change
  const updateMap = () => {
    onBackgroundChange({
      type: 'map',
      center: mapCenter,
      zoom: mapZoom,
      bounds: mapBounds,
      opacity: opacity,
      syncWithViewport: syncWithViewport,
      style: mapStyle
    })
  }

  return (
    <div className="relative">
      {/* Toggle Button */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg hover:border-gray-500 transition-colors text-sm flex items-center space-x-2"
        title="Background Settings"
      >
        <span>🗺️</span>
        <span className="text-gray-300">Background</span>
        {backgroundType !== 'none' && (
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
        )}
      </button>

      {/* Control Panel */}
      {showPanel && (
        <div className="absolute top-12 right-0 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-4 z-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-white">Background Settings</h3>
            <button
              onClick={() => setShowPanel(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          {/* Background Type Selection */}
          <div className="mb-4">
            <label className="text-xs text-gray-400 block mb-2">Background Type</label>
            <div className="space-y-2">
              <button
                onClick={() => handleRemoveBackground()}
                className={`w-full px-3 py-2 rounded text-sm text-left ${
                  backgroundType === 'none'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                None (Grid Only)
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className={`w-full px-3 py-2 rounded text-sm text-left ${
                  backgroundType === 'image'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                📁 Upload Floor Plan/Image
              </button>
              <button
                onClick={enableMapMode}
                className={`w-full px-3 py-2 rounded text-sm text-left ${
                  backgroundType === 'map'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                🌍 Geographic Map
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
          </div>

          {/* Current Background Info */}
          {backgroundType === 'image' && backgroundImage && (
            <div className="mb-4 p-3 bg-gray-950 border border-gray-800 rounded">
              <div className="text-xs text-gray-400 mb-2">Preview:</div>
              <img
                src={backgroundImage}
                alt="Background"
                className="w-full h-24 object-cover rounded border border-gray-700"
              />
              <button
                onClick={handleRemoveBackground}
                className="mt-2 w-full px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs hover:bg-red-900/70"
              >
                Remove Image
              </button>
            </div>
          )}

          {backgroundType === 'map' && (
            <div className="mb-4 p-3 bg-gray-950 border border-gray-800 rounded">
              <div className="text-xs text-gray-400 mb-3">Map Settings:</div>
              
              {/* Map Style */}
              <div className="mb-3">
                <label className="text-xs text-gray-500 block mb-1">Map Style</label>
                <select
                  value={mapStyle}
                  onChange={(e) => {
                    const newStyle = e.target.value
                    setMapStyle(newStyle)
                    onBackgroundChange({
                      type: 'map',
                      center: mapCenter,
                      zoom: mapZoom,
                      bounds: mapBounds,
                      opacity: opacity,
                      syncWithViewport: syncWithViewport,
                      style: newStyle
                    })
                  }}
                  className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                >
                  <option value="standard">🗺️ Standard</option>
                  <option value="dark">🌙 Dark Mode</option>
                  <option value="satellite">🛰️ Satellite</option>
                  <option value="terrain">⛰️ Terrain</option>
                </select>
              </div>

              {/* Sync with Viewport */}
              <div className="mb-3 p-2 bg-gray-900 rounded border border-gray-800">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={syncWithViewport}
                    onChange={(e) => {
                      const newSync = e.target.checked
                      setSyncWithViewport(newSync)
                      onBackgroundChange({
                        type: 'map',
                        center: mapCenter,
                        zoom: mapZoom,
                        bounds: mapBounds,
                        opacity: opacity,
                        syncWithViewport: newSync,
                        style: mapStyle
                      })
                    }}
                    className="mr-2"
                  />
                  <span className="text-xs text-gray-300">
                    🔄 Sync map with canvas pan/zoom
                  </span>
                </label>
                <div className="text-[10px] text-gray-600 mt-1 ml-6">
                  Map follows when you move the canvas
                </div>
              </div>
              
              {/* Center Coordinates */}
              <div className="mb-3">
                <label className="text-xs text-gray-500 block mb-1">Center (Lat, Lng)</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    step="0.0001"
                    value={mapCenter.lat}
                    onChange={(e) => {
                      const newLat = parseFloat(e.target.value)
                      setMapCenter({ ...mapCenter, lat: newLat })
                    }}
                    onBlur={() => {
                      // Update map when input loses focus
                      onBackgroundChange({
                        type: 'map',
                        center: mapCenter,
                        zoom: mapZoom,
                        bounds: mapBounds,
                        opacity: opacity
                      })
                    }}
                    className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="Latitude"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={mapCenter.lng}
                    onChange={(e) => {
                      const newLng = parseFloat(e.target.value)
                      setMapCenter({ ...mapCenter, lng: newLng })
                    }}
                    onBlur={() => {
                      // Update map when input loses focus
                      onBackgroundChange({
                        type: 'map',
                        center: mapCenter,
                        zoom: mapZoom,
                        bounds: mapBounds,
                        opacity: opacity
                      })
                    }}
                    className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="Longitude"
                  />
                </div>
              </div>

              {/* Zoom */}
              <div className="mb-3">
                <label className="text-xs text-gray-500 block mb-1">Zoom Level: {mapZoom}</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={mapZoom}
                  onChange={(e) => {
                    const newZoom = parseInt(e.target.value)
                    setMapZoom(newZoom)
                    // Update map immediately
                    onBackgroundChange({
                      type: 'map',
                      center: mapCenter,
                      zoom: newZoom,
                      bounds: mapBounds,
                      opacity: opacity,
                      syncWithViewport: syncWithViewport,
                      style: mapStyle
                    })
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-600 mt-1">
                  <span>World</span>
                  <span>Street</span>
                </div>
              </div>

              {/* Map Bounds */}
              <details className="mb-2">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                  Define Bounds (Optional)
                </summary>
                <div className="mt-2 space-y-2">
                  <input
                    type="number"
                    step="0.0001"
                    value={mapBounds.north}
                    onChange={(e) => setMapBounds({ ...mapBounds, north: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="North"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={mapBounds.south}
                    onChange={(e) => setMapBounds({ ...mapBounds, south: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="South"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={mapBounds.east}
                    onChange={(e) => setMapBounds({ ...mapBounds, east: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="East"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={mapBounds.west}
                    onChange={(e) => setMapBounds({ ...mapBounds, west: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
                    placeholder="West"
                  />
                </div>
              </details>

              <div className="space-y-2">
                <button
                  onClick={getUserLocation}
                  disabled={gettingLocation}
                  className="w-full px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50"
                >
                  {gettingLocation ? '📍 Getting Location...' : '📍 Use My Location'}
                </button>
                <button
                  onClick={updateMap}
                  className="w-full px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                >
                  Update Map
                </button>
              </div>
            </div>
          )}

          {/* Opacity Control */}
          {backgroundType !== 'none' && (
            <div className="mb-4">
              <label className="text-xs text-gray-400 block mb-2">
                Opacity: {Math.round(opacity * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={opacity}
                onChange={(e) => handleOpacityChange(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>Transparent</span>
                <span>Opaque</span>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded">
            <div className="text-xs text-blue-400 mb-1 font-medium">💡 Tips:</div>
            <ul className="text-xs text-gray-400 space-y-1">
              <li>• Upload floor plans or site maps</li>
              <li>• Use maps for outdoor locations</li>
              <li>• Nodes will snap to real positions</li>
              <li>• Adjust opacity for visibility</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

