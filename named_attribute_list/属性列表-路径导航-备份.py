import time

import bpy
import bpy.utils.previews
import os
from pprint import pprint
from bpy.props import StringProperty, EnumProperty, BoolProperty

tr = bpy.app.translations


bl_info = {
    "name" : "小王-几何节点命名属性列表",
    "author" : "小王", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (2, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}

# todo 重命名属性接口移过来 (小王-批量重命名节点和属性节点接口.py)

addon_keymaps = {}
_icons = None

domain_en_list = [
        'POINT',
        'EDGE',
        'FACE',
        'CORNER',
        'CURVE',
        'INSTANCE',
        'LAYER',
        ]
domain_cn_list = [
        '点',
        '边',
        '面',
        '面拐',
        '样条线',
        '实例',
        '层',
        ]
get_domain_cn = {k: v for k, v in zip(domain_en_list, domain_cn_list)}

data_types =        ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', ]
shader_date_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
switch_dict = { "BYTE_COLOR": "FLOAT_COLOR", "FLOAT2": "FLOAT_VECTOR"}

png_list = [
            '域-布尔.png',
            '域-浮点.png',
            '域-整数.png',
            '域-矢量.png',
            '域-颜色.png',
            '域-旋转.png',
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
        layout.menu('ATTRLIST_MT_Menu', text='属性', icon_value=0)

class ATTRLIST_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = 'addon_59776'

    def draw(self, context):
        layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
        
        if True:
            layout = self.layout 
            layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
            layout.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='显示命名属性列表', full_event=True)

class ATTRLIST_MT_Menu(bpy.types.Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = "小王-命名属性列表菜单"

    @classmethod
    def poll(cls, context):
        # # ['MESH', 'CURVE', 'SURFACE', 'FONT', 'VOLUME', 'GREASEPENCIL']   能添加几何节点 才 return True
        edit_tree = context.space_data.edit_tree
        return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree'] and edit_tree

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        sort_attrs_and_draw_menu(layout, context, is_layout_split=False)

class ATTRLIST_OT_Add_Node_Change_Name_Type_Hide(bpy.types.Operator):
    bl_idname = "sna.add_node_change_name_and_type"
    bl_label = "属性隐藏选项"
    # bl_description = "快捷键Shift 2 "
    bl_options = {"REGISTER", "UNDO"}
    attr_name:  StringProperty(name='attr_name', description='', default="", subtype='NONE')
    attr_type:  StringProperty(name='attr_type', description='', default="", subtype='NONE')
    bl_description: StringProperty(default="快捷键Shift 2 ", options={"HIDDEN"})

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
            scene.panel_info = "添加已命名属性节点"
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
            scene.panel_info = "添加属性节点"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='ShaderNodeAttribute')
            # [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
            attr_node = context.active_node
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
            attr_node.label = scene.name_prefix + self.attr_name
        attr_node.hide = scene.hide_Node
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class ATTRLIST_PT_NPanel(bpy.types.Panel):
    bl_label = '小王-命名属性列表面板'      # 还作为在快捷键列表里名称
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
            info = "活动物体及节点树属性"
            icon='GEOMETRY_NODES'
        if ui_type == 'ShaderNodeTree':
            info = "活动物体属性"
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
                box1.label(text="已知限制: ", icon='INFO')
                split = box1.split(factor=0.5)
                split.label(text='菜单快捷键 :')
                split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)
                
                split = box1.split(factor=0.5)
                split.label(text='面板快捷键 :')
                split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)

                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_option',        toggle=True, text='隐藏节点选项')
                split.prop(scene, 'hide_Exists_socket', toggle=True, text='隐藏存在接口')
                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_Name_socket',   toggle=True, text='隐藏名称接口')
                split.prop(scene, 'rename_Attr_socket', toggle=True, text='重命名属性接口')
                split = box1.split(factor=0.5)
                split.prop(scene, 'hide_Node',          toggle=True, text='折叠节点')
                split.prop(scene, 'rename_Node',        toggle=True, text='重命名节点标签')
                split = box1.split(factor=0.5)
                split.prop(scene, 'name_prefix',        toggle=True, text='前缀')
            
            arrow_add = "TRIA_RIGHT" if not scene.show_settings else "TRIA_DOWN"
            box2 = layout.box()
            box2.scale_y = 0.9
            box2.prop(scene, "show_settings", emboss=True, icon=arrow_add)
            if scene.show_settings:
                split2 = box2.split(factor=0.4)
                split2.label(text='列表排序方式')
                split2.prop(scene, 'sort_list', text='')
                
                box2.label(text='属性列表里是否显示')
                split3 = box2.split(factor=0.05)        # 使得文本左顶格，按钮前稍微缩进
                split3.label(text="")
                split31 = split3.split(factor=0.35)
                split31.prop(scene, 'show_vertex_group', toggle=True, text='顶点组')
                split32 = split31.split(factor=0.4)
                split32.prop(scene, 'show_uv_map',       toggle=True, text='UV')
                split32.prop(scene, 'show_color_attr',   toggle=True, text='颜色属性')
                
                box2.label(text='属性列表里是否隐藏')
                split4 = box2.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.5)
                split41.prop(scene, 'only_show_used_attr', toggle=True, text='未使用属性')
                split41.prop(scene, 'hide_attr_in_group',  toggle=True, text='节点组内属性')

                split41 = box2.split(factor=0.5)
                split41.label(text='属性列表文本设置')
                split41.prop(scene, 'show_attr_domain', toggle=True, text='显示所在域')
                
                box2.label(text='查找节点设置')
                split5 = box2.split(factor=0.05)
                split5.label(text="")
                split51 = split5.split(factor=0.5)
                split51.prop(scene, 'scroll_find_node', toggle=True, text='适当缩放视图')
        
        box3 = layout.box()
        sort_attrs_and_draw_menu(box3, context, is_layout_split=True)
        
        box4 = layout.box()
        box4.operator('node.test', text="测试", icon="PIVOT_CURSOR")
        box4.operator('node.move_view_to_center', text="view_selected", icon="PIVOT_CURSOR")
        # box4.operator('view2d.scroll_up', text="上移", icon="TRIA_UP")
        # box4.operator('view2d.scroll_down', text="下移", icon="TRIA_DOWN")
        # box4.operator('view2d.scroll_left', text="左移", icon="TRIA_LEFT")
        # box4.operator('view2d.scroll_right', text="右移", icon="TRIA_RIGHT")

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
                data_type = node.data_type
                if data_type in switch_dict:
                    data_type = switch_dict[data_type]
                attr_name = node.inputs["Name"].default_value
                if attr_name == "":
                    continue
                domain_cn = get_domain_cn[node.domain]               # 还可以这样

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
            domain_info = "" + get_domain_cn[attr.domain]
            attrs_dict[attr.name] = {"data_type": data_type, "domain_info": [domain_info], "group_name":"不确定"}

