import { useEffect, useRef, useCallback, useState } from 'react'
import { apiBaseUrl } from '../config'

/**
 * Auto-save hook for workflows
 * 
 * @param {string} workflowId - Current workflow ID
 * @param {object} workflowData - Workflow data to save (nodes, edges, etc.)
 * @param {object} options - Configuration options
 * @returns {object} - Save status and manual save function
 */
export function useAutoSave(workflowId, workflowData, options = {}) {
  const {
    enabled = true,
    interval = 30000, // 30 seconds default
    onSaveSuccess,
    onSaveError,
    debounceDelay = 2000 // Wait 2s after last change before saving
  } = options

  const [saveStatus, setSaveStatus] = useState('idle') // idle, saving, saved, error
  const [lastSaved, setLastSaved] = useState(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  
  const saveTimeoutRef = useRef(null)
  const lastDataRef = useRef(null)
  const lastSaveDataRef = useRef(null)

  // Manual save function
  const save = useCallback(async (force = false) => {
    if (!workflowId || !workflowData) {
      console.log('No workflow ID or data to save')
      return { success: false, reason: 'no_data' }
    }

    // Check if data has actually changed
    const currentDataStr = JSON.stringify(workflowData)
    if (!force && currentDataStr === lastSaveDataRef.current) {
      console.log('No changes to save')
      return { success: true, reason: 'no_changes' }
    }

    setSaveStatus('saving')
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/workflow-builder/${workflowId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: currentDataStr
      })

      if (response.ok) {
        const savedData = await response.json()
        lastSaveDataRef.current = currentDataStr
        setLastSaved(new Date())
        setSaveStatus('saved')
        setHasUnsavedChanges(false)
        
        if (onSaveSuccess) {
          onSaveSuccess(savedData)
        }
        
        // Reset to idle after 2 seconds
        setTimeout(() => setSaveStatus('idle'), 2000)
        
        return { success: true, data: savedData }
      } else {
        throw new Error(`Save failed: ${response.status}`)
      }
    } catch (error) {
      console.error('Auto-save error:', error)
      setSaveStatus('error')
      
      if (onSaveError) {
        onSaveError(error)
      }
      
      // Reset to idle after 3 seconds
      setTimeout(() => setSaveStatus('idle'), 3000)
      
      return { success: false, error }
    }
  }, [workflowId, workflowData, onSaveSuccess, onSaveError])

  // Debounced auto-save
  useEffect(() => {
    if (!enabled || !workflowId || !workflowData) {
      return
    }

    const currentDataStr = JSON.stringify(workflowData)
    
    // Check if data changed
    if (currentDataStr !== lastDataRef.current) {
      lastDataRef.current = currentDataStr
      setHasUnsavedChanges(currentDataStr !== lastSaveDataRef.current)
      
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
      
      // Set new timeout for debounced save
      saveTimeoutRef.current = setTimeout(() => {
        save()
      }, debounceDelay)
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [workflowData, enabled, workflowId, debounceDelay, save])

  // Periodic auto-save (fallback)
  useEffect(() => {
    if (!enabled || !workflowId) {
      return
    }

    const periodicSave = setInterval(() => {
      if (hasUnsavedChanges) {
        save()
      }
    }, interval)

    return () => clearInterval(periodicSave)
  }, [enabled, workflowId, interval, hasUnsavedChanges, save])

  // Save on page unload if there are unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
        
        // Try to save (may not complete before page closes)
        save()
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges, save])

  // Keyboard shortcut: Ctrl/Cmd + S
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        save(true) // Force save
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [save])

  return {
    save,
    saveStatus,
    lastSaved,
    hasUnsavedChanges,
    isSaving: saveStatus === 'saving',
    isSaved: saveStatus === 'saved',
    isError: saveStatus === 'error'
  }
}


