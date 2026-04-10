import bpy
import bl_keymap_utils
import rna_keymap_ui
from typing import Callable
from bpy.app.translations import pgettext_iface as _iface
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, StringProperty
from bpy.types import KeyMapItem, UILayout

from .common_class import VlnstUpdateLastExecError
from .common_func import GetFirstUpperLetters, format_tool_set, user_node_keymap
from .globals import dict_vlHhTranslations, dict_vmtMixerNodesDefs, dict_vqmtQuickMathMain
from .utils.ui import draw_hand_split_prop, draw_panel_column, LyAddQuickInactiveCol, LyAddThinSep
from .utils.drawing import TestDraw

old_info = {
    'description': "Various utilities for nodes connecting, based on distance field.",
    'wiki_url': "https://github.com/neliut/VoronoiLinker/wiki",
    'tracker_url': "https://github.com/neliut/VoronoiLinker/issues"
}

list_langDebEnumItems = []
fitVltPiDescr = "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"
hide_bool_socket_items = [
    ('ALWAYS', "Always", "Always"),
    ('IF_FALSE', "If false", "If false"),
    ('NEVER', "Never", "Never"),
    ('IF_TRUE', "If true", "If true"),
]

txt_onlyFontFormat = "Only .ttf or .otf format"
txt_copySettAsPyScript = "Copy addon settings as .py script"
txt_checkForUpdatesYourself = "Check for updates yourself"
txt_vmtNoMixingOptions = "No mixing options"
txt_vqmtThereIsNothing = "There is nothing"

txt_FloatQuickMath = "Float Quick Math"
txt_VectorQuickMath = "Vector Quick Math"
txt_IntQuickMath = "Integer Quick Math"
txt_BooleanQuickMath = "Boolean Quick Math"
txt_MatrixQuickMath = "Matrix Quick Math"
txt_ColorQuickMode = "Color Quick Mode"

def VaUpdateTestDraw(self, context):
    TestDraw.Toggle(context, self.dsIsTestDrawing)

vaUpdateSelfTgl = False

def VaUpdateDecorColSk(self, _context):
    global vaUpdateSelfTgl
    if vaUpdateSelfTgl:
        return
    vaUpdateSelfTgl = True
    self.vaDecorColSk = self.vaDecorColSkBack
    vaUpdateSelfTgl = False

class KeymapItemCategory:
    """快捷键项分类 - 用于组织和过滤keymap items"""
    prop_name: str
    matched_items: set
    idnames: set
    count: int
    filter_func: Callable[[KeyMapItem], bool] | None

    def __init__(self, prop_name='', matched_items=set(), idnames=set()):
        self.prop_name = prop_name
        self.matched_items = matched_items
        self.idnames = idnames
        self.count = 0
        self.filter_func = None

class KeymapItemCategoryContainer:
    """快捷键项分类容器 - 管理多个KeymapItemCategory实例"""
    useful_1: KeymapItemCategory
    useful_2: KeymapItemCategory
    useful_3: KeymapItemCategory
    useful_4: KeymapItemCategory
    qqm: KeymapItemCategory
    custom: KeymapItemCategory

class VoronoiOpAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    bl_description = "VL's addon tab"  # todo1v6: 想办法为每个标签页翻译不同的内容.
    opt: StringProperty()

    def invoke(self, context, event):
        #if not self.opt: return {'CANCELLED'}
        prefs = pref()
        match self.opt:
            case 'GetPySett':
                context.window_manager.clipboard = GetVaSettAsPy(prefs)
            case 'AddNewKmi':
                user_node_keymap().keymap_items.new("node.voronoi_", 'D', 'PRESS').show_expanded = True
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__ # type: ignore
    # --- VoronoiLinkerTool
    vltRepickKey            : StringProperty(name="Repick Key", default='LEFT_ALT', description="Hold this key to re-pick target socket without releasing the mouse")
    vltReroutesCanInAnyType : BoolProperty(name="Reroutes can be connected to any type", default=True)
    vltDeselectAllNodes     : BoolProperty(name="Deselect all nodes on activate",        default=False)
    vltPriorityIgnoring     : BoolProperty(name="Priority ignoring",                     default=False, description=fitVltPiDescr)
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
    vhtHideBoolSocket        : EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=hide_bool_socket_items)
    vhtHideHiddenBoolSocket  : EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=hide_bool_socket_items)
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
    vaLangDebDiscl       : BoolProperty(name="Language bruteforce debug", default=False)
    vaLangDebEnum        : EnumProperty(name="LangDebEnum", default='FREE', items=list_langDebEnumItems)
    dsIsFieldDebug       : BoolProperty(name="Field debug", default=False)
    dsIsTestDrawing      : BoolProperty(name="Testing draw", default=False, update=VaUpdateTestDraw)
    dsIncludeDev         : BoolProperty(name="IncludeDev", default=False)
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
    vaDecorColSk         : FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=VaUpdateDecorColSk)
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
    # 我本想添加这个, 但后来觉得太懒了. 这需要把所有东西都改成"仅插槽", 而且获取节点的标准也不知道怎么弄.
    # 而且收益也不确定, 除了美观. 所以算了吧. "能用就行, 别乱动".而且"仅插槽"的实现可能会陷入潜在的兔子洞.
    vSearchMethod          : EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") )) # 没在任何地方使用; 似乎也永远不会用.
    vEdgePanFac            : FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    vEdgePanSpeed          : FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    vIsOverwriteZoomLimits : BoolProperty(name="Overwriting zoom limits", default=False)
    vOwZoomMin             : FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    vOwZoomMax             : FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)
    # ------
    def LyDrawTabSettings(self, where: UILayout):
        colMain = where.column()
        LyAddThinSep(colMain, 0.1)
        # 延迟导入以避免循环导入
        from . import vt_classes
        for cls in vt_classes:
            if cls.can_draw_in_pref_setting:
                if colDiscl := draw_panel_column(colMain, format_tool_set(cls)):
                    cls.draw_in_pref_settings(colDiscl, self)

    def LyDrawTabAppearance(self, where: UILayout):
        colMain = where.column()
        #draw_hand_split_prop(draw_panel_column(colMain, text="Main"), self,'vSearchMethod')
        ##
        if p_col := draw_panel_column(colMain, "Edge pan"):
            draw_hand_split_prop(p_col, self, 'vEdgePanFac', text="Zoom factor")
            draw_hand_split_prop(p_col, self, 'vEdgePanSpeed', text="Speed")
            if (self.dsIncludeDev) or (self.vIsOverwriteZoomLimits):
                draw_hand_split_prop(p_col, self, 'vIsOverwriteZoomLimits', active=self.vIsOverwriteZoomLimits)
                if self.vIsOverwriteZoomLimits:
                    draw_hand_split_prop(p_col, self, 'vOwZoomMin')
                    draw_hand_split_prop(p_col, self, 'vOwZoomMax')
        ##
        from . import vt_classes
        for cls in vt_classes:
            if cls.can_draw_in_appearence:
                cls.LyDrawInAppearance(colMain, self)

    def LyDrawTabDraw(self, where: UILayout):

        def LyAddPairProp(where: UILayout, txt):
            row = where.row(align=True)
            row.prop(self, txt)
            row.active = getattr(self, txt.replace("Colored", "Draw"))

        colMain = where.column()
        splDrawColor = colMain.box().split(align=True)
        splDrawColor.use_property_split = True
        colDraw = splDrawColor.column(align=True, heading='Draw')
        colDraw.prop(self, 'dsIsDrawText')
        colDraw.prop(self, 'dsIsDrawMarker')
        colDraw.prop(self, 'dsIsDrawPoint')
        colDraw.prop(self, 'dsIsDrawLine')
        colDraw.prop(self, 'dsIsDrawSkArea')
        with LyAddQuickInactiveCol(colDraw, active=self.dsIsDrawText) as row:
            row.prop(self, 'dsIsDrawNodeNameLabel', text="Node label")  # "Text for node"
        colCol = splDrawColor.column(align=True, heading='Colored')
        LyAddPairProp(colCol, 'dsIsColoredText')
        LyAddPairProp(colCol, 'dsIsColoredMarker')
        LyAddPairProp(colCol, 'dsIsColoredPoint')
        LyAddPairProp(colCol, 'dsIsColoredLine')
        LyAddPairProp(colCol, 'dsIsColoredSkArea')
        tgl = (self.dsIsDrawLine) or (self.dsIsDrawPoint) or (self.dsIsDrawText and self.dsIsDrawNodeNameLabel)
        with LyAddQuickInactiveCol(colCol, active=tgl) as row:
            row.prop(self, 'dsIsColoredNodes')
        ##
        if p_col := draw_panel_column(colMain, "Behavior"):
            #draw_hand_split_prop(p_col, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
            draw_hand_split_prop(p_col, self, 'dsIsAlwaysLine')
            draw_hand_split_prop(p_col, self, 'dsIsSlideOnNodes')
        ##
        if p_col := draw_panel_column(colMain, "Color"):
            draw_hand_split_prop(p_col, self, 'dsSocketAreaAlpha', active=self.dsIsDrawSkArea)
            tgl = ((self.dsIsDrawText and not self.dsIsColoredText) or (self.dsIsDrawMarker and not self.dsIsColoredMarker)
                   or (self.dsIsDrawPoint and not self.dsIsColoredPoint) or (self.dsIsDrawLine and not self.dsIsColoredLine)
                   or (self.dsIsDrawSkArea and not self.dsIsColoredSkArea))
            if tgl:
                draw_hand_split_prop(p_col, self, 'dsUniformColor')
            tgl = ((self.dsIsDrawText and self.dsIsColoredText) or (self.dsIsDrawPoint and self.dsIsColoredPoint)
                   or (self.dsIsDrawLine and self.dsIsColoredLine))
            if tgl and (not self.dsIsColoredNodes):
                draw_hand_split_prop(p_col, self, 'dsUniformNodeColor')
            # draw_hand_split_prop(p_col, self,'dsUniformNodeColor', active=True)
            tgl1 = (self.dsIsDrawPoint and self.dsIsColoredPoint)
            tgl2 = (self.dsIsDrawLine and self.dsIsColoredLine) and (not not self.dsCursorColorAvailability)
            draw_hand_split_prop(p_col, self, 'dsCursorColor', active=tgl1 or tgl2)
            draw_hand_split_prop(p_col, self, 'dsCursorColorAvailability', active=self.dsIsDrawLine and self.dsIsColoredLine)
        ##
        if p_col := draw_panel_column(colMain, "Style"):
            draw_hand_split_prop(p_col, self, 'dsDisplayStyle')
            draw_hand_split_prop(p_col, self, 'dsFontFile')
            if not self.dsFontFile.endswith((".ttf", ".otf")):
                spl = p_col.split(factor=0.4, align=True)
                spl.label(text="")
                spl.label(text=txt_onlyFontFormat, icon='ERROR')
            LyAddThinSep(p_col, 0.5)
            draw_hand_split_prop(p_col, self, 'dsLineWidth')
            draw_hand_split_prop(p_col, self, 'dsPointScale')
            draw_hand_split_prop(p_col, self, 'dsFontSize')
            draw_hand_split_prop(p_col, self, 'dsMarkerStyle')
        ##
        if p_col := draw_panel_column(colMain, "Offset"):
            draw_hand_split_prop(p_col, self, 'dsManualAdjustment')
            draw_hand_split_prop(p_col, self, 'dsPointOffsetX')
            draw_hand_split_prop(p_col, self, 'dsFrameOffset')
            draw_hand_split_prop(p_col, self, 'dsDistFromCursor')
            LyAddThinSep(p_col, 0.25)  # 间隔的空白会累加, 所以额外加个间隔来对齐.
            draw_hand_split_prop(p_col, self, 'dsIsAllowTextShadow')
            if self.dsIsAllowTextShadow:
                colShadow = p_col.column(align=True)
                draw_hand_split_prop(colShadow, self, 'dsShadowCol')
                draw_hand_split_prop(colShadow, self, 'dsShadowBlur')  # 阴影模糊将它们分开, 以免在中间融合在一起.
                row = draw_hand_split_prop(colShadow, self, 'dsShadowOffset', returnAsLy=True).row(align=True)
                row.row().prop(self, 'dsShadowOffset', text="X  ", translate=False, index=0, icon_only=True)
                row.row().prop(self, 'dsShadowOffset', text="Y  ", translate=False, index=1, icon_only=True)
        ##
        colDev = colMain.column(align=True)
        if (self.dsIncludeDev) or (self.dsIsFieldDebug) or (self.dsIsTestDrawing):
            with LyAddQuickInactiveCol(colDev, active=self.dsIsFieldDebug) as row:
                row.prop(self, 'dsIsFieldDebug')
            with LyAddQuickInactiveCol(colDev, active=self.dsIsTestDrawing) as row:
                row.prop(self, 'dsIsTestDrawing')

    def LyDrawTabKeymaps(self, where: UILayout):
        colMain = where.column()
        colMain.separator()
        rowLabelMain = colMain.row(align=True)
        rowLabel = rowLabelMain.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(icon='DOT')
        rowLabel.label(text="Node Editor")
        rowLabelPost = rowLabelMain.row(align=True)
        colList = colMain.column(align=True)
        node_kms = user_node_keymap()
        ##
        from . import keymap_categorys
        kmiCats = KeymapItemCategoryContainer()
        kmiCats.qqm = KeymapItemCategory('vaKmiQqmDiscl', set(), keymap_categorys["qqm"])
        kmiCats.custom = KeymapItemCategory('vaKmiCustomDiscl', set())
        kmiCats.useful_1 = KeymapItemCategory('vaKmiMainstreamDiscl', set(), keymap_categorys["最有用"])
        kmiCats.useful_2 = KeymapItemCategory('vaKmiOtjersDiscl', set(), keymap_categorys["很有用"])
        kmiCats.useful_3 = KeymapItemCategory('vaKmiSpecialDiscl', set(), keymap_categorys["可能有用"])
        kmiCats.useful_4 = KeymapItemCategory('vaKmiInvalidDiscl', set(), keymap_categorys["无效"])
        kmiCats.useful_1.filter_func = lambda kmi: kmi.idname in kmiCats.useful_1.idnames
        kmiCats.useful_2.filter_func = lambda kmi: kmi.idname in kmiCats.useful_2.idnames
        kmiCats.useful_3.filter_func = lambda kmi: kmi.idname in kmiCats.useful_3.idnames
        kmiCats.useful_4.filter_func = lambda kmi: True
        kmiCats.qqm.filter_func = lambda kmi: any(
            True for txt in {'quickOprFloat', 'quickOprVector', 'quickOprBool', 'quickOprColor', 'justPieCall', 'isRepeatLastOperation'}
            if getattr(kmi.properties, txt, None))
        kmiCats.custom.filter_func = lambda kmi: kmi.id < 0  # 负id用于自定义
        # 在旧版插件中, 使用另一种搜索方法, "keymap" 标签页中的顺序与注册具有相同 `cls` 的 kmidef 的调用顺序相反.
        # 现在改成了这样. 之前的方法是如何工作的 -- 我完全不知道.
        scoAll = 0
        for li in node_kms.keymap_items:
            if li.idname.startswith("node.voronoi_"):
                for dv in kmiCats.__dict__.values():
                    if dv.filter_func(li):
                        dv.matched_items.add(li)
                        dv.count += 1
                        break
                scoAll += 1  # 热键现在变得非常非常多, 知道它们的数量会很不错.
        if node_kms.is_user_modified:
            rowRestore = rowLabelMain.row(align=True)
            # with LyAddQuickInactiveCol(rowRestore, align=False, active=True) as row:
            #     row.prop(self, 'vaInfoRestore', text="", icon='INFO')
            rowRestore.context_pointer_set('keymap', node_kms)
            # rowRestore.operator('preferences.keymap_restore', text="Restore", icon="ERROR")
        else:
            rowLabelMain.label()
        rowAddNew = rowLabelMain.row(align=True)
        rowAddNew.ui_units_x = 12
        rowAddNew.separator()
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='ADD').opt = 'AddNewKmi'  # NONE  ADD

        def LyAddKmisCategory(where: UILayout, cat):
            if not cat.matched_items:
                return
            txt = self.bl_rna.properties[cat.prop_name].name
            panel, body = where.panel(idname=cat.prop_name, default_closed=True)
            panel.label(text=_iface(txt) + f" ({cat.count})")
            if body:
                for li in sorted(cat.matched_items, key=lambda a: a.id):
                    body.context_pointer_set('keymap', node_kms)
                    rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, node_kms, li, body, 0)

        LyAddKmisCategory(colList, kmiCats.custom)
        LyAddKmisCategory(colList, kmiCats.useful_1)
        LyAddKmisCategory(colList, kmiCats.useful_2)
        LyAddKmisCategory(colList, kmiCats.useful_3)
        LyAddKmisCategory(colList, kmiCats.useful_4)
        LyAddKmisCategory(colList, kmiCats.qqm)
        rowLabelPost.label(text=f"({scoAll})", translate=False)

    def LyDrawTabInfo(self, where: UILayout):

        def LyAddUrlHl(where: UILayout, text, url, txtHl=""):
            row = where.row(align=True)
            row.alignment = 'LEFT'
            if txtHl:
                txtHl = "#:~:text=" + txtHl
            row.operator('wm.url_open', text=text, icon='URL').url = url + txtHl
            row.label()

        LyAddUrlHl(where, "Check for updates yourself", "https://github.com/yunkezengren/Blender-addons-Node-Utilities/releases")

        panel, body = where.panel(idname="工具描述", default_closed=True)
        panel.label(text="Description")
        if body:
            body = body.split(factor=0.01)
            body.label(text="")
            body = body.box()
            body.scale_y = 0.7
            from . import vt_classes
            for cls in vt_classes:
                if hasattr(cls, 'bl_description') and cls.bl_description:
                    txtToolInfo = _iface(cls.bl_description)
                    colDiscl = body.column()
                    _panel, _body = colDiscl.panel(idname=cls.bl_label)
                    _panel.label(text=cls.bl_label)
                    if not _body: continue
                    rowTool = _body.column()
                    for li in txtToolInfo.split("\n"):
                        text_row = rowTool.row(align=True)
                        text_row.label(icon='BLANK1')
                        text_row.label(text=li, translate=False)

        panel, body = where.panel(idname="old", default_closed=True)
        panel.label(text="Settings from original author (I don't understand some of them)")
        if body:
            body = body.split(factor=0.05)
            body.label()
            where = body
            colMain = where.column()
            colUrls = colMain.column()
            LyAddUrlHl(colUrls, "Check for updates yourself", "https://github.com/ugorek000/VoronoiLinker", txtHl="Latest%20version")
            LyAddUrlHl(colUrls, "VL Wiki", old_info['wiki_url'])
            LyAddUrlHl(colUrls, "RANTO Git", "https://github.com/ugorek000/RANTO")
            colUrls.separator()
            LyAddUrlHl(colUrls, "Event Type Items", "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html")
            LyAddUrlHl(colUrls, "Translator guide", "https://developer.blender.org/docs/handbook/translating/translator_guide/")
            LyAddUrlHl(colUrls, "Translator dev guide", "https://developer.blender.org/docs/handbook/translating/developer_guide/")
            ##
            colMain.separator()
            row = colMain.row(align=True)
            row.alignment = 'LEFT'
            row.operator(VoronoiOpAddonTabs.bl_idname, text=txt_copySettAsPyScript, icon='COPYDOWN').opt = 'GetPySett'  # SCRIPT  COPYDOWN
            with LyAddQuickInactiveCol(colMain, active=self.dsIncludeDev) as row:
                row.prop(self, 'dsIncludeDev')
            ##
            LyAddThinSep(colMain, 0.15)
            rowSettings = colMain.box().row(align=True)
            row = rowSettings.row(align=True)
            row.ui_units_x = 20
            view = bpy.context.preferences.view
            row.prop(view, 'language', text="")
            row = rowSettings.row(align=True)
            langCode = bpy.app.translations.locale
            row.label(text=f"   '{langCode}'   ", translate=False)
            row.prop(view, 'use_translate_interface', text="Interface")
            row.prop(view, 'use_translate_tooltips', text="Tooltips")
            ##
            colLangDebug = colMain.column(align=True)
            if (self.dsIncludeDev) or (self.vaLangDebDiscl):
                with LyAddQuickInactiveCol(colLangDebug, active=self.vaLangDebDiscl) as row:
                    row.prop(self, 'vaLangDebDiscl')
            if self.vaLangDebDiscl:
                row = colLangDebug.row(align=True)
                row.alignment = 'LEFT'
                row.label(text=f"[{langCode}]", translate=False)
                row.label(text="–", translate=False)
                if langCode in dict_vlHhTranslations:
                    dict_copy = dict_vlHhTranslations[langCode].copy()
                    del dict_copy['trans']
                    row.label(text=repr(dict_copy), translate=False)
                else:
                    with LyAddQuickInactiveCol(row) as row:
                        row.label(text="{}", translate=False)
                colLangDebug.row().prop(self, 'vaLangDebEnum', expand=True)

                def LyAddAlertNested(where: UILayout, text):
                    with LyAddQuickInactiveCol(where) as row:
                        row.label(text=text, translate=False)
                    row = where.row(align=True)
                    row.label(icon='BLANK1')
                    return row.column(align=True)

                def LyAddTran(where: UILayout, label, text, *, dot="."):
                    rowRoot = where.row(align=True)
                    with LyAddQuickInactiveCol(rowRoot) as row:
                        row.alignment = 'LEFT'
                        row.label(text=label + ": ", translate=False)
                    row = rowRoot.row(align=True)
                    col = row.column(align=True)
                    text = _iface(text)
                    if text:
                        list_split = text.split("\n")
                        hig = len(list_split) - 1
                        for cyc, li in enumerate(list_split):
                            col.label(text=li + (dot if cyc == hig else ""), translate=False)

                def LyAddTranDataForProp(where: UILayout, pr, dot="."):
                    colRoot = where.column(align=True)
                    with LyAddQuickInactiveCol(colRoot) as row:
                        row.label(text=pr.identifier, translate=False)
                    row = colRoot.row(align=True)
                    row.label(icon='BLANK1')
                    col2 = row.column(align=True)
                    LyAddTran(col2, "Name", pr.name, dot="")
                    if pr.description:
                        LyAddTran(col2, "Description", pr.description, dot=dot)
                    if type(pr) == bpy.types.EnumProperty:
                        for en in pr.enum_items:
                            LyAddTranDataForProp(col2, en, dot="")
                match self.vaLangDebEnum:
                    case 'FREE':
                        txt = _iface("Free")
                        col = LyAddAlertNested(colLangDebug, f"{txt}")
                        col.label(text="Virtual")
                        col.label(text="Colored")
                        col.label(text="Restore")
                        col.label(text="Add New")
                        col.label(text="Edge pan")
                        with LyAddQuickInactiveCol(col, att='column') as col0:
                            col0.label(text="Zoom factor")
                            col0.label(text="Speed")
                        col.label(text="Pie")
                        col.label(text="Box ")
                        col.label(text="Special")
                        col.label(text="Colors")
                        col.label(text="Customization")
                        col.label(text="Advanced")
                        col.label(text=txt_FloatQuickMath)
                        col.label(text=txt_VectorQuickMath)
                        col.label(text=txt_BooleanQuickMath)
                        col.label(text=txt_ColorQuickMode)
                        col.label(text=txt_vmtNoMixingOptions)
                        col.label(text=txt_vqmtThereIsNothing)
                        col.label(text=old_info['description'])
                        col.label(text=txt_onlyFontFormat)
                        col.label(text=txt_copySettAsPyScript)
                        col.label(text=txt_checkForUpdatesYourself)
                    case 'SPECIAL':
                        txt = _iface("Special")
                        col0 = LyAddAlertNested(colLangDebug, f"[{txt}]")
                        col1 = LyAddAlertNested(col0, "VMT")
                        for dv in dict_vmtMixerNodesDefs.values():
                            col1.label(text=dv[2])
                        col1 = LyAddAlertNested(col0, "VQMT")
                        for di in dict_vqmtQuickMathMain.items():
                            col2 = LyAddAlertNested(col1, di[0])
                            for ti in di[1]:
                                if ti[0]:
                                    col2.label(text=ti[0])
                    case 'ADDONPREFS':
                        from . import vt_classes
                        col = LyAddAlertNested(colLangDebug, "[AddonPrefs]")
                        set_toolBoxDisctPropNames = set([cls.disclBoxPropName for cls in vt_classes]) | set(
                            [cls.disclBoxPropNameInfo for cls in vt_classes])
                        set_toolBoxDisctPropNames.update({'vaLangDebEnum'})
                        for pr in self.bl_rna.properties[2:]:
                            if pr.identifier not in set_toolBoxDisctPropNames:
                                LyAddTranDataForProp(col, pr)
                    case _:
                        from . import vt_classes
                        dict_toolBlabToCls = {cls.bl_label.upper(): cls for cls in vt_classes}
                        set_alreadyDone = set()  # 考虑到 vaLangDebEnum 的分离, 这已经没用了.
                        col0 = colLangDebug.column(align=True)
                        cls = dict_toolBlabToCls[self.vaLangDebEnum]
                        col1 = LyAddAlertNested(col0, cls.bl_label)
                        rna = eval(f"bpy.ops.{cls.bl_idname}.get_rna_type()"
                                   )  # 通过 getattr 不知道为什么 `getattr(bpy.ops, cls.bl_idname).get_rna_type()` 不起作用.
                        for pr in rna.properties[1:]:  # 跳过 rna_type.
                            rowLabel = col1.row(align=True)
                            if pr.identifier not in set_alreadyDone:
                                LyAddTranDataForProp(rowLabel, pr)
                                set_alreadyDone.add(pr.identifier)

    def draw(self, context):

        def LyAddDecorLyColRaw(where: UILayout, sy=0.05, sx=1.0, en=False):
            where.prop(self, 'vaDecorLy', text="")
            where.scale_x = sx
            where.scale_y = sy  # 如果小于 0.05, 布局会消失, 圆角也会消失.
            where.enabled = en

        colLy = self.layout.column()
        colMain = colLy.column(align=True)
        colTabs = colMain.column(align=True)
        rowTabs = colTabs.row(align=True)
        # 标签页切换是通过操作符创建的, 以免在按住鼠标拖动时意外切换标签页, 这在有大量"isColored"选项时很有诱惑力.
        # 而且现在它们被装饰得更像"标签页"了, 这是普通的 prop 布局 с 'expand=True' 无法做到的.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=_iface(li.name), depress=self.vaUiTabs == li.identifier).opt = li.identifier
            # 现在更像标签页了
            LyAddDecorLyColRaw(col.row(align=True))  # row.operator(VoronoiOpAddonTabs.bl_idname, text="", emboss=False) # 通过操作符也行.
            #col.scale_x = min(1.0, (5.5-cyc)/2)
        p_col = colTabs.column(align=True)
        #LyAddDecorLyColRaw(p_col.row(align=True))
        #LyAddDecorLyColRaw(p_col.row(align=True), sy=0.25) # 盒子无法收缩到比其空状态更小. 不得不寻找其他方法..
        match self.vaUiTabs:
            case 'SETTINGS':
                self.LyDrawTabSettings(colMain)
            case 'APPEARANCE':
                self.LyDrawTabAppearance(colMain)
            case 'DRAW':
                self.LyDrawTabDraw(colMain)
            case 'KEYMAP':
                self.LyDrawTabKeymaps(colMain)
            case 'INFO':
                self.LyDrawTabInfo(colMain)

