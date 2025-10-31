"""
Workflow Graph Validator
Validates workflow graphs for correctness, cycles, and port compatibility
"""
import logging
from typing import List, Dict, Tuple, Set
from collections import defaultdict, deque

from .schema import validate_port_connection, PORT_COMPATIBILITY


logger = logging.getLogger('overwatch.workflows.validator')


class WorkflowValidator:
    """Validates workflow graphs"""
    
    def __init__(self, nodes: List[dict], edges: List[dict]):
        self.nodes = nodes
        self.edges = edges
        self.node_map = {n['id']: n for n in nodes}
        self.errors = []
        self.warnings = []
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate workflow graph
        
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Run validation checks
        self._validate_graph_structure()
        self._validate_port_connections()
        self._validate_cycles()
        self._validate_camera_pipelines()
        self._validate_action_presence()
        self._validate_dangling_nodes()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
        
    def _validate_graph_structure(self):
        """Validate basic graph structure"""
        if not self.nodes:
            self.errors.append("Workflow has no nodes")
            return
            
        # Check for duplicate node IDs
        node_ids = [n['id'] for n in self.nodes]
        duplicates = {nid for nid in node_ids if node_ids.count(nid) > 1}
        if duplicates:
            self.errors.append(f"Duplicate node IDs found: {duplicates}")
            
        # Check for duplicate edge IDs
        edge_ids = [e['id'] for e in self.edges]
        duplicates = {eid for eid in edge_ids if edge_ids.count(eid) > 1}
        if duplicates:
            self.errors.append(f"Duplicate edge IDs found: {duplicates}")
            
        # Check that all edges reference valid nodes
        for edge in self.edges:
            source_id = edge.get('source')
            target_id = edge.get('target')
            
            if source_id not in self.node_map:
                self.errors.append(f"Edge {edge['id']} references non-existent source node: {source_id}")
                
            if target_id not in self.node_map:
                self.errors.append(f"Edge {edge['id']} references non-existent target node: {target_id}")
                
    def _validate_port_connections(self):
        """Validate that all port connections are compatible"""
        for edge in self.edges:
            source_id = edge.get('source')
            target_id = edge.get('target')
            
            if source_id not in self.node_map or target_id not in self.node_map:
                continue  # Already reported in structure validation
                
            source_node = self.node_map[source_id]
            target_node = self.node_map[target_id]
            
            source_type = source_node.get('type')
            target_type = target_node.get('type')
            
            # Default handles if not specified
            source_handle = edge.get('sourceHandle', self._get_default_output_handle(source_type))
            target_handle = edge.get('targetHandle', self._get_default_input_handle(target_type))
            
            # Validate connection
            is_valid, error_msg = validate_port_connection(
                source_type, source_handle,
                target_type, target_handle
            )
            
            if not is_valid:
                self.errors.append(f"Invalid connection {source_id} -> {target_id}: {error_msg}")
                
    def _get_default_output_handle(self, node_type: str) -> str:
        """Get default output handle for node type"""
        defaults = {
            "camera": "video-output",
            "videoInput": "video-output",
            "youtube": "video-output",
            "model": "detections-output",
            "zone": "filtered-output",
            "linkIn": "link-output",
            "linkCall": "call-output"
        }
        return defaults.get(node_type, "output")
        
    def _get_default_input_handle(self, node_type: str) -> str:
        """Get default input handle for node type"""
        defaults = {
            "model": "video-input",
            "zone": "detections-input",
            "action": "trigger-input",
            "dataPreview": "data-input",
            "debug": "data-input",
            "linkOut": "link-input",
            "linkCall": "call-input",
            "catch": "error-input"
        }
        return defaults.get(node_type, "input")
        
    def _validate_cycles(self):
        """Check for cycles in the graph (per camera pipeline)"""
        # Build adjacency list
        graph = defaultdict(list)
        for edge in self.edges:
            graph[edge['source']].append(edge['target'])
            
        # Find all camera/input nodes
        input_nodes = [n['id'] for n in self.nodes if n['type'] in ['camera', 'videoInput', 'youtube']]
        
        for input_id in input_nodes:
            if self._has_cycle_from(input_id, graph):
                self.errors.append(f"Cycle detected in pipeline starting from {input_id}")
                
    def _has_cycle_from(self, start_node: str, graph: Dict[str, List[str]]) -> bool:
        """Check if there's a cycle reachable from start_node using DFS"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True  # Cycle found
                
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
                    
            rec_stack.remove(node)
            return False
            
        return dfs(start_node)
        
    def _validate_camera_pipelines(self):
        """Validate that each camera has a valid pipeline"""
        camera_nodes = [n for n in self.nodes if n['type'] in ['camera', 'videoInput', 'youtube']]
        
        for camera_node in camera_nodes:
            camera_id = camera_node['id']
            
            # Check if camera has output connections
            has_outputs = any(e['source'] == camera_id for e in self.edges)
            if not has_outputs:
                self.warnings.append(f"Input node {camera_id} has no output connections")
                continue
                
            # Check if pipeline reaches a model node
            reachable_types = self._get_reachable_node_types(camera_id)
            
            if 'model' not in reachable_types:
                self.warnings.append(f"Pipeline from {camera_id} does not reach any model node")
                
            # Check if pipeline has any action or output
            has_action = any(t in reachable_types for t in ['action', 'dataPreview', 'debug', 'linkOut'])
            if not has_action:
                self.warnings.append(f"Pipeline from {camera_id} has no action or output node")
                
    def _get_reachable_node_types(self, start_node_id: str) -> Set[str]:
        """Get all node types reachable from start_node"""
        visited = set()
        queue = deque([start_node_id])
        types = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
                
            visited.add(current)
            
            if current in self.node_map:
                types.add(self.node_map[current]['type'])
                
            # Add connected nodes
            for edge in self.edges:
                if edge['source'] == current:
                    queue.append(edge['target'])
                    
        return types
        
    def _validate_action_presence(self):
        """Validate that workflow has at least one action or sink"""
        has_action = any(n['type'] in ['action', 'dataPreview', 'debug', 'linkOut'] for n in self.nodes)
        
        if not has_action:
            self.warnings.append("Workflow has no action or output nodes")
            
    def _validate_dangling_nodes(self):
        """Check for nodes with no connections"""
        connected_nodes = set()
        
        for edge in self.edges:
            connected_nodes.add(edge['source'])
            connected_nodes.add(edge['target'])
            
        for node in self.nodes:
            node_id = node['id']
            node_type = node['type']
            
            # Skip welcome/info nodes
            if node_type == 'default':
                continue
                
            if node_id not in connected_nodes:
                self.warnings.append(f"Node {node_id} ({node_type}) has no connections")
                
                
def validate_polygon(polygon: List[List[float]]) -> Tuple[bool, str]:
    """
    Validate polygon coordinates
    
    Args:
        polygon: Array of [x, y] coordinates
        
    Returns:
        (is_valid, error_message)
    """
    if not polygon:
        return False, "Polygon is empty"
        
    if not isinstance(polygon, list):
        return False, "Polygon must be an array"
        
    if len(polygon) < 3:
        return False, f"Polygon must have at least 3 points, got {len(polygon)}"
        
    for i, point in enumerate(polygon):
        if not isinstance(point, (list, tuple)):
            return False, f"Point {i} is not an array"
            
        if len(point) != 2:
            return False, f"Point {i} must have exactly 2 coordinates, got {len(point)}"
            
        x, y = point
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, f"Point {i} coordinates must be numeric"
            
        if x < 0 or y < 0 or x > 1 or y > 1:
            return False, f"Point {i} coordinates must be normalized (0-1), got ({x}, {y})"
            
    return True, ""


def validate_classes(classes: any) -> Tuple[bool, str]:
    """
    Validate detection classes
    
    Args:
        classes: Array of class IDs or string
        
    Returns:
        (is_valid, error_message)
    """
    if isinstance(classes, str):
        return False, "Classes must be an array of integers, not a string"
        
    if not isinstance(classes, list):
        return False, "Classes must be an array"
        
    for cls in classes:
        if not isinstance(cls, int):
            return False, f"Class ID must be an integer, got {type(cls).__name__}: {cls}"
            
        if cls < 0 or cls > 255:
            return False, f"Class ID must be 0-255, got {cls}"
            
    return True, ""


