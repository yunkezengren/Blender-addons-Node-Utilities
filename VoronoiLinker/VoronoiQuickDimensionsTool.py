
from .VoronoiTool import VoronoiToolTripleSk, CheckUncollapseNodeAndReNext
from .common_func import *
from .关于节点的函数 import GetListOfNdEnums, NewLinkHhAndRemember, CheckUncollapseNodeAndReNext, FtgGetTargetOrNone
from .Rot_or_Mat_Converter import Convert_Data, Pie_MT_Converter_Rotation_To, Pie_MT_Separate_Matrix
from .globals import Cursor_X_Offset
from .draw_in_view import TemplateDrawSksToolHh

class VoronoiQuickDimensionsTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_dimensions'
    bl_label = "Voronoi Quick Dimensions"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def CallbackDrawTool(self, drata):
        # print(f"Quick Dimensions 类里 {drata = }")
        # TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2)
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Dimensions")
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
                    if (ftg.tar.type in set_utilTypeSkFields)or(ftg.tar.type=='GEOMETRY'):
                        self.fotagoSk0 = ftg
                        break
                CheckUncollapseNodeAndReNext(nd, self, cond=True, flag=True)
                break
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                if skOut0.type not in {'VALUE','INT','BOOLEAN'}:
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
                    skOut1 = FtgGetTargetOrNone(self.fotagoSk1)
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
        skOut0 = self.fotagoSk0.tar
        dict_qDM = dict_vqdtQuickDimensionsMain.get(tree.bl_idname, None)
        if not dict_qDM:
            return {'CANCELLED'}
        isOutNdCol = skOut0.node.bl_idname==dict_qDM['RGBA'][0] #Заметка: Нод разделения; на выходе всегда флоаты.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        isOutNdQuat = (isGeoTree)and(skOut0.node.bl_idname==dict_qDM['ROTATION'][0])
        #Добавить:
        if skOut0.type == "ROTATION":        # 小王-Alt D 旋转接口
            Convert_Data.sk0 = skOut0
            if self.fotagoSk1:
                Convert_Data.sk1 = self.fotagoSk1.tar
            if self.fotagoSk2:
                Convert_Data.sk2 = self.fotagoSk2.tar
            bpy.ops.wm.call_menu_pie(name=Pie_MT_Converter_Rotation_To.bl_idname)
        elif skOut0.type == "MATRIX":        # 小王-Alt D 矩阵接口
            Convert_Data.sk0 = skOut0
            if self.fotagoSk1:
                Convert_Data.sk1 = self.fotagoSk1.tar
            if self.fotagoSk2:
                Convert_Data.sk2 = self.fotagoSk2.tar
            bpy.ops.wm.call_menu_pie(name=Pie_MT_Separate_Matrix.bl_idname)
        else:
            bpy.ops.node.add_node('INVOKE_DEFAULT', type=dict_qDM[skOut0.type][isOutNdCol if not isOutNdQuat else 2], use_transform=not self.isPlaceImmediately)
            aNd = tree.nodes.active
            aNd.width = 140
            if aNd.bl_idname in {dict_qDM['RGBA'][0], dict_qDM['VALUE'][1]}: #|3|.
                aNd.show_options = False #Как-то неэстетично прятать без разбору, поэтому проверка выше.
            if aNd.bl_idname == 'GeometryNodeStringToCurves': #|3|.
                aNd.show_options = False
                aNd.outputs[-1].hide = True
                aNd.outputs[-2].hide = True
                for i in range(2, 6):
                    aNd.inputs[i].hide = True
            if skOut0.type in {'VECTOR', 'RGBA', 'ROTATION'}: #Зато экономия явных определений для каждого типа.
                aNd.inputs[0].hide_value = True
            #Установить одинаковость режимов (например, RGB и HSV):
            for li in GetListOfNdEnums(aNd):
                if hasattr(skOut0.node, li.identifier):
                    setattr(aNd, li.identifier, getattr(skOut0.node, li.identifier))
            #Соединить:
            skIn = aNd.inputs[0]
            # 遍历新建节点的输入接口,是否和目标输出接口同名,分离z 连到 合并z
            for ski in aNd.inputs:
                if skOut0.name==ski.name and skOut0.type==ski.type:
                    skIn = ski
                    break
            NewLinkHhAndRemember(skOut0, skIn)
            if self.fotagoSk1:
                NewLinkHhAndRemember(self.fotagoSk1.tar, aNd.inputs[1])
            if self.fotagoSk2:
                NewLinkHhAndRemember(self.fotagoSk2.tar, aNd.inputs[2])
