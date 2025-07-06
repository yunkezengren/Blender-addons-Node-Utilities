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

from builtins import len as length       # 我超爱三个字母的变量名.没有像"len"这样的名字, 我会感到非常伤心和孤独... 😭 还有 'Vector.length' 也是.
import bpy, rna_keymap_ui, bl_keymap_utils
from bpy.types import UILayout
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, StringProperty)
from bpy.app.translations import pgettext_iface as TranslateIface
from time import perf_counter_ns
from pprint import pprint

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
from .globals import dict_vlHhTranslations
from .common_forward_func import GetFirstUpperLetters, GetUserKmNe, format_tool_set, Prefs
from .common_forward_class import TryAndPass
from .utils_solder import SolderClsToolNames, RegisterSolderings, UnregisterSolderings
from .utils_translate import GetAnnotFromCls, VlTrMapForKey
from .utils_drawing import TestDraw

from .v_tool import VoronoiToolRoot, VoronoiToolPairSk
from .vm_Mixer import VmtOpMixer, VmtPieMixer
from .vqmt_PieMath import VqmtOpMain, VqmtPieMath
from .v_Dummy_tool import VoronoiDummyTool
from .v_Hider_tool import VoronoiHiderTool
from .v_Mixer_tool import VoronoiMixerTool
from .v_Ranto_tool import VoronoiRantoTool
from .v_CallNodePie import VoronoiCallNodePie
from .v_Linker_tool import VoronoiLinkerTool
from .v_Warper_tool import VoronoiWarperTool
from .v_Preview_tool import VoronoiPreviewTool
from .v_Swapper_tool import VoronoiSwapperTool
from .v_QuickConstant import VoronoiQuickConstant
from .v_QuickMath_tool import VoronoiQuickMathTool
from .v_ResetNode_tool import VoronoiResetNodeTool
from .v_MassLinker_tool import VoronoiMassLinkerTool
from .v_Interfacer_tool import VoronoiInterfacerTool
from .v_EnumSelector_tool import VoronoiEnumSelectorTool, VestOpBox, VestPieBox, SNA_OT_Change_Node_Domain_And_Name
from .v_LinkRepeating_tool import VoronoiLinkRepeatingTool
from .v_LinksTransfer_tool import VoronoiLinksTransferTool
from .v_PreviewAnchor_tool import VoronoiPreviewAnchorTool
from .v_QuickDimensions_tool import VoronoiQuickDimensionsTool
from .v_LazyNodeStencils_tool import VoronoiLazyNodeStencilsTool
from .rot_or_mat_convert import Rot_or_Mat_Convert, PIE_MT_Convert_To_Rotation, PIE_MT_Convert_Rotation_To, PIE_MT_Separate_Matrix, PIE_MT_Combine_Matrix

try:
    from rich import traceback
    traceback.install(extra_lines=0, width=165, code_width=160, show_locals=False)
    
    # from rich.console import Console      # 在别的文件里导入了
    # console = Console(width=160, log_time=False)
    # print = console.log    # 带有 时间戳 源文件路径 行号
    # from rich import print as rprint      # 用log打印报错太烦了每行都带路径
except ImportError:
    pass

dict_classes = {} # 所有需要注册的类都放在这里. 使用字典是为了 smart_add_to_reg_and_kmiDefs() 函数, 同时还能保持顺序.
dict_vtClasses = {} # 只存放 V*T (Voronoi Tool) 工具.

list_kmiDefs = []
dict_setKmiCats = {'grt':set(), 'oth':set(), 'spc':set(), 'qqm':set(), 'cus':set()}

def smart_add_to_reg_and_kmiDefs(cls, txt, dict_props={}):
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

dict_vlHhTranslations['ru_RU'] = {'author':"ugorek",    'vl':(5,0,0), 'created':"2024.02.29", 'trans':{'a':{}, 'Op':{}}} # 作者本人
dict_vlHhTranslations['zh_CN'] = {'author':"chenpaner", 'vl':(4,0,0), 'created':"2023.12.15", 'trans':{'a':{}, 'Op':{}}} # https://github.com/ugorek000/VoronoiLinker/issues/21
#dict_vlHhTranslations['aa_AA'] = # 谁会是第二个呢? 会有多快呢? 🤔

for dk in dict_vlHhTranslations:
    exec(dk+f" = '{dk}'") # 等什么时候出现带 @variantcode 的语言 (大概永远不会有), 才需要担心这个问题.

