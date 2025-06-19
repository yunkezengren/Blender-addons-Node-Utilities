from .关于翻译的函数 import *
from .关于节点的函数 import *
from .关于ui的函数 import *
from .关于颜色的函数 import *
from .VoronoiTool import *
from .关于sold的函数 import *
from .globals import *
from .common_class import *
from .common_func import *
from .关于绘制的函数 import *
from .VoronoiTool import VoronoiOpTool
from .common_class import VmtData
from .关于节点的函数 import DoLinkHh
from .关于颜色的函数 import get_sk_color
from bpy.app.translations import pgettext_iface as TranslateIface



def DoMix(tree, isShift, isAlt, type):
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=type, use_transform=not VmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    aNd.width = 140
    txtFix = {'VALUE':'FLOAT'}.get(VmtData.skType, VmtData.skType)
    # 两次 switch case -- 为了代码舒适和一点点节约.
    match aNd.bl_idname:
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath':
            aNd.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            aNd.operation = 'OR'
        case 'TextureNodeTexture':
            aNd.show_preview = False
        case 'GeometryNodeSwitch':
            aNd.input_type = txtFix
        case 'FunctionNodeCompare':
            aNd.data_type = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
            aNd.operation = 'EQUAL'
        case 'ShaderNodeMix':
            aNd.data_type = {'INT':'FLOAT', 'BOOLEAN':'FLOAT'}.get(txtFix, txtFix)
    match aNd.bl_idname:
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|2|.
            tgl = aNd.bl_idname!='FunctionNodeCompare'
            txtFix = VmtData.skType
            match aNd.bl_idname:
                case 'FunctionNodeCompare': txtFix = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
                case 'ShaderNodeMix':       txtFix = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(txtFix, txtFix)
            # 对于混合和切换器, 从末尾搜索, 因为它们的切换套接字类型与某些搜索的类型相同. 比较节点则相反.
            list_foundSk = [sk for sk in ( reversed(aNd.inputs) if tgl else aNd.inputs ) if sk.type==txtFix]
            NewLinkHhAndRemember(VmtData.sk0, list_foundSk[tgl^isShift]) # 由于搜索方向, 也需要根据方向从列表中选择它们.
            if VmtData.sk1:
                NewLinkHhAndRemember(VmtData.sk1, list_foundSk[(not tgl)^isShift])
        case _:
            # 这种密集的处理是为了多输入 -- 需要改变连接顺序.
            Mix_item = dict_vmtMixerNodesDefs[aNd.bl_idname]
            swap_link = 0       # sk0是矩阵,sk1是矢量,不交换(这是默认情况)
            if VmtData.sk1 and VmtData.sk1.type == "MATRIX" and VmtData.sk0.type != "MATRIX":
                swap_link = 1
            soc_in = aNd.inputs[Mix_item[1^isShift^swap_link]]
            is_multi_in = aNd.inputs[Mix_item[0]].is_multi_input
            if (VmtData.sk1)and(is_multi_in): # `0` 在这里主要是因为 dict_vmtMixerNodesDefs 中的“多输入节点”都是零.
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
            DoLinkHh( VmtData.sk0, aNd.inputs[Mix_item[0^isShift]^swap_link] ) # 注意: 这不是 NewLinkHhAndRemember(), 以便多输入的第二个视觉上是 VlrtData 中的最后一个.
            if (VmtData.sk1)and(not is_multi_in):
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
    aNd.show_options = not VmtData.isHideOptions
    # 接下来和 vqmt 中一样. 它的是主要的; 这里为了直观对应而复制.
    if isAlt:
        for sk in aNd.inputs:
            sk.hide = True

class VmtOpMixer(VoronoiOpTool):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = "Mixer Mixer"
    operation: bpy.props.StringProperty()
    def invoke(self, context, event):
        DoMix(context.space_data.edit_tree, event.shift, event.alt, self.operation)
        return {'FINISHED'}
