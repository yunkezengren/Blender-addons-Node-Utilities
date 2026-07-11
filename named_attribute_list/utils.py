import bpy, time
from bpy.types import Context, Object, NodeTree, Node
from pprint import pprint
from typing import Union

from .constants import domain_cn_list, domain_lower_list, get_domain_cn, sort_key_l1, sort_key_l2
from .my_dataclass import Attr_Info, Attr_Dict, Group
from .preferences import pref
from .translator import i18n as tr

def get_domain_list():
    view = bpy.context.preferences.view
    trans = view.use_translate_interface
    if view.language in ["zh_CN", "zh_HANS"] and trans:
        return domain_cn_list
    else:
        return domain_lower_list

def find_user_keyconfig(key):
    from . import addon_keymaps
    km, kmi = addon_keymaps[key]
    pprint(addon_keymaps)
    for item in bpy.context.window_manager.keyconfigs.user.keymaps[km.name].keymap_items:
        found_item = False
        if kmi.idname == item.idname:
            found_item = True
            for name in dir(kmi.properties):
                if not name in ["bl_rna", "rna_type"] and not name[0] == "_":
                    if name in kmi.properties and name in item.properties and not kmi.properties[name] == item.properties[name]:
                        found_item = False
        if found_item:
            return item
    print(f"Couldn't find keymap item for {key}, using addon keymap instead. This won't be saved across sessions!")
    return kmi

def add_to_attr_list_mt_editor_menus(self, context: Context):
    if context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree']:
        layout = self.layout
        layout.menu('ATTRLIST_MT_Menu', text=tr('属性'))

def get_proper_obj() -> Object:
    ui_type = bpy.context.area.ui_type
    if ui_type == 'GeometryNodeTree':
        a_object = bpy.context.space_data.id
    if ui_type == 'ShaderNodeTree':
        a_object = bpy.context.object
    deps = bpy.context.view_layer.depsgraph
    return deps.id_eval_get(a_object)

def get_active_gn_tree():
    active_mod = get_proper_obj().modifiers.active
    if active_mod and active_mod.type == 'NODES':
        return active_mod.node_group
    else:
        return False

def is_node_output_used(node: Node):
    soc_out = node.outputs
    for soc in soc_out:
        if soc.is_linked:
            return True
    return False

def loop_find_if_instanced(node: Node):
    links = node.outputs[0].links
    i = 0
    while links:
        i += 1
        if i > 10:
            return False
        to_node = links[0].to_node
        if to_node.bl_idname == "GeometryNodeInstanceOnPoints" and links[0].to_socket.name == 'Points':
            return True
        else:
            if to_node.outputs:
                links = to_node.outputs[0].links
            else:
                return False
    return False

def get_tree_attrs_dict(
    tree: NodeTree,
    attrs_dict: Attr_Dict,
    sub_attrs: Attr_Dict,
    group_node_name: str,
    group_name_parent: str,
    stored_group: list,
    in_group=False,
) -> Attr_Dict:
    nodes = tree.nodes
    for node in nodes:
        if node.mute: continue
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            name_sk = node.inputs["Name"]
            if name_sk.is_linked: continue
            attr_name = name_sk.default_value
            if attr_name == "":
                continue
            domain_cn = tr(get_domain_cn[node.domain])

            _in_group_hide = in_group and pref().hide_attr_in_group and group_node_name != "当前group是顶层节点树"
            _group_display_active = in_group and pref().group_attr_display != 'DEFAULT' and group_node_name != "当前group是顶层节点树"
            _attrs_dict = sub_attrs if _in_group_hide else attrs_dict
            if attr_name not in _attrs_dict:
                attr_info = Attr_Info(data_type=node.data_type,
                                      domain=[node.domain],
                                      domain_info=[domain_cn],
                                      group_name=[tree.name],
                                      group_name_parent=[group_name_parent],
                                      node_name=[node.name],
                                      group_node_name=[group_node_name],
                                      if_instanced=loop_find_if_instanced(node),
                                      attr_group=Group.GROUP if _in_group_hide else None,
                                      is_from_group=_group_display_active,
                                      )
                _attrs_dict[attr_name] = attr_info
            else:
                attr_info = _attrs_dict[attr_name]
                attr_info.domain.append(node.domain)
                attr_info.domain_info.append(domain_cn)
                attr_info.group_name.append(tree.name)
                attr_info.group_name_parent.append(group_name_parent)
                attr_info.group_node_name.append(group_node_name)
                if _group_display_active:
                    attr_info.is_from_group = True
                attr_info.node_name.append(node.name)
        if node.type == "GROUP" and node.node_tree:
            if pref().skip_unevaluated_group and not is_node_output_used(node):
                continue
            group_name = node.node_tree.name
            if group_name in stored_group:  continue
            stored_group.append(group_name)
            temp1 = group_node_name + "/" + node.name
            temp2 = group_name_parent + "/" + tree.name
            get_tree_attrs_dict(node.node_tree, attrs_dict, sub_attrs, stored_group=stored_group,
                                group_node_name=temp1, group_name_parent=temp2, in_group=True)
    return attrs_dict

