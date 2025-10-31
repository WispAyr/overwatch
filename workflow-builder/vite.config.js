import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 7003,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        ws: true,  // Enable WebSocket proxying
        secure: false
      }
    }
  },
  build: {
    outDir: '../frontend/workflow-builder',
    // Use relative paths for production when served by FastAPI
    base: './'
  },
  // Define global constants
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000')
  }
})

