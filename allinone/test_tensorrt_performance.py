#!/usr/bin/env python3
"""
Performance Test: ONNX vs TensorRT
Proves TensorRT is actually faster
"""

import cv2
import numpy as np
import time
from ultralytics import YOLO
import os

def test_model_performance(model_path, model_name, num_iterations=50):
    """Test inference speed of a model"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Model: {model_path}")
    print(f"{'='*60}")

    # Check file exists
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return None

    # Load model
    print(f"Loading model...")
    start_load = time.time()

    if model_path.endswith('.engine'):
        model = YOLO(model_path, task='detect')
        print(f"✅ TensorRT engine loaded")
    else:
        model = YOLO(model_path)
        print(f"✅ Model loaded")

    load_time = time.time() - start_load
    print(f"Load time: {load_time:.2f}s")

    # Create test frame (640x480)
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Warmup runs (to initialize GPU)
    print(f"\nWarmup (5 runs)...")
    for i in range(5):
        _ = model.predict(test_frame, verbose=False)

    # Actual test
    print(f"\nRunning {num_iterations} inference tests...")
    times = []

    for i in range(num_iterations):
        start = time.time()
        results = model.predict(test_frame, verbose=False)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{num_iterations} - Avg so far: {np.mean(times):.2f}ms")

    # Calculate statistics
    times = np.array(times)
    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)
    std_time = np.std(times)

    print(f"\n📊 RESULTS:")
    print(f"  Average:  {avg_time:.2f} ms/frame")
    print(f"  Min:      {min_time:.2f} ms")
    print(f"  Max:      {max_time:.2f} ms")
    print(f"  Std Dev:  {std_time:.2f} ms")
    print(f"  FPS:      {1000/avg_time:.2f}")

    return {
        'name': model_name,
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'std': std_time,
        'fps': 1000/avg_time,
        'load_time': load_time
    }

def main():
    print("\n" + "="*60)
    print("  TENSORRT vs ONNX PERFORMANCE TEST")
    print("  Jetson TX1 - License Plate Detection")
    print("="*60)

    results = []

    # Test 1: TensorRT FP16
    if os.path.exists('models/best_fp16.engine'):
        result = test_model_performance(
            'models/best_fp16.engine',
            'TensorRT FP16',
            num_iterations=50
        )
        if result:
            results.append(result)
    else:
        print("\n⚠️  TensorRT engine not found: models/best_fp16.engine")

    # Test 2: ONNX
    if os.path.exists('models/best.onnx'):
        result = test_model_performance(
            'models/best.onnx',
            'ONNX Runtime',
            num_iterations=50
        )
        if result:
            results.append(result)
    else:
        print("\n⚠️  ONNX model not found: models/best.onnx")

    # Test 3: PyTorch (if available)
    if os.path.exists('models/best.pt'):
        result = test_model_performance(
            'models/best.pt',
            'PyTorch',
            num_iterations=30  # Fewer iterations (slower)
        )
        if result:
            results.append(result)

    # Summary comparison
    if len(results) >= 2:
        print("\n" + "="*60)
        print("  PERFORMANCE COMPARISON")
        print("="*60)
        print(f"\n{'Model':<20} {'Avg Time':<12} {'FPS':<8} {'Speedup'}")
        print("-" * 60)

        baseline = None
        for r in results:
            if 'ONNX' in r['name']:
                baseline = r['avg']
                break

        if not baseline:
            baseline = results[0]['avg']

        for r in results:
            speedup = baseline / r['avg']
            speedup_str = f"{speedup:.2f}x" if speedup != 1.0 else "baseline"
            print(f"{r['name']:<20} {r['avg']:>8.2f} ms  {r['fps']:>6.2f}  {speedup_str}")

        # Highlight TensorRT advantage
        tensorrt_result = next((r for r in results if 'TensorRT' in r['name']), None)
        onnx_result = next((r for r in results if 'ONNX' in r['name']), None)

        if tensorrt_result and onnx_result:
            speedup = onnx_result['avg'] / tensorrt_result['avg']
            time_saved = onnx_result['avg'] - tensorrt_result['avg']

            print("\n" + "="*60)
            print(f"  🚀 TensorRT vs ONNX:")
            print(f"     Speedup: {speedup:.2f}x faster")
            print(f"     Time saved: {time_saved:.2f}ms per frame")
            print(f"     FPS gain: {tensorrt_result['fps'] - onnx_result['fps']:.2f}")
            print("="*60)

            if speedup >= 1.5:
                print("\n✅ PROOF: TensorRT is significantly faster!")
            elif speedup >= 1.2:
                print("\n✅ PROOF: TensorRT provides noticeable speedup!")
            else:
                print("\n⚠️  TensorRT speedup is less than expected")

    print("\n✅ Test complete!\n")

if __name__ == "__main__":
    main()
