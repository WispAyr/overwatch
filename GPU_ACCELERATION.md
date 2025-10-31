# GPU Acceleration Guide

## Automatic GPU Detection

Overwatch now **automatically detects and uses your GPU** for AI model inference!

### Supported GPUs:

✅ **NVIDIA GPUs** (CUDA)
- GeForce RTX/GTX series
- Quadro, Tesla datacenter GPUs
- 3-10x faster inference vs CPU
- Requires CUDA toolkit installed

✅ **Apple Silicon** (MPS - Metal Performance Shaders)
- M1, M2, M3, M4 chips
- Mac Studio, MacBook Pro, Mac Mini, iMac
- 2-5x faster inference vs CPU
- Built-in support (no extra drivers needed)

✅ **CPU Fallback**
- Works on any system
- No GPU required
- Still provides good performance with optimizations

## How It Works

When Overwatch starts, it automatically:

1. **Detects available hardware**
   - Checks for NVIDIA GPU (CUDA)
   - Checks for Apple Silicon (MPS)
   - Falls back to CPU if no GPU found

2. **Loads models on best device**
   - YOLO models automatically use GPU
   - All AI models benefit from acceleration
   - Seamless - no configuration needed!

3. **Logs device selection**
   ```
   ✅ GPU Detected: NVIDIA GeForce RTX 3080 (10.0 GB VRAM)
   🚀 Using NVIDIA GPU (CUDA) - Expect 3-10x faster inference!
   ```

## Performance Comparison

### CPU (Intel i7/i9 or Apple M1)
```
Model Inference:  30-50ms per frame
Max FPS:         15-20 FPS
X-RAY View:      10-15 FPS smooth
```

### Apple Silicon (M1/M2/M3/M4 with MPS)
```
Model Inference:  10-20ms per frame  (2-3x faster!)
Max FPS:         40-60 FPS
X-RAY View:      15-30 FPS smooth
```

### NVIDIA GPU (RTX 3060/3070/3080/4090)
```
Model Inference:  5-15ms per frame   (3-10x faster!)
Max FPS:         60-120 FPS
X-RAY View:      30-60 FPS smooth
```

## Manual Device Selection

If you want to force a specific device:

### Environment Variable
```bash
# Force NVIDIA GPU
export DEVICE=cuda

# Force Apple Silicon GPU
export DEVICE=mps

# Force CPU
export DEVICE=cpu

# Auto-detect (default)
export DEVICE=auto
```

### In .env File
```bash
# Add to .env file
DEVICE=auto  # or cuda, mps, cpu
```

### Check Current Device

Watch the startup logs:
```bash
tail -f /tmp/overwatch.log | grep "GPU\|Device\|CUDA\|MPS"
```

You'll see:
```
✅ GPU Detected: NVIDIA GeForce RTX 3080 (10.0 GB VRAM)
🚀 Using NVIDIA GPU (CUDA) - Expect 3-10x faster inference!
Model loaded on CUDA device
```

## Requirements

### For NVIDIA GPUs (CUDA):

1. **CUDA Toolkit** (11.x or 12.x)
   ```bash
   # Check if CUDA is available
   nvidia-smi
   ```

