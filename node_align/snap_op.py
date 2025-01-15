import bpy
from math import ceil
import mathutils
from pprint import pprint
# from mathutils import Vector
# from builtins import len as length

# bpy.context.space_data.node_tree
# bpy.context.screen
class NodeOperator:
    @classmethod
    def poll(cls, context):
        tree = context.space_data.node_tree
        if tree is None: return False
        # if tree.nodes.active is None: return False
        a = 0
        for node in tree.nodes:
            if node.select is True: 
                a = a + 1
        if a == 0:
            return False
        return True
""" # 排序
def sort_location():
    for i in bpy.context.selected_nodes:
        print(i.location)
locations = []
for node in selectedNodes:
    locations.append(node.location)
locations.sort(key=lambda loc: loc.x)
x_min = locations[0].x
x_max = locations[-1].x
 
locations.sort(key=lambda loc: loc.y)
y_min = locations[0].y
y_max = locations[-1].y
print(f"X方向的最小值是 {x_min}")
print(f"X方向的最大值是 {x_max}")
print(f"Y方向的最小值是 {y_min}")
print(f"Y方向的最大值是 {y_max}") 
"""

def sort_location(selectedNodes):
    locations = []
    loc_min_max = {}
    for node in selectedNodes:
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

def detach_parent_frame(node_parent, frame_node):
    before_selectedNodes = bpy.context.selected_nodes
    for node in before_selectedNodes:
        node_parent[node.name] = node.parent
        if node.bl_idname == "NodeFrame":
            frame_node.append(node)
            node.select = False
    bpy.ops.node.detach('INVOKE_DEFAULT')
    return node_parent, frame_node

def join_parent_frame(selectedNodes, node_parent, frame_node):
    for node in selectedNodes:
        node.parent = node_parent[node.name]
    for node in frame_node:
        node.select = True

class SnapBottomSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_bottom_side_selection_nodes"
    bl_label = "Snap Bottom Side Selection Nodes"
    bl_description = "Snaps the bottom of all selected nodes"

    def execute(self, context):
        try:
            node_parent = dict()
            frame_node = []
            detach_parent_frame(node_parent, frame_node)       # 三行换九行
            
            selectedNodes = context.selected_nodes
            y_min = sort_location(selectedNodes)["y_min"]
            for node in selectedNodes:
                node.location.y = y_min + node.dimensions.y
            
            join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        except:
            pass
        return {"FINISHED"}

class SnapTopSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_top_side_selection_nodes"
    bl_label = "Snap Top Side Selection Nodes"
    bl_description = "Snaps the top of all selected nodes"

    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        y_max = sort_location(selectedNodes)["y_max"]
        for node in selectedNodes:
            node.location.y = y_max

        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        return {"FINISHED"}

class SnapRightSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_right_side_selection_nodes"
    bl_label = "Snap Right Side Selection Nodes"
    bl_description = "Snaps the right side of all selected nodes"

    def execute(self, context):
        try:
            node_parent = dict()
            frame_node = []
            detach_parent_frame(node_parent, frame_node)       # 三行换九行
            
            selectedNodes = context.selected_nodes
            x_max = sort_location(selectedNodes)["x_max"]
            for node in selectedNodes:
                node.location.x = x_max - node.width
            
            join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        except:
            pass

        return {"FINISHED"}

class SnapLeftSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_left_side_selection_nodes"
    bl_label = "Snap Left Side Selection Nodes"
    bl_description = "Snaps the left side of all selected nodes"

    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行

        selectedNodes = context.selected_nodes
        x_min = sort_location(selectedNodes)["x_min"]
        for node in selectedNodes:
            node.location.x = x_min

        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        return {"FINISHED"}

class Distribute_Horizontal(bpy.types.Operator, NodeOperator):
    bl_idname = "node.distribute_horizontal"
    bl_label = "Selection Nodes - distribute_horizontal"
    bl_description = "水平等距分布"
    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        node_infos = []
        num = 0 ; sum_width = 0
        for node in selectedNodes:
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
        
        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行

        return {"FINISHED"}

