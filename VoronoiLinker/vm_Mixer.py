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
from .v_tool import VoronoiOpTool
from .common_forward_class import VmtData
from .utils_node import DoLinkHh
from .utils_color import get_sk_color
from bpy.app.translations import pgettext_iface as TranslateIface

from bpy.types import NodeTree, Node, GeometryNodeMenuSwitch, GeometryNodeIndexSwitch, ShaderNodeCombineXYZ, FunctionNodeCompare

def DoMix(tree: NodeTree, isShift: bool, isAlt: bool, type: str):
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=type, use_transform=not VmtData.isPlaceImmediately)
    a_node = tree.nodes.active
    # a_node: Node | GeometryNodeMenuSwitch = tree.nodes.active
    a_node.width = 140
    fix_type = {'VALUE':'FLOAT'}.get(VmtData.skType, VmtData.skType)
    # 两次 switch case -- 为了代码舒适和一点点节约.
    match a_node.bl_idname:
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath':
            a_node.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            a_node.operation = 'OR'
        case 'TextureNodeTexture':
            a_node.show_preview = False
        case 'GeometryNodeSwitch':
            a_node.input_type = fix_type
        case 'GeometryNodeIndexSwitch' :
            a_node.data_type = fix_type
        case 'GeometryNodeMenuSwitch':
            a_node.data_type = fix_type
        case 'FunctionNodeCompare':
            a_node.data_type = {'BOOLEAN':'INT'}.get(fix_type, fix_type)
            a_node.operation = 'EQUAL'
        case 'ShaderNodeMix':
            a_node.data_type = {'INT':'FLOAT', 'BOOLEAN':'FLOAT'}.get(fix_type, fix_type)
    match a_node.bl_idname:
        case 'GeometryNodeIndexSwitch'|'GeometryNodeMenuSwitch'|"ShaderNodeCombineXYZ": 
            sks = [sk for sk in (VmtData.sk0, VmtData.sk1, VmtData.sk2) if sk]
            if VmtData.sk2:
                if isinstance(a_node, GeometryNodeMenuSwitch):
                    a_node.enum_items.new(VmtData.sk2.name)
                if isinstance(a_node, GeometryNodeIndexSwitch):
                    a_node.index_switch_items.new()
            sk_index_offset = not isinstance(a_node, ShaderNodeCombineXYZ)      # 编号/菜单切换的接口从第二个开始连
            for i, sk in enumerate(sks):
                if isinstance(a_node, GeometryNodeMenuSwitch):
                    a_node.enum_items[i].name = sk.name
                NewLinkHhAndRemember(sk, a_node.inputs[i+sk_index_offset])
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|2|.
            fix_type = VmtData.skType
            match a_node.bl_idname:
                case 'FunctionNodeCompare': fix_type = {'BOOLEAN':'INT'}.get(fix_type, fix_type)
                case 'ShaderNodeMix':       fix_type = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(fix_type, fix_type)
            tgl = isinstance(a_node, bpy.types.ShaderNodeMix) and a_node.data_type in {"FLOAT", "VECTOR"}
            list_foundSk = [sk for sk in a_node.inputs if sk.type==fix_type][tgl:]    # mix三个浮点/矢量输入,第一个是非均匀模式的矢量Factor
            for i, sk in enumerate(sk for sk in (VmtData.sk0, VmtData.sk1) if sk):
                NewLinkHhAndRemember(sk, list_foundSk[i^isShift])
        case _:
            # 这种密集的处理是为了多输入 -- 需要改变连接顺序.
            Mix_item = dict_vmtMixerNodesDefs[a_node.bl_idname]
            swap_link = 0       # sk0是矩阵,sk1是矢量,不交换(这是默认情况)
            if VmtData.sk1 and VmtData.sk1.type == "MATRIX" and VmtData.sk0.type != "MATRIX":
                swap_link = 1
            soc_in = a_node.inputs[Mix_item[1^isShift^swap_link]]
            is_multi_in = a_node.inputs[Mix_item[0]].is_multi_input
            if (VmtData.sk1)and(is_multi_in): # `0` 在这里主要是因为 dict_vmtMixerNodesDefs 中的“多输入节点”都是零.
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
            DoLinkHh( VmtData.sk0, a_node.inputs[Mix_item[0^isShift]^swap_link] ) # 注意: 这不是 NewLinkHhAndRemember(), 以便多输入的第二个视觉上是 VlrtData 中的最后一个.
            if (VmtData.sk1)and(not is_multi_in):
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
    a_node.show_options = not VmtData.isHideOptions
    # 接下来和 vqmt 中一样. 它的是主要的; 这里为了直观对应而复制.
    if isAlt:
        for sk in a_node.inputs:
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
            list_cols: list[UILayout] = [pie.row(), pie.row(), pie.row() if VmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]
            def LyGetPieCol(inx: int):
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
            vec_and_mat = False    # 有矢量和矩阵输入接口的节点
            # 连接了两个接口，且一个是矩阵一不是矩阵
            # if VmtData.sk1 and ((sk0_type != "MATRIX" and sk1_type == "MATRIX") or (sk0_type == "MATRIX" and sk1_type != "MATRIX")):
            if VmtData.sk1 and (sk0_type == "MATRIX") != (sk1_type == "MATRIX"):
                vec_and_mat = True
            mat_and_mat = True if (sk0_type == "MATRIX" and sk1_type == "MATRIX") else False
            match editorBlid:
                # 这是 mix pie 的右半
                # case 'ShaderNodeTree':
                case 'ShaderNodeTree' | 'CompositorNodeTree':
                    row2 = LyGetPieCol(0).row(align=VmtData.pieAlignment==0)
                    row2.enabled = True
                    LyVmAddItem(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    column0 = LyGetPieCol(0)
                    # 这三个是几何节点全部接口类型都支持
                    for idname in support_all_type:
                        row123 = column0.row(align=VmtData.pieAlignment==0)
                        LyVmAddItem(row123, idname)
                        
                    # row1 = column0.row(align=VmtData.pieAlignment==0)
                    # row2 = column0.row(align=VmtData.pieAlignment==0)
                    # row3 = column0.row(align=VmtData.pieAlignment==0)
                    # row1.enabled = False
                    # row2.enabled = False
                    # row3.enabled = False
                    # LyVmAddItem(row1, 'GeometryNodeSwitch')
                    # LyVmAddItem(row2, 'GeometryNodeIndexSwitch')
                    # LyVmAddItem(row3, 'GeometryNodeMenuSwitch')
                    
                    row4 = column0.row(align=VmtData.pieAlignment==0)
                    row5 = column0.row(align=VmtData.pieAlignment==0)
                    row4.enabled = False
                    row5.enabled = False
                    if VmtData.skType != "MATRIX":  # 暂时只是让矩阵接口的混合饼菜单不显示 混合和比较节点
                        LyVmAddItem(row4, 'ShaderNodeMix')
                        LyVmAddItem(row5, 'FunctionNodeCompare')
                    # # todo 混合饼菜单对比较节点的额外支持
                    # row4 = col.row(align=VmtData.pieAlignment==0)
                    # row5 = col.row(align=VmtData.pieAlignment==0)
                    # LyVmAddItem(row4, 'FunctionNodeCompare')
                    # LyVmAddItem(row5, 'FunctionNodeCompare')
            sco = 0
            
            for ti in tup_nodes:
                if ti in support_all_type: continue
                match ti:
                    # case 'GeometryNodeSwitch'      : row1.enabled = True
                    # case 'GeometryNodeIndexSwitch' : row2.enabled = True
                    # case 'GeometryNodeMenuSwitch'  : row3.enabled = True
                    case 'ShaderNodeMix'           : 
                        try:        # todo 改进这里的逻辑,因为mix节点三个节点树都有
                            row4.enabled = True
                        except:
                            pass
                    case 'FunctionNodeCompare'     : row5.enabled = True
                    # 上面五个是画在左边的,多种接口通用节点
                    # todo 既然通用,全局变量里提取出来
                    case _:
                        # 下面是 mix pie 的右半
                        column1 = LyGetPieCol(1)
                        if ti==vmtSep:
                            if sco:
                                column1.separator()
                        else:
                            if vec_and_mat and ti in ["FunctionNodeMatrixMultiply", "FunctionNodeMatrixDeterminant", "FunctionNodeInvertMatrix", "FunctionNodeCombineTransform", "FunctionNodeCombineMatrix"]:
                                continue
                            if mat_and_mat and ti not in ["FunctionNodeMatrixMultiply"]: continue
                            LyVmAddItem(column1, ti)
                            sco += 1
            if VmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=get_sk_color(VmtData.sk0))
                row.label(text=VmtData.sk0.bl_label)