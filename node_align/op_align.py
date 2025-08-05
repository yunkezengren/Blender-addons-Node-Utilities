import bpy
import ctypes
from bpy.types import Operator, NodeSocket, Node
from bpy.props import EnumProperty, IntProperty
from math import ceil
from mathutils import Vector as Vec2
from pprint import pprint
from .translator import i18n as tr

# for i in range(400):      # 节点树节点个数 400个时      1600个时
#     node.location.x -= 1            # 耗时 0.135465s    0.748193s
#     list.append(node.location.x)    # 耗时 0.000102s    0.000216s
# 400个节点  相对栅格分布: 0.3754s

def ui_scale():
    return bpy.context.preferences.system.dpi / 72      # 类似于prefs.view.ui_scale, 但是不同的显示器dpi不一样吗
def pref():
    assert __package__ is not None      # 断言 __package__ 在这里不可能是 None,因为 __getitem__ 接受的 key 只能是 int 或 str
    return bpy.context.preferences.addons[__package__].preferences
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

class BaseAlignOp(Operator):
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        i = sum(node.bl_idname != "NodeFrame" for node in context.selected_nodes)
        return context.space_data.edit_tree and i > 1

    def align_nodes(self, nodes):
        raise NotImplementedError("Subclasses must implement this method")

    def execute(self, context):
        node_parent_dict = {}
        frame_node_list = []
        detach_parent_frame(node_parent_dict, frame_node_list)      # 这里还会取消选择Frame
        select_nodes = context.selected_nodes
        # s_time = time.perf_counter()
        self.align_nodes(select_nodes)
        # print("对齐总耗时: ", f"{time.perf_counter() - s_time:.6f}s\n")
        restore_parent_frame(select_nodes, node_parent_dict, frame_node_list)   # 这里还会选回来
        return {"FINISHED"}

    # def show_popup(self, message):
    #     def draw_popup(self, context):
    #         self.layout.label(text=message, icon="NONE")
    #     bpy.context.window_manager.popup_menu(draw_popup, title="信息", icon="INFO")

class NODE_OT_align_left(BaseAlignOp):
    bl_idname = "node.align_left"
    bl_label = tr("对齐节点到最左侧")
    bl_description = tr("对齐选中点到最左侧")

    def align_nodes(self, nodes):
        # self.report({"INFO"}, "普通信息")
        # self.show_popup("测试弹窗普通信息")
        x_min = get_x_min(nodes)
        for node in nodes:
            node.location.x = x_min

class NODE_OT_align_right(BaseAlignOp):
    bl_idname = "node.align_right"
    bl_label = tr("对齐节点到最右侧")
    bl_description = tr("对齐选中点到最右侧")

    def align_nodes(self, nodes):
        x_max = get_x_max(nodes)
        for node in nodes:
            node.location.x = x_max - node.width

class NODE_OT_align_top(BaseAlignOp):
    bl_idname = "node.align_top"
    bl_label = tr("对齐节点到顶部")
    bl_description = tr("对齐选中节点到顶部")

    def align_nodes(self, nodes):
        y_max = get_y_max(nodes)
        for node in nodes:
            node.location.y = y_max

class NODE_OT_align_bottom(BaseAlignOp):
    bl_idname = "node.align_bottom"
    bl_label = tr("对齐节点到底部")
    bl_description = tr("对齐选中节点到底部")

    def align_nodes(self, nodes):
        y_min = get_y_min(nodes)
        for node in nodes:
            node.location.y = y_min + node.dimensions.y / ui_scale()

def align_height(nodes):
    y_center = get_y_center(nodes)
    for node in nodes:
        node.location.y = y_center + node.dimensions.y / 2 / ui_scale()

def align_width(nodes):
    x_center = get_x_center(nodes)
    for node in nodes:
        node.location.x = x_center - node.width / 2

class NODE_OT_align_heightcenter(BaseAlignOp):
    bl_idname = "node.align_height_center"
    bl_label = tr("对齐节点高度")
    bl_description = tr("对齐选中节点的高度中心,即居中分布")

    def align_nodes(self, nodes):
        align_height(nodes)

