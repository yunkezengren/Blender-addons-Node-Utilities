import bpy
import rna_keymap_ui
from typing import Callable
from bpy.app.translations import pgettext_iface as _iface
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, StringProperty
from bpy.types import KeyMapItem, UILayout, Operator, AddonPreferences

from .common_class import VlnstUpdateLastExecError
from .utils.ui import split_prop, draw_panel_column, ColumnSetActive, add_thin_sep, format_tool_label, user_node_keymap

HIDE_BOOL_SOCKET_ITEMS = [
    ('ALWAYS', "Always", "Always"),
    ('IF_FALSE', "If false", "If false"),
    ('NEVER', "Never", "Never"),
    ('IF_TRUE', "If true", "If true"),
]

def update_test_draw(self, context):
    from .utils.drawing import TestDraw
    TestDraw.Toggle(context, self.dsIsTestDrawing)

is_updating_decor_color = False

def update_decor_color_socket(self, _context):
    global is_updating_decor_color
    if is_updating_decor_color:
        return
    is_updating_decor_color = True
    self.vaDecorColSk = self.vaDecorColSkBack
    is_updating_decor_color = False

class KeymapItemGroup:
    """快捷键项分类 - 用于组织和过滤keymap items"""
    group_key: str
    prop_name: str
    matched_items: set
    idnames: set
    count: int
    filter_func: Callable[[KeyMapItem], bool] | None

    def __init__(self, group_key='', prop_name='', matched_items=set(), idnames=set()):
        self.group_key = group_key
        self.prop_name = prop_name
        self.matched_items = matched_items
        self.idnames = idnames
        self.count = 0
        self.filter_func = None

class KeymapItemGroups:
    """快捷键项分类容器 - 管理多个KeymapItemCategory实例"""
    most_useful: KeymapItemGroup
    quite_useful: KeymapItemGroup
    maybe_useful: KeymapItemGroup
    invalid: KeymapItemGroup
    quick_math: KeymapItemGroup
    custom: KeymapItemGroup

def build_keymap_item_groups() -> KeymapItemGroups:
    from . import keymap_groups
    kmi_groups = KeymapItemGroups()
    kmi_groups.quick_math = KeymapItemGroup('quick_math', 'vaKmiQqmDiscl', set(), keymap_groups.quick_math)
    kmi_groups.custom = KeymapItemGroup('custom', 'vaKmiCustomDiscl', set(), keymap_groups.custom)
    kmi_groups.most_useful = KeymapItemGroup('most_useful', 'vaKmiMainstreamDiscl', set(), keymap_groups.most_useful)
    kmi_groups.quite_useful = KeymapItemGroup('quite_useful', 'vaKmiOtjersDiscl', set(), keymap_groups.quite_useful)
    kmi_groups.maybe_useful = KeymapItemGroup('maybe_useful', 'vaKmiSpecialDiscl', set(), keymap_groups.maybe_useful)
    kmi_groups.invalid = KeymapItemGroup('invalid', 'vaKmiInvalidDiscl', set(), keymap_groups.invalid)
    kmi_groups.most_useful.filter_func = lambda kmi: kmi.idname in kmi_groups.most_useful.idnames
    kmi_groups.quite_useful.filter_func = lambda kmi: kmi.idname in kmi_groups.quite_useful.idnames
    kmi_groups.maybe_useful.filter_func = lambda kmi: kmi.idname in kmi_groups.maybe_useful.idnames
    kmi_groups.invalid.filter_func = lambda kmi: True
    kmi_groups.quick_math.filter_func = lambda kmi: any(
        True for txt in {'quickOprFloat', 'quickOprVector', 'quickOprBool', 'quickOprColor', 'justPieCall', 'isRepeatLastOperation'}
        if getattr(kmi.properties, txt, None))
    kmi_groups.custom.filter_func = lambda kmi: kmi.id < 0  # 负id用于自定义
    return kmi_groups


