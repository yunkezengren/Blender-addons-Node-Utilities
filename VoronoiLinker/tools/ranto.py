import bpy
from bpy.app.translations import pgettext_iface as _iface
from ..base_tool import SingleNodeTool
from ..common_func import DisplayMessage
from ..utils.ui import LyAddLeftProp

# 现在 RANTO 已经集成到 VL 中了. 连我自己都感到意外.
# 参见原版: https://github.com/ugorek000/RANTO

class RantoData():
    def __init__(self, isOnlySelected=0, widthNd=140, isUniWid=False, indentX=40, indentY=30, isIncludeMutedLinks=False, isIncludeNonValidLinks=False, isFixIslands=True):
        self.kapibara = ""
        self.dict_ndTopoWorking = {}

def VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, ndRoot):
    rada.kapibara = "kapibara"


class NODE_OT_voronoi_ranto(SingleNodeTool): #完成了.
    bl_idname = 'node.voronoi_ranto'
    bl_label = "Voronoi RANTO"
    use_for_custom_tree = True
    use_for_none_tree = True
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
    def find_targets_tool(self, _is_first_active, prefs, tree):
        self.target_nd = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE':
                continue #为此，请参考原始的RANTO插件.
            self.target_nd = tar_nd
            #if not self.ndMaxAccRoot:
            #    self.ndMaxAccRoot = nd
            if prefs.vrtIsLiveRanto:
                self.DoRANTO(nd, tree, prefs.vrtIsFixIslands)
            break
    def run(self, event, prefs, tree):
        ndTar = self.target_nd.tar
        #if self.isAccumulate:
        #    self.ndMaxAccRoot = None
        #    self.lastNdProc = None
        self.DoRANTO(ndTar, tree, prefs.vrtIsFixIslands)
        DisplayMessage("RANTO", _iface("This tool is empty")+" ¯\_(ツ)_/¯")
    def initialize(self, event, prefs, tree):
        self.lastNdProc = None
        #self.ndMaxAccRoot = None
    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        LyAddLeftProp(col, prefs,'vrtIsLiveRanto')
        LyAddLeftProp(col, prefs,'vrtIsFixIslands')
