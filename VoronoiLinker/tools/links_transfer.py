import bpy
from ..base_tool import TemplateDrawNodeFull, TemplateDrawSksToolHh, VoronoiToolPairNd
from ..common_forward_func import sk_label_or_name
from ..utils.node import GenFtgFromNd, is_socket_visible
from ..utils.solder import SolderSkLinks
B = bpy.types

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
        from_node = self.fotagoNd0.tar
        to_node = self.fotagoNd1.tar
        def transfer_link(sk: B.NodeSocket, link: B.NodeLink):
            if sk.is_output:
                tree.links.new(sk, link.to_socket)
                if link.to_socket.is_multi_input:
                    tree.links.remove(link)
            else:
                tree.links.new(link.from_socket, sk)
                tree.links.remove(link)
        def get_visible_sockets(sockets: list[B.NodeSocket]):
            return [sk for sk in sockets if is_socket_visible(sk)]
        SolderSkLinks(tree) # 否则在 vl_sold_links_final 上会是 '... has been removed'; 但也可以用普通的 'sk.links'.
        if not self.isByIndexes:
            for from_sks, to_sks in [(from_node.inputs, to_node.inputs), (from_node.outputs, to_node.outputs)]:
                for sk in from_sks:
                    for link in sk.vl_sold_links_final:
                        if not link.is_muted:
                            skTar = to_sks.get(sk_label_or_name(sk))
                            if skTar:
                                transfer_link(skTar, link)
        else:
            for from_sks, to_sks in [(from_node.inputs, to_node.inputs), (from_node.outputs, to_node.outputs)]:
                for pair in zip(get_visible_sockets(from_sks), get_visible_sockets(to_sks)):
                    for link in pair[0].vl_sold_links_final:
                        if not link.is_muted:
                            transfer_link(pair[1], link)