def GetVlKeyconfigAsPy():  # 从 'bl_keymap_utils.io' 借来的. 我完全不知道它是如何工作的.

    def Ind(num: int):
        return " " * num

    def keyconfig_merge(kc1: bpy.types.KeyConfig, kc2: bpy.types.KeyConfig):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1 != kc2:
            merged_keymaps.extend((km, kc2) for km in kc2.keymaps if km.name not in kc1_names)
        return merged_keymaps

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.active

    class FakeKeyConfig:
        keymaps = []

    edited_kc = FakeKeyConfig()
    edited_kc.keymaps.append(user_node_keymap())
    if kc != wm.keyconfigs.default:
        export_keymaps = keyconfig_merge(edited_kc, kc)
    else:
        export_keymaps = keyconfig_merge(edited_kc, edited_kc)
    ##
    from . import keymap_item_defs
    result = ""
    result += "list_keyconfigData = \\\n["
    sco = 0
    for km, _kc_x in export_keymaps:
        km = km.active()
        result += "("
        result += f"\"{km.name:s}\"," + "\n"
        result += f"{Ind(2)}" "{"
        result += f"\"space_type\": '{km.space_type:s}'"
        result += f", \"region_type\": '{km.region_type:s}'"
        isModal = km.is_modal
        if isModal:
            result += ", \"modal\": True"
        result += "}," + "\n"
        result += f"{Ind(2)}" "{"
        result += f"\"items\":" + "\n"
        result += f"{Ind(3)}["
        for kmi in km.keymap_items:
            if not kmi.idname.startswith("node.voronoi_"):
                continue
            sco += 1
            if isModal:
                kmi_id = kmi.propvalue
            else:
                kmi_id = kmi.idname
            result += f"("
            kmi_args = bl_keymap_utils.io.kmi_args_as_data(kmi)
            kmi_data = bl_keymap_utils.io._kmi_attrs_or_none(4, kmi)
            result += f"\"{kmi_id:s}\""
            if kmi_data is None:
                result += f", "
            else:
                result += ",\n" f"{Ind(5)}"
            result += kmi_args
            if kmi_data is None:
                result += ", None)," + "\n"
            else:
                result += "," + "\n"
                result += f"{Ind(5)}" "{"
                result += kmi_data
                result += f"{Ind(6)}"
                result += "},\n" f"{Ind(5)}"
                result += ")," + "\n"
            result += f"{Ind(4)}"
        result += "],\n" f"{Ind(3)}"
        result += "},\n" f"{Ind(2)}"
        result += "),\n" f"{Ind(1)}"
    result += "]" + " #kmi count: " + str(sco) + "\n"
    result += "\n"
    result += "if True:" + "\n"
    result += "    import bl_keymap_utils" + "\n"
    result += "    import bl_keymap_utils.versioning" + "\n"  # 黑魔法; 似乎和 "gpu_extras" 一样.
    result += "    kc = bpy.context.window_manager.keyconfigs.active" + "\n"
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})" + "\n"
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result

