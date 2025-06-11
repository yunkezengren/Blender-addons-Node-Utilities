# from translator import i18n
from . import translator
from pprint import pprint
trans = translator.i18n

bl_info = {
    "name" : "节点组输入助手(Group input helper)-添加拆分合并移动(Add Split Merge Move)",
    "author" : "一尘不染",
    "description" : "快速添加组输入节点-拆分合并移动组输入节点-快速添加组输入输出接口(Qucik add and split merge move Group Input node-Qucik add Group Input Output socket)",
    "blender" : (3, 0, 0),
    "version" : (2, 7, 0),
    "location" : "偏好设置-标题栏-N面板(Preferences-Editor Bar-N panel)",
    "warning" : "",
    "doc_url": "",
    "tracker_url": "",
    "category" : "Node"
}

import bpy
from bpy.types import Operator, Menu, Panel, AddonPreferences

from typing import List, Dict, Union
from bpy.types import (NodeTree, NodeTreeInterfaceItem, NodeTreeInterfacePanel, NodeTreeInterfaceSocket, UILayout)
from bpy.props import EnumProperty, BoolProperty, IntProperty, StringProperty
from bpy.app.translations import pgettext_iface as iface_

import bpy.utils.previews
from mathutils import Vector
import os

# _ 拆分后删除转接口
# Todo 组输入移动后找个好位置
# Todo 顶层材质不显示着色器
# Todo 着色器接口排在最上面
# Todo 看心情添加版本控制
# ____ 百度网盘更新
# Todo 合并组输入没活动节点时,新节点位置在左上角

addon_keymaps = {}
_icons = None

socket_name = [
            "Geometry",
            "Shader",
            "Boolean",
            "Float",
            "Integer",
            "Vector",
            "Color",
            "Rotation",
            "Matrix",
            "Menu",
            "String",
            "Material",
            "Object",
            "Collection",
            "Image",
            "Texture",
            ]
socket_name_cn = [
            "几何数据",
            "着色器",
            "布尔",
            "浮点",
            "整数",
            "矢量",
            "颜色",
            "旋转",
            "矩阵",
            "菜单",
            "字符串",
            "材质",
            "物体",
            "集合",
            "图像",
            "纹理",
            ]
socket_bl_socket_idname = [
            "NodeSocketGeometry",
            "NodeSocketShader",
            "NodeSocketBool",
            "NodeSocketFloat",
            "NodeSocketInt",
            "NodeSocketVector",
            "NodeSocketColor",
            "NodeSocketRotation",
            "NodeSocketMatrix",
            "NodeSocketMenu",
            "NodeSocketString",
            "NodeSocketMaterial",
            "NodeSocketObject",
            "NodeSocketCollection",
            "NodeSocketImage",
            "NodeSocketTexture",
            ]
png_list = [
            '几何数据.png',
            '着色器.png',    # Shader接口也用几何数据
            '布尔.png',
            '浮点.png',
            '整数.png',
            '矢量.png',
            '颜色.png',
            '旋转.png',
            '矩阵.png',
            '菜单.png',
            '字符串.png',
            '材质.png',
            '物体.png',
            '集合.png',
            '图像.png',
            '纹理.png',
            '空.png',
            ]
Geometry_socket_type = [   # 这里没用到
            "GEOMETRY",
            "SHADER",
            "BOOLEAN",
            "VALUE",
            "INT",
            "VECTOR",
            "RGBA",
            "ROTATION",
            "MATRIX",
            "MENU",
            "STRING",
            "MATERIAL",
            "OBJECT",
            "COLLECTION",
            "IMAGE",
            "TEXTURE",
            "CUSTOM",    # 黑色虚拟接口
            ]

inputs_png = {k:v for k, v in zip(socket_bl_socket_idname, png_list)}
# inputs_png["NodeSocketShader"] = '几何数据.png'
get_socket_name = {k:v for k, v in zip(socket_bl_socket_idname, socket_name_cn)}
# get_socket_name = {k:v for k, v in zip(socket_bl_socket_idname, zip(socket_name_cn, socket_name))}

def find_user_keyconfig(key):
    km, kmi = addon_keymaps[key]
    for item in bpy.context.window_manager.keyconfigs.user.keymaps[km.name].keymap_items:
        found_item = False
        if kmi.idname == item.idname:
            found_item = True
            for name in dir(kmi.properties):
                if not name in ["bl_rna", "rna_type"] and not name[0] == "_":
                    if not kmi.properties[name] == item.properties[name]:
                        found_item = False
        if found_item:
            return item
    print(f"Couldn't find keymap item for {key}, using addon keymap instead. This won't be saved across sessions!")
    return kmi

