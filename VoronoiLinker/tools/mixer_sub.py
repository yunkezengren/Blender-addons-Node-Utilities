import bpy
from bpy.app.translations import pgettext_iface as _iface
from bpy.types import Menu, UILayout, FunctionNodeCompare, GeometryNodeIndexSwitch, GeometryNodeMenuSwitch, NodeTree, ShaderNodeCombineXYZ
from ..base_tool import BaseOperator
from ..common_class import VmtData
from ..globals import Color_Bar_Width, SEPARATE, dict_vmtMixerNodesDefs, mixer_default, mixer_tree_sk_nodes, node_support_all_gn_sk
from ..utils.color import get_sk_color
from ..utils.node import link_new_pro, remember_add_link, vlrt_remember_last_sockets

def _set_mix_factor(node, fac=0.5):
    # ShaderNodeMix 的 Factor_Float 在 Blender 5.x 默认是 1, Mixer 要 0.5.
    for sk in node.inputs:
        ident = getattr(sk, 'identifier', '') or ''
        name = sk.name or ''
        if ident in {'Factor_Float', 'Fac'} or (sk.type == 'VALUE' and name in {'Factor', 'Fac'}):
            try:
                sk.default_value = fac
            except Exception:
                pass
        elif ident == 'Factor_Vector' or (sk.type == 'VECTOR' and name == 'Factor'):
            try:
                sk.default_value = (fac, fac, fac)
            except Exception:
                pass

def _already_linked(sk_from, sk_to) -> bool:
    if not (sk_from and sk_to):
        return False
    try:
        return any(lk.to_socket == sk_to for lk in sk_from.links)
    except ReferenceError:
        return False

def _snapshot_outgoing_dests(*socks) -> list[tuple[str, str]]:
    dests: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for sk in socks:
        if not sk:
            continue
        try:
            for lk in sk.links:
                key = (lk.to_node.name, lk.to_socket.identifier)
                if key in seen:
                    continue
                seen.add(key)
                dests.append(key)
        except (ReferenceError, AttributeError):
            continue
    return dests

def _find_socket_by_identifier(node, identifier: str):
    for sk in node.inputs:
        if sk.identifier == identifier:
            return sk
    return None

def _transform_running() -> bool:
    try:
        win = bpy.context.window
        if not win:
            return False
        for op in win.modal_operators:
            name = (getattr(op, 'bl_idname', '') or '').lower()
            if any(tok in name for tok in ('translate', 'transform', 'attach')):
                return True
        return False
    except Exception:
        return False

def _apply_multi_input_mixer_links(tree: NodeTree, a_node, isShift: bool, isAlt: bool, dests: list[tuple[str, str]], sk0=None, sk1=None, sk2=None):
    Mix_item = dict_vmtMixerNodesDefs[a_node.bl_idname]
    swap_link = 0
    if sk1 and sk1.type == "MATRIX" and sk0 and sk0.type != "MATRIX":
        swap_link = 1
    soc_in = a_node.inputs[Mix_item[1^isShift^swap_link]]
    is_multi_in = a_node.inputs[Mix_item[0]].is_multi_input
    sk0_in = a_node.inputs[Mix_item[0^isShift]^swap_link]
    if sk1 and is_multi_in and not _already_linked(sk1, soc_in):
        remember_add_link(sk1, soc_in)
    if sk0:
        if not _already_linked(sk0, sk0_in):
            link_new_pro(sk0, sk0_in)
        else:
            vlrt_remember_last_sockets(sk0, sk0_in)
    if sk1 and not is_multi_in and not _already_linked(sk1, soc_in):
        remember_add_link(sk1, soc_in)

    out_sk = next((sk for sk in a_node.outputs if sk.enabled), None)
    sources = [sk for sk in (sk0, sk1, sk2) if sk]
    if out_sk:
        for node_name, sock_id in dests:
            dest_node = tree.nodes.get(node_name)
            if not dest_node or dest_node == a_node:
                continue
            dest = _find_socket_by_identifier(dest_node, sock_id)
            if not dest:
                continue
            if _already_linked(out_sk, dest):
                continue
            if any(_already_linked(src, dest) for src in sources):
                continue
            try:
                link_new_pro(out_sk, dest)
            except Exception:
                pass
    if isAlt:
        for sk in a_node.inputs:
            sk.hide = True

