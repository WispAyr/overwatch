#!/usr/bin/env python3
"""
Test script for C++ frame processor
"""

import numpy as np
import time
import sys

def test_import():
    """Test if module can be imported"""
    try:
        import frame_processor
        print("✓ C++ module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import C++ module: {e}")
        return False

def test_basic_operations():
    """Test basic operations"""
    import frame_processor
    
    proc = frame_processor.FrameProcessor(num_threads=4)
    
    # Create test frame
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    print("\n=== Testing Basic Operations ===")
    
    # Test JPEG encoding
    print("Testing JPEG encoding...")
    jpeg_bytes = proc.encode_jpeg(frame, quality=85)
    print(f"✓ Encoded to {len(jpeg_bytes)} bytes")
    
    # Test resize
    print("Testing resize...")
    resized = proc.resize_frame(frame, 640, 640)
    assert resized.shape == (640, 640, 3)
    print(f"✓ Resized to {resized.shape}")
    
    # Test color conversion
    print("Testing BGR to RGB...")
    rgb = proc.bgr_to_rgb(frame)
    assert rgb.shape == frame.shape
    print(f"✓ Converted to RGB")
    
    # Test preprocessing
    print("Testing preprocessing...")
    result = proc.preprocess_for_inference(frame, 640, 640, True, True)
    print(f"✓ Preprocessed: {result['width']}x{result['height']}, {result['channels']} channels")
    
    # Test stats
    print("\nStats:")
    print(f"  Frames processed: {proc.get_frames_processed()}")
    print(f"  Bytes encoded: {proc.get_bytes_encoded()}")
    
    return True

def test_batch_encoding():
    """Test batch encoding"""
    import frame_processor
    
    proc = frame_processor.FrameProcessor(num_threads=4)
    
    print("\n=== Testing Batch Encoding ===")
    
    # Create test frames
    frames = [
        np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        for _ in range(8)
    ]
    
    print(f"Encoding {len(frames)} frames...")
    start = time.time()
    results = proc.batch_encode_jpeg(frames, quality=85)
    elapsed = time.time() - start
    
    print(f"✓ Encoded {len(results)} frames in {elapsed*1000:.1f}ms")
    print(f"  Average: {elapsed*1000/len(frames):.1f}ms per frame")
    
    total_size = sum(len(r) for r in results)
    print(f"  Total size: {total_size / 1024 / 1024:.2f} MB")
    
    return True

def test_python_wrapper():
    """Test Python wrapper with fallback"""
    print("\n=== Testing Python Wrapper ===")
    
    from stream.fast_processor import FastFrameProcessor
    
    proc = FastFrameProcessor(num_threads=4)
    
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # Test single encoding
    jpeg_bytes = proc.encode_jpeg(frame, quality=85)
    print(f"✓ Encoded to {len(jpeg_bytes)} bytes")
    
    # Test batch encoding
    frames = [frame.copy() for _ in range(4)]
    results = proc.batch_encode_jpeg(frames, quality=85)
    print(f"✓ Batch encoded {len(results)} frames")
    
    # Stats
    stats = proc.get_stats()
    print(f"\nStats:")
    print(f"  Using C++: {stats['using_cpp']}")
    print(f"  Frames: {stats['frames_processed']}")
    print(f"  Bytes: {stats['bytes_encoded']}")
    
    return True

def benchmark():
    """Run performance benchmark"""
    import frame_processor
    import cv2
    
    print("\n=== Performance Benchmark ===")
    
    proc = frame_processor.FrameProcessor(num_threads=8)
    
    # Test frame
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # Warmup
    for _ in range(10):
        proc.encode_jpeg(frame, quality=85)
        cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    # Benchmark turbojpeg
    iterations = 100
    start = time.time()
    for _ in range(iterations):
        proc.encode_jpeg(frame, quality=85)
    turbo_time = (time.time() - start) / iterations
    
    # Benchmark cv2
    start = time.time()
    for _ in range(iterations):
        cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    cv2_time = (time.time() - start) / iterations
    
    print(f"Single frame (1920x1080):")
    print(f"  cv2.imencode:     {cv2_time*1000:.2f}ms")
    print(f"  turbojpeg:        {turbo_time*1000:.2f}ms")
    print(f"  Speedup:          {cv2_time/turbo_time:.2f}x")
    
    # Batch benchmark
    frames = [frame.copy() for _ in range(8)]
    
    # Warmup
    for _ in range(5):
        proc.batch_encode_jpeg(frames, quality=85)
    
    start = time.time()
    for _ in range(20):
        proc.batch_encode_jpeg(frames, quality=85)
    batch_time = (time.time() - start) / 20
    
    # Sequential cv2
    start = time.time()
    for _ in range(20):
        for f in frames:
            cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 85])
    sequential_time = (time.time() - start) / 20
    
    print(f"\nBatch encoding (8 frames):")
    print(f"  cv2 sequential:   {sequential_time*1000:.2f}ms")
    print(f"  turbojpeg batch:  {batch_time*1000:.2f}ms")
    print(f"  Speedup:          {sequential_time/batch_time:.2f}x")
    print(f"  Per frame:        {batch_time*1000/8:.2f}ms")

def main():
    print("=" * 60)
    print("Overwatch C++ Frame Processor Test Suite")
    print("=" * 60)
    
    # Test import
    if not test_import():
        print("\n✗ C++ module not available. Build with: ./build.sh")
        return 1
    
    try:
        # Run tests
        test_basic_operations()
        test_batch_encoding()
        test_python_wrapper()
        benchmark()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

