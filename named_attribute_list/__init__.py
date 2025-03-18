import os
import bpy
import bpy.utils.previews
from bpy.types import Operator, Menu, Panel, AddonPreferences
from bpy.props import StringProperty, EnumProperty, BoolProperty
from . import translator
from pprint import pprint

tr = translator.i18n

bl_info = {
    "name" : "几何节点命名属性列表",
    "author" : "一尘不染",
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (2, 5, 10),
    "location" : "",
    "warning" : "",
    "doc_url": "",
    "tracker_url": "",
    "category" : "Node"
}

# todo 重命名属性标签和接口
# todo 添加个重命名属性名: 更改 存储属性和命名属性的 名称接口值
#_ todo 快速添加组输入节点
#_ todo 隐藏未使用属性效果不好,不要把顶点组 uv也隐藏啊
# todo 属性列表多种排序方式
# todo 隐藏存在接口改成-隐藏不常用输出接口
# todo 隐藏名称接口里+描述,着色器里反而是隐藏选项

addon_keymaps = {}
_icons = None

domain_en_list = [ 'POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE',  'INSTANCE', 'LAYER' ]
domain_lower_list = ["Point", "Edge", "Face", "Corner", "Curve", "Instance", "Layer"]
domain_cn_list = [ '点',    '边',   '面',   '面拐',   '样条线', '实例',     '层'    ]
# 先从英文大写翻译成中文,再根据语言决定是否翻译成英文小写
get_domain_cn = {k: v for k, v in zip(domain_en_list, domain_cn_list)}

data_types =        ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'FLOAT4X4']
shader_date_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
switch_dict = {
                "BYTE_COLOR": "FLOAT_COLOR",
                "FLOAT2": "FLOAT_VECTOR",
                "INT8": "INT",
                # "FLOAT4X4": "MATRIX"
                }

