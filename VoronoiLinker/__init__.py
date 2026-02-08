bl_info2 = {'name': "Voronoi Linker", 
           'author': "ugorek",       # 同样感谢"Oxicid"为VL提供的关键帮助.
           'version': (5,1,2), 
           'blender': (4,0,2), 
           'created': "2024.03.06",           # 'created'键用于内部需求.
           'info_supported_blvers': "b4.0.2 – b4.0.2", # 这也是内部使用的.
           'description': "Various utilities for nodes connecting, based on distance field.", 'location':"Node Editor",  # 以前为了纪念这个插件的初衷, 这里写的是 'Node Editor > Alt + RMB'; 但现在 VL 已经"无处不在"了! 🚀
           'warning': "",  # 希望永远不要有需要在这里添加警告的那一天. 之前在Linux上无法使用的问题已经非常接近这个地步了. 😬
           'category': "Node",
           'wiki_url': "https://github.com/neliut/VoronoiLinker/wiki",  # bl_info 因为4.2吗? 相同的键会被 blender_manifest 覆盖,不同的删除
           'tracker_url': "https://github.com/neliut/VoronoiLinker/issues"}

import bpy, rna_keymap_ui, bl_keymap_utils
from bpy.app.translations import pgettext_iface as _iface
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, StringProperty)
from bpy.types import UILayout, KeyMapItem, Operator
from time import perf_counter_ns
from typing import Callable

from .common_forward_class import VlnstUpdateLastExecError
from .common_forward_func import GetFirstUpperLetters, user_node_keymaps, format_tool_set, Prefs
from .globals import dict_vlHhTranslations, dict_vmtMixerNodesDefs, dict_vqmtQuickMathMain
from .tools.call_node_pie import VoronoiCallNodePie
from .tools.dummy import VoronoiDummyTool
from .tools.enum_selector import VoronoiEnumSelectorTool, VestOpBox, VestPieBox, SNA_OT_Change_Node_Domain_And_Name
from .tools.hider import VoronoiHiderTool
from .tools.interfacer import VoronoiInterfacerTool
from .tools.lazy_node_stencils import VoronoiLazyNodeStencilsTool
from .tools.link_repeating import VoronoiLinkRepeatingTool
from .tools.linker import VoronoiLinkerTool
from .tools.links_transfer import VoronoiLinksTransferTool
from .tools.mass_linker import VoronoiMassLinkerTool
from .tools.matrix_convert import Rot_or_Mat_Convert, PIE_MT_Convert_To_Rotation, PIE_MT_Convert_Rotation_To, PIE_MT_Separate_Matrix, PIE_MT_Combine_Matrix
from .tools.mixer import VoronoiMixerTool
from .tools.mixer_sub import VmtOpMixer, VmtPieMixer
from .tools.pie_math import VqmtOpMain, VqmtPieMath
from .tools.preview import VoronoiPreviewTool
from .tools.preview_anchor import VoronoiPreviewAnchorTool
from .tools.quick_constant import VoronoiQuickConstant
from .tools.quick_dimensions import VoronoiQuickDimensionsTool
from .tools.quick_math import VoronoiQuickMathTool
from .tools.reset_node import VoronoiResetNodeTool
from .tools.swapper import VoronoiSwapperTool
from .tools.warper import VoronoiWarperTool
from .utils.drawing import TestDraw
from .utils.solder import SolderClsToolNames, RegisterSolderings, UnregisterSolderings
from .utils.ui import LyAddDisclosureProp, LyAddLabeledBoxCol, LyAddHandSplitProp, LyAddThinSep, LyAddQuickInactiveCol, LyAddEtb
from .translations import translations_dict

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

dict_classes = {} # 所有需要注册的类都放在这里. 使用字典是为了 smart_add_to_reg_and_kmiDefs() 函数, 同时还能保持顺序.
dict_vtClasses = {} # 只存放 V*T (Voronoi Tool) 工具.

list_kmiDefs = []
dict_setKmiCats = {'最有用':set(), '很有用':set(), '可能有用':set(), '无效':set(), 'qqm':set(), 'custom':set()}

def smart_add_to_reg_and_kmiDefs(cls: Operator, txt: str, dict_props={}):
    dict_numToKey = {"1":'ONE', "2":'TWO', "3":'THREE', "4":'FOUR', "5":'FIVE', "6":'SIX', "7":'SEVEN', "8":'EIGHT', "9":'NINE', "0":'ZERO'}
    dict_classes[cls] = True
    dict_vtClasses[cls] = True
    list_kmiDefs.append( (cls.bl_idname, dict_numToKey.get(txt[4:], txt[4:]), txt[0]=="S", txt[1]=="C", txt[2]=="A", txt[3]=="+", dict_props) )

#Todo0VV: 处理 n^3 种组合: space_data.tree_type 和 space_data.edit_tree.bl_idname; 包括经典的, 丢失的和插件的; 绑定和未绑定到编辑器的.
# ^ 然后检查所有工具在这些组合中的可用性. 之后在现有节点树中检查所有工具与丢失节点的丢失插槽的交互情况.

