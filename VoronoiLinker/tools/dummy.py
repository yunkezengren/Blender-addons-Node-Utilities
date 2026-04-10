import bpy
from ..base_tool import unhide_node_reassign, TemplateDrawSksToolHh, SingleSocketTool
from ..utils.node import MinFromFtgs, VlrtRememberLastSockets
from ..utils.ui import LyAddNiceColorProp

class NODE_OT_voronoi_dummy(SingleSocketTool):   # 快速便捷地添加新工具的模板
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    usefulnessForCustomTree = True
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def callback_draw_tool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def find_targets_tool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.get_nearest_nodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.get_nearest_sockets(nd, cur_x_off=0)
            ftgSkIn = list_ftgSksIn[0] if list_ftgSksIn else None
            ftgSkOut = list_ftgSksOut[0] if list_ftgSksOut else None
            self.fotagoSk = MinFromFtgs(ftgSkOut, ftgSkIn)
            unhide_node_reassign(nd, self, cond=self.fotagoSk, flag=False)
            break
        #todo0NA Я придумал что делать с концепцией, когда имеются разные критерии от isFirstActivation'а, и второй находится сразу рядом после первого моментально. Явное (и насильное) сравнение на своего и отмена.
    def can_run(self):
        return not not self.fotagoSk
    def run(self, event, prefs, tree):
        sk = self.fotagoSk.tar
        sk.name = sk.name if (sk.name)and(sk.name[0]=="\"") else f'"{sk.name}"'
        sk.node.label = "Hi i am vdt. See source code"
        VlrtRememberLastSockets(sk if sk.is_output else None, None)
    def initialize(self, event, prefs, tree):
        self.fotagoSk = None
    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        LyAddNiceColorProp(col, prefs,'vdtDummy')
