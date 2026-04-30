import bpy
from bpy.types import EnumProperty, UILayout, Node, Menu
from ..base_tool import BaseOperator, SingleNodeTool
from ..common_class import VestData
from ..utils.drawing import draw_node_template
from ..utils.node import node_show_name, node_enum_props, node_visible_menu_inputs, SelectAndActiveNdOnly
from ..utils.ui import split_prop, draw_panel_column, split_prop
bp = bpy.props

domain_en = [
    'POINT',
    'EDGE',
    'FACE',
    'CORNER',
    'CURVE',
    'INSTANCE',
    'LAYER',
]
domain_ch = [
    '点',
    '边',
    '面',
    '面拐',
    '样条线',
    '实例',
    '层',
]

mesh_domain_en = [
    'VERTICES',
    'EDGES',
    'FACES',
    'CORNERS',
]
mesh_domain_ch = ['顶点', '边', '面', '拐角']
get_domain_cn = {k: v for k, v in zip(domain_en, domain_ch)}
get_mesh_domain_cn = {k: v for k, v in zip(mesh_domain_en, mesh_domain_ch)}

def draw_enum_property_selectors(layout: UILayout):
    assert VestData.list_length
    node = VestData.nd
    main_col = layout.row()

    enum_props = sorted(VestData.enum_props, key=lambda prop: prop.identifier != 'domain')  # 让 域 排在第一个
    all_items = enum_props + VestData.menu_sockets

    for index, item in enumerate(all_items):
        menu_name = item.name
        if isinstance(item, EnumProperty):
            data = node
            prop_name = item.identifier
        else:
            data = item
            prop_name = "default_value"

        prop_col = main_col.column(align=True)  # 下拉列表的名称占一行，和选项列对齐
        prop_col.scale_y = VestData.boxScale

        if VestData.isPieChoice:
            prop_col.ui_units_x = 5
        if VestData.isDisplayLabels:
            label_row = prop_col.row(align=True)
            label_row.alignment = 'CENTER'
            label_row.label(text=menu_name)
            label_row.active = not (VestData.isDarkStyle and VestData.isPieChoice)  # 但对于深色饼菜单, 还是显示深色文本.
        elif index:
            prop_col.separator()

        # 每个下拉列表，每个选项绘制一行
        if VestData.isDarkStyle:
            prop_col.prop_tabs_enum(data, prop_name)
        else:
            prop_col.prop(data, prop_name, expand=True)
            if VestData.isPieChoice and isinstance(data, bpy.types.NodeSocketMenu):
                # todo: 解决这里为什么不显示 menu_sockets
                prop_col.label(text="有需求再修")

class NODE_OT_enum_selector_box(BaseOperator):
    bl_idname = 'node.enum_selector_box'
    bl_label = "Enum Selector"
    rename_node: bp.BoolProperty(default=True, description="Rename nodes when hiding options, currently only support Chinese")

    def execute(self, context):  # 用于下面的 draw(), 否则不显示.
        pass

    def draw(self, _context):
        draw_enum_property_selectors(self.layout)

    def invoke(self, context, event):
        width = 90 * VestData.boxScale * VestData.list_length
        return context.window_manager.invoke_popup(self, width=int(width))  # 必须要 int

    def cancel(self, context):
        run_rename_node(self.rename_node, VestData.nd)

class NODE_MT_enum_selector_pie(Menu):
    bl_idname = 'NODE_MT_enum_selector_pie'
    bl_label = "Enum Selector"
    def draw(self, _context):
        pie = self.layout.menu_pie()
        pie.row()
        draw_enum_property_selectors(pie.box().column())
        pie.row()
        pie.row().box().label(text=node_show_name(VestData.nd))