class VmtPieMixer(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_mixer_pie'
    bl_label = "" # 这里的文本将显示在饼菜单的中心.
    def draw(self, context):
        def LyVmAddOp(where: UILayout, txt):
            where.operator(VmtOpMixer.bl_idname, text=TranslateIface(dict_vmtMixerNodesDefs[txt][2])).operation = txt
        def LyVmAddItem(where: UILayout, txt):
            ly = where.row(align=VmtData.pieAlignment==0)
            soldPdsc = VmtData.pieDisplaySocketColor
            if soldPdsc:
                # ly = ly.split(factor=( abs( (soldPdsc>0)- 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VmtData.uiScale, align=True)
                # print("."*50)
                # print(f"{ VmtData.uiScale = }")
                # print(f"{ soldPdsc>0 = }")
                # print(f"{ abs(soldPdsc) = }")
                # print(f"{ 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) = }")
                # print(f"{ ( abs( (soldPdsc>0)- 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VmtData.uiScale = }")
                # ly = ly.split(factor=0.05, align=True)
                ly = ly.split(factor=Color_Bar_Width * VmtData.uiScale, align=True)      # 饼菜单颜色条宽度
            if soldPdsc<0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
            LyVmAddOp(ly, txt)
            if soldPdsc>0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        editorBlid = context.space_data.tree_type
        tup_nodes = dict_vmtTupleMixerMain[editorBlid][VmtData.skType]
        if VmtData.isSpeedPie:
            for ti in tup_nodes:
                if ti!=vmtSep:
                    LyVmAddOp(pie, ti)
        else:
            # 如果执行时列为空, 则只显示一个空的点框. 下面两个列表是为了修复这个问题.
            list_cols = [pie.row(), pie.row(), pie.row() if VmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]
            def LyGetPieCol(inx):
                if list_done[inx]:
                    return list_cols[inx]
                box = list_cols[inx].box()
                col = box.column(align=VmtData.pieAlignment<2)
                col.ui_units_x = 6*((VmtData.pieScale-1)/2+1)
                col.scale_y = VmtData.pieScale
                list_cols[inx] = col
                list_done[inx] = True
                return col
            sk0_type = VmtData.sk0.type
            sk1_type = VmtData.sk1.type if VmtData.sk1 else None
            vec_mat_math = False    # 有矢量和矩阵输入接口的节点
            # 连接了两个接口，且一矩阵一不是矩阵
            # if VmtData.sk1 and ((sk0_type != "MATRIX" and sk1_type == "MATRIX") or (sk0_type == "MATRIX" and sk1_type != "MATRIX")):
            if VmtData.sk1 and (sk0_type == "MATRIX") != (sk1_type == "MATRIX"):
                vec_mat_math = True
            mat_mat_math = True if (sk0_type == "MATRIX" and sk1_type == "MATRIX") else False
            match editorBlid:
                case 'ShaderNodeTree':
                    row2 = LyGetPieCol(0).row(align=VmtData.pieAlignment==0)
                    row2.enabled = False
                    LyVmAddItem(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    col = LyGetPieCol(0)
                    row1 = col.row(align=VmtData.pieAlignment==0)
                    row2 = col.row(align=VmtData.pieAlignment==0)
                    row3 = col.row(align=VmtData.pieAlignment==0)
                    row1.enabled = False
                    row2.enabled = False
                    row3.enabled = False
                    LyVmAddItem(row1, 'GeometryNodeSwitch')
                    if VmtData.skType != "MATRIX":  # 暂时只是让矩阵接口的混合饼菜单不显示 混合和比较节点
                        LyVmAddItem(row2, 'ShaderNodeMix')
                        LyVmAddItem(row3, 'FunctionNodeCompare')
                    # # 混合饼菜单对比较节点的额外支持
                    # row4 = col.row(align=VmtData.pieAlignment==0)
                    # row5 = col.row(align=VmtData.pieAlignment==0)
                    # LyVmAddItem(row4, 'FunctionNodeCompare')
                    # LyVmAddItem(row5, 'FunctionNodeCompare')
            sco = 0
            for ti in tup_nodes:
                match ti:
                    case 'GeometryNodeSwitch':  row1.enabled = True
                    case 'ShaderNodeMix':       row2.enabled = True
                    case 'FunctionNodeCompare': row3.enabled = True
                    case _:
                        col = LyGetPieCol(1)
                        if ti==vmtSep:
                            if sco:
                                col.separator()
                        else:
                            if vec_mat_math and ti in ["FunctionNodeMatrixMultiply", "FunctionNodeMatrixDeterminant", "FunctionNodeInvertMatrix"]:
                                continue
                            if mat_mat_math and ti not in ["FunctionNodeMatrixMultiply"]: continue
                            LyVmAddItem(col, ti)
                            sco += 1
            if VmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=get_sk_color(VmtData.sk0))
                row.label(text=VmtData.sk0.bl_label)