sort_key_list1 = [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'FLOAT4X4']
sort_key_list2 = [ 'INT', 'BOOLEAN', 'FLOAT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'FLOAT4X4']

png_list = [ '域-布尔.png', '域-浮点.png', '域-整数.png', '域-矢量.png', '域-颜色.png', '域-旋转.png', '域-矩阵.png' ]
data_with_png = {k: v for k, v in zip(data_types, png_list)}

def pref():
    return bpy.context.preferences.addons[__package__].preferences

def get_domain_list():
    view = bpy.context.preferences.view
    trans = view.use_translate_interface

    if view.language in ["zh_CN", "zh_HANS"] and trans:
        return domain_cn_list
    else:
        return domain_lower_list

def find_user_keyconfig(key):
    km, kmi = addon_keymaps[key]
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

def add_to_attr_list_mt_editor_menus(self, context):
    if context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree']:
        layout = self.layout
        layout.menu('ATTRLIST_MT_Menu', text=tr('属性'))

class ATTRLIST_AddonPrefs(AddonPreferences):
    bl_idname = __package__
    hide_option        : BoolProperty(name='hide_option'       , description=tr('添加时是否隐藏选项'),           default=True)
    hide_Exists_socket : BoolProperty(name='hide_Exists_socket', description=tr('添加时是否隐藏输出存在接口'),   default=True)
    hide_Name_socket   : BoolProperty(name='hide_Name_socket'  , description=tr('添加时是否隐藏输入名称接口'),   default=False)
    rename_Attr_socket : BoolProperty(name='rename_Attr_socket', description=tr('添加时是否重命名输出属性接口'), default=True)
    hide_Node          : BoolProperty(name='hide_Node'         , description=tr('添加时是否折叠节点'),           default=False)
    rename_Node        : BoolProperty(name='rename_Node'       , description=tr('添加时是否重命名节点为属性名'), default=False)
    is_hide_by_pre     : BoolProperty(name='is_hide_by_pre'    , description=tr('是否隐藏带有特定前缀的属性'),   default=False)
    show_set_panel     : BoolProperty(name='show_set_panel'    , description=tr('显示设置'),                     default=True)
    if_scale_editor    : BoolProperty(name='if_scale_editor'   , description=tr('查找节点时适当缩放视图'),       default=True)
    show_vertex_group  : BoolProperty(name='Show_Vertex_Group' , description=tr('是否在属性列表里显示顶点组'),   default=True)
    show_uv_map        : BoolProperty(name='Show_UV_Map',        description=tr('是否在属性列表里显示UV贴图'),   default=True)
    show_color_attr    : BoolProperty(name='Show_Color_Attr',    description=tr('是否在属性列表里显示颜色属性'), default=True)
    hide_unused_attr   : BoolProperty(name='hide_unused_attr',   description=tr('只显示输出接口连线的存储属性节点或节点组内的属性'), default=False)
    hide_attr_in_group : BoolProperty(name='hide_attr_in_group', description=tr('隐藏节点组里的属性'), default=False)
    hide_extra_attr    : BoolProperty(name='extraEvaluatedAttr', description=tr('隐藏额外的属性:\n--属性编辑器-数据-属性\n--物体/集合信息节点带的(和别的几何数据合并几何才显示顶点组)\n--存储属性节点名称接口连了线的\n--活动修改器之上的GN修改器的属性'), default=False)
    add_settings       : BoolProperty(name=tr('添加节点选项'),   description=tr('添加节点选项'),       default=False)
    show_settings      : BoolProperty(name=tr('列表显示选项'),   description=tr('列表显示选项'),       default=True)
    show_attr_domain   : BoolProperty(name='show_attr_domain',   description=tr('是否显示属性所在域'), default=True)
    use_accelerator_key: BoolProperty(name='use_accelerator_key',description=tr('使用加速键'), default=True)
    panel_info         : StringProperty(name='panel_info',    description=tr('显示在n面板上的插件当前状态描述'), default="")
    rename_prefix      : StringProperty(name='rename_prefix', description=tr('重命名节点时添加的前缀'), default="")
    hide_prefix        : StringProperty(name='hide_prefix',   description=tr('隐藏带有特定前缀的属性,以|分隔多种,例 .|_|-'), default=".")
    sort_list          : EnumProperty(name='列表排序方式',    description=tr('属性列表多种排序方式'),
                                        items=[ ('按类型排序1',      tr('按类型排序1'),      tr('布尔-浮点-整数-矢量-颜色-旋转-矩阵'), 0, 0),
                                                ('按类型排序1-反转', tr('按类型排序1-反转'), tr('矩阵-旋转-颜色-矢量-整数-浮点-布尔'), 0, 1),
                                                ('按类型排序2',      tr('按类型排序2'),      tr('整数-布尔-浮点-矢量-颜色-旋转-矩阵'), 0, 2),
                                                ('完全按字符串排序', tr('完全按字符串排序'), tr('首字-数字英文中文'), 0, 3)])

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.5)

        split.label(text=tr('命名属性菜单快捷键: '))
        split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text=tr('命名属性面板快捷键: '))
        split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text=tr('添加活动存储属性节点对应属性节点: '))
        split.prop(find_user_keyconfig('添加存储节点对应属性节点'), 'type', text='', full_event=True)

        box1 = layout.box()
        box1.label(text=tr("已知限制: "), icon='INFO')
        limit1 = " "*10 + tr("非网格域存储属性节点,名称接口由别的接口连接的话,可能识别不到")
        limit2 = " "*10 + tr("存储属性节点后经过了实例化或实现实例,在着色器添加属性,选项不一定正确")
        limit3 = " "*10 + tr("对于存了多次的属性,查找节点目前只能定位到其中之一")
        box1.label(text=limit1)
        box1.label(text=limit2)
        box1.label(text=limit3)

def get_active_gn_tree(context, ui_type):
    if ui_type == 'GeometryNodeTree':
        # for pinned node tree
        obj = context.space_data.id
    if ui_type == 'ShaderNodeTree':
        obj = context.active_object
    active = obj.modifiers.active
    if active and active.type == 'NODES':
        return active.node_group
    else:
        return False

def is_node_linked(node):
    soc_out = node.outputs
    if len(soc_out):
        for soc in soc_out:
            if soc.is_linked:
                return True
    return False

def loop_find_if_instanced(node):
    links = node.outputs[0].links
    i = 0
    while links:    # 这里links可能是空,就直接跳出循环了,最后补个 return False
        i += 1
        if i > 5:
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

