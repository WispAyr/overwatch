import { useEffect, useRef } from 'react'

export default function CustomBackground({ config }) {
  const canvasRef = useRef(null)
  const mapTilesRef = useRef({})

  useEffect(() => {
    if (!config || config.type === 'none') return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const rect = canvas.parentElement.getBoundingClientRect()
    
    canvas.width = rect.width
    canvas.height = rect.height

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (config.type === 'image' && config.url) {
      const img = new Image()
      img.onload = () => {
        ctx.globalAlpha = config.opacity || 0.3
        
        // Calculate scaling to fit canvas while maintaining aspect ratio
        const scale = Math.max(canvas.width / img.width, canvas.height / img.height)
        const x = (canvas.width - img.width * scale) / 2
        const y = (canvas.height - img.height * scale) / 2
        
        ctx.drawImage(img, x, y, img.width * scale, img.height * scale)
      }
      img.src = config.url
    } else if (config.type === 'map') {
      // Draw Map tiles with style support
      const zoom = config.zoom || 13
      const lat = config.center?.lat || 51.505
      const lng = config.center?.lng || -0.09
      const mapStyle = config.style || 'standard'
      
      // Convert lat/lng to tile coordinates
      const tileSize = 256
      const scale = Math.pow(2, zoom)
      
      const centerTileX = Math.floor((lng + 180) / 360 * scale)
      const centerTileY = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * scale)
      
      // Calculate how many tiles we need
      const tilesX = Math.ceil(canvas.width / tileSize) + 2
      const tilesY = Math.ceil(canvas.height / tileSize) + 2
      
      ctx.globalAlpha = config.opacity || 0.85
      
      // Get tile URL based on style
      const getTileUrl = (z, x, y) => {
        switch (mapStyle) {
          case 'dark':
            return `https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/${z}/${x}/${y}.png`
          case 'satellite':
            return `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`
          case 'terrain':
            return `https://tile.opentopomap.org/${z}/${x}/${y}.png`
          default: // standard
            return `https://tile.openstreetmap.org/${z}/${x}/${y}.png`
        }
      }
      
      // Draw tiles
      for (let x = -Math.floor(tilesX / 2); x <= Math.floor(tilesX / 2); x++) {
        for (let y = -Math.floor(tilesY / 2); y <= Math.floor(tilesY / 2); y++) {
          const tileX = centerTileX + x
          const tileY = centerTileY + y
          
          // Check if tile is valid
          if (tileX < 0 || tileY < 0 || tileX >= scale || tileY >= scale) continue
          
          const tileUrl = getTileUrl(zoom, tileX, tileY)
          const cacheKey = `${mapStyle}-${zoom}-${tileX}-${tileY}`
          
          // Draw from cache or load new tile
          if (mapTilesRef.current[cacheKey]) {
            const img = mapTilesRef.current[cacheKey]
            if (img.complete) {
              ctx.drawImage(
                img,
                canvas.width / 2 + x * tileSize - tileSize / 2,
                canvas.height / 2 + y * tileSize - tileSize / 2,
                tileSize,
                tileSize
              )
            }
          } else {
            const img = new Image()
            img.crossOrigin = 'anonymous'
            img.onload = () => {
              ctx.globalAlpha = config.opacity || 0.85
              ctx.drawImage(
                img,
                canvas.width / 2 + x * tileSize - tileSize / 2,
                canvas.height / 2 + y * tileSize - tileSize / 2,
                tileSize,
                tileSize
              )
            }
            img.onerror = () => {
              // Draw placeholder on error
              ctx.fillStyle = '#1f2937'
              ctx.fillRect(
                canvas.width / 2 + x * tileSize - tileSize / 2,
                canvas.height / 2 + y * tileSize - tileSize / 2,
                tileSize,
                tileSize
              )
              ctx.strokeStyle = '#374151'
              ctx.strokeRect(
                canvas.width / 2 + x * tileSize - tileSize / 2,
                canvas.height / 2 + y * tileSize - tileSize / 2,
                tileSize,
                tileSize
              )
            }
            img.src = tileUrl
            mapTilesRef.current[cacheKey] = img
          }
        }
      }
      
      // Draw center marker
      ctx.globalAlpha = 1
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2
      
      // Outer circle
      ctx.fillStyle = '#3b82f6'
      ctx.beginPath()
      ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI)
      ctx.fill()
      
      // Inner circle
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI)
      ctx.fill()
      
      // Draw coordinates text
      ctx.fillStyle = '#000000'
      ctx.fillRect(5, 5, 250, 45)
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 12px monospace'
      ctx.fillText(`📍 ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 10, 20)
      ctx.fillText(`🔍 Zoom: ${zoom}`, 10, 40)
    }
  }, [config])

  if (!config || config.type === 'none') return null

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  )
}

