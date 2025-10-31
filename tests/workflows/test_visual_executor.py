"""
Tests for Visual Workflow Executor
"""
import pytest
from workflows.visual_executor import VisualWorkflowExecutor


@pytest.fixture
def executor():
    """Create executor instance"""
    return VisualWorkflowExecutor()


@pytest.fixture
def simple_workflow():
    """Simple workflow: camera -> model -> action"""
    nodes = [
        {
            'id': 'camera-1',
            'type': 'camera',
            'data': {'cameraId': 'cam1', 'cameraName': 'Front Door'}
        },
        {
            'id': 'model-1',
            'type': 'model',
            'data': {
                'modelId': 'yolo11n',
                'confidence': 0.7,
                'classes': [0, 1, 2]  # person, bicycle, car
            }
        },
        {
            'id': 'action-1',
            'type': 'action',
            'data': {
                'actionType': 'email',
                'config': {
                    'to': 'admin@example.com',
                    'includeSnapshot': True
                }
            }
        }
    ]
    
    edges = [
        {'id': 'e1', 'source': 'camera-1', 'target': 'model-1'},
        {'id': 'e2', 'source': 'model-1', 'target': 'action-1'}
    ]
    
    return nodes, edges


@pytest.fixture
def zone_workflow():
    """Workflow with zone filtering"""
    nodes = [
        {
            'id': 'camera-1',
            'type': 'camera',
            'data': {'cameraId': 'cam1'}
        },
        {
            'id': 'model-1',
            'type': 'model',
            'data': {
                'modelId': 'yolo11n',
                'confidence': 0.7,
                'classes': [0]
            }
        },
        {
            'id': 'zone-1',
            'type': 'zone',
            'data': {
                'zoneType': 'polygon',
                'label': 'Entry Zone',
                'polygon': [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]
            }
        },
        {
            'id': 'action-1',
            'type': 'action',
            'data': {
                'actionType': 'alert',
                'config': {'severity': 'critical'}
            }
        }
    ]
    
    edges = [
        {'id': 'e1', 'source': 'camera-1', 'target': 'model-1'},
        {'id': 'e2', 'source': 'model-1', 'target': 'zone-1'},
        {'id': 'e3', 'source': 'zone-1', 'target': 'action-1'}
    ]
    
    return nodes, edges


def test_simple_workflow_parsing(executor, simple_workflow):
    """Test parsing a simple workflow"""
    nodes, edges = simple_workflow
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    assert 'workflows' in result
    assert len(result['workflows']) == 1
    
    workflow = result['workflows'][0]
    assert workflow['camera_id'] == 'cam1'
    assert workflow['model'] == 'yolo11n'
    assert workflow['detection']['confidence'] == 0.7
    assert workflow['detection']['classes'] == [0, 1, 2]
    assert len(workflow['actions']) == 1
    assert workflow['actions'][0]['type'] == 'email'


def test_zone_workflow_parsing(executor, zone_workflow):
    """Test parsing workflow with zones"""
    nodes, edges = zone_workflow
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    workflow = result['workflows'][0]
    assert 'zones' in workflow
    assert len(workflow['zones']) == 1
    
    zone = workflow['zones'][0]
    assert zone['name'] == 'Entry Zone'
    assert len(zone['polygon']) == 4


def test_multi_camera_workflow(executor):
    """Test workflow with multiple cameras"""
    nodes = [
        {'id': 'cam1', 'type': 'camera', 'data': {'cameraId': 'camera1'}},
        {'id': 'cam2', 'type': 'camera', 'data': {'cameraId': 'camera2'}},
        {'id': 'model1', 'type': 'model', 'data': {'modelId': 'yolo11n', 'classes': [0]}},
        {'id': 'model2', 'type': 'model', 'data': {'modelId': 'yolo11n', 'classes': [2]}},
        {'id': 'action1', 'type': 'action', 'data': {'actionType': 'email', 'config': {'to': 'test@test.com'}}}
    ]
    
    edges = [
        {'id': 'e1', 'source': 'cam1', 'target': 'model1'},
        {'id': 'e2', 'source': 'cam2', 'target': 'model2'},
        {'id': 'e3', 'source': 'model1', 'target': 'action1'},
        {'id': 'e4', 'source': 'model2', 'target': 'action1'}
    ]
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    assert len(result['workflows']) == 2


def test_invalid_classes(executor):
    """Test that string classes are rejected"""
    nodes = [
        {'id': 'cam1', 'type': 'camera', 'data': {'cameraId': 'cam1'}},
        {'id': 'model1', 'type': 'model', 'data': {
            'modelId': 'yolo11n',
            'classes': 'person, car'  # Invalid: should be array
        }}
    ]
    edges = [{'id': 'e1', 'source': 'cam1', 'target': 'model1'}]
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    # Should handle gracefully, returning empty classes
    workflow = result['workflows'][0]
    assert workflow['detection']['classes'] == []


def test_invalid_polygon(executor):
    """Test that invalid polygons are rejected"""
    nodes = [
        {'id': 'cam1', 'type': 'camera', 'data': {'cameraId': 'cam1'}},
        {'id': 'model1', 'type': 'model', 'data': {'modelId': 'yolo11n', 'classes': [0]}},
        {'id': 'zone1', 'type': 'zone', 'data': {
            'zoneType': 'polygon',
            'polygon': [[0.1, 0.1]]  # Invalid: less than 3 points
        }}
    ]
    edges = [
        {'id': 'e1', 'source': 'cam1', 'target': 'model1'},
        {'id': 'e2', 'source': 'model1', 'target': 'zone1'}
    ]
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    # Should handle gracefully
    workflow = result['workflows'][0]
    assert 'zones' not in workflow or len(workflow.get('zones', [])) == 0


def test_action_config_with_schema(executor):
    """Test action configuration using schema structure"""
    nodes = [
        {'id': 'cam1', 'type': 'camera', 'data': {'cameraId': 'cam1'}},
        {'id': 'model1', 'type': 'model', 'data': {'modelId': 'yolo11n', 'classes': [0]}},
        {'id': 'action1', 'type': 'action', 'data': {
            'actionType': 'webhook',
            'config': {
                'url': 'https://api.example.com/webhook',
                'method': 'POST',
                'timeout': 15,
                'retries': 5
            }
        }}
    ]
    edges = [
        {'id': 'e1', 'source': 'cam1', 'target': 'model1'},
        {'id': 'e2', 'source': 'model1', 'target': 'action1'}
    ]
    
    result = executor.parse_visual_workflow(nodes, edges)
    
    workflow = result['workflows'][0]
    action = workflow['actions'][0]
    
    assert action['type'] == 'webhook'
    assert action['timeout'] == 15
    assert action['retries'] == 5


