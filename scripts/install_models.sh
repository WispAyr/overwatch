#!/bin/bash
# Install AI Model Dependencies and Download Weights

set -e

echo "================================================"
echo "Overwatch AI Models Installation"
echo "================================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found. Please create one first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "================================================"
echo "Downloading Model Weights (Optional)"
echo "================================================"
echo "Models will auto-download on first use, but you can pre-download them now."
echo ""

read -p "Download YOLOv8-Pose models? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading YOLOv8-Pose models..."
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"
    echo "✓ yolov8n-pose.pt downloaded"
fi

read -p "Download YOLOv8-Seg models? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading YOLOv8-Seg models..."
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n-seg.pt')"
    echo "✓ yolov8n-seg.pt downloaded"
fi

echo ""
echo "================================================"
echo "Setting up Face Recognition Database"
echo "================================================"
echo "Creating face database directory..."
mkdir -p data/faces
echo "✓ Created data/faces/"
echo ""
echo "To add faces for recognition:"
echo "  1. mkdir -p data/faces/person_name"
echo "  2. cp face_image.jpg data/faces/person_name/"
echo "  3. Add multiple images per person for better accuracy"

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Available Models:"
echo "  ✓ YOLOv8 Object Detection (5 variants)"
echo "  ✓ YOLOv8-Pose Estimation (5 variants)"
echo "  ✓ YOLOv8-Seg Segmentation (5 variants)"
echo "  ✓ Object Tracking (5 variants)"
echo "  ✓ Face Recognition (DeepFace)"
echo "  ✓ License Plate Recognition (ALPR)"
echo "  ✓ Weapon Detection"
echo "  ✓ Fire & Smoke Detection"
echo "  ✓ PPE Detection"
echo "  ✓ Whisper Speech-to-Text (5 variants)"
echo "  ✓ YAMNet Audio Classification"
echo "  ✓ PANNs Audio Event Detection"
echo ""
echo "Total: 38+ model variants available!"
echo ""
echo "Next steps:"
echo "  1. Start the backend: ./run.sh"
echo "  2. Open workflow builder and see new models in sidebar"
echo "  3. Check NEW_MODELS_SUMMARY.md for usage examples"
echo ""