# INVOKE_REGION_WIN                                                2 新建节点 唤出菜单新建跟随鼠标，标题栏新建跟随
# INVOKE_DEFAULT  INVOKE_REGION_CHANNELS  INVOKE_REGION_PREVIEW    1 新建节点 唤出菜单新建跟随鼠标，标题栏新建不跟随
# INVOKE_AREA  INVOKE_SCREEN                                       报错
# EXEC_DEFAULT  EXEC_REGION_WIN  EXEC_AREA  EXEC_SCREEN  EXEC_REGION_CHANNELS  EXEC_REGION_PREVIEW  0 默认在鼠标位置新建

class GroupInputHelperAddonPreferences(AddonPreferences):
    # bl_idname = __name__
    bl_idname = __package__
    show_panel_name: BoolProperty(name='show_panel_name',  description=trans('添加组输入菜单里显示接口所属面板名字'), default=True)
    simplify_menu:   BoolProperty(name='simplify_menu', description=trans('简化<组输入合并拆分移动>菜单'), default=True)
    is_del_reroute:  BoolProperty(name='is_del_reroute', description=trans('拆分并移动组输入节点时删除转接点'), default=True)
    def draw(self, context):
        layout = self.layout
        layout.label(text=trans('标题栏和N面板显示组输入拆分'), icon="RADIOBUT_ON")

        split1 = layout.split(factor=0.65, align=True)
        split1.label(text=trans('添加组输入-菜单'))
        split1.prop(find_user_keyconfig('key_MT_Add_Group_Input'), 'type', text='', full_event=True)

        split2 = layout.split(factor=0.65, align=False)
        split2.label(text=trans('添加组输入-面板'))
        split2.prop(find_user_keyconfig('key_PT_Add_Group_Input'), 'type', text='', full_event=True)

        split3 = layout.split(factor=0.65, align=True)
        split3.label(text=trans('添加组输入输出接口'))
        split3.prop(find_user_keyconfig('key_Add_New_Group_Item'), 'type', text='', full_event=True)

        split3 = layout.split(factor=0.65, align=True)
        split3.label(text=trans('组输入合并拆分移动'))
        split3.prop(find_user_keyconfig('key_Merge_Split_Move_Group_Input'), 'type', text='', full_event=True)

        split4 = layout.split(factor=0.65)
        split4.label(text=trans('显示面板名字'))
        split4.prop(self, 'show_panel_name', text='')

        split5 = layout.split(factor=0.65)
        split5.label(text=trans('简化<组输入合并拆分移动>菜单'))
        split5.prop(self, 'simplify_menu', text='')

        split6 = layout.split(factor=0.65)
        split6.label(text=trans('拆分并移动组输入节点时删除转接点'))
        split6.prop(self, 'is_del_reroute', text='')

def get_socket_idname(socket_id):
    # 好像只3.6这样,4.0就都一种了
    if socket_id.startswith("NodeSocketFloat"):
        socket_id = "NodeSocketFloat"
    if socket_id.startswith("NodeSocketInt"):
        socket_id = "NodeSocketInt"
    if socket_id.startswith("NodeSocketVector"):
        socket_id = "NodeSocketVector"
    return socket_id

def count_input_socket_recursive(item: Union[NodeTreeInterfaceItem, NodeTreeInterfacePanel, NodeTreeInterfaceSocket]) -> int:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        return 1

    if item.item_type == 'PANEL':
        count = 0
        # 遍历面板的所有子项
        for child in item.interface_items:
            count += count_input_socket_recursive(child)
        return count

    return 0

def count_panel_depth(item: NodeTreeInterfacePanel):
    depth = 0
    while (item.parent.index != -1):
        item = item.parent  # 虽然这里更改了item,但函数外的item没变
        depth += 1
    return depth

def draw_none_socket(layout: UILayout):
    layout.separator()
    # text=trans('空')
    op = layout.operator('node.add_group_input_hide_socket', text=" ", icon_value=_icons['空.png'].icon_id)
    op.index_start = -1
    op.is_panel = False

