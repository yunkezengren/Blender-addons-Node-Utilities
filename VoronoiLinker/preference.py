import bpy
import rna_keymap_ui
from typing import Callable
from bpy.app.translations import pgettext_iface as _iface
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, PointerProperty, StringProperty
from bpy.types import KeyMapItem, UILayout, Operator, AddonPreferences, PropertyGroup

from .common_class import VlnstUpdateLastExecError
from .utils.ui import split_prop, draw_panel_column, add_thin_sep, format_tool_label, user_node_keymap

HIDE_BOOL_SOCKET_ITEMS = [
    ('ALWAYS', "Always", "Always"),
    ('IF_FALSE', "If false", "If false"),
    ('NEVER', "Never", "Never"),
    ('IF_TRUE', "If true", "If true"),
]

CURSOR_COLOR_MODE_ITEMS = [
    ('DISABLED', "Disabled", "Do not tint lines with the cursor color"),
    ('SINGLE', "Single line", "Tint only the line from a single target to the cursor"),
    ('ALWAYS', "Always", "Always tint the cursor-side part of the line"),
]

MARKER_STYLE_ITEMS = [
    ('SMOOTH', "Smooth", "Smooth circular marker"),
    ('SHARP', "Sharp", "Sharper angular marker"),
    ('LOW_POLY', "Low-poly", "Low-poly marker"),
]

def update_test_draw(self, context):
    from .utils.drawing import TestDraw
    TestDraw.Toggle(context, self.test_drawing)

is_updating_decor_color = False

def update_decor_color_socket(self, _context):
    global is_updating_decor_color
    if is_updating_decor_color:
        return
    is_updating_decor_color = True
    self.va_decor_col_sk = self.va_decor_col_skBack
    is_updating_decor_color = False

class KeymapItemGroup:
    """快捷键项分类 - 用于组织和过滤keymap items"""
    group_key: str
    label: str
    matched_items: set
    idnames: set
    count: int
    filter: Callable[[KeyMapItem], bool] | None

    def __init__(self, group_key='', label='', matched_items=set(), idnames=set()):
        self.group_key = group_key
        self.label = label
        self.matched_items = matched_items
        self.idnames = idnames
        self.count = 0
        self.filter = None

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
    kmi_groups.quick_math = KeymapItemGroup('quick_math', 'Quick Math', set(), keymap_groups.quick_math)
    kmi_groups.custom = KeymapItemGroup('custom', 'Custom', set(), keymap_groups.custom)
    kmi_groups.most_useful = KeymapItemGroup('most_useful', 'Most Useful', set(), keymap_groups.most_useful)
    kmi_groups.quite_useful = KeymapItemGroup('quite_useful', 'Quite Useful', set(), keymap_groups.quite_useful)
    kmi_groups.maybe_useful = KeymapItemGroup('maybe_useful', 'Maybe Useful', set(), keymap_groups.maybe_useful)
    kmi_groups.invalid = KeymapItemGroup('invalid', 'Invalid', set(), keymap_groups.invalid)
    kmi_groups.most_useful.filter = lambda kmi: kmi.idname in kmi_groups.most_useful.idnames
    kmi_groups.quite_useful.filter = lambda kmi: kmi.idname in kmi_groups.quite_useful.idnames
    kmi_groups.maybe_useful.filter = lambda kmi: kmi.idname in kmi_groups.maybe_useful.idnames
    kmi_groups.invalid.filter = lambda kmi: True
    kmi_groups.quick_math.filter = lambda kmi: any(
        True for txt in {'quickOprFloat', 'quickOprVector', 'quickOprBool', 'quickOprColor', 'justPieCall', 'isRepeatLastOperation'}
        if getattr(kmi.properties, txt, None))
    kmi_groups.custom.filter = lambda kmi: kmi.id < 0  # 负id用于自定义
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
                prefs.va_ui_tabs = self.opt
        return {'FINISHED'}

