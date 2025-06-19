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
from .VoronoiTool import VoronoiToolPairSk

def is_unlink_route(node):
    if node.type == 'REROUTE' and (not (node.inputs[0].links or node.outputs[0].links)):
        return True       # 转接点没连线
    return False
link_same_socket_types = ['SHADER', 'STRING', 'GEOMETRY','OBJECT', 'COLLECTION', 'MATERIAL', 'TEXTURE', 'IMAGE']
# 最初, 整个插件都是为了这个工具而创建的. 你以为为什么名字都一样.
# 但后来我被这些已掌握的能力惊呆了, 开始创作了主流三巨头. 但这还不够, 现在工具有7个以上. 太棒了!
# 重复的注释只在这里 (并且总体上递减). 如有争议, 请参考 VLT, 将其视为最终真理.
class VoronoiLinkerTool(VoronoiToolPairSk): # 神圣中的神圣. 它存在的理由. 最初的那个. 所有工具的老大. 为了伟大的距离场而荣耀!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSkOut, self.fotagoSkIn, sideMarkHh=-1, isClassicFlow=True, tool_name="Linker")
    @staticmethod
    def SkPriorityIgnoreCheck(sk): #False -- 忽略.
        # 这个函数是应外部请求添加的 (就像 VLNST).
        set_ndBlidsWithAlphaSk = {'ShaderNodeTexImage', 'GeometryNodeImageTexture', 'CompositorNodeImage', 'ShaderNodeValToRGB', 'CompositorNodeValToRGB'}
        if sk.node.bl_idname in set_ndBlidsWithAlphaSk:
            return sk.name!="Alpha" #sk!=sk.node.outputs[1]
        return True
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): #Todo0NA ToolAssignmentFirst, Next, /^Root/; 多个 NA(), 第一个节点套接字, 第二个节点套接字.
        # 如果没有找到合适的, 上一个选择会保留, 导致无法将光标移回并“取消”选择, 这非常不方便.
        self.fotagoSkIn = None # 所以每次搜索前都会清零.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=-20):
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=-20)
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    if (self.isFirstCling)or(ftg.blid!='NodeSocketVirtual')and( (not prefs.vltPriorityIgnoring)or(self.SkPriorityIgnoreCheck(ftg.tar)) ):
                        self.fotagoSkOut = ftg
                        break
            self.isFirstCling = True
            # 根据条件获取输入:
            skOut = FtgGetTargetOrNone(self.fotagoSkOut)
            if skOut: # 第一次进入总是 isFirstActivation==True, 但节点可能没有输出.
                # 注意: 工具激活套接字的节点 (isFirstActivation==True) 无论如何都需要展开.
                # 折叠对于 reroute 是有效的, 尽管在视觉上不显示; 但现在不需要处理了, 因为已经引入了对折叠的支持.
                CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
                # 在这个阶段, 否定的条件只会找到另一个结果. "不粘这个, 就粘另一个".
                for ftg in list_ftgSksIn:
                    # 注意: `|=` 操作符仍然会强制计算右操作数.
                    skIn = ftg.tar
                    # 对于允许的组内连接, 允许“转换”. 为了方便, reroute 可以连接到两侧的任何套接字, 绕过不同类型
                    tgl = self.SkBetweenFieldsCheck(skIn, skOut)or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(prefs.vltReroutesCanInAnyType)
                    # 接口处理已移至 VIT, 现在只在虚拟之间
                    tgl = (tgl)or( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') )
                    # 如果类型名称相同
                    tgl = (tgl)or(skIn.bl_idname==skOut.bl_idname) # 注意: 包括插件套接字.
                    # 如果经典树中有插件套接字 -- 也可以连接到所有经典套接字, 经典套接字可以连接到所有插件套接字
                    tgl = (tgl)or(self.isInvokeInClassicTree)and(IsClassicSk(skOut)^IsClassicSk(skIn))
                    # 限制旋转和矩阵接口
                    if skOut.type == "MATRIX":
                        tgl = (skIn.type in ["MATRIX", "ROTATION"])
                    if skOut.type == "ROTATION":
                        tgl = (skIn.type in ["ROTATION", "MATRIX", "VECTOR"])
                    # 只能连到相同类型的接口上
                    if skOut.type in link_same_socket_types:
                        tgl = skIn.type==skOut.type
                    if skIn.type in link_same_socket_types:
                        tgl = skIn.type==skOut.type
                    # 没连线的转接点,就都可以连
                    if is_unlink_route(skOut.node):
                        tgl = True
                    if is_unlink_route(skIn.node):      # from_socket 
                        tgl = True
                    # 注意: SkBetweenFieldsCheck() 只检查字段之间, 所以需要显式检查 `bl_idname` 是否相同.
                    if tgl:
                        self.fotagoSkIn = ftg
                        break # 只需要处理第一个最近的满足条件的. 否则结果会是最远的.
                # 在这个阶段, 否定的条件会使结果为空. 就像“什么都没找到”; 并且会相应地绘制.
                if self.fotagoSkIn:
                    if self.fotagoSkOut.tar.node==self.fotagoSkIn.tar.node: # 如果输出的最近输入是它自己的节点
                        self.fotagoSkIn = None
                    elif self.fotagoSkOut.tar.vl_sold_is_final_linked_cou: # 如果输出已经连接到某个地方, 即使是禁用的链接 (但由于焊接, 它们不存在).
                        for lk in self.fotagoSkOut.tar.vl_sold_links_final:
                            if lk.to_socket==self.fotagoSkIn.tar: # 如果最近的输入是输出的连接之一, 则置空 => “期望的”连接已经存在.
                                self.fotagoSkIn = None
                                # 上面检查中使用的 "self.fotagoSkIn" 被置空了, 所以需要退出, 否则下一次迭代会尝试读取不存在的元素.
                                break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkIn, flag=False) # “主流的”折叠处理.
            break # 只需要处理第一个最近的满足条件的. 否则结果会是最远的.
    def ModalMouseNext(self, event, prefs):
        if event.type==prefs.vltRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState: # 从下面复制. 不知道如何一次性搞定.
                self.NextAssignmentRoot(True)
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState: # 注意: 要求存在, 调用方负责.
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    if event.value=='RELEASE':
                        return True
        return False
    def MatterPurposePoll(self):
        return self.fotagoSkOut and self.fotagoSkIn
    def MatterPurposeTool(self, event, prefs, tree):
        sko = self.fotagoSkOut.tar
        ski = self.fotagoSkIn.tar
        ##
        tree.links.new(sko, ski) # 最重要的一行又变成了低级的.
        ##
        if ski.is_multi_input: # 如果是多输入, 实现合理的连接顺序.
            # 我个人的愿望, 它修复了奇怪的行为, 使其逻辑上正确可预期. 为什么通过 api 最后连接的会被粘到开头?
            list_skLinks = []
            for lk in ski.vl_sold_links_final:
                # 记住所有现有的套接字链接, 并删除它们:
                list_skLinks.append((lk.from_socket, lk.to_socket, lk.is_muted))
                tree.links.remove(lk)
            # 在 b3.5 版本之前, 下面的处理是必要的, 以防止新的组 io 被创建两次.
            # 现在没有这个处理, Blender 要么崩溃, 要么从虚拟到多输入的链接无效
            if sko.bl_idname=='NodeSocketVirtual':
                sko = sko.node.outputs[-2]
            tree.links.new(sko, ski) # 将下一个连接为第一个.
            for li in list_skLinks: # 恢复记住的. #todo0VV 为了支持旧版本: 以前是 [:-1], 因为列表中的最后一个已经是期望的, 由上面一行连接.
                tree.links.new(li[0], li[1]).is_muted = li[2]
        VlrtRememberLastSockets(sko, ski) # 记住 VLRT 的套接字, 它们现在是“最后使用的”.
        if prefs.vltSelectingInvolved:
            for nd in tree.nodes:
                nd.select = False
            sko.node.select = True
            ski.node.select = True
            tree.nodes.active = sko.node # P.s. 不知道为什么是它; 也可以是 ski. 把这个做成选项感觉不太好.
    def InitTool(self, event, prefs, tree):
        self.fotagoSkOut = None
        self.fotagoSkIn = None
        self.repickState = False
        self.isFirstCling = False # 用于 SkPriorityIgnoreCheck 和重新选择虚拟.
        if prefs.vltDeselectAllNodes:
            bpy.ops.node.select_all(action='DESELECT')
            tree.nodes.active = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vltRepickKey')
        LyAddLeftProp(col, prefs,'vltReroutesCanInAnyType')
        LyAddLeftProp(col, prefs,'vltDeselectAllNodes')
        LyAddLeftProp(col, prefs,'vltPriorityIgnoring')
        LyAddLeftProp(col, prefs,'vltSelectingInvolved')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetPrefsRnaProp('vltRepickKey').name) as dm:
            dm["ru_RU"] = "Клавиша перевыбора"
            dm["zh_CN"] = "重选快捷键"
        with VlTrMapForKey(GetPrefsRnaProp('vltReroutesCanInAnyType').name) as dm:
            dm["ru_RU"] = "Рероуты могут подключаться в любой тип"
            dm["zh_CN"] = "重新定向节点可以连接到任何类型的节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltDeselectAllNodes').name) as dm:
            dm["ru_RU"] = "Снять выделение со всех нодов при активации"
            dm["zh_CN"] = "快速连接时取消选择所有节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').name) as dm:
            dm["ru_RU"] = "Приоритетное игнорирование"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').description) as dm:
            dm["ru_RU"] = "Высокоуровневое игнорирование \"надоедливых\" сокетов при первом поиске.\n(Сейчас только \"Alpha\"-сокет у нод изображений)"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltSelectingInvolved').name) as dm:
            dm["ru_RU"] = "Выделять задействованные ноды"
            dm["zh_CN"] = "快速连接后自动选择连接的节点"