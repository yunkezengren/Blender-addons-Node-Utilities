# TODO 没面板的组输入和节点组,插入接口才符合顺序
# TODO 快速数学运算,在偏好设置里加个选项,如果连满了两个接口,是否hide
# TODO 整数运算饼菜单
# TODO 旋转 快速切换饼菜单
# _ TODO 矩阵 快速切换饼菜单
# TODO 切换浮点整数矢量运算

bl_info = {'name':"Voronoi Linker", 
           'author':"ugorek", #Так же спасибо "Oxicid" за важную для VL'а помощь.
           'version':(5,1,2), 
           'blender':(4,0,2), 
           'created':"2024.03.06", #Ключ 'created' для внутренних нужд.
           'info_supported_blvers': "b4.0.2 – b4.0.2", #Тоже внутреннее.
           'description':"Various utilities for nodes connecting, based on distance field.", 'location':"Node Editor", #Раньше была надпись 'Node Editor > Alt + RMB' в честь того, ради чего всё; но теперь VL "повсюду"!
           'warning':"", #Надеюсь не настанет тот момент, когда у VL будет предупреждение. Неработоспособность в Linux'е была очень близко к этому.
           'category':"Node",
           'wiki_url':"https://github.com/ugorek000/VoronoiLinker/wiki", 
           'tracker_url':"https://github.com/ugorek000/VoronoiLinker/issues"}

from builtins import len as length #Я обожаю трёхбуквенные имена переменных. А без такого имени, как "len" -- мне очень грустно и одиноко... А ещё 'Vector.length'.
import bpy, ctypes, rna_keymap_ui, bl_keymap_utils
import blf, gpu, gpu_extras.batch
from math import pi, cos, sin
from mathutils import Vector as Vec
Vec2 = Col4 = Vec

import platform
from time import perf_counter, perf_counter_ns
import copy #Для VLNST.
from pprint import pprint
from bpy.types import (NodeSocket, UILayout)


from .C_Structure import BNode, View2D, SkGetLocVec
from .common_class import Equestrian, VmtData, VqmtData
from .global_var import *
from .VoronoiLinkerTool import VoronoiLinkerTool
from .VoronoiMixerTool import VoronoiMixerTool
from .VoronoiQuickMathTool import VoronoiQuickMathTool
from .VoronoiHiderTool import VoronoiHiderTool
from .VoronoiMassLinkerTool import VoronoiMassLinkerTool
from .VoronoiEnumSelectorTool import VoronoiEnumSelectorTool, VestOpBox, VestPieBox, SNA_OT_Change_Node_Domain_And_Name
from .VoronoiLinkRepeatingTool import VoronoiLinkRepeatingTool
from .VoronoiPreviewTool import VoronoiPreviewTool
from .VoronoiPreviewAnchorTool import VoronoiPreviewAnchorTool
from .VoronoiRantoTool import VoronoiRantoTool
from .VoronoiQuickDimensionsTool import VoronoiQuickDimensionsTool
from .VoronoiInterfacerTool import VoronoiInterfacerTool
from .VoronoiLinksTransferTool import VoronoiLinksTransferTool
from .VoronoiWarperTool import VoronoiWarperTool
from .VoronoiLazyNodeStencilsTool import VoronoiLazyNodeStencilsTool
from .VoronoiResetNodeTool import VoronoiResetNodeTool
from .VoronoiDummyTool import VoronoiDummyTool
from .VoronoiQuickConstant import VoronoiQuickConstant
from .VoronoiSwapperTool import VoronoiSwapperTool
from .VqmtPieMath import VqmtPieMath
from .VmMixer import VmtOpMixer, VmtPieMixer
from .VoronoiCallNodePie import VoronoiCallNodePie
from .Rot_or_Mat_Converter import Rot_or_Mat_Converter, Pie_MT_Converter_To_Rotation, Pie_MT_Converter_Rotation_To, Pie_MT_Separate_Matrix, Pie_MT_Combine_Matrix
# Rot_or_Mat_Converter 只被快速维度和常量使用


dict_classes = {} #Все подряд, которых нужно регистрировать. Через словарь -- для smart_add_to_reg_and_kmiDefs(), но чтобы сохранял порядок.
dict_vtClasses = {} #Только инструменты V*T.  #只有V*T工具。

# list_classes = []
# list_toolClasses = []

Color_Bar_Width = 0.015     # 小王 饼菜单颜色条宽度
Cursor_X_Offset = -50       # 小王 这样更舒服，在输入或输出接口方面加强


# voronoiAddonName = bl_info['name'].replace(" ","") #todo0 узнать разницу между названием аддона, именем аддона, именем файла, именем модуля, (мб ещё пакета); и ещё в установленных посмотреть.
voronoiAddonName = __package__
class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

list_kmiDefs = []
dict_setKmiCats = {'grt':set(), 'oth':set(), 'spc':set(), 'qqm':set(), 'cus':set()}

def smart_add_to_reg_and_kmiDefs(cls, txt, dict_props={}):
    dict_numToKey = {"1":'ONE', "2":'TWO', "3":'THREE', "4":'FOUR', "5":'FIVE', "6":'SIX', "7":'SEVEN', "8":'EIGHT', "9":'NINE', "0":'ZERO'}
    dict_classes[cls] = True
    dict_vtClasses[cls] = True
    list_kmiDefs.append( (cls.bl_idname, dict_numToKey.get(txt[4:], txt[4:]), txt[0]=="S", txt[1]=="C", txt[2]=="A", txt[3]=="+", dict_props) )

isWin = platform.system()=='Windows'
#isLinux = platform.system()=='Linux'

gt_blender4 = bpy.app.version[0]>=4 #Для поддержки работы в предыдущих версиях. Нужно для комфортного осознания отсутствия напрягов при вынужденных переходах на старые версии,
# и получения дополнительной порции эндорфинов от возможности работы в разных версиях с разными api.
#Todo0VV опуститься с поддержкой как можно ниже по версиям. Сейчас с гарантией: b4.0 и b4.1?

voronoiAnchorCnName = "Voronoi_Anchor" #Перевод не поддерживается, за компанию.
voronoiAnchorDtName = "Voronoi_Anchor_Dist" #Перевод не поддерживается! См. связанную топологию.
voronoiSkPreviewName = "voronoi_preview" #Перевод не поддерживается, нет желания каждое чтение обрамлять TranslateIface().
voronoiPreviewResultNdName = "SavePreviewResult" #Перевод не поддерживается за компанию.

def GetUserKmNe():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']

#Может быть стоит когда-нибудь добавить в свойства инструмента клавишу для модифицирования в процессе самого инструмента, например вариант Alt при Alt D для VQDT. Теперь ещё больше актуально для VWT.

#Где-то в комментариях могут использоваться словосочетание "тип редактора" -- то же самое что и "тип дерева"; имеются в виду 4 классических встроенных редактора, и они же, типы деревьев.

#Для некоторых инструментов есть одинаковые между собой константы, но со своими префиксами; разнесено для удобства, чтобы не "арендовать" у других инструментов.

#Актуальные нужды для VL, доступные на данный момент только(?) через ОПА:
# 1. Является ли GeoViewer активным (по заголовку) и/или активно-просматривающим прямо сейчас? (На низком уровне, а не чтение из spreadsheet)
# 2. Однозначное определение для контекста редактора, через какой именно нод на уровень выше, пользователь зашёл в текущую группу.
# 3. Как отличить общие классовые enum'ы от уникальных enum для данного нода?
# 4. Сменить для гео-Viewer'а тип поля, который он предпросматривает.
# 5. Высота макета сокета (я уже давно пожалел, что вообще добавил Draw Socket Area (от удаления этого спасает только эстетика)).
# 6. Новосозданному интерфейсу через api теперь приходиться проходить по всем существующим деревьям, и искать его "экземпляры", чтобы установить ему `default_value`; имитируя классический не-api-шный способ.
# 7. Фулл-доступ на интерфейсные панели со всеми плюшками. См. |4|.

#Таблица (теоретической) полезности инструментов в аддонских деревьях (по умолчанию -- полезно):
# VLT
# VPT    Частично
# VPAT   Частично
# VMT    Нет?
# VQMT   Нет
# VRT
# VST
# VHT
# VMLT
# VEST
# VLRT
# VQDT   Нет
# VICT   Нет!
# VLTT
# VWT
# VLNST  Нет?
# VRNT

#Todo0VV обработать все комбинации в n^3: space_data.tree_type и space_data.edit_tree.bl_idname; классическое, потерянное, и аддонское; привязанное и не привязанное к редактору.
# ^ и потом работоспособность всех инструментов в них. А потом проверить в существующем дереве взаимодействие потерянного сокета у потерянного нода для всех инструментов.

class TryAndPass():
    def __enter__(self):
        pass
    def __exit__(self, *_):
        return True

#Именования в рамках кода этого аддона:
#sk -- сокет
#skf -- сокет-интерфейс
#skin -- входной сокет (ski)
#skout -- выходной сокет (sko)
#skfin -- входной сокет-интерфейс
#skfout -- выходной сокет-интерфейс
#skfa -- коллекция интерфейсов дерева (tree.interface.items_tree), включая simrep'ы
#skft -- основа интерфейсов дерева (tree.interface)
#nd -- нод
#rr -- рероут
##
#blid -- bl_idname
#blab -- bl_label
#dnf -- identifier
##
#Неиспользуемые переменные названы с "_подчёркиванием".

dict_timeAvg = {}
dict_timeOutside = {}
#    with ToTimeNs("aaa"):
class ToTimeNs(): #Сдаюсь. Я не знаю, почему так лагает на больших деревьях. Но судя по замерам, это где-то за пределами VL.
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

#todo1v6 при активном инструменте нажатие PrtScr спамит в консоли `WARN ... pyrna_enum_to_py: ... '171' matches no enum in 'Event'`.

from bpy.app.translations import pgettext_iface as TranslateIface

dict_vlHhTranslations = {}

dict_vlHhTranslations['ru_RU'] = {'author':"ugorek",    'vl':(5,0,0), 'created':"2024.02.29", 'trans':{'a':{}, 'Op':{}}} #self
dict_vlHhTranslations['zh_CN'] = {'author':"chenpaner", 'vl':(4,0,0), 'created':"2023.12.15", 'trans':{'a':{}, 'Op':{}}} #https://github.com/ugorek000/VoronoiLinker/issues/21
#dict_vlHhTranslations['aa_AA'] = #Кто же будет вторым?. И как скоро?

for dk in dict_vlHhTranslations:
    exec(dk+f" = '{dk}'") #Когда будут языки с @variantcode (наверное никогда), тогда и можно будет париться.

class VlTrMapForKey():
    def __init__(self, key: str, *, tc='a'):
        self.key = key
        self.data = {}
        self.tc = tc
    def __enter__(self):
        return self.data
    def __exit__(self, *_):
        for dk, dv in self.data.items():
            dict_vlHhTranslations[dk]['trans'][self.tc][self.key] = dv

def TxtClsBlabToolSett(cls):
    return cls.bl_label+" tool settings"

class TranslationHelper():
    def __init__(self, dict_trans={}, lang=''):
        self.name = voronoiAddonName+"-"+lang
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


with VlTrMapForKey(bl_info['description']) as dm:
    dm["ru_RU"] = "Разнообразные помогалочки для соединения нодов, основанные на поле расстояний."
    dm["zh_CN"] = "基于距离场的多种节点连接辅助工具。"

txtAddonVer = ".".join([str(v) for v in bl_info['version']])
txt_addonVerDateCreated = f"Version {txtAddonVer} created {bl_info['created']}"
with VlTrMapForKey(txt_addonVerDateCreated) as dm:
    dm["ru_RU"] = f"Версия {txtAddonVer} создана {bl_info['created']}"
#    dm["zh_CN"] = f" {txtAddonVer}  {bl_info['created']}"
txt_addonBlVerSupporting = f"For Blender versions: {bl_info['info_supported_blvers']}"
with VlTrMapForKey(txt_addonBlVerSupporting) as dm:
    dm["ru_RU"] = f"Для версий Блендера: {bl_info['info_supported_blvers']}"
#    dm["zh_CN"] = f" {bl_info['info_supported_blvers']}"

txt_onlyFontFormat = "Only .ttf or .otf format"
with VlTrMapForKey(txt_onlyFontFormat) as dm:
    dm["ru_RU"] = "Только .ttf или .otf формат"
    dm["zh_CN"] = "只支持.ttf或.otf格式"

txt_copySettAsPyScript = "Copy addon settings as .py script"
with VlTrMapForKey(txt_copySettAsPyScript, tc='Op') as dm:
    dm["ru_RU"] = "Скопировать настройки аддона как '.py' скрипт"
    dm["zh_CN"] = "将插件设置复制为'.py'脚本,复制到粘贴板里"

txt_сheckForUpdatesYourself = "Check for updates yourself"
with VlTrMapForKey(txt_сheckForUpdatesYourself, tc='Op') as dm:
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

#Заметка для переводчиков: слова ниже в вашем языке уже могут быть переведены.
#Заметка: Оставить их для поддержки версий без них.

with VlTrMapForKey("Virtual") as dm:
    dm["ru_RU"] = "Виртуальный"
    dm["zh_CN"] = "虚拟"
with VlTrMapForKey("Restore", tc='Op') as dm:
    dm["ru_RU"] = "Восстановить"
    dm["zh_CN"] = "恢复"
with VlTrMapForKey("Add New", tc='Op') as dm:
    dm["ru_RU"] = "Добавить" #Без слова "новый"; оно не влезает, слишком тесно.
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

prefsTran = None

class TranClsItemsUtil():
    def __init__(self, tup_items):
        if type(tup_items[0])==tuple:
            self.data = dict([(li[0], li[1:]) for li in tup_items])
        else:
            self.data = tup_items
    def __getattr__(self, att):
        if type(self.data)==tuple:
            match att:
                case 'name':
                    return self.data[0]
                case 'description':
                    return self.data[1]
            assert False
        else:
            return TranClsItemsUtil(self.data[att]) #`toolProp.ENUM1.name`
    def __getitem__(self, key):
        return TranClsItemsUtil(self.data[key]) #`toolProp['ENUM1'].name`
class TranAnnotFromCls():
    def __init__(self, annot):
        self.annot = annot
    def __getattr__(self, att):
        result = self.annot.keywords[att]
        return result if att!='items' else TranClsItemsUtil(result)
def GetAnnotFromCls(cls, key): #Так вот где они прятались, в аннотациях. А я то уж потерял надежду, думал вручную придётся.
    return TranAnnotFromCls(cls.__annotations__[key])