class DrawPrefs(PropertyGroup):
    draw_text         : BoolProperty(name="Text",        default=True)  # 考虑到 VHT 和 VEST, 这更多是用于框架中的文本, 而不是来自插槽的文本.
    node_label        : BoolProperty(name="Node label",  default=True)
    draw_point        : BoolProperty(name="Points",      default=True)
    draw_marker       : BoolProperty(name="Markers",     default=True)
    draw_line         : BoolProperty(name="Line",        default=True)
    draw_socket_area  : BoolProperty(name="Socket area", default=True)
    color_text        : BoolProperty(name="Text",        default=True)
    color_node_label  : BoolProperty(name="Node label",  default=True)
    color_point       : BoolProperty(name="Points",      default=True)
    color_marker      : BoolProperty(name="Markers",     default=True)
    color_line        : BoolProperty(name="Line",        default=True)
    color_socket_area : BoolProperty(name="Socket area", default=True)

    always_draw_line  : BoolProperty(name="Always draw line", default=True, description="Draw a line to the cursor even from a single selected socket")

    socket_area_alpha : FloatProperty(name="Socket area alpha", default=0.4, min=0.0, max=1.0, subtype="FACTOR")
    uniform_color     : FloatVectorProperty(name="Alternative uniform color", default=(1, 0, 0, 0.9), min=0, max=1, size=4, subtype='COLOR')
    uniform_node_color: FloatVectorProperty(name="Alternative nodes color", default=(0, 1, 0, 0.9), min=0, max=1, size=4, subtype='COLOR')
    cursor_color      : FloatVectorProperty(name="Cursor color", default=(0, 0, 0, 1.0), min=0, max=1, size=4, subtype='COLOR')
    cursor_color_mode : EnumProperty(name="Cursor color mode", default='ALWAYS', items=CURSOR_COLOR_MODE_ITEMS, description="How cursor color is applied to lines")

    display_style     : EnumProperty(name="Display frame style", default='ONLY_TEXT', items=(('CLASSIC', "Classic", "Classic"), ('SIMPLIFIED', "Simplified", "Simplified"), ('ONLY_TEXT', "Only text", "Only text")))
    font_file         : StringProperty(name="Font file", default='C:\\Windows\\Fonts\\consola.ttf', subtype='FILE_PATH')  # "Linux 用户表示不满".
    font_size         : IntProperty(name="Font size", default=32, min=10, max=48)
    line_width        : FloatProperty(name="Line Width", default=2, min=0.5, max=8.0, subtype="FACTOR")
    point_scale       : FloatProperty(name="Point scale", default=1.0, min=0.0, max=3.0)
    marker_style      : EnumProperty(name="Marker style", default='SMOOTH', items=MARKER_STYLE_ITEMS, description="Shape used for link markers")

    text_x_offset     : FloatProperty(name="Text X offset", default=25.0, min=-50.0, max=50.0)
    text_y_offset     : FloatProperty(name="Text Y offset", default=-0.2)
    point_x_offset    : FloatProperty(name="Point X offset", default=8.0, min=-50.0, max=50.0)
    frame_padding     : IntProperty(name="Frame padding", default=0, min=0, max=24, subtype='FACTOR', description="Extra padding for text frames")  # : 这必须是 Int.

    enable_shadow     : BoolProperty(name="Enable text shadow", default=False)
    shadow_color      : FloatVectorProperty(name="Shadow color", default=(0.0, 0.0, 0.0, 0.5), min=0, max=1, size=4, subtype='COLOR')
    shadow_offset     : IntVectorProperty(name="Shadow offset", default=(2, -2), min=-20, max=20, size=2)
    shadow_blur       : IntProperty(name="Shadow blur", default=2, min=0, max=2)

    debug_field       : BoolProperty(name="Field debug", default=False)
    test_drawing      : BoolProperty(name="Testing draw", default=False, update=update_test_draw)

