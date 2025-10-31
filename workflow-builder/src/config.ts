/**
 * Workflow Builder Configuration
 * Environment-driven configuration for API endpoints and settings
 */

// Read from Vite environment variables
const {
  VITE_API_BASE_URL,
  VITE_WS_BASE_URL,
  DEV,
  MODE
} = import.meta.env;

/**
 * API Base URL
 * Defaults to relative path for production, can be overridden via env var
 */
export const apiBaseUrl = VITE_API_BASE_URL || (DEV ? 'http://localhost:8000' : '');

/**
 * WebSocket Base URL
 * Defaults to ws:// version of API base URL
 */
export const wsBaseUrl = VITE_WS_BASE_URL || (
  apiBaseUrl 
    ? apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://') 
    : (DEV ? 'ws://localhost:8000' : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`)
);

/**
 * API Endpoints
 */
export const endpoints = {
  // Cameras
  cameras: `${apiBaseUrl}/api/cameras/`,
  
  // Workflow Builder
  workflows: `${apiBaseUrl}/api/workflow-builder/`,
  workflowById: (id: string) => `${apiBaseUrl}/api/workflow-builder/${id}`,
  workflowDeploy: (id: string) => `${apiBaseUrl}/api/workflow-builder/${id}/deploy`,
  workflowPreview: (id: string) => `${apiBaseUrl}/api/workflow-builder/${id}/preview`,
  workflowExecute: (id: string) => `${apiBaseUrl}/api/workflow-builder/${id}/execute`,
  workflowStop: (id: string) => `${apiBaseUrl}/api/workflow-builder/${id}/stop`,
  workflowExecuteRealtime: `${apiBaseUrl}/api/workflow-builder/execute`,
  workflowStopAll: `${apiBaseUrl}/api/workflow-builder/stop-all`,
  workflowStatus: `${apiBaseUrl}/api/workflow-builder/status`,
  
  // Components
  workflowComponents: {
    models: `${apiBaseUrl}/api/workflow-components/models`,
    actions: `${apiBaseUrl}/api/workflow-components/actions`,
    filters: `${apiBaseUrl}/api/workflow-components/filters`,
    classes: `${apiBaseUrl}/api/workflow-components/classes`,
  },
  
  // Component Status
  componentStatus: {
    status: `${apiBaseUrl}/api/component-status/status`,
    badges: `${apiBaseUrl}/api/component-status/badges`,
  },
  
  // Templates/Subflows
  templates: `${apiBaseUrl}/api/workflow-templates/`,
  templateById: (id: string) => `${apiBaseUrl}/api/workflow-templates/${id}`,
  
  // Config
  config: {
    sites: `${apiBaseUrl}/api/config/sites`,
    models: `${apiBaseUrl}/api/config/models`,
    cameras: `${apiBaseUrl}/api/config/cameras`,
  },
  
  // WebSocket
  websocket: `${wsBaseUrl}/ws/workflow`,
};

/**
 * Application Settings
 */
export const settings = {
  // Enable debug logging in development
  debug: DEV,
  
  // Auto-save interval (ms)
  autoSaveInterval: 30000, // 30 seconds
  
  // Maximum nodes allowed in a workflow
  maxNodes: 100,
  
  // Maximum edges allowed in a workflow
  maxEdges: 200,
  
  // Grid snap settings
  gridSize: 15,
  snapToGrid: true,
  
  // Default node positions
  nodeDefaults: {
    width: 240,
    height: 100,
  },
  
  // Validation settings
  validateOnSave: true,
  validateOnConnect: true,
  
  // UI settings
  showMinimap: true,
  showControls: true,
  animateEdges: true,
};

/**
 * Feature Flags
 */
export const features = {
  // Enable subflows/templates
  subflows: true,
  
  // Enable link nodes (linkIn/Out/Call)
  linkNodes: true,
  
  // Enable catch/error handling nodes
  catchNodes: true,
  
  // Enable keyboard shortcuts
  keyboardShortcuts: true,
  
  // Enable context menus
  contextMenus: true,
  
  // Enable real-time metrics
  realtimeMetrics: true,
  
  // Enable YAML preview
  yamlPreview: true,
  
  // Enable authentication
  authentication: false, // TODO: Enable when auth is implemented
};

/**
 * Log configuration info (non-sensitive only)
 */
if (DEV) {
  console.log('🔧 Workflow Builder Configuration:', {
    mode: MODE,
    apiBaseUrl,
    wsBaseUrl,
    features,
  });
}

export default {
  apiBaseUrl,
  wsBaseUrl,
  endpoints,
  settings,
  features,
};