# attrs_dict = {}      # 放在这里的话，只初始化一次，属性越存越多
def get_tree_attrs_dict(tree, attrs_dict, group_node_name, group_name_parent, stored_group):
    # show_unused=False的话，接下来判断is_node_linked
    nodes = tree.nodes
    # attrs_dict = {}  # 放在这里的话，偶尔出问题  {'Attribute': {'data_type': 'FLOAT_COLOR', 'domain_info': 'CORNER'}, 'Colorxx': {'data_type': 'FLOAT_COLOR', 'domain_info': 'POINT'} }
    show_unused = not pref().hide_unused_attr

    for node in nodes:
        if node.mute: continue
        # show_unused 为True 就不判断is_node_linked,否则判断是否被使用
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute' and (show_unused or is_node_linked(node)):
            # node.outputs['Geometry'].links[0].to_node
            data_type = node.data_type
            if data_type in switch_dict:
                data_type = switch_dict[data_type]
            name_soc = node.inputs["Name"]
            if name_soc.is_linked: continue
            attr_name = name_soc.default_value
            if attr_name == "":
                continue
            domain_cn = tr(get_domain_cn[node.domain])               # 还可以这样

            # print("-" * 60)
            # print(f"{attr_name = }")
            # print(f"{tree.name = }")
            # print(f"{group_name_parent = }")
            if attr_name not in attrs_dict:                      # 没有存过这个属性名
                attr_info = {"data_type": data_type, "domain_info": [domain_cn],
                                "group_name": [tree.name], "group_name_parent": [group_name_parent],
                                "node_name": [node.name],
                                "group_node_name": [group_node_name],
                                "if_instanced": loop_find_if_instanced(node),
                                }
                attrs_dict[attr_name] = attr_info
            else:                                                # 已经存过这个属性名
                dict_item = attrs_dict[attr_name]
                dict_item["domain_info"].append(domain_cn)
                dict_item["group_name"].append(tree.name)
                dict_item["group_name_parent"].append(group_name_parent)
                dict_item["group_node_name"].append(group_node_name)
                dict_item["node_name"].append(node.name)
        is_pass = not pref().hide_attr_in_group
        if node.type == "GROUP" and node.node_tree and is_pass:         # node.node_tree 以防止丢失数据的节点组
            group_name = node.node_tree.name
            if group_name in stored_group:  continue
            stored_group.append(group_name)
            if show_unused or is_node_linked(node):
                # group_name_parent = "组内"  # 这样不行，nodes for循环时，虽然不是节点组，但是group_name_parent也变了
                temp1 = group_node_name + "/" + node.name
                temp2 = group_name_parent + "/" + tree.name
                attrs_dict.update(get_tree_attrs_dict(node.node_tree, attrs_dict, stored_group=stored_group,
                                                      group_node_name=temp1, group_name_parent=temp2))
    return attrs_dict

# 遍历节点得到的属性名称列表,省的被evaluated_obj_attrs里的同名,重存覆盖
def get_tree_attrs_list(tree, all_tree_attr_list, stored_group):
    nodes = tree.nodes
    show_unused = not pref().hide_unused_attr

    for node in nodes:
        if node.mute:   continue
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            if show_unused or is_node_linked(node):
                attr_name = node.inputs["Name"].default_value
                if attr_name == "":  continue

                if attr_name not in all_tree_attr_list:                      # 没有存过这个属性名
                    all_tree_attr_list.append(attr_name)
        if node.type == "GROUP" and node.node_tree:
            group_name = node.node_tree.name
            if group_name in stored_group:
                continue
            stored_group.append(group_name)
            if show_unused or is_node_linked(node):
                # all_tree_attr_list.extend(get_all_tree_attrs_list(node.node_tree, all_tree_attr_list))    # 这样问题很严重,会指数级加项
                all_tree_attr_list = get_tree_attrs_list(node.node_tree, all_tree_attr_list, stored_group)

    return all_tree_attr_list

def extend_dict_with_evaluated_obj_attrs(attrs_dict, exclude_list, obj, all_tree_attr_list):
    box = bpy.context.evaluated_depsgraph_get()
    obj = obj.evaluated_get(box)
    attrs = obj.data.attributes
    exclude_list = exclude_list + [
                    "position", "sharp_face", "material_index",              # "id",
                    ".edge_verts", ".corner_vert", ".corner_edge",
                    ".select_vert", ".select_edge", ".select_poly",
                    ".sculpt_face_set",
                    ]
    for attr in attrs:
        if attr.name in exclude_list:
            continue
        data_type = attr.data_type
        if data_type in switch_dict:
            data_type = switch_dict[data_type]
        if attr.name not in all_tree_attr_list:             # 用节点名称接口连了线的属性(第一种方法获取不到)
            domain_info = "" + tr(get_domain_cn[attr.domain])
            attrs_dict[attr.name] = {"data_type": data_type, "domain_info": [domain_info], "group_name": tr("不确定")}

