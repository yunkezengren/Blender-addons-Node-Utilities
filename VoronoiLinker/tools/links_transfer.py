import bpy
from ..base_tool import TemplateDrawNodeFull, TemplateDrawSksToolHh, PairNodeTool
from ..common_func import sk_label_or_name
from ..utils.node import GenTarFromNd, is_socket_visible
from ..utils.solder import solder_sk_links
B = bpy.types

class NODE_OT_voronoi_links_transfer(PairNodeTool):
    bl_idname = 'node.voronoi_links_transfer'
    bl_label = "Voronoi Links Transfer"
    bl_description = "Tool for rare needs of transferring all links from one node to another.\nIn the future, it will most likely be merged with VST."
    use_for_custom_tree = True
    can_draw_in_pref_setting = False
    isByIndexes: bpy.props.BoolProperty(name="Transfer by indexes", default=False)
    def callback_draw_tool(self, drata):
        # VLT 模式
        if not self.target_nd0:
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        elif (self.target_nd0)and(not self.target_nd1):
            TemplateDrawNodeFull(drata, self.target_nd0, side=-1, tool_name="Transfer")
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        else:
            TemplateDrawNodeFull(drata, self.target_nd0, side=-1, tool_name="Transfer")
            TemplateDrawNodeFull(drata, self.target_nd1, side=1, tool_name="Transfer")
    def find_targets_tool(self, is_first_active, prefs, tree):
        if is_first_active:
            self.target_nd0 = None
        self.target_nd1 = None
        for tar_nd in self.get_nearest_nodes(includePoorNodes=False, cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE':
                continue
            if is_first_active:
                self.target_nd0 = tar_nd
            self.target_nd1 = tar_nd
            if self.target_nd0.tar==self.target_nd1.tar:
                self.target_nd1 = None
            # 成了. 现在 VL 有两个节点了.
            # 突然发现, 节点的“命中”位置简直是粘在它上面, 这在整个都是关于套接字的聚会中观察到相当不寻常.
            # 它应该滑动而不是粘住吗?. 大概不应该, 否则不可避免地会有轴向投影, 在视觉上“抹去”信息.
            # 而且它们都会随着光标移动而改变, 导致无法直观地知道谁是第一个, 谁是第二个,
            # 与粘住不同, 粘住时可以清楚地知道“这个是第一个”; 这对于这个工具尤其重要, 因为哪个节点被首先选择很重要.
            if prefs.dsIsSlideOnNodes: # 虽然不急, 但还是留着吧.
                if self.target_nd0:
                    self.target_nd0.pos = GenTarFromNd(self.target_nd0.tar, self.cursorLoc, self.uiScale).pos
            break
    def run(self, event, prefs, tree):
        from_node = self.target_nd0.tar
        to_node = self.target_nd1.tar
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
        solder_sk_links(tree) # 否则在 vl_sold_links_final 上会是 '... has been removed'; 但也可以用普通的 'sk.links'.
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