def populate_keymap_item_groups(node_kms) -> KeymapItemGroups:
    kmi_groups = build_keymap_item_groups()
    for li in node_kms.keymap_items:
        if li.idname.startswith("node.voronoi_"):
            for dv in kmi_groups.__dict__.values():
                if dv.filter_func(li):
                    dv.matched_items.add(li)
                    dv.count += 1
                    break
    return kmi_groups

class VoronoiOpAddonTabs(Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    opt: StringProperty()

    def invoke(self, context, event):
        prefs = pref()
        match self.opt:
            case 'copy_settings':
                from .逐渐弃用 import get_addon_settings_as_py as addon_settings
                context.window_manager.clipboard = addon_settings(prefs)
            case 'add_new_kmi':
                user_node_keymap().keymap_items.new("node.voronoi_", 'D', 'PRESS').show_expanded = True
            case opt if opt.startswith("toggle_kmi_group:"):
                group_key = opt.split(":", 1)[1]
                kmi_groups = populate_keymap_item_groups(user_node_keymap())
                category = getattr(kmi_groups, group_key, None)
                if category and category.matched_items:
                    should_activate = not any(kmi.active for kmi in category.matched_items)
                    for kmi in category.matched_items:
                        kmi.active = should_activate
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

class VoronoiAddonPrefs(AddonPreferences):
    bl_idname = __package__ # type: ignore
    # --- VoronoiLinkerTool
    vltRepickKey            : StringProperty(name="Repick Key", default='LEFT_ALT', description="Hold this key to re-pick target socket without releasing the mouse")
    vltReroutesCanInAnyType : BoolProperty(name="Reroutes can be connected to any type", default=True)
    vltDeselectAllNodes     : BoolProperty(name="Deselect all nodes on activate",        default=False)
    vltPriorityIgnoring     : BoolProperty(name="Priority ignoring",                     default=False, description="High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)")
    vltSelectingInvolved    : BoolProperty(name="Selecting involved nodes",              default=False)
    # --- VoronoiPreviewTool
    vptAllowClassicGeoViewer        : BoolProperty(name="Allow classic GeoNodes Viewer",   default=True,  description="Allow use of classic GeoNodes Viewer by clicking on node")
    vptAllowClassicCompositorViewer : BoolProperty(name="Allow classic Compositor Viewer", default=False, description="Allow use of classic Compositor Viewer by clicking on node")
    vptIsLivePreview                : BoolProperty(name="Live Preview",                    default=True,  description="Real-time preview")
    vptRvEeIsColorOnionNodes        : BoolProperty(name="Node onion colors",               default=False, description="Coloring topologically connected nodes")
    vptRvEeSksHighlighting          : BoolProperty(name="Topology connected highlighting", default=False, description="Display names of sockets whose links are connected to a node")
    vptRvEeIsSavePreviewResults     : BoolProperty(name="Save preview results",            default=False, description="Create a preview through an additional node, convenient for copying")
    vptOnionColorIn                 : FloatVectorProperty(name="Onion color entrance", default=(0.55,  0.188, 0.188), min=0, max=1, size=3, subtype='COLOR')
    vptOnionColorOut                : FloatVectorProperty(name="Onion color exit",     default=(0.188, 0.188, 0.5),   min=0, max=1, size=3, subtype='COLOR')
    vptHlTextScale                  : FloatProperty(name="Text scale", default=1.0, min=0.5, max=5.0)
    # ------
    vmtReroutesCanInAnyType  : BoolProperty(name="Reroutes can be mixed to any type", default=True)
    ##
    vmtPieType               : EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vmtPieScale              : FloatProperty(name="Pie scale",                default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vmtPieAlignment          : IntProperty(  name="Alignment between items",  default=1,   min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vmtPieSocketDisplayType  : IntProperty(  name="Display socket type info", default=1,   min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vmtPieDisplaySocketColor : IntProperty(  name="Display socket color",     default=-1,  min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")
    # ------
    vqmtDisplayIcons         : BoolProperty(name="Display icons",           default=True)
    vqmtIncludeThirdSk       : BoolProperty(name="Include third socket",    default=True)
    vqmtIncludeQuickPresets  : BoolProperty(name="Include quick presets",   default=False)
    vqmtIncludeExistingValues: BoolProperty(name="Include existing values", default=False)
    vqmtRepickKey            : StringProperty(name="Repick Key", default='LEFT_ALT', description="Hold this key to re-pick target socket without releasing the mouse")
    ##
    vqmtPieType              : EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vqmtPieScale             : FloatProperty(name="Pie scale",                default=1.3,  min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieScaleExtra        : FloatProperty(name="Pie scale extra",          default=1.25, min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieAlignment         : IntProperty(  name="Alignment between items",  default=1,    min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vqmtPieSocketDisplayType : IntProperty(  name="Display socket type info", default=1,    min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vqmtPieDisplaySocketColor: IntProperty(  name="Display socket color",     default=-1,   min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")
    # ------
    vrtIsLiveRanto           : BoolProperty(name="Live Ranto", default=True)
    vrtIsFixIslands          : BoolProperty(name="Fix islands", default=True)
    # ------
    vhtHideBoolSocket        : EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=HIDE_BOOL_SOCKET_ITEMS)
    vhtHideHiddenBoolSocket  : EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=HIDE_BOOL_SOCKET_ITEMS)
    vhtNeverHideGeometry     : EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False",""), ('ONLY_FIRST',"Only first",""), ('TRUE',"True","") ))
    vhtIsUnhideVirtual       : BoolProperty(name="Unhide virtual sockets",           default=True)
    vhtIsToggleNodesOnDrag   : BoolProperty(name="Toggle nodes on drag",             default=True)
    # ------
    vmltIgnoreCase           : BoolProperty(name="Ignore case", default=True)
    # ------
    vestIsToggleNodesOnDrag  : BoolProperty(name="Toggle nodes on drag", default=True)
    ##
    vestBoxScale             : FloatProperty(name="Box scale",           default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vestDisplayLabels        : BoolProperty(name="Display enum names",   default=True)
    vestDarkStyle            : BoolProperty(name="Dark style",           default=False)
    vitPasteToAnySocket      : BoolProperty(name="Allow paste to any socket", default=False)
    vwtSelectTargetKey       : StringProperty(name="Select target Key", default='LEFT_ALT', description="Hold this key to select the target node instead of just jumping to it")
    vlnstNonColorName        : StringProperty(name="Non-Color name",  default="Non-Color")
    vlnstLastExecError       : StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)
    vdtDummy                 : StringProperty(name="Dummy", default="Dummy")
    # ------
    dsIsFieldDebug       : BoolProperty(name="Field debug", default=False)
    dsIsTestDrawing      : BoolProperty(name="Testing draw", default=False, update=update_test_draw)
    dsIncludeDev         : BoolProperty(name="Include Dev", default=False)
    # ------
    vaUiTabs: EnumProperty(name="Addon pref Tabs", default='SETTINGS', items=(
        ('SETTINGS', "Settings", ""), ('APPEARANCE', "Appearance", ""), ('DRAW', "Draw", ""), ('KEYMAP', "Keymap", ""), ('INFO', "Info", "")))
    vaInfoRestore        : BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    # Box disclosures:
    vaKmiMainstreamDiscl : BoolProperty(name="Most Useful", default=True)
    vaKmiOtjersDiscl     : BoolProperty(name="Quite Useful", default=False)
    vaKmiSpecialDiscl    : BoolProperty(name="Maybe Useful", default=False)
    vaKmiInvalidDiscl    : BoolProperty(name="Invalid", default=False)
    vaKmiQqmDiscl        : BoolProperty(name="Quick Math", default=False)
    vaKmiCustomDiscl     : BoolProperty(name="Custom", default=True)
    vaDecorLy            : FloatVectorProperty(name="DecorForLayout",   default=(0.01, 0.01, 0.01),   min=0, max=1, size=3, subtype='COLOR')
    vaDecorColSk         : FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=update_decor_color_socket)
    vaDecorColSkBack     : FloatVectorProperty(name="vaDecorColSkBack", default=(1.0, 1.0, 1.0, 1.0), min = 0, max=1, size=4, subtype='COLOR')
    # ------
    dsIsDrawText      : BoolProperty(name="Text",        default=True) # 考虑到 VHT 和 VEST, 这更多是用于框架中的文本, 而不是来自插槽的文本.
    dsIsDrawMarker    : BoolProperty(name="Markers",     default=True)
    dsIsDrawPoint     : BoolProperty(name="Points",      default=True)
    dsIsDrawLine      : BoolProperty(name="Line",        default=True)
    dsIsDrawSkArea    : BoolProperty(name="Socket area", default=True)
    dsIsColoredText   : BoolProperty(name="Text",        default=True)
    dsIsColoredMarker : BoolProperty(name="Markers",     default=True)
    dsIsColoredPoint  : BoolProperty(name="Points",      default=True)
    dsIsColoredLine   : BoolProperty(name="Line",        default=True)
    dsIsColoredSkArea : BoolProperty(name="Socket area", default=True)
    dsIsColoredNodes  : BoolProperty(name="Nodes",       default=True)
    ##
    dsSocketAreaAlpha : FloatProperty(name="Socket area alpha", default=0.4, min=0.0, max=1.0, subtype="FACTOR")
    ##
    dsUniformColor            : FloatVectorProperty(name="Alternative uniform color", default=(1, 0, 0, 0.9), min=0, max=1, size=4, subtype='COLOR') # 0.65, 0.65, 0.65, 1.0
    dsUniformNodeColor        : FloatVectorProperty(name="Alternative nodes color",   default=(0, 1, 0, 0.9), min=0, max=1, size=4, subtype='COLOR') # 1.0, 1.0, 1.0, 0.9
    dsCursorColor             : FloatVectorProperty(name="Cursor color",              default=(0, 0, 0, 1.0), min=0, max=1, size=4, subtype='COLOR') # 1.0, 1.0, 1.0, 1.0
    dsCursorColorAvailability : IntProperty(name="Cursor color availability", default=2, min=0, max=2,
                                               description="If a line is drawn to the cursor, color part of it in the cursor color.\n0 – Disable.\n1 – For one line.\n2 – Always")
    ##
    dsDisplayStyle : EnumProperty(name="Display frame style", default='ONLY_TEXT', items=( ('CLASSIC',"Classic","Classic"), ('SIMPLIFIED',"Simplified","Simplified"), ('ONLY_TEXT',"Only text","Only text") ))
    dsFontFile     : StringProperty(name="Font file",    default='C:\\Windows\\Fonts\\consola.ttf', subtype='FILE_PATH') # "Linux 用户表示不满".
    dsLineWidth    : FloatProperty( name="Line Width",   default=2, min=0.5, max=8.0, subtype="FACTOR")
    dsPointScale   : FloatProperty( name="Point scale",  default=1.0, min=0.0, max=3.0)
    dsFontSize     : IntProperty(   name="Font size",    default=32,  min=10,  max=48)
    dsMarkerStyle  : IntProperty(   name="Marker Style", default=0,   min=0,   max=2)
    ##
    # https://blender.stackexchange.com/questions/312413/blf-module-how-to-draw-text-in-the-center
    dsManualAdjustment : FloatProperty(name="Manual adjustment",         default=-0.2, description="The Y-axis offset of text for this font")
    dsPointOffsetX     : FloatProperty(name="Point offset X axis",       default=8.0,   min=-50.0, max=50.0)
    dsFrameOffset      : IntProperty(  name="Frame size",                default=0,      min=0,     max=24, subtype='FACTOR') # 注意: 这必须是 Int.
    dsDistFromCursor   : FloatProperty(name="Text distance from cursor", default=25.0,   min=5.0,   max=50.0)
    ##
    dsIsAlwaysLine        : BoolProperty(name="Always draw line",      default=True, description="Draw a line to the cursor even from a single selected socket")
    dsIsSlideOnNodes      : BoolProperty(name="Slide on nodes",        default=False)
    dsIsDrawNodeNameLabel : BoolProperty(name="Display text for node", default=True)
    ##
    dsIsAllowTextShadow : BoolProperty(       name="Enable text shadow", default=False)
    dsShadowCol         : FloatVectorProperty(name="Shadow color",       default=(0.0, 0.0, 0.0, 0.5), min=0,   max=1,  size=4, subtype='COLOR')
    dsShadowOffset      : IntVectorProperty(  name="Shadow offset",      default=(2,-2),               min=-20, max=20, size=2)
    dsShadowBlur        : IntProperty(        name="Shadow blur",        default=2,                    min=0,   max=2)
    # ------
    # 没在任何地方使用; 似乎也永远不会用. 我本想添加这个, 但后来觉得太懒了. 这需要把所有东西都改成"仅插槽", 而且获取节点的标准也不知道怎么弄. 而且收益也不确定, 除了美观. 所以算了吧. "能用就行, 别乱动".而且"仅插槽"的实现可能会陷入潜在的兔子洞.
    vSearchMethod          : EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") ))
    vEdgePanFac            : FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    vEdgePanSpeed          : FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    vIsOverwriteZoomLimits : BoolProperty(name="Overwriting zoom limits", default=False)
    vOwZoomMin             : FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    vOwZoomMax             : FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)
    # ------
    def draw_tab_settings(self, layout: UILayout):
        col = layout.column()
        add_thin_sep(col, 0.1)
        # 延迟导入以避免循环导入
        from . import vt_classes
        for cls in vt_classes:
            if cls.can_draw_settings:
                if body_col := draw_panel_column(col, format_tool_label(cls)):
                    cls.draw_pref_settings(body_col, self)

    def draw_tab_appearance(self, layout: UILayout):
        col_main = layout.column()

        if panel_col := draw_panel_column(col_main, "Edge pan"):
            split_prop(panel_col, self, 'vEdgePanFac', text="Zoom factor")
            split_prop(panel_col, self, 'vEdgePanSpeed', text="Speed")
            if (self.dsIncludeDev) or (self.vIsOverwriteZoomLimits):
                split_prop(panel_col, self, 'vIsOverwriteZoomLimits', active=self.vIsOverwriteZoomLimits)
                if self.vIsOverwriteZoomLimits:
                    split_prop(panel_col, self, 'vOwZoomMin')
                    split_prop(panel_col, self, 'vOwZoomMax')

        from . import vt_classes
        for cls in vt_classes:
            if cls.can_draw_appearance:
                cls.draw_pref_appearance(col_main, self)

    def draw_tab_draw(self, layout: UILayout):
        col_main = layout.column()

        split_draw_color = col_main.box().split(align=True)
        split_draw_color.use_property_split = True

        is_draw_settings = [
            'dsIsDrawText',
            'dsIsDrawMarker',
            'dsIsDrawPoint',
            'dsIsDrawLine',
            'dsIsDrawSkArea',
        ]
        is_draw_col = split_draw_color.column(align=True, heading='Draw')
        for is_draw in is_draw_settings:
            is_draw_col.prop(self, is_draw)
        with ColumnSetActive(is_draw_col, active=self.dsIsDrawText) as row:
            row.prop(self, 'dsIsDrawNodeNameLabel', text="Node label")
        is_colored_col = split_draw_color.column(align=True, heading='Colored')
        for is_draw in is_draw_settings:
            row = is_colored_col.row(align=True)
            row.prop(self, is_draw.replace("Draw", "Colored"))
            row.active = getattr(self, is_draw)

        is_nodes_toggle_active = self.dsIsDrawLine or self.dsIsDrawPoint or (self.dsIsDrawText and self.dsIsDrawNodeNameLabel)
        with ColumnSetActive(is_colored_col, active=is_nodes_toggle_active) as row:
            row.prop(self, 'dsIsColoredNodes')
        ##
        if panel_col := draw_panel_column(col_main, "Behavior"):
            #split_prop(panel_col, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
            split_prop(panel_col, self, 'dsIsAlwaysLine')
            split_prop(panel_col, self, 'dsIsSlideOnNodes')
        ##
        if panel_col := draw_panel_column(col_main, "Color"):
            split_prop(panel_col, self, 'dsSocketAreaAlpha', active=self.dsIsDrawSkArea)
            show_uniform_color = ((self.dsIsDrawText and not self.dsIsColoredText) or (self.dsIsDrawMarker and not self.dsIsColoredMarker)
                                  or (self.dsIsDrawPoint and not self.dsIsColoredPoint) or (self.dsIsDrawLine and not self.dsIsColoredLine)
                                  or (self.dsIsDrawSkArea and not self.dsIsColoredSkArea))
            if show_uniform_color:
                split_prop(panel_col, self, 'dsUniformColor')
            show_uniform_node_color = ((self.dsIsDrawText and self.dsIsColoredText) or (self.dsIsDrawPoint and self.dsIsColoredPoint)
                                       or (self.dsIsDrawLine and self.dsIsColoredLine))
            if show_uniform_node_color and not self.dsIsColoredNodes:
                split_prop(panel_col, self, 'dsUniformNodeColor')
            is_point_cursor_color_active = self.dsIsDrawPoint and self.dsIsColoredPoint
            is_line_cursor_color_active = self.dsIsDrawLine and self.dsIsColoredLine and self.dsCursorColorAvailability
            split_prop(panel_col, self, 'dsCursorColor', active=is_point_cursor_color_active or is_line_cursor_color_active)
            split_prop(panel_col, self, 'dsCursorColorAvailability', active=self.dsIsDrawLine and self.dsIsColoredLine)
        ##
        if panel_col := draw_panel_column(col_main, "Style"):
            split_prop(panel_col, self, 'dsDisplayStyle')
            split_prop(panel_col, self, 'dsFontFile')
            if not self.dsFontFile.endswith((".ttf", ".otf")):
                split_row = panel_col.split(factor=0.4, align=True)
                split_row.label(text="")
                split_row.label(text="Only .ttf or .otf format", icon='ERROR')
            add_thin_sep(panel_col, 0.5)
            split_prop(panel_col, self, 'dsLineWidth')
            split_prop(panel_col, self, 'dsPointScale')
            split_prop(panel_col, self, 'dsFontSize')
            split_prop(panel_col, self, 'dsMarkerStyle')
        ##
        if panel_col := draw_panel_column(col_main, "Offset"):
            split_prop(panel_col, self, 'dsManualAdjustment')
            split_prop(panel_col, self, 'dsPointOffsetX')
            split_prop(panel_col, self, 'dsFrameOffset')
            split_prop(panel_col, self, 'dsDistFromCursor')
            add_thin_sep(panel_col, 0.25)  # 间隔的空白会累加, 所以额外加个间隔来对齐.
            split_prop(panel_col, self, 'dsIsAllowTextShadow')
            if self.dsIsAllowTextShadow:
                col_shadow = panel_col.column(align=True)
                split_prop(col_shadow, self, 'dsShadowCol')
                split_prop(col_shadow, self, 'dsShadowBlur')  # 阴影模糊将它们分开, 以免在中间融合在一起.
                row = split_prop(col_shadow, self, 'dsShadowOffset', returnAsLy=True).row(align=True)
                row.row().prop(self, 'dsShadowOffset', text="X  ", translate=False, index=0, icon_only=True)
                row.row().prop(self, 'dsShadowOffset', text="Y  ", translate=False, index=1, icon_only=True)
        ##
        col_dev = col_main.column(align=True)
        if self.dsIncludeDev or self.dsIsFieldDebug or self.dsIsTestDrawing:
            with ColumnSetActive(col_dev, active=self.dsIsFieldDebug) as row:
                row.prop(self, 'dsIsFieldDebug')
            with ColumnSetActive(col_dev, active=self.dsIsTestDrawing) as row:
                row.prop(self, 'dsIsTestDrawing')

    def draw_tab_keymaps(self, layout: UILayout):
        col_main = layout.column()
        col_main.separator()
        row_label_main = col_main.row(align=True)
        row_label = row_label_main.row(align=True)
        row_label.alignment = 'CENTER'
        row_label.label(icon='DOT')
        col_list = col_main.column(align=True)
        node_kms = user_node_keymap()
        ##
        voronoi_kmis = [li for li in node_kms.keymap_items if li.idname.startswith("node.voronoi_")]
        shortcut_count = len(voronoi_kmis)
        active_shortcut_count = sum(int(kmi.active) for kmi in voronoi_kmis)
        kmi_groups = populate_keymap_item_groups(node_kms)
        row_label.label(text=f"{_iface('Node Editor')}  ({active_shortcut_count}/{shortcut_count})")

        if node_kms.is_user_modified:
            row_restore = row_label_main.row(align=True)
            row_restore.context_pointer_set('keymap', node_kms)

        row_label_main.label()
        row_add_new = row_label_main.row(align=True)
        row_add_new.separator()
        row_add_new.ui_units_x = 10
        row_add_new.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='ADD').opt = 'add_new_kmi'

        def draw_km_group(layout: UILayout, category: KeymapItemGroup):
            if not category.matched_items:
                return
            group_name = self.bl_rna.properties[category.prop_name].name
            panel, body = layout.panel(idname=category.prop_name, default_closed=True)
            row = panel.row(align=True)
            active_count = sum(kmi.active for kmi in category.matched_items)
            icon= 'CHECKBOX_HLT' if active_count else 'CHECKBOX_DEHLT'
            row.operator(VoronoiOpAddonTabs.bl_idname, text="", icon=icon, emboss=False).opt = f"toggle_kmi_group:{category.group_key}"
            row.label(text=f"{_iface(group_name)}  ({active_count}/{category.count})")
            if body:
                split_body = body.split(factor=0.02, align=False)
                split_body.label(text="")
                body_col = split_body.column(align=True)
                for li in sorted(category.matched_items, key=lambda a: a.id):
                    body_col.context_pointer_set('keymap', node_kms)
                    rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, node_kms, li, body_col, 0)

        draw_km_group(col_list, kmi_groups.custom)
        draw_km_group(col_list, kmi_groups.most_useful)
        draw_km_group(col_list, kmi_groups.quite_useful)
        draw_km_group(col_list, kmi_groups.maybe_useful)
        draw_km_group(col_list, kmi_groups.invalid)
        draw_km_group(col_list, kmi_groups.quick_math)

    def draw_tab_info(self, layout: UILayout):

        def link_button(layout: UILayout, text, url, highlight_text=""):
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            if highlight_text:
                highlight_text = "#:~:text=" + highlight_text
            row.operator('wm.url_open', text=text, icon='URL').url = url + highlight_text
            row.label()

        link_button(layout, "Check for updates yourself", "https://github.com/yunkezengren/Blender-addons-Node-Utilities/releases")
        layout.prop(self, 'dsIncludeDev')

        panel, body = layout.panel(idname="工具描述", default_closed=True)
        panel.label(text="Description")
        if body:
            body = body.split(factor=0.01)
            body.label(text="")
            body = body.box()
            body.scale_y = 0.7
            from . import vt_classes
            for cls in vt_classes:
                if hasattr(cls, 'bl_description') and cls.bl_description:
                    tool_info = _iface(cls.bl_description)
                    col_disclosure = body.column()
                    _panel, _body = col_disclosure.panel(idname=cls.bl_label)
                    _panel.label(text=cls.bl_label)
                    if not _body: continue
                    tool_rows = _body.column()
                    for li in tool_info.split("\n"):
                        text_row = tool_rows.row(align=True)
                        text_row.label(icon='BLANK1')
                        text_row.label(text=li, translate=False)

        panel, body = layout.panel(idname="old", default_closed=True)
        panel.label(text="Settings from original author (I don't understand some of them)")
        if body:
            body = body.split(factor=0.05)
            body.label()
            layout = body
            col_main = layout.column()
            col_urls = col_main.column()
            link_button(col_urls, "VL Wiki", "https://github.com/neliut/VoronoiLinker/wiki")
            link_button(col_urls, "RANTO Git", "https://github.com/ugorek000/RANTO")
            col_urls.separator()
            link_button(col_urls, "Event Type Items", "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html")
            link_button(col_urls, "Translator guide", "https://developer.blender.org/docs/handbook/translating/translator_guide/")
            link_button(col_urls, "Translator dev guide", "https://developer.blender.org/docs/handbook/translating/developer_guide/")

            # todo 弃用,以后删
            col_main.separator()
            row = col_main.row(align=True)
            row.alignment = 'LEFT'
            row.operator(VoronoiOpAddonTabs.bl_idname, text="Copy addon settings as .py script", icon='COPYDOWN').opt = 'copy_settings'

    def draw(self, context):

        def draw_layout_decor_column(layout: UILayout, scale_y=0.05, scale_x=1.0, enabled=False):
            layout.prop(self, 'vaDecorLy', text="")
            layout.scale_x = scale_x
            layout.scale_y = scale_y  # 如果小于 0.05, 布局会消失, 圆角也会消失.
            layout.enabled = enabled

        col_layout = self.layout.column()
        col_main = col_layout.column(align=True)
        col_tabs = col_main.column(align=True)
        row_tabs = col_tabs.row(align=True)
        # 标签页切换是通过操作符创建的, 以免在按住鼠标拖动时意外切换标签页, 这在有大量"isColored"选项时很有诱惑力. 而且现在它们被装饰得更像"标签页"了, 这是普通的 prop 布局 с 'expand=True' 无法做到的.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = row_tabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=_iface(li.name), depress=self.vaUiTabs == li.identifier).opt = li.identifier
            draw_layout_decor_column(col.row(align=True))

        match self.vaUiTabs:
            case 'SETTINGS':
                self.draw_tab_settings(col_main)
            case 'APPEARANCE':
                self.draw_tab_appearance(col_main)
            case 'DRAW':
                self.draw_tab_draw(col_main)
            case 'KEYMAP':
                self.draw_tab_keymaps(col_main)
            case 'INFO':
                self.draw_tab_info(col_main)

# 需要在 VoronoiAddonPrefs 类定义之后执行的动态属性添加函数
def add_dynamic_properties(vt_classes):
    """为每个工具类动态添加 BoxDiscl 属性到 VoronoiAddonPrefs"""
    for cls in vt_classes:
        setattr(VoronoiAddonPrefs, cls.disclBoxPropName, BoolProperty(name="", default=False))
        setattr(VoronoiAddonPrefs, cls.disclBoxPropNameInfo, BoolProperty(name="", default=False))

def pref() -> VoronoiAddonPrefs:
    return bpy.context.preferences.addons[__package__].preferences # type: ignore
