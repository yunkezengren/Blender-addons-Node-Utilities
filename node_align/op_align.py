import bpy
from bpy.types import Operator
from math import ceil
import mathutils
from pprint import pprint
# from mathutils import Vector
# from builtins import len as length

def ui_scale():
    return bpy.context.preferences.system.dpi / 72      # 类似于prefs.view.ui_scale, 但是不同的显示器不一样吗

def sort_location(nodes):
    locations = []
    loc_min_max = {}
    for node in nodes:
        left = node.location.x
        right = node.location.x + node.width
        top = node.location.y
        bottom = node.location.y - node.dimensions.y
        locations.append([left, right, top, bottom])
    locations.sort(key=lambda x: x[0])
    loc_min_max["x_min"] = locations[0][0]
    locations.sort(key=lambda x: x[1])
    loc_min_max["x_max"] = locations[-1][1]
    locations.sort(key=lambda x: x[2])
    loc_min_max["y_max"] = locations[-1][2]
    locations.sort(key=lambda x: x[3])
    loc_min_max["y_min"] = locations[0][3]
    loc_min_max["x_center"] = (loc_min_max["x_min"] + loc_min_max["x_max"]) / 2
    loc_min_max["y_center"] = (loc_min_max["y_min"] + loc_min_max["y_max"]) / 2
    return loc_min_max

def get_x_min(nodes):
    return min(node.location.x for node in nodes)
def get_x_max(nodes):
    return max(node.location.x + node.width for node in nodes)
def get_y_min(nodes):
    return min(node.location.y - node.dimensions.y for node in nodes)
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
        if tree and context.selected_nodes:
            return True
        return False
    
    def align_nodes(self, nodes):
        raise NotImplementedError("Subclasses must implement this method")

    def execute(self, context):
        node_parent_dict = {}
        frame_node_list = []
        select_nodes = context.selected_nodes
        detach_parent_frame(node_parent_dict, frame_node_list)
        self.align_nodes(select_nodes)
        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)
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
            node.location.x = x_center - node.dimensions.x / 2


class NODE_OT_distribute_horizontal(Operator, NodePoll):
    bl_idname = "node.distribute_horizontal"
    bl_label = "Selection Nodes - distribute_horizontal"
    bl_description = "水平等距分布"
    def execute(self, context):
        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)

        select_nodes = context.selected_nodes
        node_infos = []
        num = 0 ; sum_width = 0
        for node in select_nodes:
            # if node.bl_idname != "NodeFrame":
            if node.parent is None:
                num += 1 ; sum_width += node.width
                node_infos.append((node.location.x, node.location.x + node.width, node, node.width))

        node_infos.sort(key=lambda x: x[1])
        x_max = node_infos[-1][1]

        node_infos.sort(key=lambda x: x[0])
        x_min = node_infos[0][0]
        if num == 1:
            interval =1
        else:
            interval = (x_max - x_min - sum_width) / (num - 1)

        i = 0; sum_width = 0
        for node_info in node_infos:
            node_info[2].location.x = x_min + interval * i + sum_width
            i += 1; sum_width += node_info[3]

        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)

        return {"FINISHED"}

class NODE_OT_distribute_vertical(Operator, NodePoll):
    bl_idname = "node.distribute_vertical"
    bl_label = "Selection Nodes - distribute_vertical"
    bl_description = "垂直等距分布"

    def execute(self, context):
        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)

        select_nodes = context.selected_nodes
        node_infos = []
        num = 0 ; sum_height = 0
        for node in select_nodes:
            # if node.bl_idname != "NodeFrame":
            if node.parent is None:
                num += 1 ; sum_height += node.dimensions.y
                print(node.name, node.dimensions.y)
                node_infos.append((node.location.y, node.location.y - node.dimensions.y, node, node.dimensions.y))

        node_infos.sort(key=lambda x: x[1])
        y_min = node_infos[0][1]

        node_infos.sort(key=lambda x: x[0], reverse=True)
        y_max = node_infos[0][0]
        print(y_min, y_max)
        if num == 1:
            interval =1
        else:
            interval = (y_max - y_min - sum_height) / (num - 1)

        i = 0; sort_sum_height = 0
        for node_info in node_infos:
            node_info[2].location.y = y_max - interval * i - sort_sum_height
            i += 1; sort_sum_height += node_info[3]

        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)

        return {"FINISHED"}

