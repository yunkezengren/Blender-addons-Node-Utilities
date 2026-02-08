from ..base_tool import *
from ..globals import *
from ..utils.ui import *
from ..utils.node import *
from ..utils.color import *
from ..utils.solder import *
from ..utils.drawing import *
from ..utils.translate import *
from ..common_forward_func import *
from ..common_forward_class import *
from ..base_tool import VoronoiToolTripleSk
from ..common_forward_func import *
from ..utils.node import GetListOfNdEnums, remember_add_link, opt_ftg_socket
from .matrix_convert import Convert_Data, PIE_MT_Convert_Rotation_To, PIE_MT_Separate_Matrix
from ..globals import Cursor_X_Offset
from ..utils.drawing import TemplateDrawSksToolHh

def get_dimension_node(tree: NodeTree, sk_type: str):
    return AllQuickDimensions.get(tree.bl_idname, None).get(sk_type, None)

class VoronoiQuickDimensionsTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_dimensions'
    bl_label = "Voronoi Quick Dimensions"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def CallbackDrawTool(self, drata):
        # print(f"Quick Dimensions 类里 {drata = }")
        # TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2)
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Dimensions - 暂时只输出有效")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        if not self.canPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            if not list_ftgSksOut:
                continue
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    # set_utilTypeSkFields 小王-Alt D 支持的接口
                    # if (ftg.tar.type in set_utilTypeSkFields)or(ftg.tar.type=='GEOMETRY'):
                    if get_dimension_node(tree, ftg.tar.type):
                        self.fotagoSk0 = ftg
                        break
                CheckUncollapseNodeAndReNext(nd, self, cond=True, flag=True)
                break
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            sk_out0 = opt_ftg_socket(self.fotagoSk0)
            if sk_out0:
                if not get_dimension_node(tree, sk_out0.type):
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
                    skOut1 = opt_ftg_socket(self.fotagoSk1)
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==sk_out0.type:
                            self.fotagoSk2 = ftg
                            break
                    if (self.fotagoSk2)and( (self.fotagoSk2.tar==sk_out0)or(skOut1)and(self.fotagoSk2.tar==skOut1) ):
                        self.fotagoSk2 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
                    if self.fotagoSk2:
                        break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        sk_out0 = self.fotagoSk0.tar
        Q_Dimensions = AllQuickDimensions.get(tree.bl_idname, None)
        if not Q_Dimensions:
            return {'CANCELLED'}
        isOutNdCol = sk_out0.node.bl_idname==Q_Dimensions['RGBA'][0] #Заметка: Нод разделения; на выходе всегда флоаты.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        isOutNdQuat = (isGeoTree)and(sk_out0.node.bl_idname==Q_Dimensions['ROTATION'][0])
        #Добавить:
        if sk_out0.type == "ROTATION":        # 小王-Alt D 旋转接口
            Convert_Data.sk0 = sk_out0
            if self.fotagoSk1:
                Convert_Data.sk1 = self.fotagoSk1.tar
            if self.fotagoSk2:
                Convert_Data.sk2 = self.fotagoSk2.tar
            bpy.ops.wm.call_menu_pie(name=PIE_MT_Convert_Rotation_To.bl_idname)
        elif sk_out0.type == "MATRIX":        # 小王-Alt D 矩阵接口
            Convert_Data.sk0 = sk_out0
            if self.fotagoSk1:
                Convert_Data.sk1 = self.fotagoSk1.tar
            if self.fotagoSk2:
                Convert_Data.sk2 = self.fotagoSk2.tar
            bpy.ops.wm.call_menu_pie(name=PIE_MT_Separate_Matrix.bl_idname)
        else:
            bpy.ops.node.add_node('INVOKE_DEFAULT',
                                  type=Q_Dimensions[sk_out0.type][isOutNdCol if not isOutNdQuat else 2],
                                  use_transform=not self.isPlaceImmediately)
            aNd = tree.nodes.active
            aNd.width = 140
            if aNd.bl_idname in {Q_Dimensions['RGBA'][0], Q_Dimensions['VALUE'][1]}:  #|3|.
                aNd.show_options = False  # 不加区分地隐藏(所有选项)不太美观, 所以才有了上面的检查.
            if aNd.bl_idname == 'GeometryNodeStringToCurves':  #|3|.
                aNd.show_options = False
                aNd.outputs[-1].hide = True
                aNd.outputs[-2].hide = True
                for i in range(2, 6):
                    aNd.inputs[i].hide = True
            if sk_out0.type in {'VECTOR', 'RGBA', 'ROTATION'}:  # 但这样做的好处是, 可以为每种类型节省显式的定义.
                aNd.inputs[0].hide_value = True
            # 设置相同的模式 (例如, RGB 和 HSV):
            for li in GetListOfNdEnums(aNd):
                if hasattr(sk_out0.node, li.identifier):
                    setattr(aNd, li.identifier, getattr(sk_out0.node, li.identifier))
            # 连接:
            skIn = aNd.inputs[0]
            # 遍历新建节点的输入接口,是否和目标输出接口同名,分离z 连到 合并z
            for ski in aNd.inputs:
                if sk_out0.name == ski.name and sk_out0.type == ski.type:
                    skIn = ski
                    break
            remember_add_link(sk_out0, skIn)
            if self.fotagoSk1:
                remember_add_link(self.fotagoSk1.tar, aNd.inputs[1])
            if self.fotagoSk2:
                remember_add_link(self.fotagoSk2.tar, aNd.inputs[2])

            if sk_out0.type in ["CLOSURE", "BUNDLE"]:
                bpy.ops.node.sockets_sync()
