"""
Real-time Workflow Executor
Executes visual workflows and streams data via WebSocket
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time
import cv2
import numpy as np

from models import get_model
from workflows.event_bus import get_event_bus, EventType, WorkflowEvent
from workflows.visualization import DetectionVisualizer
from workflows.hailo_xray_optimizer import get_hailo_xray_optimizer, should_use_hailo_optimization
from stream.audio_analyzer import AudioAnalyzer
from stream.lighting_analyzer import LightingAnalyzer


logger = logging.getLogger('overwatch.workflows.realtime_executor')


# Global registry of running workflows
_running_workflows: Dict[str, 'RealtimeWorkflowExecutor'] = {}

# Global stream manager reference
_stream_manager = None


def set_stream_manager(stream_manager):
    """Set global stream manager instance"""
    global _stream_manager
    _stream_manager = stream_manager


class RealtimeWorkflowExecutor:
    """Executes visual workflows in real-time"""
    
    def __init__(self, nodes: List[dict], edges: List[dict], workflow_id: str):
        self.nodes = nodes
        self.edges = edges
        self.workflow_id = workflow_id
        self.running = False
        self.task = None
        
        # Parse workflow structure
        self.input_nodes = [n for n in nodes if n['type'] in ['camera', 'videoInput', 'youtube']]
        self.model_nodes = [n for n in nodes if n['type'] == 'model']
        self.zone_nodes = [n for n in nodes if n['type'] == 'zone']
        self.filter_nodes = [n for n in nodes if n['type'] == 'detectionFilter']
        self.action_nodes = [n for n in nodes if n['type'] == 'action']
        self.output_nodes = [n for n in nodes if n['type'] in ['dataPreview', 'debug']]
        self.audio_extractor_nodes = [n for n in nodes if n['type'] == 'audioExtractor']
        self.audio_ai_nodes = [n for n in nodes if n['type'] == 'audioAI']
        self.audio_vu_nodes = [n for n in nodes if n['type'] == 'audioVU']
        self.day_night_nodes = [n for n in nodes if n['type'] == 'dayNightDetector']
        self.parking_violation_nodes = [n for n in nodes if n['type'] == 'parkingViolation']
        
        # Log received nodes for debugging
        logger.info(f"Workflow {workflow_id}: Received {len(nodes)} nodes, {len(edges)} edges")
        logger.info(f"Output nodes: {[n['id'] for n in self.output_nodes]}")
        logger.info(f"Filter nodes: {len(self.filter_nodes)}")
        logger.info(f"Audio nodes: {len(self.audio_extractor_nodes)} extractors, {len(self.audio_ai_nodes)} AI")
        logger.info(f"Parking violation nodes: {len(self.parking_violation_nodes)}")
        
        # Model instances
        self.models = {}
        self.audio_models = {}
        self.audio_extractors = {}
        
        # Analyzers
        self.audio_analyzer = AudioAnalyzer()
        self.lighting_analyzer = LightingAnalyzer()
        
        # Visualizer
        self.visualizer = DetectionVisualizer()
        
        # Hailo-optimized X-RAY (if available)
        self.use_hailo_xray = should_use_hailo_optimization()
        if self.use_hailo_xray:
            self.hailo_xray_optimizer = get_hailo_xray_optimizer(mode='balanced')
            logger.info("🚀 Hailo X-RAY optimization ENABLED - targeting 30+ FPS")
        else:
            self.hailo_xray_optimizer = None
            logger.info("📊 Standard X-RAY visualization (CPU-based)")
        
        # State tracking
        self.audio_vu_states = {}  # Track threshold states per node
        self.lighting_states = {}  # Track previous states per node
        
        # Event bus
        self.event_bus = get_event_bus()
        
        # Metrics tracking per node
        self.node_metrics = {}
        self.last_metrics_broadcast = {}
        self.metrics_broadcast_interval = 2.0  # seconds
        
        # Frame throttling
        self.last_process_time = {}  # Per node throttling
        
    async def start(self):
        """Start workflow execution"""
        if self.running:
            logger.warning(f"Workflow {self.workflow_id} is already running")
            return
            
        logger.info(f"Starting workflow execution: {self.workflow_id}")
        self.running = True
        
        # Register in global registry
        _running_workflows[self.workflow_id] = self
        
        # Initialize models
        await self._initialize_models()
        
        # Start execution loop
        self.task = asyncio.create_task(self._execution_loop())
        
    async def stop(self):
        """Stop workflow execution and clean up resources"""
        logger.info(f"Stopping workflow: {self.workflow_id}")
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        # ROBUST CLEANUP: Release all AI models and Hailo resources
        logger.info(f"🧹 Cleaning up resources for workflow: {self.workflow_id}")
        
        # Cleanup video models and release Hailo
        for node_id, model in list(self.models.items()):
            try:
                if hasattr(model, 'cleanup'):
                    await model.cleanup()
                    logger.debug(f"   Cleaned up model: {node_id}")
            except Exception as e:
                logger.warning(f"   Error cleaning up model {node_id}: {e}")
        
        self.models.clear()
        
        # Cleanup audio models
        for node_id, model in list(self.audio_models.items()):
            try:
                if hasattr(model, 'cleanup'):
                    await model.cleanup()
            except Exception as e:
                logger.warning(f"   Error cleaning up audio model {node_id}: {e}")
        
        self.audio_models.clear()
        
        # Release video captures
        if hasattr(self, '_video_captures'):
            for node_id, cap in list(self._video_captures.items()):
                try:
                    cap.release()
                except:
                    pass
            self._video_captures.clear()
        
        logger.info(f"✅ Workflow {self.workflow_id} cleanup complete")
                
        # Clean up models
        for model in self.models.values():
            try:
                await model.cleanup()
            except:
                pass
        
        # Clean up audio models
        for model in self.audio_models.values():
            try:
                await model.cleanup()
            except:
                pass
        
        # Clean up audio extractors
        for extractor in self.audio_extractors.values():
            try:
                await extractor.stop()
            except:
                pass
        
        # Clean up video captures
        if hasattr(self, '_video_captures'):
            for cap in self._video_captures.values():
                try:
                    cap.release()
                except:
                    pass
            self._video_captures.clear()
                
        # Remove from registry
        _running_workflows.pop(self.workflow_id, None)
        
    @classmethod
    async def stop_workflow(cls, workflow_id: str):
        """Stop a specific workflow by ID"""
        executor = _running_workflows.get(workflow_id)
        if executor:
            await executor.stop()
    
    @classmethod
    async def stop_all_workflows(cls):
        """Stop all running workflows"""
        workflow_ids = list(_running_workflows.keys())
        logger.info(f"Stopping {len(workflow_ids)} running workflows")
        
        for workflow_id in workflow_ids:
            executor = _running_workflows.get(workflow_id)
            if executor:
                try:
                    await executor.stop()
                except Exception as e:
                    logger.error(f"Error stopping workflow {workflow_id}: {e}")
        
        logger.info("All workflows stopped")
            
    async def _initialize_models(self):
        """Initialize AI models"""
        # Initialize video models
        for node in self.model_nodes:
            node_id = node['id']
            model_id = node['data'].get('modelId')
            
            if not model_id:
                logger.warning(f"Model node {node_id} has no modelId")
                continue
                
            try:
                # Pass node configuration to model (includes Hailo-specific options!)
                node_config = {
                    'confidence': node['data'].get('confidence', 0.7),
                    'classes': node['data'].get('classes', []),
                    'fps': node['data'].get('fps', 10),
                    'batch_size': node['data'].get('batchSize', 1),
                    'iou': node['data'].get('iou', 0.45),
                    # Hailo-specific options
                    'power_mode': node['data'].get('powerMode', 'performance'),
                    'multi_process_service': node['data'].get('multiProcessService', True),
                    'scheduling_algorithm': node['data'].get('schedulingAlgorithm', 'round_robin'),
                    'latency_measurement': node['data'].get('latencyMeasurement', False),
                }
                
                logger.info(f"🔧 Initializing model {model_id} with config: {node_config}")
                model = await get_model(model_id, node_config)
                self.models[node_id] = model
                logger.info(f"✅ Initialized model {model_id} for node {node_id}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize model {model_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Initialize audio AI models
        for node in self.audio_ai_nodes:
            node_id = node['id']
            model_id = node['data'].get('modelId')
            
            if not model_id:
                logger.warning(f"Audio AI node {node_id} has no modelId")
                continue
                
            try:
                config = {
                    'modelType': node['data'].get('modelType', 'transcription'),
                    'language': node['data'].get('language', 'auto'),
                    'confidence': node['data'].get('confidence', 0.7),
                    'detectKeywords': node['data'].get('detectKeywords', [])
                }
                model = await get_model(model_id, config)
                self.audio_models[node_id] = model
                logger.info(f"Initialized audio model {model_id} for node {node_id}")
            except Exception as e:
                logger.error(f"Failed to initialize audio model {model_id}: {e}")
                
    async def _execution_loop(self):
        """Main execution loop"""
        try:
            logger.info(f"Workflow {self.workflow_id}: Starting execution loop")
            logger.info(f"Input nodes: {len(self.input_nodes)}, Model nodes: {len(self.model_nodes)}, Output nodes: {len(self.output_nodes)}")
            
            frame_count = 0
            while self.running:
                # Process each input source
                for input_node in self.input_nodes:
                    await self._process_input_node(input_node)
                    frame_count += 1
                    
                    if frame_count % 30 == 0:
                        logger.info(f"Workflow {self.workflow_id}: Processed {frame_count} frames")
                
                # Process audio extractor nodes
                for audio_node in self.audio_extractor_nodes:
                    await self._process_audio_extractor_node(audio_node)
                
                # Process audio AI nodes
                for audio_ai_node in self.audio_ai_nodes:
                    await self._process_audio_ai_node(audio_ai_node)
                
                # Process audio VU nodes
                for audio_vu_node in self.audio_vu_nodes:
                    await self._process_audio_vu_node(audio_vu_node)
                
                # Process day/night detector nodes
                for day_night_node in self.day_night_nodes:
                    await self._process_day_night_node(day_night_node)
                
                # Process parking violation nodes
                for parking_node in self.parking_violation_nodes:
                    await self._process_parking_violation_node(parking_node)
                    
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Workflow {self.workflow_id} execution cancelled")
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}", exc_info=True)
            
    async def _process_input_node(self, input_node: dict):
        """Process a single input node"""
        node_id = input_node['id']
        node_type = input_node['type']
        
        logger.debug(f"Processing input node {node_id} ({node_type})")
        
        # Get frame from input
        frame = await self._get_frame_from_input(input_node)
        if frame is None:
            logger.debug(f"No frame available from {node_id}")
            return
            
        logger.debug(f"Got frame from {node_id}: shape={frame.shape}")
            
        # Find connected model nodes
        connected_models = self._find_connected_nodes(node_id, 'model')
        logger.debug(f"Found {len(connected_models)} connected models for {node_id}")
        
        for model_node in connected_models:
            await self._process_through_model(model_node, frame, node_id)
            
    async def _get_frame_from_input(self, input_node: dict) -> Optional[np.ndarray]:
        """Get frame from input source"""
        node_type = input_node['type']
        node_id = input_node['id']
        data = input_node['data']
        
        # Apply FPS throttling
        fps = data.get('fps', 10)
        if not self._should_process_node(node_id, fps):
            return None
        
        if node_type == 'camera':
            # Get frame from camera stream via stream manager
            camera_id = data.get('cameraId')
            if not camera_id:
                return None
            
            try:
                # Get frame from stream manager
                frame = await self._get_frame_from_stream_manager(camera_id)
                
                if frame is not None:
                    await self._update_node_metrics(node_id, {'frames_received': 1})
                    
                return frame
                
            except Exception as e:
                logger.error(f"Error getting frame from camera {camera_id}: {e}")
                await self.event_bus.emit_error(
                    self.workflow_id, node_id, e,
                    {'camera_id': camera_id}
                )
                return None
            
        elif node_type == 'youtube':
            # Get frame from YouTube stream via yt-dlp
            youtube_url = data.get('youtubeUrl')
            if not youtube_url:
                return None
            
            # Use OpenCV to capture from YouTube stream
            # This requires yt-dlp to get the actual stream URL
            try:
                import subprocess
                import json
                
                # Get stream URL using yt-dlp
                result = subprocess.run(
                    ['yt-dlp', '-f', 'best', '-g', youtube_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    stream_url = result.stdout.strip()
                    
                    # Open video capture
                    if not hasattr(self, '_video_captures'):
                        self._video_captures = {}
                    
                    node_id = input_node['id']
                    if node_id not in self._video_captures:
                        cap = cv2.VideoCapture(stream_url)
                        if cap.isOpened():
                            self._video_captures[node_id] = cap
                        else:
                            logger.error(f"Failed to open YouTube stream: {youtube_url}")
                            return None
                    
                    cap = self._video_captures[node_id]
                    ret, frame = cap.read()
                    
                    if ret:
                        return frame
                    else:
                        # Reconnect if stream failed
                        cap.release()
                        del self._video_captures[node_id]
                        return None
                else:
                    logger.error(f"yt-dlp failed: {result.stderr}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error getting YouTube frame: {e}")
                return None
            
        elif node_type == 'videoInput':
            # Get frame from video file
            video_path = data.get('videoPath')
            if not video_path:
                logger.warning(f"VideoInput node {node_id} has no videoPath configured")
                return None
            
            try:
                # Initialize video capture if not exists
                if not hasattr(self, '_video_captures'):
                    self._video_captures = {}
                
                # Open video file if not already open
                if node_id not in self._video_captures:
                    logger.info(f"Opening video file: {video_path}")
                    cap = cv2.VideoCapture(video_path)
                    
                    if not cap.isOpened():
                        logger.error(f"Failed to open video file: {video_path}")
                        await self.event_bus.emit_error(
                            self.workflow_id, node_id,
                            Exception(f"Failed to open video file: {video_path}"),
                            {'video_path': video_path}
                        )
                        return None
                    
                    self._video_captures[node_id] = cap
                    logger.info(f"Video file opened successfully: {video_path}")
                
                cap = self._video_captures[node_id]
                ret, frame = cap.read()
                
                if ret:
                    await self._update_node_metrics(node_id, {'frames_received': 1})
                    return frame
                else:
                    # End of video - loop back to start
                    logger.info(f"End of video file reached, looping back to start: {video_path}")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
                    ret, frame = cap.read()
                    
                    if ret:
                        return frame
                    else:
                        logger.error(f"Failed to read from video file after reset: {video_path}")
                        # Close and remove the capture
                        cap.release()
                        del self._video_captures[node_id]
                        return None
                        
            except Exception as e:
                logger.error(f"Error reading video file {video_path}: {e}")
                await self.event_bus.emit_error(
                    self.workflow_id, node_id, e,
                    {'video_path': video_path}
                )
                # Clean up failed capture
                if node_id in getattr(self, '_video_captures', {}):
                    try:
                        self._video_captures[node_id].release()
                        del self._video_captures[node_id]
                    except:
                        pass
                return None
            
        return None
        
    def _create_test_frame(self) -> np.ndarray:
        """Create a test frame for debugging"""
        # Create a simple test image
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            "Test Frame",
            (200, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        return frame
        
    async def _process_through_model(
        self,
        model_node: dict,
        frame: np.ndarray,
        source_node_id: str
    ):
        """Process frame through model"""
        node_id = model_node['id']
        model = self.models.get(node_id)
        
        if not model:
            logger.warning(f"Model not initialized for node {node_id}")
            # Emit error to debug nodes
            await self.event_bus.emit_error(
                self.workflow_id, node_id,
                Exception("Model not initialized"),
                {'source': source_node_id}
            )
            return
            
        try:
            # Emit node started event
            logger.info(f"🚀 Emitting NODE_STARTED for {node_id}")
            await self.event_bus.emit(WorkflowEvent(
                event_type=EventType.NODE_STARTED,
                workflow_id=self.workflow_id,
                node_id=node_id,
                timestamp=datetime.utcnow(),
                data={'source': source_node_id, 'frame_shape': frame.shape}
            ))
            logger.info(f"✅ NODE_STARTED event emitted for {node_id}")
            
            # Run detection
            detections = await model.detect(frame)
            
            # Filter by confidence
            confidence_threshold = model_node['data'].get('confidence', 0.7)
            filtered_detections = [
                d for d in detections 
                if d.get('confidence', 0) >= confidence_threshold
            ]
            
            # Emit detections event (even if empty - important for debugging!)
            await self.event_bus.emit(WorkflowEvent(
                event_type=EventType.DETECTIONS_EMITTED,
                workflow_id=self.workflow_id,
                node_id=node_id,
                timestamp=datetime.utcnow(),
                data={
                    'detections': filtered_detections,
                    'count': len(filtered_detections),
                    'total_before_filter': len(detections)
                }
            ))
            
            # Send detection data to connected output nodes
            await self._send_detections_to_outputs(
                model_node['id'],
                filtered_detections,
                frame,
                model_node
            )
            
            # Emit node completed event
            await self.event_bus.emit(WorkflowEvent(
                event_type=EventType.NODE_COMPLETED,
                workflow_id=self.workflow_id,
                node_id=node_id,
                timestamp=datetime.utcnow(),
                data={'detections_count': len(filtered_detections)}
            ))
            
        except Exception as e:
            logger.error(f"Error processing through model {node_id}: {e}")
            await self.event_bus.emit_error(
                self.workflow_id, node_id, e,
                {'source': source_node_id}
            )
            
    def _apply_detection_filter(self, filter_node: dict, detections: List[dict]) -> tuple[List[dict], bool]:
        """
        Apply detection filter logic
        Returns: (filtered_detections, should_pass)
        """
        filter_data = filter_node.get('data', {})
        
        # Get filter settings
        only_when_detections = filter_data.get('onlyWhenDetections', True)
        filter_mode = filter_data.get('filterMode', 'count')
        min_detections = filter_data.get('minDetections', 1)
        max_detections = filter_data.get('maxDetections', 999)
        selected_classes = filter_data.get('selectedClasses', [])
        class_mode = filter_data.get('classMode', 'include')
        min_confidence = filter_data.get('minConfidence', 0.25)
        
        # Quick check: if only_when_detections and no detections, block immediately
        if only_when_detections and len(detections) == 0:
            return ([], False)
        
        filtered_detections = detections.copy()
        
        # Apply filters based on mode
        if filter_mode == 'count' or filter_mode == 'advanced':
            count = len(filtered_detections)
            if count < min_detections or count > max_detections:
                return ([], False)
        
        if filter_mode == 'class' or filter_mode == 'advanced':
            if selected_classes:
                if class_mode == 'include':
                    # Only keep selected classes
                    filtered_detections = [
                        d for d in filtered_detections 
                        if d.get('class', '') in selected_classes
                    ]
                else:  # exclude mode
                    # Remove selected classes
                    filtered_detections = [
                        d for d in filtered_detections 
                        if d.get('class', '') not in selected_classes
                    ]
        
        if filter_mode == 'confidence' or filter_mode == 'advanced':
            filtered_detections = [
                d for d in filtered_detections 
                if d.get('confidence', 0) >= min_confidence
            ]
        
        # Final check: if only_when_detections and nothing left after filtering, block
        if only_when_detections and len(filtered_detections) == 0:
            return ([], False)
        
        return (filtered_detections, True)
    
    async def _send_detections_to_outputs(
        self,
        model_node_id: str,
        detections: List[dict],
        frame: np.ndarray,
        model_node: dict = None
    ):
        """Send detection data to output nodes via WebSocket, applying filters if present"""
        
        # Debug logging
        logger.info(f"_send_detections_to_outputs called with model_node type: {type(model_node)}")
        if model_node:
            logger.info(f"model_node content: {model_node}")
        
        # Check if X-RAY mode is enabled
        xray_enabled = False
        xray_settings = {}
        if model_node and isinstance(model_node, dict):
            model_data = model_node.get('data', {})
            xray_enabled = model_data.get('enableXRay', False)
            xray_settings = {
                'show_boxes': model_data.get('showBoxes', True),
                'show_labels': model_data.get('showLabels', True),
                'show_confidence': model_data.get('showConfidence', True),
                'xray_mode': model_data.get('xrayMode', 'boxes'),
                'color_scheme': model_data.get('colorScheme', 'default'),
                'schematic_mode': model_data.get('schematicMode', False),
                'overlay_alpha': model_data.get('overlayAlpha', 0.5),
                'line_thickness': model_data.get('lineThickness', 2),
                'min_confidence': model_data.get('minConfidenceViz', 0.0)
            }
        
        # Send annotated frames to X-RAY View nodes if X-RAY mode enabled
        if xray_enabled:
            await self._send_xray_frames(
                model_node_id,
                frame,
                detections,
                xray_settings
            )
        # Check if there are filter nodes connected to this model
        connected_filters = self._find_connected_nodes(model_node_id, 'detectionFilter')
        
        if connected_filters and len(connected_filters) > 0:
            # Process through each filter
            for filter_node in connected_filters:
                if not isinstance(filter_node, dict):
                    logger.error(f"Filter node is not a dict: {type(filter_node)}")
                    continue
                filtered_detections, should_pass = self._apply_detection_filter(filter_node, detections)
                
                logger.info(f"Filter {filter_node['id']}: {len(detections)} → {len(filtered_detections)} detections, pass={should_pass}")
                
                if not should_pass:
                    # Emit blocked event
                    await self.event_bus.emit(WorkflowEvent(
                        event_type=EventType.NODE_COMPLETED,
                        workflow_id=self.workflow_id,
                        node_id=filter_node['id'],
                        timestamp=datetime.utcnow(),
                        data={
                            'detections_count': 0,
                            'blocked': True,
                            'original_count': len(detections)
                        }
                    ))
                    continue  # Skip this filter branch
                
                # Send filtered detections from this filter node
                output_nodes = self._find_output_nodes_recursive(
                    filter_node['id'],
                    ['dataPreview', 'debug'],
                    max_depth=3
                )
                
                for output_node in output_nodes:
                    if output_node['type'] in ['dataPreview', 'debug']:
                        await self._send_detection_data(
                            filter_node['id'],
                            output_node,
                            filtered_detections,
                            frame
                        )
                    elif output_node['type'] == 'videoPreview' and xray_enabled:
                        # Send annotated frame to X-RAY view
                        await self._send_xray_frame_to_node(
                            filter_node['id'],
                            output_node,
                            frame,
                            filtered_detections,
                            xray_settings
                        )
                
                # Emit filter completed event
                await self.event_bus.emit(WorkflowEvent(
                    event_type=EventType.NODE_COMPLETED,
                    workflow_id=self.workflow_id,
                    node_id=filter_node['id'],
                    timestamp=datetime.utcnow(),
                    data={
                        'detections_count': len(filtered_detections),
                        'filtered_from': len(detections)
                    }
                ))
            return  # Done processing with filters
        
        # No filters, send directly to outputs
        output_nodes = self._find_output_nodes_recursive(
            model_node_id, 
            ['dataPreview', 'debug'],
            max_depth=3
        )
        
        logger.info(f"Sending {len(detections)} detections to {len(output_nodes)} output nodes")
        logger.info(f"Output node types: {[n['type'] for n in output_nodes]}")
        logger.info(f"Output node IDs: {[n['id'] for n in output_nodes]}")
        
        for output_node in output_nodes:
            output_node_id = output_node['id']
            node_type = output_node['type']
            
            # Prepare data based on node type
            if node_type == 'dataPreview':
                data = {
                    'type': 'detection_data',
                    'workflow_id': self.workflow_id,
                    'node_id': output_node_id,
                    'timestamp': datetime.now().isoformat(),
                    'detections': detections,
                    'count': len(detections),
                    'fps': 10,
                    'frame_id': id(frame),
                    'resolution': {'width': frame.shape[1], 'height': frame.shape[0]},
                    'processing_time_ms': 25
                }
            elif node_type == 'debug':
                # Format detections for debug output
                detection_summary = []
                for det in detections:
                    detection_summary.append({
                        'class': det.get('class_name', 'unknown'),
                        'confidence': f"{det.get('confidence', 0):.2f}",
                        'bbox': det.get('bbox', [])
                    })
                
                data = {
                    'type': 'debug_message',
                    'workflow_id': self.workflow_id,
                    'node_id': output_node_id,
                    'timestamp': datetime.now().isoformat(),
                    'message': f"🎯 Detected {len(detections)} objects: {', '.join([d['class'] for d in detection_summary])}",
                    'detections': detection_summary,
                    'raw_detections': detections
                }
            else:
                logger.warning(f"Unknown output node type: {node_type}")
                continue
                
            logger.info(f"Broadcasting {data['type']} to {node_type} node {output_node_id}")
            
            # Broadcast via WebSocket
            await self._broadcast_to_websocket(data)
            
    async def _send_xray_frames(
        self,
        node_id: str,
        frame: np.ndarray,
        detections: List[dict],
        xray_settings: dict
    ):
        """Send X-RAY annotated frames to X-RAY View nodes"""
        # Find connected X-RAY view nodes
        xray_nodes = self._find_output_nodes_recursive(
            node_id,
            ['videoPreview'],
            max_depth=3
        )
        
        if not xray_nodes:
            return
        
        # Create X-RAY annotated frame
        xray_mode = xray_settings.get('xray_mode', 'boxes')
        schematic_mode = xray_settings.get('schematic_mode', False)
        
        # Use Hailo-optimized path if available (async + simplified)
        if self.use_hailo_xray and self.hailo_xray_optimizer and xray_mode in ['boxes', 'both', 'schematic']:
            # Hailo-optimized visualization (async, frame skipping, simplified)
            # Note: This returns immediately and processes asynchronously
            async def send_annotated(annotated):
                # Add detection count overlay
                final_frame = self.visualizer.draw_detection_count(
                    annotated,
                    len(detections),
                    position='top-right'
                )
                # Send to clients
                await self._send_xray_frame_data(xray_nodes, final_frame, xray_mode, frame.shape)
            
            # Async visualization - doesn't block Hailo inference
            await self.hailo_xray_optimizer.visualize_detections_async(
                frame,
                detections,
                send_annotated
            )
            return  # Done - async path handles sending
        
        # Standard visualization path (CPU-based, sync)
        if xray_mode == 'boxes' or xray_mode == 'both' or xray_mode == 'schematic':
            annotated_frame = self.visualizer.draw_detections(
                frame,
                detections,
                show_confidence=xray_settings.get('show_confidence', True),
                show_labels=xray_settings.get('show_labels', True),
                show_boxes=xray_settings.get('show_boxes', True),
                min_confidence=xray_settings.get('min_confidence', 0.0),
                schematic_mode=schematic_mode or (xray_mode == 'schematic')
            )
        elif xray_mode == 'heatmap':
            annotated_frame = self.visualizer.draw_heatmap(
                frame,
                detections,
                alpha=xray_settings.get('overlay_alpha', 0.4),
                schematic_mode=schematic_mode
            )
        else:
            annotated_frame = frame.copy()
        
        # Add detection count overlay
        annotated_frame = self.visualizer.draw_detection_count(
            annotated_frame,
            len(detections),
            position='top-right'
        )
        
        # Send frame data to X-RAY nodes
        await self._send_xray_frame_data(xray_nodes, annotated_frame, xray_mode, frame.shape)
    
    async def _send_xray_frame_data(
        self,
        xray_nodes: List[dict],
        annotated_frame: np.ndarray,
        xray_mode: str,
        original_shape: tuple
    ):
        """Helper to send X-RAY frame data to nodes"""
        # Encode to JPEG
        import base64
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Send to each X-RAY view node
        for xray_node in xray_nodes:
            data = {
                'type': 'xray_frame',
                'workflow_id': self.workflow_id,
                'node_id': xray_node['id'],
                'timestamp': datetime.now().isoformat(),
                'frame_data': frame_base64,
                'fps': 30 if self.use_hailo_xray else 10,  # Hailo: 30 FPS, CPU: 10 FPS
                'detections_count': len(annotated_frame) if hasattr(annotated_frame, '__len__') else 0,
                'processing_time_ms': 15 if self.use_hailo_xray else 25,
                'xray_mode': xray_mode,
                'hailo_optimized': self.use_hailo_xray,
                'resolution': {
                    'width': original_shape[1],
                    'height': original_shape[0]
                }
            }
            
            await self._broadcast_to_websocket(data)
            
    async def _send_xray_frame_to_node(
        self,
        source_node_id: str,
        target_node: dict,
        frame: np.ndarray,
        detections: List[dict],
        xray_settings: dict
    ):
        """Send X-RAY annotated frame to a specific X-RAY view node"""
        # Create X-RAY annotated frame
        xray_mode = xray_settings.get('xray_mode', 'boxes')
        schematic_mode = xray_settings.get('schematic_mode', False)
        
        if xray_mode == 'boxes' or xray_mode == 'both' or xray_mode == 'schematic':
            annotated_frame = self.visualizer.draw_detections(
                frame,
                detections,
                show_confidence=xray_settings.get('show_confidence', True),
                show_labels=xray_settings.get('show_labels', True),
                show_boxes=xray_settings.get('show_boxes', True),
                min_confidence=xray_settings.get('min_confidence', 0.0),
                schematic_mode=schematic_mode or (xray_mode == 'schematic')
            )
        elif xray_mode == 'heatmap':
            annotated_frame = self.visualizer.draw_heatmap(
                frame,
                detections,
                alpha=xray_settings.get('overlay_alpha', 0.4),
                schematic_mode=schematic_mode
            )
        else:
            annotated_frame = frame.copy()
        
        # Add detection count
        annotated_frame = self.visualizer.draw_detection_count(
            annotated_frame,
            len(detections),
            position='top-right'
        )
        
        # Encode to JPEG
        import base64
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        data = {
            'type': 'xray_frame',
            'workflow_id': self.workflow_id,
            'node_id': target_node['id'],
            'timestamp': datetime.now().isoformat(),
            'frame_data': frame_base64,
            'fps': 10,
            'detections_count': len(detections),
            'processing_time_ms': 25,
            'xray_mode': xray_mode,
            'resolution': {
                'width': frame.shape[1],
                'height': frame.shape[0]
            }
        }
        
        await self._broadcast_to_websocket(data)
    
    async def _broadcast_to_websocket(self, data: dict):
        """Broadcast data to WebSocket clients"""
        try:
            from api.websocket import manager
            await manager.broadcast(data)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")
            
    def _find_connected_nodes(
        self,
        source_id: str,
        target_types: any
    ) -> List[dict]:
        """Find nodes connected to a source node"""
        if isinstance(target_types, str):
            target_types = [target_types]
            
        connected = []
        
        # Find edges from source
        for edge in self.edges:
            if edge['source'] == source_id:
                target_id = edge['target']
                
                # Find target node
                target_node = next(
                    (n for n in self.nodes if n['id'] == target_id),
                    None
                )
                
                if target_node and target_node['type'] in target_types:
                    connected.append(target_node)
                    
        return connected
    
    def _find_output_nodes_recursive(
        self,
        source_id: str,
        target_types: List[str],
        max_depth: int = 3
    ) -> List[dict]:
        """
        Recursively find output nodes connected to source
        Searches through intermediate nodes to find debug/preview nodes
        """
        found_nodes = []
        visited = set()
        
        def search(node_id: str, depth: int):
            if depth > max_depth or node_id in visited:
                return
            
            visited.add(node_id)
            
            # Find all edges from this node
            for edge in self.edges:
                if edge['source'] == node_id:
                    target_id = edge['target']
                    
                    # Find target node
                    target_node = next(
                        (n for n in self.nodes if n['id'] == target_id),
                        None
                    )
                    
                    if not target_node:
                        continue
                    
                    # If it's a target type, add it
                    if target_node['type'] in target_types:
                        if target_node not in found_nodes:
                            found_nodes.append(target_node)
                    
                    # Continue searching through this node
                    search(target_id, depth + 1)
        
        search(source_id, 0)
        return found_nodes
    
    async def _get_frame_from_stream_manager(self, camera_id: str) -> Optional[np.ndarray]:
        """
        Get latest frame from stream manager
        Integrates with backend stream manager to retrieve frames
        """
        global _stream_manager
        
        if not _stream_manager:
            logger.warning("Stream manager not available")
            return None
        
        try:
            # Check if stream exists and is running
            stream_status = _stream_manager.get_stream_status(camera_id)
            if not stream_status or not stream_status.get('running'):
                logger.debug(f"Stream {camera_id} not running")
                return None
            
            # Get stream instance
            stream = _stream_manager.streams.get(camera_id)
            if not stream:
                return None
            
            # Get latest frame from stream buffer
            if hasattr(stream, 'get_latest_frame'):
                # Check if it's async or sync
                result = stream.get_latest_frame()
                if asyncio.iscoroutine(result):
                    frame = await result
                else:
                    frame = result
                return frame
            
            # Fallback: try to get from frame buffer
            if hasattr(stream, 'frame_buffer') and stream.frame_buffer:
                frame = stream.frame_buffer.get_latest()
                return frame
                
        except Exception as e:
            logger.error(f"Error getting frame from stream manager: {e}")
            
        return None
    
    def _should_process_node(self, node_id: str, target_fps: float) -> bool:
        """Check if node should process based on FPS throttling"""
        current_time = time.time()
        last_time = self.last_process_time.get(node_id, 0)
        
        interval = 1.0 / target_fps if target_fps > 0 else 0
        
        if current_time - last_time >= interval:
            self.last_process_time[node_id] = current_time
            return True
            
        return False
    
    async def _update_node_metrics(self, node_id: str, metrics: dict):
        """Update metrics for a node"""
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = {
                'frames_received': 0,
                'frames_processed': 0,
                'detections_count': 0,
                'errors': 0,
                'avg_latency_ms': 0,
                'fps': 0
            }
        
        # Update metrics
        for key, value in metrics.items():
            if key in self.node_metrics[node_id]:
                self.node_metrics[node_id][key] += value
            else:
                self.node_metrics[node_id][key] = value
        
        # Broadcast metrics periodically
        current_time = time.time()
        last_broadcast = self.last_metrics_broadcast.get(node_id, 0)
        
        if current_time - last_broadcast >= self.metrics_broadcast_interval:
            self.last_metrics_broadcast[node_id] = current_time
            
            # Emit metrics event
            await self.event_bus.emit_metrics(
                self.workflow_id,
                node_id,
                self.node_metrics[node_id]
            )
    
    async def _process_audio_extractor_node(self, audio_node: dict):
        """Process audio extractor node"""
        node_id = audio_node['id']
        
        # Check if extractor already initialized
        if node_id in self.audio_extractors:
            return
        
        # Find connected input node (camera/videoInput/youtube)
        connected_inputs = self._find_connected_nodes_reverse(node_id, ['camera', 'videoInput', 'youtube'])
        if not connected_inputs:
            logger.warning(f"Audio extractor {node_id} has no connected video input")
            return
        
        input_node = connected_inputs[0]
        
        # Get RTSP URL or video source
        rtsp_url = None
        if input_node['type'] == 'camera':
            camera_id = input_node['data'].get('cameraId')
            if camera_id and _stream_manager:
                stream = _stream_manager.streams.get(camera_id)
                if stream:
                    rtsp_url = stream.rtsp_url
        elif input_node['type'] == 'youtube':
            rtsp_url = input_node['data'].get('youtubeUrl')
        elif input_node['type'] == 'videoInput':
            rtsp_url = input_node['data'].get('videoPath')
        
        if not rtsp_url:
            logger.warning(f"Could not determine stream URL for audio extractor {node_id}")
            return
        
        # Create and start audio extractor
        try:
            from stream.audio_extractor import AudioExtractor
            
            config = audio_node['data']
            extractor = AudioExtractor(
                rtsp_url=rtsp_url,
                sample_rate=config.get('sampleRate', 16000),
                channels=config.get('channels', 1),
                buffer_duration=config.get('bufferDuration', 5.0)
            )
            
            await extractor.start()
            self.audio_extractors[node_id] = extractor
            logger.info(f"Started audio extractor {node_id} for {rtsp_url}")
            
        except Exception as e:
            logger.error(f"Failed to start audio extractor {node_id}: {e}")
    
    async def _process_audio_ai_node(self, audio_ai_node: dict):
        """Process audio AI node"""
        node_id = audio_ai_node['id']
        model = self.audio_models.get(node_id)
        
        if not model:
            logger.debug(f"Audio model not initialized for node {node_id}")
            return
        
        # Find connected audio extractor
        connected_extractors = self._find_connected_nodes_reverse(node_id, ['audioExtractor'])
        if not connected_extractors:
            logger.debug(f"Audio AI {node_id} has no connected audio extractor")
            return
        
        extractor_node = connected_extractors[0]
        extractor = self.audio_extractors.get(extractor_node['id'])
        
        if not extractor:
            logger.debug(f"Audio extractor not ready for {extractor_node['id']}")
            return
        
        # Apply FPS throttling
        buffer_duration = audio_ai_node['data'].get('bufferDuration', 5.0)
        fps = 1.0 / buffer_duration  # Process based on buffer duration
        if not self._should_process_node(node_id, fps):
            return
        
        # Get audio chunk
        audio_data_result = extractor.get_audio_chunk(buffer_duration)
        if not audio_data_result:
            logger.debug(f"No audio data available for {node_id}")
            return
        
        audio_data, sample_rate, timestamp = audio_data_result
        
        try:
            # Process audio
            result = await model.process_audio(audio_data, sample_rate)
            
            if result:
                # Send results to output nodes
                await self._send_audio_results_to_outputs(node_id, result, audio_ai_node['data'])
                
        except Exception as e:
            logger.error(f"Error processing audio in node {node_id}: {e}")
    
    async def _send_audio_results_to_outputs(self, audio_ai_node_id: str, result, node_config: dict):
        """Send audio results to output nodes via WebSocket"""
        # Find connected output nodes
        output_nodes = self._find_output_nodes_recursive(
            audio_ai_node_id,
            ['dataPreview', 'debug'],
            max_depth=3
        )
        
        model_type = node_config.get('modelType', 'transcription')
        
        for output_node in output_nodes:
            output_node_id = output_node['id']
            node_type = output_node['type']
            
            # Prepare data based on model type and output node
            if model_type == 'transcription':
                # Handle transcription results
                if hasattr(result, 'to_dict'):
                    result_dict = result.to_dict()
                else:
                    result_dict = result
                
                if node_type == 'dataPreview':
                    data = {
                        'type': 'audio_transcript',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': result_dict.get('timestamp'),
                        'text': result_dict.get('text', ''),
                        'language': result_dict.get('language', 'unknown'),
                        'confidence': result_dict.get('confidence', 0),
                        'keywords_detected': result_dict.get('keywords_detected', [])
                    }
                elif node_type == 'debug':
                    keywords_str = ', '.join(result_dict.get('keywords_detected', [])) if result_dict.get('keywords_detected') else 'none'
                    data = {
                        'type': 'debug_message',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': result_dict.get('timestamp'),
                        'message': f"🎙️ Transcription ({result_dict.get('language')}): \"{result_dict.get('text', '')}\" | Keywords: {keywords_str}",
                        'audio_result': result_dict
                    }
            elif model_type == 'sound_classification':
                # Handle sound classification results
                if isinstance(result, list):
                    classifications = [c.to_dict() if hasattr(c, 'to_dict') else c for c in result]
                else:
                    classifications = []
                
                if node_type == 'dataPreview':
                    data = {
                        'type': 'sound_detection',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': datetime.now().isoformat(),
                        'sounds': classifications,
                        'count': len(classifications)
                    }
                elif node_type == 'debug':
                    sound_names = [c.get('sound_class') for c in classifications]
                    data = {
                        'type': 'debug_message',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': datetime.now().isoformat(),
                        'message': f"🔊 Detected sounds: {', '.join(sound_names)}",
                        'sounds': classifications
                    }
            else:
                continue
            
            # Broadcast via WebSocket
            await self._broadcast_to_websocket(data)
    
    def _find_connected_nodes_reverse(self, target_id: str, source_types: any) -> List[dict]:
        """Find nodes that connect TO the target node"""
        if isinstance(source_types, str):
            source_types = [source_types]
        
        connected = []
        
        # Find edges TO target
        for edge in self.edges:
            if edge['target'] == target_id:
                source_id = edge['source']
                
                # Find source node
                source_node = next(
                    (n for n in self.nodes if n['id'] == source_id),
                    None
                )
                
                if source_node and source_node['type'] in source_types:
                    connected.append(source_node)
        
        return connected
    
    async def _process_audio_vu_node(self, audio_vu_node: dict):
        """Process Audio VU/Frequency Meter node"""
        node_id = audio_vu_node['id']
        node_config = audio_vu_node.get('data', {})
        
        # Check FPS throttling
        fps_limit = 10  # Update 10 times per second
        if not self._should_process_node(node_id, fps_limit):
            return
        
        # Find connected audio source (audio extractor or camera with audio)
        audio_sources = self._find_connected_nodes_reverse(node_id, ['audioExtractor', 'camera'])
        
        if not audio_sources:
            return
        
        # Get audio data from audio extractor
        audio_source = audio_sources[0]
        audio_extractor_id = audio_source['id']
        
        # Check if we have audio data from this extractor
        extractor = self.audio_extractors.get(audio_extractor_id)
        if not extractor or not hasattr(extractor, 'get_audio_chunk'):
            return
        
        try:
            audio_chunk = extractor.get_audio_chunk()
            if audio_chunk is None or len(audio_chunk) == 0:
                return
            
            # Calculate audio levels
            levels = self.audio_analyzer.calculate_levels(audio_chunk)
            
            # Check threshold if enabled
            threshold_triggered = False
            if node_config.get('enableThreshold', False):
                threshold = node_config.get('thresholdLevel', 75)
                hysteresis = node_config.get('hysteresis', 5)
                current_state = self.audio_vu_states.get(node_id, False)
                
                threshold_triggered = self.audio_analyzer.check_threshold(
                    levels['level_db'],
                    threshold,
                    hysteresis,
                    current_state
                )
                
                self.audio_vu_states[node_id] = threshold_triggered
            
            # Get frequency bands configuration
            num_bands = node_config.get('frequencyBands', 8)
            spectrum = levels['spectrum'][:num_bands]
            
            # Broadcast data via WebSocket
            data = {
                'type': 'audioVU_update',
                'workflow_id': self.workflow_id,
                'node_id': node_id,
                'data': {
                    'level_db': levels['level_db'],
                    'spectrum': spectrum,
                    'triggered': threshold_triggered,
                    'timestamp': levels['timestamp']
                }
            }
            
            await self._broadcast_to_websocket(data)
            
            # Also send to connected output nodes
            output_nodes = self._find_output_nodes_recursive(
                node_id,
                ['dataPreview', 'debug'],
                max_depth=3
            )
            
            for output_node in output_nodes:
                output_node_id = output_node['id']
                node_type = output_node['type']
                
                if node_type == 'dataPreview':
                    preview_data = {
                        'type': 'audio_levels',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': levels['timestamp'],
                        'level_db': levels['level_db'],
                        'peak': levels['peak'],
                        'rms': levels['rms'],
                        'spectrum': spectrum,
                        'triggered': threshold_triggered
                    }
                elif node_type == 'debug':
                    trigger_status = "TRIGGERED" if threshold_triggered else "inactive"
                    preview_data = {
                        'type': 'debug_message',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': levels['timestamp'],
                        'message': f"📻 Audio Level: {levels['level_db']:.1f} dB | Threshold: {trigger_status}",
                        'audio_levels': levels
                    }
                else:
                    continue
                
                await self._broadcast_to_websocket(preview_data)
                
        except Exception as e:
            logger.error(f"Error processing audio VU node {node_id}: {e}")
    
    async def _process_day_night_node(self, day_night_node: dict):
        """Process Day/Night/IR Detector node"""
        node_id = day_night_node['id']
        node_config = day_night_node.get('data', {})
        
        # Check interval-based throttling
        check_interval = node_config.get('checkInterval', 5)  # seconds
        if not self._should_process_node(node_id, 1.0 / check_interval):
            return
        
        # Find connected camera/video source
        video_sources = self._find_connected_nodes_reverse(node_id, ['camera', 'videoInput', 'youtube'])
        
        if not video_sources:
            return
        
        # Get frame from source
        video_source = video_sources[0]
        frame = await self._get_frame_from_input(video_source)
        
        if frame is None:
            return
        
        try:
            # Analyze frame for lighting conditions
            analysis = self.lighting_analyzer.analyze_frame(
                frame,
                brightness_threshold=node_config.get('brightnessThreshold', 0.3),
                ir_threshold=node_config.get('irThreshold', 0.7),
                sensitivity=node_config.get('sensitivity', 0.5)
            )
            
            # Check if state changed
            previous_state = self.lighting_states.get(node_id)
            current_state = analysis['state']
            
            state_changed = self.lighting_analyzer.should_trigger_action(
                current_state,
                previous_state,
                node_config.get('enableActions', True)
            )
            
            self.lighting_states[node_id] = current_state
            
            # Broadcast data via WebSocket
            data = {
                'type': 'dayNight_update',
                'workflow_id': self.workflow_id,
                'node_id': node_id,
                'data': analysis
            }
            
            await self._broadcast_to_websocket(data)
            
            # Also send to connected output nodes
            output_nodes = self._find_output_nodes_recursive(
                node_id,
                ['dataPreview', 'debug'],
                max_depth=3
            )
            
            for output_node in output_nodes:
                output_node_id = output_node['id']
                node_type = output_node['type']
                
                if node_type == 'dataPreview':
                    preview_data = {
                        'type': 'lighting_conditions',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': datetime.now().isoformat(),
                        'state': current_state,
                        'brightness': analysis['brightness'],
                        'is_ir': analysis['is_ir'],
                        'confidence': analysis['confidence']
                    }
                elif node_type == 'debug':
                    state_icon = {'day': '☀️', 'dusk': '🌅', 'night': '🌙'}.get(current_state, '❓')
                    ir_status = " [IR MODE]" if analysis['is_ir'] else ""
                    preview_data = {
                        'type': 'debug_message',
                        'workflow_id': self.workflow_id,
                        'node_id': output_node_id,
                        'timestamp': datetime.now().isoformat(),
                        'message': f"{state_icon} Lighting: {current_state.upper()}{ir_status} | Brightness: {analysis['brightness']:.1%} | Confidence: {analysis['confidence']:.1%}",
                        'lighting_analysis': analysis
                    }
                else:
                    continue
                
                await self._broadcast_to_websocket(preview_data)
                
        except Exception as e:
            logger.error(f"Error processing day/night node {node_id}: {e}")
    
    async def _process_parking_violation_node(self, parking_node: dict):
        """Process Parking Violation Detection node"""
        node_id = parking_node['id']
        node_config = parking_node.get('data', {})
        
        # Check FPS throttling (check every second)
        if not self._should_process_node(node_id, 1.0):
            return
        
        logger.debug(f"Processing parking violation node {node_id}")
        
        # For now, emit a status message to debug nodes
        # Full implementation would:
        # 1. Get detections from connected ALPR/Model nodes
        # 2. Check if vehicles are in parking zones
        # 3. Track dwell time
        # 4. Emit violations
        
        # Send status to connected debug nodes
        output_nodes = self._find_output_nodes_recursive(
            node_id,
            ['dataPreview', 'debug'],
            max_depth=3
        )
        
        for output_node in output_nodes:
            output_node_id = output_node['id']
            
            status_data = {
                'type': 'debug_message',
                'workflow_id': self.workflow_id,
                'node_id': output_node_id,
                'timestamp': datetime.now().isoformat(),
                'message': f"🚗 Parking Violation Monitor Active | Zones: {len(node_config.get('parkingZones', []))} | Dwell: {node_config.get('dwellTime', 30)}s",
                'parking_config': {
                    'zones': len(node_config.get('parkingZones', [])),
                    'dwell_time': node_config.get('dwellTime', 30),
                    'restriction_type': node_config.get('restrictionType', 'no_parking')
                }
            }
            
            await self._broadcast_to_websocket(status_data)
        
        logger.debug(f"Parking violation node {node_id} processed, sent to {len(output_nodes)} outputs")