class TranslationHelper():
    def __init__(self, dict_trans={}, lang=''):
        self.name = __package__+"-"+lang
        self.dict_translations = dict()
        for cyc, dict_data in enumerate(dict_trans.values()):
            for dk, dv in dict_data.items():
                if cyc:
                    self.dict_translations.setdefault(lang, {})[ ('Operator', dk) ] = dv
                self.dict_translations.setdefault(lang, {})[ ('*', dk) ] = dv
    def register(self):
        if self.dict_translations:
            try:
                bpy.app.translations.register(self.name, self.dict_translations)
            except:
                with TryAndPass():
                    bpy.app.translations.unregister(self.name)
                    bpy.app.translations.register(self.name, self.dict_translations)
    def unregister(self):
        bpy.app.translations.unregister(self.name)

list_translationClasses = []

def RegisterTranslations():
    CollectTranslationDict()
    for dk in dict_vlHhTranslations:
        list_translationClasses.append(TranslationHelper(dict_vlHhTranslations[dk]['trans'], dk))
    for li in list_translationClasses:
        li.register()
def UnregisterTranslations():
    for li in list_translationClasses:
        li.unregister()

with VlTrMapForKey(bl_info2['description']) as dm:
    dm["ru_RU"] = "Разнообразные помогалочки для соединения нодов, основанные на поле расстояний."
    dm["zh_CN"] = "基于距离场的多种节点连接辅助工具。"

txtAddonVer = ".".join([str(v) for v in bl_info2['version']])
txt_addonVerDateCreated = f"Version {txtAddonVer} created {bl_info2['created']}"
with VlTrMapForKey(txt_addonVerDateCreated) as dm:
    dm["ru_RU"] = f"Версия {txtAddonVer} создана {bl_info2['created']}"
#    dm["zh_CN"] = f" {txtAddonVer}  {bl_info2['created']}"
txt_addonBlVerSupporting = f"For Blender versions: {bl_info2['info_supported_blvers']}"
with VlTrMapForKey(txt_addonBlVerSupporting) as dm:
    dm["ru_RU"] = f"Для версий Блендера: {bl_info2['info_supported_blvers']}"
#    dm["zh_CN"] = f" {bl_info2['info_supported_blvers']}"
txt_onlyFontFormat = "Only .ttf or .otf format"
with VlTrMapForKey(txt_onlyFontFormat) as dm:
    dm["ru_RU"] = "Только .ttf или .otf формат"
    dm["zh_CN"] = "只支持.ttf或.otf格式"
txt_copySettAsPyScript = "Copy addon settings as .py script"
with VlTrMapForKey(txt_copySettAsPyScript, tc='Op') as dm:
    dm["ru_RU"] = "Скопировать настройки аддона как '.py' скрипт"
    dm["zh_CN"] = "将插件设置复制为'.py'脚本,复制到粘贴板里"
txt_checkForUpdatesYourself = "Check for updates yourself"
with VlTrMapForKey(txt_checkForUpdatesYourself, tc='Op') as dm:
    dm["ru_RU"] = "Проверяйте обновления самостоятельно"
#    dm["zh_CN"] = ""
txt_vmtNoMixingOptions = "No mixing options"
with VlTrMapForKey(txt_vmtNoMixingOptions) as dm:
    dm["ru_RU"] = "Варианты смешивания отсутствуют"
    dm["zh_CN"] = "无混合选项"
txt_vqmtThereIsNothing = "There is nothing"
with VlTrMapForKey(txt_vqmtThereIsNothing) as dm:
    dm["ru_RU"] = "Ничего нет"

txt_FloatQuickMath = "Float Quick Math"
with VlTrMapForKey(txt_FloatQuickMath) as dm:
    dm["zh_CN"] = "快速浮点运算"
txt_VectorQuickMath = "Vector Quick Math"
with VlTrMapForKey(txt_VectorQuickMath) as dm:
    dm["zh_CN"] = "快速矢量运算"
txt_IntQuickMath = "Integer Quick Math"
with VlTrMapForKey(txt_IntQuickMath) as dm:
    dm["zh_CN"] = "快速整数运算"
txt_BooleanQuickMath = "Boolean Quick Math"
with VlTrMapForKey(txt_BooleanQuickMath) as dm:
    dm["zh_CN"] = "快速布尔运算"
txt_MatrixQuickMath = "Matrix Quick Math"
with VlTrMapForKey(txt_MatrixQuickMath) as dm:
    dm["zh_CN"] = "快速矩阵运算"
txt_ColorQuickMode = "Color Quick Mode"
with VlTrMapForKey(txt_ColorQuickMode) as dm:
    dm["zh_CN"] = "快速颜色运算"

with VlTrMapForKey("Switch  ") as dm:
    dm["ru_RU"] = "Переключение"
with VlTrMapForKey("Mix  ") as dm:
    dm["ru_RU"] = "Смешивание"
with VlTrMapForKey("Compare  ") as dm:
    dm["ru_RU"] = "Сравнение"