def extend_dict_with_obj_data_attrs(attrs, all_tree_attr_list):
    ui_type = bpy.context.area.ui_type
    if ui_type == 'GeometryNodeTree':
        a_object = bpy.context.space_data.id
    if ui_type == 'ShaderNodeTree':
        a_object = bpy.context.object
    vertex_groups = a_object.vertex_groups
    uv_layers = a_object.data.uv_layers
    color_attributes = a_object.data.color_attributes
    exclude_list = [_.name for _ in vertex_groups] + [
                    _.name for _ in uv_layers] + [
                    _.name for _ in color_attributes]
    prefs = pref()
    if not prefs.hide_extra_attr:
        extend_dict_with_evaluated_obj_attrs(attrs, exclude_list, a_object, all_tree_attr_list)         # 扩展已有字典
    if prefs.show_vertex_group:
        for v_g in vertex_groups:
            if attrs.get(v_g.name): continue        # 如果节点里又存了顶点组之类的,别覆盖
            attrs[v_g.name] = {'data_type': 'FLOAT', 'domain_info': [tr('点')],
                                "group_name":tr("物体属性"), "info": tr("顶点组") }
    if prefs.show_uv_map:
        for uv in uv_layers:
            if attrs.get(uv.name): continue
            attrs[uv.name] = {'data_type': 'FLOAT_VECTOR', 'domain_info': [tr('面拐')],
                                "group_name":tr("物体属性"), "info": tr("UV贴图") }
    if prefs.show_color_attr:
        for color in color_attributes:
            if attrs.get(color.name): continue
            attrs[color.name] = {'data_type': 'FLOAT_COLOR', 'domain_info': [tr(get_domain_cn[color.domain])],
                                "group_name":tr("物体属性"), "info": tr("颜色属性") }

def custom_sort_dict(attrs, sort_key_list):
    sorted_list = []
    for sort_key in sort_key_list:
        for key in attrs.keys():
            if attrs[key]['data_type'] == sort_key:
                sorted_list.append((key, attrs[key]))
    attrs = {k: v for k, v in sorted_list}
    return attrs

def sort_attr_dict(attrs):
    # 在函数内部创建了一个新的局部变量 attrs，这个变量在函数结束后就会被销毁，不会影响外部的 attrs 变量。
    attrs = {k: attrs[k] for k in sorted(attrs)}        # sorted(dict) = sorted(d1.keys())
    # print(f"{scene.sort_list = }")
    prefs = pref()
    if prefs.sort_list == '按类型排序1':
        attrs = custom_sort_dict(attrs, sort_key_list1)
    if prefs.sort_list == '按类型排序1-反转':
        sort_key_list = reversed(sort_key_list1)
        attrs = custom_sort_dict(attrs, sort_key_list)
    if prefs.sort_list == '按类型排序2':
        attrs = custom_sort_dict(attrs, sort_key_list2)
    # todo 完全按字符串排序
    # if prefs.sort_list == '完全按字符串排序':
    #     attrs = attrs
    return attrs

