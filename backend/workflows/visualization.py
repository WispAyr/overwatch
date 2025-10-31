"""
X-RAY Mode Visualization
Advanced visualization utilities for AI model outputs
Draws bounding boxes, labels, heatmaps, schematics, etc.
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import colorsys


# Color schemes for X-RAY mode
COLOR_SCHEMES = {
    'default': {
        'method': 'hash',  # Generate from class hash
        'saturation': 0.9,
        'value': 0.9
    },
    'confidence': {
        'method': 'gradient',  # Color based on confidence
        'low_color': (0, 0, 255),    # Red (BGR)
        'high_color': (0, 255, 0)    # Green (BGR)
    },
    'class_specific': {
        'method': 'predefined',
        'colors': {
            'person': (255, 100, 100),      # Light blue
            'car': (100, 255, 100),         # Light green
            'truck': (100, 200, 255),       # Orange
            'bus': (200, 100, 255),         # Purple
            'motorcycle': (255, 255, 100),  # Cyan
            'bicycle': (100, 255, 255),     # Yellow
            'default': (200, 200, 200)      # Gray
        }
    },
    'thermal': {
        'method': 'thermal',  # Thermal camera style
        'colormap': cv2.COLORMAP_JET
    },
    'neon': {
        'method': 'neon',  # Bright neon colors
        'saturation': 1.0,
        'value': 1.0
    }
}


class DetectionVisualizer:
    """X-RAY Mode - Visualizes what AI models see"""
    
    def __init__(self, color_scheme: str = 'default'):
        self.class_colors = {}
        self.color_scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['default'])
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.thickness = 2
        self.label_thickness = 1
        
    def get_class_color(self, class_name: str, confidence: float = 1.0) -> Tuple[int, int, int]:
        """Get color for a class based on color scheme"""
        method = self.color_scheme.get('method', 'hash')
        
        if method == 'hash':
            # Generate color based on class hash
            if class_name not in self.class_colors:
                hue = (hash(class_name) % 360) / 360.0
                sat = self.color_scheme.get('saturation', 0.9)
                val = self.color_scheme.get('value', 0.9)
                rgb = colorsys.hsv_to_rgb(hue, sat, val)
                self.class_colors[class_name] = (
                    int(rgb[2] * 255),
                    int(rgb[1] * 255),
                    int(rgb[0] * 255)
                )
            return self.class_colors[class_name]
        
        elif method == 'gradient':
            # Color based on confidence
            low = self.color_scheme['low_color']
            high = self.color_scheme['high_color']
            return tuple(int(low[i] + (high[i] - low[i]) * confidence) for i in range(3))
        
        elif method == 'predefined':
            # Use predefined colors
            colors = self.color_scheme['colors']
            return colors.get(class_name, colors.get('default', (200, 200, 200)))
        
        elif method == 'neon':
            # Bright neon colors
            if class_name not in self.class_colors:
                hue = (hash(class_name) % 360) / 360.0
                rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                self.class_colors[class_name] = (
                    int(rgb[2] * 255),
                    int(rgb[1] * 255),
                    int(rgb[0] * 255)
                )
            return self.class_colors[class_name]
        
        else:
            return (200, 200, 200)
    
    def create_schematic_frame(
        self,
        width: int,
        height: int,
        background_color: Tuple[int, int, int] = (20, 20, 20)
    ) -> np.ndarray:
        """Create blank schematic frame (no original image)"""
        return np.full((height, width, 3), background_color, dtype=np.uint8)
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        show_confidence: bool = True,
        show_labels: bool = True,
        show_boxes: bool = True,
        min_confidence: float = 0.0,
        schematic_mode: bool = False
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input frame
            detections: List of detection dicts with bbox, class, confidence
            show_confidence: Show confidence scores
            show_labels: Show class labels
            show_boxes: Show bounding boxes
            min_confidence: Minimum confidence to display
            schematic_mode: If True, draw on blank canvas (boxes only, no image)
            
        Returns:
            Annotated frame
        """
        if schematic_mode:
            # Create blank canvas for schematic view
            annotated = self.create_schematic_frame(frame.shape[1], frame.shape[0])
        else:
            annotated = frame.copy()
        
        for det in detections:
            confidence = det.get('confidence', 0)
            if confidence < min_confidence:
                continue
            
            # Get bounding box
            bbox = det.get('bbox', {})
            if not bbox:
                continue
            
            x = int(bbox.get('x', 0))
            y = int(bbox.get('y', 0))
            w = int(bbox.get('width', 0))
            h = int(bbox.get('height', 0))
            
            # Get class info
            class_name = det.get('class', det.get('class_name', 'unknown'))
            color = self.get_class_color(class_name, confidence)
            
            # Draw bounding box
            if show_boxes:
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, self.thickness)
            
            # Draw label
            if show_labels:
                label = class_name
                if show_confidence:
                    label += f" {confidence:.2f}"
                
                # Get label size
                (label_w, label_h), baseline = cv2.getTextSize(
                    label, self.font, self.font_scale, self.label_thickness
                )
                
                # Draw label background
                cv2.rectangle(
                    annotated,
                    (x, y - label_h - 10),
                    (x + label_w + 10, y),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    annotated,
                    label,
                    (x + 5, y - 5),
                    self.font,
                    self.font_scale,
                    (255, 255, 255),
                    self.label_thickness
                )
            
            # Draw track ID if available
            track_id = det.get('track_id')
            if track_id is not None and track_id >= 0:
                track_label = f"ID:{track_id}"
                cv2.putText(
                    annotated,
                    track_label,
                    (x + w - 60, y + 20),
                    self.font,
                    0.5,
                    color,
                    1
                )
        
        return annotated
    
    def draw_detection_count(
        self,
        frame: np.ndarray,
        count: int,
        position: str = 'top-left'
    ) -> np.ndarray:
        """Draw detection count overlay"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        text = f"Detections: {count}"
        (text_w, text_h), _ = cv2.getTextSize(text, self.font, 0.8, 2)
        
        # Determine position
        if position == 'top-left':
            x, y = 10, 30
        elif position == 'top-right':
            x, y = w - text_w - 20, 30
        elif position == 'bottom-left':
            x, y = 10, h - 20
        else:  # bottom-right
            x, y = w - text_w - 20, h - 20
        
        # Draw background
        cv2.rectangle(
            annotated,
            (x - 5, y - text_h - 5),
            (x + text_w + 5, y + 5),
            (0, 0, 0),
            -1
        )
        
        # Draw text
        cv2.putText(
            annotated,
            text,
            (x, y),
            self.font,
            0.8,
            (0, 255, 0),
            2
        )
        
        return annotated
    
    def draw_heatmap(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET,
        schematic_mode: bool = False
    ) -> np.ndarray:
        """Draw heatmap of detection locations"""
        h, w = frame.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Add Gaussian blobs for each detection
        for det in detections:
            bbox = det.get('bbox', {})
            if not bbox:
                continue
            
            cx = int(bbox.get('x', 0) + bbox.get('width', 0) / 2)
            cy = int(bbox.get('y', 0) + bbox.get('height', 0) / 2)
            
            # Create Gaussian blob
            sigma = max(bbox.get('width', 50), bbox.get('height', 50)) / 3
            y, x = np.ogrid[:h, :w]
            gaussian = np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
            heatmap += gaussian
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            colormap
        )
        
        if schematic_mode:
            # Pure heatmap on black background
            return heatmap_colored
        else:
            # Blend with original frame
            annotated = cv2.addWeighted(frame, 1 - alpha, heatmap_colored, alpha, 0)
            return annotated
    
    def draw_zones(
        self,
        frame: np.ndarray,
        zones: List[Dict],
        show_names: bool = True
    ) -> np.ndarray:
        """Draw detection zones"""
        annotated = frame.copy()
        
        for zone in zones:
            points = zone.get('points', [])
            if len(points) < 3:
                continue
            
            # Convert points to numpy array
            pts = np.array([[p['x'], p['y']] for p in points], dtype=np.int32)
            
            # Get zone info
            name = zone.get('name', 'Zone')
            color = zone.get('color', (0, 255, 255))
            if isinstance(color, str):
                # Convert hex to BGR
                color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))
            
            # Draw zone polygon
            cv2.polylines(annotated, [pts], True, color, 2)
            
            # Fill with transparency
            overlay = annotated.copy()
            cv2.fillPoly(overlay, [pts], color)
            annotated = cv2.addWeighted(annotated, 0.7, overlay, 0.3, 0)
            
            # Draw zone name
            if show_names:
                centroid_x = int(np.mean([p['x'] for p in points]))
                centroid_y = int(np.mean([p['y'] for p in points]))
                
                cv2.putText(
                    annotated,
                    name,
                    (centroid_x - 30, centroid_y),
                    self.font,
                    0.7,
                    (255, 255, 255),
                    2
                )
        
        return annotated
    
    def create_thumbnail(
        self,
        frame: np.ndarray,
        max_width: int = 400,
        max_height: int = 300
    ) -> np.ndarray:
        """Create thumbnail of frame"""
        h, w = frame.shape[:2]
        
        # Calculate scaling
        scale = min(max_width / w, max_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


class PoseVisualizer:
    """Visualizes pose estimation results"""
    
    # COCO keypoint pairs for skeleton
    SKELETON = [
        [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
        [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
        [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
        [2, 4], [3, 5], [4, 6], [5, 7]
    ]
    
    def draw_pose(
        self,
        frame: np.ndarray,
        keypoints: List[Dict],
        confidence_threshold: float = 0.5
    ) -> np.ndarray:
        """Draw pose keypoints and skeleton"""
        annotated = frame.copy()
        
        for person in keypoints:
            kpts = person.get('keypoints', [])
            if not kpts:
                continue
            
            # Draw skeleton
            for pair in self.SKELETON:
                if pair[0] <= len(kpts) and pair[1] <= len(kpts):
                    pt1 = kpts[pair[0] - 1]
                    pt2 = kpts[pair[1] - 1]
                    
                    if (pt1.get('confidence', 0) > confidence_threshold and
                        pt2.get('confidence', 0) > confidence_threshold):
                        cv2.line(
                            annotated,
                            (int(pt1['x']), int(pt1['y'])),
                            (int(pt2['x']), int(pt2['y'])),
                            (0, 255, 0),
                            2
                        )
            
            # Draw keypoints
            for kpt in kpts:
                if kpt.get('confidence', 0) > confidence_threshold:
                    cv2.circle(
                        annotated,
                        (int(kpt['x']), int(kpt['y'])),
                        4,
                        (0, 0, 255),
                        -1
                    )
        
        return annotated


class SegmentationVisualizer:
    """Visualizes instance segmentation masks - X-RAY for segmentation models"""
    
    def __init__(self, color_scheme: str = 'default'):
        self.color_scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['default'])
        self.class_colors = {}
    
    def get_mask_color(self, class_name: str, confidence: float = 1.0, instance_id: int = 0) -> Tuple[int, int, int]:
        """Get color for segmentation mask"""
        method = self.color_scheme.get('method', 'hash')
        
        if method == 'hash':
            # Unique color per instance
            hue = ((hash(class_name) + instance_id * 137) % 360) / 360.0
            sat = self.color_scheme.get('saturation', 0.9)
            val = self.color_scheme.get('value', 0.9)
            rgb = colorsys.hsv_to_rgb(hue, sat, val)
            return (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
        
        elif method == 'gradient':
            # Confidence-based coloring
            low = self.color_scheme['low_color']
            high = self.color_scheme['high_color']
            return tuple(int(low[i] + (high[i] - low[i]) * confidence) for i in range(3))
        
        elif method == 'predefined':
            colors = self.color_scheme['colors']
            return colors.get(class_name, colors.get('default', (200, 200, 200)))
        
        else:
            return (200, 200, 200)
    
    def draw_masks(
        self,
        frame: np.ndarray,
        masks: List[Dict],
        alpha: float = 0.5,
        schematic_mode: bool = False,
        show_contours: bool = True,
        show_labels: bool = True
    ) -> np.ndarray:
        """
        Draw segmentation masks with transparency
        
        X-RAY Modes for Segmentation:
        - Normal: Colored masks over original image
        - Schematic: Pure masks on black background
        - Contour: Only outlines
        - Solid: Fully opaque colored regions
        """
        if schematic_mode:
            annotated = np.zeros_like(frame)
        else:
            annotated = frame.copy()
        
        for idx, mask_data in enumerate(masks):
            mask = mask_data.get('mask')
            if mask is None:
                continue
            
            # Get mask info
            class_name = mask_data.get('class', 'object')
            confidence = mask_data.get('confidence', 1.0)
            color = self.get_mask_color(class_name, confidence, idx)
            
            # Create colored mask
            colored_mask = np.zeros_like(frame)
            colored_mask[mask > 0] = color
            
            # Blend with frame based on mode
            if schematic_mode:
                # Full opacity on black
                annotated[mask > 0] = color
            else:
                # Transparent overlay
                annotated = cv2.addWeighted(annotated, 1, colored_mask, alpha, 0)
            
            # Draw contour
            if show_contours:
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8),
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(annotated, contours, -1, color, 2)
            
            # Draw label at centroid
            if show_labels:
                M = cv2.moments(mask.astype(np.uint8))
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    label = f"{class_name} {confidence:.2f}"
                    cv2.putText(
                        annotated,
                        label,
                        (cx - 40, cy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )
        
        return annotated
    
    def draw_mask_overlay(
        self,
        frame: np.ndarray,
        masks: List[Dict],
        mode: str = 'blend'  # 'blend', 'contour', 'solid', 'schematic'
    ) -> np.ndarray:
        """
        Advanced mask overlay with multiple visualization modes
        
        Modes:
        - blend: Semi-transparent colored masks
        - contour: Only mask outlines
        - solid: Fully opaque masks
        - schematic: Masks only on black background
        """
        if mode == 'schematic':
            return self.draw_masks(frame, masks, alpha=1.0, schematic_mode=True, show_contours=True)
        elif mode == 'contour':
            return self.draw_masks(frame, masks, alpha=0.0, schematic_mode=False, show_contours=True)
        elif mode == 'solid':
            return self.draw_masks(frame, masks, alpha=0.8, schematic_mode=False, show_contours=True)
        else:  # blend
            return self.draw_masks(frame, masks, alpha=0.5, schematic_mode=False, show_contours=True)
    
    def create_mask_heatmap(
        self,
        frame: np.ndarray,
        masks: List[Dict],
        colormap: int = cv2.COLORMAP_VIRIDIS
    ) -> np.ndarray:
        """Create heatmap showing mask density/overlap"""
        h, w = frame.shape[:2]
        density_map = np.zeros((h, w), dtype=np.float32)
        
        # Accumulate masks
        for mask_data in masks:
            mask = mask_data.get('mask')
            if mask is not None:
                density_map += mask.astype(np.float32)
        
        # Normalize
        if density_map.max() > 0:
            density_map = density_map / density_map.max()
        
        # Apply colormap
        heatmap = cv2.applyColorMap(
            (density_map * 255).astype(np.uint8),
            colormap
        )
        
        # Blend
        return cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)
    
    def extract_object_cutouts(
        self,
        frame: np.ndarray,
        masks: List[Dict]
    ) -> List[np.ndarray]:
        """Extract individual masked objects as separate images"""
        cutouts = []
        
        for mask_data in masks:
            mask = mask_data.get('mask')
            if mask is None:
                continue
            
            # Create cutout with alpha channel
            object_cutout = frame.copy()
            object_cutout[mask == 0] = 0  # Zero out non-mask regions
            
            cutouts.append(object_cutout)
        
        return cutouts
    
    def create_mask_comparison(
        self,
        frame: np.ndarray,
        masks: List[Dict],
        layout: str = 'side-by-side'  # 'side-by-side', 'quad', 'overlay'
    ) -> np.ndarray:
        """
        Create comparison view with multiple mask visualizations
        
        Layouts:
        - side-by-side: Original | Masked
        - quad: Original | Contours | Masks | Heatmap
        - overlay: Combined view
        """
        if layout == 'side-by-side':
            masked = self.draw_masks(frame, masks, alpha=0.6)
            return np.hstack([frame, masked])
        
        elif layout == 'quad':
            # Original
            original = frame.copy()
            
            # Contours only
            contours = self.draw_masks(frame, masks, alpha=0.0, show_contours=True, show_labels=False)
            
            # Solid masks
            solid_masks = self.draw_masks(frame, masks, alpha=0.7, show_contours=True)
            
            # Heatmap
            heatmap = self.create_mask_heatmap(frame, masks)
            
            # Resize for quad view
            h, w = frame.shape[:2]
            new_h, new_w = h // 2, w // 2
            
            top_left = cv2.resize(original, (new_w, new_h))
            top_right = cv2.resize(contours, (new_w, new_h))
            bottom_left = cv2.resize(solid_masks, (new_w, new_h))
            bottom_right = cv2.resize(heatmap, (new_w, new_h))
            
            # Add labels
            cv2.putText(top_left, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(top_right, "Contours", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(bottom_left, "Masks", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(bottom_right, "Density", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Combine
            top = np.hstack([top_left, top_right])
            bottom = np.hstack([bottom_left, bottom_right])
            return np.vstack([top, bottom])
        
        else:  # overlay
            return self.draw_masks(frame, masks, alpha=0.5, show_contours=True, show_labels=True)

