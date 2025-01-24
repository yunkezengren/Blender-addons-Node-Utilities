import bpy
from bpy.types import Operator
from math import ceil
import mathutils
from pprint import pprint
# from mathutils import Vector
import time

# TODO 自定义分布后节点间距
# TODO 自定义栅格分布判断列的间距(或者根据节点密度/数量自动判断)
# for i in range(400):      # 节点树节点个数 400个时      1600个时
#     node.location.x -= 1            # 耗时 0.135465s    0.748193s
#     list.append(node.location.x)    # 耗时 0.000102s    0.000216s
# 400个节点  相对栅格分布: 0.3754s

def ui_scale():
    return bpy.context.preferences.system.dpi / 72      # 类似于prefs.view.ui_scale, 但是不同的显示器dpi不一样吗

def get_x_min(nodes):
    return min(node.location.x for node in nodes)
def get_x_max(nodes):
    return max(node.location.x + node.width for node in nodes)
def get_y_min(nodes):
    return min(node.location.y - node.dimensions.y / ui_scale() for node in nodes)
def get_y_max(nodes):
    return max(node.location.y for node in nodes)
def get_x_center(nodes):
    x_min = get_x_min(nodes)
    x_max = get_x_max(nodes)
    return (x_min + x_max) / 2
def get_y_center(nodes):
    y_min = get_y_min(nodes)
    y_max = get_y_max(nodes)
    return (y_min + y_max) / 2

def detach_parent_frame(node_parent_dict, frame_node_list):
    before_select_nodes = bpy.context.selected_nodes
    for node in before_select_nodes:
        node_parent_dict[node.name] = node.parent
        if node.bl_idname == "NodeFrame":
            frame_node_list.append(node)
            node.select = False
    bpy.ops.node.detach('INVOKE_DEFAULT')
    return node_parent_dict, frame_node_list

def restore_parent_frame(nodes, node_parent_dict, frame_node_list):
    for node in nodes:
        node.parent = node_parent_dict[node.name]
    for node in frame_node_list:
        node.select = True

class NodePoll:
    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        if tree and context.selected_nodes:
            return True
        return False

class BaseAlignOp(Operator):
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        i = 0
        for node in context.selected_nodes:
            if node.bl_idname != "NodeFrame":
                i += 1
        if tree and i > 1:
            return True
        return False

    def align_nodes(self, nodes):
        raise NotImplementedError("Subclasses must implement this method")

    def execute(self, context):
        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)      # 这里还会取消选择Frame
        select_nodes = context.selected_nodes
        s_time = time.perf_counter()
        self.align_nodes(select_nodes)
        print("对齐总耗时: ", f"{time.perf_counter() - s_time:.6f}s\n")
        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)   # 这里还会选回来
        return {"FINISHED"}

    def show_popup(self, message):
        def draw_popup(self, context):
            self.layout.label(text=message, icon="NONE")
        bpy.context.window_manager.popup_menu(draw_popup, title="信息", icon="INFO")

class NODE_OT_align_left(BaseAlignOp):
    bl_idname = "node.align_left"
    bl_label = "Align Left Side Selection Nodes"
    bl_description = "Align the left side of all selected nodes"

    def align_nodes(self, nodes):
        # self.report({"INFO"}, "普通信息")
        self.show_popup("测试弹窗普通信息")
        x_min = get_x_min(nodes)
        for node in nodes:
            node.location.x = x_min

class NODE_OT_align_right(BaseAlignOp):
    bl_idname = "node.align_right"
    bl_label = "Align Right Side Selection Nodes"
    bl_description = "Align the right side of all selected nodes"

    def align_nodes(self, nodes):
        x_max = get_x_max(nodes)
        for node in nodes:
            node.location.x = x_max - node.width

class NODE_OT_align_top(BaseAlignOp):
    bl_idname = "node.align_top"
    bl_label = "Align Top Side Selection Nodes"
    bl_description = "Align the top of all selected nodes"

    def align_nodes(self, nodes):
        y_max = get_y_max(nodes)
        for node in nodes:
            node.location.y = y_max

class NODE_OT_align_bottom(BaseAlignOp):
    bl_idname = "node.align_bottom"
    bl_label = "Align Bottom Side Selection Nodes"
    bl_description = "Align the bottom of all selected nodes"

    def align_nodes(self, nodes):
        y_min = get_y_min(nodes)
        for node in nodes:
            node.location.y = y_min + node.dimensions.y / ui_scale()

class NODE_OT_align_heightcenter(BaseAlignOp):
    bl_idname = "node.align_height_center"
    bl_label = "Align Height Center Side Selection Nodes"
    bl_description = "Align the height center of all selected nodes"

    def align_nodes(self, nodes):
        y_center = get_y_center(nodes)
        for node in nodes:
            node.location.y = y_center + node.dimensions.y / 2

