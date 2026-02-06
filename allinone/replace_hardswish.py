#!/usr/bin/env python3
"""
Replace HardSwish operators with equivalent operations TensorRT 8.0.1 supports
HardSwish(x) = x * ReLU6(x + 3) / 6
"""

import onnx
from onnx import helper, TensorProto
import numpy as np

def replace_hardswish_with_relu6(model_path, output_path):
    """Replace HardSwish nodes with ReLU6 equivalent"""
    model = onnx.load(model_path)
    graph = model.graph

    # Find all HardSwish nodes
    hardswish_nodes = [node for node in graph.node if node.op_type == 'HardSwish']

    print(f"Found {len(hardswish_nodes)} HardSwish nodes to replace")

    if len(hardswish_nodes) == 0:
        print("No HardSwish nodes found!")
        return False

    # Track nodes to remove and add
    nodes_to_remove = []
    nodes_to_add = []

    for i, hs_node in enumerate(hardswish_nodes):
        input_name = hs_node.input[0]
        output_name = hs_node.output[0]

        # Create intermediate tensor names
        add_out = f"{output_name}_add3"
        relu6_out = f"{output_name}_relu6"
        div_out = f"{output_name}_div6"

        # HardSwish(x) = x * ReLU6(x + 3) / 6

        # 1. Add constant 3
        const_3_name = f"const_3_{i}"
        const_3 = helper.make_node(
            'Constant',
            inputs=[],
            outputs=[const_3_name],
            value=helper.make_tensor(
                name=f'const_3_value_{i}',
                data_type=TensorProto.FLOAT,
                dims=[],
                vals=[3.0]
            )
        )

        # 2. Add: x + 3
        add_node = helper.make_node(
            'Add',
            inputs=[input_name, const_3_name],
            outputs=[add_out]
        )

        # 3. Clip (ReLU6): min=0, max=6
        clip_node = helper.make_node(
            'Clip',
            inputs=[add_out],
            outputs=[relu6_out]
        )
        # Add min/max as attributes for older ONNX
        clip_node.attribute.extend([
            helper.make_attribute('min', 0.0),
            helper.make_attribute('max', 6.0)
        ])

        # 4. Divide by 6
        const_6_name = f"const_6_{i}"
        const_6 = helper.make_node(
            'Constant',
            inputs=[],
            outputs=[const_6_name],
            value=helper.make_tensor(
                name=f'const_6_value_{i}',
                data_type=TensorProto.FLOAT,
                dims=[],
                vals=[6.0]
            )
        )

        div_node = helper.make_node(
            'Div',
            inputs=[relu6_out, const_6_name],
            outputs=[div_out]
        )

        # 5. Multiply: x * (result)
        mul_node = helper.make_node(
            'Mul',
            inputs=[input_name, div_out],
            outputs=[output_name]
        )

        # Add new nodes
        nodes_to_add.extend([const_3, add_node, clip_node, const_6, div_node, mul_node])
        nodes_to_remove.append(hs_node)

        print(f"  Replaced HardSwish node {i+1}/{len(hardswish_nodes)}: {hs_node.name}")

    # Remove old HardSwish nodes
    for node in nodes_to_remove:
        graph.node.remove(node)

    # Add new equivalent nodes
    graph.node.extend(nodes_to_add)

    # Save modified model
    onnx.save(model, output_path)
    print(f"\nSaved modified model to: {output_path}")
    print("✅ HardSwish replacement complete!")

    return True

if __name__ == "__main__":
    input_model = "models/paddleocr_onnx/rec_japan.onnx"
    output_model = "models/paddleocr_onnx/rec_japan_no_hardswish.onnx"

    print("="*60)
    print("Replacing HardSwish with TensorRT 8.0.1 compatible ops")
    print("="*60)

    success = replace_hardswish_with_relu6(input_model, output_model)

    if success:
        print("\n" + "="*60)
        print("Next step: Convert to TensorRT with trtexec")
        print("="*60)
        print(f"\n/usr/src/tensorrt/bin/trtexec \\")
        print(f"  --onnx={output_model} \\")
        print(f"  --saveEngine=models/paddleocr_onnx/rec_japan_fp16.engine \\")
        print(f"  --fp16 \\")
        print(f"  --minShapes=x:1x3x48x32 \\")
        print(f"  --optShapes=x:1x3x48x320 \\")
        print(f"  --maxShapes=x:1x3x48x640")
