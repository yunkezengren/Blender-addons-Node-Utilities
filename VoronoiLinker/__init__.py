import bpy
from bpy.types import Operator
from typing import NamedTuple
from .base_tool import ModelBaseTool
from .tools.call_node_pie import NODE_OT_voronoi_call_node_pie
from .tools.enum_selector import NODE_OT_enum_selector_box, NODE_MT_enum_selector_pie, NODE_OT_voronoi_enum_selector
from .tools.hider import HiderMode, NODE_OT_voronoi_hider
from .tools.interfacer import InterfacerMode, NODE_OT_voronoi_interfacer
from .tools.lazy_node_stencils import NODE_OT_voronoi_lazy_node_stencils
from .tools.link_repeating import LinkRepeatingMode, NODE_OT_voronoi_link_repeating
from .tools.linker import NODE_OT_voronoi_linker
from .tools.links_transfer import NODE_OT_voronoi_links_transfer
from .tools.mass_linker import NODE_OT_voronoi_mass_linker
from .tools.matrix_convert import PIE_MT_Combine_Matrix, PIE_MT_Convert_Rotation_To, PIE_MT_Convert_To_Rotation, PIE_MT_Separate_Matrix, NODE_OT_rot_or_mat_convert
from .tools.mixer import NODE_OT_voronoi_mixer
from .tools.mixer_sub import NODE_OT_mixer_sub, NODE_MT_mixer_pie
from .tools.preview import NODE_OT_voronoi_preview
from .tools.preview_anchor import NODE_OT_voronoi_preview_anchor
from .tools.quick_constant import NODE_OT_voronoi_quick_constant
from .tools.quick_dimensions import NODE_OT_voronoi_quick_dimensions
from .tools.quick_math import NODE_OT_voronoi_quick_math
from .tools.quick_math_sub import NODE_OT_quick_math_sub, NODE_MT_quick_math_pie
from .tools.reset_node import NODE_OT_voronoi_reset_node
from .tools.swapper import SwapperMode, NODE_OT_voronoi_swapper
from .tools.warper import NODE_OT_voronoi_warper
from .utils.translations import translations_dict
from .utils.solder import register_socket_properties, assign_tool_class_names, unregister_socket_properties
from .preference import DrawPrefs, VoronoiAddonPrefs, VoronoiOpAddonTabs, pref, add_dynamic_properties

try:
    from rich import traceback
    # traceback.install(extra_lines=0, width=165, code_width=160, show_locals=False)  # 在WindTerm里太宽了, 在VSCode终端里拉满
    traceback.install(extra_lines=0, width=140, show_locals=False)

    # from rich.console import Console      # 在别的文件里导入了
    # console = Console(width=160, log_time=False)
    # print = console.log    # 带有 时间戳 源文件路径 行号
    # from rich import print as rprint      # 用log打印报错太烦了每行都带路径
except ImportError:
    pass

class KeymapItemDef(NamedTuple):
    idname: str
    key: str
    shift: bool
    ctrl: bool
    alt: bool
    repeat: bool
    props: dict[str, object]

