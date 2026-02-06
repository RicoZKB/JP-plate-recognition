#!/usr/bin/env python3
"""
Test script to verify CSV output format
Simulates plate detection and logging
"""

import csv
import os
from datetime import datetime

def test_csv_format():
    """Test CSV creation and format"""
    print("=" * 80)
    print("CSV OUTPUT FORMAT TEST")
    print("=" * 80)

    # Create test CSV
    test_file = "logs/test_output.csv"
    os.makedirs("logs", exist_ok=True)

    # Open CSV and write header
    with open(test_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # Header
        w.writerow(["timestamp", "object_id", "vehicle_type", "direction",
                   "city", "class_number", "kana", "suffix"])

        # Test data rows - simulating Japanese license plates
        test_plates = [
            {
                "timestamp": "2026-01-15 10:23:45",
                "object_id": "01",
                "vehicle_type": "car",
                "direction": "in",
                "city": "品川",
                "class_number": "330",
                "kana": "あ",
                "suffix": "12-34"
            },
            {
                "timestamp": "2026-01-15 10:24:12",
                "object_id": "02",
                "vehicle_type": "car",
                "direction": "in",
                "city": "横浜",
                "class_number": "500",
                "kana": "さ",
                "suffix": "56-78"
            },
            {
                "timestamp": "2026-01-15 10:25:33",
                "object_id": "03",
                "vehicle_type": "car",
                "direction": "in",
                "city": "世田谷",
                "class_number": "310",
                "kana": "ろ",
                "suffix": "90-12"
            },
            {
                "timestamp": "2026-01-15 10:26:01",
                "object_id": "04",
                "vehicle_type": "car",
                "direction": "in",
                "city": "多摩",
                "class_number": "589",
                "kana": "",
                "suffix": "20-46"
            }
        ]

        # Write test data
        for plate in test_plates:
            w.writerow([
                plate["timestamp"],
                plate["object_id"],
                plate["vehicle_type"],
                plate["direction"],
                plate["city"],
                plate["class_number"],
                plate["kana"],
                plate["suffix"]
            ])
            f.flush()

    print(f"\n✓ Created test CSV: {test_file}\n")

    # Read and display the CSV
    print("CSV CONTENTS:")
    print("-" * 80)
    with open(test_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            print(" | ".join(f"{cell:15s}" for cell in row))
    print("-" * 80)

    # Simulate terminal output for each plate
    print("\nSIMULATED TERMINAL OUTPUT:")
    print("=" * 80)

    for i, plate in enumerate(test_plates, 1):
        print("=" * 80)
        print(f"🚗 LICENSE PLATE DETECTED")
        print("=" * 80)
        print(f"  Timestamp:      {plate['timestamp']}")
        print(f"  Object ID:      {plate['object_id']}")
        print(f"  Vehicle Type:   {plate['vehicle_type']}")
        print(f"  Direction:      {plate['direction']}")
        print(f"  City:           {plate['city'] or '(not detected)'}")
        print(f"  Class Number:   {plate['class_number'] or '(not detected)'}")
        print(f"  Kana:           {plate['kana'] or '(not detected)'}")
        print(f"  Suffix:         {plate['suffix'] or '(not detected)'}")
        quality = 8 if plate['kana'] else 5
        print(f"  Quality Score:  {quality}/8")
        print("=" * 80)
        print()

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nVerify the CSV file at: {test_file}")
    print("You can open it in Excel or any spreadsheet program.")
    print("\nEach field is in a separate column:")
    print("  1. timestamp      - Date and time (YYYY-MM-DD HH:MM:SS)")
    print("  2. object_id      - Sequential ID (01, 02, 03...)")
    print("  3. vehicle_type   - Type of vehicle (car, truck, etc.)")
    print("  4. direction      - Direction (in/out)")
    print("  5. city           - City name (品川, 横浜, etc.)")
    print("  6. class_number   - Class number (3 digits)")
    print("  7. kana           - Kana character (あ, さ, etc.)")
    print("  8. suffix         - Four-digit number (XX-XX)")
    print("=" * 80)

if __name__ == "__main__":
    test_csv_format()
