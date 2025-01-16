import time
import bpy
import bpy.utils.previews
import os
from pprint import pprint
from bpy.types import Operator, Menu, Panel, AddonPreferences
from bpy.props import StringProperty, EnumProperty, BoolProperty
from . import translator

tr = translator.i18n


bl_info = {
    "name" : "小王-几何节点命名属性列表",
    "author" : "一尘不染", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (2, 1, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}

# ! 提交到扩展平台时删掉辅助打印
# todo 重命名属性接口移过来 (小王-批量重命名节点和属性节点接口.py)
# todo 快速添加组输入节点 好像已经移过来了
# todo 属性列表多种排序方式
# todo 添加个重命名属性名: 更改 存储属性和命名属性的 名称接口值

addon_keymaps = {}
_icons = None

domain_en_list = [ 'POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE',  'INSTANCE', 'LAYER' ]
domain_lower_list = ["Point", "Edge", "Face", "Corner", "Curve", "Instance", "Layer"]
domain_cn_list = [ '点',    '边',   '面',   '面拐',   '样条线', '实例',     '层'    ]
# 先从英文大写翻译成中文,再根据语言决定是否翻译成英文小写
get_domain_cn = {k: v for k, v in zip(domain_en_list, domain_cn_list)}

def get_domain_list():
    view = bpy.context.preferences.view
    trans = view.use_translate_interface

    if view.language in ["zh_CN", "zh_HANS"] and trans:
        return domain_cn_list
    else:
        return domain_lower_list

data_types =        ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'MATRIX']
shader_date_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
switch_dict = { "BYTE_COLOR": "FLOAT_COLOR", "FLOAT2": "FLOAT_VECTOR"}

sort_key_list1 = [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'MATRIX']
sort_key_list2 = [ 'INT', 'BOOLEAN', 'FLOAT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'MATRIX']

png_list = [
            '域-布尔.png',
            '域-浮点.png',
            '域-整数.png',
            '域-矢量.png',
            '域-颜色.png',
            '域-旋转.png',
            '域-矩阵.png',
            ]

data_with_png = {k: v for k, v in zip(data_types, png_list)}

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

class ATTRLIST_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout 
        split = layout.split(factor=0.5)
        
        split.label(text=tr('菜单快捷键:'))
        split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)
        
        split = layout.split(factor=0.5)
        split.label(text=tr('面板快捷键:'))
        split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)
        
        box1 = layout.box()
        box1.label(text=tr("已知限制: "), icon='INFO')
        limit1 = " "*20 + tr("非网格域存储属性节点,名称接口由别的接口连接的话,可能识别不到")
        limit2 = " "*20 + tr("存储属性节点后经过了实例化或实现实例,在着色器添加属性,选项不一定正确")
        box1.label(limit1)
        box1.label(limit2)

def get_tree(context, ui_type):
    if ui_type == 'GeometryNodeTree':
        obj = context.space_data.id
    if ui_type == 'ShaderNodeTree':
        obj = context.active_object
    return obj.modifiers.active.node_group

def is_node_linked(node):
    soc_out = node.outputs
    if len(soc_out):
        for soc in soc_out:
            if soc.is_linked:
                return True
    return False

def loop_find_if_instanced(node):
    if node.outputs:
        links = node.outputs[0].links
        i = 0
        while links:
            i += 1
            if i > 30:
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
    context = bpy.context
    scene = context.scene

    nodes = tree.nodes
    # attrs_dict = {}  # 放在这里的话，偶尔出问题  {'Attribute': {'data_type': 'FLOAT_COLOR', 'domain_info': 'CORNER'}, 'Colorxx': {'data_type': 'FLOAT_COLOR', 'domain_info': 'POINT'} }
    show_unused = not scene.only_show_used_attr
    
    for node in nodes:
        if node.mute:   continue
        if node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            if show_unused or is_node_linked(node):
                
                # node.outputs['Geometry'].links[0].to_node
                data_type = node.data_type
                if data_type == "FLOAT4X4":
                    data_type = "MATRIX"
                if data_type in switch_dict:
                    data_type = switch_dict[data_type]
                attr_name = node.inputs["Name"].default_value
                if attr_name == "":
                    continue
                domain_cn = tr(get_domain_cn[node.domain])               # 还可以这样

                # ! 上个版本1.6，存过没存过的,太麻烦了
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
        is_pass = not scene.hide_attr_in_group
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