class NODE_OT_align_widthcenter(BaseAlignOp):
    bl_idname = "node.align_width_center"
    bl_label = tr("对齐节点宽度")
    bl_description = tr("对齐选中节点的宽度中心,即居中分布")

    def align_nodes(self, nodes):
        align_width(nodes)

# y_space 是想用自定义非偏好设置里的自定义宽度
def evenly_distribute_node(nodes, is_horizontal=False, is_vertical=False, min_p=None, max_p=None, y_space=None):
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
    # if node_num <= 1:   # 提前return的话,每列只有一个节点时,绝对栅格没顶对齐
    #     return node_infos
    if is_horizontal:
        node_infos.sort(key=lambda x: x[1])
        max_pos = node_infos[-1][1]
        # node_infos.sort(key=lambda x: x[0])
        node_infos.sort(key=lambda x: (x[0], -x[2].location.y))
        min_pos = node_infos[0][0]
    if is_vertical:
        node_infos.sort(key=lambda x: x[1])
        min_pos = node_infos[0][1]
        # node_infos.sort(key=lambda x: x[0], reverse=True)
        node_infos.sort(key=lambda x: (-x[0], x[2].location.x))
        max_pos = node_infos[0][0]
    if min_p is not None:
        min_pos = min_p
        max_pos = max_p
    interval = (max_pos - min_pos - total_size) / (node_num - 1) if node_num > 1 else 0  # 修复:绝对栅格分布无法在每列只有一个节点时,顶对齐

    sum_size = 0
    for i, node_info in enumerate(node_infos):
        if is_horizontal:
            interval = pref().space_x if pref().is_custom_space else interval
            node_info[2].location.x = min_pos + interval * i + sum_size
        if is_vertical:
            # interval = pref().space_y if pref().is_custom_space else interval
            if pref().is_custom_space:
                interval = pref().space_y
            if y_space is not None:
                interval = y_space
            node_info[2].location.y = max_pos - interval * i - sum_size
        sum_size += node_info[3]
    return node_infos

class NODE_OT_distribute_horizontal(BaseAlignOp):
    bl_idname = "node.distribute_horizontal"
    bl_label = tr("对齐-水平等距分布")
    bl_description = tr("水平方向节点之间间距一致")

    def align_nodes(self, nodes):
        evenly_distribute_node(nodes, is_horizontal=True)

class NODE_OT_distribute_vertical(BaseAlignOp):
    bl_idname = "node.distribute_vertical"
    bl_label = tr("对齐-垂直等距分布")
    bl_description = tr("垂直方向节点之间间距一致")

    def align_nodes(self, nodes):
        evenly_distribute_node(nodes, is_vertical=True)

class NODE_OT_align_width_vertical(BaseAlignOp):
    bl_idname = "node.align_width_vertical"
    bl_label = tr("等距对齐高度")
    bl_description = tr("对齐高度+垂直等距分布")

    def align_nodes(self, nodes):
        align_width(nodes)
        evenly_distribute_node(nodes, is_vertical=True)

class NODE_OT_align_height_horizontal(BaseAlignOp):
    bl_idname = "node.align_height_horizontal"
    bl_label = tr("等距对齐宽度")
    bl_description = tr("对齐宽度+水平等距分布")

    def align_nodes(self, nodes):
        align_height(nodes)
        evenly_distribute_node(nodes, is_horizontal=True)

class NODE_OT_distribute_horizontal_vertical(BaseAlignOp):
    bl_idname = "node.distribute_horizontal_vertical"
    bl_label = tr("对齐-水平垂直等距")
    bl_description = tr("水平+垂直等距分布")

    def align_nodes(self, nodes):
        # 对性能影响不太大吧,就不改函数内部,同时支持水平垂直对齐了
        evenly_distribute_node(nodes, is_horizontal=True)
        evenly_distribute_node(nodes, is_vertical=True)

