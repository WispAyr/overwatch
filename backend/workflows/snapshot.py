"""
Snapshot Handler
Captures and saves frame snapshots with detection overlays
"""
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

from core.config import settings


logger = logging.getLogger('overwatch.workflows.snapshot')


class SnapshotHandler:
    """Handles snapshot creation and storage"""
    
    def __init__(self):
        self.snapshot_dir = Path(settings.SNAPSHOT_DIR)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
    def save_snapshot(
        self,
        frame: np.ndarray,
        event_id: str,
        detections: list = None,
        draw_boxes: bool = True
    ) -> str:
        """
        Save a snapshot with optional detection overlays
        
        Args:
            frame: Video frame (BGR)
            event_id: Unique event ID
            detections: List of detections to overlay
            draw_boxes: Whether to draw bounding boxes
            
        Returns:
            Path to saved snapshot
        """
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{event_id}_{timestamp}.jpg"
        filepath = self.snapshot_dir / filename
        
        # Copy frame to avoid modifying original
        snapshot = frame.copy()
        
        # Draw detection boxes if requested
        if draw_boxes and detections:
            snapshot = self._draw_detections(snapshot, detections)
            
        # Save snapshot
        cv2.imwrite(str(filepath), snapshot, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        logger.info(f"Saved snapshot: {filename}")
        
        return str(filepath)
        
    def _draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            bbox = det.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = map(int, bbox)
            confidence = det.get('confidence', 0)
            class_name = det.get('class_name', 'unknown')
            
            # Draw bounding box
            color = (0, 255, 0)  # Green
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label = f"{class_name} {confidence:.2%}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(
                frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )
            
        return frame


