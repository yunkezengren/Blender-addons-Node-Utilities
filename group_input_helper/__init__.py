bl_info = {
    "name" : "节点组输入助手(Group input helper)-添加拆分合并移动(Add Split Merge Move)",
    "author" : "一尘不染",
    "description" : "快速添加组输入节点-拆分合并移动组输入节点-快速添加组输入输出接口(Qucik add and split merge move Group Input node-Qucik add Group Input Output socket)",
    "blender" : (3, 0, 0),
    "version" : (2, 9, 2),
    "category" : "Node"
}

import bpy, os
import bpy.utils.previews
from bpy.types import (Operator, Menu, Panel, AddonPreferences, Context, UILayout, Node, Nodes, NodeSocket, NodeTree, NodeLinks,
                       NodeTreeInterfaceItem, NodeTreeInterfacePanel, NodeTreeInterfaceSocket, )
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.app.translations import pgettext_iface as iface_
from mathutils import Vector as Vec2

from .translator import i18n as trans
from typing import Union
from ctypes import c_float, c_void_p

# Todo 要让支持的接口类型更通用啊,而不是自己判断
# Todo 很久之前写的了,层层嵌套的地方需要优化, 拆分移动合并要考虑复用代码
# Todo 组输入移动后找个好位置
# Todo 顶层材质不显示着色器
# Todo 合并组输入时适当重命名
# Todo 拆分组输入,增加重命名/折叠/调整宽度选项
# todo 显示组输入 是否灰显或隐藏
# todo 学习节点树仓库的 i18n

addon_keymaps = {}
_icons = None

sk_name_cn = [
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
    # "纹理",
    "捆包",
    "闭包",
]

sk_idnames = [
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
    # "NodeSocketTexture",
    "NodeSocketBundle",
    "NodeSocketClosure",
]

sk_icons = [
    "NODE_SOCKET_GEOMETRY",
    "NODE_SOCKET_SHADER",
    "NODE_SOCKET_BOOLEAN",
    "NODE_SOCKET_FLOAT",
    "NODE_SOCKET_INT",
    "NODE_SOCKET_VECTOR",
    "NODE_SOCKET_RGBA",
    "NODE_SOCKET_ROTATION",
    "NODE_SOCKET_MATRIX",
    "NODE_SOCKET_MENU",
    "NODE_SOCKET_STRING",
    "NODE_SOCKET_MATERIAL",
    "NODE_SOCKET_OBJECT",
    "NODE_SOCKET_COLLECTION",
    "NODE_SOCKET_IMAGE",
    # "NODE_SOCKET_TEXTURE",
    "NODE_SOCKET_BUNDLE",
    "NODE_SOCKET_CLOSURE",
]

png_list = [
    '几何数据.png',
    '着色器.png',  # Shader接口也用几何数据
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
    '空.png',
]

sk_idname_to_png_name = {k:v for k, v in zip(sk_idnames, png_list)}
sk_idname_to_cn = {k:v for k, v in zip(sk_idnames, sk_name_cn)}
sk_idname_to_icon = {k:v for k, v in zip(sk_idnames, sk_icons)}

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

        split3 = layout.split(factor=0.65, align=True)
        split3.label(text=trans('组输入助手-面板'))
        split3.prop(find_user_keyconfig('NODE_PT_Group_Input_Helper'), 'type', text='', full_event=True)

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

def pref() -> GroupInputHelperAddonPreferences:
    assert __package__ is not None      # 断言 __package__ 在这里不可能是 None,因为 __getitem__ 接受的 key 只能是 int 或 str
    return bpy.context.preferences.addons[__package__].preferences

def ui_scale():
    return bpy.context.preferences.system.dpi / 72      # 类似于prefs.view.ui_scale, 但是不同的显示器dpi不一样吗

def sk_idname_版本兼容(socket_id: str):
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
    op = layout.operator(NODE_OT_Add_Hided_Socket_Group_Input.bl_idname, text=" ", icon_value=_icons['空.png'].icon_id)
    op.index_start = -1
    op.in_panel = False

class BaseOperator(Operator):
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area.type == "NODE_EDITOR"

