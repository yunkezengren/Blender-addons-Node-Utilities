import bpy
from ..base_tool import unhide_node_reassign, draw_sockets_template, SingleSocketTool
from ..utils.node import pick_near_target, vlrt_remember_last_sockets
from ..utils.ui import add_nice_color_prop

class NODE_OT_voronoi_dummy(SingleSocketTool):   # 快速便捷地添加新工具的模板
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    use_for_custom_tree = True
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def callback_draw(self, drawer):
        draw_sockets_template(drawer, self.target_sk)
    def find_targets(self, _is_first_active, prefs, tree):
        self.target_sk = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE':
                continue
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            tar_sk_in = tar_sks_in[0] if tar_sks_in else None
            tar_sk_out = tar_sks_out[0] if tar_sks_out else None
            self.target_sk = pick_near_target(tar_sk_out, tar_sk_in)
            unhide_node_reassign(nd, self, cond=self.target_sk, flag=False)
            break
        #todo0NA Я придумал что делать с концепцией, когда имеются разные критерии от is_first_active'а, и второй находится сразу рядом после первого моментально. Явное (и насильное) сравнение на своего и отмена.
    def can_run(self):
        return not not self.target_sk
    def run(self, event, prefs, tree):
        sk = self.target_sk.tar
        sk.name = sk.name if (sk.name)and(sk.name[0]=="\"") else f'"{sk.name}"'
        sk.node.label = "Hi i am vdt. See source code"
        vlrt_remember_last_sockets(sk if sk.is_output else None, None)
    def initialize(self, event, prefs, tree):
        self.target_sk = None
    @staticmethod
    def draw_pref_settings(col, prefs):
        add_nice_color_prop(col, prefs,'vdt_dummy')
