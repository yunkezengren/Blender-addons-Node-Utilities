import bpy
from ..base_tool import SingleNodeTool
from ..common_class import TryAndPass
from ..utils.drawing import draw_node_template
from ..utils.solder import solder_sk_links

class NODE_OT_voronoi_reset_node(SingleNodeTool):
    bl_idname = 'node.voronoi_reset_node'
    bl_label = "Voronoi Reset Node"
    bl_description = "Tool for resetting nodes without the need for aiming, with mouse guidance convenience\nand ignoring enumeration properties. Was created because NW had something similar."
    use_for_custom_tree = True
    can_draw_settings = False
    isResetEnums: bpy.props.BoolProperty(name="Reset enums", default=False)
    isResetOnDrag: bpy.props.BoolProperty(name="Reset on grag (not recommended)", default=False)
    isSelectResetedNode: bpy.props.BoolProperty(name="Select reseted node", default=True)
    def callback_draw(self, drawer):              # 小王-工具提示
        if self.isResetEnums:
            mode = "完全重置节点"
        else:
            mode = "重置节点"
        draw_node_template(drawer, self.target_nd, tool_name=mode)
        # self.template_draw_any(drawer, self.target_any, cond=self.toolMode=='NODE', tool_name=name)
    def VrntDoResetNode(self, ndTar, tree):
        ndNew = tree.nodes.new(ndTar.bl_idname)
        ndNew.location = ndTar.location
        with TryAndPass(): #SimRep的.
            for cyc, sk in enumerate(ndTar.outputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(ndNew.outputs[cyc], lk.to_socket)
            for cyc, sk in enumerate(ndTar.inputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(lk.from_socket, ndNew.inputs[cyc])
        if ndNew.type=='GROUP':
            ndNew.node_tree = ndTar.node_tree
        if not self.isResetEnums: #如果不重置枚举，则将它们转移到新节点上.
            for li in ndNew.rna_type.properties.items():
                if (not li[1].is_readonly)and(getattr(li[1],'enum_items', None)):
                    setattr(ndNew, li[0], getattr(ndTar, li[0]))
        tree.nodes.remove(ndTar)
        tree.nodes.active = ndNew
        ndNew.select = self.isSelectResetedNode
        return ndNew
    def find_targets(self, is_first_active, prefs, tree):
        solder_sk_links(tree)
        self.target_nd = None
        for tar_nd in self.get_nearest_nodes(includePoorNodes=True, cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE': #"你确定要重新创建转向节点吗？".
                continue
            self.target_nd = tar_nd
            if (self.isResetOnDrag)and(nd not in self.set_done):
                self.set_done.add(self.VrntDoResetNode(self.target_nd.tar, tree))
                self.find_targets(is_first_active, prefs, tree)
                #总的来说'isResetOnDrag'有点问题 -- 需要为新创建的节点重绘以获取其高度；或者我没什么好主意.
                #并且点会吸附到节点角落一帧.
            break
    def can_run(self):
        return (not self.isResetOnDrag)and(self.target_nd)
    def run(self, event, prefs, tree):
        self.VrntDoResetNode(self.target_nd.tar, tree)
    def initialize(self, event, prefs, tree):
        self.set_done = set() #没有这个会有非常“可怕”的行为，如果过度操作，很可能会崩溃.
