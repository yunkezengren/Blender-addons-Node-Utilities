import bpy
from bpy.types import Area, Context, Event, Node, NodeTree, NodeSocket, Operator, SpaceNodeEditor, UILayout, View2D as View2d
from bpy.props import BoolProperty
from mathutils import Vector as Vec2
from time import perf_counter

from .Structure import RectBase, View2D
from .common_class import TryAndPass
from .common_class import Target
from .globals import set_utilTypeSkFields
from .utils.ui import user_node_keymap
from .preference import pref, VoronoiAddonPrefs
from .utils.drawing import draw_debug_info, draw_node_template, draw_sockets_template, Drawer
from .utils.node import nearest_nodes_tar, nearest_sockets_tar, RestoreCollapsedNodes, SaveCollapsedNodes, is_builtin_tree_idname
from .utils.solder import solder_sk_links, solder_theme_cols

def get_operator_keymap_item(self: type["BaseOperator"], event: Event):
    # Todo00: 有没有更正确的设计或方法?
    # 操作符可以有多种调用组合, 所有这些组合在 `keymap_items` 中的键都相同, 所以我们手动遍历所有
    idname = getattr(bpy.types, self.bl_idname).bl_idname
    for item in user_node_keymap().keymap_items:
        if item.idname != idname: continue
        # 注意: 也要按键本身是否匹配来搜索, 因为多个调用方式的修饰键也可能相同.
        if (item.type == event.type) and (item.shift_ui == event.shift) and (item.ctrl_ui == event.ctrl) and (item.alt_ui == event.alt):
            # 注意: 也可能有两个完全相同的调用热键, 但Blender只会执行其中一个 (至少对VL是这样), 即列表中排在前面的那个.
            return item  # 这个函数也只返回列表中的第一个.

class BaseOperator(Operator):
    bl_options = {'UNDO'}  # 手动创建的链接可以撤销, 所以在 VL 中也应如此. 对所有工具都一样.

    @classmethod
    def poll(cls, context):
        return context.area.type == 'NODE_EDITOR'  # 不知道为什么需要这个, 但还是留着吧.

# 定义了一组 抽象方法/占位方法 ，供子类实现。这实际上是 Mixin 模式 或 接口/协议类 。
class VlToolMixin: #-1
    use_for_custom_tree = None
    use_for_undef_tree = None
    use_for_none_tree = None
    can_draw_settings = None
    can_draw_appearance = None
    def callback_draw_tool(self, drawer: Drawer): pass
    def find_targets_tool(self, is_first_active: bool, prefs: VoronoiAddonPrefs, tree: NodeTree): pass
    def handle_modal(self, event: Event, prefs: VoronoiAddonPrefs): pass
    def run(self, event: Event, prefs: VoronoiAddonPrefs, tree: NodeTree): pass
    def initialize_pre(self, event: Event): return {}
    def initialize(self, event: Event, prefs: VoronoiAddonPrefs, tree: NodeTree): return {}
    @staticmethod
    def draw_pref_settings(col: UILayout, prefs: VoronoiAddonPrefs): pass
    @staticmethod
    def draw_pref_appearance(col: UILayout, prefs: VoronoiAddonPrefs): pass