class Distribute_Vertical(bpy.types.Operator, NodeOperator):
    bl_idname = "node.distribute_vertical"
    bl_label = "Selection Nodes - distribute_vertical"
    bl_description = "垂直等距分布"

    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        node_infos = []
        num = 0 ; sum_height = 0
        for node in selectedNodes:
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
            
        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        return {"FINISHED"}

class Distribute_Grid_Relative(bpy.types.Operator, NodeOperator):
    bl_idname = "node.distribute_grid_relative"
    bl_label = "Selection Nodes - distribute_grid_relative"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列各自最大最小高度"
    def execute(self, context):
        print("开始..............................................................................................")

        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        node_infos = []
        for node in selectedNodes:
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
        for node in selectedNodes:
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
        
        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        print("结束..............................................................................................")
        return {"FINISHED"}

class Distribute_Grid_Absolute(bpy.types.Operator, NodeOperator):
    bl_idname = "node.distribute_grid_absolute"
    bl_label = "Selection Nodes - distribute_grid_absolute"
    bl_description = "网格分布-单独列垂直等距分布居中对齐,各列水平等距分布,每列最大最小高度一样"
    def execute(self, context):
        print("开始..............................................................................................")

        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        node_infos = []
        for node in selectedNodes:
            node_infos.append((node.location.x, node))
        node_infos.sort(key=lambda x: x[0])
        x_min = node_infos[0][0]
        x_max = node_infos[-1][0]
        num = ceil((x_max - x_min) / 140)
        print("x_min:", x_min)
        print("x_max:", x_max)
        print("num:", num)
        node_location_y = []        # 和上面列表和一块还要改下面的，懒得改了，新建一个
        for node in selectedNodes:
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
        for node in selectedNodes:
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

        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        print("结束..............................................................................................")
        return {"FINISHED"}

class SnapHeightCenterSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_height_center_selection_nodes"
    bl_label = "Snap Height Center Side Selection Nodes"
    bl_description = "Snaps the height center of all selected nodes"

    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行

        selectedNodes = context.selected_nodes
        y_center = sort_location(selectedNodes)["y_center"]
        for node in selectedNodes:
            node.location.y = y_center + node.dimensions.y / 2
                
        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        return {"FINISHED"}

class SnapWidthCenterSideSelectionNodes(bpy.types.Operator, NodeOperator):
    bl_idname = "node.snap_width_center_selection_nodes"
    bl_label = "Snap Width Center Side Selection Nodes"
    bl_description = "Snaps the width center of all selected nodes"

    def execute(self, context):
        node_parent = dict()
        frame_node = []
        detach_parent_frame(node_parent, frame_node)       # 三行换九行
        
        selectedNodes = context.selected_nodes
        x_center = sort_location(selectedNodes)["x_center"]
        for node in selectedNodes:
            node.location.x = x_center - node.width / 2
                
        join_parent_frame(selectedNodes, node_parent, frame_node)             # 一行换四行
        
        return {"FINISHED"}



def RecrGetNodeFinalLoc(nd):
    return nd.location + RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location
def UiScale():
    return bpy.context.preferences.system.dpi / 72
def Vector( *args): 
    return mathutils.Vector((args)) 
def TranslateIface(txt):
    return bpy.app.translations.pgettext_iface(txt)
# linear_interpolation
def lin_inter(x, 
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
    list_result = []
    dict_result = {}
    ndLoc = RecrGetNodeFinalLoc(nd)
    ndDim = mathutils.Vector(nd.dimensions / UiScale())
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
            skLocCarriage.y -= lin_inter(ui_scale) * in_out     # 缩放 1 -> 22  1.1 -> 21.88 
    return dict_result

class Straight_Link(bpy.types.Operator, NodeOperator):
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