def get_all_tree_attrs_list(tree, all_tree_attr_list, stored_group):
    context = bpy.context
    scene = context.scene

    nodes = tree.nodes
    show_unused = not scene.only_show_used_attr
    
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
                all_tree_attr_list = get_all_tree_attrs_list(node.node_tree, all_tree_attr_list, stored_group)

    return all_tree_attr_list

def extend_dict_with_evaluated_obj_attrs(attrs_dict, exclude_list, obj, all_tree_attr_list):
    context = bpy.context
    box = context.evaluated_depsgraph_get()
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
            attrs_dict[attr.name] = {"data_type": data_type, "domain_info": [domain_info], "group_name":"不确定"}

def extend_dict_with_obj_data_attrs(attrs, scene, all_tree_attr_list):
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
    extend_dict_with_evaluated_obj_attrs(attrs, exclude_list, a_object, all_tree_attr_list)         # 扩展已有字典

    if scene.show_vertex_group:
        for v_g in vertex_groups:
            attrs[v_g.name] = {'data_type': 'FLOAT', 'domain_info': [tr('点')], 
                                "group_name":tr("物体属性"), "info": tr("顶点组") }
    if scene.show_uv_map:
        for uv in uv_layers:
            attrs[uv.name] = {'data_type': 'FLOAT_VECTOR', 'domain_info': [tr('面拐')], 
                                "group_name":tr("物体属性"), "info": tr("UV贴图") }
    if scene.show_color_attr:
        for color in color_attributes:
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

def sort_attr_dict(attrs, scene):
    # 在函数内部创建了一个新的局部变量 attrs，这个变量在函数结束后就会被销毁，不会影响外部的 attrs 变量。
    attrs = {k: attrs[k] for k in sorted(attrs)}        # sorted(dict) = sorted(d1.keys())

    if scene.sort_list == tr('按类型排序1'):
        attrs = custom_sort_dict(attrs, sort_key_list1)
    if scene.sort_list == tr('按类型排序1-反转'):
        sort_key_list = reversed(sort_key_list1)
        attrs = custom_sort_dict(attrs, sort_key_list)
    if scene.sort_list == tr('按类型排序2'):
        attrs = custom_sort_dict(attrs, sort_key_list2)
    # todo 完全按字符串排序
    # if scene.sort_list == '完全按字符串排序':
    #     attrs = attrs
    return attrs