def extend_dict_with_obj_data_attrs(attrs, scene, all_tree_attr_list):
    a_object = bpy.context.space_data.id
    vertex_groups = a_object.vertex_groups
    uv_layers = a_object.data.uv_layers
    color_attributes = a_object.data.color_attributes
    exclude_list = [_.name for _ in vertex_groups] + [
                    _.name for _ in uv_layers] + [
                    _.name for _ in color_attributes]
    extend_dict_with_evaluated_obj_attrs(attrs, exclude_list, a_object, all_tree_attr_list)         # 扩展已有字典

    if scene.show_vertex_group:
        for v_g in vertex_groups:
            attrs[v_g.name] = {'data_type': 'FLOAT', 'domain_info': ['点'], 
                                "group_name":"物体属性", "info": "顶点组" }
    if scene.show_uv_map:
        for uv in uv_layers:
            attrs[uv.name] = {'data_type': 'FLOAT_VECTOR', 'domain_info': ['面拐'], 
                                "group_name":"物体属性", "info": "UV贴图" }
    if scene.show_color_attr:
        for color in color_attributes:
            attrs[color.name] = {'data_type': 'FLOAT_COLOR', 'domain_info': [get_domain_cn[color.domain]], 
                                "group_name":"物体属性", "info": "颜色属性" }

