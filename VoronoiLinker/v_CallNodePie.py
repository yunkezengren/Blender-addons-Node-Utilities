import bpy
from .v_tool import *
from .globals import *
from .utils_ui import *
from .utils_node import *
from .utils_color import *
from .utils_solder import *
from .utils_drawing import *
from .utils_translate import *
from .common_forward_func import *
from .common_forward_class import *
from .v_tool import VoronoiToolAny


class VoronoiCallNodePie(VoronoiToolAny):
    """ Voronoi 联动 Node Pie """
    bl_idname = 'node.voronoi_call_node_pie'
    bl_label = "Voronoi联动节点饼菜单插件"
    # toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVhtModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)

    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=False, tool_name="节点饼菜单")
        # TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name="节点饼菜单")
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        # pprint(self.__dict__)
        self.fotagoAny: Fotago = None
        ftg_nodes = self.ToolGetNearestNodes()     # ->list[Fotago] <class Fotago> 这里 .tar 是 Node
        # pprint(ftg_nodes[0].__dict__)
        node_count = 5 if len(ftg_nodes) >= 5 else len(ftg_nodes)
        node_count = min(5, len(ftg_nodes))
        ftg_sockets: list[Fotago] = []
        # 优化了最近接口的获取
        for fotago in ftg_nodes[:node_count]:
            nd = fotago.tar
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            # self.fotagoAny = ftgNd
            # 这的最近节点的输入输出接口，有时候最近的是输出节口，但是没有离最近的节点的输入接口更近，所以把最近的几个节点接口列表合并
            ftg_sks_in, ftg_sks_out = self.ToolGetNearestSockets(nd)   # ->([], [])  <class Fotago> 这里 .tar 是 Socket
            ftg_sockets.extend(ftg_sks_in)
            ftg_sockets.extend(ftg_sks_out)
        ftg_sockets.sort(key=lambda soc: soc.dist)
        near_ftg_soc = None
        for ftg_sk in ftg_sockets:
            if ftg_sk.blid != "NodeSocketVirtual":
                near_ftg_soc = ftg_sk
                break
        # pprint(ftg_sockets[0].__dict__)
        self.fotagoAny = near_ftg_soc
        if near_ftg_soc:
            CheckUncollapseNodeAndReNext(near_ftg_soc.tar.node, self, cond=self.fotagoAny) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.

    def MatterPurposeTool(self, event, prefs, tree):
        # print(tar)    print(str(tar))          <bpy_struct, NodeSocketVector("Vector") at 0x000002435EFED588>
        # pprint(tar)   pprint(eval(repr(tar)))  bpy.data.node_groups['Geometry Nodes'].nodes["Vector Math"].outputs[0]
        path = repr(self.fotagoAny.tar)     # 有效解决几何和材质节点 节点数据路径不太一样的问题
        # print(self.fotagoAny.tar)
        # pprint(self.fotagoAny.tar)
        # print(repr(self.fotagoAny.tar))
        bpy.ops.node_pie.call_node_pie("INVOKE_DEFAULT", reset_args=False, voronoi_call=True, socket_path=path)

    def InitTool(self, event, prefs, tree):
        self.firstResult = None     # 从第一个节点获取操作“折叠”或“展开”，然后将其传输到所有其他节点。
