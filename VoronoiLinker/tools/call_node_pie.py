import bpy
from ..base_tool import unhide_node_reassign, AnyTargetTool
from ..common_class import Target

class NODE_OT_voronoi_call_node_pie(AnyTargetTool):
    """ Voronoi 联动 Node Pie """
    bl_idname = 'node.voronoi_call_node_pie'
    bl_label = "Voronoi Call Node Pie"
    can_draw_in_pref_setting = False
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)

    def callback_draw_tool(self, drawer):
        self.template_draw_any(drawer, self.target_any, cond=False, tool_name="Node Pie Menu")

    def find_targets_tool(self, _is_first_active, prefs, tree):
        self.target_any: Target = None
        tar_nodes = self.get_nearest_nodes()  # ->list[Target] <class Target> 这里 .tar 是 Node
        node_count = 5 if len(tar_nodes) >= 5 else len(tar_nodes)
        node_count = min(5, len(tar_nodes))
        tar_sockets: list[Target] = []
        # 优化了最近接口的获取
        for fotago in tar_nodes[:node_count]:
            nd = fotago.tar
            if (not self.isTriggerOnCollapsedNodes) and (nd.hide):
                continue
            # 这的最近节点的输入输出接口，有时候最近的是输出节口，但是没有离最近的节点的输入接口更近，所以把最近的几个节点接口列表合并
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd)  # ->([], [])  <class Target> 这里 .tar 是 Socket
            tar_sockets.extend(tar_sks_in)
            tar_sockets.extend(tar_sks_out)
        tar_sockets.sort(key=lambda soc: soc.dist)
        near_tar_sk = None
        for tar_sk in tar_sockets:
            if tar_sk.blid != "NodeSocketVirtual":
                near_tar_sk = tar_sk
                break
        self.target_any = near_tar_sk
        if near_tar_sk:
            unhide_node_reassign(
                near_tar_sk.tar.node, self,
                cond=self.target_any)  #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.

    def run(self, event, prefs, tree):
        path = repr(self.target_any.tar)  # 有效解决几何和材质节点 节点数据路径不太一样的问题
        bpy.ops.node_pie.call_node_pie("INVOKE_DEFAULT", reset_args=False, voronoi_call=True, socket_path=path)

    def initialize(self, event, prefs, tree):
        self.firstResult = None  # 从第一个节点获取操作“折叠”或“展开”，然后将其传输到所有其他节点。