def GetPrefsRnaProp(att, inx=-1):
    prop = prefsTran.rna_type.properties[att]
    return prop if inx==-1 else getattr(prop,'enum_items')[inx]

def CollectTranslationDict(): #Для удобства переводов, которые требуют регистрации свойств. См. BringTranslations'ы.
    global prefsTran
    prefsTran = Prefs()
    ##
    for cls in dict_vtClasses:
        cls.BringTranslations()
    VoronoiAddonPrefs.BringTranslations()
    ##
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').name) as dm:
        dm["ru_RU"] = "Пропускать через выделение нода"
        dm["zh_CN"] = "单击输出端口预览(而不是自动根据鼠标位置自动预览)"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').description) as dm:
        dm["ru_RU"] = "Клик над нодом активирует выделение, а не инструмент"
        dm["zh_CN"] = "单击输出端口才连接预览而不是根据鼠标位置动态预览"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').name) as dm:
        dm["ru_RU"] = "Может между полями"
        dm["zh_CN"] = "端口类型可以不一样"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').description) as dm:
        dm["ru_RU"] = "Инструмент может искать сокеты между различными типами полей"
#        dm["zh_CN"] = "工具可以连接不同类型的端口"?
    ##
    dict_vlHhTranslations['zh_HANS'] = dict_vlHhTranslations['zh_CN']
    for cls in dict_vtClasses:
        if (cls, 'zh_CN') in dict_toolLangSpecifDataPool:
            dict_toolLangSpecifDataPool[cls, 'zh_HANS'] = dict_toolLangSpecifDataPool[cls, 'zh_CN']

dict_toolLangSpecifDataPool = {}

def DisplayMessage(title, text, icon='NONE'):
    def PopupMessage(self, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')

def GetSkLabelName(sk):
    return sk.label if sk.label else sk.name

def CompareSkLabelName(sk1, sk2, isIgnoreCase=False):
    if isIgnoreCase:
        return GetSkLabelName(sk1).upper()==GetSkLabelName(sk2).upper()
    else:
        return GetSkLabelName(sk1)==GetSkLabelName(sk2)

def RecrGetNodeFinalLoc(nd):
    return nd.location+RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location

# def GetListOfNdEnums(nd):     # 判断节点是否有下拉列表 - 插件作者的方法
#     return [pr for pr in nd.rna_type.properties 
#                 if (pr.type == 'ENUM') and (not (pr.is_readonly or pr.is_registered)) ]
def GetListOfNdEnums(node):   # 小王-判断节点是否有下拉列表
    enum_l = []
    for p in node.rna_type.properties:
        if (p.type == 'ENUM') and (p.name != "Warning Propagation") and (not (p.is_readonly or p.is_registered)):
            enum_l.append(p)
    return enum_l
# 小王-显示节点选项优化-根据选项重命名节点-domain
# def get_node_enum_item_list_dict(node):
#     enum_dict = {}
#     for p in node.rna_type.properties:
#         if (p.type == 'ENUM') and (p.name != "Warning Propagation") and (not (p.is_readonly or p.is_registered)):
#             enum_dict[p.identifier] = [item.name for item in p.enum_items]
#     return enum_dict
def get_node_domain_item_list(node):
    enum_list = []
    for p in node.rna_type.properties:
        if p.type == 'ENUM' and p.identifier == "domain":
            enum_list = [item for item in p.enum_items]
            # enum_list = [item.identifier for item in p.enum_items]
            # enum_list = [[item.name, item.identifier] for item in p.enum_items]
    return enum_list

def SelectAndActiveNdOnly(ndTar):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar
    ndTar.select = True

def SkConvertTypeToBlid(sk):
    return dict_typeSkToBlid.get(sk.type, "Vl_Unknow")

def IsClassicSk(sk):
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return SkConvertTypeToBlid(sk) in set_classicSocketsBlid

def IsClassicTreeBlid(blid):
    return blid in set_quartetClassicTreeBlids

def SetPieData(self, toolData, prefs, col):
    def GetPiePref(name):
        return getattr(prefs, self.vlTripleName.lower()+name)
    toolData.isSpeedPie = GetPiePref("PieType")=='SPEED'
    toolData.pieScale = GetPiePref("PieScale") #todo1v6 уже есть toolData.prefs, так что можно аннигилировать; и перевозюкать всё это пограмотнее. А ещё комментарий в SolderClsToolNames().
    toolData.pieDisplaySocketTypeInfo = GetPiePref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = GetPiePref("PieDisplaySocketColor")
    toolData.pieAlignment = GetPiePref("PieAlignment")
    toolData.uiScale = self.uiScale
    toolData.prefs = prefs
    prefs.vaDecorColSkBack = col #Важно перед vaDecorColSk; см. VaUpdateDecorColSk().
    prefs.vaDecorColSk = col

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""

def VlrtRememberLastSockets(sko, ski):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        #ski без sko для VLRT бесполезен
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)
def NewLinkHhAndRemember(sko, ski):
    DoLinkHh(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)

def GetOpKmi(self, event): #Todo00 есть ли концепция или способ правильнее?
    #Оператор может иметь несколько комбинаций вызова, все из которых будут одинаковы по ключу в `keymap_items`, поэтому перебираем всех вручную
    blid = getattr(bpy.types, self.bl_idname).bl_idname
    for li in GetUserKmNe().keymap_items:
        if li.idname==blid:
            #Заметка: Искать и по соответствию самой клавише тоже, модификаторы тоже могут быть одинаковыми у нескольких вариантах вызова.
            if (li.type==event.type)and(li.shift_ui==event.shift)and(li.ctrl_ui==event.ctrl)and(li.alt_ui==event.alt):
                #Заметка: Могут быть и два идентичных хоткеев вызова, но Blender будет выполнять только один из них (по крайней мере для VL), тот, который будет первее в списке.
                return li # Эта функция также выдаёт только первого в списке.
def GetSetOfKeysFromEvent(event, isSide=False):
    set_keys = {event.type}
    if event.shift:
        set_keys.add('RIGHT_SHIFT' if isSide else 'LEFT_SHIFT')
    if event.ctrl:
        set_keys.add('RIGHT_CTRL' if isSide else 'LEFT_CTRL')
    if event.alt:
        set_keys.add('RIGHT_ALT' if isSide else 'LEFT_ALT')
    if event.oskey:
        set_keys.add('OSKEY' if isSide else 'OSKEY')
    return set_keys


def FtgGetTargetOrNone(ftg) -> NodeSocket:
    return ftg.tar if ftg else None

def MinFromFtgs(ftg1, ftg2):
    # print(type(ftg1))   # <class Fotago>
    if (ftg1)or(ftg2): #Если хотя бы один из них существует.
        if not ftg2: #Если одного из них не существует,
            return ftg1
        elif not ftg1: # то остаётся однозначный выбор для второго.
            return ftg2
        else: #Иначе выбрать ближайшего.
            return ftg1 if ftg1.dist<ftg2.dist else ftg2
    return None

def CheckUncollapseNodeAndReNext(nd, self, *, cond, flag=None): #Как же я презираю свёрнутые ноды.
    if (nd.hide)and(cond):
        nd.hide = False #Заметка: Осторожнее с вечным циклом в топологии NextAssignmentTool.
        #Алерт! type='DRAW_WIN' вызывает краш для некоторых редких деревьев со свёрнутыми нодами! Было бы неплохо забагрепортить бы это, если бы ещё знать как это отловить.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        #todo0 стоит перерисовывать только один раз, если было раскрыто несколько нодов подряд; но без нужды. Если таковое случилось, то у этого инструмента хреновая топология поиска.
        self.NextAssignmentRoot(flag)

class LyAddQuickInactiveCol():
    def __init__(self, where: UILayout, att='row', align=True, active=False):
        self.ly = getattr(where, att)(align=align)
        self.ly.active = active
    def __enter__(self):
        return self.ly
    def __exit__(self, *_):
        pass

def LyAddLeftProp(where: UILayout, who, att, active=True):
    #where.prop(who, att); return
    row = where.row()
    row.alignment = 'LEFT'
    row.prop(who, att)
    row.active = active

def LyAddDisclosureProp(where: UILayout, who, att, *, txt=None, active=True, isWide=False): #Заметка: Не может на всю ширину, если where -- row.
    tgl = getattr(who, att)
    rowMain = where.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #+":"*tgl
    rowProp.prop(who, att, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
    rowProp.active = active
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, att, text=" ", emboss=False)
    return tgl

def LyAddNoneBox(where: UILayout):
    box = where.box()
    box.label()
    box.scale_y = 0.5
def LyAddHandSplitProp(where: UILayout, who, att, *, text=None, active=True, returnAsLy=False, forceBoolean=0):
    spl = where.row().split(factor=0.42, align=True)
    spl.active = active
    row = spl.row(align=True)
    row.alignment = 'RIGHT'
    pr = who.rna_type.properties[att]
    isNotBool = pr.type!='BOOLEAN'
    isForceBoolean = not not forceBoolean
    row.label(text=pr.name*(isNotBool^isForceBoolean) if not text else text)
    if (not active)and(pr.type=='FLOAT')and(pr.subtype=='COLOR'):
        LyAddNoneBox(spl)
    else:
        if not returnAsLy:
            txt = "" if forceBoolean!=2 else ("True" if getattr(who, att) else "False")
            spl.prop(who, att, text=txt if isNotBool^isForceBoolean else None)
        else:
            return spl

def LyAddNiceColorProp(where: UILayout, who, att, align=False, txt="", ico='NONE', decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else TranslateIface(who.rna_type.properties[att].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, att, text="", icon=ico)
    rowProp.active = decor//2%2

def LyAddKeyTxtProp(where: UILayout, prefs, att):
    rowProp = where.row(align=True)
    LyAddNiceColorProp(rowProp, prefs, att)
    #Todo0 я так и не врубился как пользоваться вашими prop event'ами, жуть какая-то. Помощь извне не помешала бы.
    with LyAddQuickInactiveCol(rowProp) as row:
        row.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, att)

def LyAddLabeledBoxCol(where: UILayout, *, text="", active=False, scale=1.0, align=True):
    colMain = where.column(align=True)
    box = colMain.box()
    box.scale_y = 0.5
    row = box.row(align=True)
    row.alignment = 'CENTER'
    row.label(text=text)
    row.active = active
    box = colMain.box()
    box.scale_y = scale
    return box.column(align=align)

def LyAddTxtAsEtb(where: UILayout, txt: str):
    row = where.row(align=True)
    row.label(icon='ERROR')
    col = row.column(align=True)
    for li in txt.split("\n")[:-1]:
        col.label(text=li, translate=False)
def LyAddEtb(where: UILayout): #"Вы дебагов фиксите? Нет, только нахожу."
    import traceback
    LyAddTxtAsEtb(where, traceback.format_exc())


const_float4 = tuple[float, float, float, float]
def PowerArr4(arr: const_float4, *, pw=1/2.2): #def PowerArrToVec(arr, *, pw=1/2.2): return Vec(map(lambda a: a**pw, arr))
    return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def OpaqueCol3Tup4(col, *, al=1.0):
    return (col[0], col[1], col[2], al)
def MaxCol4Tup4(col):
    return (max(col[0], 0), max(col[1], 0), max(col[2], 0), max(col[3], 0))
def GetSkColorRaw(sk: NodeSocket):
    if sk.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        return sk.draw_color(bpy.context, sk.node) #Заметка: Если нужно будет избавиться от всех `bpy.` и пронести честный путь всех context'ов, то сначала подумать об этом.
    elif hasattr(sk,'draw_color_simple'):
        return sk.draw_color_simple()
    else:
        return (1, 0, 1, 1)
def GetSkColSafeTup4(sk: NodeSocket): #Не брать прозрачность от сокетов; и избавляться от отрицательных значений, что могут быть у аддонских сокетов.
    return OpaqueCol3Tup4(MaxCol4Tup4(GetSkColorRaw(sk)))

for key, value in dict_skTypeHandSolderingColor.items():
    dict_skTypeHandSolderingColor[key] = PowerArr4(value, pw=2.2)

class SoldThemeCols:
    dict_mapNcAtt = {0: 'input_node',        1:  'output_node',  3: 'color_node',
                     4: 'vector_node',       5:  'filter_node',  6: 'group_node',
                     8: 'converter_node',    9:  'matte_node',   10:'distor_node',
                     12:'pattern_node',      13: 'texture_node', 32:'script_node',
                     33:'group_socket_node', 40: 'shader_node',  41:'geometry_node',
                     42:'attribute_node',    100:'layout_node'}
def SolderThemeCols(themeNe):
    def GetNiceColNone(col4):
        return Col4(col4)
        # return Col4(PowerArr4(col4, pw=1/1.75))   # 小王 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
    def MixThCol(col1, col2, fac=0.4): #\source\blender\editors\space_node\node_draw.cc : node_draw_basis() : "Header"
        return col1*(1-fac)+col2*fac
    SoldThemeCols.node_backdrop4 = Col4(themeNe.node_backdrop)
    SoldThemeCols.node_backdrop4pw = GetNiceColNone(SoldThemeCols.node_backdrop4) #对于Ctrl-F：使用它，请参阅下面的“+”4PW”。Для Ctrl-F: оно используется, см ниже `+"4pw"`.

    # theme = C.preferences.themes[0].node_editor
    # getattr(theme, "attribute_node")
    # for pr in theme.bl_rna.properties:
    #     dnf = pr.identifier
    #     if dnf.endswith("_node"):
    #         print(f"{dnf = }")

    # themeNe is context.preferences.themes[0].node_editor
    # print("." * 50)
    for pr in themeNe.bl_rna.properties:
        dnf = pr.identifier
        if dnf.endswith("_node"):
            # print(f"{dnf = }")
            # print(f"{getattr(themeNe, dnf) = }")                            # type  Color
            # print(f"{OpaqueCol3Tup4(getattr(themeNe, dnf)) = }")            # type  tuple
            # print(f"{Col4(OpaqueCol3Tup4(getattr(themeNe, dnf))) = }")     # type  Vector
            # print(f" 混合后 {col4 = }")
            # 和背景混合使得偏亮
            # col4 = MixThCol(SoldThemeCols.node_backdrop4, Col4(OpaqueCol3Tup4(getattr(themeNe, dnf))))
            col4 = Col4(OpaqueCol3Tup4(getattr(themeNe, dnf)))   # 小王 解决 Ctrl Shift E / Ctrl E / Alt E 等显示太浅
            # 5.0.2里这样写的
            # col4 = MixThCol(SoldThemeCols.node_backdrop4, Col4(OpaqueCol3Tup4(getattr(themeNe, dnf))))
            setattr(SoldThemeCols, dnf+"4", col4)
            setattr(SoldThemeCols, dnf+"4pw", GetNiceColNone(col4))
            setattr(SoldThemeCols, dnf+"3", Vec(col4[:3])) #Для vptRvEeIsSavePreviewResults.