class NODE_OT_align_widthcenter(BaseAlignOp):
    bl_idname = "node.align_width_center"
    bl_label = "Align Width Center Side Selection Nodes"
    bl_description = "Align the width center of all selected nodes"

    def align_nodes(self, nodes):
        x_center = get_x_center(nodes)
        for node in nodes:
            node.location.x = x_center - node.width / 2

def evenly_distribute_node(nodes, is_horizontal=False, is_vertical=False, min_p=None, max_p=None):
    node_infos = []
    node_num = 0; total_size = 0
    for node in nodes:
        if node.parent is None:
            if is_horizontal:
                size = node.width
                pos_start = node.location.x
                pos_end = node.location.x + size
            if is_vertical:
                size = node.dimensions.y / ui_scale()
                pos_start = node.location.y
                pos_end = node.location.y - size
            node_num += 1
            total_size += size
            node_infos.append((pos_start, pos_end, node, size))

    if node_num <= 1:
        return node_infos
    if is_horizontal:
        node_infos.sort(key=lambda x: x[1])
        max_pos = node_infos[-1][1]
        node_infos.sort(key=lambda x: x[0])
        min_pos = node_infos[0][0]
    if is_vertical:
        node_infos.sort(key=lambda x: x[1])
        min_pos = node_infos[0][1]
        node_infos.sort(key=lambda x: x[0], reverse=True)
        max_pos = node_infos[0][0]
    if not(min_p is None):
        min_pos = min_p
        max_pos = max_p
    interval = (max_pos - min_pos - total_size) / (node_num - 1)

    sum_size = 0
    for i, node_info in enumerate(node_infos):
        if is_horizontal:
            node_info[2].location.x = min_pos + interval * i + sum_size
        if is_vertical:
            node_info[2].location.y = max_pos - interval * i - sum_size
        sum_size += node_info[3]
    return node_infos

def grid_distribute_node(nodes, min_pos=None, max_pos=None):
    node_infos = []
    for node in nodes:
        node_infos.append((node.location.x, node))
    node_infos.sort(key=lambda x: x[0])
    x_min = node_infos[0][0]        # 
    x_max = node_infos[-1][0]
    max_col_num = ceil((x_max - x_min) / 140)   # max_col_num 是最大的列数

    # 把节点以x位置间隔大于140划分为列,每列左对齐,并垂直等距分布
    vertical_node_l_l = []
    for _ in range(max_col_num + 1):       # 只有一列的话,那就应该对齐宽度
        # print("\n开始 " + "="*40)
        if len(node_infos) == 0:           # node_infos每次循环都会删除一些,max_col_num 是不一定达到的最大列数
            break
        rest_x_min = node_infos[0][0]      # 剩下的节点里的x_min
        require_align_nodes = []
        for node_info in node_infos:
            node = node_info[1]
            if node.location.x < rest_x_min + 140:   # 先左对齐
                node.location.x = rest_x_min                                        # ! 耗时的操作
                # node.location.x = rest_x_min - ((node.width - 140) / 2)       # 不知道什么用
                require_align_nodes.append(node_info[1])
        node_infos = node_infos[len(require_align_nodes):]

        node_list = evenly_distribute_node(require_align_nodes, is_vertical=True, min_p=min_pos, max_p=max_pos)   # ! 耗时的操作
        vertical_node_l_l.append(node_list)
    # pprint(vertical_node_l_l)

    # print("把每列当成一个节点,水平等距分布........................")
    col_num = 0 ; sum_width = 0                        # sum_width 是当前列到第一列的列节点最大宽度相加
    col_max_width_l = []
    sum_width_l = []     # sum_width_l 是每一列到第一列的列节点最大宽度相加
    for vertical_node_l in vertical_node_l_l:
        col_num += 1; col_sum_width = 0
        temp_width_l = []
        for node_info in vertical_node_l:
            col_sum_width += node_info[2].width
            temp_width_l.append(node_info[2].width)
        col_max_width = max(temp_width_l)
        col_max_width_l.append(col_max_width)
        sum_width += col_max_width
        sum_width_l.append(sum_width)

    # 每列再对齐宽度
    x_max = max(info[2].location.x+info[2].width for info in vertical_node_l_l[-1])    # 垂直等距分布过的,里面存的是y相关,最后(右)一列
    interval = (x_max - x_min - sum_width) / (col_num - 1) if col_num > 1 else 0
    for i, vertical_node_l in enumerate(vertical_node_l_l):
        for node_info in vertical_node_l:
            node = node_info[2]
            align = (col_max_width_l[i] -node.width) / 2 + sum_width_l[i-1]*(i!=0)
            node.location.x = x_min + interval*i + align                            # ! 耗时的操作

class NODE_OT_distribute_horizontal(BaseAlignOp):
    bl_idname = "node.distribute_horizontal"
    bl_label = "Distribute Nodes Horizontally"
    bl_description = "水平等距分布"

    def align_nodes(self, nodes):
        evenly_distribute_node(nodes, is_horizontal=True)