def custom_sort__dict(attrs, sort_key_list):
    sorted_list = []
    for sort_key in sort_key_list:
        for key in attrs.keys():
            if attrs[key]['data_type'] == sort_key:
                sorted_list.append((key, attrs[key]))
    attrs = {k: v for k, v in sorted_list}
    return attrs

def sort_attr_dict(attrs, scene):
    sort_key_list1 = [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]
    sort_key_list2 = [ 'INT', 'BOOLEAN', 'FLOAT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]
    # 在函数内部创建了一个新的局部变量 attrs，这个变量在函数结束后就会被销毁，不会影响外部的 attrs 变量。
    attrs = {k: attrs[k] for k in sorted(attrs)}        # sorted(dict) = sorted(d1.keys())

    if scene.sort_list == '按类型排序1':
        attrs = custom_sort__dict(attrs, sort_key_list1)
    if scene.sort_list == '按类型排序1-反转':
        sort_key_list = reversed(sort_key_list1)
        attrs = custom_sort__dict(attrs, sort_key_list)
    if scene.sort_list == '按类型排序2':
        attrs = custom_sort__dict(attrs, sort_key_list2)
    # todo 完全按字符串排序
    # if scene.sort_list == '完全按字符串排序':
    #     attrs = attrs
    return attrs

def sort_attrs_and_draw_menu(layout, context, is_layout_split):
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
    
    for attr_name, attr_info in attrs.items():
        data_type = attr_info["data_type"]
        ui_type = context.area.ui_type
        if data_type not in data_types:
            continue
        if ui_type == 'ShaderNodeTree' and data_type not in shader_date_types:
            continue
        stored_domain_list = list(set(attr_info['domain_info']))
        domain_list_to_str = " | ".join(sorted(stored_domain_list, key=lambda x: domain_cn_list.index(x)))
        button_txt = attr_name + "(" + domain_list_to_str + ")" if scene.show_attr_domain else attr_name
        description = "属性所在域：" + domain_list_to_str
        # description = "属性所在域：" + domain_list_to_str + \
        #             "\n此存储命名属性节点使用个数：" + "  " \
        #             "\n此命名属性节点使用个数：" + "  "
        group_name = attr_info["group_name"]
        node_name = str(attr_info.get("node_name", "无属性")[0])
        # if len(stored_domain_list) == 1:
        if group_name != "物体属性":
            description += "\n所在节点组：" + str(group_name)
        if group_name == "物体属性":
            description += "\n类型：" + attr_info['info']
        if is_layout_split:
            split = layout.split(factor=0.9)
            op = split.operator('sna.add_node_change_name_and_type', text=button_txt,
                                    icon_value=(_icons[data_with_png[data_type]].icon_id ) )
            op.attr_name = attr_name
            op.attr_type = data_type
            op.bl_description = description
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
            # print(type(op))     # <class 'bpy.types.NODE_PIE_OT_add_node'>

class Cloud_Use_Translatation(bpy.types.Operator):
    """轻轻一点，即可切换语言，如有需要可以右键加入收藏夹"""
    bl_idname = "cloud.use_translation"
    bl_label = "切换语言"
    bl_description = "切换语言"

    def execute(self, context):
        i = bpy.context.preferences.view
        i.use_translate_interface = i.use_translate_interface ^ True
        i.use_translate_tooltips = i.use_translate_interface
        return {'FINISHED'}

class NODE_OT_View_Stored_Attribute_Node_in_edit_tree(bpy.types.Operator):
    """在edit_tree里查找节点"""
    bl_idname = "node.view_stored_attribute_node_in_edit_tree"
    bl_label = "在edit_tree里查找节点"
    bl_description = "在edit_tree里查找节点"
    node_name :   StringProperty(name='node_name', description='存储属性节点目标', default="", subtype='NONE')
    
    def execute(self, context):
        bpy.ops.node.select_all(action='DESELECT')
        # context.space_data.node_tree      # 是根节点树
        nodes = context.space_data.edit_tree.nodes
        if self.node_name == "无属性":
            return
        if context.scene.scroll_find_node:
            for i in range(50):
                bpy.ops.view2d.zoom_out()
            for i in range(40):
                bpy.ops.view2d.zoom_in()
        tar_node = nodes[self.node_name]
        tar_node.select = True
        nodes.active = tar_node
        bpy.ops.node.view_selected()

        return {'FINISHED'}

def build_group_structure(node_tree, parent_path, stored_group=[], group_path="", depth=1):
    # node_name 即为 group_node_name_path
    group_structure = {}
    group_count = {}  # 用于存储每个组名出现的次数
    for node in node_tree.nodes:
        if node.type == "GROUP":
            tree = node.node_tree
            # parent_path = parent_path + "/" + tree.name if parent_path else tree.name
            # 使用了current_path来保存当前的parent_path，而不是直接修改parent_path。
            # 这样，每次递归调用时，parent_path都不会被修改，而是在递归返回时恢复到上一层的状态。
            group_name = tree.name
            if group_name in group_count:
                group_count[group_name] += 1
            else:
                group_count[group_name] = 1
            current_path = parent_path + "/" + group_name if parent_path else group_name
            temp_group_path = group_path + "/" + node.name if group_path else node.name
            # 将子组结构和出现次数存储在字典中
            group_structure[group_name] = {
                'name': node.name,
                'count': group_count[group_name],
                "parent_path": current_path,
                "group_path": temp_group_path,
                "depth": depth
                }
            # if group_name in stored_group:  continue      # 确实没出错，但是已存过的组，就不再显示自己的结构了
            n_d = [group_name, depth]
            if n_d not in stored_group:
                stored_group.append(n_d)
            subgroup_structure = build_group_structure(tree, current_path, stored_group, temp_group_path, depth+1)
            if subgroup_structure:
                group_structure[group_name]['subgroups'] = subgroup_structure
    return group_structure

def sort_dict_by_count(path_dict):
    sorted_d = {}
    for k, v in path_dict.items():
        if 'subgroups' in v:
            v['subgroups'] = sort_dict_by_count(v['subgroups'])
        sorted_d[k] = v
    return dict(sorted(sorted_d.items(), key=lambda item: item[1]['count'], reverse=False))

def draw_group_structure(layout, path_dict):
    for group_name, data in path_dict.items():
        depth = data["depth"]
        
        space = bpy.context.space_data
        tree_name = space.edit_tree.name
        if bpy.context.area.ui_type == "ShaderNodeTree":
            tree_name = space.path.to_string.split("/")[-1]     # 'Material/NodeGroup'
        depress = (group_name == tree_name)
        
        if depth == 0:
            op = layout.operator('node.test', text=group_name, depress=depress, icon="GEOMETRY_NODES")
            op.exit_root = True
        else:
            show_count = bpy.context.scene.show_group_count
            if show_count:
                split0 = layout.split(factor=0.88)
                split1 = split0
            else:
                split1 = layout
            for i in range(depth):
                split1 = split1.split(factor=0.05)
                split1.label(text="|")
            op = split1.operator('node.test', text=group_name, depress=depress, icon="NODETREE")
            op.group_path = data["group_path"]
            op.parent_path = data["parent_path"]
            op.exit_root = False
            if show_count:
                split0.label(text=f"×{data['count']}")


        if 'subgroups' in data:
            draw_group_structure(layout, data['subgroups'])

def print_group_structure(path_dict, prefix=""):
    for group_name, data in path_dict.items():
        print(prefix + f"{group_name}  × {data['count']}")
        if 'subgroups' in data:
            temp = "|   " * (data["depth"] + 1)
            print_group_structure(data['subgroups'], prefix=temp)

def get_context_tree_name():
    space = bpy.context.space_data
    # if bpy.context.area.ui_type == "ShaderNodeTree":          还可以这样
    #     tree_name = space.path.to_string.split("/")[-1]     # 'Material/NodeGroup'
    if type(space.id) ==  bpy.types.Material:
        tree_name = space.id.name
    else:
        tree_name = space.node_tree.name
    return tree_name

def build_root_tree_structure(path_dict):
    tree_name = get_context_tree_name()
    return {tree_name: {'count': 1,
                        'name': '顶层',
                        'depth': 0,
                        'subgroups': path_dict},
                }

class TREE_PATH_PT_NPanel(bpy.types.Panel):
    bl_label = '节点组路径导航'      # 还作为在快捷键列表里名称
    bl_idname = 'TREE_PATH_PT_NPanel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Group'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        edit_tree = context.space_data.edit_tree
        # return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree'] and edit_tree
        return edit_tree

    def draw(self, context):
        draw_tree_path_panel(self, context, is_npanel=True)
        
def draw_tree_path_panel(self, context, is_npanel):
    space = context.space_data
    tree = space.node_tree
    layout = self.layout
    layout.label(text="节点组路径导航", icon="TRACKING_REFINE_FORWARDS")
    tree_name = get_context_tree_name()
    tree_path_dict = build_group_structure(tree, parent_path=tree_name, stored_group=[])
    sorted_path_dict = sort_dict_by_count(tree_path_dict)
    tree_path_dict = build_root_tree_structure(sorted_path_dict)
    # pprint(tree_path_dict)
    if is_npanel:
        split_key = layout.split(factor=0.5)
        split_key.label(text='快捷键 :')
        split_key.prop(find_user_keyconfig('唤出节点组路径面板'), 'type', text='', full_event=True)
        split_count = layout.split(factor=0.5)
        split_count.label(text='显示节点组数量 :')
        split_count.prop(context.scene, "show_group_count", text='显示数量', toggle=True)
        
    draw_group_structure(layout, tree_path_dict)


def string_width(text):
    width = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 检测中文字符
            width += 2
        else:
            width += 1
    return width

class CLOUD_OT_Draw_TREE_PATH_Panel(bpy.types.Operator):
    bl_idname = "cloud.draw_tree_path_panel"
    bl_label = "Operator"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        draw_tree_path_panel(self, context, is_npanel=False)
        
    def invoke(self, context, event):
        root_name = get_context_tree_name()
        group_name_list = [[root_name, 0]]
        build_group_structure(node_tree=context.space_data.node_tree,
                              parent_path=root_name, stored_group=group_name_list)
        # pprint(group_name_list)
        # width_list = []
        # for name, depth in group_name_list:
        #     name_width = string_width(name) + depth * 2
        #     width_list.append(name_width)
        # excess = max(width_list) - 14
        max_width = max(string_width(name)+depth*2 for name, depth in group_name_list)
        width = 200
        # excess = int(max_width - 20)
        # excess = int(max_width * 1.2 - 24)
        excess = int(max_width - 24)
        # 20 相当于width=200时的最大字符宽度
        if excess > 0:
            width += excess * 8
        return context.window_manager.invoke_popup(self, width=width)

class NODE_OT_Test(bpy.types.Operator):
    """移动视图，使视图中心变成 (0, 0)"""
    bl_idname = "node.test"
    bl_label = "节点组退回顶层"
    bl_description = "节点组退回顶层"
    exit_root : BoolProperty(name='exit_root', description='目标退到顶层', default=False)
    group_path :  StringProperty(name='group_path', description='group_node_name_path', default="", subtype='NONE')
    parent_path : StringProperty(name='parent_path', description='parent_tree_name_path', default="", subtype='NONE')
    
    
    def execute(self, context):
        exit_group_to_root()
        space = context.space_data
        # context.space_data.path.pop()
        if self.exit_root:  return {'FINISHED'}

        group_list = self.group_path.split("/")
        parent_list = self.parent_path.split("/")[:-1]       #  不加[:-1]也没问题
        # print(self.group_path)   # Group.003/Group.006/Group.001           3
        # print(self.parent_path)  # Geometry Nodes/step/应用约束/获取属性   4,多一级，for zip 循环3次，跳过最后一次
        i = 0
        for path, name in zip(parent_list, group_list):
            if i == 0 and type(space.id) ==  bpy.types.Material:
                i += 1
                nodes = bpy.data.materials[path].node_tree.nodes
            else:
                nodes = bpy.data.node_groups[path].nodes
            group_node = nodes[name]
            nodes.active = group_node
            bpy.ops.node.group_edit(exit=False)
        return {'FINISHED'}

def exit_group_to_root():
    space = bpy.context.space_data
    tree_path = space.path.to_string.split("/")[1:]     # 只留下节点组的名字，不包括根名
    for i in range(len(tree_path)):
        space.path.pop()
        # bpy.ops.node.tree_path_parent()

def proper_scroll_view():
    if bpy.context.scene.scroll_find_node:
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

class NODE_OT_View_Stored_Attribute_Node(bpy.types.Operator):
    """跳转到已命名属性节点位置"""
    bl_idname = "node.view_stored_attribute_node"
    bl_label = "框选节点"
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
        
        # bpy.ops.node.select_all(action='DESELECT')
        # reroute = nodes.new(type="NodeReroute")
        # reroute.location = tar_node.location
        # reroute.location.y += 10
        # nodes.active = reroute
        # reroute.select = True
        # bpy.ops.node.view_selected()
        # # nodes.remove(reroute)

        """ # # bpy.ops.node.select_all(action="SELECT")
        # # bpy.ops.node.view_selected()
        # # 50 次就是极限了
        # for i in range(50):
        #     bpy.ops.view2d.zoom_out()
        # for i in range(40):
        #     bpy.ops.view2d.zoom_in()
        # # for i in range(2):
        #     # bpy.ops.view2d.scroll_right()
        #     # bpy.ops.view2d.zoom_border(
        #     #         xmin= 0, xmax= 100,
        #     #         ymin= 0, ymax= 100,
        #     # ) """
        return {'FINISHED'}

class NODE_OT_Move_View_To_Center(bpy.types.Operator):
    """移动视图，使视图中心变成 (0, 0)"""
    bl_idname = "node.move_view_to_center"
    bl_label = "移动视图成正中"
    bl_description = "移动视图成正中"

    def execute(self, context):
        nodes = context.space_data.edit_tree.nodes
        # bpy.ops.node.select_all(action='DESELECT')

        # math_node = nodes.new(type="ShaderNodeMath")
        # math_node.select = True
        # nodes.active = math_node
        # math_node.location.x = -800
        
        # bpy.context.scene.frame_current = 30
        bpy.ops.node.view_selected()
        # bpy.context.space_data.view2d.offset = (100, 50)
        bpy.context.area.spaces.active.scroll = (50, -100)
        bpy.context.space_data.scroll = (50, -100)
        return {'FINISHED'}


        # areas = [area for area in bpy.context.window.screen.areas if area.type == 'NODE_EDITOR']
        # with bpy.context.temp_override(
        #         area=areas[0],
        #         region=[region for region in areas[0].regions if region.type == 'WINDOW'][0]):
        #     bpy.ops.node.view_selected()

        # # Find the node group in the material node tree
        # node = [
        #     node for node in parent_material.node_tree.nodes
        #     if node.bl_idname == 'ShaderNodeGroup' and node.node_tree.name == node_group_name
        # ][0]
        
        # # nodes.remove(math_node)
        # active_node = context.active_node
        # selected_nodes = context.selected_nodes
        # nodes = context.space_data.edit_tree.nodes
        # bpy.ops.node.select_all(action='DESELECT')

        # reroute = nodes.new(type="NodeReroute")
        # reroute.select = True
        # bpy.ops.node.view_selected()
        # nodes.remove(reroute)
        # nodes.active = active_node
        # for node in selected_nodes:
        #     node.select = True
        # return {'FINISHED'}


classes = [
    ATTRLIST_OT_Add_Node_Change_Name_Type_Hide,
    ATTRLIST_MT_Menu,
    ATTRLIST_PT_NPanel,
    TREE_PATH_PT_NPanel,
    ATTRLIST_AddonPreferences,
    Cloud_Use_Translatation,
    NODE_OT_View_Stored_Attribute_Node,
    NODE_OT_Move_View_To_Center,
    NODE_OT_Test,
    CLOUD_OT_Draw_TREE_PATH_Panel
    
]
def register():
    global _icons
    _icons = bpy.utils.previews.new()
    S = bpy.types.Scene
    bpy.types.NODE_MT_editor_menus.append(add_to_attr_list_mt_editor_menus)
    S.hide_option        = BoolProperty(name='hide_option',        description='添加时是否隐藏选项',         default=True)
    S.hide_Exists_socket = BoolProperty(name='hide_Exists_socket', description='添加时是否隐藏输出接口存在', default=True)
    S.hide_Name_socket   = BoolProperty(name='hide_Name_socket',   description='添加时是否隐藏输入接口名称', default=False)
    S.rename_Attr_socket = BoolProperty(name='rename_Attr_socket', description='添加时是否命名输出接口属性', default=True)
    S.hide_Node          = BoolProperty(name='hide_Node',          description='添加时是否折叠节点',         default=False)
    S.rename_Node        = BoolProperty(name='rename_Node',        description='添加时是否重命名节点为属性名',default=False)
    S.name_prefix        = StringProperty(name='name_prefix',      description='重命名节点时的前缀',  default="")
    S.show_set_panel     = BoolProperty(name='show_set_panel',     description='显示设置',                   default=True)
    S.scroll_find_node   = BoolProperty(name='scroll_find_node',   description='查找节点时适当缩放视图',     default=True)
    S.only_show_used_attr= BoolProperty(name='only_show_used_attr',description='只显示用到的属性,连了线的属性节点',  default=True)
    S.hide_attr_in_group = BoolProperty(name='hide_attr_in_group', description='隐藏节点组里的属性',  default=False)
    S.add_settings       = BoolProperty(name='添加节点选项',      description='',  default=False)
    S.show_settings      = BoolProperty(name='列表显示选项',      description='',  default=True)
    S.show_attr_domain   = BoolProperty(name='show_attr_domain', description='是否显示属性所在域', default=True)
    S.panel_info         = StringProperty(name='显示在面板上的描述', description='显示在面板上的描述',  default="aaa")
    
    S.show_vertex_group  = BoolProperty(name='Show_Vertex_Group',  description='是否在属性列表里显示顶点组',      default=True)
    S.show_uv_map        = BoolProperty(name='Show_UV_Map',        description='是否在属性列表里显示UV贴图',     default=False)
    S.show_color_attr    = BoolProperty(name='Show_Color_Attr',    description='是否在属性列表里显示颜色属性',     default=False)
    S.sort_list          = EnumProperty(name='列表排序方式',        description='属性列表多种排序方式', 
                                                 items=[('按类型排序1', '按类型排序1', '布尔-浮点-整数-矢量-颜色-旋转', 0, 0), 
                                                        ('按类型排序1-反转', '按类型排序1-反转', '旋转-颜色-矢量-整数-浮点-布尔', 0, 1), 
                                                        ('按类型排序2', '按类型排序2', '整数-布尔-浮点-矢量-颜色-旋转', 0, 2), 
                                                        ('完全按字符串排序', '完全按字符串排序', '首字-数字英文中文', 0, 3)])
    
    S.show_group_count   = BoolProperty(name='show_group_count', description='是否显示节点组数量', default=True)
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
    
    # kmi = km.keymap_items.new('wm.call_panel', 'THREE', 'PRESS', ctrl=False, alt=False, shift=True, repeat=False)
    # kmi.properties.name = 'TREE_PATH_PT_NPanel'
    # kmi.properties.keep_open = True
    # addon_keymaps['唤出节点组路径导航面板'] = (km, kmi)

    kmi = km.keymap_items.new('cloud.draw_tree_path_panel', 'THREE', 'PRESS',
        ctrl=False, alt=False, shift=True, repeat=False)
    addon_keymaps['唤出节点组路径面板'] = (km, kmi)


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
    del S.show_set_panel
    del S.scroll_find_node
    del S.panel_info
    del S.show_vertex_group
    del S.show_uv_map
    del S.show_color_attr
    del S.sort_list
    
    bpy.types.NODE_MT_editor_menus.remove(add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)