# yapf: disable
# 每个 Operator 类的 keymap 配置. 格式: "S#A_KEY" 或 ("S#A_KEY", {'prop': value})  S=Shift, C=Ctrl, A=Alt, #=忽略, + =repeat
operator_keymaps: dict[type[Operator], list[str | tuple[str, dict[str, object]]]] = {
    NODE_OT_voronoi_linker: ["##A_RIGHTMOUSE"],
    NODE_OT_voronoi_preview: ["SC#_LEFTMOUSE"],
    NODE_OT_voronoi_mixer: ["S#A_LEFTMOUSE"],
    NODE_OT_voronoi_call_node_pie: ["#C#_LEFTMOUSE"],
    NODE_OT_voronoi_quick_dimensions: ["##A_D"],
    NODE_OT_voronoi_quick_constant: ["##A_C"],
    NODE_OT_voronoi_mass_linker: [
        "SCA_LEFTMOUSE",
        ("SCA_RIGHTMOUSE", {'isIgnoreExistingLinks': True}),
        ],
    NODE_OT_voronoi_links_transfer: [
        "S##_T",
        ("SCA_T", {'isByIndexes': True}),
        ],
    NODE_OT_voronoi_warper: [
        "S#A_W",
        ("SCA_W", {'isZoomedTo': False}),
        ],
    NODE_OT_voronoi_reset_node: [
        "###_BACK_SPACE",
        ("S##_BACK_SPACE", {'isResetEnums': True}),
        ],
    NODE_OT_voronoi_preview_anchor: [
        "SC#_RIGHTMOUSE",
        ("SC#_1", {'anchorType': 1}),
        ("SC#_2", {'anchorType': 2}),
        ("SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors': 2}),  # ACCENT_GRAVE 是 `
    ],
    NODE_OT_voronoi_enum_selector: [
        ("##A_E", {'isToggleOptions': True}),
        ("#C#_E", {'isInstantActivation': False}),
        ("#C#_R", {'isPieChoice': True, 'isSelectNode': 1}),
    ],
    NODE_OT_voronoi_swapper: [
        ("S##_S", {'toolMode': SwapperMode.SWAP.value}),
        ("##A_S", {'toolMode': SwapperMode.ADD.value}),
        ("S#A_S", {'toolMode': SwapperMode.TRAN.value}),
    ],
    NODE_OT_voronoi_hider: [
        ("S##_E", {'toolMode': HiderMode.HIDE_SOCKET.value}),
        ("#CA_E", {'toolMode': HiderMode.HIDE_VALUE.value}),
        ("SC#_E", {'toolMode': HiderMode.HIDE_AUTO.value}),
    ],
    NODE_OT_voronoi_link_repeating: [
        ("###_V", {'toolMode': LinkRepeatingMode.SOCKET.value}),
        ("S##_V", {'toolMode': LinkRepeatingMode.NODE.value}),
    ],
    NODE_OT_voronoi_interfacer: [
        ("SC#_A", {'toolMode': InterfacerMode.NEW.value}),
        ("S#A_A", {'toolMode': InterfacerMode.CREATE.value}),
        ("S#A_C", {'toolMode': InterfacerMode.COPY.value}),
        ("S#A_V", {'toolMode': InterfacerMode.PASTE.value}),
        ("S#A_X", {'toolMode': InterfacerMode.SWAP.value}),
        ("S#A_Z", {'toolMode': InterfacerMode.MOVE.value}),
        # ("S#A_Q", {'toolMode':InterfacerMode.DELETE.value}),
        # ("S#A_E", {'toolMode':InterfacerMode.TYPE.value}),
    ],
    NODE_OT_voronoi_quick_math: [
        "S#A_RIGHTMOUSE",  # 留在了右键, 以免在'Speed Pie'类型的饼菜单下三击左键时抓狂.
        ("##A_ACCENT_GRAVE", {'isRepeatLastOperation': True}),
        # 快速数学运算的快速操作列表("x2 组合"): "3"键上的布尔运算存在两难选择, 它可以是减法, 像这个键上的所有操作一样, 也可以是否定, 作为前两个的逻辑延续. 在第二种情况下, "4"键上的布尔运算很可能得留空.
        ("##A_1", {'quickOprFloat': 'ADD',      'quickOprVector': 'ADD',      'quickOprBool': 'OR',     'quickOprColor': 'ADD'}),
        ("##A_2", {'quickOprFloat': 'SUBTRACT', 'quickOprVector': 'SUBTRACT', 'quickOprBool': 'NIMPLY', 'quickOprColor': 'SUBTRACT'}),
        ("##A_3", {'quickOprFloat': 'MULTIPLY', 'quickOprVector': 'MULTIPLY', 'quickOprBool': 'AND',    'quickOprColor': 'MULTIPLY'}),
        ("##A_4", {'quickOprFloat': 'DIVIDE',   'quickOprVector': 'DIVIDE',   'quickOprBool': 'NOT',    'quickOprColor': 'DIVIDE'}),
        # 我本想为QuickMathMain实现这个功能, 但发现将技术操作符变成用户操作符太麻烦. 主要问题是VqmtData的饼菜单设置. 出乎意料的是, 这样的热键用起来非常舒服.因为有两个修饰键, 必须按住,所以必须通过光标位置来选择, 而不是点击. 我原以为会不方便, 结果感觉还不错.
        ("S#A_1", {'justPieCall': 1}),
        ("S#A_2", {'justPieCall': 2}),
        ("S#A_3", {'justPieCall': 3}),
        ("S#A_4", {'justPieCall': 4}),
        ("S#A_5", {'justPieCall': 5}),
    ],
    # NODE_OT_voronoi_lazy_node_stencils: [("S#A_Q")],
    # NODE_OT_voronoi_ranto: [
    #     ("###_R"),
    #     ("S##_R", {'isAccumulate':True}),
    #     ("#C#_R", {'isOnlySelected':2}),
    #     ("#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True}),
    # ],
}

vt_classes: list[type[ModelBaseTool]] = []  # 只存放 Voronoi Tool 工具
keymap_item_defs: list[KeymapItemDef] = []

num_to_word: dict[str, str] = {"1": 'ONE', "2": 'TWO', "3": 'THREE', "4": 'FOUR', "5": 'FIVE', "6": 'SIX', "7": 'SEVEN', "8": 'EIGHT', "9": 'NINE', "0": 'ZERO'}
for operator_cls, keymaps in operator_keymaps.items():
    vt_classes.append(operator_cls)
    for km in keymaps:
        if isinstance(km, str):
            keymap_str, props = km, {}
        else:
            keymap_str, props = km
        mods, key = keymap_str[:4], keymap_str[4:]
        keymap_item_defs.append(KeymapItemDef(
            operator_cls.bl_idname,
            num_to_word.get(key, key),
            "S" in mods,
            "C" in mods,
            "A" in mods,
            "+" in mods,
            props,
        ))
# yapf: enable

class KeymapGroups(NamedTuple):
    most_useful: set[str]
    quite_useful: set[str]
    maybe_useful: set[str]
    invalid: set[str]
    quick_math: set[str]
    custom: set[str]

keymap_groups = KeymapGroups(
    most_useful={
        NODE_OT_voronoi_linker.bl_idname,
        NODE_OT_voronoi_preview.bl_idname,
        NODE_OT_voronoi_mixer.bl_idname,
        NODE_OT_voronoi_quick_math.bl_idname,
        NODE_OT_voronoi_hider.bl_idname,
        NODE_OT_voronoi_call_node_pie.bl_idname,
        NODE_OT_voronoi_quick_constant.bl_idname,
    },
    quite_useful={
        NODE_OT_voronoi_mass_linker.bl_idname,
        NODE_OT_voronoi_interfacer.bl_idname,
        NODE_OT_voronoi_quick_dimensions.bl_idname,
        NODE_OT_voronoi_links_transfer.bl_idname,
        NODE_OT_voronoi_enum_selector.bl_idname,
        NODE_OT_voronoi_swapper.bl_idname,
    },
    maybe_useful={
        NODE_OT_voronoi_link_repeating.bl_idname,
        NODE_OT_voronoi_reset_node.bl_idname,
        NODE_OT_voronoi_lazy_node_stencils.bl_idname,
        NODE_OT_voronoi_preview_anchor.bl_idname,
        NODE_OT_voronoi_warper.bl_idname,
    },
    invalid=set(),
    quick_math=set(),
    custom=set(),
)
# keymap_groups.invalid.add(NODE_OT_voronoi_ranto.bl_idname)

assign_tool_class_names(vt_classes)
add_dynamic_properties(vt_classes)

_classes = [
    NODE_OT_mixer_sub,
    NODE_MT_mixer_pie,
    NODE_OT_quick_math_sub,
    NODE_MT_quick_math_pie,
    NODE_OT_enum_selector_box,
    NODE_MT_enum_selector_pie,
    NODE_OT_rot_or_mat_convert,
    PIE_MT_Convert_To_Rotation,
    PIE_MT_Convert_Rotation_To,
    PIE_MT_Separate_Matrix,
    PIE_MT_Combine_Matrix,
    VoronoiOpAddonTabs,
    DrawPrefs,
    VoronoiAddonPrefs,
]
all_classes = vt_classes + _classes

addon_keymaps = []

def register():
    bpy.app.translations.register(__package__, translations_dict)
    for cls in all_classes:
        bpy.utils.register_class(cls)

    prefs = pref()
    prefs.vlnst_last_exec_error = ""
    for cls in vt_classes:
        setattr(prefs, cls.discl_box_prop_name_info, False)
    prefs.draw_prefs.test_drawing = False

    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for idname, key, shift, ctrl, alt, repeat, props in keymap_item_defs:
        kmi = km.keymap_items.new(idname=idname, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        if props:
            for key, value in props.items():
                setattr(kmi.properties, key, value)
        addon_keymaps.append(kmi)

    register_socket_properties()

def unregister():
    unregister_socket_properties()

    km = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in all_classes:
        bpy.utils.unregister_class(cls)
    bpy.app.translations.unregister(__package__)
