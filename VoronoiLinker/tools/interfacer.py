from enum import Enum

import bpy
from mathutils import Vector as Vec
from bpy.types import Node, NodeTree, NodeSocket, NodeSocketVirtual
from ..base_tool import unhide_node_reassign, draw_node_template, draw_sockets_template, PairSocketTool
from ..common_class import Target
from ..node_items import NodeItemsUtils
from ..utils.color import get_sk_color_safe
from ..utils.drawing import Drawer, draw_socket_area
from ..utils.node import socket_label, DoLinkHh, FindAnySk, pick_near_target, opt_tar_socket
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
    use_for_custom_tree = False
    can_draw_settings = False
    toolMode: bpy.props.EnumProperty(name="Mode", default=eMode.NEW.value, items=ModeItems)

    def callback_draw_tool(self, drawer):

        def draw_insert_preview(drawer: Drawer,
                                tarNdTar: Target | None,
                                source_sk: NodeSocket | None,
                                target_is_output: bool,
                                skip_sk: NodeSocket | None = None):
            if (not tarNdTar) or (not source_sk):
                return
            tarNearest = self.find_nearest_insert_tar(tarNdTar.tar, tarNdTar.pos, target_is_output, skip_sk=skip_sk)
            if not tarNearest:
                return
            y = tarNdTar.pos.y
            height_box = Vec((y - 7, y + 7))
            draw_socket_area(drawer, tarNearest.tar, height_box, Vec(get_sk_color_safe(source_sk)))

        mode_map = {
            eMode.NEW:    "Connect Extend Socket",
            eMode.CREATE: "Insert to Add Socket",
            eMode.COPY:   "Copy Socket Name",
            eMode.PASTE:  "Paste Socket Name",
            eMode.FLIP:   "Move Socket",
            eMode.SWAP:   "Swap Sockets",
            eMode.TYPE:   "Change Socket Type",
        }
        mode = mode_map[eMode(self.toolMode)]
        match eMode(self.toolMode):
            case eMode.NEW:
                draw_sockets_template(drawer, self.target_skRosw, self.target_skMain, is_classic_flow=True, tool_name=mode)
            case eMode.CREATE:
                tarMain = self.target_skMain
                if tarMain:
                    draw_sockets_template(drawer, tarMain, side_mark_offset=-2, tool_name=mode)
                    draw_insert_preview(drawer, self.target_ndTar, tarMain.tar, not tarMain.tar.is_output)
            case eMode.FLIP:
                draw_sockets_template(drawer, self.target_skRosw, tool_name=mode)
                skRosw = opt_tar_socket(self.target_skRosw)
                if skRosw:
                    draw_insert_preview(drawer, self.target_ndTar, skRosw, skRosw.is_output, skip_sk=skRosw)
            case _:
                draw_sockets_template(drawer, self.target_skMain, self.target_skRosw, tool_name=mode)

    def find_targets_copy_paste(self, prefs):
        self.target_skMain = None
        if (self.toolMode == eMode.PASTE.value) and (not self.clipboard):
            # 预料之中; 还有 #https://projects.blender.org/blender/blender/issues/113860
            return  #Todo0VV 遍历版本并指出哪些会崩溃.
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if (not prefs.vitPasteToAnySocket) and (self.toolMode == eMode.PASTE.value) and (nd.type not in NodeItemsUtils.support_types):
                break  # 光标必须靠近骑士 (或组节点) (对于非 vitPasteToAnySocket). 还有 `continue` 不会有高级取消.
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            self.target_skMain = FindAnySk(nd, tar_sks_in, tar_sks_out)
            if self.target_skMain:
                unhide_node_reassign(nd, self, cond=self.target_skMain.tar.node == nd, flag=True)
            break

    @staticmethod
    def is_insert_target_valid(nd: Node, tar: Target, skip_sk: NodeSocket | None = None) -> bool:
        return (tar.idname != 'NodeSocketVirtual') and (tar.tar != skip_sk) and NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)

    def find_nearest_insert_tar(self, nd: Node, pos: Vec, is_output: bool, skip_sk: NodeSocket | None = None) -> Target | None:
        tarNearest = None
        min_len = float("inf")
        tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd)
        for tar in tar_sks_out if is_output else tar_sks_in:
            if self.is_insert_target_valid(nd, tar, skip_sk=skip_sk):
                length = (pos - tar.pos).length
                if min_len > length:
                    min_len = length
                    tarNearest = tar
        return tarNearest

    def move_item_to_insert(self, items_tool: NodeItemsUtils, skfFrom, skfTo, tarNearest: Target, tarNdTar: Target) -> None:
        items_tool.MoveBySkfs(skfFrom, skfTo, isSwap=False)
        if (tarNdTar.pos.y < tarNearest.pos.y):  # 'True' -- 在组中往下, 而不是世界朝向.
            if items_tool.has_extend_socket:
                items_tool.MoveBySkfs(items_tool.get_item(tarNearest.tar), skfTo, isSwap=True)  # 小心 skfTo.
            else:
                items_tool.MoveBySkfs(skfFrom, skfTo, isSwap=True)

    def move_existing_item_to_insert(self, items_tool: NodeItemsUtils, skfFrom, skfTo, tarNearest: Target, tarNdTar: Target) -> None:
        if not items_tool.has_extend_socket:
            self.move_item_to_insert(items_tool, skfFrom, skfTo, tarNearest, tarNdTar)
            return

        inxFrom = -1
        inxTo = -1
        for cyc, skf in enumerate(items_tool.skfa):
            if skf == skfFrom:
                inxFrom = cyc
            if skf == skfTo:
                inxTo = cyc
        if (inxFrom == -1) or (inxTo == -1):
            raise Exception(f"Index not found from `{skfFrom}` or `{skfTo}`")

        is_insert_after = tarNdTar.pos.y < tarNearest.pos.y
        target_index = inxTo - (inxFrom < inxTo)
        final_index = target_index + is_insert_after
        if final_index != inxFrom:
            items_tool.skfa.move(inxFrom, final_index)

    def find_targets_swap_flip(self, is_first_active):
        self.target_skMain = None
        if self.toolMode == eMode.FLIP.value:
            self.target_ndTar = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            if nd.type not in NodeItemsUtils.support_types:
                break  # 光标必须靠近骑士 (或组节点); 但也可以通过选择同一个套接字来取消, 所以不确定.
            if (self.target_skRosw) and (self.target_skRosw.tar.node != nd):
                continue
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            if is_first_active:
                self.target_skRosw = FindAnySk(nd, tar_sks_in, tar_sks_out)
            unhide_node_reassign(nd, self, cond=self.target_skRosw, flag=True)
            skRosw = opt_tar_socket(self.target_skRosw)
            if skRosw:
                for tar in tar_sks_out if skRosw.is_output else tar_sks_in:
                    if self.is_insert_target_valid(nd, tar, skip_sk=skRosw if self.toolMode == eMode.FLIP.value else None):
                        self.target_skMain = tar
                        break
                if self.toolMode == eMode.FLIP.value:
                    self.target_ndTar = tar_nd if self.target_skMain else None
                elif (self.target_skMain) and (self.target_skMain.tar == skRosw):
                    self.target_skMain = None
            break

    def find_targets_new_create(self, is_first_active):
        for tar_nd in self.get_nearest_nodes(includePoorNodes=True, cur_x_off=0):
            nd = tar_nd.tar
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            match eMode(self.toolMode):
                case eMode.NEW:
                    self.target_skMain = None
                    if is_first_active:
                        self.target_skRosw = None
                        for tar in tar_sks_out:
                            self.target_skRosw = tar
                            self.tglCrossVirt = tar.idname == 'NodeSocketVirtual'
                            break
                        unhide_node_reassign(nd, self, cond=self.target_skRosw, flag=True)
                    skRosw = opt_tar_socket(self.target_skRosw)
                    if skRosw:
                        for tar in tar_sks_in:
                            if (tar.idname == 'NodeSocketVirtual') ^ self.tglCrossVirt:
                                self.target_skMain = tar
                                break
                        if (self.target_skMain) and (self.target_skMain.tar.node == skRosw.node):  #todo0NA 概括这种检查到类中.
                            self.target_skMain = None
                    unhide_node_reassign(nd, self, cond=self.target_skMain, flag=True)
                case eMode.CREATE:
                    if is_first_active:
                        tar_sk_out, tar_sk_in = None, None
                        for tar in tar_sks_in:
                            if (tar.idname != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
                                tar_sk_in = tar
                                break
                        for tar in tar_sks_out:
                            if (tar.idname != 'NodeSocketVirtual') and (NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
                                tar_sk_out = tar
                                break
                        self.target_skMain = pick_near_target(tar_sk_out, tar_sk_in)
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

    def find_targets_tool(self, is_first_active, prefs, tree):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                self.find_targets_copy_paste(prefs)
            case eMode.SWAP | eMode.FLIP:
                self.find_targets_swap_flip(is_first_active)
            case eMode.NEW | eMode.CREATE:
                self.find_targets_new_create(is_first_active)

    def can_run(self):
        match eMode(self.toolMode):
            case eMode.COPY | eMode.PASTE:
                return not not self.target_skMain
            case eMode.SWAP | eMode.FLIP:
                if self.toolMode == eMode.FLIP.value:
                    return self.target_skRosw and self.target_skMain and self.target_ndTar
                return self.target_skRosw and self.target_skMain
            case eMode.NEW:
                for sk, hide in self.hide_extend_sks.items():
                    sk.hide = hide
                return self.target_skRosw and self.target_skMain
            case eMode.CREATE:
                return self.target_skMain and self.target_ndTar

    def run(self, event, prefs, tree):
        links = tree.links
        match eMode(self.toolMode):
            case eMode.COPY:
                self.clipboard = socket_label(self.target_skMain.tar)
            case eMode.PASTE:
                #tovo1v6 添加一个按键, 按下后会“取消”--不进行粘贴; 因为此模式保证会粘附 (参见选项) 到任何套接字, 需要某种方式来“退后一步”.
                skMain = self.target_skMain.tar
                if (skMain.node.type not in NodeItemsUtils.support_types) and (prefs.vitPasteToAnySocket):
                    skMain.name = self.clipboard
                else:
                    NodeItemsUtils(skMain).get_item(skMain).name = self.clipboard
            case eMode.SWAP:
                skMain = self.target_skMain.tar
                items_tool = NodeItemsUtils(skMain)
                skfFrom = items_tool.get_item(self.target_skRosw.tar)
                skfTo = items_tool.get_item(skMain)
                items_tool.MoveBySkfs(skfFrom, skfTo, isSwap=True)
            case eMode.FLIP:
                tarNdTar = self.target_ndTar
                skRosw = self.target_skRosw.tar
                items_tool = NodeItemsUtils(skRosw)
                tarNearest = self.find_nearest_insert_tar(tarNdTar.tar, tarNdTar.pos, skRosw.is_output, skip_sk=skRosw)
                if not tarNearest: return
                skfFrom = items_tool.get_item(skRosw)
                skfTo = items_tool.get_item(tarNearest.tar)
                self.move_existing_item_to_insert(items_tool, skfFrom, skfTo, tarNearest, tarNdTar)
            case eMode.NEW:
                DoLinkHh(self.target_skRosw.tar, self.target_skMain.tar)
            case eMode.CREATE:
                tarNdTar = self.target_ndTar
                _tar_nd = tarNdTar.tar
                items_tool = NodeItemsUtils(_tar_nd)
                skMain = self.target_skMain.tar
                skfNew = items_tool.NewSkfFromSk(skMain, isFlipSide=_tar_nd.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'})
                if not skfNew: return
                is_group = _tar_nd.type in ['GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT']
                item_name = skfNew.name
                tarNearest = self.find_nearest_insert_tar(_tar_nd, tarNdTar.pos, not skMain.is_output)
                if tarNearest:
                    if not items_tool.is_index_switch:
                        skfTo = items_tool.get_item(tarNearest.tar)
                        self.move_item_to_insert(items_tool, skfNew, skfTo, tarNearest, tarNdTar)
                    elif items_tool.is_index_switch:
                        tar_input = tarNearest.tar  # 要插入的位置的接口
                        inputs = tar_input.node.inputs
                        if tar_input.name == "Index":
                            tar_index = 1
                        else:
                            is_ = tarNdTar.pos.y < tarNearest.pos.y  # 例: 插入1/2之间,离2近时正确,离1近时插到1上了(这时判断为True,插入1/2之间)
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
        def store_extend_hide_state(extend_sk: NodeSocket):
            if isinstance(extend_sk, NodeSocketVirtual):
                self.hide_extend_sks[extend_sk] = extend_sk.hide
                extend_sk.hide = False
        match eMode(self.toolMode):
            case eMode.NEW:
                self.hide_extend_sks: dict[NodeSocketVirtual, bool] = {}
                for nd in tree.nodes:
                    if nd.inputs:
                        store_extend_hide_state(nd.inputs[-1])
                    if nd.outputs:
                        store_extend_hide_state(nd.outputs[-1])
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
    def draw_pref_settings(col, prefs):
        draw_hand_split_prop(col, prefs, 'vitPasteToAnySocket')
