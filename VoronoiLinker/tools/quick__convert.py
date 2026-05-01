import bpy
from enum import Enum
from bpy.types import Context, NodeTree
from ..base_tool import BaseOperator
from ..common_class import VmtData

Convert_Data = VmtData()

class Convert(Enum):
    combine_matrix = 'combine_matrix'
    separate_matrix = 'separate_matrix'
    rotation_to = 'rotation_to'
    to_rotation = 'to_rotation'

PIE_MENU_ITEMS: dict[Convert, list[tuple[str, str]]] = {
    Convert.combine_matrix: [
        ('Combine Transform', 'FunctionNodeCombineTransform'),
        ('Combine Matrix',    'FunctionNodeCombineMatrix'),
    ],
    Convert.separate_matrix: [
        ('Separate Matrix',    'FunctionNodeSeparateMatrix'),
        ('Separate Transform', 'FunctionNodeSeparateTransform'),
    ],
    Convert.rotation_to: [
        ('Rotation > Euler',        'FunctionNodeRotationToEuler'),
        ('Rotation > Axis Angle',   'FunctionNodeRotationToAxisAngle'),
        ('Rotation > Quaternion',   'FunctionNodeRotationToQuaternion'),
        ('Rotation > Separate XYZ', 'ShaderNodeSeparateXYZ'),
    ],
    Convert.to_rotation: [
        ('Euler > Rotation',       'FunctionNodeEulerToRotation'),
        ('Axis Angle > Rotation',  'FunctionNodeAxisAngleToRotation'),
        ('Quaternion > Rotation',  'FunctionNodeQuaternionToRotation'),
        ('Combine XYZ > Rotation', 'ShaderNodeCombineXYZ'),
    ],
}

current_pie = None
def call_convert_pie(menu_key: Convert) -> None:
    global current_pie
    current_pie = menu_key
    bpy.ops.wm.call_menu_pie(name=NODE_MT_voronoi_convert.bl_idname)

class NODE_MT_voronoi_convert(bpy.types.Menu):
    bl_idname = "NODE_MT_voronoi_convert"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        for text, node_type in PIE_MENU_ITEMS[current_pie]:
            op = pie.operator(NODE_OT_voronoi_convert.bl_idname, text=text)
            op.node_type = node_type

def _run_node_convert(context: Context, isS: bool, isA: bool, node_type: str):
    tree: NodeTree = context.space_data.edit_tree
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=node_type, use_transform=True)
    new_node = context.active_node
    sk0 = Convert_Data.sk0
    sk1 = Convert_Data.sk1
    sk2 = Convert_Data.sk2
    if not sk0.is_output:
        skIn = new_node.outputs[0]
        tree.links.new(skIn, sk0)
        if sk1:
            if sk1.type == sk0.type:     # 解决矩阵和旋转接口共用 Convert_Data 问题
                tree.links.new(skIn, sk1)
                if sk2:
                    tree.links.new(skIn, sk2)
        if not hasattr(sk0, "default_value"):
            return
        value = sk0.default_value
        if new_node.bl_idname == "FunctionNodeEulerToRotation":
            new_node.inputs[0].default_value = value     # 旋转值传递
        if new_node.bl_idname == "ShaderNodeCombineXYZ":
            new_node.inputs[0].default_value = value[0]
            new_node.inputs[1].default_value = value[1]
            new_node.inputs[2].default_value = value[2]
    if sk0.is_output:
        sk_out = new_node.inputs[0]
        tree.links.new(sk0, sk_out)

# NODE_OT_voronoi_convert 只被快速维度和常量使用
class NODE_OT_voronoi_convert(BaseOperator):
    bl_idname = "node.voronoi_convert"
    bl_label = "Mixer Mixer"
    node_type: bpy.props.StringProperty()
    def invoke(self, context, event):
        _run_node_convert(context, event.shift, event.alt, self.node_type)
        return {'FINISHED'}
