"""
Lighting Analyzer - Detect day/night/dusk and IR mode from video frames
"""
import cv2
import numpy as np
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LightingState(str, Enum):
    """Lighting states"""
    DAY = 'day'
    DUSK = 'dusk'
    NIGHT = 'night'


class LightingAnalyzer:
    """Analyze video frames for lighting conditions and IR mode detection"""
    
    def __init__(self, history_size: int = 5):
        """
        Initialize lighting analyzer
        
        Args:
            history_size: Number of frames to average for smoothing
        """
        self.history_size = history_size
        self.brightness_history = []
        self.saturation_history = []
    
    def analyze_frame(
        self,
        frame: np.ndarray,
        brightness_threshold: float = 0.3,
        ir_threshold: float = 0.7,
        sensitivity: float = 0.5
    ) -> Dict:
        """
        Analyze frame for lighting conditions
        
        Args:
            frame: BGR image from camera
            brightness_threshold: Threshold for day/night (0.0-1.0)
            ir_threshold: Threshold for IR detection (0.0-1.0)
            sensitivity: Overall sensitivity adjustment (0.0-1.0)
            
        Returns:
            Dict with state, brightness, is_ir, confidence
        """
        try:
            # Convert to HSV for better analysis
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Calculate average brightness (V channel)
            brightness = np.mean(hsv[:, :, 2]) / 255.0
            
            # Calculate color saturation (S channel)
            saturation = np.mean(hsv[:, :, 1]) / 255.0
            
            # Add to history for smoothing
            self.brightness_history.append(brightness)
            self.saturation_history.append(saturation)
            
            # Maintain history size
            if len(self.brightness_history) > self.history_size:
                self.brightness_history.pop(0)
            if len(self.saturation_history) > self.history_size:
                self.saturation_history.pop(0)
            
            # Use smoothed values
            avg_brightness = np.mean(self.brightness_history)
            avg_saturation = np.mean(self.saturation_history)
            
            # Detect IR mode (low saturation = monochrome image)
            # Adjust threshold with sensitivity
            adjusted_ir_threshold = ir_threshold - (sensitivity - 0.5) * 0.2
            is_ir = avg_saturation < (1.0 - adjusted_ir_threshold)
            
            # Determine lighting state
            # Adjust brightness threshold with sensitivity
            adjusted_brightness_threshold = brightness_threshold + (sensitivity - 0.5) * 0.2
            
            if avg_brightness >= (adjusted_brightness_threshold + 0.2):
                state = LightingState.DAY
                confidence = min(1.0, (avg_brightness - adjusted_brightness_threshold) / 0.5)
            elif avg_brightness >= adjusted_brightness_threshold:
                state = LightingState.DUSK
                confidence = 0.7
            else:
                state = LightingState.NIGHT
                confidence = min(1.0, (adjusted_brightness_threshold - avg_brightness) / 0.3)
            
            return {
                'state': state.value,
                'brightness': float(avg_brightness),
                'saturation': float(avg_saturation),
                'is_ir': bool(is_ir),
                'confidence': float(confidence),
                'raw_brightness': float(brightness),
                'raw_saturation': float(saturation)
            }
        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return self._default_result()
    
    def _default_result(self) -> Dict:
        """Return default result on error"""
        return {
            'state': LightingState.DAY.value,
            'brightness': 0.5,
            'saturation': 0.5,
            'is_ir': False,
            'confidence': 0.0,
            'raw_brightness': 0.5,
            'raw_saturation': 0.5
        }
    
    def should_trigger_action(
        self,
        current_state: str,
        previous_state: Optional[str],
        enable_actions: bool
    ) -> bool:
        """
        Check if state change should trigger actions
        
        Args:
            current_state: Current lighting state
            previous_state: Previous lighting state (can be None)
            enable_actions: Whether actions are enabled
            
        Returns:
            True if actions should be triggered
        """
        return enable_actions and previous_state is not None and current_state != previous_state
    
    def reset_history(self):
        """Reset smoothing history"""
        self.brightness_history = []
        self.saturation_history = []
    
    def get_state_description(self, state: str) -> str:
        """Get human-readable description of state"""
        descriptions = {
            'day': 'Daytime - Normal lighting conditions',
            'dusk': 'Dusk/Dawn - Transitional lighting',
            'night': 'Nighttime - Low light conditions'
        }
        return descriptions.get(state, 'Unknown state')


