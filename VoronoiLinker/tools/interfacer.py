from enum import Enum

import bpy
from mathutils import Vector as Vec
from bpy.types import NodeTree
from ..base_tool import unhide_node_reassign, TemplateDrawNodeFull, TemplateDrawSksToolHh, PairSocketTool
from ..node_items import NodeItemsUtils
from ..common_func import sk_label_or_name
from ..globals import set_utilEquestrianPortalBlids
from ..utils.color import Color4, get_sk_color_safe
from ..utils.drawing import DrawVlSocketArea
from ..utils.node import DoLinkHh, FindAnySk, MinFromFtgs, opt_ftg_socket
from ..utils.ui import draw_hand_split_prop

# yapf: disable
class InterfacerMode(Enum):
    COPY   = 'COPY'
    PASTE  = 'PASTE'
    SWAP   = 'SWAP'
    FLIP   = 'FLIP'
    NEW    = 'NEW'
    CREATE = 'CREATE'
    TYPE   = 'TYPE'

eMode = InterfacerMode
ModeItems = (
    (eMode.COPY.value,   "Copy",   "Copy a socket name to clipboard"),
    (eMode.PASTE.value,  "Paste",  "Paste the contents of clipboard into an interface name"),
    (eMode.SWAP.value,   "Swap",   "Swap a two interfaces"),
    (eMode.FLIP.value,   "Flip",   "Move the interface to a new location, shifting everyone else"),
    (eMode.NEW.value,    "New",    "Create an interface using virtual sockets"),
    (eMode.CREATE.value, "Create", "Create an interface from a selected socket, and paste it into a specified location"),
    # (eMode.DELETE.value, "Delete", "Delete one socket"),
    (eMode.TYPE.value,   "Type", "Change socket type"),
)
# yapf: enable

