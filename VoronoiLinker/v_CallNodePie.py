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
    bl_label = "Voronoi Call Node Pie"
    # toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVhtModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)

    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=False, tool_name="节点饼菜单")
        # TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name="节点饼菜单")
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        # pprint(self.__dict__)
        self.fotagoAny = None
        Fotago_nodes = self.ToolGetNearestNodes()     # ->list[Fotago] <class Fotago> 这里 .tar 是 Node
        # pprint(Fotago_nodes[0].__dict__)
        node_count = 5 if len(Fotago_nodes) >= 5 else len(Fotago_nodes)
        Fotago_sockets = []
        # 优化了最近接口的获取
        for ftgNd in Fotago_nodes[:node_count]:
            nd = ftgNd.tar
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            self.fotagoAny = ftgNd
            # 这的最近节点的输入输出接口，有时候最近的是输出节口，但是没有离最近的节点的输入接口更近，所以把最近的几个节点接口列表合并
            l_ftgSksIn, l_ftgSksOut = self.ToolGetNearestSockets(nd)   # ->([], [])  <class Fotago> 这里 .tar 是 Socket
            Fotago_sockets.extend(l_ftgSksIn)
            Fotago_sockets.extend(l_ftgSksOut)
        Fotago_sockets.sort(key=lambda soc: soc.dist)
        near_ftg_soc = Fotago_sockets[0] if Fotago_sockets else []
        # pprint(Fotago_sockets[0].__dict__)
        self.fotagoAny = near_ftg_soc
        if near_ftg_soc:
            CheckUncollapseNodeAndReNext(near_ftg_soc.tar.node, self, cond=self.fotagoAny) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.

    def MatterPurposeTool(self, event, prefs, tree):
        # print(self.fotagoAny)
        # print(self.fotagoAny.tar)
        # pprint(self.fotagoAny.__dict__)
        # print(dict_str)
        dict_str = str(self.fotagoAny.__dict__)
        start = dict_str.find("bpy.data")
        end = dict_str.find("],")
        path = dict_str[start:end+1]
        print(path)
        # bpy.data.materials['Material'].node_tree.nodes["Principled BSDF"].outputs[0]
        # bpy.data.scenes['Scene'].node_tree.nodes["Render Layers"].outputs[0]
        # bpy.data.node_groups['Geometry Nodes.002'].nodes["Group Input"].outputs[0]
        # socket = self.fotagoAny.tar;socket_id = socket.identifier;node = socket.node;group_name = node.id_data.name;in_out = "outputs" if socket.is_output else "inputs"
        # path = f"bpy.data.node_groups['{group_name}'].nodes['{node.name}'].{in_out}['{socket_id}']"   # 只适合几何节点,材质合成还不一样
        bpy.ops.node_pie.call_node_pie("INVOKE_DEFAULT", reset_args=False, vor_call=True, socket_path=path)

    def InitTool(self, event, prefs, tree):
        self.firstResult = None #Получить действие у первого нода "свернуть" или "развернуть", а потом транслировать его на все остальные попавшиеся.