def GetNdThemeNclassCol(ndTar):
    if ndTar.bl_idname=='ShaderNodeMix':
        match ndTar.data_type:
            case 'RGBA':   return SoldThemeCols.color_node4pw
            case 'VECTOR': return SoldThemeCols.vector_node4pw
            case _:        return SoldThemeCols.converter_node4pw
    else:
        # 小王
        return getattr(SoldThemeCols, SoldThemeCols.dict_mapNcAtt.get(BNode.GetFields(ndTar).typeinfo.contents.nclass, 'node_backdrop')+"4pw")

def GetBlackAlphaFromCol(col, *, pw):
    return ( 1.0-max(max(col[0], col[1]), col[2]) )**pw


viaverSkfMethod = -1 #Переключатель-пайка под успешный способ взаимодействия. Можно было и распределить по карте с версиями, но у попытки "по факту" есть свои эстетические прелести.

#Заметка: ViaVer'ы не обновлялись.
def ViaVerNewSkf(tree, isSide, ess, name):
    if gt_blender4: #Todo1VV переосмыслить топологию; глобальные функции с методами и глобальная переменная, указывающая на успешную из них; с "полной пайкой защёлкиванием".
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        socketType = ess if type(ess)==str else SkConvertTypeToBlid(ess)
        match viaverSkfMethod:
            case 1: skf = tree.interface.new_socket(name, in_out={'OUTPUT' if isSide else 'INPUT'}, socket_type=socketType)
            case 2: skf = tree.interface.new_socket(name, in_out='OUTPUT' if isSide else 'INPUT', socket_type=socketType)
    else:
        skf = (tree.outputs if isSide else tree.inputs).new(ess if type(ess)==str else ess.bl_idname, name)
    return skf
def ViaVerGetSkfa(tree, isSide):
    if gt_blender4:
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        match viaverSkfMethod:
            case 1: return tree.interface.ui_items
            case 2: return tree.interface.items_tree
    else:
        return (tree.outputs if isSide else tree.inputs)
def ViaVerGetSkf(tree, isSide, name):
    return ViaVerGetSkfa(tree, isSide).get(name)
def ViaVerSkfRemove(tree, isSide, name):
    if gt_blender4:
        tree.interface.remove(name)
    else:
        (tree.outputs if isSide else tree.inputs).remove(name)

def index_switch_add_input(nodes, index_switch_node):
    old_active = nodes.active
    nodes.active = index_switch_node
    bpy.ops.node.index_switch_item_add()
    nodes.active = old_active
    return index_switch_node.inputs[-2]

dict_solderedSkLinksFinal = {}
def SkGetSolderedLinksFinal(self): #.vl_sold_links_final
    return dict_solderedSkLinksFinal.get(self, [])

dict_solderedSkIsFinalLinkedCount = {}
def SkGetSolderedIsFinalLinkedCount(self): #.vl_sold_is_final_linked_cou
    return dict_solderedSkIsFinalLinkedCount.get(self, 0)

def SolderSkLinks(tree):
    def Update(dict_data, lk):
        dict_data.setdefault(lk.from_socket, []).append(lk)
        dict_data.setdefault(lk.to_socket, []).append(lk)
    #dict_solderedSkLinksRaw.clear()
    dict_solderedSkLinksFinal.clear()
    dict_solderedSkIsFinalLinkedCount.clear()
    for lk in tree.links:
        #Update(dict_solderedSkLinksRaw, lk)
        if (lk.is_valid)and not(lk.is_muted or lk.is_hidden):
            Update(dict_solderedSkLinksFinal, lk)
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.from_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.from_socket] += 1
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.to_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.to_socket] += 1

def RegisterSolderings():
    txtDoc = "Property from and only for VoronoiLinker addon."
    #NodeSocket.vl_sold_links_raw = property(SkGetSolderedLinksRaw)
    NodeSocket.vl_sold_links_final = property(SkGetSolderedLinksFinal)
    NodeSocket.vl_sold_is_final_linked_cou = property(SkGetSolderedIsFinalLinkedCount)
    #NodeSocket.vl_sold_links_raw.__doc__ = txtDoc
    NodeSocket.vl_sold_links_final.__doc__ = txtDoc
    NodeSocket.vl_sold_is_final_linked_cou.__doc__ = txtDoc
def UnregisterSolderings():
    #del NodeSocket.vl_sold_links_raw
    del NodeSocket.vl_sold_links_final
    del NodeSocket.vl_sold_is_final_linked_cou

#Обеспечивает поддержку свёрнутых нодов:
#Дождались таки... Конечно же не "честную поддержку". Я презираю свёрнутые ноды; и у меня нет желания шататься с округлостью, и соответствующе изменённым рисованием.
#Так что до введения api на позицию сокета, это лучшее что есть. Ждём и надеемся.
dict_collapsedNodes = {}
def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide
#Я не стал показывать развёрнутым только ближайший нод, а сделал этакий "след".
#Чтобы всё это не превращалось в хаос с постоянным "дёрганьем", и чтобы можно было провести, раскрыть, успокоиться, увидеть "текущую обстановку", проанализировать, и спокойно соединить что нужно.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, None): #Инструменты могут создавать ноды в процессе; например vptRvEeIsSavePreviewResults.
            nd.hide = dict_collapsedNodes[nd]

class Fotago(): #Found Target Goal, "а там дальше сами разберётесь".
    #def __getattr__(self, att): #Гениально. Второе после '(*args): return Vector((args))'.
    #    return getattr(self.target, att) #Но осторожнее, оно в ~5 раз медленнее.
    def __init__(self, target, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        #self.target = target
        self.tar = target
        #self.sk = target #Fotago.sk = property(lambda a:a.target)
        #self.nd = target #Fotago.nd = property(lambda a:a.target)
        self.blid = target.bl_idname #Fotago.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        #Далее нужно только для сокетов.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text #Нужен для поддержки перевода на другие языки. Получать перевод каждый раз при рисовании слишком не комильфо, поэтому паяется.

def GenFtgFromNd(nd, pos, uiScale): #Вычленено из GetNearestNodesFtg, изначально без нужды, но VLTT вынудил.
    def DistanceField(field0, boxbou): #Спасибо RayMarching'у, без него я бы до такого не допёр.
        field1 = Vec2(( (field0.x>0)*2-1, (field0.y>0)*2-1 ))
        field0 = Vec2(( abs(field0.x), abs(field0.y) ))-boxbou/2
        field2 = Vec2(( max(field0.x, 0.0), max(field0.y, 0.0) ))
        field3 = Vec2(( abs(field0.x), abs(field0.y) ))
        field3 = field3*Vec2((field3.x<=field3.y, field3.x>field3.y))
        field3 = field3*-( (field2.x+field2.y)==0.0 )
        return (field2+field3)*field1
    isReroute = nd.type=='REROUTE'
    #Технический размер рероута явно перезаписан в 4 раза меньше, чем он есть.
    #Насколько я смог выяснить, рероут в отличие от остальных нодов свои размеры при изменении uiScale не меняет. Так что ему не нужно делиться на 'uiScale'.
    ndSize = Vec2((4, 4)) if isReroute else nd.dimensions/uiScale
    #Для нода позицию в центр нода. Для рероута позиция уже в его визуальном центре
    ndCenter = RecrGetNodeFinalLoc(nd).copy() if isReroute else RecrGetNodeFinalLoc(nd)+ndSize/2*Vec2((1.0, -1.0))
    if nd.hide: #Для VHT, "шустрый костыль" из имеющихся возможностей.
        ndCenter.y += ndSize.y/2-10 #Нужно быть аккуратнее с этой записью(write), ибо оно может оказаться указателем напрямую, если выше нодом является рероут, (https://github.com/ugorek000/VoronoiLinker/issues/16).
    #Сконструировать поле расстояний
    vec = DistanceField(pos-ndCenter, ndSize)
    #Добавить в список отработанный нод
    return Fotago(nd, dist=vec.length, pos=pos-vec)
def GetNearestNodesFtg(nodes, samplePos, uiScale, includePoorNodes=True): #Выдаёт список ближайших нод. Честное поле расстояний.
    #Почти честное. Скруглённые уголки не высчитываются. Их отсутствие не мешает, а вычисление требует больше телодвижений. Поэтому выпендриваться нет нужды.
    #С другой стороны скруглённость актуальна для свёрнутых нод, но я их презираю, так что...
    ##
    #Рамки пропускаются, ибо ни одному инструменту они не нужны.
    #Ноды без сокетов -- как рамки; поэтому можно игнорировать их ещё на этапе поиска.
    return sorted([GenFtgFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.dist)

#Уж было я хотел добавить велосипедную структуру ускорения, но потом внезапно осознал, что ещё нужна информация и о "вторых ближайших". Так что кажись без полной обработки никуда.
#Если вы знаете, как можно это ускорить с сохранением информации, поделитесь со мной.
#С другой стороны, за всё время существования аддона не было ни одной стычки с производительностью, так что... только ради эстетики.
#А ещё нужно учитывать свёрнутые ноды, пропади они пропадом, которые могут раскрыться в процессе, наворачивая всю прелесть кеширования.

def GenFtgsFromPuts(nd, isSide, samplePos, uiScale): #Вынесено для vptRvEeSksHighlighting.
    #Заметка: Эта функция сама должна получить сторону от метки, ибо `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    list_result = []
    ndDim = Vec2(nd.dimensions/uiScale) #"nd.dimensions" уже содержат в себе корректировку на масштаб интерфейса, поэтому вернуть их обратно в мир.
    for sk in nd.outputs if isSide else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (sk.enabled)and(not sk.hide):
            pos = SkGetLocVec(sk)/uiScale #Чорт возьми, это офигенно. Долой велосипедный кринж прошлых версий.
            #Но api на высоту макета у сокета тем более нет, так что остаётся только точечно-костылить; пока не придумается что-то ещё.
            hei = 0
            if (not isSide)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if "VectorDirection" in str(sk.rna_type):
                    hei = 2
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not gt_blender4) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3
            boxHeiBound = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = TranslateIface(GetSkLabelName(sk)) if sk.bl_idname!='NodeSocketVirtual' else TranslateIface("Virtual" if not sk.name else GetSkLabelName(sk))
            list_result.append(Fotago(sk, dist=(samplePos-pos).length, pos=pos, dir= 1 if sk.is_output else -1 , boxHeiBound=boxHeiBound, text=txt))
    return list_result
def GetNearestSocketsFtg(nd, samplePos, uiScale): #Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного. Всё верно, аддон назван именно из-за этого.
    #Если рероут, то имеем тривиальный вариант, не требующий вычисления; вход и выход всего одни, позиции сокетов -- он сам
    if nd.type=='REROUTE':
        loc = RecrGetNodeFinalLoc(nd)
        L = lambda a: Fotago(a, dist=(samplePos-loc).length, pos=loc, dir=1 if a.is_output else -1, boxHeiBound=(-1, -1), text=nd.label if nd.label else TranslateIface(a.name))
        return [L(nd.inputs[0])], [L(nd.outputs[0])]
    list_ftgSksIn = GenFtgsFromPuts(nd, False, samplePos, uiScale)
    list_ftgSksOut = GenFtgsFromPuts(nd, True, samplePos, uiScale)
    list_ftgSksIn.sort(key=lambda a:a.dist)
    list_ftgSksOut.sort(key=lambda a:a.dist)
    return list_ftgSksIn, list_ftgSksOut


smart_add_to_reg_and_kmiDefs(VoronoiLinkerTool, "##A_RIGHTMOUSE") #"##A_RIGHTMOUSE"?
dict_setKmiCats['grt'].add(VoronoiLinkerTool.bl_idname)

fitVltPiDescr = "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vltRepickKey:            bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    vltReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be connected to any type", default=True)
    vltDeselectAllNodes:     bpy.props.BoolProperty(name="Deselect all nodes on activate",        default=False)
    vltPriorityIgnoring:     bpy.props.BoolProperty(name="Priority ignoring",                     default=False, description=fitVltPiDescr)
    vltSelectingInvolved:    bpy.props.BoolProperty(name="Selecting involved nodes",              default=False)