def rename_node_based_option(node: Node):
    """ 节点根据选项重命名 """
    nodes_has_domin = [ "GeometryNodeFieldOnDomain", "GeometryNodeFieldAtIndex",
                        "GeometryNodeSampleIndex", "GeometryNodeSampleNearest",
                        "GeometryNodeStoreNamedAttribute", "GeometryNodeCaptureAttribute",
                        "GeometryNodeSeparateGeometry", "GeometryNodeDeleteGeometry",
                        ]
    if node.bl_idname in nodes_has_domin:
        domain_cn = get_domain_cn[node.domain]
        if node.bl_idname == "GeometryNodeFieldOnDomain":
            node.label = "在" + domain_cn + "域上评估"
        if node.bl_idname == "GeometryNodeFieldAtIndex":
            node.label = "在" + domain_cn + "编号上评估"
        if node.bl_idname == "GeometryNodeSampleIndex":
            node.label = "采样" + domain_cn + "编号"
        if node.bl_idname == "GeometryNodeSampleNearest":
            node.label = "采样最近的" + domain_cn + "编号"
        if node.bl_idname == "GeometryNodeStoreNamedAttribute":
            attr_name = node.inputs["Name"].default_value
            if attr_name:
                node.label = domain_cn + ": " + attr_name
            else:
                node.label = "存储" + domain_cn + "属性"
        if node.bl_idname == "GeometryNodeCaptureAttribute":
            node.label = "捕捉" + domain_cn + "属性"
        if node.bl_idname == "GeometryNodeSeparateGeometry":
            node.label = "分离" + domain_cn
        if node.bl_idname == "GeometryNodeDeleteGeometry":
            node.label = "删除" + domain_cn

    if node.bl_idname == "GeometryNodeInputNamedAttribute":
        attr_name = node.inputs["Name"].default_value
        if attr_name:
            node.label = "属性: " + attr_name

    if node.bl_idname == "GeometryNodeMeshToPoints":
        domain_cn = get_mesh_domain_cn[node.mode]
        node.label = domain_cn + " -> 点"
    if node.bl_idname == "GeometryNodeResampleCurve":
        if hasattr(node, "mode") and node.mode == "EVALUATED":
            node.label = "曲线重采样: 已解算"
    if node.bl_idname == "ShaderNodeVectorRotate":
        rot_type = node.rotation_type
        if "_AXIS" in rot_type:
            node.label = "矢量旋转: " + rot_type.replace("_AXIS", "轴")
            if node.invert:
                node.label += " 反转"

def run_rename_node(rename: bool, node: Node):
    if rename and bpy.app.translations.locale in ["zh_Hans", "zh_CN", "zh_HANS", "ZH_HANT"]:
        rename_node_based_option(node)