def draw_add_group_input_hide_socket(layout: UILayout):
    # 默认时并不会真正创建 Operator 实例,把每个菜单项的信息打包成一个轻量级的数据结构,菜单跳过invoke,面板不跳
    # 在“高效的快捷模式”和“功能完整的正式模式”之间进行切换。
    layout.operator_context = 'INVOKE_DEFAULT'
    prefs = bpy.context.preferences.addons[__package__].preferences
    tree: NodeTree = bpy.context.space_data.edit_tree

    # print("*"*50)
    if bpy.app.version < (4, 0, 0):
        in_items = tree.inputs
    if bpy.app.version >= (4, 0, 0):
        in_items: List[Dict[str, Union[NodeTreeInterfaceSocket, int]]] = []
        items = tree.interface.items_tree
        index = 0   # 只算接口的序号
        for item in items:
            # i = item
            # print(f"{i.index:2} {i.position:2} {i.item_type:6} parent.index:{i.parent.index:2} {i.parent.parent==None}")
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                in_items.append({"item": item, "index": index, "len": 1})
                index += 1
            if item.item_type == 'PANEL':
                length = count_input_socket_recursive(item)
                depth = count_panel_depth(item)
                in_items.append({"item": item, "index": index, "len": length, "depth": depth})
    # pprint(in_items)
    panel_count = 0
    for in_item in in_items:
        item = in_item["item"]
        if item.item_type == 'PANEL':
            if panel_count == 0:    # 如果有面板,就把none放在面板上方
                draw_none_socket(layout)
            panel_count += 1
            layout.separator()
            if prefs.show_panel_name:
                panel_name = "●" * in_item["depth"] + item.name
                op = layout.operator('node.add_group_input_hide_socket', text=iface_(panel_name), icon="DOWNARROW_HLT")
                op.panel_name = item.name
                op.is_panel = True
        if item.item_type == 'SOCKET':
            socket_id = get_socket_idname(item.bl_socket_idname)
            input_png = inputs_png[socket_id]
            socket_name = item.name if item.name else " "  # 文本为空时,菜单里按钮不对齐
            op = layout.operator('node.add_group_input_hide_socket', text=iface_(socket_name), icon_value=(_icons[input_png].icon_id ) )
            in_panel = item.parent.index != -1
            op.is_panel = in_panel   # 不等于-1的话是面板内的接口
            if in_panel:
                op.panel_name = item.parent.name
        op.index_start = in_item["index"]
        op.index_end = in_item["index"] + in_item["len"] - 1   # 长度-1才是结束序号
        op.bl_description = item.description
        # op.bl_description = des + "\n" + str(in_item)
    if panel_count == 0:
        draw_none_socket(layout)

class NODE_OT_Add_Group_Input_Hide_Socket(Operator):
    bl_idname = "node.add_group_input_hide_socket"
    bl_label = trans("组输入隐藏节口")
    bl_options = {"REGISTER", "UNDO"}
    bl_description: StringProperty(name='btn_info', default="快捷键Shift 2 ")
    index_start:    IntProperty(name='index_start', description='', default=0)
    index_end:      IntProperty(name='index_end', description='', default=0)
    panel_name:     StringProperty(name='panel_name', description='', default="")
    is_panel:       BoolProperty(name='panel_name', description='', default=False)

    # 用于存储事件状态
    use_shift = False
    use_ctrl  = False
    use_alt   = False
    
    @classmethod
    def description(cls, context, props):
        key_des = trans("● 默认: 面板内接口根据面板重命名 \n● Ctrl: 不重命名节点 \n● Shift:根据接口重命名")
        if props:
            sk_des = props.bl_description
            socket_des = ("\n" + trans("接口描述: ") + sk_des) if sk_des else ""
            return key_des + socket_des

    def execute(self, context):
        bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='NodeGroupInput')
        node = bpy.context.active_node
        if not self.use_ctrl:
            if self.is_panel and not self.use_ctrl:
                node.label = self.panel_name
        start = self.index_start
        end = self.index_end
        index = -1
        for output in node.outputs:
            if start == -1:
                output.hide = (output.type != "CUSTOM")
            else:
                index += 1   # +1 要放到上面不能在下面，因为每次循环index+1 在下面一旦满足条件之后就一直continue
                if start == index == end and self.use_shift:
                    node.label = output.name
                if start <= index <= end:    # 当前选中的接口不隐藏
                    continue
                output.hide = True

        return {"FINISHED"}

    def invoke(self, context, event):
        self.use_shift = event.shift
        self.use_ctrl = event.ctrl
        self.use_alt = event.alt
        return self.execute(context)

def add_group_input_helper_to_node_mt_editor_menus(self, context):
    layout = self.layout
    layout.menu('NODE_MT_Add_Group_Input_Hide_Socket', text=trans('组输入'))

class NODE_MT_Add_Group_Input_Hide_Socket(Menu):
    bl_idname = "NODE_MT_Add_Group_Input_Hide_Socket"
    bl_label = trans("添加组输入")

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout
        draw_add_group_input_hide_socket(layout)

class NODE_PT_Add_Group_Input_Hide_Socket(Panel):
    # bl_category = 'Group'
    bl_category = '节点树'
    bl_label = trans('组输入拆分')
    bl_idname = 'NODE_PT_Add_Group_Input_Hide_Socket'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout
        draw_add_group_input_hide_socket(layout)

