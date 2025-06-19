from .关于翻译的函数 import *
from .关于节点的函数 import *
from .关于ui的函数 import *
from .关于颜色的函数 import *
from .VoronoiTool import *
from .关于sold的函数 import *
from .globals import *
from .common_class import *
from .common_func import *
from .draw_in_view import *
from .VoronoiTool import VoronoiOpTool
from .common_class import VmtData

import bpy
from bpy.types import Context, NodeTree


Convert_Data = VmtData()

def Do_Rot_or_Mat_Converter(context: Context, isS: bool, isA: bool, node_type: str):
    tree: NodeTree = context.space_data.edit_tree
    if not tree:
        return
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=node_type, use_transform=True)
    aNd = context.active_node
    sk0 = Convert_Data.sk0
    sk1 = Convert_Data.sk1
    sk2 = Convert_Data.sk2
    # if "ToRotation" in aNd.bl_idname:
    if not sk0.is_output:
        # print("." * 70)
        # print(f"{Convert_Data.__dict__ = }")
        # pprint(Convert_Data.__dict__)
        skIn = aNd.outputs[0]
        tree.links.new(skIn, sk0)
        if sk1:
            if sk1.type == sk0.type:     # 解决矩阵和旋转接口共用 Convert_Data 问题
                tree.links.new(skIn, sk1)
                if sk2:
                    tree.links.new(skIn, sk2)
        if not hasattr(sk0, "default_value"):
            return
        value = sk0.default_value
        if aNd.bl_idname == "FunctionNodeEulerToRotation":
            aNd.inputs[0].default_value = value     # 旋转值传递
        if aNd.bl_idname == "ShaderNodeCombineXYZ":
            aNd.inputs[0].default_value = value[0]
            aNd.inputs[1].default_value = value[1]
            aNd.inputs[2].default_value = value[2]
        # if isA:
        #     for sk in aNd.inputs:
        #         sk.hide = True
    if sk0.is_output:
    # if "RotationTo" in aNd.bl_idname:
        skOut = aNd.inputs[0]
        tree.links.new(sk0, skOut)
        # if Convert_Data.sk1:     tree.links.new(Convert_Data.sk1, skOut)    # 只有sk0,旋转节口不会触发更多

# Rot_or_Mat_Converter 只被快速维度和常量使用
class Rot_or_Mat_Converter(VoronoiOpTool):
    bl_idname = 'node.rot_or_mat_converter'
    bl_label = "Mixer Mixer"
    node_type: bpy.props.StringProperty()
    def invoke(self, context, event):
        Do_Rot_or_Mat_Converter(context, event.shift, event.alt, self.node_type)
        return {'FINISHED'}



class Pie_MT_Combine_Matrix(bpy.types.Menu):
    bl_idname = "Combine_Matrix"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        op = pie.operator('node.rot_or_mat_converter', text='Combine Transform')
        op.node_type = 'FunctionNodeCombineTransform'
        op = pie.operator('node.rot_or_mat_converter', text='Combine Matrix')
        op.node_type = 'FunctionNodeCombineMatrix'

class Pie_MT_Separate_Matrix(bpy.types.Menu):
    bl_idname = "Separate_Matrix"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        op = pie.operator('node.rot_or_mat_converter', text='Separate Matrix')
        op.node_type = 'FunctionNodeSeparateMatrix'
        op = pie.operator('node.rot_or_mat_converter', text='Separate Transform')
        op.node_type = 'FunctionNodeSeparateTransform'

class Pie_MT_Converter_Rotation_To(bpy.types.Menu):
    bl_idname = "Converter_Rotation_To"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        op = pie.operator('node.rot_or_mat_converter', text='Rotation > Euler')
        op.node_type = 'FunctionNodeRotationToEuler'
        op = pie.operator('node.rot_or_mat_converter', text='Rotation > Axis Angle')
        op.node_type = 'FunctionNodeRotationToAxisAngle'
        op = pie.operator('node.rot_or_mat_converter', text='Rotation > Quaternion')
        op.node_type = 'FunctionNodeRotationToQuaternion'
        op = pie.operator('node.rot_or_mat_converter', text='Rotation > Separate XYZ')
        op.node_type = 'ShaderNodeSeparateXYZ'

class Pie_MT_Converter_To_Rotation(bpy.types.Menu):
    bl_idname = "Converter_To_Rotation"
    bl_label = ""

    def draw(self, context):
        pie = self.layout.menu_pie()
        op = pie.operator('node.rot_or_mat_converter', text='Euler > Rotation')
        op.node_type = 'FunctionNodeEulerToRotation'
        op = pie.operator('node.rot_or_mat_converter', text='Axis Angle > Rotation')
        op.node_type = 'FunctionNodeAxisAngleToRotation'
        op = pie.operator('node.rot_or_mat_converter', text='Quaternion > Rotation')
        op.node_type = 'FunctionNodeQuaternionToRotation'
        op = pie.operator('node.rot_or_mat_converter', text='Combine XYZ > Rotation')
        op.node_type = 'ShaderNodeCombineXYZ'
