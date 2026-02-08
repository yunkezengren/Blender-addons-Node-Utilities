import bpy
from pprint import pprint
from bpy.types import (NodeSocket, UILayout, NodeTree)

from .matrix_convert import Convert_Data, PIE_MT_Convert_To_Rotation, PIE_MT_Combine_Matrix
from ..globals import Cursor_X_Offset
from ..utils.drawing import TemplateDrawSksToolHh
from ..base_tool import *
from ..globals import *
from ..utils.ui import *
from ..utils.node import *
from ..utils.color import *
from ..utils.solder import *
from ..utils.drawing import *
from ..common_forward_func import *
from ..common_forward_class import *
from ..base_tool import VoronoiToolTripleSk

BT = bpy.types

def get_const_node(tree: NodeTree, sk_type: str):
    return AllQuickConstant.get(tree.bl_idname, None).get(sk_type, None)

class VoronoiQuickConstant(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_constant'
    bl_label = "Voronoi Quick Constant"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Constant - 暂时只对输入有效")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        if not self.canPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off= -Cursor_X_Offset):
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off= -Cursor_X_Offset)[0]
            if not list_ftgSksOut:
                continue
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    # ! AllQuickConstant 新的接口类型要在这里更新
                    if get_const_node(tree, ftg.tar.type):
                        self.fotagoSk0 = ftg
                        break
                CheckUncollapseNodeAndReNext(nd, self, cond=True, flag=True)
                break
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            sk_out0 = opt_ftg_socket(self.fotagoSk0)
            if sk_out0:
                only_single_link = {'MENU'}
                if sk_out0.type in only_single_link:     # 小王 输出接口类型 不允许同时连到多个输入接口
                    break
                if not self.canPickThird:
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==sk_out0.type:
                            self.fotagoSk1 = ftg
                            break
                    if (self.fotagoSk1)and(self.fotagoSk1.tar==sk_out0):
                        self.fotagoSk1 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
                    if self.fotagoSk1:
                        break
                else:
                    sk_out1 = opt_ftg_socket(self.fotagoSk1)
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==sk_out0.type:
                            self.fotagoSk2 = ftg
                            break
                    if (self.fotagoSk2)and( (self.fotagoSk2.tar==sk_out0)or(sk_out1)and(self.fotagoSk2.tar==sk_out1) ):
                        self.fotagoSk2 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
                    if self.fotagoSk2:
                        break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        skIn0 = self.fotagoSk0.tar
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
                # active_node.width = 200   # md这里不行，运行ops后立马运行下面的了？放在Rotation_Convert里的invoke就行了？ (那里放好这里忘删了找了半天错误)
            if skIn0.type == "MATRIX":
                bpy.ops.wm.call_menu_pie(name=PIE_MT_Combine_Matrix.bl_idname)
        else:
            node_type = get_const_node(tree, skIn0.type)
            if node_type == "NodeClosureOutput":
                bpy.ops.node.add_closure_zone('INVOKE_DEFAULT', use_transform=True)
            else:
                bpy.ops.node.add_node('INVOKE_DEFAULT', type=node_type, use_transform=not self.isPlaceImmediately)
            active_node = tree.nodes.active
            sk_out = active_node.outputs[0]

            tree.links.new(sk_out, skIn0)
            if self.fotagoSk1:
                tree.links.new(sk_out, self.fotagoSk1.tar)
            if self.fotagoSk2:
                tree.links.new(sk_out, self.fotagoSk2.tar)

            if isinstance(active_node, (BT.NodeClosureOutput, BT.NodeCombineBundle)):
                bpy.ops.node.sockets_sync()
                return

            # 小王 transfer value
            if not hasattr(skIn0, "default_value"):
                return
            value = skIn0.default_value

            if isinstance(active_node, BT.ShaderNodeValue):
                active_node.outputs[0].default_value = value

            elif isinstance(active_node, (BT.FunctionNodeInputColor, BT.ShaderNodeRGB)):
                active_node.value = value

            elif isinstance(active_node, BT.FunctionNodeInputInt):
                active_node.integer = value

            elif isinstance(active_node, BT.FunctionNodeInputBool):
                active_node.boolean = value

            elif isinstance(active_node, BT.FunctionNodeInputString):
                active_node.string = value

            elif isinstance(active_node, BT.GeometryNodeInputImage):
                active_node.image = value

            elif isinstance(active_node, BT.GeometryNodeInputMaterial):
                active_node.material = value

            elif isinstance(active_node, BT.GeometryNodeInputObject):
                active_node.object = value

            elif isinstance(active_node, BT.GeometryNodeInputCollection):
                active_node.collection = value

            elif isinstance(active_node, BT.FunctionNodeEulerToRotation):
                active_node.inputs[0].default_value = value

            elif isinstance(active_node, BT.ShaderNodeCombineXYZ):
                for i in range(3):
                    active_node.inputs[i].default_value = value[i]

            elif isinstance(active_node, BT.GeometryNodeIndexSwitch):
                active_node.data_type = "MENU"
                active_node.show_options = False
                id_name = skIn0.node.bl_idname
                if id_name == "GeometryNodeMenuSwitch":
                    active_node.inputs[-1].hide = True
                    items = skIn0.node.enum_items
                    items_l = len(items)
                    if items_l >= 2:
                        for i in range(items_l - 2):
                            bpy.ops.node.index_switch_item_add()
                    for i in range(items_l):
                        active_node.inputs[i + 1].default_value = items[i].name
                if id_name == "GeometryNodeIndexSwitch":
                    if skIn0.default_value != '':
                        active_node.inputs[1].default_value = skIn0.default_value
