"""
Hailo Device Detection and Configuration
Automatically configures Overwatch to use Hailo acceleration when available
"""
import logging
import sys
from pathlib import Path

# Add system packages to path for Hailo
sys.path.append('/usr/lib/python3/dist-packages')

logger = logging.getLogger('overwatch.hailo')


def detect_hailo() -> bool:
    """Check if Hailo accelerator is available"""
    try:
        from hailo_platform.pyhailort.pyhailort import InternalPcieDevice
        devices = InternalPcieDevice.scan_devices()
        if devices:
            logger.info(f"Hailo accelerator detected: {len(devices)} device(s)")
            return True
    except (ImportError, Exception) as e:
        logger.debug(f"Hailo not available: {e}")
    return False


def get_hailo_models() -> list:
    """Get list of available Hailo-compiled models"""
    models = []
    hailo_models_dir = Path("/usr/local/hailo/resources/models/hailo8l")
    
    if hailo_models_dir.exists():
        for hef_file in hailo_models_dir.glob("*.hef"):
            model_name = hef_file.stem
            models.append(f"hailo-{model_name}")
    
    return models


def get_recommended_device() -> str:
    """Get recommended compute device based on available hardware"""
    if detect_hailo():
        return "hailo"
    
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    
    return "cpu"


def convert_model_to_hailo(model_id: str) -> str:
    """
    Convert a standard model ID to Hailo version if available
    
    Args:
        model_id: Original model ID (e.g., 'ultralytics-yolov8s')
    
    Returns:
        Hailo model ID if available, otherwise original model ID
    """
    if not detect_hailo():
        return model_id
    
    # Mapping of standard models to Hailo equivalents
    model_mapping = {
        'ultralytics-yolov8s': 'hailo-yolov8s',
        'yolov8s': 'hailo-yolov8s',
        'ultralytics-yolov6n': 'hailo-yolov6n',
        'yolov6n': 'hailo-yolov6n',
    }
    
    # Check if Hailo version exists
    hailo_model = model_mapping.get(model_id)
    if hailo_model:
        hef_path = Path(f"/usr/local/hailo/resources/models/hailo8l/{hailo_model.replace('hailo-', '')}.hef")
        if hef_path.exists():
            logger.info(f"Converting {model_id} to {hailo_model} for hardware acceleration")
            return hailo_model
    
    return model_id


def get_device_capabilities() -> dict:
    """Get information about available compute devices"""
    capabilities = {
        'hailo': False,
        'cuda': False,
        'hailo_models': [],
        'recommended_device': 'cpu',
        'hailo_device_info': None
    }
    
    # Check Hailo
    if detect_hailo():
        capabilities['hailo'] = True
        capabilities['hailo_models'] = get_hailo_models()
        capabilities['recommended_device'] = 'hailo'
        
        try:
            # Get device info using hailortcli
            import subprocess
            result = subprocess.run(['hailortcli', 'fw-control', 'identify'], 
                                  capture_output=True, text=True, timeout=5)
            capabilities['hailo_device_info'] = result.stdout
        except Exception as e:
            logger.debug(f"Could not get Hailo device info: {e}")
    
    # Check CUDA
    try:
        import torch
        if torch.cuda.is_available():
            capabilities['cuda'] = True
            if not capabilities['hailo']:
                capabilities['recommended_device'] = 'cuda'
    except ImportError:
        pass
    
    return capabilities