def _schedule_multi_input_mixer_finish(tree: NodeTree, node_name: str, isShift: bool, isAlt: bool, dests: list[tuple[str, str]], sk0=None, sk1=None, sk2=None):
    state = {
        'tree': tree,
        'node_name': node_name,
        'isShift': isShift,
        'isAlt': isAlt,
        'dests': dests,
        'sk0': sk0,
        'sk1': sk1,
        'sk2': sk2,
        'saw': False,
        'idle': 0,
    }

    def poll():
        try:
            node = state['tree'].nodes.get(state['node_name'])
        except ReferenceError:
            return None
        if not node:
            return None
        if _transform_running():
            state['saw'] = True
            return 0.04
        if not state['saw']:
            state['idle'] += 1
            # transform 有时会晚几帧才进 modal_operators; 连线已在拖动前接上.
            if state['idle'] < 25:
                return 0.04
            return None
        _apply_multi_input_mixer_links(
            state['tree'], node, state['isShift'], state['isAlt'], state['dests'],
            state['sk0'], state['sk1'], state['sk2'])
        return None

    bpy.app.timers.register(poll, first_interval=0.02)

def DoMix(tree: NodeTree, isShift: bool, isAlt: bool, type: str):
    dests = _snapshot_outgoing_dests(VmtData.sk0, VmtData.sk1, VmtData.sk2)
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
            _set_mix_factor(a_node, 0.5)
    delay_multi = False
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
            is_multi_in = a_node.inputs[Mix_item[0]].is_multi_input
            # Join Geometry / String Join 等多输入: 拖动时先连上, 这样能看到 noodles.
            # insert-on-link 放下时会清掉多输入上已有的外部连线, 只留被插入的那根;
            # 所以 transform 结束后再补一次 Mixer 输入和下游.
            _apply_multi_input_mixer_links(tree, a_node, isShift, isAlt, dests, VmtData.sk0, VmtData.sk1, VmtData.sk2)
            if is_multi_in and not VmtData.isPlaceImmediately:
                delay_multi = True
    if a_node.bl_idname in {'ShaderNodeMix', 'ShaderNodeMixRGB', 'TextureNodeMixRGB', 'ShaderNodeMixShader'}:
        _set_mix_factor(a_node, 0.5)
    a_node.show_options = not VmtData.isHideOptions
    if delay_multi:
        _schedule_multi_input_mixer_finish(
            tree, a_node.name, isShift, isAlt, dests, VmtData.sk0, VmtData.sk1, VmtData.sk2)
        return
    # 接下来和 vqmt 中一样. 它的是主要的; 这里为了直观对应而复制.
    if isAlt:
        for sk in a_node.inputs:
            sk.hide = True

class NODE_OT_mixer_sub(BaseOperator):
    bl_idname = 'node.mixer_sub'
    bl_label = "Mixer Sub-operator"
    operation: bpy.props.StringProperty()
    def invoke(self, context, event):
        DoMix(context.space_data.edit_tree, event.shift, event.alt, self.operation)
        return {'FINISHED'}

class NODE_MT_mixer_pie(Menu):
    bl_idname = 'NODE_MT_mixer_pie'
    bl_label = "" # 这里的文本将显示在饼菜单的中心.
    def draw(self, context):
        def LyVmAddOp(where: UILayout, txt):
            where.operator(NODE_OT_mixer_sub.bl_idname, text=_iface(dict_vmtMixerNodesDefs[txt][2])).operation = txt
        def LyVmAddItem(where: UILayout, txt):
            ly = where.row(align=_align)
            soldPdsc = VmtData.pieDisplaySocketColor
            if soldPdsc:
                ly = ly.split(factor=Color_Bar_Width * VmtData.ui_scale, align=True)      # 饼菜单颜色条宽度
            if soldPdsc<0:
                ly.prop(VmtData.prefs, 'sk_hint_color', text="")
            LyVmAddOp(ly, txt)
            if soldPdsc>0:
                ly.prop(VmtData.prefs, 'sk_hint_color', text="")
        pie = self.layout.menu_pie()
        tree_idname = context.space_data.tree_type

        default_nodes = mixer_default.get(tree_idname, None)
        tup_nodes = mixer_tree_sk_nodes[tree_idname].get(VmtData.skType, default_nodes)
        if VmtData.isSpeedPie:
            for ti in tup_nodes:
                if ti != SEPARATE and hasattr(bpy.types, ti):
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
                if not hasattr(bpy.types, idname):
                    continue
                row123 = col_left.row(align=_align)
                LyVmAddItem(row123, idname)

            sco = 0
            last_ti = None
            for ti in tup_nodes:
                if ti in node_support_all_gn_sk: continue
                if ti != SEPARATE and not hasattr(bpy.types, ti):
                    continue
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
