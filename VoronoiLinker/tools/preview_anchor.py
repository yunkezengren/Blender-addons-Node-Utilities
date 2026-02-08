import bpy
from ..base_tool import VoronoiToolSk
from ..common_forward_class import VptData
from ..globals import voronoiAnchorCnName, voronoiAnchorDtName

class VoronoiPreviewAnchorTool(VoronoiToolSk): #嗯, 现在这是一个完整的工具了; 甚至可能需要在布局中为其创建一个新的独立类别.
    bl_idname = 'node.voronoi_preview_anchor'
    bl_label = "Voronoi Preview Anchor"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    anchorType: bpy.props.IntProperty(name="Anchor type", default=0, min=0, max=2)
    isActiveAnchor: bpy.props.BoolProperty(name="Active anchor", default=True)
    isSelectAnchor: bpy.props.BoolProperty(name="Select anchor", default=True)
    isDeleteNonCanonAnchors: bpy.props.IntProperty(name="Clear anchors", default=0, min=0, max=2)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)[0]
            for ftg in list_ftgSksOut:
                if ftg.blid!='NodeSocketVirtual':
                    self.fotagoSk = ftg
                    break
            if self.fotagoSk:
                break
    def MatterPurposeTool(self, event, prefs, tree):
        VptData.reprSkAnchor = repr(self.fotagoSk.tar)
    def InitTool(self, event, prefs, tree):
        if self.isDeleteNonCanonAnchors:
            for nd in tree.nodes:
                if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                    tree.nodes.remove(nd)
            if self.isDeleteNonCanonAnchors==2:
                if nd:=tree.nodes.get(voronoiAnchorCnName):
                    tree.nodes.remove(nd)
            return {'FINISHED'}
        if self.anchorType:
            for nd in tree.nodes:
                nd.select = False
            match self.anchorType:
                case 1:
                    rrAnch = tree.nodes.get(voronoiAnchorCnName)
                    isFirstApr = not rrAnch #用于首次出现时处理的标记.
                    rrAnch = rrAnch or tree.nodes.new('NodeReroute')
                    rrAnch.name = voronoiAnchorCnName
                    rrAnch.label = voronoiAnchorCnName
                case 2:
                    sco = 0
                    tgl = True
                    while tgl:
                        sco += 1
                        name = voronoiAnchorDtName+str(sco)
                        tgl = not not tree.nodes.get(name, None)
                    isFirstApr = True
                    rrAnch = tree.nodes.new('NodeReroute')
                    rrAnch.name = name
                    rrAnch.label = voronoiAnchorDtName
            if self.isActiveAnchor:
                tree.nodes.active = rrAnch
            rrAnch.location = self.cursorLoc
            rrAnch.select = self.isSelectAnchor
            if isFirstApr:
                #为什么不呢. 反正很漂亮.
                rrAnch.inputs[0].type = 'COLLECTION' if self.anchorType==2 else 'MATERIAL' #对于插件树, 因为在其中下面的“硬闯”方式不起作用.
                rrAnch.outputs[0].type = rrAnch.inputs[0].type #以便链接的输出颜色相同.
                if self.anchorType==1:
                    #直接设置 `.type = 'CUSTOM'` 不起作用, 所以我们硬闯; 感谢 Blender 3.5 的更新:
                    nd = tree.nodes.new('NodeGroupInput')
                    tree.links.new(nd.outputs[-1], rrAnch.inputs[0])
                    tree.nodes.remove(nd)
            return {'FINISHED'}
