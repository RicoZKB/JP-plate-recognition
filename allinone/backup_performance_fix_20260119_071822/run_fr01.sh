#!/bin/bash
# Run script for License Plate Detection System (fr01.py)
# Clean camera initialization with IMX477 CSI camera support

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================================================${NC}"
echo -e "${GREEN}License Plate Detection System - IMX477 CSI Camera${NC}"
echo -e "${GREEN}================================================================================${NC}"

# Check if virtual environment exists
if [ ! -d "../myenv" ]; then
    echo -e "${RED}Error: Virtual environment not found at ../myenv${NC}"
    exit 1
fi

# Step 1: Clean up previous camera processes
echo -e "${YELLOW}[1/6] Cleaning up previous camera processes...${NC}"

# Kill any existing GStreamer processes
GSTREAMER_PIDS=$(pgrep -f "gst-launch\|nvarguscamera\|nvargus")
if [ ! -z "$GSTREAMER_PIDS" ]; then
    echo -e "${BLUE}  Found GStreamer processes: $GSTREAMER_PIDS${NC}"
    pkill -f "gst-launch"
    pkill -f "nvarguscamera"
    sleep 1
else
    echo -e "${BLUE}  No GStreamer processes found${NC}"
fi

# Kill any Python processes using OpenCV/camera
PYTHON_CAM_PIDS=$(pgrep -f "fr01.py\|fast_realtime")
if [ ! -z "$PYTHON_CAM_PIDS" ]; then
    echo -e "${BLUE}  Found Python camera processes: $PYTHON_CAM_PIDS${NC}"
    pkill -f "fr01.py"
    pkill -f "fast_realtime"
    sleep 1
else
    echo -e "${BLUE}  No Python camera processes found${NC}"
fi

# Step 2: Restart nvargus-daemon for clean camera state
echo -e "${YELLOW}[2/6] Restarting nvargus-daemon...${NC}"

# Stop nvargus-daemon
sudo systemctl stop nvargus-daemon
sleep 2

# Kill any remaining nvargus processes
sudo pkill -9 nvargus-daemon 2>/dev/null
sleep 1

# Start nvargus-daemon
sudo systemctl start nvargus-daemon
sleep 2

# Check if nvargus-daemon is running
if systemctl is-active --quiet nvargus-daemon; then
    echo -e "${GREEN}  ✓ nvargus-daemon restarted successfully${NC}"
else
    echo -e "${RED}  ✗ Warning: nvargus-daemon may not be running properly${NC}"
    echo -e "${YELLOW}  Attempting to start manually...${NC}"
    sudo /usr/sbin/nvargus-daemon &
    sleep 2
fi

# Step 3: Verify camera device
echo -e "${YELLOW}[3/6] Verifying camera device...${NC}"
if [ -e "/dev/video0" ]; then
    echo -e "${GREEN}  ✓ Camera device /dev/video0 found${NC}"
    ls -l /dev/video* | head -3
else
    echo -e "${RED}  ✗ Warning: Camera device not found${NC}"
fi

# Step 4: Activate virtual environment
echo -e "${YELLOW}[4/6] Activating virtual environment...${NC}"
source ../myenv/bin/activate
echo -e "${GREEN}  ✓ Virtual environment activated${NC}"

# Step 5: Set required environment variables
echo -e "${YELLOW}[5/6] Setting environment variables...${NC}"
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0:/usr/lib/aarch64-linux-gnu/libgomp.so.1
export GST_DEBUG=2  # GStreamer debug level (reduce if too verbose)
echo -e "${GREEN}  ✓ Environment variables set${NC}"

# Step 6: Run the detection system
echo -e "${YELLOW}[6/6] Starting license plate detection...${NC}"
echo -e "${GREEN}================================================================================${NC}"
echo ""

# Run with clean environment
python3 fr01.py

# Cleanup after exit
EXIT_CODE=$?
echo ""
echo -e "${GREEN}================================================================================${NC}"
echo -e "${GREEN}System stopped (exit code: $EXIT_CODE)${NC}"
echo -e "${GREEN}================================================================================${NC}"

# Optional: Clean up camera processes on exit
echo -e "${BLUE}Cleaning up camera processes...${NC}"
pkill -f "nvarguscamera" 2>/dev/null
echo -e "${GREEN}Done.${NC}"
