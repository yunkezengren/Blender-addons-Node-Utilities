import bpy
from time import perf_counter_ns
from bpy.types import Operator
from .common_forward_func import Prefs
from .tools.call_node_pie import VoronoiCallNodePie
from .tools.enum_selector import VestOpBox, VestPieBox, VoronoiEnumSelectorTool
from .tools.hider import HiderMode, VoronoiHiderTool
from .tools.interfacer import InterfacerMode, VoronoiInterfacerTool
from .tools.lazy_node_stencils import VoronoiLazyNodeStencilsTool
from .tools.link_repeating import LinkRepeatingMode, VoronoiLinkRepeatingTool
from .tools.linker import VoronoiLinkerTool
from .tools.links_transfer import VoronoiLinksTransferTool
from .tools.mass_linker import VoronoiMassLinkerTool
from .tools.matrix_convert import PIE_MT_Combine_Matrix, PIE_MT_Convert_Rotation_To, PIE_MT_Convert_To_Rotation, PIE_MT_Separate_Matrix, Rot_or_Mat_Convert
from .tools.mixer import VoronoiMixerTool
from .tools.mixer_sub import VmtOpMixer, VmtPieMixer
from .tools.pie_math import VqmtOpMain, VqmtPieMath
from .tools.preview import VoronoiPreviewTool
from .tools.preview_anchor import VoronoiPreviewAnchorTool
from .tools.quick_constant import VoronoiQuickConstant
from .tools.quick_dimensions import VoronoiQuickDimensionsTool
from .tools.quick_math import VoronoiQuickMathTool
from .tools.reset_node import VoronoiResetNodeTool
from .tools.swapper import SwapperMode, VoronoiSwapperTool
from .tools.warper import VoronoiWarperTool
from .translations import translations_dict
from .utils.solder import RegisterSolderings, SolderClsToolNames, UnregisterSolderings
from .preference import VoronoiAddonPrefs, VoronoiOpAddonTabs, AddDynamicProperties, UpdateLangDebEnumItems

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

dict_classes = {}  # 所有需要注册的类都放在这里. 使用字典是为了 smart_add_to_reg_and_kmiDefs() 函数, 同时还能保持顺序.
dict_vtClasses = {}  # 只存放 V*T (Voronoi Tool) 工具.

list_kmiDefs = []
dict_setKmiCats = {'最有用': set(), '很有用': set(), '可能有用': set(), '无效': set(), 'qqm': set(), 'custom': set()}

def smart_add_to_reg_and_kmiDefs(cls: Operator, txt: str, dict_props={}):
    dict_numToKey = {
        "1": 'ONE',
        "2": 'TWO',
        "3": 'THREE',
        "4": 'FOUR',
        "5": 'FIVE',
        "6": 'SIX',
        "7": 'SEVEN',
        "8": 'EIGHT',
        "9": 'NINE',
        "0": 'ZERO'
    }
    dict_classes[cls] = True
    dict_vtClasses[cls] = True
    list_kmiDefs.append((cls.bl_idname, dict_numToKey.get(txt[4:],
                                                          txt[4:]), txt[0] == "S", txt[1] == "C", txt[2] == "A", txt[3] == "+", dict_props))

#Todo0VV: 处理 n^3 种组合: space_data.tree_type 和 space_data.edit_tree.bl_idname; 包括经典的, 丢失的和插件的; 绑定和未绑定到编辑器的.
# ^ 然后检查所有工具在这些组合中的可用性. 之后在现有节点树中检查所有工具与丢失节点的丢失插槽的交互情况.

dict_timeAvg = {}
dict_timeOutside = {}

#    with ToTimeNs("aaa"):
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

# todo1v6: 当工具处于活动状态时, 按下 PrtScr 会在控制台刷屏 `WARN ... pyrna_enum_to_py: ... '171' matches no enum in 'Event'`.

def _tool_desc(tool_cls: Operator, /, desc=""):
    """注册工具的多语言描述"""
    if desc: tool_cls.bl_description = desc

