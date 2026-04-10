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
from ..utils.node import DoLinkHh, FindAnySk, MinFromFtgs, opt_tar_socket
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

    def callback_draw_tool(self, drata):
        match eMode(self.toolMode):
            case eMode.NEW:
                TemplateDrawSksToolHh(drata, self.target_skRosw, self.target_skMain, isClassicFlow=True, tool_name="Connect to Extend Socket")
            case eMode.CREATE:
                ftgMain = self.target_skMain
                if ftgMain:
                    TemplateDrawSksToolHh(drata, ftgMain, sideMarkHh=-2, tool_name="Insert to Socket")
                ftgNdTar = self.target_ndTar
                if ftgNdTar:
                    TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Node Group")
                    tar_sks_in, tar_sks_out = self.get_nearest_sockets(ftgNdTar.tar, cur_x_off=0)
                    if not tar_sks_in: return
                    near_group_in = tar_sks_in[0]  # 节点组可能没有输入接口:

                    y = ftgNdTar.pos.y
                    boxHeiBound = Vec((y - 7, y + 7))
                    DrawVlSocketArea(drata, near_group_in.tar, boxHeiBound, Color4(get_sk_color_safe(ftgMain.tar)))
            case eMode.FLIP:  # 失败
                # ftgMain = self.target_skMain
                # if ftgMain:
                # TemplateDrawSksToolHh(drata, ftgMain, isFlipSide=True, tool_name="")

                TemplateDrawSksToolHh(drata, self.target_skMain, self.target_skRosw, tool_name="Move to Socket")
                ftgNdTar = self.target_ndTar
                if ftgNdTar:
                    # TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Interfacer")
                    tar_sks_in, tar_sks_out = self.get_nearest_sockets(ftgNdTar.tar, cur_x_off=0)
                    near_group_in = tar_sks_in[0]

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
                TemplateDrawSksToolHh(drata, self.target_skMain, self.target_skRosw, tool_name=mode)

    def find_targets_toolCopyPaste(self, _isFirstActivation, prefs, tree):
        self.target_skMain = None
        if (self.toolMode == eMode.PASTE.value) and (not self.clipboard):  # 预料之中; 还有 #https://projects.blender.org/blender/blender/issues/113860
            return  #Todo0VV 遍历版本并指出哪些会崩溃.
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if nd.type == 'REROUTE':
                continue
            if (not prefs.vitPasteToAnySocket) and (self.toolMode == eMode.PASTE.value) and (nd.type not in NodeItemsUtils.support_types):
                break  # 光标必须靠近骑士 (或组节点) (对于非 vitPasteToAnySocket). 还有 `continue` 不会有高级取消.
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            self.target_skMain = FindAnySk(nd, tar_sks_in, tar_sks_out)
            if self.target_skMain:
                unhide_node_reassign(nd, self, cond=self.target_skMain.tar.node == nd, flag=True)
            break
    def find_targets_toolSwapFlip(self, isFirstActivation, prefs, tree):
        self.target_skMain = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE':
                continue
            if nd.type not in NodeItemsUtils.support_types:
                break # 光标必须靠近骑士 (或组节点); 但也可以通过选择同一个套接字来取消, 所以不确定.
            if (self.target_skRosw)and(self.target_skRosw.tar.node!=nd):
                continue
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            if isFirstActivation:
                self.target_skRosw = FindAnySk(nd, tar_sks_in, tar_sks_out)
            unhide_node_reassign(nd, self, cond=self.target_skRosw, flag=True)
            skRosw = opt_tar_socket(self.target_skRosw)
            if skRosw:
                for tar in tar_sks_out if skRosw.is_output else tar_sks_in:
                    if (tar.blid!='NodeSocketVirtual')and(NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
                        self.target_skMain = tar
                        break
                if (self.target_skMain)and(self.target_skMain.tar==skRosw):
                    self.target_skMain = None
            break
    def find_targets_toolNewCreate(self, isFirstActivation, prefs, tree):
        for tar_nd in self.get_nearest_nodes(includePoorNodes=True, cur_x_off=0):
            nd = tar_nd.tar
            if nd.type=='REROUTE':
                continue
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            match eMode(self.toolMode):
                case eMode.NEW:
                    self.target_skMain = None
                    if isFirstActivation:
                        self.target_skRosw = None
                        for tar in tar_sks_out:
                            self.target_skRosw = tar
                            self.tglCrossVirt = tar.blid == 'NodeSocketVirtual'
                            break
                        unhide_node_reassign(nd, self, cond=self.target_skRosw, flag=True)
                    skRosw = opt_tar_socket(self.target_skRosw)
                    if skRosw:
                        for tar in tar_sks_in:
                            if (tar.blid == 'NodeSocketVirtual') ^ self.tglCrossVirt:
                                self.target_skMain = tar
                                break
                        if (self.target_skMain) and (self.target_skMain.tar.node == skRosw.node):  #todo0NA 概括这种检查到类中.
                            self.target_skMain = None
                    unhide_node_reassign(nd, self, cond=self.target_skMain, flag=True)
                case eMode.CREATE:
                    if isFirstActivation:
                        tar_sk_out, tar_sk_in = None, None
                        for tar in tar_sks_in:
                            if (tar.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
                                tar_sk_in = tar
                                break
                        for tar in tar_sks_out:
                            if (tar.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
                                tar_sk_out = tar
                                break
                        self.target_skMain = MinFromFtgs(tar_sk_out, tar_sk_in)
                    self.target_ndTar = None
                    skMain = opt_tar_socket(self.target_skMain)
                    if not skMain: continue
                    if nd == skMain.node:
                        break
                    if nd.type not in NodeItemsUtils.support_types:
                        continue
                    if skMain.is_output and nd.type == 'GROUP_INPUT': continue
                    if not skMain.is_output and nd.type in NodeItemsUtils.only_inputs: continue
                    self.target_ndTar = tar_nd
            break

    def find_targets_tool(self, isFirstActivation, prefs, tree):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                self.find_targets_toolCopyPaste(isFirstActivation, prefs, tree)
            case eMode.SWAP | eMode.FLIP:
                self.find_targets_toolSwapFlip(isFirstActivation, prefs, tree)
            case eMode.NEW | eMode.CREATE:
                self.find_targets_toolNewCreate(isFirstActivation, prefs, tree)

    def can_run(self):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                return not not self.target_skMain
            case eMode.SWAP | eMode.FLIP:
                return self.target_skRosw and self.target_skMain
            case eMode.NEW:
                for dk, dv in self.dict_ndHidingVirtualIn.items():
                    dk.inputs[-1].hide = dv
                for dk, dv in self.dict_ndHidingVirtualOut.items():
                    dk.outputs[-1].hide = dv
                return self.target_skRosw and self.target_skMain
            case eMode.CREATE:
                return self.target_skMain and self.target_ndTar

    def run(self, event, prefs, tree: NodeTree):
        links = tree.links
        match eMode(self.toolMode):
            case eMode.COPY:
                self.clipboard = sk_label_or_name(self.target_skMain.tar)
            case eMode.PASTE:
                #tovo1v6 添加一个按键, 按下后会“取消”--不进行粘贴; 因为此模式保证会粘附 (参见选项) 到任何套接字, 需要某种方式来“退后一步”.
                skMain = self.target_skMain.tar
                if (skMain.node.type not in NodeItemsUtils.support_types) and (prefs.vitPasteToAnySocket):
                    skMain.name = self.clipboard
                else:
                    NodeItemsUtils(skMain).get_item(skMain).name = self.clipboard
            case eMode.SWAP | eMode.FLIP:
                skMain = self.target_skMain.tar
                items_tool = NodeItemsUtils(skMain)
                skfFrom = items_tool.get_item(self.target_skRosw.tar)
                skfTo = items_tool.get_item(skMain)
                items_tool.MoveBySkfs(skfFrom, skfTo, isSwap=self.toolMode == eMode.SWAP.value)
            case eMode.NEW:
                DoLinkHh(self.target_skRosw.tar, self.target_skMain.tar)
            case eMode.CREATE:
                ftgNdTar = self.target_ndTar
                _tar_nd = ftgNdTar.tar
                items_tool = NodeItemsUtils(_tar_nd)
                skMain = self.target_skMain.tar
                skfNew = items_tool.NewSkfFromSk(skMain, isFlipSide=_tar_nd.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'})
                if not skfNew: return
                can = True
                # if not items_tool.has_extend_socket:
                is_group = _tar_nd.type in ['GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT']
                if is_group:
                    for skf in items_tool.skfa:
                        if skf.item_type == 'PANEL':  # 该死的头疼. 你们自己搞定吧, 我已经懒得搞了.
                            can = False  #|4|.
                            break
                if can:  #tovo0v6 还有面板.
                    item_name = skfNew.name
                    ftgNearest = None  # MinFromFtgs(tar_sks_in[0] if tar_sks_in else None, tar_sks_out[0] if tar_sks_out else None)
                    min = 16777216.0
                    tar_sks_in, tar_sks_out = self.get_nearest_sockets(_tar_nd)
                    for tar in tar_sks_in if skMain.is_output else tar_sks_out:
                        if (tar.blid != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(_tar_nd, tar.tar)):
                            length = (ftgNdTar.pos - tar.pos).length
                            if min > length:
                                min = length
                                ftgNearest = tar
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

    def initialize(self, event, prefs, tree):
        self.target_skMain = None
        self.target_skRosw = None  #RootSwap
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
                self.target_ndTar = None  # 天啊.
            case eMode.FLIP:
                self.target_ndTar = None
        NODE_OT_voronoi_interfacer.clipboard = property(lambda _: bpy.context.window_manager.clipboard,
                                                   lambda _, v: setattr(bpy.context.window_manager, 'clipboard', v))

    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        draw_hand_split_prop(col, prefs, 'vitPasteToAnySocket')