def draw_add_new_socket(layout, context):
    for socket_type, socket_name in get_socket_name.items():
        in_socket_png = inputs_png[socket_type]
        tree_type = context.space_data.edit_tree.bl_idname
        group_type = None
        a_node = context.active_node
        name = trans(socket_name)
        if a_node and a_node.select:
            group_type = a_node.bl_idname
        # print("--" * 20)
        # print(f"{tree_type = }")
        # print(f"{a_node.bl_idname = }")
        # print(f"{a_node.type = }")
        # if tree_type == "ShaderNodeTree" or group_type == "GROUP":            # 这样对于组节点就绘制多次了
        if tree_type == "ShaderNodeTree" or group_type == "ShaderNodeGroup":
            if socket_name in ["着色器", "布尔", "浮点", "整数", "矢量", "颜色"]:
                op = layout.operator('node.add_new_group_item', text=name, icon_value=(_icons[in_socket_png].icon_id ) )
                op.socket_type = socket_type
        if tree_type == "CompositorNodeTree" or group_type == "CompositorNodeGroup":
            if socket_name in ["浮点", "矢量", "颜色"]:
                op = layout.operator('node.add_new_group_item', text=name, icon_value=(_icons[in_socket_png].icon_id ) )
                op.socket_type = socket_type
        if tree_type == "GeometryNodeTree" and socket_name != "着色器":
            # if group_type == "GeometryNodeGroup" or tree_type == "GeometryNodeTree":
            op = layout.operator('node.add_new_group_item', text=name, icon_value=(_icons[in_socket_png].icon_id ) )
            op.socket_type = socket_type

class NODE_OT_Add_New_Group_Item(Operator):
    bl_idname = "node.add_new_group_item"
    bl_label = trans("添加输入输出接口")
    bl_description = trans("添加输入输出接口")
    bl_options = {"REGISTER", "UNDO"}
    socket_type: StringProperty(name='socket type', description='')

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        a_node = context.active_node
        if a_node and a_node.select and a_node.bl_idname in ["GeometryNodeGroup", "ShaderNodeGroup"]:
            tree = a_node.node_tree
        else:
            tree = context.space_data.edit_tree
        interface = tree.interface
        name = trans(get_socket_name[self.socket_type])
        if context.scene.add_input_socket:
            item = interface.new_socket(name, socket_type=self.socket_type, in_out="INPUT")
            interface.active = item
        if context.scene.add_output_socket:
            item = interface.new_socket(name, socket_type=self.socket_type, in_out="OUTPUT")
            interface.active = item
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_PT_Add_New_Group_Item(Panel):
    bl_category = '节点树'
    bl_label = trans('添加组输入输出接口')
    bl_idname = 'NODE_PT_Add_New_Group_Item'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        # name = trans(socket_name)     # 什么时候加的?会出问题
        info = trans("添加输入输出接口")
        a_node = context.active_node
        if a_node and a_node.select and a_node.type=="GROUP":
            info = trans("给活动节点组添加接口")
        layout = self.layout
        layout.label(text=trans(info), icon='NODETREE')
        split = layout.split(factor=0.5, align=True)
        split.prop(context.scene, 'add_input_socket',  text=trans('输入接口'), toggle=True, icon='BACK')
        split.prop(context.scene, 'add_output_socket', text=trans('输出接口'), toggle=True, icon='FORWARD')
        draw_add_new_socket(layout, context)

def abs_loc(node):
    return node.location + abs_loc(node.parent) if node.parent else node.location

def get_nodes_center(nodes):
    if nodes:     #  没有节点不运行
        locs = []
        for node in nodes:
            node.select = True
            if node.bl_idname == "NodeFrame": continue
            location = abs_loc(node)
            # center = location + Vector((node.width / 2, -node.dimensions.y / 2))
            center = [location.x, location.x + node.width, location.y, location.y -node.dimensions.y]
            locs.append(center)
        # print([[l[0], l[1]] for l in locs])
        # # 选中节点重心位置
        # center_x = sum(x for x, y in locs) / len(nodes); center_y = sum(y for x, y in locs) / len(nodes)
        # # 选中节点中心位置
        # center_x1 = (max(x for x, y in locs) + min(x for x, y in locs)) / 2: center_y1 = (max(y for x, y in locs) + min(y for x, y in locs)) / 2
        center_x1 = (min(l[0] for l in locs) + max(l[1] for l in locs)) / 2
        center_y1 = (max(l[2] for l in locs) + min(l[3] for l in locs)) / 2
        nodes_center = Vector((center_x1, center_y1))
        return nodes_center

def has_link(node):
    for socket in node.outputs:
        if socket.is_linked:
            return True
    return False

def is_tall(socket):
    if socket.type not in ["VECTOR", "ROTATION"]:
        return False
    if socket.hide_value:
        return False
    if socket.is_linked:
        return False
    return True

