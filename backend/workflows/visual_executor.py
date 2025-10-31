"""
Visual Workflow Executor
Converts and executes workflows created in the visual builder
"""
import logging
from typing import Dict, List
import yaml
from pathlib import Path

from core.config import settings


logger = logging.getLogger('overwatch.workflows.visual_executor')


class VisualWorkflowExecutor:
    """Converts visual workflows to executable YAML configs"""
    
    def __init__(self):
        pass
        
    def parse_visual_workflow(self, nodes: List[dict], edges: List[dict]) -> Dict:
        """
        Parse visual workflow into executable configuration
        
        Args:
            nodes: List of workflow nodes from React Flow
            edges: List of connections between nodes
            
        Returns:
            Dict containing workflow configuration
        """
        # Find camera nodes (sources)
        camera_nodes = [n for n in nodes if n['type'] == 'camera']
        
        workflows = []
        
        for camera_node in camera_nodes:
            camera_id = camera_node['data'].get('cameraId')
            
            # Build workflow for this camera
            workflow = self._build_workflow_for_camera(
                camera_node,
                nodes,
                edges
            )
            
            if workflow:
                workflows.append({
                    'camera_id': camera_id,
                    'workflow': workflow
                })
                
        return {'workflows': workflows}
        
    def _build_workflow_for_camera(
        self,
        camera_node: dict,
        all_nodes: List[dict],
        edges: List[dict]
    ) -> Dict:
        """Build workflow configuration for a specific camera"""
        workflow = {
            'camera_id': camera_node['data'].get('cameraId'),
            'enabled': True
        }
        
        # Find connected model node
        model_node = self._find_connected_node(
            camera_node['id'],
            'model',
            all_nodes,
            edges
        )
        
        if model_node:
            # Check for connected Config node
            config_node = self._find_connected_node(
                model_node['id'],
                'config',
                all_nodes,
                edges,
                search_incoming=True  # Config connects TO model
            )
            
            # Merge config from Config node if present
            model_config = model_node['data'].copy()
            if config_node:
                external_config = config_node['data'].get('config', {})
                model_config.update(external_config)
                logger.info(f"Merged config from Config node {config_node['id']} into model {model_node['id']}")
            
            workflow['model'] = model_config.get('modelId')
            workflow['detection'] = {
                'confidence': model_config.get('confidence', 0.7),
                'classes': self._parse_classes(model_config.get('classes', []))
            }
            
            # Add optional model settings
            if 'fps' in model_config:
                if 'processing' not in workflow:
                    workflow['processing'] = {}
                workflow['processing']['fps'] = model_config['fps']
            
            if 'batchSize' in model_config:
                if 'processing' not in workflow:
                    workflow['processing'] = {}
                workflow['processing']['batch_size'] = model_config['batchSize']
            
            # Find zones/filters
            zone_nodes = self._find_all_connected_nodes(
                model_node['id'],
                'zone',
                all_nodes,
                edges
            )
            
            if zone_nodes:
                workflow['zones'] = []
                for zone in zone_nodes:
                    zone_type = zone['data'].get('zoneType')
                    if zone_type == 'polygon':
                        workflow['zones'].append({
                            'name': zone['data'].get('label', 'zone'),
                            'polygon': self._parse_polygon(zone['data'].get('polygon', ''))
                        })
                        
            # Find actions
            action_nodes = self._find_all_connected_nodes(
                model_node['id'],
                'action',
                all_nodes,
                edges,
                search_depth=2  # Can be connected via zones
            )
            
            if action_nodes:
                workflow['actions'] = []
                for action in action_nodes:
                    action_config = self._build_action_config(action)
                    if action_config:
                        workflow['actions'].append(action_config)
        
        # Find audio processing nodes connected to the camera
        audio_extractor_nodes = self._find_connected_node(
            camera_node['id'],
            'audioExtractor',
            all_nodes,
            edges
        )
        
        if audio_extractor_nodes:
            # Find audio AI nodes connected to the audio extractor
            audio_ai_nodes = self._find_connected_node(
                audio_extractor_nodes['id'],
                'audioAI',
                all_nodes,
                edges
            )
            
            if audio_ai_nodes:
                audio_config = self._build_audio_config(audio_extractor_nodes, audio_ai_nodes)
                if audio_config:
                    workflow['audio_processing'] = audio_config
                        
        return workflow
        
    def _find_connected_node(
        self,
        source_id: str,
        target_type: str,
        nodes: List[dict],
        edges: List[dict],
        search_incoming: bool = False
    ) -> dict:
        """
        Find first connected node of specific type
        
        Args:
            search_incoming: If True, search for nodes connecting TO source_id (incoming edges)
                           If False, search for nodes source_id connects to (outgoing edges)
        """
        if search_incoming:
            # Find edges coming INTO this node (e.g., Config → Model)
            connected_edges = [e for e in edges if e['target'] == source_id]
            
            for edge in connected_edges:
                source_node = next((n for n in nodes if n['id'] == edge['source']), None)
                if source_node and source_node['type'] == target_type:
                    return source_node
        else:
            # Find edges going OUT from this node (default behavior)
            connected_edges = [e for e in edges if e['source'] == source_id]
            
            for edge in connected_edges:
                target_node = next((n for n in nodes if n['id'] == edge['target']), None)
                if target_node and target_node['type'] == target_type:
                    return target_node
                
        return None
        
    def _find_all_connected_nodes(
        self,
        source_id: str,
        target_type: str,
        nodes: List[dict],
        edges: List[dict],
        search_depth: int = 1
    ) -> List[dict]:
        """Find all connected nodes of specific type"""
        found_nodes = []
        visited = set()
        
        def search(node_id, depth):
            if depth > search_depth or node_id in visited:
                return
                
            visited.add(node_id)
            connected_edges = [e for e in edges if e['source'] == node_id]
            
            for edge in connected_edges:
                target_node = next((n for n in nodes if n['id'] == edge['target']), None)
                if target_node:
                    if target_node['type'] == target_type:
                        found_nodes.append(target_node)
                    else:
                        search(target_node['id'], depth + 1)
                        
        search(source_id, 0)
        return found_nodes
        
    def _parse_classes(self, classes: any) -> List[int]:
        """
        Parse detection classes
        Now expects arrays only, no string parsing
        """
        from .validator import validate_classes
        
        if not classes:
            return []
        
        # Validate classes
        is_valid, error_msg = validate_classes(classes)
        if not is_valid:
            logger.error(f"Invalid classes configuration: {error_msg}")
            return []
            
        return classes
        
    def _parse_polygon(self, polygon: any) -> List[List[float]]:
        """
        Parse polygon coordinates
        Now expects arrays only, validates structure
        """
        from .validator import validate_polygon
        
        if not polygon:
            return []
        
        # Validate polygon
        is_valid, error_msg = validate_polygon(polygon)
        if not is_valid:
            logger.error(f"Invalid polygon configuration: {error_msg}")
            return []
            
        return polygon
            
    def _build_action_config(self, action_node: dict) -> dict:
        """
        Build action configuration from node using schema
        Now uses node.data.config with validated structure
        """
        from .schema import get_action_schema, redact_sensitive_data
        
        action_type = action_node['data'].get('actionType')
        
        # Get config from node data (schema-validated structure)
        node_config = action_node['data'].get('config', {})
        
        config = {'type': action_type}
        
        if action_type == 'email':
            config.update({
                'to': node_config.get('to', ''),
                'cc': node_config.get('cc', []),
                'subject': node_config.get('subject', 'Detection Alert'),
                'include_snapshot': node_config.get('includeSnapshot', True),
                'include_detections': node_config.get('includeDetections', True)
            })
            
        elif action_type == 'webhook':
            config.update({
                'url': node_config.get('url', ''),
                'method': node_config.get('method', 'POST'),
                'headers': node_config.get('headers', {}),
                'timeout': node_config.get('timeout', 10),
                'retries': node_config.get('retries', 3),
                'secret_key': node_config.get('secretKey')  # Reference to secrets store
            })
            
        elif action_type == 'record':
            config.update({
                'duration': node_config.get('duration', 30),
                'pre_buffer': node_config.get('preBuffer', 5),
                'post_buffer': node_config.get('postBuffer', 5),
                'format': node_config.get('format', 'mp4'),
                'quality': node_config.get('quality', 'medium')
            })
            
        elif action_type == 'alert':
            config.update({
                'severity': node_config.get('severity', 'warning'),
                'notify': node_config.get('notify', []),
                'message': node_config.get('message', 'Detection alert')
            })
            
        elif action_type == 'snapshot':
            config.update({
                'draw_boxes': node_config.get('drawBoxes', True),
                'draw_zones': node_config.get('drawZones', False),
                'format': node_config.get('format', 'jpg'),
                'quality': node_config.get('quality', 90)
            })
            
        # Log without sensitive data
        safe_config = redact_sensitive_data(config)
        logger.debug(f"Built action config: {safe_config}")
            
        return config
    
    def _build_audio_config(self, audio_extractor_node: dict, audio_ai_node: dict) -> dict:
        """
        Build audio processing configuration from audio nodes
        
        Args:
            audio_extractor_node: AudioExtractor node
            audio_ai_node: AudioAI node
            
        Returns:
            Dict containing audio configuration
        """
        # Extract audio extractor settings
        extractor_data = audio_extractor_node['data']
        
        # Extract audio AI settings
        ai_data = audio_ai_node['data']
        
        audio_config = {
            'extraction': {
                'sample_rate': extractor_data.get('sampleRate', 16000),
                'channels': extractor_data.get('channels', 1),
                'format': extractor_data.get('format', 'wav'),
                'buffer_duration': extractor_data.get('bufferDuration', 5.0)
            },
            'model': {
                'model_id': ai_data.get('modelId'),
                'model_name': ai_data.get('modelName'),
                'model_type': ai_data.get('modelType', 'transcription'),
                'language': ai_data.get('language', 'auto'),
                'confidence': ai_data.get('confidence', 0.7),
                'detect_keywords': ai_data.get('detectKeywords', []),
                'buffer_duration': ai_data.get('bufferDuration', 5.0)
            }
        }
        
        logger.debug(f"Built audio config: {audio_config}")
        
        return audio_config
        
    def save_to_yaml(self, workflow_config: Dict, output_path: str):
        """Save workflow configuration to YAML file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(workflow_config, f, default_flow_style=False, sort_keys=False)
            
        logger.info(f"Saved workflow to {output_path}")

