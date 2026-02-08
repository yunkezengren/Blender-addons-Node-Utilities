import bpy
from ..base_tool import CheckUncollapseNodeAndReNext, VoronoiToolAny
from ..globals import Cursor_X_Offset, set_utilTypeSkFields
from ..utils.node import CompareSkLabelName, DoLinkHh, VlrtData, VlrtRememberLastSockets
from ..utils.solder import SolderSkLinks

fitVlrtModeItems = ( ('SOCKET', "For socket", "Using the last link created by some from the tools, create the same for the specified socket"),
                     ('NODE',   "For node",   "Using name of the last socket, find and connect for a selected node") )
class VoronoiLinkRepeatingTool(VoronoiToolAny): # 分离成单独的工具, 以免用意大利面条代码玷污神圣的地方 (最初只用于 VLT).
    bl_idname = 'node.voronoi_link_repeating'
    bl_label = "Voronoi Link Repeating"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVlrtModeItems)
    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE')
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        def IsSkBetweenFields(sk1, sk2):
            return (sk1.type in set_utilTypeSkFields)and( (sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
        skLastOut = self.skLastOut
        skLastIn = self.skLastIn
        if not skLastOut:
            return
        SolderSkLinks(tree) # 好像不重新焊接也能工作.
        self.fotagoAny = None
        cur_x_off_repeat = -Cursor_X_Offset if self.toolMode=='SOCKET' else 0     # 小王 这个有点特殊
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=cur_x_off_repeat):
            nd = ftgNd.tar
            if nd==skLastOut.node: # 排除自身节点.
                break #continue
            if self.toolMode=='SOCKET':
                list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=-Cursor_X_Offset)
                if skLastOut:
                    for ftg in list_ftgSksIn:
                        if (skLastOut.bl_idname==ftg.blid)or(IsSkBetweenFields(skLastOut, ftg.tar)):
                            can = True
                            for lk in ftg.tar.vl_sold_links_final:
                                if lk.from_socket==skLastOut: # 识别已有的链接, 并且不选择这样的套接字.
                                    can = False
                            if can:
                                self.fotagoAny = ftg
                                break
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny, flag=False)
            else:
                if skLastIn:
                    if nd.inputs:
                        self.fotagoAny = ftgNd
                    for sk in nd.inputs:
                        if CompareSkLabelName(sk, skLastIn):
                            if (sk.enabled)and(not sk.hide):
                                tree.links.new(skLastOut, sk) # 注意: 不是高级的; 为什么节点重复需要接口?.
            break
    def MatterPurposeTool(self, event, prefs, tree):
        if self.toolMode=='SOCKET':
            # 这里不需要检查套接字树是否相同, NextAssignmentTool() 中已经检查过了.
            # 同样不需要检查 skLastOut 是否存在, 参见其在 NextAssignmentTool() 中的拓扑.
            # 注意: VlrtRememberLastSockets() 中有 `.id_data` 的相同性检查.
            # 注意: 不需要检查树是否存在, 因为如果连接的套接字在这里存在, 那它就肯定在某个地方.
            DoLinkHh(self.skLastOut, self.fotagoAny.tar)
            VlrtRememberLastSockets(self.skLastOut, self.fotagoAny.tar) # 因为. 而且.. “自递归”?.
    def InitTool(self, event, prefs, tree):
        for txt in "Out", "In":
            txtAttSkLast = 'skLast'+txt
            txtAttReprLastSk = 'reprLastSk'+txt # 如果失败, 不记录任何东西.
            setattr(self, txtAttSkLast, None) # 为工具初始化并在下面赋值.
            if reprTxtSk:=getattr(VlrtData, txtAttReprLastSk):
                try:
                    sk = eval(reprTxtSk)
                    if sk.id_data==tree:
                        setattr(self, txtAttSkLast, sk)
                    else:
                        setattr(VlrtData, txtAttReprLastSk, "")
                except:
                    setattr(VlrtData, txtAttReprLastSk, "")
        # 注意: 原来, Ctrl-Z 会使(全局保存的) tree 链接变成 'ReferenceError: StructRNA of type ShaderNodeTree has been removed'.