with VlTrMapForKey(VoronoiLinkerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速连接"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiLinkerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiLinkerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiLinkerTool.bl_label}快速连接设置:"

dict_toolLangSpecifDataPool[VoronoiLinkerTool, "ru_RU"] = "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника."


smart_add_to_reg_and_kmiDefs(VoronoiPreviewTool, "SC#_LEFTMOUSE")
dict_setKmiCats['grt'].add(VoronoiPreviewTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vptAllowClassicGeoViewer:        bpy.props.BoolProperty(name="Allow classic GeoNodes Viewer",   default=True,  description="Allow use of classic GeoNodes Viewer by clicking on node")
    vptAllowClassicCompositorViewer: bpy.props.BoolProperty(name="Allow classic Compositor Viewer", default=False, description="Allow use of classic Compositor Viewer by clicking on node")
    vptIsLivePreview:                bpy.props.BoolProperty(name="Live Preview",                    default=True,  description="Real-time preview")
    vptRvEeIsColorOnionNodes:        bpy.props.BoolProperty(name="Node onion colors",               default=False, description="Coloring topologically connected nodes")
    vptRvEeSksHighlighting:          bpy.props.BoolProperty(name="Topology connected highlighting", default=False, description="Display names of sockets whose links are connected to a node")
    vptRvEeIsSavePreviewResults:     bpy.props.BoolProperty(name="Save preview results",            default=False, description="Create a preview through an additional node, convenient for copying")
    vptOnionColorIn:  bpy.props.FloatVectorProperty(name="Onion color entrance", default=(0.55,  0.188, 0.188), min=0, max=1, size=3, subtype='COLOR')
    vptOnionColorOut: bpy.props.FloatVectorProperty(name="Onion color exit",     default=(0.188, 0.188, 0.5),   min=0, max=1, size=3, subtype='COLOR')
    vptHlTextScale:   bpy.props.FloatProperty(name="Text scale", default=1.0, min=0.5, max=5.0)

with VlTrMapForKey(VoronoiPreviewTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速预览"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiPreviewTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiPreviewTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiPreviewTool.bl_label}快速预览设置:"

dict_toolLangSpecifDataPool[VoronoiPreviewTool, "ru_RU"] = "Канонический инструмент для мгновенного перенаправления явного вывода дерева.\nЕщё более полезен при использовании совместно с VPAT."

class VptData:
    reprSkAnchor = ""


smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':1})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':2})
smart_add_to_reg_and_kmiDefs(VoronoiPreviewAnchorTool, "SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors':2})
dict_setKmiCats['oth'].add(VoronoiPreviewAnchorTool.bl_idname) #spc?

with VlTrMapForKey(VoronoiPreviewAnchorTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi新建预览转接点"

dict_toolLangSpecifDataPool[VoronoiPreviewAnchorTool, "ru_RU"] = "Вынужденное отделение от VPT, своеобразный \"менеджер-компаньон\" для VPT.\nЯвное указание сокета и создание рероут-якорей."

class VptWayTree():
    def __init__(self, tree=None, nd=None):
        self.tree = tree
        self.nd = nd
        self.isUseExtAndSkPr = None #Оптимизация для чистки.
        self.finalLink = None #Для более адекватной организации в RvEe.
def VptGetTreesPath(nd):
    list_path = [VptWayTree(pt.node_tree, pt.node_tree.nodes.active) for pt in bpy.context.space_data.path]
    #Как я могу судить, сама суть реализации редактора узлов не хранит >нод<, через который пользователь зашёл в группу (но это не точно).
    #Поэтому если активным оказалась не нод-группа, то заменить на первый найденный-по-группе нод (или ничего, если не найдено)
    for curWy, upWy in zip(list_path, list_path[1:]):
        if (not curWy.nd)or(curWy.nd.type!='GROUP')or(curWy.nd.node_tree!=upWy.tree): #Определить отсутствие связи между глубинами.
            curWy.nd = None #Избавиться от текущего неправильного. Уж лучше останется никакой.
            for nd in curWy.tree.nodes:
                if (nd.type=='GROUP')and(nd.node_tree==upWy.tree): #Если в текущей глубине с неправильным нодом имеется нод группы с правильной группой.
                    curWy.nd = nd
                    break #Починка этой глубины успешно завершена.
    return list_path

def VptGetGeoViewerFromTree(tree):
    #Todo1PR Для очередных глубин тоже актуально получать перецепление сразу в виевер, но см. |1|, текущий конвейер логически не приспособлен для этого.
    #Поэтому больше не поддерживается, ибо "решено" только на половину. Так что старый добрый якорь в помощь.
    nameView = ""
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='SPREADSHEET':
                for space in area.spaces:
                    if space.type=='SPREADSHEET':
                        nameView = space.viewer_path.path[-1].ui_name #todo0VV
                        break
    if nameView:
        nd = tree.nodes.get(nameView)
    else:
        for nd in reversed(tree.nodes):
            if nd.type=='VIEWER':
                break #Нужен только первый попавшийся виевер, иначе будет неудобное поведение.
    if nd:
        if any(True for sk in nd.inputs[1:] if sk.vl_sold_is_final_linked_cou): #Todo1PR возможно для этого нужна опция. И в целом здесь бардак с этим виевером.
            return nd #Выбирать виевер только если у него есть линк для просмотра поля.
    return None

def VptGetRootNd(tree):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            for nd in tree.nodes:
                if (nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD', 'OUTPUT_LIGHT', 'OUTPUT_LINESTYLE',
                                'OUTPUT'}) and (nd.is_active_output):
                    return nd
                if nd.type == 'NPR_OUTPUT':  # 小王-npr预览
                    return nd
        case 'GeometryNodeTree':
            if nd:=VptGetGeoViewerFromTree(tree):
                return nd
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    for sk in nd.inputs:
                        if sk.type=='GEOMETRY':
                            return nd
        case 'CompositorNodeTree':
            for nd in tree.nodes:
                if nd.type=='VIEWER':
                    return nd
            for nd in tree.nodes:
                if nd.type=='COMPOSITE':
                    return nd
        case 'TextureNodeTree':
            for nd in tree.nodes:
                if nd.type=='OUTPUT':
                    return nd
    return None
def VptGetRootSk(tree, ndRoot, skTar):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            inx = 0
            if ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD'}:
            # if ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD', 'NPR_OUTPUT'}:   # 小王-npr预览
                inx =  (skTar.name=="Volume")or(ndRoot.inputs[0].hide)
            else:
                for node in tree.nodes:
                    if node.type == 'NPR_OUTPUT':
                        return node.inputs[0]
            return ndRoot.inputs[inx]
        case 'GeometryNodeTree':
            for sk in ndRoot.inputs:
                if sk.type=='GEOMETRY':
                    return sk
    return ndRoot.inputs[0] #Заметка: Здесь также окажется неудачный от GeometryNodeTree выше.

vptFeatureUsingExistingPath = True
#Заметка: Интерфейсы симуляции и зоны повторения не рассматривать, их обработка потребует поиска по каждому ноду в дереве, отчего будет BigO алерт.
#Todo1PR нужно всё снова перелизать; но прежде сделать тесты на все возможные комбинации глубин, якорей, геовиевера, отсутствия нод, "уже-путей", и прочих прелестей (а ещё аддонские деревья), и ещё местные BigO.
def DoPreviewCore(skTar, list_distAnchs, cursorLoc):
    def NewLostNode(type, ndTar=None):
        ndNew = tree.nodes.new(type)
        if ndTar:
            ndNew.location = ndTar.location
            ndNew.location.x += ndTar.width*2
        return ndNew
    list_way = VptGetTreesPath(skTar.node)
    higWay = length(list_way)-1
    list_way[higWay].nd = skTar.node #Подразумеваемым гарантией-конвейером глубин заходов целевой не обрабатывается, поэтому указывать явно. (не забыть перевести с эльфийского на русский)
    ##
    previewSkType = "RGBA" #Цвет, а не шейдер -- потому что иногда есть нужда вставить нод куда-то на пути предпросмотра.
    #Но если линки шейдерные -- готовьтесь к разочарованию. Поэтому цвет (кой и был изначально у NW).
    isGeoTree = list_way[0].tree.bl_idname=='GeometryNodeTree'
    if isGeoTree:
        previewSkType = "GEOMETRY"
    elif skTar.type=='SHADER':
        previewSkType = "SHADER"
    dnfLastSkEx = '' #Для vptFeatureUsingExistingPath.
    def GetBridgeSk(puts):
        sk = puts.get(voronoiSkPreviewName)
        if (sk)and(sk.type!=previewSkType):
            ViaVerSkfRemove(tree, True, ViaVerGetSkf(tree, True, voronoiSkPreviewName))
            return None
        return sk
    def GetTypeSkfBridge():
        match previewSkType:
            case 'GEOMETRY': return "NodeSocketGeometry"
            case 'SHADER':   return "NodeSocketShader"
            case 'RGBA':     return "NodeSocketColor"
    ##
    isInClassicTrees = IsClassicTreeBlid(skTar.id_data.bl_idname)
    for cyc in reversed(range(higWay+1)):
        curWay = list_way[cyc]
        tree = curWay.tree
        #Определить отправляющий нод:
        portalNdFrom = curWay.nd #skTar.node уже включён в путь для cyc==higWay.
        isCreatedNgOut = False
        if not portalNdFrom:
            portalNdFrom = tree.nodes.new(tree.bl_idname.replace("Tree","Group"))
            portalNdFrom.node_tree = list_way[cyc+1].tree
            isCreatedNgOut = True #Чтобы установить позицию нода от принимающего нода, который сейчас неизвестен.
        assert portalNdFrom
        #Определить принимающий нод:
        portalNdTo = None
        if not cyc: #Корень.
            portalNdTo = VptGetRootNd(tree)
            if (not portalNdTo)and(isInClassicTrees):
                #"Визуальное оповещение", что соединяться некуда. Можно было бы и вручную добавить, но лень шататься с принимающими нодами ShaderNodeTree'а.
                portalNdTo = NewLostNode('NodeReroute', portalNdFrom) #"У меня лапки".
        else: #Очередная глубина.
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    portalNdTo = nd
                    break
            if not portalNdTo:
                #Создать вывод группы самостоятельно, вместо того чтобы остановиться и не знать что делать.
                portalNdTo = NewLostNode('NodeGroupOutput', portalNdFrom)
            if isGeoTree:
                #Теперь поведение наличия виевера похоже на якорь.
                if nd:=VptGetGeoViewerFromTree(tree):
                    portalNdTo = nd
        if isCreatedNgOut:
            portalNdFrom.location = portalNdTo.location-Vec2((portalNdFrom.width+40, 0))
        assert portalNdTo or not isInClassicTrees
        #Определить отправляющий сокет:
        portalSkFrom = None
        if (vptFeatureUsingExistingPath)and(dnfLastSkEx):
            for sk in portalNdFrom.outputs:
                if sk.identifier==dnfLastSkEx:
                    portalSkFrom = sk
                    break
            dnfLastSkEx = '' #Важно обнулять. Выбранный сокет может не иметь линков или связи до следующего портала, отчего на следующей глубине будут несоответствия.
        if not portalSkFrom:
            if cyc==higWay:
                portalSkFrom = skTar
            else:
                try:
                    portalSkFrom = GetBridgeSk(portalNdFrom.outputs)
                except:
                    return list_way
        assert portalSkFrom
        #Определить принимающий сокет:
        portalSkTo = None
        if (isGeoTree)and(portalNdTo.type=='VIEWER'):
            portalSkTo = portalNdTo.inputs[0]
        if (not portalSkTo)and(vptFeatureUsingExistingPath)and(cyc): #Имеет смысл записывать для не-корня.
            #Моё улучшающее изобретение -- если соединение уже имеется, то зачем создавать рядом такое же?.
            #Это эстетически комфортно, а также помогает очистить последствия предпросмотра не выходя из целевой глубины (добавлены условия, см. чистку).
            for lk in portalSkFrom.vl_sold_links_final:
                #Поскольку интерфейсы не удаляются, вместо мейнстрима ниже он заполучится отсюда (и результат будет таким же), поэтому вторая проверка для isUseExtAndSkPr.
                if (lk.to_node==portalNdTo)and(lk.to_socket.name!=voronoiSkPreviewName):
                    portalSkTo = lk.to_socket
                    dnfLastSkEx = portalSkTo.identifier #Выходы нода нод-группы и входы выхода группы совпадают. Сохранить информацию для следующей глубины продолжения.
                    curWay.isUseExtAndSkPr = GetBridgeSk(portalNdTo.inputs) #Для чистки. Если будет без линков, то удалять. При чистке они не ищутся по факту, потому что BigO.
        if (not portalSkTo)and(isInClassicTrees): #Основной мейнстрим получения.
            portalSkTo = VptGetRootSk(tree, portalNdTo, skTar) if not cyc else GetBridgeSk(portalNdTo.inputs) #|1|.
        if (not portalSkTo)and(cyc): #Очередные глубины -- всегда группы, для них и нужно генерировать skf. Проверка на `cyc` не обязательна, сокет с корнем (из-за рероута) всегда будет.
            #Если выше не смог получить сокет от входов нода нод группы, то и интерфейса-то тоже нет. Поэтому проверка `not tree.outputs.get(voronoiSkPreviewName)` без нужды.
            ViaVerNewSkf(tree, True, GetTypeSkfBridge(), voronoiSkPreviewName).hide_value = True
            portalSkTo = GetBridgeSk(portalNdTo.inputs) #Перевыбрать новосозданный.
        #Обработка якоря, мимикрирующего под явное указание канонического вывода:
        if (cyc==higWay)and(VptData.reprSkAnchor):
            skAnchor = None
            try:
                skAnchor = eval(VptData.reprSkAnchor)
                if skAnchor.id_data!=skTar.id_data:
                    skAnchor = None
                    VptData.reprSkAnchor = ""
            except:
                VptData.reprSkAnchor = ""
            if (skAnchor):#and(skAnchor.node!=skTar.node):
                portalSkTo = skAnchor
        assert portalSkTo or not isInClassicTrees
        #Соединить:
        ndAnchor = tree.nodes.get(voronoiAnchorCnName)
        if (cyc==higWay)and(not ndAnchor)and(list_distAnchs): #Ближайший ищется от курсора; где-же взять курсор для нецелевых глубин?.
            min = 32768
            for nd in list_distAnchs:
                len = (nd.location-cursorLoc).length
                if min>len:
                    min = len
                    ndAnchor = nd
        if ndAnchor: #Якорь делает "планы изменились", и пересасывает поток на себя.
            lk = tree.links.new(portalSkFrom, ndAnchor.inputs[0])
            # print(f"0 {ndAnchor = }")
            #tree.links.new(ndAnchor.outputs[0], portalSkTo)
            curWay.finalLink = lk
            break #Завершение после напарывания повышает возможности использования якоря, делая его ещё круче. Если у вас течка от Voronoi_Anchor, то я вас понимаю. У меня тоже.
            #Завершение позволяет иметь пользовательское соединение от глубины с якорем и до корня, не разрушая их.
        elif (portalSkFrom)and(portalSkTo): #assert portalSkFrom and portalSkTo #Иначе обычное соединение маршрута.
            lk = tree.links.new(portalSkFrom, portalSkTo)
            # view_node = portalSkTo.node       # 小王-想让预览器自动激活
            # if view_node.bl_idname == "GeometryNodeViewer":
            #     view_node.hide = True
            #     print(f"1 {view_node.bl_idname = }")
            curWay.finalLink = lk
    return list_way
def VptPreviewFromSk(self, prefs, skTar):
    if not(skTar and skTar.is_output):
        return
    list_way = DoPreviewCore(skTar, self.list_distanceAnchors, self.cursorLoc)
    if self.isSelectingPreviewedNode:
        SelectAndActiveNdOnly(skTar.node) #Важно не только то, что только один он выделяется, но ещё и то, что он становится активным.
    if not self.isInvokeInClassicTree:
        return
    #Гениально я придумал удалять интерфейсы после предпросмотра; стало возможным благодаря не-удалению в контекстных путях. Теперь ими можно будет пользоваться более свободно.
    if (True)or(not self.tree.nodes.get(voronoiAnchorCnName)): #Про 'True' читать ниже.
        #Если в текущем дереве есть якорь, то никаких voronoiSkPreviewName не удалять; благодаря чему становится доступным ещё одно особое использование инструмента.
        #Должно было стать логическим продолжением после "завершение после напарывания", но допёр до этого только сейчас.
        #P.s. Я забыл нахрен какое. А теперь они не удаляются от контекстных путей, так что теперь информация утеряна D:
        dict_treeNext = dict({(wy.tree, wy.isUseExtAndSkPr) for wy in list_way})
        dict_treeOrder = dict({(wy.tree, cyc) for cyc, wy in enumerate(reversed(list_way))}) #Путь имеет линки, середине не узнать о хвосте, поэтому из текущей глубины до корня, чтобы "каскадом" корректно обработалось.
        for ng in sorted(bpy.data.node_groups, key=lambda a: dict_treeOrder.get(a,-1)):
            #Удалить все свои следы предыдущего использования инструмента для всех нод-групп, чей тип текущего редактора такой же.
            if ng.bl_idname==self.tree.bl_idname:
                #Но не удалять мосты для деревьев контекстного пути (удалять, если их сокеты пустые).
                sk = dict_treeNext.get(ng, None) #Для Ctrl-F: isUseExtAndSkPr используется здесь.
                if (ng not in dict_treeNext)or((not sk.vl_sold_is_final_linked_cou) if sk else None)or( (ng==self.tree)and(sk) ):
                    sk = True
                    while sk: #Ищется по имени. Пользователь может сделать дубликат, от чего без while они будут исчезать по одному каждую активацию предпросмотра.
                        sk = ViaVerGetSkf(ng, True, voronoiSkPreviewName)
                        if sk:
                            ViaVerSkfRemove(ng, True, sk)
    if (prefs.vptRvEeIsSavePreviewResults)and(not self.isAnyAncohorExist): #Помощь в реверс-инженеринге -- сохранять текущий сокет просмотра для последующего "менеджмента".
        def GetTypeOfNodeSave(sk):
            match sk.type:
                case 'GEOMETRY': return 2
                case 'SHADER': return 1
                case _: return 0
        finalLink = list_way[-1].finalLink
        idSave = GetTypeOfNodeSave(finalLink.from_socket)
        pos = finalLink.to_node.location
        pos = (pos[0]+finalLink.to_node.width+40, pos[1])
        ndRvSave = self.tree.nodes.get(voronoiPreviewResultNdName)
        if ndRvSave:
            if ndRvSave.label!=voronoiPreviewResultNdName:
                ndRvSave.name += "_"+ndRvSave.label
                ndRvSave = None
            elif GetTypeOfNodeSave(ndRvSave.outputs[0])!=idSave: #Если это нод от другого типа сохранения.
                pos = ndRvSave.location.copy() #При смене типа сохранять позицию "активного" нода-сохранения. Заметка: Не забывать про .copy(), потому что далее нод удаляется.
                self.tree.nodes.remove(ndRvSave)
                ndRvSave = None
        if not ndRvSave:
            match idSave:
                case 0: txt = "MixRGB" #Потому что он может быть во всех редакторах; а ещё Shift+G > Type.
                case 1: txt = "AddShader"
                case 2: txt = "SeparateGeometry" #Нужен нод с минимальным влияем (нагрузкой) и поддерживающим все типы геометрии, (и без мультиинпутов).
            ndRvSave = self.tree.nodes.new(self.tree.bl_idname.replace("Tree","")+txt)
            ndRvSave.location = pos
        ndRvSave.name = voronoiPreviewResultNdName
        ndRvSave.select = False
        ndRvSave.label = ndRvSave.name
        ndRvSave.use_custom_color = True
        #Разукрасить нод сохранения
        match idSave:
            case 0:
                ndRvSave.color = SoldThemeCols.color_node3
                ndRvSave.show_options = False
                ndRvSave.blend_type = 'ADD'
                ndRvSave.inputs[0].default_value = 0
                ndRvSave.inputs[1].default_value = PowerArr4(SoldThemeCols.color_node4, pw=2.2)
                ndRvSave.inputs[2].default_value = ndRvSave.inputs[1].default_value #Немного лишнее.
                ndRvSave.inputs[0].hide = True
                ndRvSave.inputs[1].name = "Color"
                ndRvSave.inputs[2].hide = True
            case 1:
                ndRvSave.color = SoldThemeCols.shader_node3
                ndRvSave.inputs[1].hide = True
            case 2:
                ndRvSave.color = SoldThemeCols.geometry_node3
                ndRvSave.show_options = False
                ndRvSave.inputs[1].hide = True
                ndRvSave.outputs[0].name = "Geometry"
                ndRvSave.outputs[1].hide = True
        self.tree.links.new(finalLink.from_socket, ndRvSave.inputs[not idSave])
        self.tree.links.new(ndRvSave.outputs[0], finalLink.to_socket)


smart_add_to_reg_and_kmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") #Миксер перенесён на левую, чтобы освободить нагрузку для VQMT.
dict_setKmiCats['grt'].add(VoronoiMixerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmtReroutesCanInAnyType:  bpy.props.BoolProperty(name="Reroutes can be mixed to any type", default=True)
    ##
    vmtPieType:               bpy.props.EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vmtPieScale:              bpy.props.FloatProperty(name="Pie scale",                default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vmtPieAlignment:          bpy.props.IntProperty(  name="Alignment between items",  default=1,   min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vmtPieSocketDisplayType:  bpy.props.IntProperty(  name="Display socket type info", default=1,   min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vmtPieDisplaySocketColor: bpy.props.IntProperty(  name="Display socket color",     default=-1,  min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")

with VlTrMapForKey(VoronoiMixerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速混合"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiMixerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiMixerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiMixerTool.bl_label}快速混合设置:"

dict_toolLangSpecifDataPool[VoronoiMixerTool, "ru_RU"] = "Канонический инструмент для частых нужд смешивания.\nСкорее всего 70% уйдёт на использование \"Instance on Points\"."

with VlTrMapForKey("Switch  ") as dm:
    dm["ru_RU"] = "Переключение"
with VlTrMapForKey("Mix  ") as dm:
    dm["ru_RU"] = "Смешивание"
with VlTrMapForKey("Compare  ") as dm:
    dm["ru_RU"] = "Сравнение"


dict_classes[VmtOpMixer] = True
dict_classes[VmtPieMixer] = True


smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_RIGHTMOUSE") #Осталось на правой, чтобы не охреневать от тройного клика левой при 'Speed Pie' типе пирога.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_ACCENT_GRAVE", {'isRepeatLastOperation':True})
#Список быстрых операций для быстрой математики ("x2 комбо"):
#Дилемма с логическим на "3", там может быть вычитание, как все на этой клавише, или отрицание, как логическое продолжение первых двух. Во втором случае булеан на 4 скорее всего придётся делать никаким.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_1", {'quickOprFloat':'ADD',      'quickOprVector':'ADD',      'quickOprBool':'OR',     'quickOprColor':'ADD'     })
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_2", {'quickOprFloat':'SUBTRACT', 'quickOprVector':'SUBTRACT', 'quickOprBool':'NIMPLY', 'quickOprColor':'SUBTRACT'})
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_3", {'quickOprFloat':'MULTIPLY', 'quickOprVector':'MULTIPLY', 'quickOprBool':'AND',    'quickOprColor':'MULTIPLY'})
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "##A_4", {'quickOprFloat':'DIVIDE',   'quickOprVector':'DIVIDE',   'quickOprBool':'NOT',    'quickOprColor':'DIVIDE'  })
#Хотел я реализовать это для QuickMathMain, но оказалось слишком лажа превращать технический оператор в пользовательский. Основная проблема -- VqmtData настроек пирога.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_1", {'justPieCall':1}) #Неожиданно, но такой хоткей весьма приятный в использовании.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_2", {'justPieCall':2}) # Из-за наличия двух модификаторов приходится держать нажатым,
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_3", {'justPieCall':3}) # от чего приходится выбирать позицией курсора, а не кликом.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_4", {'justPieCall':4}) # Я думал это будет неудобно, а оказалось даже приятно.
smart_add_to_reg_and_kmiDefs(VoronoiQuickMathTool, "S#A_5", {'justPieCall':5}) # 整数饼菜单
dict_setKmiCats['grt'].add(VoronoiQuickMathTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vqmtDisplayIcons:          bpy.props.BoolProperty(name="Display icons",           default=True)
    vqmtIncludeThirdSk:        bpy.props.BoolProperty(name="Include third socket",    default=True)
    vqmtIncludeQuickPresets:   bpy.props.BoolProperty(name="Include quick presets",   default=False)
    vqmtIncludeExistingValues: bpy.props.BoolProperty(name="Include existing values", default=False)
    vqmtRepickKey: bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    ##
    vqmtPieType:               bpy.props.EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vqmtPieScale:              bpy.props.FloatProperty(name="Pie scale",                default=1.3,  min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieScaleExtra:         bpy.props.FloatProperty(name="Pie scale extra",          default=1.25, min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieAlignment:          bpy.props.IntProperty(  name="Alignment between items",  default=1,    min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vqmtPieSocketDisplayType:  bpy.props.IntProperty(  name="Display socket type info", default=1,    min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vqmtPieDisplaySocketColor: bpy.props.IntProperty(  name="Display socket color",     default=-1,   min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")

with VlTrMapForKey(VoronoiQuickMathTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速数学运算"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiQuickMathTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiQuickMathTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiQuickMathTool.bl_label}快速数学运算设置:"

dict_toolLangSpecifDataPool[VoronoiQuickMathTool, "ru_RU"] = """Полноценное ответвление от VMT. Быстрая и быстрая быстрая математика на спидах.
Имеет дополнительный мини-функционал. Также см. \"Quick quick math\" в раскладе."""


dict_classes[VqmtOpMain] = True
dict_classes[VqmtPieMath] = True


smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "###_R")
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "S##_R", {'isAccumulate':True})
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#C#_R", {'isOnlySelected':2})
smart_add_to_reg_and_kmiDefs(VoronoiRantoTool, "#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True})
dict_setKmiCats['spc'].add(VoronoiRantoTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vrtIsLiveRanto:  bpy.props.BoolProperty(name="Live Ranto", default=True)
    vrtIsFixIslands: bpy.props.BoolProperty(name="Fix islands", default=True)

with VlTrMapForKey(VoronoiRantoTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi节点自动排布对齐"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiRantoTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiRantoTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiRantoTool.bl_label}节点自动排布对齐工具设置:"

dict_toolLangSpecifDataPool[VoronoiRantoTool, "ru_RU"] = "Сейчас этот инструмент не более чем пустышка.\nСтанет доступным, когда VL стяжет свои заслуженные(?) лавры популярности."

#Теперь RANTO интегрирован в VL. Неожиданно даже для меня.
#См. оригинал: https://github.com/ugorek000/RANTO

class RantoData():
    def __init__(self, isOnlySelected=0, widthNd=140, isUniWid=False, indentX=40, indentY=30, isIncludeMutedLinks=False, isIncludeNonValidLinks=False, isFixIslands=True):
        self.kapibara = ""
        self.dict_ndTopoWorking = {}

def VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, ndRoot):
    rada.kapibara = "kapibara"


smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':'ADD'})
smart_add_to_reg_and_kmiDefs(VoronoiSwapperTool, "S#A_S", {'toolMode':'TRAN'})
dict_setKmiCats['oth'].add(VoronoiSwapperTool.bl_idname)

with VlTrMapForKey(VoronoiSwapperTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速替换端口"

dict_toolLangSpecifDataPool[VoronoiSwapperTool, "ru_RU"] = """Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.
Для линка обмена не будет, если в итоге он окажется исходящим из своего же нода."""
dict_toolLangSpecifDataPool[VoronoiSwapperTool, "zh_CN"] = "Alt是批量替换输出端口,Shift是互换端口"


smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "#CA_E", {'toolMode':'SOCKETVAL'})
smart_add_to_reg_and_kmiDefs(VoronoiHiderTool, "SC#_E", {'toolMode':'NODE'})
dict_setKmiCats['oth'].add(VoronoiHiderTool.bl_idname)


smart_add_to_reg_and_kmiDefs(VoronoiCallNodePie, "#C#_LEFTMOUSE")
dict_setKmiCats['oth'].add(VoronoiCallNodePie.bl_idname)


list_itemsProcBoolSocket = [('ALWAYS',"Always","Always"), ('IF_FALSE',"If false","If false"), ('NEVER',"Never","Never"), ('IF_TRUE',"If true","If true")]

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vhtHideBoolSocket:       bpy.props.EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=list_itemsProcBoolSocket)
    vhtHideHiddenBoolSocket: bpy.props.EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=list_itemsProcBoolSocket)
    vhtNeverHideGeometry:    bpy.props.EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False",""), ('ONLY_FIRST',"Only first",""), ('TRUE',"True","") ))
    vhtIsUnhideVirtual:      bpy.props.BoolProperty(name="Unhide virtual sockets",           default=True)
    vhtIsToggleNodesOnDrag:  bpy.props.BoolProperty(name="Toggle nodes on drag",             default=True)

with VlTrMapForKey(VoronoiHiderTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速隐藏"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiHiderTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiHiderTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiHiderTool.bl_label}快速隐藏端口设置:"

dict_toolLangSpecifDataPool[VoronoiHiderTool, "ru_RU"] = "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов."
dict_toolLangSpecifDataPool[VoronoiHiderTool, "zh_CN"] = "Shift是自动隐藏数值为0/颜色纯黑/未连接的端口,Ctrl是单个隐藏端口"

def HideFromNode(prefs, ndTarget, lastResult, isCanDo=False): #Изначально лично моя утилита, была создана ещё до VL.
    set_equestrianHideVirtual = {'GROUP_INPUT','SIMULATION_INPUT','SIMULATION_OUTPUT','REPEAT_INPUT','REPEAT_OUTPUT'}
    scoGeoSks = 0 #Для CheckSkZeroDefaultValue().
    def CheckSkZeroDefaultValue(sk): #Shader и Virtual всегда True, Geometry от настроек аддона.
        match sk.type: #Отсортированы в порядке убывания сложности.
            case 'GEOMETRY':
                match prefs.vhtNeverHideGeometry: #Задумывалось и для out тоже, но как-то леновато, а ещё `GeometryNodeBoundBox`, так что...
                    case 'FALSE': return True
                    case 'TRUE': return False
                    case 'ONLY_FIRST':
                        nonlocal scoGeoSks
                        scoGeoSks += 1
                        return scoGeoSks!=1
            case 'VALUE':
                #Todo1v6 когда приспичит, или будет нечем заняться -- добавить список настраиваемых точечных сокрытий, через оценку с помощью питона.
                # ^ словарь[блид сокета]:{множество имён}. А ещё придумать, как пронести default_value.
                if (GetSkLabelName(sk) in {'Alpha', 'Factor'})and(sk.default_value==1): #Для некоторых float сокетов тоже было бы неплохо иметь точечную проверку.
                    return True
                return sk.default_value==0
            case 'VECTOR':
                if (GetSkLabelName(sk)=='Scale')and(sk.default_value[0]==1)and(sk.default_value[1]==1)and(sk.default_value[2]==1):
                    return True #Меня переодически напрягал 'GeometryNodeTransform', и в один прекрасной момент накопилось..
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #Заметка: `sk.default_value==(0,0,0)` не прокатит.
            case 'BOOLEAN':
                if not sk.hide_value: #Лень паять, всё обрабатывается в прямом виде.
                    match prefs.vhtHideBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match prefs.vhtHideHiddenBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
            case 'RGBA':
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #4-й компонент игнорируются, может быть любым.
            case 'INT':
                return sk.default_value==0
            case 'STRING'|'OBJECT'|'MATERIAL'|'COLLECTION'|'TEXTURE'|'IMAGE': #Заметка: STRING не такой же, как и остальные, но имеет одинаковую обработку.
                return not sk.default_value
            # 小王-自动隐藏接口优化-旋转接口
            case 'ROTATION':
                euler = sk.default_value
                return euler[0] == 0 and euler[1] == 0 and euler[2] == 0
            # 小王-自动隐藏接口优化-inline
            case _:
                return True
    if lastResult: #Результат предыдущего анализа, есть ли сокеты чьё состояние изменилось бы. Нужно для 'isCanDo'.
        def CheckAndDoForIo(puts, LMainCheck):
            success = False
            for sk in puts:
                if (sk.enabled)and(not sk.hide)and(not sk.vl_sold_is_final_linked_cou)and(LMainCheck(sk)): #Ядро сокрытия находится здесь, в первых двух проверках.
                    success |= not sk.hide #Здесь success означает будет ли оно скрыто.
                    if isCanDo:
                        sk.hide = True
            return success
        #Если виртуальные были созданы вручную, то не скрывать их. Потому что. Но если входов групп больше одного, то всё равно скрывать.
        #Изначальный смысл LVirtual -- "LCheckOver" -- проверка "над", точечные дополнительные условия. Но в ней скопились только для виртуальных, поэтому переназвал.
        isMoreNgInputs = False if ndTarget.type!='GROUP_INPUT' else length([True for nd in ndTarget.id_data.nodes if nd.type=='GROUP_INPUT'])>1
        LVirtual = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and #Смысл этой Labmda -- точечное не-сокрытие для тех, которые виртуальные,
                                   (sk.node.type in {'GROUP_INPUT','GROUP_OUTPUT'})and # у io-всадников,
                                   (sk!=( sk.node.outputs if sk.is_output else sk.node.inputs )[-1])and # и не последние (то ради чего),
                                   (not isMoreNgInputs) ) # и GROUP_INPUT в дереве всего один.
        #Ядро в трёх строчках ниже:
        success = CheckAndDoForIo(ndTarget.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LVirtual(sk)) ) #Для входов мейнстримная проверка их значений, и дополнительно виртуальные.
        a = [True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)]
        if any(True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)): #Если хотя бы один сокет подсоединён вовне
            success |= CheckAndDoForIo(ndTarget.outputs, lambda sk: LVirtual(sk) ) #Для выводов актуально только проверка виртуальных, если их нодом оказался всадник.
        else:
            #Всё равно переключать последний виртуальный, даже если нет соединений вовне.
            if ndTarget.type in set_equestrianHideVirtual: #Заметка: 'GROUP_OUTPUT' бесполезен, у него всё прячется по значению.
                if ndTarget.outputs: #Вместо for, чтобы читать из последнего.
                    sk = ndTarget.outputs[-1]
                    if sk.bl_idname=='NodeSocketVirtual':
                        success |= not sk.hide #Так же, как и в CheckAndDoForIo().
                        if isCanDo:
                            sk.hide = True
        return success #Урожай от двух CheckAndDoForIo() изнутри.
    elif isCanDo: #Иначе раскрыть всё.
        success = False
        for puts in [ndTarget.inputs, ndTarget.outputs]:
            for sk in puts:
                success |= sk.hide #Здесь success означает будет ли оно раскрыто.
                sk.hide = (sk.bl_idname=='NodeSocketVirtual')and(not prefs.vhtIsUnhideVirtual)
        return success


smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
smart_add_to_reg_and_kmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})
dict_setKmiCats['oth'].add(VoronoiMassLinkerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmltIgnoreCase: bpy.props.BoolProperty(name="Ignore case", default=True)

with VlTrMapForKey(VoronoiMassLinkerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi根据端口名批量快速连接"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiMassLinkerTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiMassLinkerTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiMassLinkerTool.bl_label}根据端口名批量连接设置:"

dict_toolLangSpecifDataPool[VoronoiMassLinkerTool, "ru_RU"] = """"Малыш котопёс", не ноды, не сокеты. Создан ради редких точечных спец-ускорений.
VLT на максималках. В связи со своим принципом работы, по своему божественен."""



#Изначально хотел 'V_Sca', но слишком далеко тянуться пальцем до V. И вообще, учитывая причину создания этого инструмента, нужно минимизировать сложность вызова.
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_R", {'isPieChoice':True, 'isSelectNode':3})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "#C#_E", {'isInstantActivation':False})
smart_add_to_reg_and_kmiDefs(VoronoiEnumSelectorTool, "##A_E", {'isToggleOptions':True})
dict_setKmiCats['oth'].add(VoronoiEnumSelectorTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vestIsToggleNodesOnDrag: bpy.props.BoolProperty(name="Toggle nodes on drag", default=True)
    ##
    vestBoxScale:            bpy.props.FloatProperty(name="Box scale",           default=1.3, min=1.0, max=2.0, subtype="FACTOR")
    vestDisplayLabels:       bpy.props.BoolProperty(name="Display enum names",   default=True)
    vestDarkStyle:           bpy.props.BoolProperty(name="Dark style",           default=False)

with VlTrMapForKey(VoronoiEnumSelectorTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速切换节点内部下拉列表"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiEnumSelectorTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiEnumSelectorTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiEnumSelectorTool.bl_label}快速显示节点里下拉列表设置:"

dict_toolLangSpecifDataPool[VoronoiEnumSelectorTool, "ru_RU"] = """Инструмент для удобно-ленивого переключения свойств перечисления.
Избавляет от прицеливания мышкой, клика, а потом ещё одного прицеливания и клика."""



dict_classes[SNA_OT_Change_Node_Domain_And_Name] = True



dict_classes[VestOpBox] = True
dict_classes[VestPieBox] = True

#См.: VlrtData, VlrtRememberLastSockets() и NewLinkHhAndRemember().



smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "###_V", {'toolMode':'SOCKET'})
smart_add_to_reg_and_kmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'toolMode':'NODE'})
dict_setKmiCats['oth'].add(VoronoiLinkRepeatingTool.bl_idname)

with VlTrMapForKey(VoronoiLinkRepeatingTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi重复连接到上次用快速连接到的输出端" #dm["zh_CN"] = "Voronoi快速恢复连接"

dict_toolLangSpecifDataPool[VoronoiLinkRepeatingTool, "ru_RU"] = """Полноценное ответвление от VLT, повторяет любой предыдущий линк от большинства
других инструментов. Обеспечивает удобство соединения "один ко многим"."""


smart_add_to_reg_and_kmiDefs(VoronoiQuickDimensionsTool, "##A_D")
dict_setKmiCats['spc'].add(VoronoiQuickDimensionsTool.bl_idname)

with VlTrMapForKey(VoronoiQuickDimensionsTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速分离/合并 矢量/颜色"

dict_toolLangSpecifDataPool[VoronoiQuickDimensionsTool, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."


dict_classes[rot_or_mat_converter] = True
dict_classes[Pie_MT_Converter_To_Rotation] = True
dict_classes[Pie_MT_Converter_Rotation_To] = True
dict_classes[Pie_MT_Separate_Matrix] = True
dict_classes[Pie_MT_Combine_Matrix] = True


smart_add_to_reg_and_kmiDefs(VoronoiQuickConstant, "##A_C")
dict_setKmiCats['spc'].add(VoronoiQuickConstant.bl_idname)

with VlTrMapForKey(VoronoiQuickConstant.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速常量"

dict_toolLangSpecifDataPool[VoronoiQuickConstant, "ru_RU"] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."


def FindAnySk(nd, list_ftgSksIn, list_ftgSksOut): #Todo0NA нужно обобщение!, с лямбдой. И внешний цикл по спискам, а не два цикла.
    ftgSkOut, ftgSkIn = None, None
    for ftg in list_ftgSksOut:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)): #todo1v6 эта функция везде используется в паре с !=NodeSocketVirtual, нужно пределать топологию.
            ftgSkOut = ftg
            break
    for ftg in list_ftgSksIn:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
            ftgSkIn = ftg
            break
    return MinFromFtgs(ftgSkOut, ftgSkIn)

smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "SC#_A", {'toolMode':'NEW'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_A", {'toolMode':'CREATE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_C", {'toolMode':'COPY'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_V", {'toolMode':'PASTE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_X", {'toolMode':'SWAP'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Z", {'toolMode':'FLIP'})
# smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_Q", {'toolMode':'DELETE'})
smart_add_to_reg_and_kmiDefs(VoronoiInterfacerTool, "S#A_E", {'toolMode':'SOC_TY'})
dict_setKmiCats['spc'].add(VoronoiInterfacerTool.bl_idname)


class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vitPasteToAnySocket: bpy.props.BoolProperty(name="Allow paste to any socket", default=False)

with VlTrMapForKey(VoronoiInterfacerTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi在节点组里快速复制粘贴端口名给节点组输入输出端"

dict_toolLangSpecifDataPool[VoronoiInterfacerTool, "ru_RU"] = """Инструмент на уровне "The Great Trio". Ответвление от VLT ради удобного ускорения
процесса создания и спец-манипуляций с интерфейсами. "Менеджер интерфейсов"."""


smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "SC#_T")
smart_add_to_reg_and_kmiDefs(VoronoiLinksTransferTool, "S##_T", {'isByIndexes':True})
dict_setKmiCats['spc'].add(VoronoiLinksTransferTool.bl_idname)

with VlTrMapForKey(VoronoiLinksTransferTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi链接按输入端类型切换到别的端口"

dict_toolLangSpecifDataPool[VoronoiLinksTransferTool, "ru_RU"] = "Инструмент для редких нужд переноса всех линков с одного нода на другой.\nВ будущем скорее всего будет слито с VST."


smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "##A_W")
smart_add_to_reg_and_kmiDefs(VoronoiWarperTool, "S#A_W", {'isZoomedTo':False})
dict_setKmiCats['spc'].add(VoronoiWarperTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vwtSelectTargetKey: bpy.props.StringProperty(name="Select target Key", default='LEFT_ALT')

with VlTrMapForKey(VoronoiWarperTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速聚焦某条连接"

dict_toolLangSpecifDataPool[VoronoiWarperTool, "ru_RU"] = "Мини-ответвление реверс-инженеринга топологии, (как у VPT).\nИнструмент для \"точечных прыжков\" по сокетам."


smart_add_to_reg_and_kmiDefs(VoronoiLazyNodeStencilsTool, "##A_Q")
dict_setKmiCats['spc'].add(VoronoiLazyNodeStencilsTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnstNonColorName:  bpy.props.StringProperty(name="Non-Color name",  default="Non-Color")

with VlTrMapForKey(VoronoiLazyNodeStencilsTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi在输入端快速节点"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiLazyNodeStencilsTool)) as dm:
    dm["ru_RU"] = f"Настройки инструмента {VoronoiLazyNodeStencilsTool.bl_label}:"
    dm["zh_CN"] = f"{VoronoiLazyNodeStencilsTool.bl_label}快速添加纹理设置:"

dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "ru_RU"] = """Мощь. Три буквы на инструмент, дожили... Инкапсулирует Ctrl-T от
NodeWrangler'а, и никогда не реализованный 'VoronoiLazyNodeContinuationTool'. """ #"Больше лени богу лени!"
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, "zh_CN"] = "代替NodeWrangler的ctrl+t"

class VlnstData:
    lastLastExecError = "" #Для пользовательского редактирования vlnstLastExecError, низя добавить или изменить, но можно удалить.
    isUpdateWorking = False
def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnstLastExecError = ""
    elif self.vlnstLastExecError:
        if self.vlnstLastExecError!=VlnstData.lastLastExecError: #Заметка: Остерегаться переполнения стека.
            self.vlnstLastExecError = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnstLastExecError: bpy.props.StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)

#Внезапно оказалось, что моя когдато-шняя идея для инструмента "Ленивое Продолжение" инкапсулировалось в этом инструменте. Вот так неожиданность.
#Этот инструмент, то же самое, как и ^ (где сокет и нод однозначно определял следующий нод), только для двух сокетов; и возможностей больше!

lzAny = '!any'
class LazyKey():
    def __init__(self, fnb, fst, fsn, fsg, snb=lzAny, sst=lzAny, ssn=lzAny, ssg=lzAny):
        self.firstNdBlid = fnb
        self.firstSkBlid = dict_typeSkToBlid.get(fst, fst)
        self.firstSkName = fsn
        self.firstSkGend = fsg
        self.secondNdBlid = snb
        self.secondSkBlid = dict_typeSkToBlid.get(sst, sst)
        self.secondSkName = ssn
        self.secondSkGend = ssg
class LazyNode():
    #Чёрная магия. Если в __init__(list_props=[]), то указание в одном nd.list_props += [..] меняет вообще у всех в lzSt. Нереально чёрная магия; ночные кошмары обеспечены.
    def __init__(self, blid, list_props, ofsPos=(0,0), hhoSk=0, hhiSk=0):
        self.blid = blid
        #list_props Содержит в себе обработку и сокетов тоже.
        #Указание на сокеты (в list_props и lzHh_Sk) -- +1 от индекса, а знак указывает сторону; => 0 не используется.
        self.list_props = list_props
        self.lzHhOutSk = hhoSk
        self.lzHhInSk = hhiSk
        self.locloc = Vec2(ofsPos) #"Local location"; и offset от центра мира.
class LazyStencil():
    def __init__(self, key, csn=2, name="", prior=0.0):
        self.lzkey = key
        self.prior = prior #Чем выше, тем важнее.
        self.name = name
        self.trees = {} #Это также похоже на часть ключа.
        self.isTwoSkNeeded = csn==2
        self.list_nodes = []
        self.list_links = [] #Порядковый нод / сокет, и такое же на вход.
        self.isSameLink = False
        self.txt_exec = ""

list_vlnstDataPool = []

#Database:
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VECTOR','Normal',False), 2, "Fast Color NormalMap")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeNormalMap', [], hhiSk=-2, hhoSk=1) )
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VALUE',lzAny,False), 2, "Lazy Non-Color data to float socket")
lzSt.trees = {'ShaderNodeTree'}
lzSt.isSameLink = True
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',False), 1, "NW TexCord Parody")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexImage', [(2,'hide',True)], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,0,1,0) ]
list_vlnstDataPool.append(lzSt)
lzSt = copy.deepcopy(lzSt)
lzSt.lzkey.firstSkName = "Base Color"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'VECTOR','Vector',False), 1, "NW TexCord Parody Half")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], hhoSk=-1, ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0) ]
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA',lzAny,True, lzAny,'SHADER',lzAny,False), 2, "Insert Emission")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeEmission', [], hhiSk=-1, hhoSk=1) )
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey('ShaderNodeBackground','RGBA','Color',False), 1, "World env texture", prior=1.0)
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexEnvironment', [], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeTexCoord', [('show_options',False)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,3,1,0) ]
list_vlnstDataPool.append(lzSt)
##