_tool_desc(VoronoiLinkerTool,
    "The sacred tool. The reason this entire addon was created.\nA moment of silence in honor of NodeWrangler, the original ancestor.",
)
_tool_desc(VoronoiPreviewTool,
    "The canonical tool for instant redirection of the tree's active output.\nEven more useful when used together with VPAT.",
)
_tool_desc(VoronoiPreviewAnchorTool,
    "A forced separation from VPT, a kind of \"companion manager\" for VPT.\nExplicit socket specification and creation of reroute anchors.",
)
_tool_desc(VoronoiMixerTool,
    "The canonical tool for frequent mixing needs.\nMost likely 70% will go to using \"Instance on Points\".",
)
_tool_desc(VoronoiQuickMathTool,
    "A full-fledged branch from VMT. Quick and quick-quick math at speeds.\nHas additional mini-functionality. Also see \"Quick quick math\" in the layout.",
)
_tool_desc(VoronoiSwapperTool,
    "Tool for swapping links between two sockets, or adding them to one of them.\nNo link swap will occur if it ends up originating from its own node.",
)
_tool_desc(VoronoiHiderTool,
    "Tool for bringing order and aesthetics to the node tree.\nMost likely 90% will go to using automatic socket hiding.",
)
_tool_desc(VoronoiMassLinkerTool,
    "\"Puppy cat-dog\", neither nodes nor sockets. Created for rare point special accelerations.\nVLT on max. Due to its working principle, divine in its own way.",
)
_tool_desc(VoronoiEnumSelectorTool,
    "Tool for convenient lazy switching of enumeration properties.\nEliminates the need for mouse aiming, clicking, and then aiming and clicking again.",
)
_tool_desc(VoronoiLinkRepeatingTool,
    "A full-fledged branch from VLT, repeats any previous link from most\nother tools. Provides convenience for \"one to many\" connections.",
)
_tool_desc(VoronoiQuickDimensionsTool,
    "Tool for accelerating the needs of separating and combining vectors (and color).\nAnd can also split geometry into components.",
)
_tool_desc(VoronoiQuickConstant,
    "Tool for quickly adding constant value nodes.\nSupports various data types including vectors, colors, matrices and more.",
)
_tool_desc(VoronoiInterfacerTool,
    "A tool on the level of \"The Great Trio\". A branch from VLT for convenient acceleration\nof the creation process and special manipulations with interfaces. \"Interface Manager\".",
)
_tool_desc(VoronoiLinksTransferTool,
    "Tool for rare needs of transferring all links from one node to another.\nIn the future, it will most likely be merged with VST.",
)
_tool_desc(VoronoiWarperTool,
    "A mini-branch of topology reverse-engineering (like VPT).\nTool for \"point jumps\" along sockets.",
)
_tool_desc(VoronoiLazyNodeStencilsTool,
    "Power. Three letters for a tool, we've come to this... Encapsulates Ctrl-T from\nNodeWrangler, and the never-implemented 'VoronoiLazyNodeContinuationTool'.",
)
_tool_desc(VoronoiResetNodeTool,
    "Tool for resetting nodes without the need for aiming, with mouse guidance convenience\nand ignoring enumeration properties. Was created because NW had something similar.",
)

smart_add_to_reg_and_kmiDefs(VoronoiLinkerTool, "##A_RIGHTMOUSE")

smart_add_to_reg_and_kmiDefs(VoronoiPreviewTool, "SC#_LEFTMOUSE")

smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':1})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':2})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors':2})

smart_add_to_reg_and_kmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") # 混合器移到了左键, 为 VQMT 减轻负担.

smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_RIGHTMOUSE") # 留在了右键, 以免在'Speed Pie'类型的饼菜单下三击左键时抓狂.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_ACCENT_GRAVE", {'isRepeatLastOperation':True})
# 快速数学运算的快速操作列表("x2 组合"):
# "3"键上的布尔运算存在两难选择, 它可以是减法, 像这个键上的所有操作一样, 也可以是否定, 作为前两个的逻辑延续. 在第二种情况下, "4"键上的布尔运算很可能得留空.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_1", {'quickOprFloat':'ADD',      'quickOprVector':'ADD',      'quickOprBool':'OR',     'quickOprColor':'ADD'     })
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_2", {'quickOprFloat':'SUBTRACT', 'quickOprVector':'SUBTRACT', 'quickOprBool':'NIMPLY', 'quickOprColor':'SUBTRACT'})
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_3", {'quickOprFloat':'MULTIPLY', 'quickOprVector':'MULTIPLY', 'quickOprBool':'AND',    'quickOprColor':'MULTIPLY'})
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_4", {'quickOprFloat':'DIVIDE',   'quickOprVector':'DIVIDE',   'quickOprBool':'NOT',    'quickOprColor':'DIVIDE'  })
# 我本想为QuickMathMain实现这个功能, 但发现将技术操作符变成用户操作符太麻烦了. 主要问题是VqmtData的饼菜单设置.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_1", {'justPieCall':1}) # 出乎意料的是, 这样的热键用起来非常舒服.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_2", {'justPieCall':2}) # 因为有两个修饰键, 必须按住,
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_3", {'justPieCall':3}) # 所以必须通过光标位置来选择, 而不是点击.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_4", {'justPieCall':4}) # 我原以为会不方便, 结果感觉还不错.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_5", {'justPieCall':5}) # 整数饼菜单

# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "###_R")
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "S##_R", {'isAccumulate':True})
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#C#_R", {'isOnlySelected':2})
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True})

smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':SwapperMode.SWAP.value})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':SwapperMode.ADD.value})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S#A_S", {'toolMode':SwapperMode.TRAN.value})

smart_add_to_reg_and_kmiDefs(VoronoiCallNodePie, "#C#_LEFTMOUSE")

smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':HiderMode.HIDE_SOCKET.value})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "#CA_E", {'toolMode':HiderMode.HIDE_VALUE.value})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "SC#_E", {'toolMode':HiderMode.HIDE_NODE.value})

smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})