class NODE_OT_distribute_grid_relative(Operator, NodePoll):
    bl_idname = "node.distribute_grid_relative"
    bl_label = "Selection Nodes - distribute_grid_relative"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列各自最大最小高度"
    def execute(self, context):
        print("开始..............................................................................................")

        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)

        select_nodes = context.selected_nodes
        node_infos = []
        for node in select_nodes:
            node_infos.append((node.location.x, node))
        node_infos.sort(key=lambda x: x[0])
        x_min = node_infos[0][0]
        x_max = node_infos[-1][0]
        num = ceil((x_max - x_min) / 140)
        print("x_min:", x_min)
        print("x_max:", x_max)
        print("num:", num)

        # 把节点以y位置间隔大于140划分为列并垂直等距分布
        vertical_nodes = []
        for i in range(1, num + 1):
            print("node_info:", [[i[1].name, i[1].location.x] for i in node_infos])
            if len(node_infos) == 0:
                break
            x_min = node_infos[0][0]
            print("x_min:", x_min)
            remove_list = []
            for node_info in node_infos:
                node = node_info[1]
                if node.location.x < x_min + 140:
                    node.location.x = x_min
                    # node.location.x = x_min - ((node.width- 140) / 2)

                    remove_list.append(node_info)
            print("remove_list:", [i[1].name for i in remove_list])
            for node in remove_list:
                node_infos.remove(node)

            # 垂直等距对齐,每列对齐一次
            vertical_node = []
            num = 0 ; sum_height = 0; sum_width = 0
            for node_info in remove_list:
                node = node_info[1]
                num += 1 ; sum_height += node.dimensions.y; sum_width += node.width
                vertical_node.append([node.location.y, node.location.y - node.dimensions.y, node, node.dimensions.y])
            # avera_width = sum_width / num
            # vertical_node[-1].append(avera_width)
            vertical_node.sort(key=lambda x: x[1])
            y_min = vertical_node[0][1]
            vertical_node.sort(key=lambda x: x[0], reverse=True)
            y_max = vertical_node[0][0]
            if num == 1:
                interval =1
            else:
                interval = (y_max - y_min - sum_height) / (num - 1)
            i = 0; sort_sum_height = 0
            for node_info in vertical_node:
                node_info[2].location.y = y_max - interval * i - sort_sum_height
                i += 1; sort_sum_height += node_info[3]
            vertical_nodes.append(vertical_node)

        # print("水平等距对齐,把每列当成一个节点........................")
        # 水平等距对齐,把每列当成一个节点........................
        num = 0 ; sum_width = 0; avera_width = 0
        max_widths = []
        avera_widths = []; sum_widths = []
        for vertical_node in vertical_nodes:
            num += 1; width = 0; n = 0
            temp_width = []
            for node_info in vertical_node:
                n += 1
                width += node_info[2].width
                temp_width.append(node_info[2].width)
            temp_width.sort()
            max_width = temp_width[-1]
            avera_widths.append(width / n)
            max_widths.append(max_width)
            # sum_width += avera_width
            sum_width += max_width
            sum_widths.append(sum_width)
            print("max_width:", max_width)
            print("sum_width:", sum_width)
        node_location = []
        for node in select_nodes:
            node_location.append(node.location.x)
        node_location = list(set(node_location))
        node_location.sort()
        x_min = node_location[0]
        x_max = node_location[-1] + max_widths[-1]
        if num == 1:
            interval =1
        else:
            interval = (x_max - x_min - sum_width) / (num - 1)

        i = 0
        for vertical_node in vertical_nodes:
            print("sum_widths[i]:", sum_widths[i])
            for node_info in vertical_node:
                if i == 0:
                    node_info[2].location.x = x_min + interval * i
                else:
                    align = (max_widths[i] -node_info[2].width) / 2    # 每列别的节点和宽度最大的节点(它不移动)对齐宽度补偿偏移
                    node_info[2].location.x = x_min + interval * i + sum_widths[i-1] + align
            i += 1

        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)

        print("结束..............................................................................................")
        return {"FINISHED"}