list_vlnstDataPool.sort(key=lambda a:a.prior, reverse=True)

def DoLazyStencil(tree, skFirst, skSecond, lzSten):
    list_result = []
    firstCenter = None
    for li in lzSten.list_nodes:
        nd = tree.nodes.new(li.blid)
        nd.location += li.locloc
        list_result.append(nd)
        for pr in li.list_props:
            if length(pr)==2:
                setattr(nd, pr[0], pr[1])
            else:
                setattr( (nd.outputs if pr[0]>0 else nd.inputs)[abs(pr[0])-1], pr[1], pr[2] )
        if li.lzHhOutSk:
            tree.links.new(nd.outputs[abs(li.lzHhOutSk)-1], skFirst if li.lzHhOutSk<0 else skSecond)
        if li.lzHhInSk:
            tree.links.new(skFirst if li.lzHhInSk<0 else skSecond, nd.inputs[abs(li.lzHhInSk)-1])
    #Для одного нода ещё и сгодилось бы, но учитывая большое разнообразие и гибкость, наверное лучше без NewLinkHhAndRemember(), соединять в сыром виде.
    for li in lzSten.list_links:
        tree.links.new(list_result[li[0]].outputs[li[1]], list_result[li[2]].inputs[li[3]])
    if lzSten.isSameLink:
        tree.links.new(skFirst, skSecond)
    return list_result