def sort_attrs_and_draw_menu(layout, context, is_panel):
    '''is_panel = True 时，在面板里额外绘制一些东西'''
    scene = context.scene
    ui_type = context.area.ui_type
    tree = get_tree(context, ui_type)

    attrs_dict = {}     # {'组内': {'data_type': 'FLOAT', 'domain_info': ['点', '面']},'距离': {'data_type': 'FLOAT', 'domain_info': ['点']}}
    attrs = get_tree_attrs_dict(tree, attrs_dict, stored_group=[], 
                                group_node_name="当前group是顶层节点树", group_name_parent="顶层节点树无父级")

    all_tree_attr_list = get_all_tree_attrs_list(tree, all_tree_attr_list=[], stored_group=[])

    extend_dict_with_obj_data_attrs(attrs, scene, all_tree_attr_list)
    attrs = sort_attr_dict(attrs, scene)

    # print("最终" + "*" * 60)
    # pprint(attrs)
    """ # # 一些方便打印
    # print("最终" + "*" * 100)
    # print(context.space_data.id.name)
    # print("开始" + "*" * 100)
    # pprint(attrs_dict)
    # if scene.show_vertex_group or scene.show_uv_map or scene.show_color_attr:
    #     pprint(attrs_dict)
    # pprint("-+*" * 20)
    # print("排序：")
    # pprint(attrs) """
    prefix_list = scene.hide_by_prefix.split("|")
    for attr_name, attr_info in attrs.items():
        has_prefix = False
        if scene.is_hide_by_pre:
            for prefix in prefix_list:
                if attr_name.startswith(prefix):
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
        button_txt = attr_name + "(" + domain_list_to_str + ")" if scene.show_attr_domain else attr_name
        if_instanced = attr_info.get("if_instanced", False)
        if ui_type == 'ShaderNodeTree' and if_instanced:
            # button_txt = button_txt[:-1] + " ->实例)"
            button_txt = button_txt[:-1] + f' ->{ tr("实例") })'        #  或者外双引号内单引号
        description = tr("属性所在域: ") + domain_list_to_str
        # description = "属性所在域:" + domain_list_to_str + \
        #             "\n此存储命名属性节点使用个数:" + "  " \
        #             "\n此命名属性节点使用个数:" + "  "
        group_name = attr_info["group_name"]
        node_name = str(attr_info.get("node_name", "无属性")[0])
        # if len(stored_domain_list) == 1:
        if group_name != tr("物体属性"):
            description += f'\n{tr("所在节点组: ")}' + str(group_name)
        if group_name == tr("物体属性"):
            description += f'\n{tr("类型: ")}' + attr_info['info']  # "\n类型:"
        if is_panel:
            split = layout.split(factor=0.9)
            op = split.operator('sna.add_node_change_name_and_type', text=button_txt,
                                    icon_value=(_icons[data_with_png[data_type]].icon_id ) )
            op.attr_name = attr_name
            op.attr_type = data_type
            op.bl_description = description
            op.if_instanced = if_instanced
            op.domain_str = domain_list_to_str
            
            # can_find_node = ( group_name[0] == edit_tree.name ) and len(group_name)==1    # 只能查找跳转 当前活动树里的属性
            can_find_node = len(group_name)==1
            if can_find_node:
                icon = "HIDE_OFF"
            else:
                icon = "HIDE_ON"
            op = split.operator('node.view_stored_attribute_node', text="", emboss=can_find_node, icon=icon)
            # op.node_name = attr_info.get("node_name", "无属性")
            op.node_name = node_name
            op.group_node_name = str(attr_info.get("group_node_name", "无属性")[0])
            op.parent_path = str(attr_info.get("group_name_parent", "无属性")[0])
        else:
            op = layout.operator('sna.add_node_change_name_and_type', text=button_txt,
                                    icon_value=(_icons[data_with_png[data_type]].icon_id ) )
            op.attr_name = attr_name
            op.attr_type = data_type
            op.bl_description = description
            op.domain_str = domain_list_to_str
            op.if_instanced = if_instanced
            # print(type(op))     # <class 'bpy.types.NODE_PIE_OT_add_node'>