def get_in_socket_location(tar_node, tar_socket):
    has_tall = 0
    for socket in reversed(tar_node.inputs):
        has_tall += is_tall(socket)
        # print(f"{has_tall=}")
    deviation = 5 * has_tall if has_tall else 0      # 矢量接口导致dimensions.y不准?
    x = abs_loc(tar_node).x - 190
    y = abs_loc(tar_node).y - tar_node.dimensions.y + deviation + 43     # 额外加的是组输入输出接口和顶端的距离差
    soc_loc_dict = {}    # socket_location_dictionary
    for socket in reversed(tar_node.inputs):
        if socket.hide or not socket.enabled:
            continue
        y_offset = 21.9   # 接口之间常规距离
        vec_offset = 60   # 矢量接口距离
        y += y_offset + vec_offset * is_tall(socket)
        soc_loc_dict[socket] = y
    return Vector((x, soc_loc_dict[tar_socket]))

class NODE_OT_Merge_Group_Input_Socket(Operator):
    bl_idname = "node.merge_group_input_socket"
    bl_label = trans("合并组输入接口")
    bl_description = trans("选中组输入节点,合并接口到一个组输入节点")
    bl_options = {"REGISTER", "UNDO"}
    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        a_node = nodes.active
        # nodes = context.selected_nodes
        # a_node = context.active_node
        links = tree.links
        list_group = []
        for node in nodes:
            if node.bl_idname == "NodeGroupInput" and node.select:
                list_group.append(node)
        if len(list_group) >= 2:
            condition = a_node and a_node.bl_idname == "NodeGroupInput" and a_node.select
            if condition:
                target_group = a_node
            else:
                target_group = list_group[0]
                nodes_center = get_nodes_center(list_group)
            group_id = {socket.identifier: socket for socket in target_group.outputs}
            for node in list_group:
                if node != target_group:
                    for out_socket in node.outputs:
                        tar_socket = group_id[out_socket.identifier]
                        if out_socket.is_linked:
                            for link in out_socket.links:
                                links.new(tar_socket, link.to_socket)
                        if out_socket.hide == False:
                            tar_socket.hide = False
                    nodes.remove(node)    # 没出错,不确定这样删会不会出错(删的是nodes里的)
            if not condition:
                tar_loc = target_group.dimensions
                target_group.location = nodes_center - Vector((tar_loc.x / 2,  - tar_loc.y))
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

def merge_group_input_linked(selected_nodes, active_node, loc_at_max_y=False):
    tree = bpy.context.space_data.edit_tree
    nodes = tree.nodes
    links = tree.links
    list_group = []
    list_group_loc_y = []
    for node in selected_nodes:
        if node.bl_idname == "NodeGroupInput":
            list_group.append(node)
            list_group_loc_y.append(abs_loc(node).y)
    list_group_loc_y.sort()
    y_max = list_group_loc_y[-1]
    if len(list_group) == 1:
        return None
    condition = active_node and active_node.bl_idname == "NodeGroupInput" and active_node.select
    if condition:
        target_group = active_node
    else:
        target_group = list_group[0]
        nodes_center = get_nodes_center(list_group)
    group_id = {out_socket.identifier: out_socket for out_socket in target_group.outputs}
    for node in list_group:
        if node != target_group:
            for out_socket in node.outputs:
                if out_socket.is_linked:
                    for link in out_socket.links:
                        links.new(group_id[out_socket.identifier], link.to_socket)
            nodes.remove(node)    # 没出错,不确定这样删会不会出错
    if not condition:
        tar_loc = target_group.dimensions
        target_group.location = nodes_center - Vector((tar_loc.x / 2, - tar_loc.y))
    if loc_at_max_y:
        target_group.location.y = y_max
    for soc in target_group.outputs:
        soc.hide = True
    return target_group