def get_tree_attrs_list(tree: NodeTree, all_tree_attr: list[str], stored_group) -> list[str]:
    """ 遍历节点得到的属性名称列表,省的被evaluated_obj_attrs里的同名,重存覆盖 """
    nodes = tree.nodes
    show_unused = not pref().hide_unevaluated_attr

    for node in nodes:
        if node.mute: continue
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            if show_unused or is_node_output_used(node):
                name_input = node.inputs["Name"]
                if name_input.is_linked: continue
                attr_name = node.inputs["Name"].default_value
                if attr_name == "":  continue

                if attr_name not in all_tree_attr:
                    all_tree_attr.append(attr_name)
        if node.type == "GROUP" and node.node_tree:
            if pref().skip_unevaluated_group and not is_node_output_used(node):
                continue
            group_name = node.node_tree.name
            if group_name in stored_group:
                continue
            stored_group.append(group_name)
            all_tree_attr = get_tree_attrs_list(node.node_tree, all_tree_attr, stored_group)

    return all_tree_attr

def extend_dict_with_evaluated_obj_attrs(attrs_d: Attr_Dict, exclude_l: list[str], obj: Object, all_tree_attr: list[str], attr_group: str = None):
    exclude_l = exclude_l + [
                    "position", "sharp_face", "material_index",
                    ".edge_verts", ".corner_vert", ".corner_edge",
                    ".select_vert", ".select_edge", ".select_poly",
                    ".uv_select_vert", ".uv_select_edge", ".uv_select_face",
                    ".sculpt_face_set",
                    ".reference_index", "instance_transform",
                    "radius", "curve_type", "cyclic",
                    ]
    deps = bpy.context.view_layer.depsgraph
    obj = deps.id_eval_get(obj)

    all_evaluated_attr: list[str] = []
    if hasattr(obj, "evaluated_geometry"):
        geo = obj.evaluated_geometry()
        components = [geo.instances_pointcloud(), geo.mesh, geo.pointcloud, geo.curves, geo.grease_pencil]
        for i, component in enumerate(components):
            if not component: continue
            for attr in component.attributes:
                domain = attr.domain if i else "INSTANCE"
                name = attr.name
                all_evaluated_attr.append(name)
                if name in exclude_l or name in all_tree_attr: continue
                if not domain: continue
                if name not in attrs_d:
                    attrs_d[name] = Attr_Info(data_type=attr.data_type, domain=[domain],
                                            domain_info=[tr(get_domain_cn[domain])], group_name=[tr("不确定")],
                                            attr_group=attr_group)
                else:
                    info = attrs_d[name]
                    info.domain.append(domain)
                    info.domain_info.append(tr(get_domain_cn[domain]))
                    info.group_name.append(tr("不确定"))
    else:
        attrs = obj.data.attributes
        for attr in attrs:
            name = attr.name
            domain = attr.domain
            if name in exclude_l or name in all_tree_attr: continue
            all_evaluated_attr.append(name)
            attrs_d[name] = Attr_Info(data_type=attr.data_type, domain=[attr.domain],
                                        domain_info=[tr(get_domain_cn[domain])], group_name=tr("不确定"),
                                        attr_group=attr_group)
    return all_evaluated_attr

def extend_dict_with_obj_data_attrs(attrs_d: Attr_Dict, sub_attrs_d: Attr_Dict, all_tree_attr: list[str]):
    exclude_l = []
    a_object = get_proper_obj()
    if a_object.type == "MESH":
        vertex_groups = a_object.vertex_groups
        uv_layers = a_object.data.uv_layers
        color_attrs = a_object.data.color_attributes
        exclude_l = [ _.name for _ in vertex_groups] + [
                    _.name for _ in uv_layers] + [
                    _.name for _ in color_attrs]
    prefs = pref()
    _dict = sub_attrs_d if prefs.hide_extra_attr else attrs_d

    _extra_cat = Group.EXTRA_ATTR if prefs.hide_extra_attr else None
    all_evaluated_attr = extend_dict_with_evaluated_obj_attrs(_dict, exclude_l, a_object, all_tree_attr, attr_group=_extra_cat)
    if a_object.type == "MESH":
        hide_in_sub = prefs.hide_vertex_group
        for attr in vertex_groups:
            if attrs_d.get(attr.name) and not hide_in_sub: continue
            _attrs_d = sub_attrs_d if hide_in_sub else attrs_d
            _attrs_d[attr.name] = Attr_Info(data_type='FLOAT',
                                            domain=["POINT"],
                                            domain_info=[tr('点')],
                                            group_name=tr("物体属性"),
                                            info=tr("顶点组"),
                                            attr_group=Group.VERTEX_GROUP if hide_in_sub else None)
        hide_in_sub = prefs.hide_uv_map
        for attr in uv_layers:
            if attrs_d.get(attr.name) and not hide_in_sub: continue
            _attrs_d = sub_attrs_d if hide_in_sub else attrs_d
            _attrs_d[attr.name] = Attr_Info(data_type='FLOAT2',
                                            domain=["CORNER"],
                                            domain_info=[tr('面拐')],
                                            group_name=tr("物体属性"),
                                            info=tr("UV贴图"),
                                            attr_group=Group.UV_MAP if hide_in_sub else None)
        hide_in_sub = prefs.hide_color_attr
        for attr in color_attrs:
            if attrs_d.get(attr.name) and not hide_in_sub: continue
            _attrs_d = sub_attrs_d if hide_in_sub else attrs_d
            _attrs_d[attr.name] = Attr_Info(data_type=attr.data_type,
                                            domain=[attr.domain],
                                            domain_info=[tr(get_domain_cn[attr.domain])],
                                            group_name=tr("物体属性"),
                                            info=tr("颜色属性"),
                                            attr_group=Group.COLOR_ATTR if hide_in_sub else None)
    return all_evaluated_attr