# 译者注: 以下词汇在您的语言中可能已经被Blender官方翻译了. 保留这些是为了支持没有内置这些翻译的旧版本.
with VlTrMapForKey("Virtual") as dm:
    dm["ru_RU"] = "Виртуальный"
    dm["zh_CN"] = "虚拟"
with VlTrMapForKey("Restore", tc='Op') as dm:
    dm["ru_RU"] = "Восстановить"
    dm["zh_CN"] = "恢复"
with VlTrMapForKey("Add New", tc='Op') as dm:
    dm["ru_RU"] = "Добавить"
    dm["zh_CN"] = "添加"
with VlTrMapForKey("Mode") as dm:
    dm["ru_RU"] = "Режим"
    dm["zh_CN"] = "模式"
with VlTrMapForKey("Colored") as dm:
    dm["ru_RU"] = "Цветной"
    dm["zh_CN"] = "根据端点类型自动设置颜色:"
with VlTrMapForKey("Edge pan") as dm:
    dm["ru_RU"] = "Краевое панорамирование"
with VlTrMapForKey("Pie") as dm:
    dm["ru_RU"] = "Пирог"
with VlTrMapForKey("Special") as dm:
    dm["ru_RU"] = "Специальное"
with VlTrMapForKey("Customization") as dm:
    dm["ru_RU"] = "Кастомизация"


def CollectTranslationDict(): # 为了方便翻译那些需要注册属性的文本. 请参阅 BringTranslations 系列函数.
    global prefsTran
    prefsTran = Prefs()

    for cls in dict_vtClasses:
        cls.BringTranslations()
    VoronoiAddonPrefs.BringTranslations()

    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').name) as dm:
        dm["ru_RU"] = "Пропускать через выделение нода"
        dm["zh_CN"] = "单击输出接口预览(而不是自动根据鼠标位置自动预览)"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').description) as dm:
        dm["ru_RU"] = "Клик над нодом активирует выделение, а не инструмент"
        dm["zh_CN"] = "单击输出接口才连接预览而不是根据鼠标位置动态预览"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').name) as dm:
        dm["ru_RU"] = "Может между полями"
        dm["zh_CN"] = "接口类型可以不一样"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').description) as dm:
        dm["ru_RU"] = "Инструмент может искать сокеты между различными типами полей"
        dm["zh_CN"] = "工具可以连接不同类型的接口"

    dict_vlHhTranslations['zh_HANS'] = dict_vlHhTranslations['zh_CN']
    for cls in dict_vtClasses:
        if (cls, 'zh_CN') in dict_toolLangSpecifDataPool:
            dict_toolLangSpecifDataPool[cls, 'zh_HANS'] = dict_toolLangSpecifDataPool[cls, 'zh_CN']

dict_toolLangSpecifDataPool = {}