def LzCompare(a, b):
    return (a==b)or(a==lzAny)
def LzNodeDoubleCheck(zk, a, b): return LzCompare(zk.firstNdBlid,            a.bl_idname if a else "") and LzCompare(zk.secondNdBlid,            b.bl_idname if b else "")
def LzTypeDoubleCheck(zk, a, b): return LzCompare(zk.firstSkBlid, SkConvertTypeToBlid(a) if a else "") and LzCompare(zk.secondSkBlid, SkConvertTypeToBlid(b) if b else "") #Не 'type', а blid'ы; для аддонских деревьев.
def LzNameDoubleCheck(zk, a, b): return LzCompare(zk.firstSkName,      GetSkLabelName(a) if a else "") and LzCompare(zk.secondSkName,      GetSkLabelName(b) if b else "")
def LzGendDoubleCheck(zk, a, b): return LzCompare(zk.firstSkGend,            a.is_output if a else "") and LzCompare(zk.secondSkGend,            b.is_output if b else "")
def LzLazyStencil(prefs, tree, skFirst, skSecond):
    if not skFirst:
        return []
    ndOut = skFirst.node
    ndIn = skSecond.node if skSecond else None
    for li in list_vlnstDataPool:
        if (li.isTwoSkNeeded)^(not skSecond): #Должен не иметь второго для одного, или иметь для двух.
            if (not li.trees)or(tree.bl_idname in li.trees): #Должен поддерживать тип дерева.
                zk = li.lzkey
                if LzNodeDoubleCheck(zk, ndOut, ndIn): #Совпадение нод.
                    for cyc in (False, True):
                        skF = skFirst
                        skS = skSecond
                        if cyc: #Оба выхода и оба входа, но разные гендеры могут быть в разном порядке. Но перестановка имеет значение для содержания txt_exec'ов.
                            skF, skS = skSecond, skFirst
                        if LzTypeDoubleCheck(zk, skF, skS): #Совпадение Blid'ов сокетов.
                            if LzNameDoubleCheck(zk, skF, skS): #Имён/меток сокетов.
                                if LzGendDoubleCheck(zk, skF, skS): #Гендеров.
                                    result = DoLazyStencil(tree, skF, skS, li)
                                    if li.txt_exec:
                                        try:
                                            exec(li.txt_exec) #Тревога!1, А нет.. без паники, это внутреннее. Всё ещё всё в безопасности.
                                        except Exception as ex:
                                            VlnstData.lastLastExecError = str(ex)
                                            prefs.vlnstLastExecError = VlnstData.lastLastExecError
                                    return result