class NODE_OT_distribute_vertical(BaseAlignOp):
    bl_idname = "node.distribute_vertical"
    bl_label = "Distribute Nodes Vertically"
    bl_description = "垂直等距分布"

    def align_nodes(self, nodes):
        evenly_distribute_node(nodes, is_vertical=True)

class NODE_OT_distribute_grid_relative(BaseAlignOp):
    bl_idname = "node.distribute_grid_relative"
    bl_label = "Selection Nodes - distribute_grid_relative"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列各自最大最小高度"

    def align_nodes(self, nodes):
        grid_distribute_node(nodes)

class NODE_OT_distribute_grid_absolute(BaseAlignOp):
    bl_idname = "node.distribute_grid_absolute"
    bl_label = "Selection Nodes - distribute_grid_absolute"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列最大最小高度一样"

    def align_nodes(self, nodes):
        y_min = get_y_min(nodes)
        y_max = get_y_max(nodes)
        grid_distribute_node(nodes, min_pos=y_min, max_pos=y_max)

def get_abs_local(node):
    return node.location + get_abs_local(node.parent) if node.parent else node.location

def Vector(*args):
    return mathutils.Vector((args))

def TranslateIface(txt):
    return bpy.app.translations.pgettext_iface(txt)

def linear_interpolation(x,
              xp=[  0.5,   0.8,  1,   1.1,  1.15,   1.2,  1.3,   1.4,  1.5,      2,   2.5,  3,   3.5,    4],
              fp=[24.01, 21.48, 22, 21.87, 21.95, 21.77, 20.9, 20.86, 20.66, 20.45, 20.37, 21, 20.83, 21.24]):
    for i in range(len(xp) - 1):
        if xp[i] <= x <= xp[i + 1]:
            x1 = xp[i]
            y1 = fp[i]
            x2 = xp[i + 1]
            y2 = fp[i + 1]
            y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            return y
    return None

def GetSocketLocation(nd, in_out):    # in -1 out 1
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.links) and (sk.links[0].is_muted)
    dict_result = {}
    ndLoc = get_abs_local(nd)
    ndDim = mathutils.Vector(nd.dimensions / ui_scale())
    if in_out == 1:
        skLocCarriage = Vector(ndLoc.x + ndDim.x, ndLoc.y - 35)
    else:
        skLocCarriage = Vector(ndLoc.x, ndLoc.y - ndDim.y + 15)
    for sk in nd.outputs if in_out == 1 else reversed(nd.inputs):
        if (sk.enabled) and (not sk.hide):
            if (in_out ==  -1) and (sk.type == 'VECTOR') and (SkIsLinkedVisible(sk)) and (not sk.hide_value):
                if str(sk.rna_type).find("VectorDirection") != -1:
                    skLocCarriage.y += 20 * 2
                elif ( not(nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING')) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    skLocCarriage.y += 30 * 2
            goalPos = skLocCarriage.copy()
            if sk.is_linked:
                dict_result[sk] = {"pos": goalPos, "name": TranslateIface(sk.label if sk.label else sk.name)}
            skLocCarriage.y -= linear_interpolation(ui_scale()) * in_out     # 缩放 1 -> 22  1.1 -> 21.88
    return dict_result

class NODE_OT_straight_link(Operator, NodePoll):
    bl_idname = "node.straight_link"
    bl_label = "straight_link"
    bl_description = "拉直节点输入输出之间连线-需要选中活动节点"

    def execute(self, context):
        tree = context.space_data.edit_tree
        links = tree.links
        a_node = context.active_node

        from_nodes = [a_node]
        to_nodes = [a_node]
        condition = 1
        while condition:
            condition = 0
            temp_from_nodes = []; temp_to_nodes = []
            for condition_node in from_nodes:
                condition_SkIn  = GetSocketLocation(condition_node, -1)
                for link in links:
                    from_node = link.from_node; to_node = link.to_node
                    from_socket = link.from_socket; to_socket = link.to_socket
                    if to_node.name == condition_node.name and from_node.select:
                        from_node_SKOut = GetSocketLocation(from_node, 1)
                        from_node.location.y += condition_SkIn[to_socket]["pos"].y - from_node_SKOut[from_socket]["pos"].y - from_node.hide*24 + condition_node.hide*6 - 2
                        if from_node.inputs:
                            condition += 1
                            temp_from_nodes.append(from_node)
            from_nodes = temp_from_nodes
            for condition_node in to_nodes:
                condition_SkOut = GetSocketLocation(condition_node, 1)
                for link in links:
                    from_node = link.from_node; to_node = link.to_node
                    from_socket = link.from_socket; to_socket = link.to_socket
                    if from_node.name == condition_node.name and to_node.select:
                        to_node_SKIn = GetSocketLocation(to_node, -1)
                        to_node.location.y += condition_SkOut[from_socket]["pos"].y - to_node_SKIn[to_socket]["pos"].y - to_node.hide*4 + condition_node.hide*26
                        if to_node.outputs:
                            condition += 1
                            temp_to_nodes.append(to_node)
            to_nodes = temp_to_nodes
        return {"FINISHED"}

