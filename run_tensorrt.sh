#!/bin/bash
# Wrapper script to run inout_event.py with TensorRT
# Preloads libGLdispatch to fix TLS memory allocation error

export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0
source ../myenv/bin/activate
python3 inout_event.py "$@"