def VlnstLazyTemplate(prefs, tree, skFirst, skSecond, cursorLoc):
    list_nodes = LzLazyStencil(prefs, tree, skFirst, skSecond)
    if list_nodes:
        bpy.ops.node.select_all(action='DESELECT')
        firstOffset = cursorLoc-list_nodes[0].location
        for nd in list_nodes:
            nd.select = True
            nd.location += firstOffset
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')


smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
smart_add_to_reg_and_kmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})
dict_setKmiCats['spc'].add(VoronoiResetNodeTool.bl_idname)

with VlTrMapForKey(VoronoiResetNodeTool.bl_label) as dm:
    dm["zh_CN"] = "Voronoi快速恢复节点默认参数"

dict_toolLangSpecifDataPool[VoronoiResetNodeTool, "ru_RU"] = """Инструмент для сброса нодов без нужды прицеливания, с удобствами ведения мышкой
и игнорированием свойств перечислений. Был создан, потому что в NW было похожее."""


#smart_add_to_reg_and_kmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})
dict_setKmiCats['grt'].add(VoronoiDummyTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vdtDummy: bpy.props.StringProperty(name="Dummy", default="Dummy")

with VlTrMapForKey(VoronoiDummyTool.bl_label) as dm:
    dm["ru_RU"] = "Voronoi Болванка"

dict_toolLangSpecifDataPool[VoronoiDummyTool, "ru_RU"] = """"Ой дурачёк"."""

# =======

def GetVlKeyconfigAsPy(): #Взято из 'bl_keymap_utils.io'. Понятия не имею, как оно работает.
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
    result += "    import bl_keymap_utils.versioning"+"\n" #Чёрная магия; кажется, такая же как и с "gpu_extras".
    result += "    kc = bpy.context.window_manager.keyconfigs.active"+"\n"
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})"+"\n"
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result
def GetVaSettAsPy(prefs):
    set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'dsIsFieldDebug', 'dsIsTestDrawing', #tovo2v6 все ли?
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
    #Сконструировать изменённые настройки аддона:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{voronoiAddonName}'].preferences"+"\n\n"
    txt_vasp += "def SetProp(att, val):"+"\n"
    txt_vasp += "    if hasattr(prefs, att):"+"\n"
    txt_vasp += "        setattr(prefs, att, val)"+"\n\n"
    def AddAndProc(txt):
        nonlocal txt_vasp
        len = txt.find(",")
        txt_vasp += txt.replace(", ",","+" "*(42-len), 1)
    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            #'_BoxDiscl'ы не стал игнорировать, пусть будут.
            if pr.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(pr,'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(pr.default_array, getattr(prefs, pr.identifier)) if li[0]!=li[1]]
                else:
                    isDiff = pr.default!=getattr(prefs, pr.identifier)
                if (True)or(isDiff): #Наверное сохранять только разницу небезопасно, вдруг не сохранённые свойства изменят своё значение по умолчанию.
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
    #Сконструировать все VL хоткеи:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    #P.s. я не знаю, как обрабатывать только изменённые хоткеи; это выглядит слишком головной болью и дремучим лесом. #tovo0v6
    # Лень реверсинженерить '..\scripts\modules\bl_keymap_utils\io.py', поэтому просто сохранять всех.
    txt_vasp += GetVlKeyconfigAsPy() #Оно нахрен не работает; та часть, которая восстанавливает; сгенерированным скриптом ничего не сохраняется, только временный эффект.
    #Придётся ждать того героя, кто придёт и починит всё это.
    return txt_vasp

def GetFirstUpperLetters(txt):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)
def SolderClsToolNames():
    for cls in dict_vtClasses:
        cls.vlTripleName = GetFirstUpperLetters(cls.bl_label)+"T" #Изначально было создано "потому что прикольно", но теперь это нужно; см. SetPieData().
        cls.disclBoxPropName = cls.vlTripleName[:-1].lower()+"BoxDiscl"
        cls.disclBoxPropNameInfo = cls.disclBoxPropName+"Info"
SolderClsToolNames()

for cls in dict_vtClasses:
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropName}: bpy.props.BoolProperty(name=\"\", default=False)")
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropNameInfo}: bpy.props.BoolProperty(name=\"\", default=False)")

list_langDebEnumItems = []
for li in ["Free", "Special", "AddonPrefs"]+[cls.bl_label for cls in dict_vtClasses]:
    list_langDebEnumItems.append( (li.upper(), GetFirstUpperLetters(li), "") )

def VaUpdateTestDraw(self, context):
    TestDraw.Toggle(context, self.dsIsTestDrawing)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaLangDebDiscl: bpy.props.BoolProperty(name="Language bruteforce debug", default=False)
    vaLangDebEnum: bpy.props.EnumProperty(name="LangDebEnum", default='FREE', items=list_langDebEnumItems)
    dsIsFieldDebug: bpy.props.BoolProperty(name="Field debug", default=False)
    dsIsTestDrawing: bpy.props.BoolProperty(name="Testing draw", default=False, update=VaUpdateTestDraw)
    dsIncludeDev: bpy.props.BoolProperty(name="IncludeDev", default=False)

#Оставлю здесь маленький список моих личных "хотелок" (по хронологии интеграции), которые перекочевали из других моих личных аддонов в VL:
#Hider
#QuckMath и JustMathPie
#Warper
#RANTO

def Prefs():
    # return bpy.context.preferences.addons[voronoiAddonName].preferences
    return bpy.context.preferences.addons[__package__].preferences

class VoronoiOpAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    bl_description = "VL's addon tab" #todo1v6 придумать, как перевести для каждой вкладки разное.
    opt: bpy.props.StringProperty()
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

def LyAddThinSep(where: UILayout, scaleY):
    row = where.row(align=True)
    row.separator()
    row.scale_y = scaleY

class KmiCat():
    def __init__(self, propName='', set_kmis=set(), set_idn=set()):
        self.propName = propName
        self.set_kmis = set_kmis
        self.set_idn = set_idn
        self.sco = 0
class KmiCats:
    pass

vaUpdateSelfTgl = False
def VaUpdateDecorColSk(self, _context):
    global vaUpdateSelfTgl
    if vaUpdateSelfTgl:
        return
    vaUpdateSelfTgl = True
    self.vaDecorColSk = self.vaDecorColSkBack
    vaUpdateSelfTgl = False

fitTabItems = ( ('SETTINGS',"Settings",""), ('APPEARANCE',"Appearance",""), ('DRAW',"Draw",""), ('KEYMAP',"Keymap",""), ('INFO',"Info","") )#, ('DEV',"Dev","")
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaUiTabs: bpy.props.EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=fitTabItems)
    vaInfoRestore:     bpy.props.BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    #Box disclosures:
    vaKmiMainstreamDiscl: bpy.props.BoolProperty(name="The Great Trio ", default=True) #Заметка: Пробел важен для переводов.
    vaKmiOtjersDiscl:     bpy.props.BoolProperty(name="Others ", default=False)
    vaKmiSpecialDiscl:    bpy.props.BoolProperty(name="Specials ", default=False)
    vaKmiQqmDiscl:        bpy.props.BoolProperty(name="Quick quick math ", default=False)
    vaKmiCustomDiscl:     bpy.props.BoolProperty(name="Custom ", default=True)
    ##
    vaDecorLy:        bpy.props.FloatVectorProperty(name="DecorForLayout",   default=(0.01, 0.01, 0.01),   min=0, max=1, size=3, subtype='COLOR')
    vaDecorColSk:     bpy.props.FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=VaUpdateDecorColSk)
    vaDecorColSkBack: bpy.props.FloatVectorProperty(name="vaDecorColSkBack", default=(1.0, 1.0, 1.0, 1.0), min = 0, max=1, size=4, subtype='COLOR')