class NODE_OT_Add_Hided_Socket_Group_Input(BaseOperator):
    bl_idname = "node.add_hided_socket_group_input"
    bl_label = trans("组输入隐藏节口")
    bl_description: StringProperty(name='btn_info', default="快捷键Shift 2 ")
    index_start:    IntProperty(name='index_start', description='', default=0)
    index_end:      IntProperty(name='index_end', description='', default=0)
    panel_name:     StringProperty(name='panel_name', description='', default="")
    in_panel:       BoolProperty(name='panel_name', description='', default=False)
    is_panel:       BoolProperty(default=False)

    use_shift: bool
    use_ctrl : bool
    use_alt  : bool

    @classmethod
    def description(cls, context, props):
        extra_info = "" if props.is_panel else "\n● Shift:根据接口重命名"
        key_des = trans("● 默认: 根据面板重命名 \n● Ctrl: 不重命名节点" + extra_info)
        if props:
            sk_des = props.bl_description
            socket_des = ("\n" + trans("接口描述: ") + sk_des) if sk_des else ""
            return key_des + socket_des

    def invoke(self, context, event):
        self.use_shift = event.shift
        self.use_ctrl = event.ctrl
        self.use_alt = event.alt
        return self.execute(context)

    def execute(self, context):
        bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='NodeGroupInput')
        node = bpy.context.active_node
        if not self.use_ctrl:
            if self.in_panel and not self.use_ctrl:
                node.label = iface_(self.panel_name)
        start = self.index_start
        end = self.index_end
        index = -1
        for output in node.outputs:
            if start == -1:
                output.hide = (output.type != "CUSTOM")
            else:
                index += 1   # +1 要放到上面不能在下面，因为每次循环index+1 在下面一旦满足条件之后就一直continue
                if start == index == end and self.use_shift:
                    node.label = iface_(output.name)
                if start <= index <= end:    # 当前选中的接口不隐藏
                    continue
                output.hide = True

        return {"FINISHED"}

def add_group_input_helper_to_node_mt_editor_menus(self: Menu, context: Context):
    layout = self.layout
    layout.menu('NODE_MT_Add_Hided_Socket_Group_Input', text=trans('组输入'))

class NODE_MT_Add_Hided_Socket_Group_Input(Menu):
    bl_idname = "NODE_MT_Add_Hided_Socket_Group_Input"
    bl_label = trans("添加组输入节点")

    def draw(self, context):
        layout = self.layout
        draw_add_hided_socket_group_input(layout)

def draw_add_hided_socket_group_input(layout: UILayout):
    # 默认时并不会真正创建 Operator 实例,把每个菜单项的信息打包成一个轻量级的数据结构,菜单跳过invoke,面板不跳
    # 在“高效的快捷模式”和“功能完整的正式模式”之间进行切换。
    layout.operator_context = 'INVOKE_DEFAULT'
    prefs =  pref()
    tree: NodeTree = bpy.context.space_data.edit_tree

    if bpy.app.version < (4, 0, 0):
        in_items = tree.inputs
    if bpy.app.version >= (4, 0, 0):
        in_items: list[dict[str, Union[NodeTreeInterfaceSocket, int]]] = []
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
    panel_count = 0
    for in_item in in_items:
        item = in_item["item"]
        op: NODE_OT_Add_Hided_Socket_Group_Input = None
        if item.item_type == 'PANEL':
            if panel_count == 0:    # 如果有面板,就把none放在面板上方
                draw_none_socket(layout)
            panel_count += 1
            layout.separator()
            if prefs.show_panel_name:
                panel_name = "●" * in_item["depth"] + " " + item.name
                op = layout.operator(NODE_OT_Add_Hided_Socket_Group_Input.bl_idname, text=iface_(panel_name), icon="DOWNARROW_HLT")
                op.panel_name = item.name
                op.in_panel = True
                op.is_panel = True
        if item.item_type == 'SOCKET':
            socket_name = item.name if item.name else " "  # 文本为空时,菜单里按钮不对齐
            if bpy.app.version >= (4, 5, 0):
                op = layout.operator(NODE_OT_Add_Hided_Socket_Group_Input.bl_idname,
                                     text=iface_(socket_name),
                                     icon=sk_idname_to_icon[item.bl_socket_idname])
            else:
                socket_id = sk_idname_版本兼容(item.bl_socket_idname)
                input_png = sk_idname_to_png_name[socket_id]
                op = layout.operator(NODE_OT_Add_Hided_Socket_Group_Input.bl_idname,
                                     text=iface_(socket_name),
                                     icon_value=(_icons[input_png].icon_id))
            in_panel = item.parent.index != -1
            op.in_panel = in_panel   # 不等于-1的话是面板内的接口
            if in_panel:
                op.panel_name = item.parent.name
        op.index_start = in_item["index"]
        op.index_end = in_item["index"] + in_item["len"] - 1   # 长度-1才是结束序号
        op.bl_description = item.description
        # op.bl_description = des + "\n" + str(in_item)
    if panel_count == 0:
        draw_none_socket(layout)

