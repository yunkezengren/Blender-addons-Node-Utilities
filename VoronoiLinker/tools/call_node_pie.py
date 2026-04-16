import bpy
from ..base_tool import unhide_node_reassign, AnyTargetTool
from ..common_class import Target

class NODE_OT_voronoi_call_node_pie(AnyTargetTool):
    """ Voronoi 联动 Node Pie """
    bl_idname = 'node.voronoi_call_node_pie'
    bl_label = "Voronoi Call Node Pie"
    can_draw_settings = False
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)

    def callback_draw_tool(self, drawer):
        self.template_draw_any(drawer, self.target_any, cond=False, tool_name="Node Pie Menu")

    def find_targets_tool(self, _is_first_active, prefs, tree):
        tar_sockets = self.nearest_target_sockets()
        nearest_tar_sk = next((sk for sk in tar_sockets if sk.tar.type != "CUSTOM"), None)
        self.target_any = nearest_tar_sk
        if nearest_tar_sk:
            unhide_node_reassign(nearest_tar_sk.tar.node, self, cond=self.target_any)

    def run(self, event, prefs, tree):
        path = repr(self.target_any.tar)  # 有效解决几何和材质节点 节点数据路径不太一样的问题
        bpy.ops.node_pie.call_node_pie("INVOKE_DEFAULT", reset_args=False, voronoi_call=True, socket_path=path)

    def initialize(self, event, prefs, tree):
        self.firstResult = None  # 从第一个节点获取操作“折叠”或“展开”，然后将其传输到所有其他节点。