def GetVaSettAsPy(prefs: bpy.types.AddonPreferences):
    from . import vt_classes, txtAddonVer
    set_ignoredAddonPrefs = {
        'bl_idname',
        'vaUiTabs',
        'vaInfoRestore',
        'dsIsFieldDebug',
        'dsIsTestDrawing',  # tovo2v6: 是全部吗?
        'vaKmiMainstreamDiscl',
        'vaKmiOtjersDiscl',
        'vaKmiSpecialDiscl',
        'vaKmiInvalidDiscl',
        'vaKmiQqmDiscl',
        'vaKmiCustomDiscl'
    }
    for cls in vt_classes:
        set_ignoredAddonPrefs.add(cls.disclBoxPropName)
        set_ignoredAddonPrefs.add(cls.disclBoxPropNameInfo)
    txt_vasp = ""
    txt_vasp += "#Exported/Importing addon settings for Voronoi Linker v" + txtAddonVer + "\n"
    import datetime
    txt_vasp += f"#Generated " + datetime.datetime.now().strftime("%Y.%m.%d") + "\n"
    txt_vasp += "\n"
    txt_vasp += "import bpy\n"
    # 构建已更改的插件设置:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{__package__}'].preferences" + "\n\n"
    txt_vasp += "def SetProp(att, val):" + "\n"
    txt_vasp += "    if hasattr(prefs, att):" + "\n"
    txt_vasp += " setattr(prefs, att, val)" + "\n\n"

    def AddAndProc(txt: str):
        nonlocal txt_vasp
        length = txt.find(",")
        txt_vasp += txt.replace(", ", "," + " " * (42-length), 1)

    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            # '_BoxDiscl' 我没忽略, 留着吧.
            if pr.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(pr, 'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(pr.default_array, getattr(prefs, pr.identifier)) if li[0] != li[1]]
                else:
                    isDiff = pr.default != getattr(prefs, pr.identifier)
                if (True) or (isDiff):  # 只保存差异可能不安全, 以防未保存的属性的默认值发生变化.
                    if isArray:
                        #txt_vasp += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                        list_vals = [str(li) + "," for li in getattr(prefs, pr.identifier)]
                        list_vals[-1] = list_vals[-1][:-1]
                        AddAndProc(f"SetProp('{pr.identifier}', (" + " ".join(list_vals) + "))\n")
                    else:
                        match pr.type:
                            case 'STRING':
                                AddAndProc(f"SetProp('{pr.identifier}', \"{getattr(prefs, pr.identifier)}\")" + "\n")
                            case 'ENUM':
                                AddAndProc(f"SetProp('{pr.identifier}', '{getattr(prefs, pr.identifier)}')" + "\n")
                            case _:
                                AddAndProc(f"SetProp('{pr.identifier}', {getattr(prefs, pr.identifier)})" + "\n")
    # 构建所有 VL 热键:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    # P.s. 我不知道如何只处理已更改的热键; 这看起来太头疼了, 像是一片茂密的森林. # tovo0v6
    # 懒得逆向工程 '..\scripts\modules\bl_keymap_utils\io.py', 所以就保存全部吧.
    txt_vasp += GetVlKeyconfigAsPy()  # 它根本不起作用; 恢复的那部分; 生成的脚本什么也没保存, 只有临时效果.
    # 不得不等待那个英雄来修复这一切.
    return txt_vasp

# 需要在 VoronoiAddonPrefs 类定义之后执行的动态属性添加函数
def add_dynamic_properties(vt_classes):
    """为每个工具类动态添加 BoxDiscl 属性到 VoronoiAddonPrefs"""
    for cls in vt_classes:
        setattr(VoronoiAddonPrefs, cls.disclBoxPropName, BoolProperty(name="", default=False))
        setattr(VoronoiAddonPrefs, cls.disclBoxPropNameInfo, BoolProperty(name="", default=False))

def update_lang_deb_enum_items(vt_classes):
    """更新语言调试枚举项列表"""
    global list_langDebEnumItems
    list_langDebEnumItems.clear()
    for li in ["Free", "Special", "AddonPrefs"] + [cls.bl_label for cls in vt_classes]:
        list_langDebEnumItems.append((li.upper(), GetFirstUpperLetters(li), ""))
    # 更新 VoronoiAddonPrefs 中的 vaLangDebEnum 属性
    VoronoiAddonPrefs.vaLangDebEnum = EnumProperty(name="LangDebEnum", default='FREE', items=list_langDebEnumItems)

def pref() -> VoronoiAddonPrefs:
    return bpy.context.preferences.addons[__package__].preferences # type: ignore