# ==================================================================================================
class NODE_OT_Add_New_Group_Item(BaseOperator):
    bl_idname = "node.add_new_group_item"
    bl_label = trans("添加输入输出接口")
    bl_description = trans("添加输入输出接口")
    socket_type: StringProperty(name='socket type', description='')

    def execute(self, context):
        a_node = context.active_node
        if a_node and a_node.select and a_node.type == "GROUP":
            tree = a_node.node_tree
        else:
            tree = context.space_data.edit_tree
        interface = tree.interface
        name = trans(sk_idname_to_cn[self.socket_type])
        if context.scene.add_input_socket:
            item = interface.new_socket(name, socket_type=self.socket_type, in_out="INPUT")
            interface.active = item
        if context.scene.add_output_socket:
            item = interface.new_socket(name, socket_type=self.socket_type, in_out="OUTPUT")
            interface.active = item
        return {"FINISHED"}

class NODE_PT_Group_Input_Helper(Panel):
    bl_category = "Group"
    bl_label = trans('组输入助手')
    bl_idname = 'NODE_PT_Group_Input_Helper'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0
    @classmethod
    def poll(cls, context):
        a_node = context.active_node
        # todo 合成器和材质里顶层无效,要显示提示信息
        return context.space_data.edit_tree

    def draw(self, context):
        layout = self.layout
        # layout.label(text=trans("1"), icon='NODETREE')

        header, body = layout.panel("group_helper_1")
        info = trans("添加输入输出接口")
        a_node = context.active_node
        icons = ['FORWARD', 'BACK']
        if a_node and a_node.select and a_node.type == "GROUP":
            icons.reverse()
            info = trans("给活动节点组添加接口")
        header.label(text=trans(info))
        if body:
            split = body.split(factor=0.5, align=True)
            split.prop(context.scene, 'add_input_socket',  text=trans('输入接口'), toggle=True, icon=icons[0])
            split.prop(context.scene, 'add_output_socket', text=trans('输出接口'), toggle=True, icon=icons[1])
            draw_add_new_socket(body, context)

        header, body = layout.panel("group_helper_2", default_closed=True)
        header.label(text=trans("添加组输入节点"))
        if body:
            draw_add_hided_socket_group_input(body)

def draw_add_new_socket(layout: UILayout, context: Context):
    for sk_idname, socket_name in sk_idname_to_cn.items():
        tree_type = context.space_data.edit_tree.bl_idname
        name = trans(socket_name)
        base_type = ["浮点", "整数", "布尔", "矢量", "颜色"]
        if tree_type == "ShaderNodeTree" and socket_name not in ["着色器"] + base_type + ["菜单", "捆包", "闭包"]:
            continue
        if tree_type == "CompositorNodeTree" and socket_name not in base_type + ["菜单"]:
            continue
        if tree_type == "GeometryNodeTree" and socket_name == "着色器":
            continue
        if bpy.app.version < (5, 0, 0) and socket_name in ["捆包", "闭包"]:
            continue
        if bpy.app.version >= (4, 5, 0):
            op = layout.operator('node.add_new_group_item', text=name, icon=sk_idname_to_icon[sk_idname])
        else:
            in_socket_png = sk_idname_to_png_name[sk_idname]
            op = layout.operator('node.add_new_group_item', text=name, icon_value=(_icons[in_socket_png].icon_id))
        op.socket_type = sk_idname