class VoronoiAddonPrefs(AddonPreferences):
    bl_idname = __package__ # type: ignore
    draw_prefs: PointerProperty(type=DrawPrefs)
    # --- VoronoiLinkerTool
    vlt_repick_key            : StringProperty(name="Repick Key", default='LEFT_ALT', description="Hold this key to re-pick target socket without releasing the mouse")
    vlt_reroutes_can_in_any_type : BoolProperty(name="Reroutes can be connected to any type", default=True)
    vlt_deselect_all_nodes     : BoolProperty(name="Deselect all nodes on activate",        default=False)
    vlt_priority_ignoring     : BoolProperty(name="Priority ignoring",                     default=False, description="High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)")
    vlt_selecting_involved    : BoolProperty(name="Selecting involved nodes",              default=False)
    # --- VoronoiPreviewTool
    vpt_allow_classic_geo_viewer        : BoolProperty(name="Allow classic GeoNodes Viewer",   default=True,  description="Allow use of classic GeoNodes Viewer by clicking on node")
    vpt_allow_classic_compositor_viewer : BoolProperty(name="Allow classic Compositor Viewer", default=False, description="Allow use of classic Compositor Viewer by clicking on node")
    vpt_is_live_preview                : BoolProperty(name="Live Preview",                    default=True,  description="Real-time preview")
    vpt_rv_ee_is_color_onion_nodes        : BoolProperty(name="Node onion colors",               default=False, description="Coloring topologically connected nodes")
    vpt_rv_ee_sks_highlighting          : BoolProperty(name="Topology connected highlighting", default=False, description="Display names of sockets whose links are connected to a node")
    vpt_rv_ee_is_save_preview_results     : BoolProperty(name="Save preview results",            default=False, description="Create a preview through an additional node, convenient for copying")
    vpt_onion_color_in                 : FloatVectorProperty(name="Onion color entrance", default=(0.55,  0.188, 0.188), min=0, max=1, size=3, subtype='COLOR')
    vpt_onion_color_out                : FloatVectorProperty(name="Onion color exit",     default=(0.188, 0.188, 0.5),   min=0, max=1, size=3, subtype='COLOR')
    vpt_hl_text_scale                  : FloatProperty(name="Text scale", default=1.0, min=0.5, max=5.0)
    # ------
    vmt_reroutes_can_in_any_type  : BoolProperty(name="Reroutes can be mixed to any type", default=True)
    ##
    vmt_pie_type               : EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vmt_pie_scale              : FloatProperty(name="Pie scale",                default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vmt_pie_alignment          : IntProperty(  name="Alignment between items",  default=1,   min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vmt_pie_socket_display_type  : IntProperty(  name="Display socket type info", default=1,   min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vmt_pie_display_socket_color : IntProperty(  name="Display socket color",     default=-1,  min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")
    # ------
    vqmt_display_icons         : BoolProperty(name="Display icons",           default=True)
    vqmt_include_third_sk       : BoolProperty(name="Include third socket",    default=True)
    vqmt_include_quick_presets  : BoolProperty(name="Include quick presets",   default=False)
    vqmt_include_existing_values: BoolProperty(name="Include existing values", default=False)
    vqmt_repick_key            : StringProperty(name="Repick Key", default='LEFT_ALT', description="Hold this key to re-pick target socket without releasing the mouse")
    ##
    vqmt_pie_type              : EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vqmt_pie_scale             : FloatProperty(name="Pie scale",                default=1.3,  min=1.0, max=2.0, subtype="FACTOR")
    vqmt_pie_scale_extra        : FloatProperty(name="Pie scale extra",          default=1.25, min=1.0, max=2.0, subtype="FACTOR")
    vqmt_pie_alignment         : IntProperty(  name="Alignment between items",  default=1,    min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vqmt_pie_socket_display_type : IntProperty(  name="Display socket type info", default=1,    min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vqmt_pie_display_socket_color: IntProperty(  name="Display socket color",     default=-1,   min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")
    # ------
    vrt_is_live_ranto           : BoolProperty(name="Live Ranto", default=True)
    vrt_is_fix_islands          : BoolProperty(name="Fix islands", default=True)
    # ------
    vht_hide_bool_socket        : EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=HIDE_BOOL_SOCKET_ITEMS)
    vht_hide_hidden_bool_socket  : EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=HIDE_BOOL_SOCKET_ITEMS)
    vht_never_hide_geometry     : EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False",""), ('ONLY_FIRST',"Only first",""), ('TRUE',"True","") ))
    vht_is_unhide_virtual       : BoolProperty(name="Unhide virtual sockets",           default=True)
    vht_is_toggle_nodes_on_drag   : BoolProperty(name="Toggle nodes on drag",             default=True)
    # ------
    vmlt_ignore_case           : BoolProperty(name="Ignore case", default=True)
    # ------
    vest_is_toggle_nodes_on_drag  : BoolProperty(name="Toggle nodes on drag", default=True)
    vest_box_scale             : FloatProperty(name="Box scale",           default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vest_display_labels        : BoolProperty(name="Display enum names",   default=True)
    vest_dark_style            : BoolProperty(name="Dark style",           default=False)
    vit_paste_to_any_socket      : BoolProperty(name="Allow paste to any socket", default=False)
    vwt_select_target_key       : StringProperty(name="Select target Key", default='LEFT_ALT', description="Hold this key to select the target node instead of just jumping to it")
    vlnst_non_color_name        : StringProperty(name="Non-Color name",  default="Non-Color")
    vlnst_last_exec_error       : StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)
    vdt_dummy                 : StringProperty(name="Dummy", default="Dummy")
    # ------
    ds_include_dev          : BoolProperty(name="Include Dev", default=False)
    # ------
    va_ui_tabs: EnumProperty(name="Addon pref Tabs", default='SETTINGS', items=(
        ('SETTINGS', "Settings", ""), ('APPEARANCE', "Appearance", ""), ('DRAW', "Draw", ""), ('KEYMAP', "Keymap", ""), ('INFO', "Info", "")))
    va_info_restore        : BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    va_decor_ly            : FloatVectorProperty(name="DecorForLayout",   default=(0.01, 0.01, 0.01),   min=0, max=1, size=3, subtype='COLOR')
    va_decor_col_sk         : FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=update_decor_color_socket)
    va_decor_col_skBack     : FloatVectorProperty(name="va_decor_col_skBack", default=(1.0, 1.0, 1.0, 1.0), min = 0, max=1, size=4, subtype='COLOR')
    # ------
    edge_pan_factor      : FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    edge_pan_speed            : FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    override_zoom_limits      : BoolProperty(name="Overwriting zoom limits", default=False)
    zoom_min         : FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    zoom_max         : FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)
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
            split_prop(panel_col, self, 'edge_pan_factor', text="Zoom factor")
            split_prop(panel_col, self, 'edge_pan_speed', text="Speed")
            if (self.ds_include_dev) or self.override_zoom_limits:
                split_prop(panel_col, self, 'override_zoom_limits')
                if self.override_zoom_limits:
                    split_prop(panel_col, self, 'zoom_min')
                    split_prop(panel_col, self, 'zoom_max')

        from . import vt_classes
        for cls in vt_classes:
            if cls.can_draw_appearance:
                cls.draw_pref_appearance(col_main, self)

    def draw_tab_draw(self, layout: UILayout):
        col_main = layout.column()
        draw_pref = self.draw_prefs

        is_draw_props = [
            'draw_text',
            'node_label',
            'draw_point',
            'draw_marker',
            'draw_line',
            'draw_socket_area',
        ]
        box_split_draw = col_main.box().split(align=True)
        box_split_draw.use_property_split = True
        is_draw_col = box_split_draw.column(align=True, heading='Draw')
        for is_draw in is_draw_props:
            row = is_draw_col.row(align=True)
            row.prop(draw_pref, is_draw)
            if is_draw == "node_label":
                row.active = draw_pref.draw_text
        is_colored_col = box_split_draw.column(align=True, heading='Colored')
        for is_draw in is_draw_props:
            row = is_colored_col.row(align=True)
            color_prop = is_draw.replace("draw_", "color_", 1) if is_draw.startswith("draw_") else f"color_{is_draw}"
            row.prop(draw_pref, color_prop)
            label_active = True if is_draw != "node_label" else draw_pref.draw_text and draw_pref.color_text and draw_pref.color_node_label
            row.active = getattr(draw_pref, is_draw) and label_active

        if panel_col := draw_panel_column(col_main, "Behavior"):
            split_prop(panel_col, draw_pref, 'always_draw_line')

        if panel_col := draw_panel_column(col_main, "Color"):
            split_prop(panel_col, draw_pref, 'socket_area_alpha', active=draw_pref.draw_socket_area)
            use_uniform_color = ((draw_pref.draw_text and not draw_pref.color_text)
                                 or (draw_pref.draw_marker and not draw_pref.color_marker)
                                 or (draw_pref.draw_point and not draw_pref.color_point)
                                 or (draw_pref.draw_line and not draw_pref.color_line)
                                 or (draw_pref.draw_socket_area and not draw_pref.color_socket_area))
            if use_uniform_color:
                split_prop(panel_col, draw_pref, 'uniform_color')
            use_node_color = ((draw_pref.draw_text and draw_pref.color_text) or (draw_pref.draw_point and draw_pref.color_point)
                              or (draw_pref.draw_line and draw_pref.color_line))
            if use_node_color and not draw_pref.color_node_label:
                split_prop(panel_col, draw_pref, 'uniform_node_color')
            point_cursor = draw_pref.draw_point and draw_pref.color_point
            line_cursor = draw_pref.draw_line and draw_pref.color_line and draw_pref.cursor_color_mode != 'DISABLED'
            split_prop(panel_col, draw_pref, 'cursor_color', active=point_cursor or line_cursor)
            split_prop(panel_col, draw_pref, 'cursor_color_mode', active=draw_pref.draw_line and draw_pref.color_line)

        if panel_col := draw_panel_column(col_main, "Style"):
            split_prop(panel_col, draw_pref, 'display_style')
            split_prop(panel_col, draw_pref, 'font_file')
            if not draw_pref.font_file.endswith((".ttf", ".otf")):
                split_row = panel_col.split(factor=0.4, align=True)
                split_row.label(text="")
                split_row.label(text="Only .ttf or .otf format", icon='ERROR')
            add_thin_sep(panel_col, 0.5)
            split_prop(panel_col, draw_pref, 'line_width')
            split_prop(panel_col, draw_pref, 'point_scale')
            split_prop(panel_col, draw_pref, 'font_size')
            split_prop(panel_col, draw_pref, 'marker_style')

        if panel_col := draw_panel_column(col_main, "Offset"):
            split_prop(panel_col, draw_pref, 'point_x_offset')
            split_prop(panel_col, draw_pref, 'text_x_offset')
            split_prop(panel_col, draw_pref, 'text_y_offset')
            if draw_pref.display_style != "ONLY_TEXT":
                split_prop(panel_col, draw_pref, 'frame_padding')
            add_thin_sep(panel_col, 0.25)  # 间隔的空白会累加, 所以额外加个间隔来对齐.
            split_prop(panel_col, draw_pref, 'enable_shadow')
            if draw_pref.enable_shadow:
                col_shadow = panel_col.column(align=True)
                split_prop(col_shadow, draw_pref, 'shadow_color')
                split_prop(col_shadow, draw_pref, 'shadow_blur')  # 阴影模糊将它们分开, 以免在中间融合在一起.
                row = split_prop(col_shadow, draw_pref, 'shadow_offset', returnAsLy=True).row(align=True)
                row.row().prop(draw_pref, 'shadow_offset', text="X  ", translate=False, index=0, icon_only=True)
                row.row().prop(draw_pref, 'shadow_offset', text="Y  ", translate=False, index=1, icon_only=True)

        if self.ds_include_dev:
            if panel_col := draw_panel_column(col_main, "Debug"):
                split_prop(panel_col, draw_pref, 'debug_field')
                split_prop(panel_col, draw_pref, 'test_drawing')

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
            panel, body = layout.panel(idname=category.group_key, default_closed=True)
            row = panel.row(align=True)
            active_count = sum(kmi.active for kmi in category.matched_items)
            icon= 'CHECKBOX_HLT' if active_count else 'CHECKBOX_DEHLT'
            row.operator(VoronoiOpAddonTabs.bl_idname, text="", icon=icon, emboss=False).opt = f"toggle_kmi_group:{category.group_key}"
            row.label(text=f"{_iface(category.label)}  ({active_count}/{category.count})")
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
        layout.prop(self, 'ds_include_dev')

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

    def draw(self, context):

        def draw_layout_decor_column(layout: UILayout, scale_y=0.05, scale_x=1.0, enabled=False):
            layout.prop(self, 'va_decor_ly', text="")
            layout.scale_x = scale_x
            layout.scale_y = scale_y  # 如果小于 0.05, 布局会消失, 圆角也会消失.
            layout.enabled = enabled

        col_layout = self.layout.column()
        col_main = col_layout.column(align=True)
        col_tabs = col_main.column(align=True)
        row_tabs = col_tabs.row(align=True)
        # 标签页切换是通过操作符创建的, 以免在按住鼠标拖动时意外切换标签页, 这在有大量"isColored"选项时很有诱惑力. 而且现在它们被装饰得更像"标签页"了, 这是普通的 prop 布局 с 'expand=True' 无法做到的.
        for cyc, li in enumerate(en for en in self.rna_type.properties['va_ui_tabs'].enum_items):
            col = row_tabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=_iface(li.name), depress=self.va_ui_tabs == li.identifier).opt = li.identifier
            draw_layout_decor_column(col.row(align=True))

        match self.va_ui_tabs:
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
        setattr(VoronoiAddonPrefs, cls.discl_box_prop_name, BoolProperty(name="", default=False))
        setattr(VoronoiAddonPrefs, cls.discl_box_prop_name_info, BoolProperty(name="", default=False))

def pref() -> VoronoiAddonPrefs:
    return bpy.context.preferences.addons[__package__].preferences # type: ignore