class NODE_OT_distribute_grid_absolute(Operator, NodePoll):
    bl_idname = "node.distribute_grid_absolute"
    bl_label = "Selection Nodes - distribute_grid_absolute"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列最大最小高度一样"
    def execute(self, context):
        print("开始..............................................................................................")

        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)

        select_nodes = context.selected_nodes
        node_infos = []
        for node in select_nodes:
            node_infos.append((node.location.x, node))
        node_infos.sort(key=lambda x: x[0])
        x_min = node_infos[0][0]
        x_max = node_infos[-1][0]
        num = ceil((x_max - x_min) / 140)
        print("x_min:", x_min)
        print("x_max:", x_max)
        print("num:", num)
        node_location_y = []        # 和上面列表和一块还要改下面的，懒得改了，新建一个
        for node in select_nodes:
            node_location_y.append((node.location.y, node.location.y - node.dimensions.y))
        node_location_y.sort(key=lambda x: x[0])
        y_max = node_location_y[-1][0]
        node_location_y.sort(key=lambda x: x[1])
        y_min = node_location_y[0][1]

        # 把节点以y位置间隔大于140划分为列并垂直等距分布
        vertical_nodes = []
        for i in range(1, num + 1):
            print("node_info:", [[i[1].name, i[1].location.x] for i in node_infos])
            if len(node_infos) == 0:
                break
            x_min = node_infos[0][0]
            print("x_min:", x_min)
            remove_list = []
            for node_info in node_infos:
                node = node_info[1]
                if node.location.x < x_min + 140:
                    node.location.x = x_min
                    # node.location.x = x_min - ((node.width- 140) / 2)
                    remove_list.append(node_info)
            print("remove_list:", [i[1].name for i in remove_list])
            for node in remove_list:
                node_infos.remove(node)
            # 垂直等距对齐,每列对齐一次
            vertical_node = []
            num = 0 ; sum_height = 0; sum_width = 0
            for node_info in remove_list:
                node = node_info[1]
                num += 1 ; sum_height += node.dimensions.y; sum_width += node.width
                vertical_node.append([node.location.y, node.location.y - node.dimensions.y, node, node.dimensions.y])
            avera_width = sum_width / num
            vertical_node[-1].append(avera_width)
            vertical_node.sort(key=lambda x: x[1])
            # y_min = vertical_node[0][1]
            vertical_node.sort(key=lambda x: x[0], reverse=True)
            # y_max = vertical_node[0][0]
            if num == 1:
                interval =1
            else:
                interval = (y_max - y_min - sum_height) / (num - 1)
            i = 0; sort_sum_height = 0
            for node_info in vertical_node:
                node_info[2].location.y = y_max - interval * i - sort_sum_height
                i += 1; sort_sum_height += node_info[3]
            vertical_nodes.append(vertical_node)

        # print("水平等距对齐,把每列当成一个节点........................")
        # 水平等距对齐,把每列当成一个节点........................
        num = 0 ; sum_width = 0; avera_width = 0
        max_widths = []
        avera_widths = []; sum_widths = []
        for vertical_node in vertical_nodes:
            num += 1; width = 0; n = 0
            temp_width = []
            for node_info in vertical_node:
                n += 1
                width += node_info[2].width
                temp_width.append(node_info[2].width)
            temp_width.sort()
            max_width = temp_width[-1]
            avera_widths.append(width / n)
            max_widths.append(max_width)
            # sum_width += avera_width
            sum_width += max_width
            sum_widths.append(sum_width)
            print("max_width:", max_width)
            print("sum_width:", sum_width)
        node_location = []
        for node in select_nodes:
            node_location.append(node.location.x)
        node_location = list(set(node_location))
        node_location.sort()
        x_min = node_location[0]
        x_max = node_location[-1] + max_widths[-1]
        if num == 1:
            interval =1
        else:
            interval = (x_max - x_min - sum_width) / (num - 1)

        i = 0
        for vertical_node in vertical_nodes:
            print("sum_widths[i]:", sum_widths[i])
            for node_info in vertical_node:
                if i == 0:
                    node_info[2].location.x = x_min + interval * i
                else:
                    align = (max_widths[i] -node_info[2].width) / 2    # 每列别的节点和宽度最大的节点(它不移动)对齐宽度补偿偏移
                    node_info[2].location.x = x_min + interval * i + sum_widths[i-1] + align
            i += 1

        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)
        print("结束..............................................................................................")
        return {"FINISHED"}


def get_abs_local(node):
    return node.location + get_abs_local(node.parent) if node.parent else node.location

def Vector( *args):
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
            ui_scale = bpy.context.preferences.view.ui_scale
            skLocCarriage.y -= linear_interpolation(ui_scale) * in_out     # 缩放 1 -> 22  1.1 -> 21.88
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