# ==================================================================================================
def nd_abs_loc(node: Node):
    return node.location + nd_abs_loc(node.parent) if node.parent else node.location

def get_nodes_target_loc(nodes: Nodes):
    locs = []
    for node in nodes:
        if node.bl_idname == "NodeFrame": continue
        location = nd_abs_loc(node)
        center = [location.x, location.y, location.y - node.dimensions.y]
        locs.append(center)
    min_x1 = min(l[0] for l in locs)
    center_y1 = (max(l[1] for l in locs) + min(l[2] for l in locs)) / 2
    return Vec2((min_x1, center_y1))

def has_link(node: Node):
    for socket in node.outputs:
        if socket.is_linked:
            return True
    return False

def sk_location(socket: NodeSocket):
    try:
        offset = 520
        if bpy.app.version >= (5, 1, 0):
            offset = 456  # 520-64  5.1移除了short_label https://projects.blender.org/blender/blender/pulls/148940/files
        return Vec2((c_float * 2).from_address(c_void_p.from_address(socket.as_pointer() + offset).value + 24))
    except:
        raise Exception("获取接口位置函数出错")

def move_nd_to_sk(input_nd: Node, to_socket: NodeSocket, offset: int):
    input_nd.location = sk_location(to_socket) / ui_scale()
    input_nd.location.x -= 180
    input_nd.location.y += offset
    input_nd.parent = to_socket.node.parent

class NODE_OT_Merge_Group_Input_Socket(BaseOperator):
    bl_idname = "node.merge_group_input_socket"
    bl_label = trans("合并组输入接口")
    bl_description = trans("选中组输入节点,合并接口到一个组输入节点")

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
                nodes_center = get_nodes_target_loc(list_group)
            group_id = {socket.identifier: socket for socket in target_group.outputs}
            for node in list_group:
                if node != target_group:
                    for sk_out in node.outputs:
                        tar_socket = group_id[sk_out.identifier]
                        if sk_out.is_linked:
                            for link in sk_out.links:
                                links.new(tar_socket, link.to_socket)
                        if sk_out.hide == False:
                            tar_socket.hide = False
                    nodes.remove(node)    # 没出错,不确定这样删会不会出错(删的是nodes里的)
            if not condition:
                tar_loc = target_group.dimensions
                target_group.location = nodes_center - Vec2((0,  - tar_loc.y))
        return {"FINISHED"}

def merge_group_input_linked(selected_nodes: Nodes, active_node: Node, loc_at_max_y=False):
    tree: NodeTree = bpy.context.space_data.edit_tree
    nodes = tree.nodes
    links = tree.links
    list_group = []
    list_group_loc_y = []
    for node in selected_nodes:
        if node.bl_idname != "NodeGroupInput": continue
        node.parent = None
        list_group.append(node)
        list_group_loc_y.append(nd_abs_loc(node).y)
    list_group_loc_y.sort()
    y_max = list_group_loc_y[-1]
    if len(list_group) == 1:
        return None
    condition = active_node and active_node.bl_idname == "NodeGroupInput" and active_node.select
    if condition:
        target_group = active_node
    else:
        target_group = list_group[0]
        nodes_center = get_nodes_target_loc(list_group)
    group_id = {sk_out.identifier: sk_out for sk_out in target_group.outputs}
    for node in list_group:
        if node == target_group: continue
        for sk_out in node.outputs:
            if not sk_out.is_linked: continue
            for link in sk_out.links:
                links.new(group_id[sk_out.identifier], link.to_socket)
        nodes.remove(node)    # 没出错,不确定这样删会不会出错
    if not condition:
        tar_loc = target_group.dimensions
        target_group.location = nodes_center - Vec2((0, -tar_loc.y))
    if loc_at_max_y:
        target_group.location.y = y_max
    for soc in target_group.outputs:
        soc.hide = True
    return target_group

