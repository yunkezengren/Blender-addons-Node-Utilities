from .一些前向func import DisplayMessage
from .关于翻译的函数 import GetAnnotFromCls, VlTrMapForKey
from .关于翻译的函数 import *
from .关于节点的函数 import *
from .关于ui的函数 import *
from .关于颜色的函数 import *
from .VoronoiTool import *
from .关于sold的函数 import *
from .globals import *
from .一些前向class import *
from .一些前向func import *
from .关于绘制的函数 import *
from .VoronoiTool import VoronoiToolNd
from bpy.app.translations import pgettext_iface as TranslateIface


# 现在 RANTO 已经集成到 VL 中了. 连我自己都感到意外.
# 参见原版: https://github.com/ugorek000/RANTO

class RantoData():
    def __init__(self, isOnlySelected=0, widthNd=140, isUniWid=False, indentX=40, indentY=30, isIncludeMutedLinks=False, isIncludeNonValidLinks=False, isFixIslands=True):
        self.kapibara = ""
        self.dict_ndTopoWorking = {}

def VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, ndRoot):
    rada.kapibara = "kapibara"


class VoronoiRantoTool(VoronoiToolNd): #完成了.
    bl_idname = 'node.voronoi_ranto'
    bl_label = "Voronoi RANTO"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    isOnlySelected: bpy.props.IntProperty(name="Only selected", default=0, min=0, max=2, description="0 – Any node.\n1 – Selected + reroutes.\n2 – Only selected")
    isUniWid:       bpy.props.BoolProperty(name="Uniform width", default=False)
    widthNd: bpy.props.IntProperty(name="Node width", default=140, soft_min=100, soft_max=180, subtype='FACTOR')
    indentX: bpy.props.IntProperty(name="Indent x",   default=40,  soft_min=0,   soft_max=80,  subtype='FACTOR')
    indentY: bpy.props.IntProperty(name="Indent y",   default=30,  soft_min=0,   soft_max=60,  subtype='FACTOR')
    isUncollapseNodes: bpy.props.BoolProperty(name="Uncollapse nodes", default=False)
    isDeleteReroutes:  bpy.props.BoolProperty(name="Delete reroutes",  default=False)
    isSelectNodes: bpy.props.IntProperty(name="Select nodes", default=1, min=-1, max=1, description="-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting involveds node")
    isIncludeMutedLinks:    bpy.props.BoolProperty(name="Include muted links",     default=False)
    isIncludeNonValidLinks: bpy.props.BoolProperty(name="Include non valid links", default=True)
    isAccumulate: bpy.props.BoolProperty(name="Accumulate", default=False)
    def DoRANTO(self, ndTar, tree, isFixIslands=True):
        if ndTar==self.lastNdProc:
            return
        self.lastNdProc = ndTar
        ndTar.select = True
        if not self.isAccumulate:
            tree.nodes.active = ndTar
        #elif self.ndMaxAccRoot:
        #    ndTar = self.ndMaxAccRoot
        def DoRanto(nd):
            rada = RantoData(self.isOnlySelected+self.isAccumulate, self.widthNd, self.isUniWid, self.indentX, self.indentY, self.isIncludeMutedLinks, self.isIncludeNonValidLinks, isFixIslands)
            VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, nd)
            return rada
        if self.isUncollapseNodes:
            dict_remresNdHide = {}
            for nd in tree.nodes:
                dict_remresNdHide[nd] = nd.hide
                nd.hide = False
            bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        rada = DoRanto(ndTar)
        if self.isDeleteReroutes:
            bpy.ops.node.select_all(action='DESELECT')
            isInvl = False
            for nd in rada.dict_ndTopoWorking:
                if nd.type=='REROUTE':
                    nd.select = True
                    isInvl = True
            if isInvl:
                bpy.ops.node.delete_reconnect()
                rada = DoRanto(ndTar)
        if (self.isSelectNodes==-1)and(not self.isAccumulate):
            bpy.ops.node.select_all(action='DESELECT')
        soldNAcc = not self.isAccumulate
        for nd in tree.nodes:
            tgl = nd in rada.dict_ndTopoWorking
            if (self.isSelectNodes==1)and(soldNAcc):
                nd.select = tgl
            if (not tgl)and(self.isUncollapseNodes): #恢复未涉及节点的隐藏状态.
                nd.hide = dict_remresNdHide[nd]
        if self.isAccumulate:
            tree.nodes.active = ndTar
            for nd in rada.dict_ndTopoWorking:
                nd.select = True
        #ndTar.location = ndTar.location #bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue #为此，请参考原始的RANTO插件.
            self.fotagoNd = ftgNd
            #if not self.ndMaxAccRoot:
            #    self.ndMaxAccRoot = nd
            if prefs.vrtIsLiveRanto:
                self.DoRANTO(nd, tree, prefs.vrtIsFixIslands)
            break
    def MatterPurposeTool(self, event, prefs, tree):
        ndTar = self.fotagoNd.tar
        #if self.isAccumulate:
        #    self.ndMaxAccRoot = None
        #    self.lastNdProc = None
        self.DoRANTO(ndTar, tree, prefs.vrtIsFixIslands)
        DisplayMessage("RANTO", TranslateIface("This tool is empty")+" ¯\_(ツ)_/¯")
    def InitTool(self, event, prefs, tree):
        self.lastNdProc = None
        #self.ndMaxAccRoot = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vrtIsLiveRanto')
        LyAddLeftProp(col, prefs,'vrtIsFixIslands')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey("This tool is empty") as dm:
            dm["ru_RU"] = "Этот инструмент пуст"
            dm["zh_CN"] = "该工具是空的"
        ##
        with VlTrMapForKey(GetAnnotFromCls(cls,'isOnlySelected').name) as dm:
            dm["ru_RU"] = "Только выделенные"
            dm["zh_CN"] = "仅选定的"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isOnlySelected').description) as dm:
            dm["ru_RU"] = "0 – Любой нод.\n1 – Выделенные + рероуты.\n2 – Только выделенные"
            dm["zh_CN"] = "0 – 任意节点。\n1 – 选定+转向节点。\n2 – 仅选定的节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isUniWid').name) as dm:
            dm["ru_RU"] = "Постоянная ширина"
            dm["zh_CN"] = "统一宽度"
        with VlTrMapForKey(GetAnnotFromCls(cls,'widthNd').name) as dm:
            dm["ru_RU"] = "Ширина нод"
            dm["zh_CN"] = "节点宽度"
        with VlTrMapForKey(GetAnnotFromCls(cls,'indentX').name) as dm:
            dm["ru_RU"] = "Отступ по X"
            dm["zh_CN"] = "X缩进"
        with VlTrMapForKey(GetAnnotFromCls(cls,'indentY').name) as dm:
            dm["ru_RU"] = "Отступ по Y"
            dm["zh_CN"] = "Y缩进"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isUncollapseNodes').name) as dm:
            dm["ru_RU"] = "Разворачивать ноды"
            dm["zh_CN"] = "展开节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isDeleteReroutes').name) as dm:
            dm["ru_RU"] = "Удалять рероуты"
            dm["zh_CN"] = "删除转向节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNodes').name) as dm:
            dm["ru_RU"] = "Выделять ноды"
            dm["zh_CN"] = "选择节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNodes').description) as dm:
            dm["ru_RU"] = "-1 – Де-выделять всё.\n 0 – Ничего не делать.\n 1 – Выделять задействованные ноды"
            dm["zh_CN"] = "-1 – 取消全选。\n 0 – 不做任何事。\n 1 – 选择涉及的节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIncludeMutedLinks').name) as dm:
            dm["ru_RU"] = "Разрешить выключенные линки"
            dm["zh_CN"] = "包含禁用的连线"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIncludeNonValidLinks').name) as dm:
            dm["ru_RU"] = "Разрешить невалидные линки"
            dm["zh_CN"] = "包含无效的连线"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isAccumulate').name) as dm:
            dm["ru_RU"] = "Накапливать"
            dm["zh_CN"] = "累积"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vrtIsLiveRanto').name) as dm:
            dm["ru_RU"] = "Ranto в реальном времени"
            dm["zh_CN"] = "实时对齐"
        with VlTrMapForKey(GetPrefsRnaProp('vrtIsFixIslands').name) as dm:
            dm["ru_RU"] = "Чинить острова"
            dm["zh_CN"] = "修复孤岛"