def draw_attr_menu(layout, context, is_panel):
    '''is_panel = True 时，在面板里额外绘制一些东西'''
    ui_type = context.area.ui_type
    # tree = get_tree(context, ui_type)
    tree = get_active_gn_tree(context, ui_type)
    if tree:
        attrs_dict = {}     # {'组内': {'data_type': 'FLOAT', 'domain_info': ['点', '面']},'距离': {'data_type': 'FLOAT', 'domain_info': ['点']}}
        attrs = get_tree_attrs_dict(tree, attrs_dict, stored_group=[],
                                    group_node_name="当前group是顶层节点树", group_name_parent="顶层节点树无父级")
        all_tree_attr_list = get_tree_attrs_list(tree, all_tree_attr_list=[], stored_group=[])
    else:
        attrs = {}
        all_tree_attr_list = []
    if context.space_data.id_from.type == "MESH":    # 几何节点时id是物体，材质节点时id是材质,id_from都是物体
        extend_dict_with_obj_data_attrs(attrs, all_tree_attr_list)
    attrs = sort_attr_dict(attrs)
    # print("最终" + "*" * 60)
    # pprint(attrs)
    # # print(context.space_data.id.name)
    prefix_list = pref().hide_prefix.split("|")
    for attr_name, attr_info in attrs.items():
        has_prefix = False
        if pref().is_hide_by_pre:
            for prefix in prefix_list:
                if prefix and attr_name.startswith(prefix):
                    has_prefix = True
                    break
        if has_prefix:
            continue
        data_type = attr_info["data_type"]
        ui_type = context.area.ui_type
        if data_type not in data_types:
            continue
        if ui_type == 'ShaderNodeTree' and data_type not in shader_date_types:
            continue
        stored_domain_list = list(set(attr_info['domain_info']))

        domain_list_to_str = " | ".join(sorted(stored_domain_list, key=lambda x: get_domain_list().index(x)))
        button_txt = attr_name + "(" + domain_list_to_str + ")" if pref().show_attr_domain else attr_name
        if_instanced = attr_info.get("if_instanced", False)
        if ui_type == 'ShaderNodeTree' and if_instanced:
            button_txt = button_txt[:-1] + " ->实例)"
            # button_txt = button_txt[:-1] + f' ->{ tr("实例") })'        #  或者外双引号内单引号
        description = tr("属性所在域: ") + domain_list_to_str
        # todo 更详细的description
        # description = "属性所在域:" + domain_list_to_str + \
        #             "\n此存储命名属性节点使用个数:" + "  " \
        #             "\n此命名属性节点使用个数:" + "  "
        group_name = attr_info["group_name"]
        node_name = str(attr_info.get("node_name", "无属性")[0])
        # if len(stored_domain_list) == 1:
        can_find_store_node = False
        if group_name != tr("物体属性"):        # group_name 是该命名属性节点在什么节点组里存过
            description += f'\n{tr("所在节点组: ")}' + str(group_name)
            if group_name != tr("不确定"):
                can_find_store_node = True
        if group_name == tr("物体属性"):
            description += f'\n{tr("类型: ")}' + attr_info['info']  # "\n类型:"
        if is_panel:        # 面板里额外绘制
            split = layout.split(factor=0.9)
            op = split.operator('sna.add_node_change_name_and_type', text=button_txt,
                                    icon_value=(_icons[data_with_png[data_type]].icon_id ) )
            if can_find_store_node:
                icon = "HIDE_OFF"
            else:
                icon = "HIDE_ON"
            if ui_type == 'GeometryNodeTree':
                op_find = split.operator('node.view_stored_attribute_node', text="", emboss=can_find_store_node, icon=icon)
                # op_find.node_name = attr_info.get("node_name", "无属性")
                op_find.node_name = node_name
                group_name_list = attr_info.get("group_node_name", "无属性")
                op_find.group_node_name = str(group_name_list[0])
                op_find.parent_path = str(attr_info.get("group_name_parent", "无属性")[0])
                # total = len(group_name_list)
                # op_find.total = total
                # op_find.current += 1
                # op_find.bl_description = "该属性存储次数:" + str(total) \
                #                                     + "\ncurrent:" + str(op_find.current)
        else:
            op = layout.operator('sna.add_node_change_name_and_type', text=button_txt,
                                    icon_value=(_icons[data_with_png[data_type]].icon_id ) )
            # print(type(op))     # <class 'bpy.types.NODE_PIE_OT_add_node'>
        op.attr_name = attr_name
        op.attr_type = data_type
        op.bl_description = description
        op.domain_str = domain_list_to_str
        op.if_instanced = if_instanced
        op.shader_node_type = "ShaderNodeAttribute"
        if group_name == tr("物体属性"):
            if attr_info['info'] == tr("颜色属性"):
                op.shader_node_type = "ShaderNodeVertexColor"
            if attr_info['info'] == tr("UV贴图"):
                op.shader_node_type = "ShaderNodeUVMap"