def move_by_prefix_or_unused(dict1: Attr_Dict, dict2: Attr_Dict, all_evaluated_attr: list):
    """ 把符合条件的从 dict1 积到 dict2, 优先级: 前缀 > 未评估 > 组内 """
    prefix_list = pref().prefix_to_hide.split("|")
    for name in list(dict1):
        has_prefix = False
        if pref().hide_by_prefix:
            for prefix in prefix_list:
                if prefix and name.startswith(prefix):
                    has_prefix = True
                    break
        hide_unuse = (pref().hide_unevaluated_attr and name not in all_evaluated_attr)
        if has_prefix or hide_unuse:
            attr_info = dict1.pop(name)
            if has_prefix:
                attr_info.attr_group = Group.PREFIX
            elif hide_unuse:
                attr_info.attr_group = Group.UNEVALUATED
            dict2[name] = attr_info
    # 未评估优先级高于组内: 把 dict2 中 attr_group==GROUP 且未评估的改为 UNEVALUATED
    if pref().hide_unevaluated_attr:
        for name, attr_info in dict2.items():
            if attr_info.attr_group == Group.GROUP and name not in all_evaluated_attr:
                attr_info.attr_group = Group.UNEVALUATED

def custom_sort_dict(attrs: Attr_Dict, sort_key_l: list[Union[str, list]]) -> Attr_Dict:
    sorted_attrs: Attr_Dict = {}
    for sort_key in sort_key_l:
        _sort_key: set[str] = set(sort_key) if isinstance(sort_key, list) else {sort_key}
        for key in attrs:
            if attrs[key].data_type in _sort_key:
                sorted_attrs[key] = attrs[key]
    return sorted_attrs

def sort_attr_dict(attrs: Attr_Dict) -> Attr_Dict:
    attrs = {k: attrs[k] for k in sorted(attrs)}
    sort_map = {
        '按类型排序1': sort_key_l1,
        '按类型排序2': sort_key_l2,
        '按类型排序1-反转': reversed(sort_key_l1),
        '完全按字符串排序': None,
    }
    if sort_key := sort_map.get(pref().sort_type):
        attrs = custom_sort_dict(attrs, sort_key)
    return attrs

def get_attrs(get_hided=False):
    tree = get_active_gn_tree()
    attrs: Attr_Dict = {}
    all_tree_attr = []
    sub_attrs: Attr_Dict = {}
    if tree:
        attrs = get_tree_attrs_dict(tree, attrs, sub_attrs, stored_group=[], group_node_name="当前group是顶层节点树", group_name_parent="顶层节点树无父级")
        all_tree_attr = get_tree_attrs_list(tree, all_tree_attr=[], stored_group=[])
    all_evaluated_attr = extend_dict_with_obj_data_attrs(attrs, sub_attrs, all_tree_attr)
    move_by_prefix_or_unused(attrs, sub_attrs, all_evaluated_attr)
    attrs = sub_attrs if get_hided else attrs
    return sort_attr_dict(attrs)

def get_hided_attrs_by_group(group: Group) -> Attr_Dict:
    """获取指定组的隐藏属性"""
    attrs = get_attrs(get_hided=True)
    return {k: v for k, v in attrs.items() if v.attr_group == group}

def exit_group_to_root():
    space = bpy.context.space_data
    tree_path = space.path.to_string.split("/")[1:]
    for i in range(len(tree_path)):
        space.path.pop()

def proper_scroll_view():
    if pref().if_scale_editor: # type: ignore
        for i in range(50):
            bpy.ops.view2d.zoom_out()
        for i in range(40):
            bpy.ops.view2d.zoom_in()

def exist_node_tree(context: Context):
    ui_type = context.area.ui_type
    edit_tree = context.space_data.edit_tree
    if ui_type == "GeometryNodeTree" and edit_tree:
        return True
    if ui_type == "ShaderNodeTree" and edit_tree:
        a_obj = context.active_object
        if a_obj and a_obj.type in {'MESH','CURVE','SURFACE','FONT','META','GPENCIL','VOLUME','CURVES','POINTCLOUD'}:
            return True
    return False
