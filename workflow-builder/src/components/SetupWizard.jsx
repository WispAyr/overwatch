/**
 * Setup Wizard Framework
 * Generic wizard component for guided node setup
 */
import React, { useState } from 'react'

const SetupWizard = ({
  title,
  steps,
  onComplete,
  onCancel,
  nodeType,
  nodeId
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [stepData, setStepData] = useState({})
  const [stepErrors, setStepErrors] = useState({})
  const [isValidating, setIsValidating] = useState(false)

  const step = steps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === steps.length - 1

  const handleNext = async () => {
    // Validate current step
    if (step.validate) {
      setIsValidating(true)
      const validation = await step.validate(stepData[currentStep])
      setIsValidating(false)

      if (!validation.valid) {
        setStepErrors({
          ...stepErrors,
          [currentStep]: validation.error
        })
        return
      }
    }

    // Clear error for this step
    const newErrors = { ...stepErrors }
    delete newErrors[currentStep]
    setStepErrors(newErrors)

    if (isLastStep) {
      // Complete wizard
      onComplete(stepData)
    } else {
      // Go to next step
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (!isFirstStep) {
      setCurrentStep(currentStep - 1)
    }
  }

  const updateStepData = (data) => {
    setStepData({
      ...stepData,
      [currentStep]: {
        ...stepData[currentStep],
        ...data
      }
    })

    // Clear error when user makes changes
    if (stepErrors[currentStep]) {
      const newErrors = { ...stepErrors }
      delete newErrors[currentStep]
      setStepErrors(newErrors)
    }
  }

  const canProceed = () => {
    if (step.canProceed) {
      return step.canProceed(stepData[currentStep])
    }
    return true
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-bold text-white">{title}</h2>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-white text-2xl"
            >
              ✕
            </button>
          </div>

          {/* Progress Bar */}
          <div className="flex items-center gap-2">
            {steps.map((s, idx) => (
              <React.Fragment key={idx}>
                <div
                  className={`flex-1 h-2 rounded-full transition-colors ${
                    idx < currentStep
                      ? 'bg-green-500'
                      : idx === currentStep
                      ? 'bg-blue-500'
                      : 'bg-gray-700'
                  }`}
                />
              </React.Fragment>
            ))}
          </div>

          {/* Step Counter */}
          <div className="text-xs text-gray-400 mt-2">
            Step {currentStep + 1} of {steps.length}
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step Icon and Title */}
          <div className="text-center mb-6">
            {step.icon && <div className="text-5xl mb-3">{step.icon}</div>}
            <h3 className="text-lg font-semibold text-white mb-2">
              {step.title}
            </h3>
            {step.description && (
              <p className="text-sm text-gray-400">
                {step.description}
              </p>
            )}
          </div>

          {/* Step Error */}
          {stepErrors[currentStep] && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-sm text-red-300">
              {stepErrors[currentStep]}
            </div>
          )}

          {/* Step Component */}
          <div className="space-y-4">
            {step.component && React.createElement(step.component, {
              data: stepData[currentStep] || {},
              onChange: updateStepData,
              nodeType,
              nodeId
            })}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between bg-gray-800/30">
          <button
            onClick={handleBack}
            disabled={isFirstStep}
            className={`px-4 py-2 text-sm transition-colors ${
              isFirstStep
                ? 'text-gray-600 cursor-not-allowed'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            ← Back
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed() || isValidating}
              className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                canProceed() && !isValidating
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isValidating ? (
                'Validating...'
              ) : isLastStep ? (
                '✓ Complete Setup'
              ) : (
                'Next →'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SetupWizard

