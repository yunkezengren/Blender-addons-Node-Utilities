from .utils_translate import GetAnnotFromCls, VlTrMapForKey
from .v_tool import *
from .globals import *
from .utils_ui import *
from .utils_node import *
from .utils_color import *
from .utils_solder import *
from .utils_drawing import *
from .utils_translate import *
from .common_forward_func import *
from .common_forward_class import *
from .v_tool import VoronoiOpTool, VoronoiToolNd
from bpy.app.translations import pgettext_iface as TranslateIface


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



def VestLyAddEnumSelectorBox(where: UILayout, lyDomain=None):
    assert VestData.list_enumProps
    colMain = where.row()           # 显示节点选项优化-每个下拉列表，各占一列
    colDomain = lyDomain.column() if lyDomain else None
    nd = VestData.nd
    # 数学节点有高级的分类用于 .prop(), 但我不知道如何通过简单枚举手动显示它们. 反正有 VQMT.
    # 我没有忽略它们, 让它们按原样处理. 用它们选择矢量数学运算甚至非常方便 (普通数学运算放不下).
    # 域总是第一个. 例如, StoreNamedAttribute 和 FieldAtIndex 有相同的枚举, 但顺序不同; 有趣为什么.
    # print("开始-" * 20)
    # pprint("VestData.__dict__")
    # pprint(VestData.__dict__)
    # print("结束-" * 20)
    for cyc, li in enumerate(sorted(VestData.list_enumProps, key=lambda a:a.identifier!='domain')):
        if (cyc)and(colWhere!=colDomain):
            colProp.separator()
        colWhere = (colDomain if (lyDomain)and(li.identifier=='domain') else colMain)
        colProp = colWhere.column(align=True)  # 下拉列表的名称占一行，和选项列对齐
        if VestData.isDisplayLabels:
            rowLabel = colProp.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text=li.name)
            #rowLabel.active = not VestData.isPieChoice # 对于饼菜单, 边框是透明的, 文本可能会与背景中明亮的节点融合. 所以关闭了.
            rowLabel.active = not(VestData.isDarkStyle and VestData.isPieChoice) # 但对于深色饼菜单, 还是显示深色文本.
        elif cyc:
            colProp.separator()
        colEnum = colProp.column(align=True)     # 每个下拉列表，每个选项绘制一行
        colEnum.scale_y = VestData.boxScale
        if VestData.isDarkStyle:
            colEnum.prop_tabs_enum(nd, li.identifier)
        else:
            colEnum.prop(nd, li.identifier, expand=True)
    # 在我最初的想法中, 我错误地称这个工具为“Prop Selector”. 需要想办法区分节点的通用属性和在选项中绘制的属性.
    # 幸运的是, 每个节点没有不同的枚举...
class VestOpBox(VoronoiOpTool):
    bl_idname = 'node.voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    rename_store_node:   bpy.props.BoolProperty(default=True, description="隐藏选项时重命名存储属性等一些节点")
    def execute(self, context): # 用于下面的 draw(), 否则不显示.
        pass
    def draw(self, _context):
        VestLyAddEnumSelectorBox(self.layout)
    def invoke(self, context, event):
        # 显示节点选项优化-box宽度*列数
        width = 90 * VestData.boxScale * len(VestData.list_enumProps)
        return context.window_manager.invoke_popup(self, width=int(width))    # 必须要 int
        # return context.window_manager.invoke_popup(self, width=int(128*VestData.boxScale))
    def cancel(self, context):
        if self.rename_store_node:
            rename_node_based_option(VestData.nd)     # 显示节点选项优化-根据选项重命名节点-domain