class ATTRLIST_OT_Add_Node_Change_Name_Type_Hide(Operator):
    bl_idname = "sna.add_node_change_name_and_type"
    bl_label = "属性隐藏选项"
    bl_options = {"REGISTER", "UNDO"}
    bl_description   : StringProperty(name='btn_info', default="快捷键Shift 2 ", options={"HIDDEN"})    # 乐,记不清什么时候的了
    attr_name        : StringProperty(name='attr_name', description='', default="", subtype='NONE')
    attr_type        : StringProperty(name='attr_type', description='', default="", subtype='NONE')
    domain_str       : StringProperty(name='domain_str', default="", description='该属性所在域,例：面 | 实例', options={"HIDDEN"})
    shader_node_type : StringProperty(name='shader_node_type', description='', default="", subtype='NONE')
    if_instanced     : BoolProperty(name='if instanced', description='该属性是否转到了实例域上', default=False)

    @classmethod
    def description(cls, context, props):
        if props:
            return props.bl_description

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        prefs = pref()
        data_type = self.attr_type
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            prefs.panel_info = tr("添加已命名属性节点")
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = self.attr_name
            attr_node.inputs["Name"].hide = prefs.hide_Name_socket
            attr_node.show_options = not prefs.hide_option
            if prefs.rename_Attr_socket:
                if bpy.data.version >= (4, 1, 0):
                    attr_node.outputs["Attribute"].name = self.attr_name        # socket的identifier也是Attribute  socket[identifier] 优先
                else:
                    for socket in attr_node.outputs:        # 因为之前版本,已命名属性节点有多个Attribute输出接口
                        if socket.enabled and not socket.hide and socket.name=="Attribute":
                            socket.name = self.attr_name
            attr_node.outputs["Exists"].hide = prefs.hide_Exists_socket

        if ui_type == 'ShaderNodeTree':
            prefs.panel_info = tr("添加属性节点")
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type=self.shader_node_type)
            # [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
            attr_node = context.active_node
            if self.shader_node_type == "ShaderNodeAttribute":
                if self.domain_str == tr("实例") or self.if_instanced:
                    attr_node.attribute_type = "INSTANCER"
                attr_node.attribute_name = self.attr_name
                socket_order = { 'BOOLEAN'     : 2,
                                'FLOAT'       : 2,
                                'INT'         : 2,
                                'FLOAT_VECTOR': 1,
                                'FLOAT_COLOR' : 0,
                                }
                for i, out_soc in enumerate(attr_node.outputs):
                    order = socket_order[data_type]
                    if i == order and prefs.rename_Attr_socket:
                        out_soc.name = self.attr_name
                    if i != order:
                        out_soc.hide = True
            if self.shader_node_type == "ShaderNodeVertexColor":
                attr_node.layer_name = self.attr_name
            if self.shader_node_type == "ShaderNodeUVMap":
                attr_node.uv_map = self.attr_name
            attr_node.show_options = not prefs.hide_Name_socket
        if prefs.rename_Node:
            # attr_node.label = "属性:" + self.attr_name
            attr_node.label = prefs.rename_prefix + self.attr_name
        attr_node.hide = prefs.hide_Node
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

def exist_node_tree(context):
    ui_type = context.area.ui_type
    edit_tree = context.space_data.edit_tree
    if ui_type == "GeometryNodeTree" and edit_tree:
        return True
    if ui_type == "ShaderNodeTree" and edit_tree:
        a_obj = context.active_object
        if a_obj and a_obj.type in {'MESH','CURVE','SURFACE','FONT','META','GPENCIL','VOLUME','CURVES','POINTCLOUD'}:
            return True
    return False

