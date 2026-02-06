#!/bin/bash
# Install TensorRT Python bindings for Python 3.8 on Jetson TX1
# Based on: https://forums.developer.nvidia.com/t/tensorrt-on-jetson-with-python-3-9/196131/9
# Adapted for Python 3.8

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TensorRT Python 3.8 Installation${NC}"
echo -e "${GREEN}Jetson TX1 - JetPack 4.6.1${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${BLUE}Current Python: ${PYTHON_VERSION}${NC}"

if [[ ! "$PYTHON_VERSION" =~ ^3.8 ]]; then
    echo -e "${YELLOW}Warning: This script is designed for Python 3.8${NC}"
    echo -e "${YELLOW}Your version: ${PYTHON_VERSION}${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create build directory
BUILD_DIR="$HOME/tensorrt_build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo -e "\n${BLUE}Step 1: Install dependencies${NC}"
sudo apt-get update
sudo apt-get install -y \
    git \
    cmake \
    protobuf-compiler \
    libprotobuf-dev \
    python3-dev \
    python3-pip \
    libssl-dev

echo -e "\n${BLUE}Step 2: Clone pybind11${NC}"
if [ ! -d "pybind11" ]; then
    git clone https://github.com/pybind/pybind11.git
    cd pybind11
    git checkout v2.6.2  # Compatible version
    cd ..
fi

echo -e "\n${BLUE}Step 3: Clone TensorRT${NC}"
if [ ! -d "TensorRT" ]; then
    git clone -b release/8.0 https://github.com/NVIDIA/TensorRT.git
    cd TensorRT
    git submodule update --init --recursive
    cd ..
fi

echo -e "\n${BLUE}Step 4: Prepare Python headers${NC}"
PYTHON_INCLUDE=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())")
echo "Python include path: $PYTHON_INCLUDE"

# Create symbolic link if needed
if [ ! -f "TensorRT/python/include/python3.8/pyconfig.h" ]; then
    mkdir -p TensorRT/python/include/python3.8
    cp -r $PYTHON_INCLUDE/* TensorRT/python/include/python3.8/
fi

echo -e "\n${BLUE}Step 5: Build TensorRT Python bindings${NC}"
cd TensorRT/python

# Set environment variables
export TRT_OSSPATH=$(pwd)/..
export EXT_PATH=$(pwd)/../..
export TENSORRT_MODULE=tensorrt

# Modify build script for Python 3.8
sed -i 's/python3.9/python3.8/g' build.sh || true
sed -i 's/cp39/cp38/g' build.sh || true

echo -e "${YELLOW}Building TensorRT Python bindings... This may take 10-30 minutes${NC}"
bash ./build.sh

# Check if build succeeded
if [ -f "build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl" ]; then
    echo -e "\n${GREEN}✅ Build successful!${NC}"

    # Install to virtual environment
    echo -e "\n${BLUE}Step 6: Install to virtual environment${NC}"
    VENV_PATH="/home/jetson/yolo/yolov7/myenv"

    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
        pip install build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl

        # Test installation
        python3 -c "import tensorrt; print('TensorRT version:', tensorrt.__version__)"

        echo -e "\n${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ Installation Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}TensorRT Python bindings installed to:${NC}"
        echo -e "${GREEN}$VENV_PATH${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo -e "1. cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording"
        echo -e "2. Update fr01.py to use USE_TENSORRT = True"
        echo -e "3. Run: ./run_fr01.sh"
    else
        echo -e "${YELLOW}Virtual environment not found: $VENV_PATH${NC}"
        echo -e "${YELLOW}Wheel file created at:${NC}"
        echo -e "$(pwd)/build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl"
        echo -e "${YELLOW}Install manually with:${NC}"
        echo -e "pip install $(pwd)/build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl"
    fi
else
    echo -e "\n${RED}❌ Build failed${NC}"
    echo -e "${RED}Check the error messages above${NC}"
    exit 1
fi