class NODE_OT_voronoi_enum_selector(SingleNodeTool):
    bl_idname = 'node.voronoi_enum_selector'
    bl_label = "Voronoi Enum Selector"
    bl_description = "Tool for convenient lazy switching of enumeration properties.\nEliminates the need for mouse aiming, clicking, and then aiming and clicking again."
    use_for_custom_tree = True
    can_draw_appearance = True
    isInstantActivation: bp.BoolProperty(name="Instant activation",  default=True, description="Skip drawing to a node and activation when release, and activate immediately when pressed")
    isPieChoice:         bp.BoolProperty(name="Pie choice",          default=False, description="Allows to select an enum by releasing the key")
    isToggleOptions:     bp.BoolProperty(name="Toggle node options", default=False)
    isSelectNode:        bp.IntProperty(name="Select target node",   default=1, min=0, max=3, description="0 – Do not select.\n1 – Select.\n2 – And center.\n3 – And zooming")
    rename_node:         bp.BoolProperty(name="Rename Node Only Chinese", default=True, description="Rename nodes when toggling options, currently only support Chinese")
    def callback_draw(self, drawer):              # 工具提示
        if self.isToggleOptions:
            mode = "Hide Options"
            if self.firstResult == False:           # 最近节点选项是隐藏的，后续就是显示选项
                mode = "Show Options"
        else:
            mode = "Toggle Options"
        draw_node_template(drawer, self.target_nd, tool_name=mode)
    def ToggleOptionsFromNode(self, nd, lastResult, isCanDo=False): # 工作原理复制自 VHT HideFromNode().
        if lastResult:
            success = nd.show_options
            if isCanDo:
                run_rename_node(self.rename_node, nd)
                nd.show_options = False
            return success
        elif isCanDo:
            success = not nd.show_options
            nd.show_options = True
            return success
    def find_targets(self, _is_first_active, prefs, tree):
        self.target_nd = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            node = tar_nd.tar
            if node.type=='REROUTE': # 对于这个工具, reroute 会被跳过, 原因很明显.
                continue
            if self.isToggleOptions:
                self.target_nd = tar_nd
                # 和 VHT 的意思一样:
                if prefs.vestIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        self.firstResult = self.ToggleOptionsFromNode(node, True)
                    self.ToggleOptionsFromNode(node, self.firstResult, True)
                break
            elif node_enum_props(node) or node_visible_menu_inputs(node):
                self.target_nd = tar_nd
                break
    def DoActivation(self, prefs, tree):
        def IsPtInRect(pos, rect):
            if pos[0]<rect[0]:
                return False
            elif pos[1]<rect[1]:
                return False
            elif pos[0]>rect[2]:
                return False
            elif pos[1]>rect[3]:
                return False
            return True
        VestData.enum_props = node_enum_props(self.target_nd.tar)
        VestData.menu_sockets = node_visible_menu_inputs(self.target_nd.tar)
        VestData.list_length = len(VestData.enum_props) + len(VestData.menu_sockets)
        # 如果什么都没有, 盒子调用还是会处理, 就像它存在一样, 导致不移动光标就无法再次调用工具.
        if VestData.list_length:
            ndTar = self.target_nd.tar
            VestData.nd = ndTar
            VestData.boxScale = prefs.vestBoxScale
            if ndTar.bl_idname == "ShaderNodeMath":
                VestData.boxScale = 0.9
            # VestData.boxScale = prefs.vestBoxScale * len(VestData.enum_props)  # 这个整体缩放，不是x方向缩放
            VestData.isDarkStyle = prefs.vestDarkStyle
            VestData.isDisplayLabels = prefs.vestDisplayLabels
            VestData.isPieChoice = self.isPieChoice
            if self.isSelectNode:
                SelectAndActiveNdOnly(VestData.nd)
                if self.isSelectNode>1:
                    # 判断节点是否在屏幕外; 只有这样才居中:
                    region = self.region
                    vec = ndTar.location.copy()
                    tup1 = region.view2d.view_to_region(vec.x, vec.y, clip=False)
                    vec.x += ndTar.dimensions.x
                    vec.y -= ndTar.dimensions.y
                    tup2 = region.view2d.view_to_region(vec.x, vec.y, clip=False)
                    rect = (region.x, region.y, region.width, region.height)
                    if not(IsPtInRect(tup1, rect) and IsPtInRect(tup2, rect)):
                        if self.isSelectNode==3:
                            # "HACK", (但还需要重绘):
                            rr1 = tree.nodes.new('NodeReroute')
                            rr1.location = (ndTar.location.x-360, ndTar.location.y)
                            rr2 = tree.nodes.new('NodeReroute')
                            rr2.location = (ndTar.location.x+360, ndTar.location.y)
                            bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
                        bpy.ops.node.view_selected('INVOKE_DEFAULT')
                        if self.isSelectNode==3:
                            tree.nodes.remove(rr1)
                            tree.nodes.remove(rr2)
            if self.isPieChoice:
                bpy.ops.wm.call_menu_pie(name=NODE_MT_enum_selector_pie.bl_idname)
            else:
                # 更改节口类型-todo
                bpy.ops.node.enum_selector_box('INVOKE_DEFAULT')
            # ops运行唤出菜单后生效,再更改选项不生效，不是实时更改name
            # # rename_node_based_option(ndTar)
            return True # 用于 modal(), 返回成功.
    def run(self, event, prefs, tree):
        if self.isToggleOptions:
            if not prefs.vestIsToggleNodesOnDrag: # 和 VHT 中一样.
                self.ToggleOptionsFromNode(self.target_nd.tar, self.ToggleOptionsFromNode(self.target_nd.tar, True), True)
        else:
            if not self.isInstantActivation:
                self.DoActivation(prefs, tree)
    def initialize(self, event, prefs, tree):
        if (self.isInstantActivation)and(not self.isToggleOptions):
            # 注意: 盒子可能会完全覆盖节点及其连接线.
            self.find_targets_base(None)
            if not self.target_nd:
                return {'CANCELLED'}
            self.DoActivation(prefs, tree)
            return {'FINISHED'} # 完成工具很重要.
        self.firstResult = None # 理想情况下也应该在上面, 但不是必须的, 参见 isToggleOptions 的拓扑.
    @staticmethod
    def draw_pref_settings(col, prefs):
        split_prop(col, prefs,'vestIsToggleNodesOnDrag')
    @staticmethod
    def draw_pref_appearance(col, prefs): # 注意: 这是 @staticmethod.
        if body_col := draw_panel_column(col, "Enum Select Box"):
            split_prop(body_col, prefs,'vestBoxScale')
            split_prop(body_col, prefs,'vestDisplayLabels', bool_label_left=True)
            split_prop(body_col, prefs,'vestDarkStyle', bool_label_left=True)