class ATTRLIST_OT_Add_Node_Change_Name_Type_Hide(Operator):
    bl_idname = "sna.add_node_change_name_and_type"
    bl_label = "属性隐藏选项"
    # bl_description = "快捷键Shift 2 "
    bl_options = {"REGISTER", "UNDO"}
    attr_name:  StringProperty(name='attr_name', description='', default="", subtype='NONE')
    attr_type:  StringProperty(name='attr_type', description='', default="", subtype='NONE')
    bl_description: StringProperty(default="快捷键Shift 2 ", options={"HIDDEN"})
    domain_str    : StringProperty(default="", description='该属性所在域,例：面 | 实例', options={"HIDDEN"})
    if_instanced : BoolProperty(name='if instanced', description='该属性是否转到了实例域上', default=False)

    @classmethod
    def description(cls, context, props):
        if props:
            return props.bl_description

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        data_type = self.attr_type
        scene = context.scene
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            scene.panel_info = tr("添加已命名属性节点")
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = self.attr_name
            attr_node.inputs["Name"].hide = scene.hide_Name_socket
            attr_node.show_options = not scene.hide_option
            if scene.rename_Attr_socket:
                if bpy.data.version >= (4, 1, 0):
                    attr_node.outputs["Attribute"].name = self.attr_name        # socket的identifier也是Attribute  socket[identifier] 优先
                else:
                    for socket in attr_node.outputs:        # 因为之前版本,已命名属性节点有多个Attribute输出接口
                        if socket.enabled and not socket.hide and socket.name=="Attribute":
                            socket.name = self.attr_name
            attr_node.outputs["Exists"].hide = scene.hide_Exists_socket

        if ui_type == 'ShaderNodeTree':
            scene.panel_info = tr("添加属性节点")
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='ShaderNodeAttribute')
            # [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
            attr_node = context.active_node
            if self.domain_str == tr("实例") or self.if_instanced:
                attr_node.attribute_type = "INSTANCER"
            attr_node.attribute_name = self.attr_name
            attr_node.show_options = not scene.hide_Name_socket
            socket_order = { 'BOOLEAN'     : 2,
                             'FLOAT'       : 2,
                             'INT'         : 2,
                             'FLOAT_VECTOR': 1,
                             'FLOAT_COLOR' : 0,
                            }
            for i, out_soc in enumerate(attr_node.outputs):
                order = socket_order[data_type]
                if i == order:
                    out_soc.name = self.attr_name
                if i != order:
                    out_soc.hide = True
        
        if scene.rename_Node:
            # attr_node.label = "属性:" + self.attr_name
            attr_node.label = scene.rename_prefix + self.attr_name
        attr_node.hide = scene.hide_Node
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class ATTRLIST_MT_Menu(Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = tr("小王-命名属性列表菜单")

    @classmethod
    def poll(cls, context):
        # # ['MESH', 'CURVE', 'SURFACE', 'FONT', 'VOLUME', 'GREASEPENCIL']   能添加几何节点 才 return True
        edit_tree = context.space_data.edit_tree
        return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree'] and edit_tree

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        sort_attrs_and_draw_menu(layout, context, is_panel=False)

class ATTRLIST_PT_NPanel(Panel):
    bl_label = tr('小王-命名属性列表面板')      # 还作为在快捷键列表里名称
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
        edit_tree = context.space_data.edit_tree
        return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree'] and edit_tree

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
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
        split.prop(scene, 'show_set_panel', toggle=True, text='', icon="PREFERENCES")

        if scene.show_set_panel:
            arrow_show = "TRIA_RIGHT" if not scene.add_settings else "TRIA_DOWN"
            box1 = layout.box()
            box1.scale_y = 0.9
            box1.prop(scene, "add_settings", emboss=True, icon=arrow_show)
            if scene.add_settings:

                # split.label(text=tr('菜单快捷键: '))
                # split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)
                # split = box1.split(factor=0.5)
                # split.label(text=tr('面板快捷键: '))
                # split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)

                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_option',        toggle=True, text=tr('隐藏节点选项'))
                split.prop(scene, 'hide_Exists_socket', toggle=True, text=tr('隐藏存在接口'))
                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_Name_socket',   toggle=True, text=tr('隐藏名称接口'))
                split.prop(scene, 'rename_Attr_socket', toggle=True, text=tr('重命名属性接口'))
                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_Node',          toggle=True, text=tr('折叠节点'))
                split.prop(scene, 'rename_Node',        toggle=True, text=tr('重命名节点标签'))
                split = box1.split(factor=0.5)
                split.prop(scene, 'rename_prefix',      toggle=True, text=tr('前缀'))
            
            arrow_add = "TRIA_RIGHT" if not scene.show_settings else "TRIA_DOWN"
            box2 = layout.box()
            box2.scale_y = 0.9
            box2.prop(scene, "show_settings", emboss=True, icon=arrow_add)
            if scene.show_settings:
                split2 = box2.split(factor=0.4)
                split2.label(text=tr('列表排序方式'))
                split2.prop(scene, 'sort_list', text='')
                
                box2.label(text=tr('属性列表里是否显示'))
                split3 = box2.split(factor=0.05)        # 使得文本左顶格，按钮前稍微缩进
                split3.label(text="")
                split31 = split3.split(factor=0.35)
                split31.prop(scene, 'show_vertex_group', toggle=True, text=tr('顶点组'))
                split32 = split31.split(factor=0.4)
                split32.prop(scene, 'show_uv_map',       toggle=True, text=tr('UV'))
                split32.prop(scene, 'show_color_attr',   toggle=True, text=tr('颜色属性'))
                
                box2.label(text=tr('属性列表里是否隐藏'))
                split4 = box2.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.5)
                split41.prop(scene, 'only_show_used_attr', toggle=True, text=tr('未使用属性'))
                split41.prop(scene, 'hide_attr_in_group',  toggle=True, text=tr('节点组内属性'))
                
                split4 = box2.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.5)
                split41.prop(scene, 'is_hide_by_pre', toggle=True, text=tr('前缀'))
                if scene.is_hide_by_pre:
                    split41.prop(scene, 'hide_by_prefix', text='')

                split41 = box2.split(factor=0.5)
                split41.label(text=tr('属性列表文本设置'))
                split41.prop(scene, 'show_attr_domain', toggle=True, text=tr('显示所在域'))
                
                box2.label(text=tr('查找节点设置'))
                split5 = box2.split(factor=0.05)
                split5.label(text="")
                split51 = split5.split(factor=0.5)
                split51.prop(scene, 'if_scale_editor', toggle=True, text=tr('适当缩放视图'))
        
        box3 = layout.box()
        sort_attrs_and_draw_menu(box3, context, is_panel=True)
        
        box4 = layout.box()
        box4.operator('node.test', text="测试", icon="PIVOT_CURSOR")
        box4.operator('node.move_view_to_center', text="view_selected", icon="PIVOT_CURSOR")
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
    if bpy.context.scene.if_scale_editor:
        for i in range(50):
            bpy.ops.view2d.zoom_out()
        for i in range(40):
            bpy.ops.view2d.zoom_in()

