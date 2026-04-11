from enum import Enum

import bpy
from ..base_tool import unhide_node_reassign, PairSocketTool
from ..utils.drawing import draw_sockets_template
from ..utils.node import MinFromTars, opt_tar_socket

class SwapperMode(Enum):
    SWAP = 'SWAP'
    ADD  = 'ADD'
    TRAN = 'TRAN'

eMode = SwapperMode

ModeItems = (
    (eMode.SWAP.value, "Swap",     "All links from the first socket will be on the second, from the second on the first"),
    (eMode.ADD.value,  "Add",      "Add all links from the second socket to the first one"),
    (eMode.TRAN.value, "Transfer", "Move all links from the second socket to the first one with replacement"),
)

class NODE_OT_voronoi_swapper(PairSocketTool):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    bl_description = "Tool for swapping links between two sockets, or adding them to one of them.\nNo link swap will occur if it ends up originating from its own node."
    use_for_custom_tree = True
    can_draw_in_pref_setting = False
    toolMode:     bpy.props.EnumProperty(name="Mode", default=eMode.SWAP.value, items=ModeItems)
    isCanAnyType: bpy.props.BoolProperty(name="Can swap with any socket type", default=False)
    def callback_draw_tool(self, drawer):      # 我模仿着加的
        # 小王-模式名匹配
        match eMode(self.toolMode):
            case eMode.SWAP: mode = "交换连线"
            case eMode.ADD:  mode = "移动并加入连线"
            case eMode.TRAN: mode = "移动并替换连线"
        draw_sockets_template(drawer, self.target_sk0, self.target_sk1, tool_name=mode,)
    def find_targets_tool(self, is_first_active, prefs, tree):
        if is_first_active:
            self.target_sk0 = None
        self.target_sk1 = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            unhide_node_reassign(nd, self, cond=is_first_active, flag=True)
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            #基于Mixer的标准.
            if is_first_active:
                tar_sk_out, tar_sk_in = None, None
                for tar in tar_sks_out: #todo0NA 但这不就是Findanysk吗!?
                    if tar.blid!='NodeSocketVirtual':
                        tar_sk_out = tar
                        break
                for tar in tar_sks_in:
                    if tar.blid!='NodeSocketVirtual':
                        tar_sk_in = tar
                        break
                #也允许对输入接口使用“添加”功能，但仅限于多输入接口，因为这很明显
                if (self.toolMode==eMode.ADD.value)and(tar_sk_in):
                    #按类型检查，而不是按'is_multi_input'，这样就可以从常规输入添加到多输入.
                    if (tar_sk_in.blid not in ('NodeSocketGeometry','NodeSocketString')):#or(not tar_sk_in.tar.is_multi_input): #没有第二个条件可能性更多.
                        tar_sk_in = None
                self.target_sk0 = MinFromTars(tar_sk_out, tar_sk_in)
            #这里积累了很多奇怪的关于None等的检查 -- 这是我将自己发明的许多高级函数连接在一起的结果.
            skOut0 = opt_tar_socket(self.target_sk0)
            if skOut0:
                for tar in tar_sks_out if skOut0.is_output else tar_sks_in:
                    if tar.blid=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.bl_idname==tar.blid)or(self.check_between_sk_fields(skOut0, tar.tar)):
                        self.target_sk1 = tar
                    if self.target_sk1: #如果成功则停止搜索.
                        break
                if (self.target_sk1)and(skOut0==self.target_sk1.tar): #检查是否为自我复制.
                    self.target_sk1 = None
                    break #当is_first_active==False且接口为自我复制时，为isCanAnyType中断循环；以免一次找到两个节点.
                if not self.isCanAnyType:
                    if not(self.target_sk1 or is_first_active): #如果没有结果，则继续搜索.
                        continue
                unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
            break
    def can_run(self):
        return self.target_sk0 and self.target_sk1
    def run(self, event, prefs, tree):
        skIo0 = self.target_sk0.tar
        skIo1 = self.target_sk1.tar
        match eMode(self.toolMode):
            case eMode.SWAP:
                #交换第一个和第二个接口的所有连接:
                list_memSks = []
                if skIo0.is_output: #检查 is_output 的一致性是 find_targets_tool() 的任务.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  以防止节点创建指向自身的连接。需要检查所有情况并且不处理此类连接.
                            list_memSks.append(lk.to_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.to_node!=skIo0.node: # T 0  ^
                            tree.links.new(skIo0, lk.to_socket)
                            if lk.to_socket.is_multi_input: #对于多输入接口则删除.
                                tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(skIo1, li)
                else:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            list_memSks.append(lk.from_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.from_node!=skIo0.node: # F 0  ^
                            tree.links.new(lk.from_socket, skIo0)
                            tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(li, skIo1)
            case eMode.ADD|eMode.TRAN:
                #只需将第一个接口的连接添加到第二个接口。即合并、添加.
                if self.toolMode==eMode.TRAN.value:
                    #与添加相同，只是第一个接口会丢失连接.
                    for lk in skIo1.vl_sold_links_final:
                        tree.links.remove(lk)
                if skIo0.is_output:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  ^
                            tree.links.new(skIo1, lk.to_socket)
                            if lk.to_socket.is_multi_input: #没有这个，lk仍然会指向“已添加”的连接，从而被删除。因此需要对多输入进行显式检查.
                                tree.links.remove(lk)
                else: #为了多输入接口而添加.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            tree.links.new(lk.from_socket, skIo1)
                            tree.links.remove(lk)
        #VST VLRT是不需要的，对吧？