smart_add_to_reg_and_kmiDefs(VoronoiLinkerTool, "##A_RIGHTMOUSE") # "##A_RIGHTMOUSE"?
with VlTrMapForKey(VoronoiLinkerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速连接"
with VlTrMapForKey(format_tool_set(VoronoiLinkerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiLinkerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiLinkerTool.bl_label}快速连接设置:"
dict_toolLangSpecifDataPool[VoronoiLinkerTool, "ru_RU"] = "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника."

smart_add_to_reg_and_kmiDefs(VoronoiPreviewTool, "SC#_LEFTMOUSE")
with VlTrMapForKey(VoronoiPreviewTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速预览"
with VlTrMapForKey(format_tool_set(VoronoiPreviewTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiPreviewTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiPreviewTool.bl_label}快速预览设置:"
dict_toolLangSpecifDataPool[VoronoiPreviewTool, "ru_RU"] = "Канонический инструмент для мгновенного перенаправления явного вывода дерева.\nЕщё более полезен при использовании совместно с VPAT."

smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':1})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':2})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors':2})
with VlTrMapForKey(VoronoiPreviewAnchorTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi新建预览转接点"
dict_toolLangSpecifDataPool[VoronoiPreviewAnchorTool, "ru_RU"] = "Вынужденное отделение от VPT, своеобразный \"менеджер-компаньон\" для VPT.\nЯвное указание сокета и создание рероут-якорей."

smart_add_to_reg_and_kmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") # 混合器移到了左键, 为 VQMT 减轻负担.
with VlTrMapForKey(VoronoiMixerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速混合"
with VlTrMapForKey(format_tool_set(VoronoiMixerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiMixerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiMixerTool.bl_label}快速混合设置:"
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
with VlTrMapForKey(VoronoiQuickMathTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速数学运算"
with VlTrMapForKey(format_tool_set(VoronoiQuickMathTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiQuickMathTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiQuickMathTool.bl_label}快速数学运算设置:"
dict_toolLangSpecifDataPool[VoronoiQuickMathTool, "ru_RU"] = """Полноценное ответвление от VMT. Быстрая и быстрая быстрая математика на спидах.
Имеет дополнительный мини-функционал. Также см. \"Quick quick math\" в раскладе."""

smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "###_R")
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "S##_R", {'isAccumulate':True})
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#C#_R", {'isOnlySelected':2})
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True})
with VlTrMapForKey(VoronoiRantoTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi节点自动排布对齐"
with VlTrMapForKey(format_tool_set(VoronoiRantoTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiRantoTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiRantoTool.bl_label}节点自动排布对齐工具设置:"
dict_toolLangSpecifDataPool[VoronoiRantoTool, "ru_RU"] = "Сейчас этот инструмент не более чем пустышка.\nСтанет доступным, когда VL стяжет свои заслуженные(?) лавры популярности."

smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':'ADD'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S#A_S", {'toolMode':'TRAN'})
with VlTrMapForKey(VoronoiSwapperTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速替换接口"

dict_toolLangSpecifDataPool[VoronoiSwapperTool, "ru_RU"] = """Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.
Для линка обмена не будет, если в итоге он окажется исходящим из своего же нода."""
dict_toolLangSpecifDataPool[VoronoiSwapperTool, "zh_CN"] = "Alt是批量替换输出接口,Shift是互换接口"

smart_add_to_reg_and_kmiDefs(VoronoiCallNodePie, "#C#_LEFTMOUSE")

smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "#CA_E", {'toolMode':'SOCKETVAL'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "SC#_E", {'toolMode':'NODE'})
with VlTrMapForKey(VoronoiHiderTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速隐藏"
with VlTrMapForKey(format_tool_set(VoronoiHiderTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiHiderTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiHiderTool.bl_label}快速隐藏接口设置:"
dict_toolLangSpecifDataPool[VoronoiHiderTool, "ru_RU"] = "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов."
dict_toolLangSpecifDataPool[VoronoiHiderTool, "zh_CN"] = "Shift是自动隐藏数值为0/颜色纯黑/未连接的接口,Ctrl是单个隐藏接口"


smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})
with VlTrMapForKey(VoronoiMassLinkerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi根据接口名批量快速连接"
with VlTrMapForKey(format_tool_set(VoronoiMassLinkerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiMassLinkerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiMassLinkerTool.bl_label}根据接口名批量连接设置:"
dict_toolLangSpecifDataPool[VoronoiMassLinkerTool, "ru_RU"] = """"Малыш котопёс", не ноды, не сокеты. Создан ради редких точечных спец-ускорений.
VLT на максималках. В связи со своим принципом работы, по своему божественен."""

# 最初想用 'V_Sca', 但手指伸到 V 太远了. 而且, 考虑到创建这个工具的原因, 需要最小化调用的复杂性.
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_R", {'isPieChoice':True, 'isSelectNode':3})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_E", {'isInstantActivation':False})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "##A_E", {'isToggleOptions':True})
with VlTrMapForKey(VoronoiEnumSelectorTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速切换节点内部下拉列表"
with VlTrMapForKey(format_tool_set(VoronoiEnumSelectorTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiEnumSelectorTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiEnumSelectorTool.bl_label}快速显示节点里下拉列表设置:"
dict_toolLangSpecifDataPool[VoronoiEnumSelectorTool, "ru_RU"] = """Инструмент для удобно-ленивого переключения свойств перечисления.
Избавляет от прицеливания мышкой, клика, а потом ещё одного прицеливания и клика."""

# 参见: VlrtData, VlrtRememberLastSockets() 和 NewLinkHhAndRemember().
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "###_V", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'toolMode':'NODE'})
with VlTrMapForKey(VoronoiLinkRepeatingTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi重复连接到上次用快速连接到的输出端" # dm["zh_CN"] = "Voronoi快速恢复连接"
dict_toolLangSpecifDataPool[VoronoiLinkRepeatingTool, "ru_RU"] = """Полноценное ответвление от VLT, повторяет любой предыдущий линк от большинства
других инструментов. Обеспечивает удобство соединения "один ко многим"."""


smart_add_to_reg_and_kmiDefs(VoronoiQuickDimensionsTool, "##A_D")
with VlTrMapForKey(VoronoiQuickDimensionsTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速分离/合并 矢量/颜色"
dict_toolLangSpecifDataPool[VoronoiQuickDimensionsTool, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."

smart_add_to_reg_and_kmiDefs(VoronoiQuickConstant, "##A_C")
with VlTrMapForKey(VoronoiQuickConstant.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速常量"
dict_toolLangSpecifDataPool[VoronoiQuickConstant, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."

smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "SC#_A", {'toolMode':'NEW'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_A", {'toolMode':'CREATE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_C", {'toolMode':'COPY'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_V", {'toolMode':'PASTE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_X", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Z", {'toolMode':'FLIP'})
# smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Q", {'toolMode':'DELETE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_E", {'toolMode':'SOC_TY'})
with VlTrMapForKey(VoronoiInterfacerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi在节点组里快速复制粘贴接口名给节点组输入输出端"
dict_toolLangSpecifDataPool[VoronoiInterfacerTool, "ru_RU"] = """Инструмент на уровне "The Great Trio". Ответвление от VLT ради удобного ускорения
процесса создания и спец-манипуляций с интерфейсами. "Менеджер интерфейсов"."""

smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "SC#_T")
smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "S##_T", {'isByIndexes':True})
with VlTrMapForKey(VoronoiLinksTransferTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi链接按输入端类型切换到别的接口"
dict_toolLangSpecifDataPool[VoronoiLinksTransferTool, "ru_RU"] = "Инструмент для редких нужд переноса всех линков с одного нода на другой.\nВ будущем скорее всего будет слито с VST."

smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "##A_W")
smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "S#A_W", {'isZoomedTo':False})
with VlTrMapForKey(VoronoiWarperTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速聚焦某条连接"
dict_toolLangSpecifDataPool[VoronoiWarperTool, "ru_RU"] = "Мини-ответвление реверс-инженеринга топологии, (как у VPT).\nИнструмент для \"точечных прыжков\" по сокетам."

smart_add_to_reg_and_kmiDefs(VoronoiLazyNodeStencilsTool, "##A_Q")
with VlTrMapForKey(VoronoiLazyNodeStencilsTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi在输入端快速节点"
with VlTrMapForKey(format_tool_set(VoronoiLazyNodeStencilsTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiLazyNodeStencilsTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiLazyNodeStencilsTool.bl_label}快速添加纹理设置:"
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "ru_RU"] = """Мощь. Три буквы на инструмент, дожили... Инкапсулирует Ctrl-T от
NodeWrangler'а, и никогда не реализованный 'VoronoiLazyNodeContinuationTool'. """ #"Больше лени богу лени!"
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "zh_CN"] = "代替NodeWrangler的ctrl+t"

smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})
with VlTrMapForKey(VoronoiResetNodeTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速恢复节点默认参数"
dict_toolLangSpecifDataPool[VoronoiResetNodeTool, "ru_RU"] = """Инструмент для сброса нодов без нужды прицеливания, с удобствами ведения мышкой
и игнорированием свойств перечислений. Был создан, потому что в NW было похожее."""

#smart_add_to_reg_and_kmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})

dict_setKmiCats['grt'].add(VoronoiDummyTool.bl_idname)
dict_setKmiCats['grt'].add(VoronoiLinkerTool.bl_idname)
dict_setKmiCats['grt'].add(VoronoiMixerTool.bl_idname)
dict_setKmiCats['grt'].add(VoronoiPreviewTool.bl_idname)
dict_setKmiCats['grt'].add(VoronoiQuickMathTool.bl_idname)

dict_setKmiCats['oth'].add(VoronoiCallNodePie.bl_idname)
dict_setKmiCats['oth'].add(VoronoiHiderTool.bl_idname)
dict_setKmiCats['oth'].add(VoronoiEnumSelectorTool.bl_idname)
dict_setKmiCats['oth'].add(VoronoiQuickConstant.bl_idname)
dict_setKmiCats['oth'].add(VoronoiQuickDimensionsTool.bl_idname)
dict_setKmiCats['oth'].add(VoronoiMassLinkerTool.bl_idname)         # 批量连线

dict_setKmiCats['spc'].add(VoronoiLazyNodeStencilsTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiPreviewAnchorTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiSwapperTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiInterfacerTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiLinkRepeatingTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiLinksTransferTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiRantoTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiResetNodeTool.bl_idname)
dict_setKmiCats['spc'].add(VoronoiWarperTool.bl_idname)

with VlTrMapForKey(VoronoiDummyTool.bl_label) as dm:
    dm["ru_RU"] = "Voronoi Болванка"

dict_toolLangSpecifDataPool[VoronoiDummyTool, "ru_RU"] = """"Ой дурачёк"."""

# =======

def GetVlKeyconfigAsPy(): # 从 'bl_keymap_utils.io' 借来的. 我完全不知道它是如何工作的.
    def Ind(num):
        return " "*num
    def keyconfig_merge(kc1, kc2):
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
    edited_kc.keymaps.append(GetUserKmNe())
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
def GetVaSettAsPy(prefs):
    set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'dsIsFieldDebug', 'dsIsTestDrawing', # tovo2v6: 是全部吗?
                             'vaKmiMainstreamDiscl', 'vaKmiOtjersDiscl', 'vaKmiSpecialDiscl', 'vaKmiQqmDiscl', 'vaKmiCustomDiscl'}
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
    txt_vasp += "        setattr(prefs, att, val)"+"\n\n"
    def AddAndProc(txt):
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
                GetUserKmNe().keymap_items.new("node.voronoi_",'D','PRESS').show_expanded = True
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__
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
    vaKmiMainstreamDiscl : BoolProperty(name="The Great Trio ", default=True) # 注意: 空格对翻译很重要.
    vaKmiOtjersDiscl     : BoolProperty(name="Others ", default=False)
    vaKmiSpecialDiscl    : BoolProperty(name="Specials ", default=False)
    vaKmiQqmDiscl        : BoolProperty(name="Quick quick math ", default=False)
    vaKmiCustomDiscl     : BoolProperty(name="Custom ", default=True)
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
    dsPointOffsetX     : FloatProperty(name="Point offset X axis",       default=20.0,   min=-50.0, max=50.0)
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
    @staticmethod
    def BringTranslations():
        with VlTrMapForKey(GetPrefsRnaProp('vaInfoRestore').description) as dm:
            dm["ru_RU"] = "Этот список лишь копия из настроек. \"Восстановление\" восстановит всё, а не только аддон"
            dm["zh_CN"] = "危险:“恢复”按钮将恢复整个快捷键里“节点编辑器”类中的所有设置,而不仅仅是恢复此插件!下面只显示本插件的快捷键。"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiMainstreamDiscl').name) as dm:
            dm["ru_RU"] = "Великое трио"
            dm["zh_CN"] = "最有用"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiOtjersDiscl').name) as dm:
            dm["ru_RU"] = "Другие"
            dm["zh_CN"] = "很有用"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiSpecialDiscl').name) as dm:
            dm["ru_RU"] = "Специальные"
            dm["zh_CN"] = "也有用"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiQqmDiscl').name) as dm:
            dm["ru_RU"] = "Быстрая быстрая математика"
            dm["zh_CN"] = "数学运算饼菜单"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiCustomDiscl').name) as dm:
            dm["ru_RU"] = "Кастомные"
            dm["zh_CN"] = "自定义"
        #== Draw ==
        with VlTrMapForKey(GetPrefsRnaProp('dsUniformColor').name) as dm:
            dm["ru_RU"] = "Альтернативный постоянный цвет"
            dm["zh_CN"] = "自定义轮选时接口的颜色"    
        with VlTrMapForKey(GetPrefsRnaProp('dsUniformNodeColor').name) as dm:
            dm["ru_RU"] = "Альтернативный цвет нодов"
            dm["zh_CN"] = "动态选择节点时标识的颜色(显示下拉列表时)"
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColor').name) as dm:
            dm["ru_RU"] = "Цвет курсора"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColorAvailability').name) as dm:
            dm["ru_RU"] = "Наличие цвета курсора"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColorAvailability').description) as dm:
            dm["ru_RU"] = "Если линия рисуется к курсору, окрашивать её часть в цвет курсора.\n0 – Выключено.\n1 – Для одной линии.\n2 – Всегда"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsSocketAreaAlpha').name) as dm:
            dm["ru_RU"] = "Прозрачность области сокета"
            dm["zh_CN"] = "接口区域的透明度"
        with VlTrMapForKey(GetPrefsRnaProp('dsFontFile').name) as dm:
            dm["ru_RU"] = "Файл шрифта"
            dm["zh_CN"] = "字体文件"
        with VlTrMapForKey(GetPrefsRnaProp('dsManualAdjustment').name) as dm:
            dm["ru_RU"] = "Ручная корректировка"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsManualAdjustment').description) as dm:
            dm["ru_RU"] = "Смещение текста по оси Y для данного шрифта"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsPointOffsetX').name) as dm:
            dm["ru_RU"] = "Смещение точки по оси X"
            dm["zh_CN"] = "X轴上的点偏移"
        with VlTrMapForKey(GetPrefsRnaProp('dsFrameOffset').name) as dm:
            dm["ru_RU"] = "Размер рамки"
            dm["zh_CN"] = "边框大小"
        with VlTrMapForKey(GetPrefsRnaProp('dsFontSize').name) as dm:
            dm["ru_RU"] = "Размер шрифта"
            dm["zh_CN"] = "字体大小"
        with VlTrMapForKey(GetPrefsRnaProp('dsMarkerStyle').name) as dm:
            dm["ru_RU"] = "Стиль маркера"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsIsDrawSkArea').name) as dm:
            dm["ru_RU"] = "Область сокета"
            dm["zh_CN"] = "高亮显示选中接口"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle').name) as dm:
            dm["ru_RU"] = "Стиль отображения рамки"
            dm["zh_CN"] = "边框显示样式"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',0).name) as dm:
            dm["ru_RU"] = "Классический"
            dm["zh_CN"] = "经典"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',1).name) as dm:
            dm["ru_RU"] = "Упрощённый"
            dm["zh_CN"] = "简化"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',2).name) as dm:
            dm["ru_RU"] = "Только текст"
            dm["zh_CN"] = "仅文本"
        with VlTrMapForKey(GetPrefsRnaProp('dsPointScale').name) as dm:
            dm["ru_RU"] = "Масштаб точки"
#            dm["zh_CN"] = "点的大小"?
        with VlTrMapForKey(GetPrefsRnaProp('dsDistFromCursor').name) as dm:
            dm["ru_RU"] = "Расстояние до текста от курсора"
            dm["zh_CN"] = "到文本的距离"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAlwaysLine').name) as dm:
            dm["ru_RU"] = "Всегда рисовать линию"
            dm["zh_CN"] = "始终绘制线条"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAlwaysLine').description) as dm:
            dm["ru_RU"] = "Рисовать линию к курсору даже от одного выбранного сокета"
            dm["zh_CN"] = "在鼠标移动到移动到已有连接接口的时是否还显示连线"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsSlideOnNodes').name) as dm:
            dm["ru_RU"] = "Скользить по нодам"
            dm["zh_CN"] = "在节点上滑动"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAllowTextShadow').name) as dm:
            dm["ru_RU"] = "Включить тень текста"
            dm["zh_CN"] = "启用文本阴影"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowCol').name) as dm:
            dm["ru_RU"] = "Цвет тени"
            dm["zh_CN"] = "阴影颜色"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowOffset').name) as dm:
            dm["ru_RU"] = "Смещение тени"
            dm["zh_CN"] = "阴影偏移"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowBlur').name) as dm:
            dm["ru_RU"] = "Размытие тени"
            dm["zh_CN"] = "阴影模糊"
        #== Settings ==
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanFac').name) as dm:
            dm["ru_RU"] = "Фактор панорамирования масштаба"
            dm["zh_CN"] = "边缘平移缩放系数"
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanFac').description) as dm:
            dm["ru_RU"] = "0.0 – Только сдвиг; 1.0 – Только масштаб"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanSpeed').name) as dm:
            dm["ru_RU"] = "Скорость краевого панорамирования"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vIsOverwriteZoomLimits').name) as dm:
            dm["ru_RU"] = "Перезапись лимитов масштаба"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vOwZoomMin').name) as dm:
            dm["ru_RU"] = "Минимальный масштаб"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vOwZoomMax').name) as dm:
            dm["ru_RU"] = "Максимальный масштаб"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsIsDrawNodeNameLabel').name) as dm:
            dm["ru_RU"] = "Показывать заголовок для нода"
            dm["zh_CN"] = "显示节点标签"
    # ------
    def LyDrawTabSettings(self, where):
        def LyAddAddonBoxDiscl(where: UILayout, who, att, *, txt=None, isWide=False, align=False):
            colBox = where.box().column(align=True)
            if LyAddDisclosureProp(colBox, who, att, txt=txt, active=False, isWide=isWide):
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
    def LyDrawTabAppearance(self, where):
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
    def LyDrawTabDraw(self, where):
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
    def LyDrawTabKeymaps(self, where):
        colMain = where.column()
        colMain.separator()
        rowLabelMain = colMain.row(align=True)
        rowLabel = rowLabelMain.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(icon='DOT')
        rowLabel.label(text="Node Editor")
        rowLabelPost = rowLabelMain.row(align=True)
        colList = colMain.column(align=True)
        kmUNe = GetUserKmNe()
        ##
        kmiCats = KmiCats()
        kmiCats.cus = KmiCat('vaKmiCustomDiscl',     set())
        kmiCats.qqm = KmiCat('vaKmiQqmDiscl',        set(), dict_setKmiCats["qqm"] )
        kmiCats.grt = KmiCat('vaKmiMainstreamDiscl', set(), dict_setKmiCats["grt"] )
        kmiCats.oth = KmiCat('vaKmiOtjersDiscl',     set(), dict_setKmiCats["oth"] )
        kmiCats.spc = KmiCat('vaKmiSpecialDiscl',    set(), dict_setKmiCats["spc"] )
        kmiCats.cus.LCond = lambda a: a.id<0 # 负id用于自定义? 好吧. 就当是识别标准了.
        kmiCats.qqm.LCond = lambda a: any(True for txt in {'quickOprFloat','quickOprVector','quickOprBool','quickOprColor','justPieCall','isRepeatLastOperation'} if getattr(a.properties, txt, None))
        kmiCats.grt.LCond = lambda a: a.idname in kmiCats.grt.set_idn
        kmiCats.oth.LCond = lambda a: a.idname in kmiCats.oth.set_idn
        kmiCats.spc.LCond = lambda a:True
        # 在旧版插件中, 使用另一种搜索方法, "keymap" 标签页中的顺序与注册具有相同 `cls` 的 kmidef 的调用顺序相反.
        # 现在改成了这样. 之前的方法是如何工作的 -- 我完全不知道.
        scoAll = 0
        for li in kmUNe.keymap_items:
            if li.idname.startswith("node.voronoi_"):
                for dv in kmiCats.__dict__.values():
                    if dv.LCond(li):
                        dv.set_kmis.add(li)
                        dv.sco += 1
                        break
                scoAll += 1 # 热键现在变得非常非常多, 知道它们的数量会很不错.
        if kmUNe.is_user_modified:
            rowRestore = rowLabelMain.row(align=True)
            with LyAddQuickInactiveCol(rowRestore, align=False) as row:
                row.prop(self,'vaInfoRestore', text="", icon='INFO', emboss=False)
            rowRestore.context_pointer_set('keymap', kmUNe)
            rowRestore.operator('preferences.keymap_restore', text="Restore")
        else:
            rowLabelMain.label()
        rowAddNew = rowLabelMain.row(align=True)
        rowAddNew.ui_units_x = 12
        rowAddNew.separator()
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='NONE').opt = 'AddNewKmi' # NONE  ADD
        def LyAddKmisCategory(where: UILayout, cat):
            if not cat.set_kmis:
                return
            colListCat = where.row().column(align=True)
            txt = self.bl_rna.properties[cat.propName].name
            if not LyAddDisclosureProp(colListCat, self, cat.propName, txt=TranslateIface(txt)+f" ({cat.sco})", active=False, isWide=1-1):
                return
            for li in sorted(cat.set_kmis, key=lambda a:a.id):
                colListCat.context_pointer_set('keymap', kmUNe)
                rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, kmUNe, li, colListCat, 0) # 注意: 如果 colListCat 不是 colListCat, 那么删除 kmi 的功能将不可用.
        LyAddKmisCategory(colList, kmiCats.cus)
        LyAddKmisCategory(colList, kmiCats.grt)
        LyAddKmisCategory(colList, kmiCats.oth)
        LyAddKmisCategory(colList, kmiCats.spc)
        LyAddKmisCategory(colList, kmiCats.qqm)
        rowLabelPost.label(text=f"({scoAll})", translate=False)
    def LyDrawTabInfo(self, where):
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
                    colText = rowTool.column(align=True)
                    for li in txtToolInfo.split("\n"):
                        colText.label(text=li, translate=False)
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
                text = TranslateIface(text)
                if text:
                    list_split = text.split("\n")
                    hig = length(list_split)-1
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
                if type(pr)==typeEnum:
                    for en in pr.enum_items:
                        LyAddTranDataForProp(col2, en, dot="")
            typeEnum = bpy.types.EnumProperty
            match self.vaLangDebEnum:
                case 'FREE':
                    txt = TranslateIface("Free")
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
                    txt = TranslateIface("Special")
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
            col.operator(VoronoiOpAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
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

class KmiCat():
    def __init__(self, propName='', set_kmis=set(), set_idn=set()):
        self.propName = propName
        self.set_kmis = set_kmis
        self.set_idn = set_idn
        self.sco = 0

class KmiCats:
    pass

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
    
    RegisterTranslations()
    RegisterSolderings()

def unregister():
    UnregisterSolderings()
    UnregisterTranslations()

    km = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for li in list_addonKeymaps:
        km.keymap_items.remove(li)
    list_addonKeymaps.clear()

    for dk in dict_classes:
        bpy.utils.unregister_class(dk)

def DisableKmis(): # 用于重复运行脚本. 在第一次"恢复"之前有效.
    kmUNe = GetUserKmNe()
    for li, *oi in list_kmiDefs:
        for kmiCon in kmUNe.keymap_items:
            if li==kmiCon.idname:
                kmiCon.active = False # 这会删除重复项. 是个 hack 吗?
                kmiCon.active = True # 如果是原始的, 就恢复.

if __name__ == "__main__":
    DisableKmis() # 似乎在添加热键之前或之后调用都无所谓.
    register_from_main = True
    register()