dict_timeAvg = {}
dict_timeOutside = {}
#    with ToTimeNs("aaa"):
class ToTimeNs(): # 我投降了. 🤷‍ 我不知道为什么在大型节点树上会这么卡. 但从测量结果来看, 卡顿的地方在 VL 插件之外.
    def __init__(self, name):
        self.name = name
        tpcn = perf_counter_ns()
        dict_timeOutside[name] = tpcn-dict_timeOutside.setdefault(name, 0)
        dict_timeAvg.setdefault(name, [0, 0])
        self.tmn = tpcn
    def __enter__(self):
        pass
    def __exit__(self, *_):
        tpcn = perf_counter_ns()
        nsExec = tpcn-self.tmn
        list_avg = dict_timeAvg[self.name]
        list_avg[0] += 1
        list_avg[1] += nsExec
        txt1 = "{:,}".format(nsExec).rjust(13)
        txt2 = "{:,}".format(dict_timeOutside[self.name]).rjust(13)
        txt3 = "{:,}".format(int(list_avg[1]/list_avg[0]))
        txt = " ".join(("", self.name, txt1, "~~~", txt2, "===", txt3))
        dict_timeOutside[self.name] = tpcn

# todo1v6: 当工具处于活动状态时, 按下 PrtScr 会在控制台刷屏 `WARN ... pyrna_enum_to_py: ... '171' matches no enum in 'Event'`.

txtAddonVer = ".".join([str(v) for v in bl_info2['version']])
txt_addonVerDateCreated = f"Version {txtAddonVer} created {bl_info2['created']}"
txt_addonBlVerSupporting = f"For Blender versions: {bl_info2['info_supported_blvers']}"
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

dict_toolLangSpecifDataPool = {}

smart_add_to_reg_and_kmiDefs(VoronoiLinkerTool, "##A_RIGHTMOUSE") # "##A_RIGHTMOUSE"?
dict_toolLangSpecifDataPool[VoronoiLinkerTool, "ru_RU"] = "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника."

smart_add_to_reg_and_kmiDefs(VoronoiPreviewTool, "SC#_LEFTMOUSE")
dict_toolLangSpecifDataPool[VoronoiPreviewTool, "ru_RU"] = "Канонический инструмент для мгновенного перенаправления явного вывода дерева.\nЕщё более полезен при использовании совместно с VPAT."

smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':1})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':2})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors':2})
dict_toolLangSpecifDataPool[VoronoiPreviewAnchorTool, "ru_RU"] = "Вынужденное отделение от VPT, своеобразный \"менеджер-компаньон\" для VPT.\nЯвное указание сокета и создание рероут-якорей."

smart_add_to_reg_and_kmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") # 混合器移到了左键, 为 VQMT 减轻负担.
dict_toolLangSpecifDataPool[VoronoiMixerTool, "ru_RU"] = "Канонический инструмент для частых нужд смешивания.\nСкорее всего 70% уйдёт на использование \"Instance on Points\"."

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
dict_toolLangSpecifDataPool[VoronoiQuickMathTool, "ru_RU"] = """Полноценное ответвление от VMT. Быстрая и быстрая быстрая математика на спидах.
Имеет дополнительный мини-функционал. Также см. \"Quick quick math\" в раскладе."""

# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "###_R")
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "S##_R", {'isAccumulate':True})
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#C#_R", {'isOnlySelected':2})
# smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':'ADD'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S#A_S", {'toolMode':'TRAN'})

dict_toolLangSpecifDataPool[VoronoiSwapperTool, "ru_RU"] = """Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.
Для линка обмена не будет, если в итоге он окажется исходящим из своего же нода."""
dict_toolLangSpecifDataPool[VoronoiSwapperTool, "zh_HANS"] = "Alt是批量替换输出接口,Shift是互换接口"

smart_add_to_reg_and_kmiDefs(VoronoiCallNodePie, "#C#_LEFTMOUSE")

smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "#CA_E", {'toolMode':'SOCKETVAL'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "SC#_E", {'toolMode':'NODE'})
dict_toolLangSpecifDataPool[VoronoiHiderTool, "ru_RU"] = "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов."
dict_toolLangSpecifDataPool[VoronoiHiderTool, "zh_HANS"] = "Shift是自动隐藏数值为0/颜色纯黑/未连接的接口,Ctrl是单个隐藏接口"


smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})
dict_toolLangSpecifDataPool[VoronoiMassLinkerTool, "ru_RU"] = """"Малыш котопёс", не ноды, не сокеты. Создан ради редких точечных спец-ускорений.
VLT на максималках. В связи со своим принципом работы, по своему божественен."""

# 最初想用 'V_Sca', 但手指伸到 V 太远了. 而且, 考虑到创建这个工具的原因, 需要最小化调用的复杂性.
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_R", {'isPieChoice':False, 'isSelectNode':1})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_E", {'isInstantActivation':False})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "##A_E", {'isToggleOptions':True})
dict_toolLangSpecifDataPool[VoronoiEnumSelectorTool, "ru_RU"] = """Инструмент для удобно-ленивого переключения свойств перечисления.
Избавляет от прицеливания мышкой, клика, а потом ещё одного прицеливания и клика."""

