#!/bin/bash
# Rebuild PaddleOCR TensorRT Engines for GPU
# This converts PaddleOCR ONNX models to TensorRT engines optimized for Jetson TX1

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}PaddleOCR TensorRT Engine Rebuild${NC}"
echo -e "${GREEN}======================================================================${NC}"

# Check for ONNX models
if [ ! -f "models/paddleocr_onnx/det.onnx" ]; then
    echo -e "${RED}Error: ONNX models not found in models/paddleocr_onnx/${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/4] Activating environment...${NC}"
source ../myenv/bin/activate

echo -e "${YELLOW}[2/4] Converting Detection Model (det.onnx → det_fp16.engine)...${NC}"
/usr/src/tensorrt/bin/trtexec \
    --onnx=models/paddleocr_onnx/det.onnx \
    --saveEngine=models/paddleocr_onnx/det_fp16.engine \
    --fp16 \
    --workspace=1024 \
    --verbose \
    --dumpLayerInfo \
    --exportLayerInfo=models/paddleocr_onnx/det_layers.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Detection engine built${NC}"
else
    echo -e "${RED}✗ Detection engine failed${NC}"
fi

echo -e "${YELLOW}[3/4] Converting Recognition Model (rec_japan.onnx → rec_japan_fp16.engine)...${NC}"
/usr/src/tensorrt/bin/trtexec \
    --onnx=models/paddleocr_onnx/rec_japan.onnx \
    --saveEngine=models/paddleocr_onnx/rec_japan_fp16_gpu.engine \
    --fp16 \
    --workspace=1024 \
    --verbose \
    --dumpLayerInfo \
    --exportLayerInfo=models/paddleocr_onnx/rec_layers.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Recognition engine built${NC}"
else
    echo -e "${RED}✗ Recognition engine failed, trying without hardswish fix...${NC}"

    # Try with the no_hardswish version
    /usr/src/tensorrt/bin/trtexec \
        --onnx=models/paddleocr_onnx/rec_japan_no_hardswish.onnx \
        --saveEngine=models/paddleocr_onnx/rec_japan_fp16_gpu.engine \
        --fp16 \
        --workspace=1024 \
        --verbose
fi

echo -e "${YELLOW}[4/4] Converting Angle Classifier (cls.onnx → cls_fp16.engine)...${NC}"
/usr/src/tensorrt/bin/trtexec \
    --onnx=models/paddleocr_onnx/cls.onnx \
    --saveEngine=models/paddleocr_onnx/cls_fp16.engine \
    --fp16 \
    --workspace=512 \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Classifier engine built${NC}"
else
    echo -e "${RED}✗ Classifier engine failed (optional)${NC}"
fi

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}======================================================================${NC}"

# List created engines
echo ""
echo "Created engines:"
ls -lh models/paddleocr_onnx/*.engine

echo ""
echo -e "${GREEN}Next step: Update licence_plate_detection.py to use TensorRT engines${NC}"
echo -e "${GREEN}======================================================================${NC}"
