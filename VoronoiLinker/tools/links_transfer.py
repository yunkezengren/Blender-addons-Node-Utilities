from ..utils.solder import SolderSkLinks
from ..utils.node import GenFtgFromNd
from ..common_forward_func import sk_label_or_name
from ..base_tool import VoronoiToolPairNd, TemplateDrawSksToolHh, TemplateDrawNodeFull
import bpy

class VoronoiLinksTransferTool(VoronoiToolPairNd): #Todo2v6 与 VST 合并并变成 "PairAny" 的候选者.
    bl_idname = 'node.voronoi_links_transfer'
    bl_label = "Voronoi Links Transfer"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isByIndexes: bpy.props.BoolProperty(name="Transfer by indexes", default=False)
    def CallbackDrawTool(self, drata):
        # VLT 模式
        if not self.fotagoNd0:
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        elif (self.fotagoNd0)and(not self.fotagoNd1):
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1, tool_name="Transfer")
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        else:
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1, tool_name="Transfer")
            TemplateDrawNodeFull(drata, self.fotagoNd1, side=1, tool_name="Transfer")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoNd0 = None
        self.fotagoNd1 = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=False, cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if isFirstActivation:
                self.fotagoNd0 = ftgNd
            self.fotagoNd1 = ftgNd
            if self.fotagoNd0.tar==self.fotagoNd1.tar:
                self.fotagoNd1 = None
            # 成了. 现在 VL 有两个节点了.
            # 突然发现, 节点的“命中”位置简直是粘在它上面, 这在整个都是关于套接字的聚会中观察到相当不寻常.
            # 它应该滑动而不是粘住吗?. 大概不应该, 否则不可避免地会有轴向投影, 在视觉上“抹去”信息.
            # 而且它们都会随着光标移动而改变, 导致无法直观地知道谁是第一个, 谁是第二个,
            # 与粘住不同, 粘住时可以清楚地知道“这个是第一个”; 这对于这个工具尤其重要, 因为哪个节点被首先选择很重要.
            if prefs.dsIsSlideOnNodes: # 虽然不急, 但还是留着吧.
                if self.fotagoNd0:
                    self.fotagoNd0.pos = GenFtgFromNd(self.fotagoNd0.tar, self.cursorLoc, self.uiScale).pos
            break
    def MatterPurposeTool(self, event, prefs, tree):
        ndFrom = self.fotagoNd0.tar
        ndTo = self.fotagoNd1.tar
        def NewLink(sk, lk):
            if sk.is_output:
                tree.links.new(sk, lk.to_socket)
                if lk.to_socket.is_multi_input:
                    tree.links.remove(lk)
            else:
                tree.links.new(lk.from_socket, sk)
                tree.links.remove(lk)
        def GetOnlyVisualSks(puts):
            return [sk for sk in puts if sk.enabled and not sk.hide]
        SolderSkLinks(tree) # 否则在 vl_sold_links_final 上会是 '... has been removed'; 但也可以用普通的 'sk.links'.
        if not self.isByIndexes:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for sk in putsFrom:
                    for lk in sk.vl_sold_links_final:
                        if not lk.is_muted:
                            skTar = putsTo.get(sk_label_or_name(sk))
                            if skTar:
                                NewLink(skTar, lk)
        else:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for zp in zip(GetOnlyVisualSks(putsFrom), GetOnlyVisualSks(putsTo)):
                    for lk in zp[0].vl_sold_links_final:
                        if not lk.is_muted:
                            NewLink(zp[1], lk)