class NODE_OT_Merge_Group_Input_Linked(Operator):
    bl_idname = "node.merge_group_input_linked"
    bl_label = trans("合并组输入连线")
    bl_description = trans("选中组输入节点,合并连线到一个组输入节点,隐藏未连线节口")
    bl_options = {"REGISTER", "UNDO"}
    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        selected_nodes = context.selected_nodes
        active_node = context.active_node
        merge_group_input_linked(selected_nodes, active_node)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Hide_Group_Input_Sockets(Operator):
    bl_idname = "node.hide_group_input_sockets"
    bl_label = trans("隐藏未使用组输入接口")
    bl_description = trans("隐藏所有组输入节点未使用的接口")
    bl_options = {"REGISTER", "UNDO"}
    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        nodes = context.space_data.edit_tree.nodes
        for node in nodes:
            if node.bl_idname == "NodeGroupInput":
                for soc in node.outputs:
                    soc.hide = True

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Split_Group_Input_Socket(Operator):
    bl_idname = "node.split_group_input_socket"
    bl_label = trans("拆分组输入接口")
    bl_description = trans("选中组输入节点,每一个接口拆分成一个节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        i = 0
        for node in selected_nodes:
            if node.bl_idname == "NodeGroupInput" and node.select:
                i = -1
                for out_soc in node.outputs:
                    if not out_soc.hide and out_soc.enabled and out_soc.bl_idname != "NodeSocketVirtual":
                        # if out_soc.is_linked:
                        i += 1
                        group_node = nodes.new('NodeGroupInput')
                        group_node.location = abs_loc(node)
                        group_node.location.y = abs_loc(node).y - 60 * i
                        group_id = {socket.identifier: socket for socket in group_node.outputs}
                        for link in out_soc.links:
                            links.new(group_id[out_soc.identifier], link.to_socket)
                        for new_out_soc in group_node.outputs:
                            if new_out_soc.identifier != out_soc.identifier:
                                new_out_soc.hide = True
                nodes.remove(node)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Split_All_Group_Input_Socket(Operator):
    bl_idname = "node.split_all_group_input_socket"
    bl_label = trans("完全拆分")
    bl_description = trans("选中组输入节点,每一个接口/连线拆分成一个节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        i = 0
        for node in selected_nodes:
            if node.bl_idname == "NodeGroupInput" and node.select:
                i = -1
                for out_soc in node.outputs:
                    if not out_soc.hide and out_soc.enabled and out_soc.bl_idname != "NodeSocketVirtual":
                        link_count = len(out_soc.links)
                        soc_links = out_soc.links if out_soc.links else range(1)
                        for link in soc_links:
                            if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                                continue
                            i += 1
                            group_node = nodes.new('NodeGroupInput')
                            group_node.location = abs_loc(node)
                            group_node.location.y = abs_loc(node).y - 60 * i
                            group_id = {socket.identifier: socket for socket in group_node.outputs}
                            if link_count:
                                links.new(group_id[out_soc.identifier], link.to_socket)
                            for new_out_soc in group_node.outputs:
                                if new_out_soc.identifier != out_soc.identifier:
                                    new_out_soc.hide = True
                nodes.remove(node)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Split_All_And_Move(Operator):
    bl_idname = "node.split_all_and_move"
    bl_label = trans("完全拆分并移动")
    bl_description = trans("选中组输入节点,每一个连线拆分成一个节点,并移动到连向接口(to_socket)的附近")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        is_del_reroute = context.preferences.addons[__package__].preferences.is_del_reroute
        i = 0
        for node in selected_nodes:
            if node.bl_idname == "NodeGroupInput" and node.select and has_link(node):
                i = -1
                for out_soc in node.outputs:
                    if not out_soc.hide and out_soc.enabled and out_soc.bl_idname != "NodeSocketVirtual":
                        # 删掉组输入输出接口后面连的所有转接点
                        if is_del_reroute and out_soc.links:
                            for link in out_soc.links:
                                delete_reroute(link, nodes, links, out_soc)
                        link_count = len(out_soc.links)
                        soc_links = out_soc.links if out_soc.links else range(1)
                        for link in soc_links:
                            if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                                continue
                            i += 1
                            if link_count:         # is_linked:
                                group_node = nodes.new('NodeGroupInput')
                                # group_node.location = node.location
                                # group_node.location.y = node.location.y - 80 * i
                                group_id = {socket.identifier: socket for socket in group_node.outputs}
                                spec_in_socket = group_id[out_soc.identifier]

                                links.new(spec_in_socket, link.to_socket)
                                to_node = spec_in_socket.links[0].to_node
                                to_socket = spec_in_socket.links[0].to_socket
                                group_node.location = get_in_socket_location(to_node, to_socket)
                            for new_out_soc in group_node.outputs:
                                if new_out_soc.identifier != out_soc.identifier:
                                    new_out_soc.hide = True
                nodes.remove(node)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

def delete_reroute(link, nodes, links, out_socket):
    if link.to_node.type == "REROUTE":
        reroute = link.to_node
        for re_link in reroute.outputs[0].links:
            links.new(out_socket, re_link.to_socket)
            delete_reroute(re_link, nodes, links, out_socket)
        nodes.remove(reroute)
""" # 多两行的版本
def delete_reroute(link, nodes, links, out_socket):
    if link.to_node.type == "REROUTE":
        reroute = link.to_node
        re_links = reroute.outputs[0].links
        for re_link in re_links:
            tar_socket = re_link.to_socket
            links.new(out_socket, tar_socket)
            delete_reroute(re_link, nodes, links, out_socket)
        nodes.remove(reroute)
 """

def split_all_and_merge_move(context, is_pre_merge=False):
    selected_nodes = context.selected_nodes
    if is_pre_merge:
        merge_group_input_linked(selected_nodes, context.active_node)
    selected_nodes = context.selected_nodes
    tree = context.space_data.edit_tree
    nodes = tree.nodes
    links = tree.links
    is_del_reroute = context.preferences.addons[__package__].preferences.is_del_reroute
    i = 0
    to_node_with_inputs = {}    # to_node_with_group_inputs节点输入接口的组输入数量
    for node in selected_nodes:
        if node.bl_idname == "NodeGroupInput" and node.select and has_link(node):
            i = -1
            for out_soc in node.outputs:
                if not out_soc.hide and out_soc.enabled and out_soc.bl_idname != "NodeSocketVirtual":
                    # 删掉组输入输出接口后面连的所有转接点
                    if is_del_reroute and out_soc.links:
                        for link in out_soc.links:
                            delete_reroute(link, nodes, links, out_soc)
                    link_count = len(out_soc.links)
                    # soc_links = out_soc.links if out_soc.links else range(1)
                    if out_soc.links:
                        soc_links = out_soc.links
                    else:
                        continue
                    for link in soc_links:
                        if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                            continue
                        i += 1
                        group_node = nodes.new('NodeGroupInput')
                        # group_node.location = node.location; group_node.location.y = node.location.y - 80 * i
                        group_id = {socket.identifier: socket for socket in group_node.outputs}
                        spec_in_socket = group_id[out_soc.identifier]
                        if link_count:         # is_linked:
                            links.new(spec_in_socket, link.to_socket)
                            to_node = spec_in_socket.links[0].to_node
                            to_socket = spec_in_socket.links[0].to_socket
                            if to_node in to_node_with_inputs:
                                to_node_with_inputs[to_node].append(group_node)
                            else:
                                to_node_with_inputs[to_node] = [group_node]
                            group_node.location = get_in_socket_location(to_node, to_socket)
                        for new_out_soc in group_node.outputs:
                            if new_out_soc.identifier != out_soc.identifier:
                                new_out_soc.hide = True
            nodes.remove(node)

    for node_list in to_node_with_inputs.values():
        if len(node_list) > 1:
            # 不知道为什么合并后会偏移md
            merge_group_input_linked(node_list, None, loc_at_max_y=True).location.x = abs_loc(node_list[0]).x

class NODE_OT_Split_All_And_Merge_Move(Operator):
    bl_idname = "node.split_all_and_merge_move"
    bl_label = trans("拆分并移动合并")
    bl_description = trans("选中组输入节点,每一个连线拆分成一个节点,并移动到连向接口(to_socket)的附近,并合并连到一个节点上的组输入节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        split_all_and_merge_move(context)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Merge_Node_And_Split_Merge_Move(Operator):
    bl_idname = "node.merge_node_and_split_merge_move"
    bl_label = trans("合并节点并拆分")
    bl_description = trans("选中组输入节点,先合并成一个节点,再拆分接口,并移动到连向接口(to_socket)的附近,并合并连到一个节点上的组输入节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        split_all_and_merge_move(context, is_pre_merge=True)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_OT_Split_Group_Input_Linked(Operator):
    bl_idname = "node.split_group_input_linked"
    bl_label = trans("拆分组输入")
    bl_description = trans("选中组输入节点,隐藏未连线节口后,拆分组输入接口")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        # for node in tree.nodes:   # nodes 会包括后面新添加的节点
        #     for out_socket in node.outputs:
        #         if out_socket.is_linked:
        #             group_node = nodes.new('NodeGroupInput')
        #             for link in out_socket.links:
        #                 links.new(link.from_socket, link.to_socket)  # 新建的节点连上线，后面被判定is_linked继续拆分崩溃
        i = 0
        for node in selected_nodes:
            if node.bl_idname == "NodeGroupInput" and node.select:
                i = -1
                for out_socket in node.outputs:
                    if out_socket.is_linked:
                        i += 1
                        group_node = nodes.new('NodeGroupInput')
                        group_node.location = abs_loc(node)
                        group_node.location.y = abs_loc(node).y - 60 * i
                        group_id = {out_socket1.identifier: out_socket1 for out_socket1 in group_node.outputs}
                        for link in out_socket.links:
                            links.new(group_id[out_socket.identifier], link.to_socket)
                        for out_soc in group_node.outputs:
                            out_soc.hide = True
                nodes.remove(node)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class NODE_MT_Merge_Split_Move_Group_Input(Menu):
    bl_idname = "NODE_MT_Merge_Split_Move_Group_Input"
    bl_label = trans("组输入拆分合并移动")

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences.addons[__package__].preferences
        if bpy.app.version < (4, 0, 0):
            # layout.operator('node.merge_node_and_split_merge_move', text=trans('合并节点并拆分'), icon="ANIM")
            # layout.separator()
            layout.operator('node.split_all_and_merge_move', text=trans('拆分并移动合并'), icon="ANIM")
            layout.operator('node.split_all_and_move', text=trans('完全拆分并移动'), icon="ANIM")
            layout.operator('node.split_all_group_input_socket', text=trans('完全拆分'), icon="")
            layout.separator()
            layout.operator('node.merge_group_input_linked',  text=trans('合并组输入连线'), icon="")
            layout.operator('node.split_group_input_linked', text=trans('拆分组输入连线'), icon="")
            layout.separator()
            layout.operator('node.merge_group_input_socket', text=trans('合并组输入接口'), icon="")
            layout.operator('node.split_group_input_socket', text=trans('拆分组输入接口'), icon="")
        else:
            # 艹,原来是重复了,<合并节点并拆分>是先合并选中组输入节点,再拆分,多此一举.
            # if not prefs.simplify_menu:
            #     layout.operator('node.merge_node_and_split_merge_move', text=trans('合并节点并拆分'), icon="ANIM")
            # layout.separator()
            layout.operator('node.split_all_and_merge_move', text=trans('拆分并移动合并'), icon="ANIM")
            layout.operator('node.split_all_and_move', text=trans('完全拆分并移动'), icon="ANIM")
            if not prefs.simplify_menu:
                layout.operator('node.split_all_group_input_socket', text=trans('完全拆分'), icon="SPLIT_HORIZONTAL")
            layout.separator()
            layout.operator('node.merge_group_input_linked',  text=trans('合并组输入连线'), icon="AREA_JOIN")
            layout.operator('node.split_group_input_linked', text=trans('拆分组输入连线'), icon="SPLIT_HORIZONTAL")
            layout.separator()
            if not prefs.simplify_menu:
                layout.operator('node.merge_group_input_socket', text=trans('合并组输入接口'), icon="AREA_JOIN")
                layout.operator('node.split_group_input_socket', text=trans('拆分组输入接口'), icon="SPLIT_HORIZONTAL")
                layout.separator()
            layout.operator('node.hide_group_input_sockets', text=trans('隐藏未使用组输入接口'), icon="DECORATE")

classes = [
    NODE_OT_Add_Group_Input_Hide_Socket,
    NODE_MT_Add_Group_Input_Hide_Socket,
    NODE_PT_Add_Group_Input_Hide_Socket,
    NODE_OT_Add_New_Group_Item,
    NODE_PT_Add_New_Group_Item,
    NODE_OT_Merge_Group_Input_Socket,
    NODE_OT_Split_Group_Input_Socket,
    NODE_OT_Split_All_Group_Input_Socket,
    NODE_OT_Split_All_And_Move,
    NODE_OT_Merge_Group_Input_Linked,
    NODE_OT_Split_Group_Input_Linked,
    NODE_OT_Split_All_And_Merge_Move,
    NODE_OT_Hide_Group_Input_Sockets,
    NODE_OT_Merge_Node_And_Split_Merge_Move,
    NODE_MT_Merge_Split_Move_Group_Input,
    GroupInputHelperAddonPreferences,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    for png in png_list:
        _icons.load(png, os.path.join(os.path.dirname(__file__), 'icons', png), "IMAGE")

    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.NODE_MT_editor_menus.append(add_group_input_helper_to_node_mt_editor_menus)
    bpy.types.Scene.add_input_socket  = BoolProperty(name='add_input_socket',  description='trans(同时添加输入接口)', default=True)
    bpy.types.Scene.add_output_socket = BoolProperty(name='add_output_socket', description='trans(同时添加输出接口)', default=False)

    # 第一种
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new('wm.call_menu', 'ONE', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'NODE_MT_Add_Group_Input_Hide_Socket'
    addon_keymaps['key_MT_Add_Group_Input'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_panel', 'ONE', 'PRESS', ctrl=True, alt=True, shift=True, repeat=False)
    kmi.properties.name = 'NODE_PT_Add_Group_Input_Hide_Socket'
    kmi.properties.keep_open = True
    addon_keymaps['key_PT_Add_Group_Input'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_panel', 'ONE', 'PRESS', ctrl=True, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'NODE_PT_Add_New_Group_Item'
    kmi.properties.keep_open = True
    addon_keymaps['key_Add_New_Group_Item'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_menu', 'ONE', 'PRESS', ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'NODE_MT_Merge_Split_Move_Group_Input'
    addon_keymaps['key_Merge_Split_Move_Group_Input'] = (km, kmi)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        # print(kmi)
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.types.NODE_MT_editor_menus.remove(add_group_input_helper_to_node_mt_editor_menus)
    del bpy.types.Scene.add_input_socket
    del bpy.types.Scene.add_output_socket

    for i in classes:
        bpy.utils.unregister_class(i)