# 参见: VlrtData, VlrtRememberLastSockets() 和 remember_add_link().
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "###_V", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'toolMode':'NODE'})
dict_toolLangSpecifDataPool[VoronoiLinkRepeatingTool, "ru_RU"] = """Полноценное ответвление от VLT, повторяет любой предыдущий линк от большинства
других инструментов. Обеспечивает удобство соединения "один ко многим"."""


smart_add_to_reg_and_kmiDefs(VoronoiQuickDimensionsTool, "##A_D")
dict_toolLangSpecifDataPool[VoronoiQuickDimensionsTool, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."

smart_add_to_reg_and_kmiDefs(VoronoiQuickConstant, "##A_C")
dict_toolLangSpecifDataPool[VoronoiQuickConstant, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."

smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "SC#_A", {'toolMode':'NEW'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_A", {'toolMode':'CREATE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_C", {'toolMode':'COPY'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_V", {'toolMode':'PASTE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_X", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Z", {'toolMode':'FLIP'})
# smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Q", {'toolMode':'DELETE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_E", {'toolMode':'SOC_TY'})
dict_toolLangSpecifDataPool[VoronoiInterfacerTool, "ru_RU"] = """Инструмент на уровне "The Great Trio". Ответвление от VLT ради удобного ускорения
процесса создания и спец-манипуляций с интерфейсами. "Менеджер интерфейсов"."""

smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "SCA_T")
smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "S##_T", {'isByIndexes':True})
dict_toolLangSpecifDataPool[VoronoiLinksTransferTool, "ru_RU"] = "Инструмент для редких нужд переноса всех линков с одного нода на другой.\nВ будущем скорее всего будет слито с VST."

smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "S#A_W")
smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "SCA_W", {'isZoomedTo':False})
dict_toolLangSpecifDataPool[VoronoiWarperTool, "ru_RU"] = "Мини-ответвление реверс-инженеринга топологии, (как у VPT).\nИнструмент для \"точечных прыжков\" по сокетам."

smart_add_to_reg_and_kmiDefs(VoronoiLazyNodeStencilsTool, "S#A_Q")
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "ru_RU"] = """Мощь. Три буквы на инструмент, дожили... Инкапсулирует Ctrl-T от
NodeWrangler'а, и никогда не реализованный 'VoronoiLazyNodeContinuationTool'. """ #"Больше лени богу лени!"
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "zh_HANS"] = "代替NodeWrangler的ctrl+t"

smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})
dict_toolLangSpecifDataPool[VoronoiResetNodeTool, "ru_RU"] = """Инструмент для сброса нодов без нужды прицеливания, с удобствами ведения мышкой
и игнорированием свойств перечислений. Был создан, потому что в NW было похожее."""

#smart_add_to_reg_and_kmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})

dict_setKmiCats['最有用'].add(VoronoiLinkerTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiPreviewTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiMixerTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiQuickMathTool.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiCallNodePie.bl_idname)
dict_setKmiCats['最有用'].add(VoronoiHiderTool.bl_idname)

dict_setKmiCats['很有用'].add(VoronoiMassLinkerTool.bl_idname)         # 批量连线
dict_setKmiCats['很有用'].add(VoronoiQuickConstant.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiInterfacerTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiQuickDimensionsTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiLinksTransferTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiEnumSelectorTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiSwapperTool.bl_idname)
dict_setKmiCats['很有用'].add(VoronoiResetNodeTool.bl_idname)

dict_setKmiCats['可能有用'].add(VoronoiLinkRepeatingTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiLazyNodeStencilsTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiPreviewAnchorTool.bl_idname)
dict_setKmiCats['可能有用'].add(VoronoiWarperTool.bl_idname)

# dict_setKmiCats['无效'].add(VoronoiRantoTool.bl_idname)

dict_toolLangSpecifDataPool[VoronoiDummyTool, "ru_RU"] = """"Ой дурачёк"."""

# =======