class NODE_OT_Merge_Group_Input_Linked(BaseOperator):
    bl_idname = "node.merge_group_input_linked"
    bl_label = trans("合并组输入连线")
    bl_description = trans("选中组输入节点,合并连线到一个组输入节点,隐藏未连线节口")

    def execute(self, context):
        selected_nodes = context.selected_nodes
        active_node = context.active_node
        merge_group_input_linked(selected_nodes, active_node)
        return {"FINISHED"}

class NODE_OT_Split_Group_Input_Socket(BaseOperator):
    bl_idname = "node.split_group_input_socket"
    bl_label = trans("拆分组输入接口")
    bl_description = trans("选中组输入节点,每一个接口拆分成一个节点")

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        i = 0
        for node in selected_nodes:
            if node.bl_idname != "NodeGroupInput" or not node.select: continue
            i = -1
            for sk_out in node.outputs:
                if sk_out.hide or not sk_out.enabled or sk_out.bl_idname == "NodeSocketVirtual": continue
                i += 1
                group_in_nd = nodes.new('NodeGroupInput')
                group_in_nd.location = nd_abs_loc(node)
                group_in_nd.location.y = nd_abs_loc(node).y - 60 * i
                group_id = {socket.identifier: socket for socket in group_in_nd.outputs}
                for link in sk_out.links:
                    links.new(group_id[sk_out.identifier], link.to_socket)
                for new_sk_out in group_in_nd.outputs:
                    if new_sk_out.identifier != sk_out.identifier:
                        new_sk_out.hide = True
            nodes.remove(node)
        return {"FINISHED"}

class NODE_OT_Split_All_Group_Input_Socket(BaseOperator):
    bl_idname = "node.split_all_group_input_socket"
    bl_label = trans("完全拆分")
    bl_description = trans("选中组输入节点,每一个接口/连线拆分成一个节点")

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        i = 0
        for node in selected_nodes:
            if node.bl_idname != "NodeGroupInput" or not node.select: continue
            i = -1
            for sk_out in node.outputs:
                if sk_out.hide or not sk_out.enabled or sk_out.bl_idname == "NodeSocketVirtual": continue
                link_count = len(sk_out.links)
                soc_links = sk_out.links if sk_out.links else range(1)
                for link in soc_links:
                    if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                        continue
                    i += 1
                    group_in_nd = nodes.new('NodeGroupInput')
                    group_in_nd.location = nd_abs_loc(node)
                    group_in_nd.location.y = nd_abs_loc(node).y - 60 * i
                    group_id = {socket.identifier: socket for socket in group_in_nd.outputs}
                    if link_count:
                        links.new(group_id[sk_out.identifier], link.to_socket)
                    for new_sk_out in group_in_nd.outputs:
                        if new_sk_out.identifier != sk_out.identifier:
                            new_sk_out.hide = True
            nodes.remove(node)
        return {"FINISHED"}

class NODE_OT_Split_All_And_Move(BaseOperator):
    bl_idname = "node.split_all_and_move"
    bl_label = trans("完全拆分并移动")
    bl_description = trans("选中组输入节点,每一个连线拆分成一个节点,并移动到连向接口(to_socket)的附近")

    def execute(self, context):
        tree: NodeTree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = get_selected_group_input(context)
        is_del_reroute = pref().is_del_reroute
        i = 0
        offset = 0
        for node in selected_nodes:
            i = -1
            node.parent = None
            for sk_out in node.outputs:
                if not sk_out.hide and sk_out.enabled and sk_out.bl_idname != "NodeSocketVirtual":
                    if not offset:
                        offset = node.location.y - sk_location(sk_out).y / ui_scale()
                    # 删掉组输入输出接口后面连的所有转接点
                    if is_del_reroute and sk_out.links:
                        delete_reroute(sk_out, nodes, links)
                    link_count = len(sk_out.links)
                    soc_links = sk_out.links if sk_out.links else range(1)
                    for link in soc_links:
                        if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                            continue
                        i += 1
                        if link_count:         # is_linked:
                            group_in_nd = nodes.new('NodeGroupInput')
                            group_id = {socket.identifier: socket for socket in group_in_nd.outputs}
                            spec_in_socket = group_id[sk_out.identifier]

                            links.new(spec_in_socket, link.to_socket)
                            to_socket = spec_in_socket.links[0].to_socket
                            move_nd_to_sk(group_in_nd, to_socket, offset)
                        for new_sk_out in group_in_nd.outputs:
                            if new_sk_out.identifier != sk_out.identifier:
                                new_sk_out.hide = True
            nodes.remove(node)
        return {"FINISHED"}

