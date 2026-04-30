from enum import Enum

import bpy
from ..base_tool import unhide_node_reassign, AnyTargetTool
from ..globals import Cursor_X_Offset, sk_type_support_field
from ..utils.node import compare_sk_label, link_new_pro, VlrtData, VlrtRememberLastSockets
from ..utils.solder import solder_sk_links

class LinkRepeatingMode(Enum):
    SOCKET = 'SOCKET'
    NODE   = 'NODE'

eMode = LinkRepeatingMode

ModeItems = (
    (eMode.SOCKET.value, "For socket", "Using the last link created by some from the tools, create the same for the specified socket"),
    (eMode.NODE.value,   "For node",   "Using name of the last socket, find and connect for a selected node"),
)

class NODE_OT_voronoi_link_repeating(AnyTargetTool):  # 分离成单独的工具, 以免用意大利面条代码玷污神圣的地方 (最初只用于 VLT).
    bl_idname = 'node.voronoi_link_repeating'
    bl_label = "Voronoi Link Repeating"
    bl_description = "A full-fledged branch from VLT, repeats any previous link from most\nother tools. Provides convenience for \"one to many\" connections."
    use_for_custom_tree = True
    can_draw_settings = False
    toolMode: bpy.props.EnumProperty(name="Mode", default=eMode.SOCKET.value, items=ModeItems)
    def callback_draw(self, drawer):
        self.template_draw_any(drawer, self.target_any, cond=self.toolMode==eMode.NODE.value)
    def find_targets(self, _is_first_active, prefs, tree):
        def IsSkBetweenFields(sk1, sk2):
            return (sk1.type in sk_type_support_field)and( (sk2.type in sk_type_support_field)or(sk1.type==sk2.type) )
        skLastOut = self.skLastOut
        skLastIn = self.skLastIn
        if not skLastOut:
            return
        solder_sk_links(tree) # 好像不重新焊接也能工作.
        self.target_any = None
        cur_x_off_repeat = -Cursor_X_Offset if self.toolMode==eMode.SOCKET.value else 0     # 小王 这个有点特殊
        for tar_nd in self.get_nearest_nodes(cur_x_off=cur_x_off_repeat):
            nd = tar_nd.tar
            if nd==skLastOut.node: # 排除自身节点.
                break #continue
            if self.toolMode==eMode.SOCKET.value:
                tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=-Cursor_X_Offset)
                if skLastOut:
                    for tar in tar_sks_in:
                        if (skLastOut.bl_idname==tar.idname)or(IsSkBetweenFields(skLastOut, tar.tar)):
                            can = True
                            for lk in tar.tar.vl_sold_links_final:
                                if lk.from_socket==skLastOut: # 识别已有的链接, 并且不选择这样的套接字.
                                    can = False
                            if can:
                                self.target_any = tar
                                break
                unhide_node_reassign(nd, self, cond=self.target_any, flag=False)
            else:
                if skLastIn:
                    if nd.inputs:
                        self.target_any = tar_nd
                    for sk in nd.inputs:
                        if compare_sk_label(sk, skLastIn):
                            if (sk.enabled)and(not sk.hide):
                                tree.links.new(skLastOut, sk) # 注意: 不是高级的; 为什么节点重复需要接口?.
            break
    def run(self, event, prefs, tree):
        if self.toolMode==eMode.SOCKET.value:
            # 这里不需要检查套接字树是否相同, find_targets() 中已经检查过了.
            # 同样不需要检查 skLastOut 是否存在, 参见其在 find_targets() 中的拓扑.
            # 注意: VlrtRememberLastSockets() 中有 `.id_data` 的相同性检查.
            # 注意: 不需要检查树是否存在, 因为如果连接的套接字在这里存在, 那它就肯定在某个地方.
            link_new_pro(self.skLastOut, self.target_any.tar)
            VlrtRememberLastSockets(self.skLastOut, self.target_any.tar) # 因为. 而且.. “自递归”?.
    def initialize(self, event, prefs, tree):
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