2. **PyTorch with CUDA**
   ```bash
   # Already installed if using requirements.txt
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

### For Apple Silicon (MPS):

**No extra setup needed!** ✅

PyTorch automatically supports Apple Silicon GPUs on:
- macOS 12.3+ (Monterey)
- M1, M2, M3, M4 chips
- Already works with your existing installation

### For CPU Only:

**No setup needed!** Works on any system.

## Troubleshooting

### "No GPU detected" on NVIDIA System

1. **Check NVIDIA drivers:**
   ```bash
   nvidia-smi
   ```

2. **Reinstall PyTorch with CUDA:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Check CUDA version:**
   ```bash
   nvcc --version
   ```

### "MPS not available" on Apple Silicon

1. **Update macOS** to 12.3 or later
2. **Restart backend** - MPS detection happens on startup
3. **Check PyTorch version:**
   ```bash
   python -c "import torch; print(torch.backends.mps.is_available())"
   ```

### GPU Out of Memory

If you get OOM errors:

1. **Lower resolution scale** in Video Input node (25% instead of 50%)
2. **Reduce processing FPS** (5-10 instead of 30)
3. **Use smaller model** (YOLOv8n instead of YOLOv8l)
4. **Close other GPU applications** (games, video editors, etc.)

## Monitoring GPU Usage

### NVIDIA GPUs:
```bash
# Watch GPU usage in real-time
watch -n 1 nvidia-smi
```

Look for:
- **GPU Util:** Should be 30-90% during inference
- **Memory Used:** Model uses ~500MB-2GB depending on size
- **Temperature:** Should stay under 80°C

### Apple Silicon:
```bash
# Monitor GPU activity
sudo powermetrics --samplers gpu_power -i 1000
```

Or use **Activity Monitor**:
- Open Activity Monitor
- Window → GPU History
- See "GPU %" usage

## Expected Performance Gains

### YOLOv8n (Nano) Model:

| Device | Inference Time | Max FPS | X-RAY FPS |
|--------|---------------|---------|-----------|
| CPU (i7) | 30-50ms | 15-20 | 10-15 |
| Apple M1 (MPS) | 10-20ms | 40-60 | 15-30 |
| RTX 3060 (CUDA) | 8-12ms | 60-80 | 30-60 |
| RTX 3080 (CUDA) | 5-10ms | 80-120 | 30-60 |
| RTX 4090 (CUDA) | 3-8ms | 100-200 | 30-60 |

*Note: X-RAY FPS capped at 15-30 for optimal visualization*

### YOLOv8s (Small) Model:

| Device | Inference Time | Max FPS |
|--------|---------------|---------|
| CPU (i7) | 60-100ms | 10-15 |
| Apple M1 (MPS) | 20-40ms | 25-50 |
| RTX 3080 (CUDA) | 8-15ms | 60-120 |

## Best Practices

### For Development:
- Use **auto-detection** (default)
- Monitor GPU usage to ensure it's being used
- Lower resolution if GPU memory is limited

### For Production:
- Explicitly set `DEVICE=cuda` or `DEVICE=mps` for consistency
- Monitor GPU temperature and usage
- Have CPU fallback ready for systems without GPU

### For Maximum Performance:
```bash
# Settings for high-FPS GPU inference
DEVICE=auto              # Auto-detect GPU
Resolution Scale: 50%    # Good balance
Processing FPS: 30       # Let GPU handle it
Batch Size: 1           # Real-time mode
JPEG Quality: 60%       # Optimized
```

## GPU Memory Requirements

### By Model Size:

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| YOLOv8n (Nano) | ~500 MB | Fastest | Good |
| YOLOv8s (Small) | ~1 GB | Fast | Better |
| YOLOv8m (Medium) | ~2 GB | Medium | Great |
| YOLOv8l (Large) | ~4 GB | Slower | Excellent |
| YOLOv8x (XLarge) | ~6 GB | Slowest | Best |

**Recommendation:** Start with YOLOv8n for real-time applications!

## Verification

Check if GPU acceleration is working:

1. **Start backend**
2. **Check logs:**
   ```bash
   tail -20 /tmp/overwatch.log | grep -i "gpu\|cuda\|mps\|device"
   ```

3. **Should see:**
   ```
   ✅ GPU Detected: [Your GPU]
   🚀 Using [CUDA/MPS] - Expect faster inference!
   Model loaded on [cuda/mps] device
   ```

4. **Monitor inference times:**
   - CPU: 30-50ms
   - GPU: 5-20ms ← Much faster!

## Success! 🎉

If you see GPU detection in the logs and faster inference times, you're all set!

GPU acceleration provides:
- ✅ Faster model inference
- ✅ Higher FPS capabilities  
- ✅ Smoother X-RAY View
- ✅ Lower CPU usage
- ✅ Better overall performance

Enjoy your accelerated AI detection! 🚀