area = None
counter = None
# 该函数用于在间隔一段时间后运行ops
def run_times():
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
    bl_label = "查找命名属性节点"
    bl_description = "跳转到已命名属性节点位置"
    node_name :   StringProperty(name='node_name', description='存储属性节点目标', default="", subtype='NONE')
    group_node_name :  StringProperty(name='group_node_name', description='group_node_name', default="", subtype='NONE')
    parent_path : StringProperty(name='parent_path', description='parent_path', default="", subtype='NONE')
    
    def execute(self, context):
        exit_group_to_root()
        proper_scroll_view()
        if self.node_name == "无属性":  return
        # self.parent_path          # 顶层节点树无父级/Geometry Nodes/测试组
        # self.group_node_name      # 当前group是顶层节点树/Group.001/Group.002
        # print(path_list)
        # print(name_list)

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
        bpy.app.timers.register(run_times) 

        return {'FINISHED'}

classes = [
    ATTRLIST_OT_Add_Node_Change_Name_Type_Hide,
    ATTRLIST_MT_Menu,
    ATTRLIST_PT_NPanel,
    ATTRLIST_AddonPreferences,
    NODE_OT_View_Stored_Attribute_Node,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    S = bpy.types.Scene
    bpy.types.NODE_MT_editor_menus.append(add_to_attr_list_mt_editor_menus)
    S.hide_option        = BoolProperty(name='hide_option',        description=tr('添加时是否隐藏选项'),         default=True)
    S.hide_Exists_socket = BoolProperty(name='hide_Exists_socket', description=tr('添加时是否隐藏输出接口存在'), default=True)
    S.hide_Name_socket   = BoolProperty(name='hide_Name_socket',   description=tr('添加时是否隐藏输入接口名称'), default=False)
    S.rename_Attr_socket = BoolProperty(name='rename_Attr_socket', description=tr('添加时是否命名输出接口属性'), default=True)
    S.hide_Node          = BoolProperty(name='hide_Node',          description=tr('添加时是否折叠节点'),         default=False)
    S.rename_Node        = BoolProperty(name='rename_Node',        description=tr('添加时是否重命名节点为属性名'), default=False)
    S.is_hide_by_pre     = BoolProperty(name='is_hide_by_pre',     description=tr('是否隐藏带有特定前缀的属性'), default=False)
    S.show_set_panel     = BoolProperty(name='show_set_panel',     description=tr('显示设置'),                   default=True)
    S.if_scale_editor    = BoolProperty(name='if_scale_editor',    description=tr('查找节点时适当缩放视图'),     default=True)
    S.show_vertex_group  = BoolProperty(name='Show_Vertex_Group',  description=tr('是否在属性列表里显示顶点组'),   default=True)
    S.show_uv_map        = BoolProperty(name='Show_UV_Map',        description=tr('是否在属性列表里显示UV贴图'),   default=False)
    S.show_color_attr    = BoolProperty(name='Show_Color_Attr',    description=tr('是否在属性列表里显示颜色属性'), default=False)
    S.only_show_used_attr= BoolProperty(name='only_show_used_attr',description=tr('只显示用到的属性,连了线的属性节点'), default=True)
    S.hide_attr_in_group = BoolProperty(name='hide_attr_in_group', description=tr('隐藏节点组里的属性'), default=False)
    S.add_settings       = BoolProperty(name=tr('添加节点选项'),   description=tr('添加节点选项'),       default=False)
    S.show_settings      = BoolProperty(name=tr('列表显示选项'),   description=tr('列表显示选项'),       default=True)
    S.show_attr_domain   = BoolProperty(name='show_attr_domain',   description=tr('是否显示属性所在域'), default=True)
    
    S.panel_info         = StringProperty(name='panel_info',     description=tr('显示在n面板上的插件当前状态描述'), default="")
    S.rename_prefix      = StringProperty(name='rename_prefix',  description=tr('重命名节点时添加的前缀'), default="")
    S.hide_by_prefix     = StringProperty(name='hide_by_prefix', description=tr('隐藏带有特定前缀的属性,以|分隔多种,例 .|_|-'), default="")
    
    S.sort_list          = EnumProperty(name='列表排序方式',     description=tr('属性列表多种排序方式'),
                                                 items=[('按类型排序1',      tr('按类型排序1'),      tr('布尔-浮点-整数-矢量-颜色-旋转-矩阵'), 0, 0), 
                                                        ('按类型排序1-反转', tr('按类型排序1-反转'), tr('矩阵-旋转-颜色-矢量-整数-浮点-布尔'), 0, 1), 
                                                        ('按类型排序2',      tr('按类型排序2'),      tr('整数-布尔-浮点-矢量-颜色-旋转-矩阵'), 0, 2), 
                                                        ('完全按字符串排序', tr('完全按字符串排序'), tr('首字-数字英文中文'), 0, 3)])
    
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

def unregister():
    global _icons
    S = bpy.types.Scene
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    del S.hide_option
    del S.hide_Exists_socket
    del S.hide_Name_socket
    del S.rename_Attr_socket
    del S.hide_Node
    del S.rename_Node
    del S.only_show_used_attr
    del S.hide_attr_in_group
    del S.add_settings
    del S.show_settings
    del S.rename_prefix
    del S.show_set_panel
    del S.if_scale_editor
    del S.panel_info
    del S.show_vertex_group
    del S.show_uv_map
    del S.show_color_attr
    del S.hide_by_prefix
    del S.sort_list
    
    bpy.types.NODE_MT_editor_menus.remove(add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)


