import bpy
from bpy.app.translations import pgettext_iface as _iface
from ..base_tool import CheckUncollapseNodeAndReNext, VoronoiToolTripleSk
from ..common_forward_class import VmtData
from ..common_forward_func import DisplayMessage, SetPieData
from ..globals import Cursor_X_Offset
from ..utils.color import get_sk_color_safe, power_color4
from ..utils.drawing import TemplateDrawSksToolHh
from ..utils.node import opt_ftg_socket
from ..utils.ui import LyAddHandSplitProp, LyAddLabeledBoxCol, LyAddLeftProp
from .mixer_sub import DoMix, mixer_default, mixer_tree_sk_nodes, VmtPieMixer

class VoronoiMixerTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #放在第一位, 以便在 kmi 中与 VQMT 类似.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Mix")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None #需要清空, 因为下面有两个 continue.
        if not self.canPickThird:
            self.fotagoSk1 = None
        soldReroutesCanInAnyType = prefs.vmtReroutesCanInAnyType
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            if not list_ftgSksOut:
                continue
            #节点过滤器没有必要.
            #这个工具会触发第一个遇到的任何输出 (现在除了虚拟接口).
            if isFirstActivation:
                self.fotagoSk0 = list_ftgSksOut[0] if list_ftgSksOut else None
            #对于第二个, 根据条件:
            skOut0 = opt_ftg_socket(self.fotagoSk0)
            # todo 做一些接口类型判断,比如 一个是 geometry 剩下的也要是
            if skOut0:
                if not self.canPickThird:
                    for ftg in list_ftgSksOut:
                        skOut1 = ftg.tar
                        if skOut0 == skOut1:
                            break
                        orV = (skOut1.bl_idname == 'NodeSocketVirtual') or (skOut0.bl_idname == 'NodeSocketVirtual')
                        #现在 VMT 又可以连接到虚拟接口了
                        tgl = (skOut1.bl_idname == 'NodeSocketVirtual') ^ (skOut0.bl_idname == 'NodeSocketVirtual')
                        tgl = tgl or (self.SkBetweenFieldsCheck(skOut0, skOut1) or ((skOut1.bl_idname == skOut0.bl_idname) and (not orV)))
                        tgl = tgl or ((skOut0.node.type == 'REROUTE') or (skOut1.node.type == 'REROUTE')) and (soldReroutesCanInAnyType)
                        if tgl:
                            self.fotagoSk1 = ftg
                            break
                    if (self.fotagoSk1) and (skOut0 == self.fotagoSk1.tar): #检查是否是自我复制.
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
                    if self.fotagoSk1:
                        break
                else:
                    skOut1 = opt_ftg_socket(self.fotagoSk1)
                    for ftg in list_ftgSksOut:
                        self.fotagoSk2 = ftg
                        if (ftg.tar == skOut0) or (ftg.tar == skOut1):
                            self.fotagoSk2 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
                    if self.fotagoSk2:
                        break
            #尽管节点过滤器没有必要, 并且在第一个遇到的节点上工作得很好, 但如果第一个接口没有找到, 仍然需要继续搜索.
            #因为如果第一个(最近的)节点搜索结果失败, 循环将结束, 工具将不会选择任何东西, 即使旁边有合适的.
            if self.fotagoSk0:  # 在使用现在不存在的 isCanReOut 时尤其明显; 如果没有这个, 结果会根据光标位置成功/不成功地选择.
                break
    def MatterPurposePoll(self):
        if not self.fotagoSk0:
            return False
        if self.isCanFromOne:
            return (self.fotagoSk0.blid!='NodeSocketVirtual')or(self.fotagoSk1)
        else:
            return self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        VmtData.sk0 = self.fotagoSk0.tar
        socket1 = opt_ftg_socket(self.fotagoSk1)
        VmtData.sk1 = socket1
        #对虚拟接口的支持已关闭; 只从第一个读取
        VmtData.sk2 = opt_ftg_socket(self.fotagoSk2)
        VmtData.skType = VmtData.sk0.type if VmtData.sk0.bl_idname!='NodeSocketVirtual' else socket1.type
        VmtData.isHideOptions = self.isHideOptions
        VmtData.isPlaceImmediately = self.isPlaceImmediately
        _sk = VmtData.sk0
        if socket1 and socket1.type == "MATRIX":
            VmtData.skType = "MATRIX"
            _sk = VmtData.sk1
        SetPieData(self, VmtData, prefs, power_color4(get_sk_color_safe(_sk), pw=2.2))
        if not self.in_builtin_tree: #由于 usefulnessForCustomTree, 这是个无用的检查.
            return {'CANCELLED'} #如果操作地点不在经典编辑器中, 就直接退出. 因为经典编辑器对所有人都一样, 而插件编辑器有无数种.

        default_nodes = mixer_default.get(tree.bl_idname, None)
        tup_nodes = mixer_tree_sk_nodes.get(tree.bl_idname, False).get(VmtData.skType, default_nodes)
        if tup_nodes:
            if len(tup_nodes) == 1:  #如果只有一个选择, 就跳过它直接进行混合.
                DoMix(tree, False, False, tup_nodes[0])  #在即时激活时, 可能没有释放修饰键. 因此 DoMix() 接收的是手动设置而不是 event.
            else: #否则提供选择
                bpy.ops.wm.call_menu_pie(name=VmtPieMixer.bl_idname)
        else: #否则接口类型未定义 (例如几何节点中的着色器).
            # ! 草
            txt_vmtNoMixingOptions = "No mixing options"
            DisplayMessage(self.bl_label, txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmtReroutesCanInAnyType')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        colBox = LyAddLabeledBoxCol(colLy, text=_iface("Pie")+f" ({cls.vlTripleName})")
        tlw = cls.vlTripleName.lower()
        LyAddHandSplitProp(colBox, prefs,f'{tlw}PieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieScale')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieAlignment')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieDisplaySocketColor')
        colProps.active = getattr(prefs,f'{tlw}PieType')=='CONTROL'

