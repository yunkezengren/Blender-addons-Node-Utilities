from enum import Enum

import bpy
from ..base_tool import unhide_node_reassign, AnyTargetTool
from ..common_class import Target
from ..utils.node import pick_near_target, socket_label
from ..utils.ui import split_prop

def HideFromNode(prefs, ndTarget, lastResult, isCanDo=False): # 最初是我个人的实用工具, 在 VL 之前就创建了.
    set_equestrianHideVirtual = {'GROUP_INPUT','SIMULATION_INPUT','SIMULATION_OUTPUT','REPEAT_INPUT','REPEAT_OUTPUT'}
    scoGeoSks = 0 # 用于 CheckSkZeroDefaultValue().
    def CheckSkZeroDefaultValue(sk): # Shader 和 Virtual 总是 True, Geometry 取决于插件设置.
        match sk.type: # 按复杂性降序排序.
            case 'GEOMETRY':
                match prefs.vht_never_hide_geometry: # 也曾考虑用于 out, 但有点懒, 还有 `GeometryNodeBoundBox`, 所以...
                    case 'FALSE': return True
                    case 'TRUE': return False
                    case 'ONLY_FIRST':
                        nonlocal scoGeoSks
                        scoGeoSks += 1
                        return scoGeoSks!=1
            case 'VALUE':
                # Todo1v6: 当需要时, 或者无事可做时 -- 添加一个可配置的点状隐藏列表, 通过 Python 进行评估.
                # ^ 字典[插槽blid]:{名称集合}. 还要想办法传递 default_value.
                if (socket_label(sk) in {'Alpha', 'Factor'})and(sk.default_value==1): # 对于某些 float 插槽, 进行点状检查也不错.
                    return True
                return sk.default_value==0
            case 'VECTOR':
                if (socket_label(sk)=='Scale')and(sk.default_value[0]==1)and(sk.default_value[1]==1)and(sk.default_value[2]==1):
                    return True # 'GeometryNodeTransform' 经常让我烦恼, 有一天终于受不了了..
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) # 注意: `sk.default_value==(0,0,0)` 是行不通的.
            case 'BOOLEAN':
                if not sk.hide_value: # 懒得焊接, 直接处理.
                    match prefs.vht_hide_bool_socket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match prefs.vht_hide_hidden_bool_socket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
            case 'RGBA':
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) # 第4个分量被忽略, 可以是任何值.
            case 'INT':
                return sk.default_value==0
            case 'STRING'|'OBJECT'|'MATERIAL'|'COLLECTION'|'TEXTURE'|'IMAGE': # 注意: STRING 与其他不同, 但处理方式相同.
                return not sk.default_value
            # 小王-自动隐藏接口优化-旋转接口
            case 'ROTATION':
                euler = sk.default_value
                return euler[0] == 0 and euler[1] == 0 and euler[2] == 0
            # 小王-自动隐藏接口优化-inline
            case _:
                return True
    if lastResult: # 上次分析的结果, 是否有插槽的状态会改变. 'isCanDo' 需要.
        def CheckAndDoForIo(puts, LMainCheck):
            success = False
            for sk in puts:
                if (sk.enabled)and(not sk.hide)and(not sk.vl_sold_is_final_linked_cou)and(LMainCheck(sk)): # 隐藏的核心在这里, 在前两个检查中.
                    success |= not sk.hide # 在这里 success 表示它是否会被隐藏.
                    if isCanDo:
                        sk.hide = True
            return success
        # 如果虚拟节点是手动创建的, 就不要隐藏它们. 因为就是这样. 但如果组的输入不止一个, 还是要隐藏.
        # LVirtual 的最初意思是 "LCheckOver" -- "上层"检查, 点状的附加条件. 但后来只积累了虚拟节点的条件, 所以改了名.
        isMoreNgInputs = False if ndTarget.type!='GROUP_INPUT' else len([True for nd in ndTarget.id_data.nodes if nd.type=='GROUP_INPUT'])>1
        LVirtual = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and # 这个 Labmda 的意思是, 对于那些虚拟的,
                                   (sk.node.type in {'GROUP_INPUT','GROUP_OUTPUT'})and # 在 io-骑士节点上的,
                                   (sk!=( sk.node.outputs if sk.is_output else sk.node.inputs )[-1])and # 并且不是最后一个的 (这才是重点),
                                   (not isMoreNgInputs) ) # 并且树中只有一个 GROUP_INPUT.
        # 核心在下面的三行代码中:
        success = CheckAndDoForIo(ndTarget.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LVirtual(sk)) ) # 对于输入, 是主流的值检查, 外加虚拟节点的检查.
        a = [True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)]
        if any(True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)): # 如果至少有一个输出插槽连接到外部
            success |= CheckAndDoForIo(ndTarget.outputs, lambda sk: LVirtual(sk) ) # 对于输出, 只有当它们的节点是骑士时, 虚拟节点的检查才有效.
        else:
            # 即使没有外部连接, 也要切换最后一个虚拟节点.
            if ndTarget.type in set_equestrianHideVirtual: # 注意: 'GROUP_OUTPUT' 没用, 它的一切都按值隐藏.
                if ndTarget.outputs: # 代替 for, 以便从最后一个读取.
                    sk = ndTarget.outputs[-1]
                    if sk.bl_idname=='NodeSocketVirtual':
                        success |= not sk.hide # 与 CheckAndDoForIo() 中一样.
                        if isCanDo:
                            sk.hide = True
        return success # 来自两个 CheckAndDoForIo() 内部的收获.
    elif isCanDo: # 否则展开全部.
        success = False
        for puts in [ndTarget.inputs, ndTarget.outputs]:
            for sk in puts:
                success |= sk.hide # 在这里 success 表示它是否会被展开.
                sk.hide = (sk.bl_idname=='NodeSocketVirtual')and(not prefs.vht_is_unhide_virtual)
        return success