# 最初想用 'V_Sca', 但手指伸到 V 太远了. 而且, 考虑到创建这个工具的原因, 需要最小化调用的复杂性.
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_R", {'isPieChoice':False, 'isSelectNode':1})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_E", {'isInstantActivation':False})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "##A_E", {'isToggleOptions':True})

# 参见: VlrtData, VlrtRememberLastSockets() 和 remember_add_link().
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "###_V", {'toolMode':LinkRepeatingMode.SOCKET.value})
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'toolMode':LinkRepeatingMode.NODE.value})

smart_add_to_reg_and_kmiDefs(VoronoiQuickDimensionsTool, "##A_D")

smart_add_to_reg_and_kmiDefs(VoronoiQuickConstant, "##A_C")

smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "SC#_A", {'toolMode':InterfacerMode.NEW.value})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_A", {'toolMode':InterfacerMode.CREATE.value})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_C", {'toolMode':InterfacerMode.COPY.value})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_V", {'toolMode':InterfacerMode.PASTE.value})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_X", {'toolMode':InterfacerMode.SWAP.value})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Z", {'toolMode':InterfacerMode.FLIP.value})
# smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Q", {'toolMode':InterfacerMode.DELETE.value})
# smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_E", {'toolMode':InterfacerMode.TYPE.value})

smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "S##_T")
smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "SCA_T", {'isByIndexes':True})

smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "S#A_W")
smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "SCA_W", {'isZoomedTo':False})

smart_add_to_reg_and_kmiDefs(VoronoiLazyNodeStencilsTool, "S#A_Q")

smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})


dict_setKmiCats['最有用'].add(VoronoiLinkerTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiPreviewTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiMixerTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiQuickMathTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiHiderTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiCallNodePie.bl_idname)

dict_setKmiCats['很有用'].add(VoronoiMassLinkerTool.bl_idname)         # 批量连线
dict_setKmiCats['很有用'].add(VoronoiQuickConstant.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiInterfacerTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiQuickDimensionsTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiLinksTransferTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiEnumSelectorTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiSwapperTool.bl_idname)

dict_setKmiCats['可能有用'].add(VoronoiLinkRepeatingTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiResetNodeTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiLazyNodeStencilsTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiPreviewAnchorTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiWarperTool.bl_idname)

# dict_setKmiCats['无效'].add(VoronoiRantoTool.bl_idname)

# =======

SolderClsToolNames(dict_vtClasses)

# 更新语言调试枚举项并添加动态属性
UpdateLangDebEnumItems(dict_vtClasses)
AddDynamicProperties(dict_vtClasses)

_classes = [
    VmtOpMixer,
    VmtPieMixer,
    VqmtOpMain,
    VqmtPieMath,
    VestOpBox,
    VestPieBox,
    Rot_or_Mat_Convert,
    PIE_MT_Convert_To_Rotation,
    PIE_MT_Convert_Rotation_To,
    PIE_MT_Separate_Matrix,
    PIE_MT_Combine_Matrix,
    VoronoiOpAddonTabs,
    VoronoiAddonPrefs,
]
for i in _classes:
    dict_classes[i] = True

list_addonKeymaps = []
register_from_main = False

def register():
    bpy.app.translations.register(__package__, translations_dict)
    for dk in dict_classes:
        bpy.utils.register_class(dk)

    prefs = Prefs()
    if register_from_main:
        if hasattr(bpy.types.SpaceNodeEditor, 'handle'):
            bpy.types.SpaceNodeEditor.nsReg = perf_counter_ns()
    else:
        prefs.vlnstLastExecError = ""
        prefs.vaLangDebDiscl = False
        for cls in dict_vtClasses:
            setattr(prefs, cls.disclBoxPropNameInfo, False)
        prefs.dsIsTestDrawing = False

    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blid, key, shift, ctrl, alt, repeat, dict_props in list_kmiDefs:
        kmi = km.keymap_items.new(idname=blid, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        kmi.active = blid != 'node.voronoi_dummy'
        if dict_props:
            for dk, dv in dict_props.items():
                setattr(kmi.properties, dk, dv)
        list_addonKeymaps.append(kmi)

    RegisterSolderings()

def unregister():
    UnregisterSolderings()

    km = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for li in list_addonKeymaps:
        km.keymap_items.remove(li)
    list_addonKeymaps.clear()

    for dk in dict_classes:
        bpy.utils.unregister_class(dk)
    bpy.app.translations.unregister(__package__)

def DisableKmis():  # 用于重复运行脚本. 在第一次"恢复"之前有效.
    from .common_forward_func import user_node_keymaps
    node_kms = user_node_keymaps()
    for li, *oi in list_kmiDefs:
        for kmiCon in node_kms.keymap_items:
            if li == kmiCon.idname:
                kmiCon.active = False  # 这会删除重复项. 是个 hack 吗?
                kmiCon.active = True  # 如果是原始的, 就恢复.

if __name__ == "__main__":
    DisableKmis()  # 似乎在添加热键之前或之后调用都无所谓.
    register_from_main = True
    register()