def GetVlKeyconfigAsPy(): # 从 'bl_keymap_utils.io' 借来的. 我完全不知道它是如何工作的.
    def Ind(num: int):
        return " "*num
    def keyconfig_merge(kc1: bpy.types.KeyConfig, kc2: bpy.types.KeyConfig):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1!=kc2:
            merged_keymaps.extend(
                (km, kc2)
                for km in kc2.keymaps
                if km.name not in kc1_names)
        return merged_keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.active
    class FakeKeyConfig:
        keymaps = []
    edited_kc = FakeKeyConfig()
    edited_kc.keymaps.append(user_node_keymaps())
    if kc!=wm.keyconfigs.default:
        export_keymaps = keyconfig_merge(edited_kc, kc)
    else:
        export_keymaps = keyconfig_merge(edited_kc, edited_kc)
    ##
    result = ""
    result += "list_keyconfigData = \\\n["
    sco = 0
    for km, _kc_x in export_keymaps:
        km = km.active()
        result += "("
        result += f"\"{km.name:s}\","+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"space_type\": '{km.space_type:s}'"
        result += f", \"region_type\": '{km.region_type:s}'"
        isModal = km.is_modal
        if isModal:
            result += ", \"modal\": True"
        result += "},"+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"items\":"+"\n"
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
                result += ", None),"+"\n"
            else:
                result += ","+"\n"
                result += f"{Ind(5)}" "{"
                result += kmi_data
                result += f"{Ind(6)}"
                result += "},\n" f"{Ind(5)}"
                result += "),"+"\n"
            result += f"{Ind(4)}"
        result += "],\n" f"{Ind(3)}"
        result += "},\n" f"{Ind(2)}"
        result += "),\n" f"{Ind(1)}"
    result += "]"+" #kmi count: "+str(sco)+"\n"
    result += "\n"
    result += "if True:"+"\n"
    result += "    import bl_keymap_utils"+"\n"
    result += "    import bl_keymap_utils.versioning"+"\n" # 黑魔法; 似乎和 "gpu_extras" 一样.
    result += "    kc = bpy.context.window_manager.keyconfigs.active"+"\n"
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})"+"\n"
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result
def GetVaSettAsPy(prefs: bpy.types.AddonPreferences):
    set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'dsIsFieldDebug', 'dsIsTestDrawing', # tovo2v6: 是全部吗?
                             'vaKmiMainstreamDiscl', 'vaKmiOtjersDiscl', 'vaKmiSpecialDiscl', 'vaKmiInvalidDiscl', 
                             'vaKmiQqmDiscl', 'vaKmiCustomDiscl'}
    for cls in dict_vtClasses:
        set_ignoredAddonPrefs.add(cls.disclBoxPropName)
        set_ignoredAddonPrefs.add(cls.disclBoxPropNameInfo)
    txt_vasp = ""
    txt_vasp += "#Exported/Importing addon settings for Voronoi Linker v"+txtAddonVer+"\n"
    import datetime
    txt_vasp += f"#Generated "+datetime.datetime.now().strftime("%Y.%m.%d")+"\n"
    txt_vasp += "\n"
    txt_vasp += "import bpy\n"
    # 构建已更改的插件设置:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{__package__}'].preferences"+"\n\n"
    txt_vasp += "def SetProp(att, val):"+"\n"
    txt_vasp += "    if hasattr(prefs, att):"+"\n"
    txt_vasp += " setattr(prefs, att, val)"+"\n\n"
    def AddAndProc(txt: str):
        nonlocal txt_vasp
        len = txt.find(",")
        txt_vasp += txt.replace(", ",","+" "*(42-len), 1)
    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            # '_BoxDiscl' 我没忽略, 留着吧.
            if pr.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(pr,'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(pr.default_array, getattr(prefs, pr.identifier)) if li[0]!=li[1]]
                else:
                    isDiff = pr.default!=getattr(prefs, pr.identifier)
                if (True)or(isDiff): # 只保存差异可能不安全, 以防未保存的属性的默认值发生变化.
                    if isArray:
                        #txt_vasp += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                        list_vals = [str(li)+"," for li in getattr(prefs, pr.identifier)]
                        list_vals[-1] = list_vals[-1][:-1]
                        AddAndProc(f"SetProp('{pr.identifier}', ("+" ".join(list_vals)+"))\n")
                    else:
                        match pr.type:
                            case 'STRING': AddAndProc(f"SetProp('{pr.identifier}', \"{getattr(prefs, pr.identifier)}\")"+"\n")
                            case 'ENUM':   AddAndProc(f"SetProp('{pr.identifier}', '{getattr(prefs, pr.identifier)}')"+"\n")
                            case _:        AddAndProc(f"SetProp('{pr.identifier}', {getattr(prefs, pr.identifier)})"+"\n")
    # 构建所有 VL 热键:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    # P.s. 我不知道如何只处理已更改的热键; 这看起来太头疼了, 像是一片茂密的森林. # tovo0v6
    # 懒得逆向工程 '..\scripts\modules\bl_keymap_utils\io.py', 所以就保存全部吧.
    txt_vasp += GetVlKeyconfigAsPy() # 它根本不起作用; 恢复的那部分; 生成的脚本什么也没保存, 只有临时效果.
    # 不得不等待那个英雄来修复这一切.
    return txt_vasp

SolderClsToolNames(dict_vtClasses)

list_langDebEnumItems = []
for li in ["Free", "Special", "AddonPrefs"] + [cls.bl_label for cls in dict_vtClasses]:
    list_langDebEnumItems.append( (li.upper(), GetFirstUpperLetters(li), "") )

fitVltPiDescr = "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"
list_itemsProcBoolSocket = [('ALWAYS',"Always","Always"), ('IF_FALSE',"If false","If false"), ('NEVER',"Never","Never"), ('IF_TRUE',"If true","If true")]

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
fitTabItems = ( ('SETTINGS',"Settings",""), ('APPEARANCE',"Appearance",""), ('DRAW',"Draw",""), ('KEYMAP',"Keymap",""), ('INFO',"Info","") )#, ('DEV',"Dev","")

class VoronoiOpAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    bl_description = "VL's addon tab" # todo1v6: 想办法为每个标签页翻译不同的内容.
    opt  : StringProperty()
    def invoke(self, context, event):
        #if not self.opt: return {'CANCELLED'}
        prefs = Prefs()
        match self.opt:
            case 'GetPySett':
                context.window_manager.clipboard = GetVaSettAsPy(prefs)
            case 'AddNewKmi':
                user_node_keymaps().keymap_items.new("node.voronoi_",'D','PRESS').show_expanded = True
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__ # type: ignore
    # --- VoronoiLinkerTool
    vltRepickKey            : StringProperty(name="Repick Key", default='LEFT_ALT')
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
    vqmtRepickKey            : StringProperty(name="Repick Key", default='LEFT_ALT')
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
    vhtHideBoolSocket        : EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=list_itemsProcBoolSocket)
    vhtHideHiddenBoolSocket  : EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=list_itemsProcBoolSocket)
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
    vwtSelectTargetKey       : StringProperty(name="Select target Key", default='LEFT_ALT')
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
    vaUiTabs             : EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=fitTabItems)
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
    dsFontFile     : StringProperty(name="Font file",    default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH') # "Linux 用户表示不满".
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
        def LyAddAddonBoxDiscl(where: UILayout, who, att, *, txt=None, isWide=False, align=False):
            colBox = where.box().column(align=True)
            if LyAddDisclosureProp(colBox, who, att, txt=txt, active=True, isWide=isWide):
                rowTool = colBox.row()
                rowTool.separator()
                return rowTool.column(align=align)
            return None
        colMain = where.column()
        LyAddThinSep(colMain, 0.1)
        for cls in dict_vtClasses:
            if cls.canDrawInAddonDiscl:
                if colDiscl:=LyAddAddonBoxDiscl(colMain, self, cls.disclBoxPropName, txt=format_tool_set(cls), align=True):
                    cls.LyDrawInAddonDiscl(colDiscl, self)
    def LyDrawTabAppearance(self, where: UILayout):
        colMain = where.column()
        #LyAddHandSplitProp(LyAddLabeledBoxCol(colMain, text="Main"), self,'vSearchMethod')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'vEdgePanFac', text="Zoom factor")
        LyAddHandSplitProp(colBox, self,'vEdgePanSpeed', text="Speed")
        if (self.dsIncludeDev)or(self.vIsOverwriteZoomLimits):
            LyAddHandSplitProp(colBox, self,'vIsOverwriteZoomLimits', active=self.vIsOverwriteZoomLimits)
            if self.vIsOverwriteZoomLimits:
                LyAddHandSplitProp(colBox, self,'vOwZoomMin')
                LyAddHandSplitProp(colBox, self,'vOwZoomMax')
        ##
        for cls in dict_vtClasses:
            if cls.canDrawInAppearance:
                cls.LyDrawInAppearance(colMain, self)
    def LyDrawTabDraw(self, where: UILayout):
        def LyAddPairProp(where: UILayout, txt):
            row = where.row(align=True)
            row.prop(self, txt)
            row.active = getattr(self, txt.replace("Colored","Draw"))
        colMain = where.column()
        splDrawColor = colMain.box().split(align=True)
        splDrawColor.use_property_split = True
        colDraw = splDrawColor.column(align=True, heading='Draw')
        colDraw.prop(self,'dsIsDrawText')
        colDraw.prop(self,'dsIsDrawMarker')
        colDraw.prop(self,'dsIsDrawPoint')
        colDraw.prop(self,'dsIsDrawLine')
        colDraw.prop(self,'dsIsDrawSkArea')
        with LyAddQuickInactiveCol(colDraw, active=self.dsIsDrawText) as row:
            row.prop(self,'dsIsDrawNodeNameLabel', text="Node text") # "Text for node"
        colCol = splDrawColor.column(align=True, heading='Colored')
        LyAddPairProp(colCol,'dsIsColoredText')
        LyAddPairProp(colCol,'dsIsColoredMarker')
        LyAddPairProp(colCol,'dsIsColoredPoint')
        LyAddPairProp(colCol,'dsIsColoredLine')
        LyAddPairProp(colCol,'dsIsColoredSkArea')
        tgl = (self.dsIsDrawLine)or(self.dsIsDrawPoint)or(self.dsIsDrawText and self.dsIsDrawNodeNameLabel)
        with LyAddQuickInactiveCol(colCol, active=tgl) as row:
            row.prop(self,'dsIsColoredNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        #LyAddHandSplitProp(colBox, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
        LyAddHandSplitProp(colBox, self,'dsIsAlwaysLine')
        LyAddHandSplitProp(colBox, self,'dsIsSlideOnNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'dsSocketAreaAlpha', active=self.dsIsDrawSkArea)
        tgl = ( (self.dsIsDrawText   and not self.dsIsColoredText  )or
                (self.dsIsDrawMarker and not self.dsIsColoredMarker)or
                (self.dsIsDrawPoint  and not self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and not self.dsIsColoredLine  )or
                (self.dsIsDrawSkArea and not self.dsIsColoredSkArea) )
        LyAddHandSplitProp(colBox, self,'dsUniformColor', active=tgl)    # 小王 原先这样 不确定什么用
        # LyAddHandSplitProp(colBox, self,'dsUniformColor', active=True)
        tgl = ( (self.dsIsDrawText   and self.dsIsColoredText  )or
                (self.dsIsDrawPoint  and self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and self.dsIsColoredLine  ) )
        LyAddHandSplitProp(colBox, self,'dsUniformNodeColor', active=(tgl)and(not self.dsIsColoredNodes))    # 原先这样 不确定什么用
        # LyAddHandSplitProp(colBox, self,'dsUniformNodeColor', active=True)
        tgl1 = (self.dsIsDrawPoint and self.dsIsColoredPoint)
        tgl2 = (self.dsIsDrawLine  and self.dsIsColoredLine)and(not not self.dsCursorColorAvailability)
        LyAddHandSplitProp(colBox, self,'dsCursorColor', active=tgl1 or tgl2)
        LyAddHandSplitProp(colBox, self,'dsCursorColorAvailability', active=self.dsIsDrawLine and self.dsIsColoredLine)
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'dsDisplayStyle')
        LyAddHandSplitProp(colBox, self,'dsFontFile')
        if not self.dsFontFile.endswith((".ttf",".otf")):
            spl = colBox.split(factor=0.4, align=True)
            spl.label(text="")
            spl.label(text=txt_onlyFontFormat, icon='ERROR')
        LyAddThinSep(colBox, 0.5)
        LyAddHandSplitProp(colBox, self,'dsLineWidth')
        LyAddHandSplitProp(colBox, self,'dsPointScale')
        LyAddHandSplitProp(colBox, self,'dsFontSize')
        LyAddHandSplitProp(colBox, self,'dsMarkerStyle')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'dsManualAdjustment')
        LyAddHandSplitProp(colBox, self,'dsPointOffsetX')
        LyAddHandSplitProp(colBox, self,'dsFrameOffset')
        LyAddHandSplitProp(colBox, self,'dsDistFromCursor')
        LyAddThinSep(colBox, 0.25) # 间隔的空白会累加, 所以额外加个间隔来对齐.
        LyAddHandSplitProp(colBox, self,'dsIsAllowTextShadow')
        colShadow = colBox.column(align=True)
        LyAddHandSplitProp(colShadow, self,'dsShadowCol', active=self.dsIsAllowTextShadow)
        LyAddHandSplitProp(colShadow, self,'dsShadowBlur') # 阴影模糊将它们分开, 以免在中间融合在一起.
        row = LyAddHandSplitProp(colShadow, self,'dsShadowOffset', returnAsLy=True).row(align=True)
        row.row().prop(self,'dsShadowOffset', text="X  ", translate=False, index=0, icon_only=True)
        row.row().prop(self,'dsShadowOffset', text="Y  ", translate=False, index=1, icon_only=True)
        colShadow.active = self.dsIsAllowTextShadow
        ##
        colDev = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.dsIsFieldDebug)or(self.dsIsTestDrawing):
            with LyAddQuickInactiveCol(colDev, active=self.dsIsFieldDebug) as row:
                row.prop(self,'dsIsFieldDebug')
            with LyAddQuickInactiveCol(colDev, active=self.dsIsTestDrawing) as row:
                row.prop(self,'dsIsTestDrawing')
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
        node_kms = user_node_keymaps()
        ##
        kmiCats = KeymapItemCategoryContainer()
        kmiCats.qqm = KeymapItemCategory('vaKmiQqmDiscl', set(), dict_setKmiCats["qqm"])
        kmiCats.custom = KeymapItemCategory('vaKmiCustomDiscl', set())
        kmiCats.useful_1 = KeymapItemCategory('vaKmiMainstreamDiscl', set(), dict_setKmiCats["最有用"])
        kmiCats.useful_2 = KeymapItemCategory('vaKmiOtjersDiscl', set(), dict_setKmiCats["很有用"])
        kmiCats.useful_3 = KeymapItemCategory('vaKmiSpecialDiscl', set(), dict_setKmiCats["可能有用"])
        kmiCats.useful_4 = KeymapItemCategory('vaKmiInvalidDiscl', set(), dict_setKmiCats["无效"])
        kmiCats.useful_1.filter_func = lambda kmi: kmi.idname in kmiCats.useful_1.item_idnames
        kmiCats.useful_2.filter_func = lambda kmi: kmi.idname in kmiCats.useful_2.item_idnames
        kmiCats.useful_3.filter_func = lambda kmi: kmi.idname in kmiCats.useful_3.item_idnames
        kmiCats.useful_4.filter_func = lambda kmi: True
        kmiCats.qqm.filter_func = lambda kmi: any(True for txt in {'quickOprFloat', 'quickOprVector', 'quickOprBool', 'quickOprColor', 'justPieCall', 'isRepeatLastOperation'} if getattr(kmi.properties, txt, None))
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
            with LyAddQuickInactiveCol(rowRestore, align=False, active=True) as row:
                row.prop(self,'vaInfoRestore', text="", icon='INFO')
            rowRestore.context_pointer_set('keymap', node_kms)
            rowRestore.operator('preferences.keymap_restore', text="Restore", icon="ERROR")
        else:
            rowLabelMain.label()
        rowAddNew = rowLabelMain.row(align=True)
        rowAddNew.ui_units_x = 12
        rowAddNew.separator()
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='ADD').opt = 'AddNewKmi' # NONE  ADD
        def LyAddKmisCategory(where: UILayout, cat):
            if not cat.matched_items:
                return
            colListCat = where.row().column(align=True)
            txt = self.bl_rna.properties[cat.prop_name].name
            if not LyAddDisclosureProp(colListCat, self, cat.prop_name, txt=_iface(txt)+f" ({cat.count})", isWide=1-1):
                return
            # for li in cat.matched_items:
            for li in sorted(cat.matched_items, key=lambda a:a.id):
                colListCat.context_pointer_set('keymap', node_kms)
                rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, node_kms, li, colListCat, 0) # 注意: 如果 colListCat 不是 colListCat, 那么删除 kmi 的功能将不可用.
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
                txtHl = "#:~:text="+txtHl
            row.operator('wm.url_open', text=text, icon='URL').url=url+txtHl
            row.label()
        colMain = where.column()
        with LyAddQuickInactiveCol(colMain, att='column') as row:
            row.alignment = 'LEFT'
            row.label(text=txt_addonVerDateCreated)
            row.label(text=txt_addonBlVerSupporting)
        colUrls = colMain.column()
        LyAddUrlHl(colUrls, "Check for updates yourself", "https://github.com/ugorek000/VoronoiLinker", txtHl="Latest%20version")
        LyAddUrlHl(colUrls, "VL Wiki", bl_info2['wiki_url'])
        LyAddUrlHl(colUrls, "RANTO Git", "https://github.com/ugorek000/RANTO")
        colUrls.separator()
        LyAddUrlHl(colUrls, "Event Type Items", "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html")
        LyAddUrlHl(colUrls, "Translator guide", "https://developer.blender.org/docs/handbook/translating/translator_guide/")
        LyAddUrlHl(colUrls, "Translator dev guide", "https://developer.blender.org/docs/handbook/translating/developer_guide/")
        ##
        colMain.separator()
        row = colMain.row(align=True)
        row.alignment = 'LEFT'
        row.operator(VoronoiOpAddonTabs.bl_idname, text=txt_copySettAsPyScript, icon='COPYDOWN').opt = 'GetPySett' # SCRIPT  COPYDOWN
        with LyAddQuickInactiveCol(colMain, active=self.dsIncludeDev) as row:
            row.prop(self,'dsIncludeDev')
        ##
        LyAddThinSep(colMain, 0.15)
        rowSettings = colMain.box().row(align=True)
        row = rowSettings.row(align=True)
        row.ui_units_x = 20
        view = bpy.context.preferences.view
        row.prop(view,'language', text="")
        row = rowSettings.row(align=True)
        langCode = view.language
        row.label(text=f"   '{langCode}'   ", translate=False)
        #row = rowSettings.row(align=True)
        #row.alignment = 'RIGHT'
        row.prop(view,'use_translate_interface', text="Interface")
        row.prop(view,'use_translate_tooltips', text="Tooltips")
        ##
        colVlTools = colMain.column(align=True)
        for cls in dict_vtClasses:
            if txtToolInfo:=dict_toolLangSpecifDataPool.get((cls, langCode), ""):
                colDiscl = colVlTools.column(align=True)
                rowLabel = colDiscl.row(align=True)
                if LyAddDisclosureProp(rowLabel, self, cls.disclBoxPropNameInfo, txt=cls.bl_label+" Tool"):
                    rowTool = colDiscl.row(align=True)
                    rowTool.label(icon='BLANK1')
                    rowTool.label(icon='BLANK1')
                    text_color = rowTool.column(align=True)
                    for li in txtToolInfo.split("\n"):
                        text_color.label(text=li, translate=False)
                with LyAddQuickInactiveCol(rowLabel, att='row') as row:
                    row.alignment = 'LEFT'
                    row.label(text=f"({cls.vlTripleName})", translate=False)
                    row.alignment = 'EXPAND'
                    #row.prop(self, cls.disclBoxPropNameInfo, text=" ", translate=False, emboss=False)
        ##
        colLangDebug = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.vaLangDebDiscl):
            with LyAddQuickInactiveCol(colLangDebug, active=self.vaLangDebDiscl) as row:
                row.prop(self,'vaLangDebDiscl')
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
            colLangDebug.row().prop(self,'vaLangDebEnum', expand=True)
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
                    row.label(text=label+": ", translate=False)
                row = rowRoot.row(align=True)
                col = row.column(align=True)
                text = _iface(text)
                if text:
                    list_split = text.split("\n")
                    hig = len(list_split)-1
                    for cyc, li in enumerate(list_split):
                        col.label(text=li+(dot if cyc==hig else ""), translate=False)
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
                if type(pr)==bpy.types.EnumProperty:
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
                    col.label(text=bl_info2['description'])
                    col.label(text=txt_addonVerDateCreated)
                    col.label(text=txt_addonBlVerSupporting)
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
                    col = LyAddAlertNested(colLangDebug, "[AddonPrefs]")
                    set_toolBoxDisctPropNames = set([cls.disclBoxPropName for cls in dict_vtClasses])|set([cls.disclBoxPropNameInfo for cls in dict_vtClasses])
                    set_toolBoxDisctPropNames.update({'vaLangDebEnum'})
                    for pr in self.bl_rna.properties[2:]:
                        if pr.identifier not in set_toolBoxDisctPropNames:
                            LyAddTranDataForProp(col, pr)
                case _:
                    dict_toolBlabToCls = {cls.bl_label.upper():cls for cls in dict_vtClasses}
                    set_alreadyDone = set() # 考虑到 vaLangDebEnum 的分离, 这已经没用了.
                    col0 = colLangDebug.column(align=True)
                    cls = dict_toolBlabToCls[self.vaLangDebEnum]
                    col1 = LyAddAlertNested(col0, cls.bl_label)
                    rna = eval(f"bpy.ops.{cls.bl_idname}.get_rna_type()") # 通过 getattr 不知道为什么 `getattr(bpy.ops, cls.bl_idname).get_rna_type()` 不起作用.
                    for pr in rna.properties[1:]: # 跳过 rna_type.
                        rowLabel = col1.row(align=True)
                        if pr.identifier not in set_alreadyDone:
                            LyAddTranDataForProp(rowLabel, pr)
                            set_alreadyDone.add(pr.identifier)
    # ------
    def draw(self, context):
        def LyAddDecorLyColRaw(where: UILayout, sy=0.05, sx=1.0, en=False):
            where.prop(self,'vaDecorLy', text="")
            where.scale_x = sx
            where.scale_y = sy # 如果小于 0.05, 布局会消失, 圆角也会消失.
            where.enabled = en
        colLy = self.layout.column()
        colMain = colLy.column(align=True)
        colTabs = colMain.column(align=True)
        rowTabs = colTabs.row(align=True)
        # 标签页切换是通过操作符创建的, 以免在按住鼠标拖动时意外切换标签页, 这在有大量"isColored"选项时很有诱惑力.
        # 而且现在它们被装饰得更像"标签页"了, 这是普通的 prop 布局 с 'expand=True' 无法做到的.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=_iface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
            # 现在更像标签页了
            LyAddDecorLyColRaw(col.row(align=True)) # row.operator(VoronoiOpAddonTabs.bl_idname, text="", emboss=False) # 通过操作符也行.
            #col.scale_x = min(1.0, (5.5-cyc)/2)
        colBox = colTabs.column(align=True)
        #LyAddDecorLyColRaw(colBox.row(align=True))
        #LyAddDecorLyColRaw(colBox.row(align=True), sy=0.25) # 盒子无法收缩到比其空状态更小. 不得不寻找其他方法..
        try:
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
        except Exception as ex:
            LyAddEtb(colMain) # colMain.label(text=str(ex), icon='ERROR', translate=False)