def grid_distribute_node(nodes, min_pos=None, max_pos=None, x_space=None, y_space=None):
    node_infos = []
    for node in nodes:
        node_infos.append((node.location.x, node))
    node_infos.sort(key=lambda x: x[0])
    x_min = node_infos[0][0]        #
    x_max = node_infos[-1][0]
    # max_col_num = ceil((x_max - x_min) / 140)   # max_col_num 是最大的列数
    max_col_num = ceil((x_max - x_min) / pref().col_width)   # max_col_num 是最大的列数

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
            if node.location.x < rest_x_min + pref().col_width:   # 先左对齐
                node.location.x = rest_x_min                                        # ! 耗时的操作
                # node.location.x = rest_x_min - ((node.width - 140) / 2)       # 不知道什么用
                require_align_nodes.append(node_info[1])
        node_infos = node_infos[len(require_align_nodes):]
        # 由于每列的等距有自定义间距,导致绝对不够绝对
        node_list = evenly_distribute_node(require_align_nodes, is_vertical=True, min_p=min_pos, max_p=max_pos, y_space=y_space)   # ! 耗时的操作
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

    # 每列 水平等距分布 + 对齐宽度
    x_max = max(info[2].location.x+info[2].width for info in vertical_node_l_l[-1])    # 垂直等距分布过的,里面存的是y相关,最后(右)一列
    interval = (x_max - x_min - sum_width) / (col_num - 1) if col_num > 1 else 0
    if pref().is_custom_space:
        interval = pref().space_x
    if x_space is not None:
        interval = x_space
    for i, vertical_node_l in enumerate(vertical_node_l_l):
        for node_info in vertical_node_l:
            node = node_info[2]
            align = (col_max_width_l[i] -node.width) / 2 + sum_width_l[i-1]*(i!=0)
            node.location.x = x_min + interval*i + align                            # ! 耗时的操作

class NODE_OT_distribute_grid_relative(BaseAlignOp):
    bl_idname = "node.distribute_grid_relative"
    bl_label = tr("对齐-相对网格分布")
    bl_description = tr("每一列先垂直等距分布,各列之间水平等距分布,每列对齐宽度居中对齐")

    def align_nodes(self, nodes):
        grid_distribute_node(nodes)

class NODE_OT_distribute_grid_absolute(BaseAlignOp):
    bl_idname = "node.distribute_grid_absolute"
    bl_label = tr("对齐-绝对网格分布")
    bl_description = tr("每一列先垂直等距分布,各列之间水平等距分布,每列对齐宽度居中对齐,每列最大最小高度一样")

    def align_nodes(self, nodes):
        y_min = get_y_min(nodes)
        y_max = get_y_max(nodes)
        grid_distribute_node(nodes, min_pos=y_min, max_pos=y_max)       # 使得每列顶对齐,列长一样

class NODE_OT_distribute_row_column(BaseAlignOp):
    bl_idname = "node.distribute_row_column"
    bl_label = tr("对齐-改变行列数")
    bl_description = tr("例:20行20列节点,改成10列就是40行")

    align_mode: EnumProperty(name=tr("对齐方式"), description=tr("把选中节点改成多少行或列"), default='ROW',
                             items=[('ROW', tr("行"), tr("更改行数")), ('COLUMN', tr("列"), tr("更改列数"))])
    count     : IntProperty(name=tr("行或列数"),  description=tr("列模式:count=0是1行;行模式:count=0是1列"), default=5, min=0, max=500)
    x_interval: IntProperty(name=tr("x方向间隔"), description=tr("x方向两个节点之间间隔"), default=40, min=0, max=500)
    y_interval: IntProperty(name=tr("y方向间隔"), description=tr("y方向两个节点之间间隔"), default=40, min=0, max=500)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def align_nodes(self, nodes):
        x_min = get_x_min(nodes)
        y_max = get_y_max(nodes)
        nodes.sort(key=lambda node: node.location.x * 100 - node.location.y)
        # for i, node in enumerate(nodes):
        #     node.label = str(int(node.location.x * 100 - node.location.y))
        #     node.label = "号:" + str(i+1)
        count = self.count if self.count else len(nodes)
        nums = ceil(len(nodes) / count)
        for i in range(count):
            node_list = nodes[i*nums : (i+1)*nums]      # 一行或一行节点
            if not node_list: break
            for j, node in enumerate(node_list):
                if self.align_mode == 'ROW':
                    node.location.x = x_min + 200*j
                    node.location.y = y_max - 200*i     # 先每列 y 相同
                if self.align_mode == 'COLUMN':
                    node.location.x = x_min + 200*i     # 先每列 x 相同
                    node.location.y = y_max - 200*j
        grid_distribute_node(nodes, x_space=self.x_interval, y_space=self.y_interval)
        return {'FINISHED'}