# 只需要为了树中的整洁和美观.
# 对于那些 (比如我) 觉得"无所事事"的空输出套接字, 或者值为零 (0.0, 黑色等) 的未使用输入套接字感到困扰的人.
class HiderMode(Enum):
    HIDE_AUTO   = 'HideAuto'
    HIDE_SOCKET = 'HideSocket'
    HIDE_VALUE  = 'HideValue'

eMode = HiderMode

ModeItems = (
    (eMode.HIDE_AUTO.value,   "Auto",         "Automatically processing of hiding of sockets for a node"),
    (eMode.HIDE_SOCKET.value, "Socket",       "Hiding the socket"),
    (eMode.HIDE_VALUE.value,  "Socket value", "Switching the visibility of a socket contents"),
)

class NODE_OT_voronoi_hider(AnyTargetTool):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    bl_description = "Tool for bringing order and aesthetics to the node tree.\nMost likely 90% will go to using automatic socket hiding."
    use_for_custom_tree = True
    use_for_none_tree = True
    toolMode: bpy.props.EnumProperty(name="Mode", default=eMode.HIDE_SOCKET.value, items=ModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    def callback_draw(self, drawer):
        # 模式名匹配
        match eMode(self.toolMode):
            case eMode.HIDE_AUTO:   mode = "Auto Hide/Show Sockets"
            case eMode.HIDE_SOCKET: mode = "Hide Socket"
            case eMode.HIDE_VALUE:  mode = "Hide/Show Socket Value"
        self.template_draw_any(drawer, self.target_any, cond=self.toolMode==eMode.HIDE_AUTO.value, tool_name=mode)
    def find_targets(self, _is_first_active, prefs, tree):
        self.target_any = None

        match eMode(self.toolMode):
            case eMode.HIDE_SOCKET | eMode.HIDE_VALUE:
                    if self.toolMode == eMode.HIDE_SOCKET.value:
                        tar_sockets = self.nearest_target_sockets()
                    else:
                        tar_sockets = self.nearest_target_sockets(only_input=True)
                    self.target_any = next((sk for sk in tar_sockets if (not sk.tar.links) and sk.tar.node.type != "REROUTE"), None)
                    if self.target_any:
                        unhide_node_reassign(self.target_any.tar.node, self, cond=self.target_any) # 对于套接字模式也需要重绘, 因为连接的套接字节点可能是折叠的.
            
            case eMode.HIDE_AUTO:
                for tar_nd in self.get_nearest_nodes(cur_x_off=0):
                    nd = tar_nd.tar
                    if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                        continue
                    if nd.type=='REROUTE': # 对于这个工具, reroute 会被跳过, 原因很明显.
                        continue
                    self.target_any = tar_nd

                    # 对于节点模式, 展开光标下的所有节点或不展开, 没有区别.
                    if prefs.vht_is_toggle_nodes_on_drag:
                        if self.firstResult is None:
                            # 如果对节点的激活没有改变任何东西, 那么对于其余的, 最好是隐藏而不是展开. 但当前概念不允许,
                            # 根本没有这方面的信息. 所以我在这里局部地实现了它, 而不是修改实现本身.
                            LGetVisSide = lambda puts: [sk for sk in puts if sk.enabled and not sk.hide]
                            list_visibleSks = [LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]
                            self.firstResult = HideFromNode(prefs, nd, True, False)
                            HideFromNode(prefs, nd, self.firstResult, True) # 注意: 改变节点 (为了下面的检查), 但不要动 'self.firstResult'.
                            if list_visibleSks==[LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]:
                                self.firstResult = True
                        HideFromNode(prefs, nd, self.firstResult, True)
                        # 参见 wiki, 为什么 isReDrawAfterChange 选项被删除了.
                        #Todo0v6SF 唯一可能的解决方案是, 在绘制一帧后_再_改变节点.
                        #^ 也就是说, 附加到新节点一帧, 然后立即处理它, 同时寻找新节点并向其绘制 (如 wiki 中的示例).
                    break
    def run(self, event, prefs, tree):
        match eMode(self.toolMode):
            case eMode.HIDE_AUTO:
                if not prefs.vht_is_toggle_nodes_on_drag:
                    # 在隐藏套接字时, 需要所有套接字的信息, 因此执行两次. 第一次收集信息, 第二次执行.
                    HideFromNode(prefs, self.target_any.tar, HideFromNode(prefs, self.target_any.tar, True), True)
            case eMode.HIDE_SOCKET:
                tar_socket = self.target_any.tar
                tar_socket.hide = True
                # 自动隐藏接口优化-inline
                inline_socket_node_list = [
                        'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput',
                        'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                        'GeometryNodeForeachGeometryElementInput', 'GeometryNodeForeachGeometryElementOutput',
                        "GeometryNodeCaptureAttribute", "GeometryNodeBake",
                                        ]
                try:
                    tar_node = tar_socket.node
                    socket_identifier = tar_socket.identifier
                    if tar_node.bl_idname == "GeometryNodeCaptureAttribute":
                        socket_identifier = tar_socket.name
                    if tar_node.bl_idname in inline_socket_node_list:
                        if tar_socket.is_output:
                            tar_node.inputs[socket_identifier].hide = True
                        else:
                            tar_node.outputs[socket_identifier].hide = True
                except:
                    pass
            case eMode.HIDE_VALUE:
                socket = self.target_any.tar
                node = socket.node
                def hide_sk_value_in_tree(tar_tree: bpy.types.NodeTree):
                    for item in tar_tree.interface.items_tree:
                        if item.item_type == 'SOCKET' and item.identifier == socket.identifier:
                            item.hide_value = not socket.hide_value
                if node.type == "GROUP":
                    node: bpy.types.NodeGroup
                    hide_sk_value_in_tree(node.node_tree)
                elif isinstance(node, bpy.types.NodeGroupOutput):
                    hide_sk_value_in_tree(bpy.context.space_data.edit_tree)
                else:
                    socket.hide_value = not socket.hide_value

    def initialize(self, event, prefs, tree):
        self.firstResult = None # 从第一个节点获取“折叠”或“展开”的动作, 然后将其广播到所有其他遇到的节点.
    @staticmethod
    def draw_pref_settings(col, prefs):
        split_prop(col, prefs, 'vht_hide_bool_socket')
        split_prop(col, prefs, 'vht_hide_hidden_bool_socket')
        split_prop(col, prefs, 'vht_never_hide_geometry')
        split_prop(col, prefs, 'vht_is_unhide_virtual', bool_label_left=True)
        split_prop(col, prefs, 'vht_is_toggle_nodes_on_drag', bool_label_left=True)