def pref():
    return bpy.context.preferences.addons[__name__].preferences

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    dsIsDrawText:   bpy.props.BoolProperty(name="Text",        default=True) #Учитывая VHT и VEST, это уже больше просто для текста в рамке, чем для текста от сокетов.
    dsIsDrawMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsDrawPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsDrawLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsDrawSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsColoredText:   bpy.props.BoolProperty(name="Text",        default=True)
    dsIsColoredMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsColoredPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsColoredLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsColoredSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    dsIsColoredNodes:  bpy.props.BoolProperty(name="Nodes",       default=True)
    ##
    dsSocketAreaAlpha: bpy.props.FloatProperty(name="Socket area alpha", default=0.4, min=0.0, max=1.0, subtype="FACTOR")
    ##
    dsUniformColor:     bpy.props.FloatVectorProperty(name="Alternative uniform color", default=(1, 0, 0, 0.9), min=0, max=1, size=4, subtype='COLOR') #0.65, 0.65, 0.65, 1.0
    dsUniformNodeColor: bpy.props.FloatVectorProperty(name="Alternative nodes color",   default=(0, 1, 0, 0.9), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 0.9
    dsCursorColor:      bpy.props.FloatVectorProperty(name="Cursor color",              default=(0, 0, 0, 1.0), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 1.0
    dsCursorColorAvailability: bpy.props.IntProperty(name="Cursor color availability", default=2, min=0, max=2, description="If a line is drawn to the cursor, color part of it in the cursor color.\n0 – Disable.\n1 – For one line.\n2 – Always")
    ##
    dsDisplayStyle: bpy.props.EnumProperty(name="Display frame style", default='ONLY_TEXT', items=( ('CLASSIC',"Classic","Classic"), ('SIMPLIFIED',"Simplified","Simplified"), ('ONLY_TEXT',"Only text","Only text") ))
    dsFontFile:     bpy.props.StringProperty(name="Font file",    default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH') #"Пользователи Линукса негодуют".
    dsLineWidth:    bpy.props.FloatProperty( name="Line Width",   default=2, min=0.5, max=8.0, subtype="FACTOR")
    dsPointScale:   bpy.props.FloatProperty( name="Point scale",  default=1.0, min=0.0, max=3.0)
    dsFontSize:     bpy.props.IntProperty(   name="Font size",    default=32,  min=10,  max=48)
    dsMarkerStyle:  bpy.props.IntProperty(   name="Marker Style", default=0,   min=0,   max=2)
    ##
    dsManualAdjustment: bpy.props.FloatProperty(name="Manual adjustment",         default=-0.2, description="The Y-axis offset of text for this font") #https://blender.stackexchange.com/questions/312413/blf-module-how-to-draw-text-in-the-center
    dsPointOffsetX:     bpy.props.FloatProperty(name="Point offset X axis",       default=20.0,   min=-50.0, max=50.0)
    dsFrameOffset:      bpy.props.IntProperty(  name="Frame size",                default=0,      min=0,     max=24, subtype='FACTOR') #Заметка: Важно, чтобы это был Int.
    dsDistFromCursor:   bpy.props.FloatProperty(name="Text distance from cursor", default=25.0,   min=5.0,   max=50.0)
    ##
    dsIsAlwaysLine:        bpy.props.BoolProperty(name="Always draw line",      default=True, description="Draw a line to the cursor even from a single selected socket")
    dsIsSlideOnNodes:      bpy.props.BoolProperty(name="Slide on nodes",        default=False)
    dsIsDrawNodeNameLabel: bpy.props.BoolProperty(name="Display text for node", default=True)
    ##
    dsIsAllowTextShadow: bpy.props.BoolProperty(       name="Enable text shadow", default=False)
    dsShadowCol:         bpy.props.FloatVectorProperty(name="Shadow color",       default=(0.0, 0.0, 0.0, 0.5), min=0,   max=1,  size=4, subtype='COLOR')
    dsShadowOffset:      bpy.props.IntVectorProperty(  name="Shadow offset",      default=(2,-2),               min=-20, max=20, size=2)
    dsShadowBlur:        bpy.props.IntProperty(        name="Shadow blur",        default=2,                    min=0,   max=2)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    #Уж было я хотел добавить это, но потом мне стало таак лень. Это же нужно всё менять под "только сокеты", и критерии для нод неведомо как получать.
    #И выгода неизвестно какая, кроме эстетики. Так что ну его нахрен. "Работает -- не трогай".
    #А ещё реализация "только сокеты" где-то может грозить потенциальной кроличьей норой.
    vSearchMethod: bpy.props.EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") )) #Нигде не используется; и кажется, никогда не будет.
    vEdgePanFac: bpy.props.FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    vEdgePanSpeed: bpy.props.FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    vIsOverwriteZoomLimits: bpy.props.BoolProperty(name="Overwriting zoom limits", default=False)
    vOwZoomMin: bpy.props.FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    vOwZoomMax: bpy.props.FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    @staticmethod
    def BringTranslations():
        with VlTrMapForKey(GetPrefsRnaProp('vaInfoRestore').description) as dm:
            dm["ru_RU"] = "Этот список лишь копия из настроек. \"Восстановление\" восстановит всё, а не только аддон"
            dm["zh_CN"] = "危险:“恢复”按钮将恢复整个快捷键里“节点编辑器”类中的所有设置,而不仅仅是恢复此插件!下面只显示本插件的快捷键。"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiMainstreamDiscl').name) as dm:
            dm["ru_RU"] = "Великое трио"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiOtjersDiscl').name) as dm:
            dm["ru_RU"] = "Другие"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiSpecialDiscl').name) as dm:
            dm["ru_RU"] = "Специальные"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiQqmDiscl').name) as dm:
            dm["ru_RU"] = "Быстрая быстрая математика"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiCustomDiscl').name) as dm:
            dm["ru_RU"] = "Кастомные"
#            dm["zh_CN"] = ""
        #== Draw ==
        with VlTrMapForKey(GetPrefsRnaProp('dsUniformColor').name) as dm:
            dm["ru_RU"] = "Альтернативный постоянный цвет"
            dm["zh_CN"] = "自定义轮选时端口的颜色"    
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
            dm["zh_CN"] = "端口区域的透明度"
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
            dm["zh_CN"] = "高亮显示选中端口"
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
            dm["zh_CN"] = "在鼠标移动到移动到已有连接端口的时是否还显示连线"
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

class VoronoiAddonPrefs(VoronoiAddonPrefs):
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
                if colDiscl:=LyAddAddonBoxDiscl(colMain, self, cls.disclBoxPropName, txt=TxtClsBlabToolSett(cls), align=True):
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
            row.prop(self,'dsIsDrawNodeNameLabel', text="Node text") #"Text for node"
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
        colBox = LyAddLabeledBoxCol(colMain, text="Special")
        #LyAddHandSplitProp(colBox, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
        LyAddHandSplitProp(colBox, self,'dsIsAlwaysLine')
        LyAddHandSplitProp(colBox, self,'dsIsSlideOnNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Colors")
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
        colBox = LyAddLabeledBoxCol(colMain, text="Customization")
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
        colBox = LyAddLabeledBoxCol(colMain, text="Advanced")
        LyAddHandSplitProp(colBox, self,'dsManualAdjustment')
        LyAddHandSplitProp(colBox, self,'dsPointOffsetX')
        LyAddHandSplitProp(colBox, self,'dsFrameOffset')
        LyAddHandSplitProp(colBox, self,'dsDistFromCursor')
        LyAddThinSep(colBox, 0.25) #Межгалкоевые отступы складываются, поэтому дополнительный отступ для выравнивания.
        LyAddHandSplitProp(colBox, self,'dsIsAllowTextShadow')
        colShadow = colBox.column(align=True)
        LyAddHandSplitProp(colShadow, self,'dsShadowCol', active=self.dsIsAllowTextShadow)
        LyAddHandSplitProp(colShadow, self,'dsShadowBlur') #Размытие тени разделяет их, чтобы не сливались вместе по середине.
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
        kmiCats.qqm = KmiCat('vaKmiQqmDiscl',        set(), dict_setKmiCats['qqm'] )
        kmiCats.grt = KmiCat('vaKmiMainstreamDiscl', set(), dict_setKmiCats['grt'] )
        kmiCats.oth = KmiCat('vaKmiOtjersDiscl',     set(), dict_setKmiCats['oth'] )
        kmiCats.spc = KmiCat('vaKmiSpecialDiscl',    set(), dict_setKmiCats['spc'] )
        kmiCats.cus.LCond = lambda a: a.id<0 #Отрицательный ид для кастомных? Ну ладно. Пусть будет идентифицирующим критерием.
        kmiCats.qqm.LCond = lambda a: any(True for txt in {'quickOprFloat','quickOprVector','quickOprBool','quickOprColor','justPieCall','isRepeatLastOperation'} if getattr(a.properties, txt, None))
        kmiCats.grt.LCond = lambda a: a.idname in kmiCats.grt.set_idn
        kmiCats.oth.LCond = lambda a: a.idname in kmiCats.oth.set_idn
        kmiCats.spc.LCond = lambda a:True
        #В старых версиях аддона с другим методом поиска, на вкладке "keymap" порядок отображался в обратном порядке вызовов регистрации kmidef с одинаковыми `cls`.
        #Теперь сделал так. Как работал предыдущий метод -- понятия не имею.
        scoAll = 0
        for li in kmUNe.keymap_items:
            if li.idname.startswith("node.voronoi_"):
                for dv in kmiCats.__dict__.values():
                    if dv.LCond(li):
                        dv.set_kmis.add(li)
                        dv.sco += 1
                        break
                scoAll += 1 #Хоткеев теперь стало та-а-ак много, что неплохо было бы узнать их количество.
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
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='NONE').opt = 'AddNewKmi' #NONE  ADD
        def LyAddKmisCategory(where: UILayout, cat):
            if not cat.set_kmis:
                return
            colListCat = where.row().column(align=True)
            txt = self.bl_rna.properties[cat.propName].name
            if not LyAddDisclosureProp(colListCat, self, cat.propName, txt=TranslateIface(txt)+f" ({cat.sco})", active=False, isWide=1-1):
                return
            for li in sorted(cat.set_kmis, key=lambda a:a.id):
                colListCat.context_pointer_set('keymap', kmUNe)
                rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, kmUNe, li, colListCat, 0) #Заметка: Если colListCat будет не colListCat, то возможность удаления kmi станет недоступной.
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
        LyAddUrlHl(colUrls, "VL Wiki", bl_info['wiki_url'])
        LyAddUrlHl(colUrls, "RANTO Git", "https://github.com/ugorek000/RANTO")
        colUrls.separator()
        LyAddUrlHl(colUrls, "Event Type Items", "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html")
        LyAddUrlHl(colUrls, "Translator guide", "https://developer.blender.org/docs/handbook/translating/translator_guide/")
        LyAddUrlHl(colUrls, "Translator dev guide", "https://developer.blender.org/docs/handbook/translating/developer_guide/")
        ##
        colMain.separator()
        row = colMain.row(align=True)
        row.alignment = 'LEFT'
        row.operator(VoronoiOpAddonTabs.bl_idname, text=txt_copySettAsPyScript, icon='COPYDOWN').opt = 'GetPySett' #SCRIPT  COPYDOWN
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
                    col.label(text=bl_info['description'])
                    col.label(text=txt_addonVerDateCreated)
                    col.label(text=txt_addonBlVerSupporting)
                    col.label(text=txt_onlyFontFormat)
                    col.label(text=txt_copySettAsPyScript)
                    col.label(text=txt_сheckForUpdatesYourself)
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
                    set_alreadyDone = set() #Учитывая разделение с помощью vaLangDebEnum, уже бесполезно.
                    col0 = colLangDebug.column(align=True)
                    cls = dict_toolBlabToCls[self.vaLangDebEnum]
                    col1 = LyAddAlertNested(col0, cls.bl_label)
                    rna = eval(f"bpy.ops.{cls.bl_idname}.get_rna_type()") #Через getattr какого-то чёрта не работает `getattr(bpy.ops, cls.bl_idname).get_rna_type()`.
                    for pr in rna.properties[1:]: #Пропуск rna_type.
                        rowLabel = col1.row(align=True)
                        if pr.identifier not in set_alreadyDone:
                            LyAddTranDataForProp(rowLabel, pr)
                            set_alreadyDone.add(pr.identifier)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    def draw(self, context):
        def LyAddDecorLyColRaw(where: UILayout, sy=0.05, sx=1.0, en=False):
            where.prop(self,'vaDecorLy', text="")
            where.scale_x = sx
            where.scale_y = sy #Если будет меньше, чем 0.05, то макет исчезнет, и угловатость пропадёт.
            where.enabled = en
        colLy = self.layout.column()
        colMain = colLy.column(align=True)
        colTabs = colMain.column(align=True)
        rowTabs = colTabs.row(align=True)
        #Переключение вкладок создано через оператор, чтобы случайно не сменить вкладку при ведении зажатой мышки, кой есть особый соблазн с таким большим количеством "isColored".
        #А также теперь они задекорены ещё больше под "вкладки", чего нельзя сделать с обычным макетом prop'а с 'expand=True'.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
            #Теперь ещё больше похожи на вкладки
            LyAddDecorLyColRaw(col.row(align=True)) #row.operator(VoronoiOpAddonTabs.bl_idname, text="", emboss=False) #Через оператор тоже работает.
            #col.scale_x = min(1.0, (5.5-cyc)/2)
        colBox = colTabs.column(align=True)
        #LyAddDecorLyColRaw(colBox.row(align=True))
        #LyAddDecorLyColRaw(colBox.row(align=True), sy=0.25) #Коробка не может сузиться меньше, чем своё пустое состояние. Пришлось искать другой способ..
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
            LyAddEtb(colMain) #colMain.label(text=str(ex), icon='ERROR', translate=False)

dict_classes[VoronoiOpAddonTabs] = True
dict_classes[VoronoiAddonPrefs] = True

list_addonKeymaps = []

isRegisterFromMain = False
def register():
    for dk in dict_classes:
        bpy.utils.register_class(dk)
    ##
    prefs = Prefs()
    if isRegisterFromMain:
        if hasattr(bpy.types.SpaceNodeEditor,'handle'):
            bpy.types.SpaceNodeEditor.nsReg = perf_counter_ns()
    else:
        prefs.vlnstLastExecError = ""
        prefs.vaLangDebDiscl = False
        for cls in dict_vtClasses:
            setattr(prefs, cls.disclBoxPropNameInfo, False)
        prefs.dsIsTestDrawing = False
    ##
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blid, key, shift, ctrl, alt, repeat, dict_props in list_kmiDefs:
        kmi = kmANe.keymap_items.new(idname=blid, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        kmi.active = blid!='node.voronoi_dummy'
        if dict_props:
            for dk, dv in dict_props.items():
                setattr(kmi.properties, dk, dv)
        list_addonKeymaps.append(kmi)
    ##
    RegisterTranslations()
    RegisterSolderings()
def unregister():
    UnregisterSolderings()
    UnregisterTranslations()
    ##
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for li in list_addonKeymaps:
        kmANe.keymap_items.remove(li)
    list_addonKeymaps.clear()
    ##
    for dk in dict_classes:
        bpy.utils.unregister_class(dk)

#Мой гит в bl_info, это конечно же круто, однако было бы неплохо иметь ещё и явно указанные способы связи:
#  coaltangle@gmail.com
#  ^ Моя почта. Если вдруг случится апокалипсис, или эта VL-археологическая-находка сможет решить не-полиномиальную задачу, то писать туда.
# Для более реалтаймового общения (предпочтительно) и по вопросам о VL и его коде пишите на мой дискорд 'ugorek#6434'.
# А ещё есть тема на blenderartists.org/t/voronoi-linker-addon-node-wrangler-killer

def DisableKmis(): #Для повторных запусков скрипта. Работает до первого "Restore".
    kmUNe = GetUserKmNe()
    for li, *oi in list_kmiDefs:
        for kmiCon in kmUNe.keymap_items:
            if li==kmiCon.idname:
                kmiCon.active = False #Это удаляет дубликаты. Хак?
                kmiCon.active = True #Вернуть обратно, если оригинал.
if __name__=="__main__":
    DisableKmis() #Кажется не важно в какой очерёдности вызывать, перед или после добавления хоткеев.
    isRegisterFromMain = True
    register()
