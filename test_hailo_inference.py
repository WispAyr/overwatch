#!/usr/bin/env python3
"""
Test Hailo Inference
Verify Hailo-8L is actually running AI inference
"""
import sys
import asyncio
import time
import numpy as np
import cv2
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
sys.path.append('/usr/lib/python3/dist-packages')

async def test_hailo_inference():
    """Test Hailo inference with a sample image"""
    from models import get_model
    from core.hailo_detector import detect_hailo
    
    print("=" * 60)
    print("🧪 HAILO INFERENCE TEST")
    print("=" * 60)
    print()
    
    # Check Hailo
    if not detect_hailo():
        print("❌ Hailo not detected!")
        return False
    
    print("✅ Hailo-8L detected (13 TOPS)")
    print()
    
    # Create test image
    print("📸 Creating test image (640x640)...")
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # Draw some shapes to detect
    cv2.rectangle(test_frame, (100, 100), (200, 200), (255, 0, 0), -1)
    cv2.circle(test_frame, (400, 400), 50, (0, 255, 0), -1)
    
    print("✅ Test image created")
    print()
    
    # Test Hailo model
    print("🚀 Loading Hailo YOLOv8s model...")
    try:
        model = await get_model('hailo-yolov8s', {
            'confidence': 0.3,
            'power_mode': 'ultra_performance',
            'batch_size': 1,
            'latency_measurement': True
        })
        print("✅ Hailo model loaded successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to load Hailo model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Run inference
    print("⚡ Running Hailo inference (3 frames)...")
    inference_times = []
    
    for i in range(3):
        start = time.time()
        detections = await model.detect(test_frame)
        elapsed = (time.time() - start) * 1000  # ms
        inference_times.append(elapsed)
        
        print(f"  Frame {i+1}: {elapsed:.2f}ms, {len(detections)} detections")
    
    print()
    avg_time = sum(inference_times) / len(inference_times)
    avg_fps = 1000 / avg_time
    
    print("=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"Average inference time: {avg_time:.2f}ms")
    print(f"Average FPS: {avg_fps:.1f}")
    print(f"Target FPS (Hailo-8L): 26-30 (single stream)")
    print()
    
    # Get Hailo-specific metrics
    if hasattr(model, 'get_performance_metrics'):
        metrics = model.get_performance_metrics()
        if metrics:
            print("🔥 Hailo Hardware Metrics:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
            print()
    
    # Cleanup
    await model.cleanup()
    
    # Verdict
    if avg_fps >= 20:
        print("✅ TEST PASSED - Hailo is working!")
        print(f"   Inference speed: {avg_fps:.1f} FPS")
        return True
    else:
        print("⚠️  TEST WARNING - FPS lower than expected")
        print(f"   Got: {avg_fps:.1f} FPS")
        print(f"   Expected: 20+ FPS")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_hailo_inference())
    sys.exit(0 if result else 1)

