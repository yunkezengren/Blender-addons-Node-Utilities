import bpy
from ..base_tool import unhide_node_reassign, SingleSocketTool
from ..utils.node import pick_near_target
from ..utils.ui import split_prop

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

class NODE_OT_voronoi_warper(SingleSocketTool):
    bl_idname = 'node.voronoi_warper'
    bl_label = "Voronoi Warper"
    bl_description = "A mini-branch of topology reverse-engineering (like VPT).\nTool for \"point jumps\" along sockets."
    use_for_custom_tree = True
    isZoomedTo: bpy.props.BoolProperty(name="Zoom to", default=True)
    isSelectReroutes: bpy.props.IntProperty(name="Select reroutes", default=1, min=-1, max=1, description="-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting linked reroutes")
    def find_targets_tool(self, _is_first_active, prefs, tree):
        def FindAnySk():
            tar_sk_out, tar_sk_in = None, None
            for tar in tar_sks_out:
                if (tar.tar.vl_sold_is_final_linked_cou)and(tar.idname!='NodeSocketVirtual'):
                    tar_sk_out = tar
                    break
            for tar in tar_sks_in:
                if (tar.tar.vl_sold_is_final_linked_cou)and(tar.idname!='NodeSocketVirtual'):
                    tar_sk_in = tar
                    break
            return pick_near_target(tar_sk_out, tar_sk_in)
        self.target_sk = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            if nd.type=='REROUTE': #todo0NA 以及这个要加入到通用的通用部分中.
                self.target_sk = tar_sks_in[0] if self.cursorLoc.x<nd.location.x else tar_sks_out[0]
            else:
                self.target_sk = FindAnySk()
            if self.target_sk:
                unhide_node_reassign(nd, self, cond=self.target_sk)
                break
    def handle_modal(self, event, prefs):
        if event.type==prefs.vwtSelectTargetKey:
            self.isSelectTargetKey = event.value=='PRESS'
    def run(self, event, prefs, tree):
        skTar = self.target_sk.tar
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
    def initialize(self, event, prefs, tree):
        self.isSelectTargetKey = prefs.vwtSelectTargetKey in GetSetOfKeysFromEvent(event)
        self.dict_saveRestoreRerouteSelecting = {} #见 `action='DESELECT'`.
        for nd in tree.nodes:
            if nd.type=='REROUTE':
                self.dict_saveRestoreRerouteSelecting[nd] = nd.select
    @staticmethod
    def draw_pref_settings(col, prefs):
        split_prop(col, prefs,'vwtSelectTargetKey', link_btn=True)