class ATTRLIST_MT_Menu(Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = tr("命名属性菜单")
    bl_options = {'SEARCH_ON_KEY_PRESS'}
    
    @classmethod
    def poll(cls, context):
        # # ['MESH', 'CURVE', 'SURFACE', 'FONT', 'VOLUME', 'GREASEPENCIL']   能添加几何节点 才 return True
        return exist_node_tree(context)

    def draw(self, context):
        self.bl_options = {'SEARCH_ON_KEY_PRESS'} if not pref().use_accelerator_key else set()
        draw_attr_menu(self.layout, context, is_panel=False)

class ATTRLIST_PT_NPanel(Panel):
    bl_label = tr('命名属性面板')      # 还作为在快捷键列表里名称
    bl_idname = 'ATTRLIST_PT_NPanel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Node'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return exist_node_tree(context)

    def draw(self, context):
        layout = self.layout
        prefs = pref()
        a_node = context.active_node
        if a_node:
            if a_node.bl_idname == "GeometryNodeObjectInfo" and a_node.select:
                obj_name = a_node.inputs[0].default_value.name
                info = obj_name + "的属性"
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            info = tr("活动物体及节点树属性")
            icon='GEOMETRY_NODES'
        if ui_type == 'ShaderNodeTree':
            info = tr("活动物体属性")
            icon='MATERIAL_DATA'
        split = layout.split(factor=0.9)
        split.label(text=info, icon=icon)
        split.prop(prefs, 'show_set_panel', toggle=True, text='', icon="PREFERENCES")

        if prefs.show_set_panel:
            arrow_show = "TRIA_RIGHT" if not prefs.add_settings else "TRIA_DOWN"
            box1 = layout.box()
            box1.scale_y = 0.9
            box1.prop(prefs, "add_settings", emboss=True, icon=arrow_show)
            if prefs.add_settings:

                # split.label(text=tr('菜单快捷键: '))
                # split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)
                # split = box1.split(factor=0.5)
                # split.label(text=tr('面板快捷键: '))
                # split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)

                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_option',        toggle=True, text=tr('隐藏节点选项'))
                split.prop(prefs, 'hide_Exists_socket', toggle=True, text=tr('隐藏存在接口'))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_Name_socket',   toggle=True, text=tr('隐藏名称接口'))
                split.prop(prefs, 'rename_Attr_socket', toggle=True, text=tr('重命名属性接口'))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_Node',          toggle=True, text=tr('折叠节点'))
                split.prop(prefs, 'rename_Node',        toggle=True, text=tr('重命名节点标签'))
                split = box1.split(factor=0.5)
                split.label(text=tr('重命名添加前缀: '))
                split.prop(prefs, 'rename_prefix', text="")

            arrow_add = "TRIA_RIGHT" if not prefs.show_settings else "TRIA_DOWN"
            box2 = layout.box()
            box2.scale_y = 0.9
            box2.prop(prefs, "show_settings", emboss=True, icon=arrow_add)
            if prefs.show_settings:
                split2 = box2.split(factor=0.4)
                split2.label(text=tr('列表排序方式'))
                split2.prop(prefs, 'sort_list', text='')

                box2.label(text=tr('属性列表里是否显示'))
                split3 = box2.split(factor=0.05)        # 使得文本左顶格，按钮前稍微缩进
                split3.label(text="")
                split31 = split3.split(factor=0.35)
                split31.prop(prefs, 'show_vertex_group',  toggle=True, text=tr('顶点组'))
                split32 = split31.split(factor=0.4)
                split32.prop(prefs, 'show_uv_map',        toggle=True, text=tr('UV'))
                split32.prop(prefs, 'show_color_attr',    toggle=True, text=tr('颜色属性'))

                box2.label(text=tr('属性列表里是否隐藏'))
                split4 = box2.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.33)
                split41.prop(prefs, 'hide_extra_attr', toggle=True, text=tr('额外属性'))
                split42 = split41.split(factor=0.5)
                split42.prop(prefs, 'hide_unused_attr',   toggle=True, text=tr('未使用属性'))
                split42.prop(prefs, 'hide_attr_in_group', toggle=True, text=tr('组内属性'))

                split4 = box2.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.5)
                split41.prop(prefs, 'is_hide_by_pre', toggle=True, text=tr('隐藏前缀'))
                if prefs.is_hide_by_pre:
                    split41.prop(prefs, 'hide_prefix', text='')

                split5 = box2.split(factor=0.5)
                split5.label(text=tr('属性列表文本设置'))
                split5.prop(prefs, 'show_attr_domain', toggle=True, text=tr('显示所在域'))

                split6 = box2.split(factor=0.5)
                split6.label(text=tr('查找节点设置'))
                split6.prop(prefs, 'if_scale_editor', toggle=True, text=tr('适当缩放视图'))
                
                split7 = box2.split(factor=0.5)
                split7.label(text=tr('使用加速键'))
                split7.prop(prefs, 'use_accelerator_key', toggle=True, text=tr('使用加速键'))

        box3 = layout.box()
        draw_attr_menu(box3, context, is_panel=True)

        # box4 = layout.box()
        # box4.operator('node.test', text="测试", icon="PIVOT_CURSOR")
        # box4.operator('node.move_view_to_center', text="view_selected", icon="PIVOT_CURSOR")
        # box4.operator('view2d.scroll_up', text="上移", icon="TRIA_UP")
        # box4.operator('view2d.scroll_down', text="下移", icon="TRIA_DOWN")
        # box4.operator('view2d.scroll_left', text="左移", icon="TRIA_LEFT")
        # box4.operator('view2d.scroll_right', text="右移", icon="TRIA_RIGHT")

def exit_group_to_root():
    space = bpy.context.space_data
    tree_path = space.path.to_string.split("/")[1:]     # 只留下节点组的名字，不包括根名
    for i in range(len(tree_path)):
        space.path.pop()
        # bpy.ops.node.tree_path_parent()

def proper_scroll_view():
    if bpy.context.preferences.addons[__package__].preferences.if_scale_editor:
        for i in range(50):
            bpy.ops.view2d.zoom_out()
        for i in range(40):
            bpy.ops.view2d.zoom_in()

area = None
counter = None
# 该函数用于在间隔一段时间后运行ops
def timer_view_selected():
    global counter, area
    counter += 1
    if counter == 2:
        # 在正确的上下文中运行ops
        region = [region for region in area.regions if region.type == "WINDOW"][0]
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.node.view_selected()
        return None         # 返回 None 以结束计时器
    return 0.05

