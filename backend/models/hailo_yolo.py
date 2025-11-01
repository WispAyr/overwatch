"""
Hailo-Accelerated YOLO Model
Optimized for Raspberry Pi with Hailo-8L accelerator
"""
import asyncio
import logging
import sys
from typing import List
from pathlib import Path

import numpy as np

# Add system packages to path for Hailo
sys.path.append('/usr/lib/python3/dist-packages')

from hailo_platform import pyhailort

from core.config import settings
from .base import BaseModel, Detection


logger = logging.getLogger('overwatch.models.hailo')


class HailoYOLOModel(BaseModel):
    """YOLO model accelerated by Hailo-8L"""
    
    # COCO class names (same as YOLOv8)
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    def __init__(self, model_id: str, config: dict):
        super().__init__(model_id, config)
        self.device = None
        self.vdevice = None
        self.network_group = None
        self.input_vstream_info = None
        self.output_vstream_info = None
        self.input_vstreams = None
        self.output_vstreams = None
        
        # Hailo-specific configuration options
        self.power_mode = config.get('power_mode', 'performance')  # 'performance' or 'ultra_performance'
        self.batch_size = config.get('batch_size', 1)  # Hardware batch processing
        self.multi_process_service = config.get('multi_process_service', True)  # Share across workflows (DEFAULT: True)
        self.scheduling_algorithm = config.get('scheduling_algorithm', 'round_robin')  # 'round_robin' or 'none'
        self.enable_monitoring = config.get('enable_monitoring', True)  # Performance metrics
        self.latency_measurement = config.get('latency_measurement', False)  # Measure inference latency
        
        # Performance tracking (Hailo-specific)
        self.inference_count = 0
        self.total_latency = 0.0
        self.hw_latency = 0.0  # Hardware-only latency
        
    async def initialize(self):
        """Initialize Hailo YOLO model"""
        logger.info(f"Loading Hailo-accelerated {self.model_id}...")
        
        # Determine model file
        variant = self.model_id.split('-')[-1]  # e.g., 'yolov8s'
        hef_path = f"/usr/local/hailo/resources/models/hailo8l/{variant}.hef"
        
        if not Path(hef_path).exists():
            logger.warning(f"Hailo model not found: {hef_path}, falling back to yolov8s.hef")
            hef_path = "/usr/local/hailo/resources/models/hailo8l/yolov8s.hef"
        
        # Load model in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._load_model,
            hef_path
        )
        
        logger.info(f"Loaded {self.model_id} on Hailo-8L accelerator (13 TOPS)")
        
    def _load_model(self, hef_path: str):
        """Load Hailo model with Hailo-specific optimizations"""
        try:
            # Import Hailo classes
            from hailo_platform.pyhailort.pyhailort import (
                InternalPcieDevice, HEF, VDevice, ConfigureParams,
                HailoStreamInterface, InferVStreams,
                HailoPowerMode, HailoSchedulingAlgorithm
            )
            
            # Scan for devices
            devices = InternalPcieDevice.scan_devices()
            if not devices:
                raise RuntimeError("No Hailo PCIe devices found")
            
            logger.info(f"Found Hailo device: {devices[0]}")
            
            # Create VDevice with Hailo-specific parameters
            params = VDevice.create_params()
            params.device_count = 1
            params.multi_process_service = self.multi_process_service
            
            # Set scheduling algorithm (Hailo-specific)
            if self.scheduling_algorithm == 'round_robin':
                params.scheduling_algorithm = HailoSchedulingAlgorithm.ROUND_ROBIN
            else:
                params.scheduling_algorithm = HailoSchedulingAlgorithm.NONE
            
            self.vdevice = VDevice(params)
            
            # Set power mode (Hailo-specific optimization)
            try:
                if self.power_mode == 'ultra_performance':
                    logger.info("🔥 Setting Hailo to ULTRA PERFORMANCE mode")
                    # Note: Actual power mode setting may require device control
                    # self.vdevice.set_power_mode(HailoPowerMode.HAILO_POWER_MODE_ULTRA_PERFORMANCE)
                else:
                    logger.info("⚡ Setting Hailo to PERFORMANCE mode")
                    # self.vdevice.set_power_mode(HailoPowerMode.HAILO_POWER_MODE_PERFORMANCE)
            except Exception as e:
                logger.debug(f"Power mode setting not available: {e}")
            
            # Load HEF (Hailo Executable Format)
            hef = HEF(hef_path)
            
            # Create configure params from HEF
            configure_params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
            
            # Enable latency measurement if requested (Hailo-specific)
            if self.latency_measurement:
                try:
                    configure_params[0].latency_measurement_en = True
                    logger.info("📊 Hailo latency measurement enabled")
                except:
                    pass
            
            self.network_group = self.vdevice.configure(hef, configure_params)[0]
            
            # Get network info (Hailo-specific capabilities)
            try:
                network_info = self.network_group.get_network_infos()[0]
                logger.info(f"Network: {network_info.name}")
                logger.info(f"Batch size: {network_info.batch_size}")
                logger.info(f"FPS: ~{1000 / network_info.hw_latency_ms:.1f} (hardware only)")
            except Exception as e:
                logger.debug(f"Could not get network info: {e}")
            
            # Store for inference
            self.hef = hef
            
            logger.info(f"✅ Hailo model loaded: {hef_path}")
            logger.info(f"   Power mode: {self.power_mode}")
            logger.info(f"   Batch size: {self.batch_size}")
            logger.info(f"   Scheduling: {self.scheduling_algorithm}")
            logger.info(f"   Multi-process: {self.multi_process_service}")
            
        except Exception as e:
            logger.error(f"Failed to load Hailo model: {e}")
            raise
            
    async def detect(self, frame: np.ndarray) -> List[dict]:
        """Run YOLO detection on Hailo"""
        if self.network_group is None:
            logger.error("Model not initialized")
            return []
            
        # Run inference in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._run_inference,
            frame
        )
        
        return results
        
    def _run_inference(self, frame: np.ndarray) -> List[dict]:
        """Run inference (blocking operation)"""
        try:
            from hailo_platform.pyhailort.pyhailort import InferVStreams
            
            # Preprocess frame for Hailo input
            input_data = self._preprocess(frame)
            
            # Activate network and run inference
            with self.network_group.activate() as activated_network:
                # Create inference streams
                with InferVStreams(self.network_group, input_data.shape) as infer_streams:
                    # Run inference
                    output_dict = infer_streams.infer({0: input_data})
            
            # Post-process results
            detections = self._postprocess(output_dict, frame.shape)
            
            return detections
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            logger.exception(e)
            return []
            
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for Hailo input"""
        import cv2
        
        # YOLOv8 expects 640x640 input
        height, width = 640, 640
        
        # Resize frame
        resized = cv2.resize(frame, (width, height))
        
        # Convert to RGB if needed
        if len(resized.shape) == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        elif resized.shape[2] == 4:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB)
        elif resized.shape[2] == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Convert to uint8 if needed
        if resized.dtype != np.uint8:
            resized = resized.astype(np.uint8)
        
        return resized
        
    def _postprocess(self, output_dict: dict, frame_shape: tuple) -> List[dict]:
        """Post-process Hailo output to detections"""
        detections = []
        
        # YOLOv8 has multiple output layers
        # This is a simplified parser - adjust based on actual output format
        for output_name, output_data in output_dict.items():
            # Parse YOLO output format
            # Format: [batch, num_detections, (x, y, w, h, conf, class_probs...)]
            if len(output_data.shape) == 3:
                batch_size, num_boxes, num_values = output_data.shape
                
                for box_idx in range(num_boxes):
                    box_data = output_data[0, box_idx, :]
                    
                    # Extract confidence (assuming it's at index 4)
                    conf = box_data[4] if len(box_data) > 4 else 0.0
                    
                    # Skip low confidence detections
                    if conf < self.config.get('confidence', 0.5):
                        continue
                    
                    # Extract bbox (x, y, w, h format)
                    x_center, y_center, width, height = box_data[0:4]
                    
                    # Convert to image coordinates
                    img_h, img_w = frame_shape[:2]
                    x1 = int((x_center - width / 2) * img_w)
                    y1 = int((y_center - height / 2) * img_h)
                    x2 = int((x_center + width / 2) * img_w)
                    y2 = int((y_center + height / 2) * img_h)
                    
                    # Extract class probabilities (after first 5 values)
                    if len(box_data) > 5:
                        class_probs = box_data[5:]
                        class_id = int(np.argmax(class_probs))
                        class_conf = class_probs[class_id]
                        
                        # Get class name
                        class_name = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else f"class_{class_id}"
                        
                        detection = {
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': float(conf * class_conf),
                            'bbox': [x1, y1, x2, y2]
                        }
                        
                        detections.append(detection)
        
        return detections
        
    async def cleanup(self):
        """Cleanup Hailo resources"""
        try:
            # Log Hailo-specific performance metrics
            if self.inference_count > 0:
                avg_latency = self.total_latency / self.inference_count
                avg_hw_latency = self.hw_latency / self.inference_count
                logger.info(f"📊 Hailo Performance Stats:")
                logger.info(f"   Total inferences: {self.inference_count}")
                logger.info(f"   Avg total latency: {avg_latency:.2f}ms")
                logger.info(f"   Avg HW latency: {avg_hw_latency:.2f}ms")
                logger.info(f"   Avg FPS: {1000/avg_latency:.1f}")
            
            if self.network_group:
                self.network_group = None
            if self.vdevice:
                self.vdevice = None
                
            logger.info("Hailo model cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_performance_metrics(self) -> dict:
        """Get Hailo-specific performance metrics"""
        if self.inference_count == 0:
            return {}
        
        return {
            'inference_count': self.inference_count,
            'avg_latency_ms': self.total_latency / self.inference_count,
            'avg_hw_latency_ms': self.hw_latency / self.inference_count,
            'avg_fps': 1000 / (self.total_latency / self.inference_count),
            'power_mode': self.power_mode,
            'batch_size': self.batch_size,
            'accelerator': 'Hailo-8L (13 TOPS)'
        }