class NODE_OT_voronoi_interfacer(PairSocketTool):
    bl_idname = 'node.voronoi_interfacer'
    bl_label = "Voronoi Interfacer"
    bl_description = "A tool on the level of \"The Great Trio\". A branch from VLT for convenient acceleration\nof the creation process and special manipulations with interfaces. \"Interface Manager\"."
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default=eMode.NEW.value, items=ModeItems)

    def CallbackDrawTool(self, drata):
        match eMode(self.toolMode):
            case eMode.NEW:
                TemplateDrawSksToolHh(drata, self.fotagoSkRosw, self.fotagoSkMain, isClassicFlow=True, tool_name="Connect to Extend Socket")
            case eMode.CREATE:
                ftgMain = self.fotagoSkMain
                if ftgMain:
                    TemplateDrawSksToolHh(drata, ftgMain, sideMarkHh=-2, tool_name="Insert to Socket")
                ftgNdTar = self.fotagoNdTar
                if ftgNdTar:
                    TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Node Group")
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ftgNdTar.tar, cur_x_off=0)
                    if not list_ftgSksIn: return
                    near_group_in = list_ftgSksIn[0]  # 节点组可能没有输入接口:

                    y = ftgNdTar.pos.y
                    boxHeiBound = Vec((y - 7, y + 7))
                    DrawVlSocketArea(drata, near_group_in.tar, boxHeiBound, Color4(get_sk_color_safe(ftgMain.tar)))
            case eMode.FLIP:  # 失败
                # ftgMain = self.fotagoSkMain
                # if ftgMain:
                # TemplateDrawSksToolHh(drata, ftgMain, isFlipSide=True, tool_name="")

                TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name="Move to Socket")
                ftgNdTar = self.fotagoNdTar
                if ftgNdTar:
                    # TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Interfacer")
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ftgNdTar.tar, cur_x_off=0)
                    near_group_in = list_ftgSksIn[0]

                    y = ftgNdTar.pos.y
                    boxHeiBound = Vec((y-20, y+20 ))
                    DrawVlSocketArea(drata, near_group_in.tar, boxHeiBound, Color4(get_sk_color_safe(ftgMain.tar)))
                    # DrawVlSocketArea(drata, near_group_in.tar, near_group_in.boxHeiBound, Color4(get_sk_color_safe(near_group_in.tar)))
            case _:
                # 小王-模式名匹配
                match eMode(self.toolMode):
                    case eMode.COPY:   mode = "Copy Socket Name"
                    case eMode.PASTE:  mode = "Paste Socket Name"
                    case eMode.SWAP:   mode = "Swap Sockets"
                    case eMode.TYPE:   mode = "Change Socket Type"
                # todo 接口1移到接口2上  FLIP模式，在两个接口绘制名后加上 接口1 接口2
                TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name=mode)

    def NextAssignmentToolCopyPaste(self, _isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        if (self.toolMode == eMode.PASTE.value) and (not self.clipboard):  # 预料之中; 还有 #https://projects.blender.org/blender/blender/issues/113860
            return  #Todo0VV 遍历版本并指出哪些会崩溃.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type == 'REROUTE':
                continue
            if (not prefs.vitPasteToAnySocket) and (self.toolMode == eMode.PASTE.value) and (nd.type not in NodeItemsUtils.support_types):
                break  # 光标必须靠近骑士 (或组节点) (对于非 vitPasteToAnySocket). 还有 `continue` 不会有高级取消.
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            self.fotagoSkMain = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            if self.fotagoSkMain:
                unhide_node_reassign(nd, self, cond=self.fotagoSkMain.tar.node == nd, flag=True)
            break
    def NextAssignmentToolSwapFlip(self, isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if nd.type not in NodeItemsUtils.support_types:
                break # 光标必须靠近骑士 (或组节点); 但也可以通过选择同一个套接字来取消, 所以不确定.
            if (self.fotagoSkRosw)and(self.fotagoSkRosw.tar.node!=nd):
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            if isFirstActivation:
                self.fotagoSkRosw = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            unhide_node_reassign(nd, self, cond=self.fotagoSkRosw, flag=True)
            skRosw = opt_ftg_socket(self.fotagoSkRosw)
            if skRosw:
                for ftg in list_ftgSksOut if skRosw.is_output else list_ftgSksIn:
                    if (ftg.blid!='NodeSocketVirtual')and(NodeItemsUtils.IsSimRepCorrectSk(nd, ftg.tar)):
                        self.fotagoSkMain = ftg
                        break
                if (self.fotagoSkMain)and(self.fotagoSkMain.tar==skRosw):
                    self.fotagoSkMain = None
            break
    def NextAssignmentToolNewCreate(self, isFirstActivation, prefs, tree):
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=True, cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            match eMode(self.toolMode):
                case eMode.NEW:
                    self.fotagoSkMain = None
                    if isFirstActivation:
                        self.fotagoSkRosw = None
                        for ftg in list_ftgSksOut:
                            self.fotagoSkRosw = ftg
                            self.tglCrossVirt = ftg.blid == 'NodeSocketVirtual'
                            break
                        unhide_node_reassign(nd, self, cond=self.fotagoSkRosw, flag=True)
                    skRosw = opt_ftg_socket(self.fotagoSkRosw)
                    if skRosw:
                        for ftg in list_ftgSksIn:
                            if (ftg.blid == 'NodeSocketVirtual') ^ self.tglCrossVirt:
                                self.fotagoSkMain = ftg
                                break
                        if (self.fotagoSkMain) and (self.fotagoSkMain.tar.node == skRosw.node):  #todo0NA 概括这种检查到类中.
                            self.fotagoSkMain = None
                    unhide_node_reassign(nd, self, cond=self.fotagoSkMain, flag=True)
                case eMode.CREATE:
                    if isFirstActivation:
                        ftgSkOut, ftgSkIn = None, None
                        for ftg in list_ftgSksIn:
                            if (ftg.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkIn = ftg
                                break
                        for ftg in list_ftgSksOut:
                            if (ftg.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkOut = ftg
                                break
                        self.fotagoSkMain = MinFromFtgs(ftgSkOut, ftgSkIn)
                    self.fotagoNdTar = None
                    skMain = opt_ftg_socket(self.fotagoSkMain)
                    if not skMain: continue
                    if nd == skMain.node:
                        break
                    if nd.type not in NodeItemsUtils.support_types:
                        continue
                    if skMain.is_output and nd.type == 'GROUP_INPUT': continue
                    if not skMain.is_output and nd.type in NodeItemsUtils.only_inputs: continue
                    self.fotagoNdTar = ftgNd
            break

    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                self.NextAssignmentToolCopyPaste(isFirstActivation, prefs, tree)
            case eMode.SWAP | eMode.FLIP:
                self.NextAssignmentToolSwapFlip(isFirstActivation, prefs, tree)
            case eMode.NEW | eMode.CREATE:
                self.NextAssignmentToolNewCreate(isFirstActivation, prefs, tree)

    def MatterPurposePoll(self):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                return not not self.fotagoSkMain
            case eMode.SWAP | eMode.FLIP:
                return self.fotagoSkRosw and self.fotagoSkMain
            case eMode.NEW:
                for dk, dv in self.dict_ndHidingVirtualIn.items():
                    dk.inputs[-1].hide = dv
                for dk, dv in self.dict_ndHidingVirtualOut.items():
                    dk.outputs[-1].hide = dv
                return self.fotagoSkRosw and self.fotagoSkMain
            case eMode.CREATE:
                return self.fotagoSkMain and self.fotagoNdTar

    def MatterPurposeTool(self, event, prefs, tree: NodeTree):
        links = tree.links
        match eMode(self.toolMode):
            case eMode.COPY:
                self.clipboard = sk_label_or_name(self.fotagoSkMain.tar)
            case eMode.PASTE:
                #tovo1v6 添加一个按键, 按下后会“取消”--不进行粘贴; 因为此模式保证会粘附 (参见选项) 到任何套接字, 需要某种方式来“退后一步”.
                skMain = self.fotagoSkMain.tar
                if (skMain.node.type not in NodeItemsUtils.support_types) and (prefs.vitPasteToAnySocket):
                    skMain.name = self.clipboard
                else:
                    NodeItemsUtils(skMain).get_item(skMain).name = self.clipboard
            case eMode.SWAP | eMode.FLIP:
                skMain = self.fotagoSkMain.tar
                items_tool = NodeItemsUtils(skMain)
                skfFrom = items_tool.get_item(self.fotagoSkRosw.tar)
                skfTo = items_tool.get_item(skMain)
                items_tool.MoveBySkfs(skfFrom, skfTo, isSwap=self.toolMode == eMode.SWAP.value)
            case eMode.NEW:
                DoLinkHh(self.fotagoSkRosw.tar, self.fotagoSkMain.tar)
            case eMode.CREATE:
                ftgNdTar = self.fotagoNdTar
                tar_nd = ftgNdTar.tar
                items_tool = NodeItemsUtils(tar_nd)
                skMain = self.fotagoSkMain.tar
                skfNew = items_tool.NewSkfFromSk(skMain, isFlipSide=tar_nd.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'})
                if not skfNew: return
                can = True
                # if not items_tool.has_extend_socket:
                is_group = tar_nd.type in ['GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT']
                if is_group:
                    for skf in items_tool.skfa:
                        if skf.item_type == 'PANEL':  # 该死的头疼. 你们自己搞定吧, 我已经懒得搞了.
                            can = False  #|4|.
                            break
                if can:  #tovo0v6 还有面板.
                    item_name = skfNew.name
                    ftgNearest = None  # MinFromFtgs(list_ftgSksIn[0] if list_ftgSksIn else None, list_ftgSksOut[0] if list_ftgSksOut else None)
                    min = 16777216.0
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(tar_nd)
                    for ftg in list_ftgSksIn if skMain.is_output else list_ftgSksOut:
                        if (ftg.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(tar_nd, ftg.tar)):
                            length = (ftgNdTar.pos - ftg.pos).length
                            if min > length:
                                min = length
                                ftgNearest = ftg
                    if ftgNearest and (not items_tool.is_index_switch):
                        skfTo = items_tool.get_item(ftgNearest.tar)
                        items_tool.MoveBySkfs(skfNew, skfTo, isSwap=False)
                        if (ftgNdTar.pos.y < ftgNearest.pos.y):  # 'True' -- 在组中往下, 而不是世界朝向.
                            if items_tool.has_extend_socket:
                                items_tool.MoveBySkfs(items_tool.get_item(ftgNearest.tar), skfTo, isSwap=None)  # 小心 skfTo.
                            else:
                                items_tool.MoveBySkfs(skfNew, skfTo, isSwap=None)  # 天才!
                    if ftgNearest and items_tool.is_index_switch:
                        tar_input = ftgNearest.tar  # 要插入的位置的接口
                        inputs = tar_input.node.inputs
                        if tar_input.name == "Index":
                            tar_index = 1
                        else:
                            is_ = ftgNdTar.pos.y < ftgNearest.pos.y  # 例: 插入1/2之间,离2近时正确,离1近时插到1上了(这时判断为True,插入1/2之间)
                            tar_index = int(tar_input.name) + 1 + is_  # 接口名 + 1才是在输入接口列表里的序号,因为编号切换第一个接口是编号
                        max_index = int(skfNew.name) + 1  # 最后一个即新建接口的序号
                        for i in range(max_index, tar_index - 1, -1):
                            link = inputs[i - 1].links
                            if link:
                                links.new(link[0].from_socket, inputs[i])  # 建立新连线
                                links.remove(link[0])  # 删除旧连线
                        links.new(skMain, inputs[i])

                if items_tool.has_extend_socket:
                    links.new(skMain, items_tool.get_socket(items_tool.skfa.get(item_name), is_out=not skMain.is_output))
                if is_group:
                    links.new(skMain, items_tool.get_socket(skfNew, is_out=(skfNew.in_out == 'OUTPUT') ^ (items_tool.type != 'GROUP')))

    def InitTool(self, event, prefs, tree):
        self.fotagoSkMain = None
        self.fotagoSkRosw = None  #RootSwap
        match eMode(self.toolMode):
            case eMode.NEW:
                self.dict_ndHidingVirtualIn = {}
                self.dict_ndHidingVirtualOut = {}
                for nd in tree.nodes:
                    if nd.bl_idname in set_utilEquestrianPortalBlids:
                        if nd.inputs:
                            self.dict_ndHidingVirtualIn[nd] = nd.inputs[-1].hide
                            nd.inputs[-1].hide = False
                        if nd.outputs:
                            self.dict_ndHidingVirtualOut[nd] = nd.outputs[-1].hide
                            nd.outputs[-1].hide = False
                self.tglCrossVirt = None
                # 某个 bug, 如果不重绘, 第一个找到的虚拟的就无法正确选择.
                bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
            case eMode.CREATE:
                self.fotagoNdTar = None  # 天啊.
            case eMode.FLIP:
                self.fotagoNdTar = None
        NODE_OT_voronoi_interfacer.clipboard = property(lambda _: bpy.context.window_manager.clipboard,
                                                   lambda _, v: setattr(bpy.context.window_manager, 'clipboard', v))

    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        draw_hand_split_prop(col, prefs, 'vitPasteToAnySocket')
