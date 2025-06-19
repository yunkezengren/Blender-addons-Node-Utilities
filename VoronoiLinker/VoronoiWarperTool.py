from .关于翻译的函数 import GetAnnotFromCls, VlTrMapForKey
from .VoronoiTool import VoronoiToolSk, CheckUncollapseNodeAndReNext


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


class VoronoiWarperTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_warper'
    bl_label = "Voronoi Warper"
    usefulnessForCustomTree = True
    isZoomedTo: bpy.props.BoolProperty(name="Zoom to", default=True)
    isSelectReroutes: bpy.props.IntProperty(name="Select reroutes", default=1, min=-1, max=1, description="-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting linked reroutes")
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        def FindAnySk():
            ftgSkOut, ftgSkIn = None, None
            for ftg in list_ftgSksOut:
                if (ftg.tar.vl_sold_is_final_linked_cou)and(ftg.blid!='NodeSocketVirtual'):
                    ftgSkOut = ftg
                    break
            for ftg in list_ftgSksIn:
                if (ftg.tar.vl_sold_is_final_linked_cou)and(ftg.blid!='NodeSocketVirtual'):
                    ftgSkIn = ftg
                    break
            return MinFromFtgs(ftgSkOut, ftgSkIn)
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            if nd.type=='REROUTE': #todo0NA 以及这个要加入到通用的通用部分中.
                self.fotagoSk = list_ftgSksIn[0] if self.cursorLoc.x<nd.location.x else list_ftgSksOut[0]
            else:
                self.fotagoSk = FindAnySk()
            if self.fotagoSk:
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk)
                break
    def ModalTool(self, event, prefs):
        if event.type==prefs.vwtSelectTargetKey:
            self.isSelectTargetKey = event.value=='PRESS'
    def MatterPurposeTool(self, event, prefs, tree):
        skTar = self.fotagoSk.tar
        bpy.ops.node.select_all(action='DESELECT')
        if skTar.vl_sold_is_final_linked_cou:
            def RecrRerouteWalkerSelecting(sk):
                for lk in sk.vl_sold_links_final:
                    nd = lk.to_node if sk.is_output else lk.from_node
                    if nd.type=='REROUTE':
                        if self.isSelectReroutes:
                            nd.select = self.isSelectReroutes>0
                        else:
                            nd.select = self.dict_saveRestoreRerouteSelecting[nd]
                        RecrRerouteWalkerSelecting(nd.outputs[0] if sk.is_output else nd.inputs[0])
                    else:
                        nd.select = True
            RecrRerouteWalkerSelecting(skTar)
            #可以为选中的节点添加颜色，但我不知道之后如何清除这些颜色。为此设置一个快捷键会太不方便使用.
            #Todo0v6SF 或者可以在节点上方绘制明亮的矩形一帧。但这可能与平滑缩放到目标的功能不兼容.
            if self.isSelectTargetKey:
                skTar.node.select = True
            tree.nodes.active = skTar.node
            if self.isZoomedTo:
                bpy.ops.node.view_selected('INVOKE_DEFAULT')
        else: #这个分支没有被使用.
            skTar.node.select = True
            if self.isZoomedTo:
                bpy.ops.node.view_selected('INVOKE_DEFAULT')
            skTar.node.select = False #很棒的技巧.
    def InitTool(self, event, prefs, tree):
        self.isSelectTargetKey = prefs.vwtSelectTargetKey in GetSetOfKeysFromEvent(event)
        self.dict_saveRestoreRerouteSelecting = {} #见 `action='DESELECT'`.
        for nd in tree.nodes:
            if nd.type=='REROUTE':
                self.dict_saveRestoreRerouteSelecting[nd] = nd.select
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vwtSelectTargetKey')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isZoomedTo').name) as dm:
            dm["ru_RU"] = "Центрировать"
            dm["zh_CN"] = "自动最大化显示"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectReroutes').name) as dm:
            dm["ru_RU"] = "Выделять рероуты"
            dm["zh_CN"] = "选择更改路线"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectReroutes').description) as dm:
            dm["ru_RU"] = "-1 – Де-выделять всех.\n 0 – Ничего не делать.\n 1 – Выделять связанные рероуты"
            dm["zh_CN"] = "-1 – 取消全选。\n 0 – 不做任何事。\n 1 – 选择相连的转向节点"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vwtSelectTargetKey').name) as dm:
            dm["ru_RU"] = "Клавиша выделения цели"
            dm["zh_CN"] = "选择目标快捷键"