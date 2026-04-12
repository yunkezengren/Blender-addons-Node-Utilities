import bpy
from typing import Any
from bpy.types import Operator
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
from .preference import VoronoiAddonPrefs, VoronoiOpAddonTabs, pref, add_dynamic_properties, update_lang_deb_enum_items

try:
    from rich import traceback
    # 在WindTerm里太宽了, 在VSCode终端里拉满
    # traceback.install(extra_lines=0, width=165, code_width=160, show_locals=False)
    traceback.install(extra_lines=0, width=140, show_locals=False)

    # from rich.console import Console      # 在别的文件里导入了
    # console = Console(width=160, log_time=False)
    # print = console.log    # 带有 时间戳 源文件路径 行号
    # from rich import print as rprint      # 用log打印报错太烦了每行都带路径
except ImportError:
    pass

""" 
#Todo0VV: 处理 n^3 种组合: space_data.tree_type 和 space_data.edit_tree.bl_idname; 包括经典的, 丢失的和插件的; 绑定和未绑定到编辑器的.
# ^ 然后检查所有工具在这些组合中的可用性. 之后在现有节点树中检查所有工具与丢失节点的丢失插槽的交互情况.
# todo1v6: 当工具处于活动状态时, 按下 PrtScr 会在控制台刷屏 `WARN ... pyrna_enum_to_py: ... '171' matches no enum in 'Event'.

dict_timeAvg = {}
dict_timeOutside = {}
# with ToTimeNs("aaa"):
class ToTimeNs():  # 我投降了. 🤷‍ 我不知道为什么在大型节点树上会这么卡. 但从测量结果来看, 卡顿的地方在 VL 插件之外.
    def __init__(self, name):
        self.name = name
        tpcn = perf_counter_ns()
        dict_timeOutside[name] = tpcn - dict_timeOutside.setdefault(name, 0)
        dict_timeAvg.setdefault(name, [0, 0])
        self.tmn = tpcn
    def __enter__(self):
        pass
    def __exit__(self, *_):
        tpcn = perf_counter_ns()
        nsExec = tpcn - self.tmn
        list_avg = dict_timeAvg[self.name]
        list_avg[0] += 1
        list_avg[1] += nsExec
        txt1 = "{:,}".format(nsExec).rjust(13)
        txt2 = "{:,}".format(dict_timeOutside[self.name]).rjust(13)
        txt3 = "{:,}".format(int(list_avg[1] / list_avg[0]))
        txt = " ".join(("", self.name, txt1, "~~~", txt2, "===", txt3))
        dict_timeOutside[self.name] = tpcn 
"""

# yapf: disable
# 每个 Operator 类的 keymap 配置. 格式: "S#A_KEY" 或 ("S#A_KEY", {'prop': value})  S=Shift, C=Ctrl, A=Alt, #=忽略, + =repeat
operator_keymaps: dict[type[Operator], list[str | tuple[str, dict[str, Any]]]] = {
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
        ("#C#_R", {'isPieChoice': False, 'isSelectNode': 1}),
        ("#C#_E", {'isInstantActivation': False}),
        ("##A_E", {'isToggleOptions': True}),
    ],
    NODE_OT_voronoi_swapper: [
        ("S##_S", {'toolMode': SwapperMode.SWAP.value}),
        ("##A_S", {'toolMode': SwapperMode.ADD.value}),
        ("S#A_S", {'toolMode': SwapperMode.TRAN.value}),
    ],
    NODE_OT_voronoi_hider: [
        ("S##_E", {'toolMode': HiderMode.HIDE_SOCKET.value}),
        ("#CA_E", {'toolMode': HiderMode.HIDE_VALUE.value}),
        ("SC#_E", {'toolMode': HiderMode.HIDE_NODE.value}),
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
        ("S#A_Z", {'toolMode': InterfacerMode.FLIP.value}),
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

all_classes: list[type[Operator]] = []  # 所有需要注册的类 (包括工具、偏好、饼菜单等)
vt_classes: list[type[Operator]] = []  # 只存放 V*T (Voronoi Tool) 工具
keymap_item_defs: list[tuple[str, str, bool, bool, bool, bool, dict[str, Any]]] = []

num_to_word: dict[str, str] = {"1": 'ONE', "2": 'TWO', "3": 'THREE', "4": 'FOUR', "5": 'FIVE', "6": 'SIX', "7": 'SEVEN', "8": 'EIGHT', "9": 'NINE', "0": 'ZERO'}
for operator_cls, keymaps in operator_keymaps.items():
    vt_classes.append(operator_cls)
    for km in keymaps:
        if isinstance(km, str):
            keymap_str, props = km, {}
        else:
            keymap_str, props = km
        mods, key = keymap_str[:4], keymap_str[4:]
        keymap_item_defs.append((
            operator_cls.bl_idname,
            num_to_word.get(key, key),
            "S" in mods,
            "C" in mods,
            "A" in mods,
            "+" in mods,
            props,
        ))
# yapf: enable

keymap_categorys = {'最有用': set(), '很有用': set(), '可能有用': set(), '无效': set(), 'qqm': set(), 'custom': set()}
keymap_categorys['最有用'] = {
    NODE_OT_voronoi_linker.bl_idname,
    NODE_OT_voronoi_preview.bl_idname,
    NODE_OT_voronoi_mixer.bl_idname,
    NODE_OT_voronoi_quick_math.bl_idname,
    NODE_OT_voronoi_hider.bl_idname,
    NODE_OT_voronoi_call_node_pie.bl_idname,
    NODE_OT_voronoi_quick_constant.bl_idname,
}
keymap_categorys['很有用'] = {
    NODE_OT_voronoi_mass_linker.bl_idname,
    NODE_OT_voronoi_interfacer.bl_idname,
    NODE_OT_voronoi_quick_dimensions.bl_idname,
    NODE_OT_voronoi_links_transfer.bl_idname,
    NODE_OT_voronoi_enum_selector.bl_idname,
    NODE_OT_voronoi_swapper.bl_idname,
}
keymap_categorys['可能有用'] = {
    NODE_OT_voronoi_link_repeating.bl_idname,
    NODE_OT_voronoi_reset_node.bl_idname,
    NODE_OT_voronoi_lazy_node_stencils.bl_idname,
    NODE_OT_voronoi_preview_anchor.bl_idname,
    NODE_OT_voronoi_warper.bl_idname,
}
# keymap_categorys['无效'].add(NODE_OT_voronoi_ranto.bl_idname)

assign_tool_class_names(vt_classes)
# 更新语言调试枚举项并添加动态属性
update_lang_deb_enum_items(vt_classes)
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
    VoronoiAddonPrefs,
]
all_classes = vt_classes + _classes

addon_keymaps = []

def register():
    bpy.app.translations.register(__package__, translations_dict)
    for cls in all_classes:
        bpy.utils.register_class(cls)

    prefs = pref()
    prefs.vlnstLastExecError = ""
    prefs.vaLangDebDiscl = False
    for cls in vt_classes:
        setattr(prefs, cls.disclBoxPropNameInfo, False)
    prefs.dsIsTestDrawing = False

    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for idname, key, shift, ctrl, alt, repeat, props in keymap_item_defs:
        kmi = km.keymap_items.new(idname=idname, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        kmi.active = idname != 'node.voronoi_dummy'
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