def delete_reroute(sk_out: NodeSocket, nodes: Nodes, links: NodeLinks):
    links_to_check = list(sk_out.links)
    reroutes = set()

    while links_to_check:
        link = links_to_check.pop()
        if link and link.to_node and link.to_node.type == 'REROUTE':
            reroute = link.to_node
            reroutes.add(reroute)

            for next_link in reroute.outputs[0].links:
                links_to_check.append(next_link)

        # elif link and link.to_socket:
        else:
            links.new(sk_out, link.to_socket)

    for reroute in reroutes:
        nodes.remove(reroute)

def get_selected_group_input(context: Context, deselect_other=True) -> list[Node]:
    selected_nodes = []
    for node  in context.selected_nodes:
        if node.bl_idname == "NodeGroupInput" and node.select and has_link(node):
            selected_nodes.append(node)
        elif deselect_other:
            node.select = False
    return selected_nodes

def split_all_and_merge_move(context: Context, is_pre_merge=False):
    selected_nodes = get_selected_group_input(context)
    if is_pre_merge:
        merge_group_input_linked(selected_nodes, context.active_node)
    # selected_nodes = context.selected_nodes
    tree = context.space_data.edit_tree
    nodes = tree.nodes
    links = tree.links
    is_del_reroute = pref().is_del_reroute
    i = 0
    to_node_with_inputs = {}    # to_node_with_group_inputs节点输入接口的组输入数量
    for node in selected_nodes:
        if node.bl_idname != "NodeGroupInput" or not has_link(node):
            continue
        node.parent = None
        i = -1
        offset = 0
        for sk_out in node.outputs:
            if sk_out.hide or not sk_out.enabled or sk_out.bl_idname == "NodeSocketVirtual":
                continue
            if not offset:
                offset = node.location.y - sk_location(sk_out).y / ui_scale()
            # 删掉组输入输出接口后面连的所有转接点
            if is_del_reroute and sk_out.links:
                delete_reroute(sk_out, nodes, links)
            link_count = len(sk_out.links)
            # soc_links = sk_out.links if sk_out.links else range(1)
            if sk_out.links:
                soc_links = sk_out.links
            else:
                continue
            for link in soc_links:
                if hasattr(link, "is_valid") and not link.is_valid:       # 有些线存在，但是因为节点不同选项，线不可见
                    continue
                i += 1
                group_in_nd = nodes.new('NodeGroupInput')
                # group_in_nd.location = node.location; group_in_nd.location.y = node.location.y - 80 * i
                group_id = {socket.identifier: socket for socket in group_in_nd.outputs}
                spec_in_socket = group_id[sk_out.identifier]
                if link_count:         # is_linked:
                    links.new(spec_in_socket, link.to_socket)
                    to_node = spec_in_socket.links[0].to_node
                    to_socket = spec_in_socket.links[0].to_socket
                    if to_node in to_node_with_inputs:
                        to_node_with_inputs[to_node].append(group_in_nd)
                    else:
                        to_node_with_inputs[to_node] = [group_in_nd]
                    move_nd_to_sk(group_in_nd, to_socket, offset)
                for new_sk_out in group_in_nd.outputs:
                    if new_sk_out.identifier != sk_out.identifier:
                        new_sk_out.hide = True
        nodes.remove(node)

    for node_list in to_node_with_inputs.values():
        if len(node_list) > 1:
            # 不知道为什么合并后会偏移md
            merge_group_input_linked(node_list, None, loc_at_max_y=True).location.x = nd_abs_loc(node_list[0]).x