for cls in dict_vtClasses:
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropName}: bpy.props.BoolProperty(name=\"\", default=False)")
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropNameInfo}: bpy.props.BoolProperty(name=\"\", default=False)")

class KeymapItemCategory:
    """快捷键项分类 - 用于组织和过滤keymap items"""
    prop_name: str
    matched_items: set
    item_idnames: set
    count: int
    filter_func: Callable[[KeyMapItem], bool] | None

    def __init__(self, prop_name='', matched_items=set(), item_idnames=set()):
        self.prop_name = prop_name
        self.matched_items = matched_items
        self.item_idnames = item_idnames
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

_classes = [
    VmtOpMixer,
    VmtPieMixer,
    VqmtOpMain,
    VqmtPieMath,
    VestOpBox,
    VestPieBox,
    SNA_OT_Change_Node_Domain_And_Name,
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
        kmi.active = blid!='node.voronoi_dummy'
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

def DisableKmis(): # 用于重复运行脚本. 在第一次"恢复"之前有效.
    node_kms = user_node_keymaps()
    for li, *oi in list_kmiDefs:
        for kmiCon in node_kms.keymap_items:
            if li==kmiCon.idname:
                kmiCon.active = False # 这会删除重复项. 是个 hack 吗?
                kmiCon.active = True # 如果是原始的, 就恢复.

if __name__ == "__main__":
    DisableKmis() # 似乎在添加热键之前或之后调用都无所谓.
    register_from_main = True
    register()
