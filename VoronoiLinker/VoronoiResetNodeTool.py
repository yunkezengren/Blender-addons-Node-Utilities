from .一些前向class import TryAndPass
from .关于sold的函数 import SolderSkLinks
from .关于绘制的函数 import TemplateDrawNodeFull
from .关于翻译的函数 import GetAnnotFromCls, VlTrMapForKey
from .关于翻译的函数 import *
from .关于节点的函数 import *
from .关于ui的函数 import *
from .关于颜色的函数 import *
from .VoronoiTool import *
from .关于sold的函数 import *
from .globals import *
from .一些前向class import *
from .一些前向func import *
from .关于绘制的函数 import *
from .VoronoiTool import VoronoiToolNd

class VoronoiResetNodeTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_reset_node'
    bl_label = "Voronoi Reset Node"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isResetEnums: bpy.props.BoolProperty(name="Reset enums", default=False)
    isResetOnDrag: bpy.props.BoolProperty(name="Reset on grag (not recommended)", default=False)
    isSelectResetedNode: bpy.props.BoolProperty(name="Select reseted node", default=True)
    def CallbackDrawTool(self, drata):              # 小王-工具提示
        if self.isResetEnums:
            mode = "完全重置节点"
        else:
            mode = "重置节点"
        TemplateDrawNodeFull(drata, self.fotagoNd, tool_name=mode)
        # self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE', tool_name=name)
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
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        SolderSkLinks(tree)
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=True, cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE': #"你确定要重新创建转向节点吗？".
                continue
            self.fotagoNd = ftgNd
            if (self.isResetOnDrag)and(nd not in self.set_done):
                self.set_done.add(self.VrntDoResetNode(self.fotagoNd.tar, tree))
                self.NextAssignmentTool(isFirstActivation, prefs, tree)
                #总的来说'isResetOnDrag'有点问题 -- 需要为新创建的节点重绘以获取其高度；或者我没什么好主意.
                #并且点会吸附到节点角落一帧.
            break
    def MatterPurposePoll(self):
        return (not self.isResetOnDrag)and(self.fotagoNd)
    def MatterPurposeTool(self, event, prefs, tree):
        self.VrntDoResetNode(self.fotagoNd.tar, tree)
    def InitTool(self, event, prefs, tree):
        self.set_done = set() #没有这个会有非常“可怕”的行为，如果过度操作，很可能会崩溃.
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetEnums').name) as dm:
            dm["ru_RU"] = "Восстанавливать свойства перечисления"
            dm["zh_CN"] = "恢复下拉列表里的选择"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetOnDrag').name) as dm:
            dm["ru_RU"] = "Восстанавливать при ведении курсора (не рекомендуется)"
            dm["zh_CN"] = "悬停时恢复(不推荐)"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectResetedNode').name) as dm:
            dm["ru_RU"] = "Выделять восстановленный нод"
            dm["zh_CN"] = "选择重置的节点"