class NODE_OT_Split_All_And_Merge_Move(BaseOperator):
    bl_idname = "node.split_all_and_merge_move"
    bl_label = trans("拆分并移动合并")
    bl_description = trans("选中组输入节点,每一个连线拆分成一个节点,并移动到连向接口(to_socket)的附近,并合并连到一个节点上的组输入节点")

    def execute(self, context):
        split_all_and_merge_move(context)
        return {"FINISHED"}

class NODE_OT_Merge_Node_And_Split_Merge_Move(BaseOperator):
    bl_idname = "node.merge_node_and_split_merge_move"
    bl_label = trans("合并节点并拆分")
    bl_description = trans("选中组输入节点,先合并成一个节点,再拆分接口,并移动到连向接口(to_socket)的附近,并合并连到一个节点上的组输入节点")

    def execute(self, context):
        split_all_and_merge_move(context, is_pre_merge=True)
        return {"FINISHED"}

class NODE_OT_Split_Group_Input_Linked(BaseOperator):
    bl_idname = "node.split_group_input_linked"
    bl_label = trans("拆分组输入")
    bl_description = trans("选中组输入节点,隐藏未连线节口后,拆分组输入接口")

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        links = tree.links
        selected_nodes = context.selected_nodes
        i = 0
        for node in selected_nodes:
            if node.bl_idname == "NodeGroupInput" and node.select:
                i = -1
                for sk_out in node.outputs:
                    if sk_out.is_linked:
                        i += 1
                        group_in_nd = nodes.new('NodeGroupInput')
                        group_in_nd.location = nd_abs_loc(node)
                        group_in_nd.location.y = nd_abs_loc(node).y - 60 * i
                        group_id = {sk_outket1.identifier: sk_outket1 for sk_outket1 in group_in_nd.outputs}
                        for link in sk_out.links:
                            links.new(group_id[sk_out.identifier], link.to_socket)
                        for sk_out in group_in_nd.outputs:
                            sk_out.hide = True
                nodes.remove(node)
        return {"FINISHED"}

class NODE_OT_Hide_Group_Input_Sockets(BaseOperator):
    bl_idname = "node.hide_group_input_sockets"
    bl_label = trans("隐藏未使用组输入接口")
    bl_description = trans("隐藏所有组输入节点未使用的接口")

    def execute(self, context):
        nodes = context.space_data.edit_tree.nodes
        for node in nodes:
            if node.bl_idname == "NodeGroupInput":
                for soc in node.outputs:
                    soc.hide = True

        return {"FINISHED"}

class NODE_MT_Merge_Split_Move_Group_Input(Menu):
    bl_idname = "NODE_MT_Merge_Split_Move_Group_Input"
    bl_label = trans("组输入拆分合并移动")

    def draw(self, context):
        layout = self.layout
        prefs =  pref()
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
    NODE_OT_Add_Hided_Socket_Group_Input,
    NODE_MT_Add_Hided_Socket_Group_Input,
    NODE_PT_Group_Input_Helper,
    NODE_OT_Add_New_Group_Item,
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
    if bpy.app.version >= (4, 5, 0):
        _icons.load('空.png', os.path.join(os.path.dirname(__file__), 'icons', '空.png'), "IMAGE")
    else:
        for png in png_list:
            _icons.load(png, os.path.join(os.path.dirname(__file__), 'icons', png), "IMAGE")

    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.NODE_MT_editor_menus.append(add_group_input_helper_to_node_mt_editor_menus)
    bpy.types.Scene.add_input_socket  = BoolProperty(name='add_input_socket',  description=trans('同时添加输入接口'), default=True)
    bpy.types.Scene.add_output_socket = BoolProperty(name='add_output_socket', description=trans('同时添加输出接口'), default=False)

    # 第一种
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new('wm.call_menu', 'ONE', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'NODE_MT_Add_Hided_Socket_Group_Input'
    addon_keymaps['key_MT_Add_Group_Input'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_panel', 'ONE', 'PRESS', ctrl=True, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'NODE_PT_Group_Input_Helper'
    kmi.properties.keep_open = True
    addon_keymaps['NODE_PT_Group_Input_Helper'] = (km, kmi)

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