class BaseTool(BaseOperator, VlToolMixin):  #0
    use_for_undef_tree = False
    use_for_none_tree = False
    can_draw_settings = True
    can_draw_appearance = False
    vlTripleName: str
    disclBoxPropName: str
    disclBoxPropNameInfo: str
    # 点击节点编辑器总是不可避免的, 那里有节点, 所以对于所有工具
    isPassThrough: BoolProperty(name="Pass through node selecting",
                                default=False,
                                description="Clicking over a node activates selection, not the tool")

    def callback_draw_base(self, drawer: Drawer, context: Context):
        if drawer.whereActivated != context.space_data:  # 需要只在活动的编辑器中绘制, 而不是在所有打开相同树的编辑器中绘制.
            return
        drawer.worldZoom = self.ctView2d.GetZoom()  # 每次都从 EdgePan 和鼠标滚轮获取. 以前可以一次性焊接.
        if self.prefs.dsIsFieldDebug:
            draw_debug_info(self, drawer)
        if self.tree:  # 现在对于没有树的情况可以不显示任何迹象; 由于拓扑结构的头疼问题以及在插件树中传递热键时工具的跳过问题而关闭 (?).
            self.callback_draw_tool(drawer)

    def get_nearest_nodes(self, includePoorNodes=False, cur_x_off: float = 0):
        self.cursorLoc.x += cur_x_off  # 唤起位置偏移
        return nearest_nodes_tar(self.tree.nodes[:], self.cursorLoc, self.uiScale, includePoorNodes)

    def get_nearest_sockets(self, nd: Node, cur_x_off: float = 0):
        self.cursorLoc.x += cur_x_off  #     唤起位置偏移
        return nearest_sockets_tar(nd, self.cursorLoc, self.uiScale)

    def find_targets_base(self, flag: bool):
        if self.tree:
            try:
                self.find_targets_tool(flag, self.prefs, self.tree)
            except:
                EdgePan.isWorking = False  # 现在只对 VLT 有效. 也许应该做个 ~self.ErrorToolProc, 并在 VLT 中 "退后一步".
                SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
                raise

    def modal_handle_mouse(self, event: Event, prefs: VoronoiAddonPrefs):
        match event.type:
            case 'MOUSEMOVE':
                self.find_targets_base(False)
            case self.kmi.type | 'ESC':
                if event.value == 'RELEASE':
                    return True
        return False

    def modal(self, context: Context, event: Event):
        context.area.tag_redraw()
        if num := (event.type == 'WHEELUPMOUSE') - (event.type == 'WHEELDOWNMOUSE'):
            self.ctView2d.cur.Zooming(self.cursorLoc, 1.0 - num*0.15)
        self.handle_modal(event, self.prefs)
        if not self.modal_handle_mouse(event, self.prefs):
            return {'RUNNING_MODAL'}
        #* 工具的结束从这里开始 *
        EdgePan.isWorking = False
        if event.type == 'ESC':  # 这正是 Escape 键应该做的.
            return {'CANCELLED'}
        with TryAndPass():  # 它可能已经被删除了, 参见第二个这样的情况.
            SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
        tree = self.tree
        if not tree:
            return {'FINISHED'}
        RestoreCollapsedNodes(tree.nodes)
        if (tree) and (tree.bl_idname == 'NodeTreeUndefined'):  # 如果来自某个插件的节点树消失了, 那么剩下的就是 NodeUndefined 和 NodeSocketUndefined.
            return {'CANCELLED'}  # 通过 API 无法创建到 SocketUndefined 的链接, 在这个树里也没什么可做的; 所以退出.
        ##
        if not self.can_run():
            return {'CANCELLED'}
        if result := self.run(event, self.prefs, tree):
            return result
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event):
        tree = context.space_data.edit_tree
        self.tree = tree
        editorBlid = context.space_data.tree_type  # 无需 `self.`?.
        self.in_builtin_tree = is_builtin_tree_idname(editorBlid)
        if not (self.use_for_custom_tree or self.in_builtin_tree):
            return {'PASS_THROUGH'}  #'CANCELLED'?.
        if (not self.use_for_undef_tree) and (editorBlid == 'NodeTreeUndefined'):
            return {'CANCELLED'}  # 为了不绘制而离开.
        if not (self.use_for_none_tree or tree):
            return {'FINISHED'}
        # 对所有工具相同的跳过选择处理
        if (self.isPassThrough) and (tree) and ('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):  # 检查树是第二位的, 为了美学优化.
            # 如果调用工具的热键与取消选择的热键相同, 那么上面一行选择的节点在交接后会重新取消选择 (但仍然是活动的).
            # 因此, 对于这种情况, 需要取消选择, 以便再次切换回已选择的节点.
            tree.nodes.active.select = False  # 但没有条件, 对所有情况都适用. 因为 ^ 否则将永远是选择而不切换; 我没有想法如何处理这种情况.
            return {'PASS_THROUGH'}
        ##
        self.kmi = get_operator_keymap_item(self, event)
        if not self.kmi:
            return {'CANCELLED'}  # 如果总体上出了问题, 或者操作符是通过布局按钮调用的.
        # 如果在 keymap 调用操作符时未指定其属性, 它们会从上次调用中读取; 所以需要将它们设置回默认值.
        # 尽早这样做是有意义的; 对 VQMT 和 VEST 有效.
        for li in self.rna_type.properties:
            if li.identifier != 'rna_type':
                # 注意: 判断是否在 kmi 中设置 -- `kmi.properties[li.identifier]` 的存在.
                setattr(self, li.identifier, getattr(self.kmi.properties, li.identifier))  # 为了这个我不得不反向工程 Blender 并进行调试. 原来是这么简单..
        ##
        self.prefs = pref()  # "原来是这么简单".
        self.uiScale = context.preferences.system.dpi / 72
        self.cursorLoc: Vec2 = context.space_data.cursor_location  # 这是 class Vector, 通过引用复制; 所以可以在这里设置(绑定)一次, 就不用担心了.
        self.drawer = Drawer(context, self.cursorLoc, self.uiScale, self.prefs)
        solder_theme_cols(context.preferences.themes[0].node_editor)  # 和 fontId 一样; 虽然在大多数情况下主题在整个会话期间不会改变.
        self.region = context.region
        self.ctView2d = View2D.GetFields(context.region.view2d)
        if self.prefs.vIsOverwriteZoomLimits:
            self.ctView2d.minzoom = self.prefs.vOwZoomMin
            self.ctView2d.maxzoom = self.prefs.vOwZoomMax
        ##
        if result := self.initialize_pre(event):  # 对于 'Pre' 返回某些内容不太重要.
            return result
        if result := self.initialize(event, self.prefs, tree):  # 注意: 参见拓扑结构: 不返回任何东西等同于返回 `{'RUNNING_MODAL'}`.
            return result
        edge_pan_init(self, context.area)
        ##
        self.handle = SpaceNodeEditor.draw_handler_add(self.callback_draw_base, (
            self.drawer,
            context,
        ), 'WINDOW', 'POST_PIXEL')
        if tree:  # 注意: 参见本地拓扑结构, 工具本身可以, 但每个工具都明确地对缺失的树禁用了.
            solder_sk_links(self.tree)
            SaveCollapsedNodes(tree.nodes)
            self.find_targets_base(True)  # 原来只需要在 modal_handler_add() 之前移动它. #https://projects.blender.org/blender/blender/issues/113479
        ##
        context.area.tag_redraw()  # 需要在激活时绘制找到的; 本地顺序不重要.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class SingleSocketTool(BaseTool):  #1

    def callback_draw_tool(self, drawer: Drawer):
        draw_sockets_template(drawer, self.target_sk)

    def can_run(self):
        return not not self.target_sk

    def initialize_pre(self, event: Event):
        self.target_sk = None

class PairSocketTool(SingleSocketTool):  #2
    isCanBetweenFields: BoolProperty(name="Can between fields",
                                     default=True,
                                     description="Tool can connecting between different field types")

    def callback_draw_tool(self, drawer: Drawer):
        draw_sockets_template(drawer, self.target_sk0, self.target_sk1)

    def check_between_sk_fields(self, sk1: NodeSocket, sk2: NodeSocket):
        # 注意: 考虑到此函数的目的和名称, sk1 和 sk2 无论如何都应该是来自字段, 且仅来自字段.
        return (sk1.type in set_utilTypeSkFields) and ((self.isCanBetweenFields) and (sk2.type in set_utilTypeSkFields) or
                                                       (sk1.type == sk2.type))

    def initialize_pre(self, event: Event):
        self.target_sk0 = None
        self.target_sk1 = None

class TripleSocketTool(PairSocketTool):  #3

    def handle_modal(self, event: Event, prefs: VoronoiAddonPrefs):
        if (self.isStartWithModf) and (not self.canPickThird):  # 谁会真的通过按下和释放某个修饰键来切换到选择第三个套接字呢?.
            # 因为这代价太高了; 既然选择了没有修饰键的热键, 那就满足于有限的功能吧. 或者自己动手.
            self.canPickThird = not (event.shift or event.ctrl or event.alt)

    def initialize_pre(self, event: Event):
        self.target_sk2 = None
        self.canPickThird = False
        self.isStartWithModf = (event.shift) or (event.ctrl) or (event.alt)

class SingleNodeTool(BaseTool):  #1

    def callback_draw_tool(self, drawer: Drawer):
        draw_node_template(drawer, self.target_nd)

    def can_run(self):
        return bool(self.target_nd)

    def initialize_pre(self, event: Event):
        self.target_nd = None

class PairNodeTool(SingleSocketTool):  #2

    def can_run(self):
        return self.target_nd0 and self.target_nd1

    def initialize_pre(self, event: Event):
        self.target_nd0 = None
        self.target_nd1 = None

class AnyTargetTool(SingleSocketTool, SingleNodeTool):  #2

    @staticmethod
    def template_draw_any(drawer: Drawer, tar: Target, *, cond: bool, tool_name=""):
        if cond:
            draw_node_template(drawer, tar, tool_name=tool_name)
        else:
            draw_sockets_template(drawer, tar, tool_name=tool_name)  # 绘制工具提示

    def can_run(self):
        return self.target_any

    def initialize_pre(self, event: Event):
        self.target_any = None

def unhide_node_reassign(nd: Node, self: BaseTool, *, cond: bool, flag=None):  # 我是多么鄙视折叠起来的节点啊.
    if nd.hide and cond:
        nd.hide = False
        # 注意: 在 find_targets_tool 的拓扑结构中要小心无限循环.
        # 警告! type='DRAW_WIN' 会导致某些罕见的带有折叠节点的节点树崩溃! 如果知道如何重现, 最好能报个bug.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        # todo0: 如果连续展开了多个节点, 应该只重绘一次; 但没必要. 如果发生了这种情况, 说明这个工具的搜索拓扑很糟糕.
        self.find_targets_base(flag)

class EdgePan:
    area: Area = None  # 本应是 'context', 但它总是 None.
    ctCur: RectBase = None
    # 快速凑合的:
    isWorking = False
    view2d: View2d = None
    cursorPos: Vec2 = Vec2((0, 0))
    uiScale = 1.0
    center: Vec2 = Vec2((0, 0))
    delta = 0.0  # 哦, 这些增量.
    zoomFac = 0.5
    speed = 1.0

def edge_pan_init(self: BaseTool, area: Area):
    EdgePan.area = area
    EdgePan.ctCur = self.ctView2d.cur
    EdgePan.isWorking = True
    EdgePan.cursorPos = self.cursorLoc
    EdgePan.uiScale = self.uiScale
    EdgePan.view2d = self.region.view2d
    EdgePan.center = Vec2((self.region.width / 2, self.region.height / 2))
    EdgePan.delta = perf_counter()  #..还有 "轻微边界".
    EdgePan.zoomFac = 1.0 - self.prefs.vEdgePanFac
    EdgePan.speed = self.prefs.vEdgePanSpeed
    bpy.app.timers.register(edge_pan_timer, first_interval=0.0)

def edge_pan_timer():
    delta = perf_counter() - EdgePan.delta
    vec = EdgePan.cursorPos * EdgePan.uiScale
    field0 = Vec2(EdgePan.view2d.view_to_region(vec.x, vec.y, clip=False))
    zoomWorld = (EdgePan.view2d.view_to_region(vec.x + 1000, vec.y, clip=False)[0] - field0.x) / 1000
    # 再来点光线步进:
    field1 = field0 - EdgePan.center
    field2 = Vec2((abs(field1.x), abs(field1.y)))
    field2 = field2 - EdgePan.center + Vec2((10, 10))  # 稍微减小光标紧贴屏幕边缘的边界.
    field2 = Vec2((max(field2.x, 0), max(field2.y, 0)))
    ##
    xi, yi, xa, ya = EdgePan.ctCur.GetRaw()
    speedZoomSize = Vec2((xa - xi, ya - yi)) / 2.5 * delta  # 没有 delta 时是 125.
    field1 = field1.normalized() * speedZoomSize * ((zoomWorld-1) / 1.5 + 1) * EdgePan.speed * EdgePan.uiScale
    if (field2.x != 0) or (field2.y != 0):
        EdgePan.ctCur.TranslateScaleFac((field1.x, field1.y), fac=EdgePan.zoomFac)
    EdgePan.delta = perf_counter()  # 在下一次进入前 "发送到未知处".
    EdgePan.area.tag_redraw()
    return 0.0 if EdgePan.isWorking else None
