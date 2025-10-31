#!/bin/bash
#
# Build script for C++ frame processor
#

set -e

echo "================================"
echo "Building Overwatch Frame Processor"
echo "================================"
echo ""

# Check for required dependencies
command -v cmake >/dev/null 2>&1 || { echo "Error: cmake not found. Install with: brew install cmake"; exit 1; }

# Check for turbojpeg
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list jpeg-turbo &>/dev/null; then
        echo "Installing jpeg-turbo..."
        brew install jpeg-turbo
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! ldconfig -p | grep -q libturbojpeg; then
        echo "Error: libturbojpeg not found. Install with: sudo apt install libturbojpeg0-dev"
        exit 1
    fi
fi

# Create build directory
BUILD_DIR="build"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Configure
echo "Configuring build..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=.. \
    -DPython3_EXECUTABLE=$(which python3)

# Build
echo ""
echo "Building..."
make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

# Install (copy .so to parent directory)
echo ""
echo "Installing..."
make install

cd ..

echo ""
echo "================================"
echo "Build complete!"
echo "================================"
echo ""
echo "Module location: $(pwd)/frame_processor*.so"
echo ""
echo "Test the module:"
echo "  python3 -c 'import frame_processor; print(frame_processor.__doc__)'"
echo ""

