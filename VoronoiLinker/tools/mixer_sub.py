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
from ..base_tool import VoronoiOpTool
from ..common_forward_class import VmtData
from ..utils.node import DoLinkHh
from ..utils.color import get_sk_color
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
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'ShaderNodeMath'|'TextureNodeMath':
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
                remember_add_link(sk, a_node.inputs[i+sk_index_offset])
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|2|.
            fix_type = VmtData.skType
            match a_node.bl_idname:
                case 'FunctionNodeCompare': fix_type = {'BOOLEAN':'INT'}.get(fix_type, fix_type)
                case 'ShaderNodeMix':       fix_type = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(fix_type, fix_type)
            tgl = isinstance(a_node, bpy.types.ShaderNodeMix) and a_node.data_type in {"FLOAT", "VECTOR"}
            list_foundSk = [sk for sk in a_node.inputs if sk.type==fix_type][tgl:]    # mix三个浮点/矢量输入,第一个是非均匀模式的矢量Factor
            for i, sk in enumerate(sk for sk in (VmtData.sk0, VmtData.sk1) if sk):
                remember_add_link(sk, list_foundSk[i^isShift])
        case _:
            # 这种密集的处理是为了多输入 -- 需要改变连接顺序.
            Mix_item = dict_vmtMixerNodesDefs[a_node.bl_idname]
            swap_link = 0       # sk0是矩阵,sk1是矢量,不交换(这是默认情况)
            if VmtData.sk1 and VmtData.sk1.type == "MATRIX" and VmtData.sk0.type != "MATRIX":
                swap_link = 1
            soc_in = a_node.inputs[Mix_item[1^isShift^swap_link]]
            is_multi_in = a_node.inputs[Mix_item[0]].is_multi_input
            if (VmtData.sk1)and(is_multi_in): # `0` 在这里主要是因为 dict_vmtMixerNodesDefs 中的“多输入节点”都是零.
                remember_add_link( VmtData.sk1, soc_in)
            DoLinkHh( VmtData.sk0, a_node.inputs[Mix_item[0^isShift]^swap_link] ) # 注意: 这不是 remember_add_link(), 以便多输入的第二个视觉上是 VlrtData 中的最后一个.
            if (VmtData.sk1)and(not is_multi_in):
                remember_add_link( VmtData.sk1, soc_in)
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
            ly = where.row(align=_align)
            soldPdsc = VmtData.pieDisplaySocketColor
            if soldPdsc:
                ly = ly.split(factor=Color_Bar_Width * VmtData.uiScale, align=True)      # 饼菜单颜色条宽度
            if soldPdsc<0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
            LyVmAddOp(ly, txt)
            if soldPdsc>0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        tree_idname = context.space_data.tree_type

        default_nodes = mixer_default.get(tree_idname, None)
        tup_nodes = mixer_tree_sk_nodes[tree_idname].get(VmtData.skType, default_nodes)
        if VmtData.isSpeedPie:
            for ti in tup_nodes:
                if ti != SEPARATE:
                    LyVmAddOp(pie, ti)
        else:
            # 如果执行时列为空, 则只显示一个空的点框. 下面两个列表是为了修复这个问题.
            list_cols: list[UILayout] = [pie.row(), pie.row(), pie.row() if VmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]

            def LyGetPieCol(inx: int):
                if list_done[inx]:
                    return list_cols[inx]
                box = list_cols[inx].box()
                col = box.column(align=VmtData.pieAlignment < 2)
                col.ui_units_x = 6 * ((VmtData.pieScale - 1) / 2 + 1)
                col.scale_y = VmtData.pieScale
                list_cols[inx] = col
                list_done[inx] = True
                return col
            col_left = LyGetPieCol(0)
            col_right = LyGetPieCol(1)
            _align = VmtData.pieAlignment == 0

            for idname in default_nodes:
                row123 = col_left.row(align=_align)
                LyVmAddItem(row123, idname)

            sco = 0
            last_ti = None
            for ti in tup_nodes:
                if ti in node_support_all_gn_sk: continue
                match ti:
                    case 'ShaderNodeMix'           :
                        # todo 改进这里的逻辑,虽然mix节点三个节点树都有，但为了画在左半
                        row4 = col_left.row(align=_align)
                        LyVmAddItem(row4, 'ShaderNodeMix')
                    case 'FunctionNodeCompare'     :
                        # todo 比较节点的额外支持: 显示多种比较模式
                        row5 = col_left.row(align=_align)
                        LyVmAddItem(row5, 'FunctionNodeCompare')
                    case _:
                        if ti == SEPARATE:
                            if last_ti == SEPARATE:
                                continue
                            if sco:
                                col_right.separator()
                        else:
                            sk0_type = VmtData.sk0.type
                            sk1_type = VmtData.sk1.type if VmtData.sk1 else None
                            # 混合 选的 两个 接口类型
                            types_set = {sk0_type, sk1_type}
                            vec_and_mat = (types_set == {"VECTOR", "MATRIX"})
                            rot_and_mat = (types_set == {"ROTATION", "MATRIX"})
                            mat_and_mat = (sk0_type == sk1_type == "MATRIX")
                            if vec_and_mat and ti not in ["FunctionNodeTransformPoint", "FunctionNodeTransformDirection", "FunctionNodeProjectPoint"]:
                                continue
                            if (mat_and_mat or rot_and_mat) and ti not in ["FunctionNodeMatrixMultiply"]:
                                continue
                            
                            LyVmAddItem(col_right, ti)
                            sco += 1
                        last_ti = ti
            if VmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=get_sk_color(VmtData.sk0))
                row.label(text=VmtData.sk0.bl_label)
