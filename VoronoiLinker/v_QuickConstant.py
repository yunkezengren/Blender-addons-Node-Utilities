import bpy
from pprint import pprint
from bpy.types import (NodeSocket, UILayout)

from .rot_or_mat_convert import Convert_Data, PIE_MT_Convert_To_Rotation, PIE_MT_Combine_Matrix
from .globals import Cursor_X_Offset
from .utils_drawing import TemplateDrawSksToolHh
from .v_tool import *
from .globals import *
from .utils_ui import *
from .utils_node import *
from .utils_color import *
from .utils_solder import *
from .utils_drawing import *
from .utils_translate import *
from .common_forward_func import *
from .common_forward_class import *
from .v_tool import VoronoiToolTripleSk

class VoronoiQuickConstant(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_constant'
    bl_label = "Voronoi Quick Constant"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def CallbackDrawTool(self, drata):
        # print(f"Quick Dimensions 类里 {drata = }")
        # TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2)
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Constant")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        if not self.canPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off= -Cursor_X_Offset):
            nd = ftgNd.tar
            # list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off= -Cursor_X_Offset)[0]
            if not list_ftgSksOut:
                continue
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    constant_type = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'STRING', 'BOOLEAN', 'ROTATION', 'MATRIX', 'MENU'}
                    if (ftg.tar.type in constant_type):
                    # if (ftg.tar.type in constant_type)or(ftg.tar.type=='GEOMETRY'):
                        self.fotagoSk0 = ftg
                        break
                CheckUncollapseNodeAndReNext(nd, self, cond=True, flag=True)
                break
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            skOut0 = optional_ftg_sk(self.fotagoSk0)
            if skOut0:
                multiple_link = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'STRING', 'BOOLEAN', 'ROTATION', 'MATRIX'}
                if skOut0.type not in multiple_link:     # 小王 允许同时连到多个输入的 输出接口类型
                    break
                if not self.canPickThird:
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==skOut0.type:
                            self.fotagoSk1 = ftg
                            break
                    if (self.fotagoSk1)and(self.fotagoSk1.tar==skOut0):
                        self.fotagoSk1 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
                    if self.fotagoSk1:
                        break
                else:
                    skOut1 = optional_ftg_sk(self.fotagoSk1)
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==skOut0.type:
                            self.fotagoSk2 = ftg
                            break
                    if (self.fotagoSk2)and( (self.fotagoSk2.tar==skOut0)or(skOut1)and(self.fotagoSk2.tar==skOut1) ):
                        self.fotagoSk2 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
                    if self.fotagoSk2:
                        break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        skIn0 = self.fotagoSk0.tar
        dict_qDM = dict_vqdtQuickConstantMain.get(tree.bl_idname, None)
        if skIn0.type in ["ROTATION", "MATRIX"]:
            Convert_Data.sk0 = skIn0
            if self.fotagoSk1:
                Convert_Data.sk1 = self.fotagoSk1.tar
            if self.fotagoSk2:
                Convert_Data.sk2 = self.fotagoSk2.tar
            if skIn0.type == "ROTATION":
                if hasattr(skIn0, "default_value"):
                    bpy.ops.wm.call_menu_pie(name=PIE_MT_Convert_To_Rotation.bl_idname)
                # return {'FINISHED'}       # 想松开按键确认
                # a_node.width = 200   # md这里不行，运行ops后立马运行下面的了？放在Rotation_Convert里的invoke就行了？ (那里放好这里忘删了找了半天错误)
            if skIn0.type == "MATRIX":
                bpy.ops.wm.call_menu_pie(name=PIE_MT_Combine_Matrix.bl_idname)
        else:
            node_type = dict_qDM[skIn0.type]
            bpy.ops.node.add_node('INVOKE_DEFAULT', type=node_type, use_transform=not self.isPlaceImmediately)
            a_node = tree.nodes.active
            skIn = a_node.outputs[0]

            tree.links.new(skIn, skIn0)
            if self.fotagoSk1:
                tree.links.new(skIn, self.fotagoSk1.tar)
            if self.fotagoSk2:
                tree.links.new(skIn, self.fotagoSk2.tar)

            # 小王 transfer value
            if hasattr(skIn0, "default_value"):
                value = skIn0.default_value
                if a_node.bl_idname == "FunctionNodeEulerToRotation":
                    a_node.inputs[0].default_value = value
                if a_node.bl_idname == "FunctionNodeInputBool":
                    a_node.boolean = value
                if a_node.bl_idname == "FunctionNodeInputString":
                    a_node.string = value
                if a_node.bl_idname == "GeometryNodeIndexSwitch":
                    a_node.data_type = "MENU"
                    a_node.show_options = False
                    id_name = skIn0.node.bl_idname
                    if id_name == "GeometryNodeMenuSwitch":
                        a_node.inputs[-1].hide = True
                        items = skIn0.node.enum_items
                        items_l = len(items)
                        if items_l >= 2:
                            for i in range(items_l - 2):
                                bpy.ops.node.index_switch_item_add()
                        for i in range(items_l):
                            a_node.inputs[i + 1].default_value = items[i].name
                    if id_name == "GeometryNodeIndexSwitch":
                        if skIn0.default_value != '':
                            a_node.inputs[1].default_value = skIn0.default_value
                if a_node.bl_idname == "ShaderNodeValue":
                    a_node.outputs[0].default_value = value
                if a_node.bl_idname == "FunctionNodeInputInt":
                    a_node.integer = value
                if a_node.bl_idname == "ShaderNodeCombineXYZ":
                    for i in range(3):
                        a_node.inputs[i].default_value = value[i]
                if a_node.bl_idname in ["FunctionNodeInputColor", "ShaderNodeRGB"]:
                    a_node.value = value
                    # a_node.color = value