class NODE_OT_View_Stored_Attribute_Node(Operator):
    bl_idname = "node.view_stored_attribute_node"
    bl_label = tr("跳转到已命名属性节点位置")
    bl_description = tr("对于存了多次的属性,查找节点目前只能定位到其中之一")
    node_name :   StringProperty(name='node_name', description='存储属性节点目标', default="无", subtype='NONE')
    parent_path : StringProperty(name='parent_path', description='parent_path', default="", subtype='NONE')
    group_node_name : StringProperty(name='group_node_name', description='group_node_name', default="", subtype='NONE')
    # bl_description: StringProperty(default="", options={"HIDDEN"})
    # total :   IntProperty(description='total', default=0)
    # current : IntProperty(description='current', default=0)

    @classmethod
    def description(cls, context, props):
        if props:
            return props.bl_description

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'GeometryNodeTree'

    def execute(self, context):
        if self.node_name == "无":
            return {'FINISHED'}
        exit_group_to_root()
        proper_scroll_view()
        # self.parent_path          # 顶层节点树无父级/Geometry Nodes/测试组
        # self.group_node_name      # 当前group是顶层节点树/Group.001/Group.002
        # print(path_list)
        # print(name_list)
        print(self.node_name)

        path_list = self.parent_path.split("/")[1:]
        name_list = self.group_node_name.split("/")[1:]

        for path, name in zip(path_list, name_list):
            nodes = bpy.data.node_groups[path].nodes
            group_node = nodes[name]
            nodes.active = group_node
            bpy.ops.node.group_edit(exit=False)

        bpy.ops.node.select_all(action='DESELECT')
        nodes = context.space_data.edit_tree.nodes
        tar_node = nodes[self.node_name]
        tar_node.select = True
        nodes.active = tar_node
        # bpy.ops.node.view_selected()
        # 储存上下文信息并启动计时器
        global counter, area
        area = context.area
        counter = 0
        bpy.app.timers.register(timer_view_selected)

        return {'FINISHED'}

class NODE_OT_Add_Named_Attribute(Operator):
    bl_idname = "node.add_named_attribute_node"
    bl_label = tr("快速添加命名属性节点")
    bl_description = tr("快速添加选中的活动存储属性节点相应的已命名属性节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        # edit_tree = context.space_data.edit_tree
        return context.area.ui_type == 'GeometryNodeTree'

    def execute(self, context):
        active_node = context.active_node
        prefs = pref()
        if active_node and active_node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            attr_name = active_node.inputs["Name"].default_value
            data_type = active_node.data_type
            if data_type in switch_dict:
                data_type = switch_dict[data_type]
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = attr_name
            attr_node.inputs["Name"].hide = prefs.hide_Name_socket
            attr_node.show_options = not prefs.hide_option
            attr_node.hide = prefs.hide_Node
            if prefs.rename_Node:
                attr_node.label = prefs.rename_prefix + self.attr_name
            if prefs.rename_Attr_socket:
                if bpy.data.version >= (4, 1, 0):
                    attr_node.outputs["Attribute"].name = attr_name        # socket的identifier也是Attribute  socket[identifier] 优先
                else:
                    for socket in attr_node.outputs:        # 因为之前版本,已命名属性节点有多个Attribute输出接口
                        if socket.enabled and not socket.hide and socket.name=="Attribute":
                            socket.name = attr_name
            attr_node.outputs["Exists"].hide = prefs.hide_Exists_socket
        else:
            bpy.ops.node.add_node('INVOKE_DEFAULT', use_transform=True, type='GeometryNodeInputNamedAttribute')
        return {"FINISHED"}

classes = [
    ATTRLIST_OT_Add_Node_Change_Name_Type_Hide,
    ATTRLIST_MT_Menu,
    ATTRLIST_PT_NPanel,
    ATTRLIST_AddonPrefs,
    NODE_OT_View_Stored_Attribute_Node,
    NODE_OT_Add_Named_Attribute,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.NODE_MT_editor_menus.append(add_to_attr_list_mt_editor_menus)

    for cla in classes:
        bpy.utils.register_class(cla)

    for png in png_list:
        _icons.load(png, os.path.join(os.path.dirname(__file__), 'icons', png), "IMAGE")

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'ATTRLIST_MT_Menu'
    addon_keymaps['唤出菜单快捷键'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_panel', 'TWO', 'PRESS', ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'ATTRLIST_PT_NPanel'
    kmi.properties.keep_open = True
    addon_keymaps['ATTRLIST_PT_NPanel'] = (km, kmi)

    kmi = km.keymap_items.new('node.add_named_attribute_node', 'TWO', 'PRESS', ctrl=True, alt=False, shift=False, repeat=False)
    addon_keymaps['添加存储节点对应属性节点'] = (km, kmi)

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.types.NODE_MT_editor_menus.remove(add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)