def sk_loc(socket: NodeSocket):
    """ 草,问题出在这个运行时数据,界面刷新时才更新 """
    try:
        return Vec2((ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24))
    except:
        return socket.node.location

def linked_valid(sk: NodeSocket):
    return sk.enabled and sk.is_linked and not sk.hide

class NODE_OT_align_link(Operator):
    bl_idname = "node.align_link"
    bl_label = tr("对齐-拉直连线")
    bl_description = tr("选中节点,以活动节点为中心,拉直输入输出接口之间的连线")
    bl_options = {'REGISTER', 'UNDO'}
    
    # 在类级别声明实例属性的 "蓝图"
    timer: bpy.types.Timer
    aligned_nodes: list[Node]    # 从已对齐的节点出发找没对齐的
    index: int
    iter_index: int

    @classmethod
    def poll(cls, context):
        i = sum(node.bl_idname != "NodeFrame" for node in context.selected_nodes)
        return context.space_data.edit_tree and i >= 2

    def invoke(self, context, event):
        # --- 初始化 ---
        a_node = context.active_node
        if a_node is None or not a_node.select:
            a_node = context.selected_nodes[0]

        self.index = 0
        self.iter_index = 0
        self.aligned_nodes = [a_node]

        # --- 启动模态和定时器 ---
        wm = context.window_manager
        # 定时器间隔非常短, 比如 0.01 秒, 看起来就像动画一样
        self.timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # --- 退出条件 ---
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        # --- 核心逻辑: 在定时器事件中执行 ---
        if event.type == 'TIMER':
            # 如果队列空了, 说明所有节点都处理完了
            if self.index >= len(self.aligned_nodes):
                while self.iter_index < len(context.selected_nodes):
                    node = context.selected_nodes[self.iter_index]
                    self.iter_index += 1
                    if node not in self.aligned_nodes:
                        self.aligned_nodes.append(node)
                        return {'RUNNING_MODAL'}
                self.cancel(context)
                return {'FINISHED'}

            node = self.aligned_nodes[self.index]
            for sk_in in node.inputs:
                if linked_valid(sk_in):
                    link = sk_in.links[0]
                    from_nd = link.from_node
                    from_sk = link.from_socket
                    
                    # 检查邻居节点是否需要处理
                    if from_nd.select and (from_nd not in self.aligned_nodes) and linked_valid(from_sk):
                        from_nd.location.y += (sk_loc(sk_in).y - sk_loc(from_sk).y) / ui_scale()
                        self.aligned_nodes.append(from_nd)

            for sk_out in node.outputs:
                if linked_valid(sk_out):
                    for link in sk_out.links:
                        to_nd = link.to_node
                        to_sk = link.to_socket
                        if to_nd.select and (to_nd not in self.aligned_nodes) and linked_valid(to_sk):
                            to_nd.location.y += (sk_loc(sk_out).y - sk_loc(to_sk).y) / ui_scale()
                            self.aligned_nodes.append(to_nd)

            self.index += 1
            # 强制重绘视图, 以便下一次timer事件能读到最新的sk_loc
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def cancel(self, context):
        """清理定时器"""
        context.window_manager.event_timer_remove(self.timer)