class VestPieBox(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def draw(self, _context):
        pie = self.layout.menu_pie()
        def GetCol(where: UILayout, tgl=True):
            col = (where.box() if tgl else where).column()
            col.ui_units_x = 7*((VestData.boxScale-1)/2+1)            # 只对饼菜单显示选项有用
            # col.ui_units_x = 7*((VestData.boxScale-1)/2+1) * len(VestData.list_enumProps)
            return col
        colDom = GetCol(pie, any(True for li in VestData.list_enumProps if li.identifier=='domain'))
        colAll = GetCol(pie, any(True for li in VestData.list_enumProps if li.identifier!='domain'))
        VestLyAddEnumSelectorBox(colAll, colDom)


def rename_node_based_option(node):
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
        if node.mode == "EVALUATED":
            node.label = "曲线重采样: 已解算"
    if node.bl_idname == "ShaderNodeVectorRotate":
        rot_type = node.rotation_type
        if "_AXIS" in rot_type:
            node.label = "矢量旋转: " + rot_type.replace("_AXIS", "轴")
            if node.invert:
                node.label += " 反转"

class VoronoiEnumSelectorTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_enum_selector'
    bl_label = "Voronoi Enum Selector"
    usefulnessForCustomTree = True
    canDrawInAppearance = True
    isInstantActivation: bpy.props.BoolProperty(name="Instant activation",  default=True,  description="Skip drawing to a node and activation when release, and activate immediately when pressed")
    isPieChoice:         bpy.props.BoolProperty(name="Pie choice",          default=False, description="Allows to select an enum by releasing the key")
    isToggleOptions:     bpy.props.BoolProperty(name="Toggle node options", default=False)
    isSelectNode:        bpy.props.IntProperty(name="Select target node",  default=1, min=0, max=3, description="0 – Do not select.\n1 – Select.\n2 – And center.\n3 – And zooming")
    rename_store_node:   bpy.props.BoolProperty(default=True, description="隐藏选项时重命名存储属性等一些节点")
    def CallbackDrawTool(self, drata):              # 工具提示
        if self.isToggleOptions:
            mode = "隐藏选项"
            if self.firstResult == False:           # 最近节点选项是隐藏的，后续就是显示选项
                mode = "显示选项"
        else:
            mode = "切换选项"
        TemplateDrawNodeFull(drata, self.fotagoNd, tool_name=mode)
        # self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE', tool_name=name)
    def ToggleOptionsFromNode(self, nd, lastResult, isCanDo=False): # 工作原理复制自 VHT HideFromNode().
        if lastResult:
            success = nd.show_options
            if isCanDo:
                # 显示节点选项优化-根据选项重命名节点-domain
                if self.rename_store_node:
                    rename_node_based_option(nd)
                nd.show_options = False
            return success
        elif isCanDo:
            success = not nd.show_options
            nd.show_options = True
            return success
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE': # 对于这个工具, reroute 会被跳过, 原因很明显.
                continue
            # if nd.bl_idname in set_utilEquestrianPortalBlids:    # 注释掉
            #     continue
            # have_options = ["GeometryNodeBake", "GeometryNodeGroup",
            #                 "GeometryNodeForeachGeometryElementInput", "ShaderNodeTexCoord"]
            # if nd.bl_idname not in have_options:
            #     if not GetListOfNdEnums(nd):    # 想只对有下拉列表选项的节点绘制-导致节点组、bake、serpens里很多节点的 隐藏选项失效
            #         continue
            # if nd.hide: # 对于折叠的节点, 切换结果看不到, 所以忽略.
            #     continue              # 折叠的节点同样绘制
            if self.isToggleOptions:
                self.fotagoNd = ftgNd
                # 和 VHT 的意思一样:
                if prefs.vestIsToggleNodesOnDrag:
                    # print(f"{self.firstResult = }")
                    if self.firstResult is None:
                        self.firstResult = self.ToggleOptionsFromNode(nd, True)
                    self.ToggleOptionsFromNode(nd, self.firstResult, True)
                break
            elif GetListOfNdEnums(nd): # 为什么不忽略没有枚举属性的节点呢?.
                self.fotagoNd = ftgNd
                break
    def DoActivation(self, prefs, tree):
        def IsPtInRect(pos, rect): #return (pos[0]>rect[0])and(pos[1]>rect[1])and(pos[0]<rect[2])and(pos[1]>rect[3])
            if pos[0]<rect[0]:
                return False
            elif pos[1]<rect[1]:
                return False
            elif pos[0]>rect[2]:
                return False
            elif pos[1]>rect[3]:
                return False
            return True
        VestData.list_enumProps = GetListOfNdEnums(self.fotagoNd.tar)
        VestData.domain_item_list = get_node_domain_item_list(self.fotagoNd.tar)  # 显示节点选项优化-根据选项重命名节点-domain
        # print("-"*50)
        # print(self.fotagoNd.tar.name)
        # pprint(VestData.domain_item_list)
        # 如果什么都没有, 盒子调用还是会处理, 就像它存在一样, 导致不移动光标就无法再次调用工具.
        if VestData.list_enumProps: # 所以如果为空, 什么也不做. 还有 VestLyAddEnumSelectorBox() 中的 assert.
            ndTar = self.fotagoNd.tar
            VestData.nd = ndTar
            VestData.boxScale = prefs.vestBoxScale
            if ndTar.bl_idname == "ShaderNodeMath":
                VestData.boxScale = 0.9
            # VestData.boxScale = prefs.vestBoxScale * len(VestData.list_enumProps)  # 这个整体缩放，不是x方向缩放
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
                bpy.ops.wm.call_menu_pie(name=VestPieBox.bl_idname)
            else:
                # 更改节口类型-todo
                bpy.ops.node.voronoi_enum_selector_box('INVOKE_DEFAULT')
            # ops运行唤出菜单后生效,再更改选项不生效，不是实时更改name
            # # rename_node_based_option(ndTar)         # 显示节点选项优化-根据选项重命名节点-domain

            return True # 用于 modal(), 返回成功.
    def MatterPurposeTool(self, event, prefs, tree):
        if self.isToggleOptions:
            if not prefs.vestIsToggleNodesOnDrag: # 和 VHT 中一样.
                self.ToggleOptionsFromNode(self.fotagoNd.tar, self.ToggleOptionsFromNode(self.fotagoNd.tar, True), True)
        else:
            if not self.isInstantActivation:
                self.DoActivation(prefs, tree)
    def InitTool(self, event, prefs, tree):
        if (self.isInstantActivation)and(not self.isToggleOptions):
            # 注意: 盒子可能会完全覆盖节点及其连接线.
            self.NextAssignmentRoot(None)
            if not self.fotagoNd:
                return {'CANCELLED'}
            self.DoActivation(prefs, tree)
            return {'FINISHED'} # 完成工具很重要.
        self.firstResult = None # 理想情况下也应该在上面, 但不是必须的, 参见 isToggleOptions 的拓扑.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vestIsToggleNodesOnDrag')
    @staticmethod
    def LyDrawInAppearance(colLy, prefs): # 注意: 这是 @staticmethod.
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Box ").strip()+" (VEST)")
        LyAddHandSplitProp(colBox, prefs,'vestBoxScale')
        LyAddHandSplitProp(colBox, prefs,'vestDisplayLabels')
        LyAddHandSplitProp(colBox, prefs,'vestDarkStyle')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey("Box ") as dm:
            dm["ru_RU"] = "Коробка"
        ##
        with VlTrMapForKey(GetAnnotFromCls(cls,'isInstantActivation').name) as dm:
            dm["ru_RU"] = "Моментальная активация"
            dm["zh_CN"] = "直接打开饼菜单"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isInstantActivation').description) as dm:
            dm["ru_RU"] = "Пропустить рисование к ноду и активацию при отпускании, и активировать немедленно при нажатии"
            dm["zh_CN"] = "不勾选可以先根据鼠标位置动态选择节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPieChoice').name) as dm:
            dm["ru_RU"] = "Выбор пирогом"
            dm["zh_CN"] = "饼菜单选择"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPieChoice').description) as dm:
            dm["ru_RU"] = "Позволяет выбрать элемент отпусканием клавиши"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isToggleOptions').name) as dm:
            dm["ru_RU"] = "Переключение опций нода"
#            dm["zh_CN"] = "隐藏节点里的下拉列表"?
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNode').name) as dm:
            dm["ru_RU"] = "Выделять целевой нод"
            dm["zh_CN"] = "选择目标节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNode').description) as dm:
            dm["ru_RU"] = "0 – Не выделять.\n1 – Выделять.\n2 – и центрировать.\n3 – и приближать"
#            dm["zh_CN"] = ""
##
#* vestIsToggleNodesOnDrag 的翻译已在 VHT 中 *
        with VlTrMapForKey(GetPrefsRnaProp('vestBoxScale').name) as dm:
            dm["ru_RU"] = "Масштаб панели"
            dm["zh_CN"] = "下拉列表面板大小"
        with VlTrMapForKey(GetPrefsRnaProp('vestDisplayLabels').name) as dm:
            dm["ru_RU"] = "Отображать имена свойств перечислений"
            dm["zh_CN"] = "显示下拉列表属性名称"
        with VlTrMapForKey(GetPrefsRnaProp('vestDarkStyle').name) as dm:
            dm["ru_RU"] = "Тёмный стиль"
            dm["zh_CN"] = "暗色风格"


# 显示节点选项优化-根据选项重命名节点-不好用-自定义ops,单击按钮立即运行(缺点：按钮文本居中对齐，按钮上文本翻译有问题)
class SNA_OT_Change_Node_Domain_And_Name(bpy.types.Operator):
    bl_idname = "vor.change_node_domain_and_name"
    bl_label = ""
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    domain_item:  bpy.props.StringProperty(name='name', description='', default='', subtype='NONE', maxlen=0)

    def execute(self, context):
        node = VestData.nd
        node.domain = self.domain_item
        rename_node_based_option(node)
        return {"FINISHED"}
