import bpy
from bpy.types import Node, NodeSocket, NodeTree
from typing import Any
B = bpy.types

from .globals import is_bl5_plus

node_has_items = {
    'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT', 'MENU_SWITCH', 'BAKE', 'CAPTURE_ATTRIBUTE',
    'INDEX_SWITCH'
}

# Equestrian 的意思是"骑手"或"马术的",取其驾驭、控制的寓意.似乎是专门用来操作管理有 item 的节点, 比如:
# 这些节点都有一个共同点: 它们内部有自己的items, 可以动态地添加、删除、移动它们上面的插槽 (socket).
# 提供了一套统一的 API 来驾驭它们的内部接口, 抽象成了统一的操作
class NodeItemsUtils:
    support_types = node_has_items | {
        'GROUP',
        'GROUP_INPUT',
        'GROUP_OUTPUT',
        "FOREACH_GEOMETRY_ELEMENT_INPUT",
        "FOREACH_GEOMETRY_ELEMENT_OUTPUT",
    }
    only_inputs = {'GROUP_OUTPUT', 'INDEX_SWITCH'}
    has_extend_socket = property(lambda self: self.type in ('SIM', 'REP', 'MENU', 'CAPTURE', 'BAKE'))
    is_index_switch = property(lambda self: self.type == 'INDEX')  # 编号切换单独判断

    @staticmethod
    def is_socket_definitely(ess: Any): # 未使用
        base = ess.bl_rna
        while base:
            identifier = base.identifier
            base = base.base
        if identifier == 'NodeSocket':
            return True
        if identifier == 'Node':
            return False
        return None

    @staticmethod
    def is_item_socket_allowed(node: Node, from_sk: NodeSocket):
        if (from_sk.bl_idname == 'NodeSocketVirtual') and (node.type in node_has_items):
            return False
        match node.type:
            case 'SIMULATION_INPUT':
                return from_sk != node.outputs[0]
            case 'REPEAT_INPUT':
                return from_sk != node.inputs[0]
            case 'SIMULATION_OUTPUT' | 'REPEAT_INPUT':
                return from_sk != node.inputs[0]
            case 'MENU_SWITCH':
                return from_sk not in {node.inputs[0], node.outputs[0]}
            case 'CAPTURE_ATTRIBUTE':
                return hasattr(node, "capture_items") and from_sk not in {node.inputs[0], node.outputs[0]}
            case _:
                return True  # raise Exception("is_item_socket_allowed() 调用时未针对 SimRep")

    def contains_item(self, target_item: Any):
        for item in self.items:  # 没有这个 API (或者至少我没找到)，所以不得不“实际”检查匹配。
            if item == target_item:
                return True
        return False

    def get_item(self, from_sk: NodeSocket):
        """ get_item_from_socket """
        if from_sk.node != self.node:
            raise Exception(f"Equestrian node is not equal `{from_sk.path_from_id()}`")
        match self.type:
            case 'SIM' | 'REP':
                for item in self.items:
                    if item.name == from_sk.name:
                        return item
                raise Exception(f"Interface not found from `{from_sk.path_from_id()}`")  # 如果套接字在节点上直接重命名，而不是通过接口。
            case 'CLASSIC' | 'GROUP':
                for item in self.items:
                    if (item.item_type == 'SOCKET') and (item.identifier == from_sk.identifier):
                        return item
            case 'MENU' | 'BAKE' | 'CAPTURE' | 'FOREACH_OUT':
                for item in self.items:
                    if item.name == from_sk.name:
                        return item

    def get_socket(self, item: Any, *, is_out: bool):
        """ get_socket_from_item """
        # 不知道干什么用的,会导致节点组连到组输入报错
        # if not self.contains_item(item): raise Exception(f"Equestrian items does not contain `{item}`")
        match self.type:
        # 小王-插入接口会用到
            case 'SIM' | 'REP' | 'CAPTURE' | 'BAKE' | 'MENU':
                for sk in (self.node.outputs if is_out else self.node.inputs):
                    if sk.name == item.name:
                        return sk
            case 'INDEX':
                for sk in self.node.inputs:
                    if sk.name == item.name:
                        return sk
            case 'CLASSIC' | 'GROUP':
                if item.item_type == 'PANEL':
                    raise Exception(f"`Panel cannot be used for search: {item}`")
                for sk in (self.node.outputs if is_out else self.node.inputs):
                    if sk.identifier == item.identifier:
                        return sk
                raise Exception(f"`Socket for node side not found: {item}`")

    def new_item_from_socket(self, from_sk: NodeSocket, is_flip_side: bool = False):
        from .utils.node import socket_label, sk_type_to_idname, add_item_for_index_switch, is_builtin_tree  # 延迟导入避免循环导入
        sk_name = socket_label(from_sk)
        sk_type = from_sk.type
        match self.type:
            case 'SIM' | 'REP' | 'BAKE' | 'CAPTURE':
                if sk_type == 'VALUE':
                    sk_type = 'FLOAT'
                geometry_items: B.NodeGeometrySimulationOutputItems | B.NodeGeometryRepeatOutputItems | B.NodeGeometryBakeItems | B.NodeGeometryCaptureAttributeItems = self.items
                # todo 过滤不支持的接口类型
                try:
                    return geometry_items.new(sk_type, sk_name)
                except:
                    pass
            case 'MENU':
                menu_items: B.NodeMenuSwitchItems = self.items
                return menu_items.new(sk_name)
            case 'INDEX':
                if from_sk.is_output:
                    return add_item_for_index_switch(self.node)
                return
            case 'CLASSIC' | 'GROUP':
                # self.items 是 tree.interface.items_tree  是 bpy_prop_collection[NodeTreeInterfaceItem]
                data: B.NodeTreeInterface = self.items.data
                interface_sk = data.new_socket(sk_name,
                                               socket_type=sk_type_to_idname(from_sk),
                                               in_out='OUTPUT' if (from_sk.is_output ^ is_flip_side) else 'INPUT')
                interface_sk.hide_value = from_sk.hide_value
                if hasattr(interface_sk, 'default_value') and from_sk.type != "MENU":
                    # todo 菜单接口先连线才能设置默认值啊
                    interface_sk.default_value = from_sk.default_value
                    if hasattr(interface_sk, 'min_value'):
                        nd = from_sk.node
                        if (nd.type in {'GROUP_INPUT', 'GROUP_OUTPUT'}) or ((nd.type == 'GROUP') and (nd.node_tree)):
                            # 如果套接字来自另一个节点组，则完全复制。
                            source_item = NodeItemsUtils(nd).get_item(from_sk)
                            for pr in interface_sk.rna_type.properties:
                                if not (pr.is_readonly or pr.is_registered):
                                    setattr(interface_sk, pr.identifier, getattr(source_item, pr.identifier))
                    # tovo2v6 用于 `interface_sk.subtype =` 的套接字 blid 替换映射。
                    # TODO0 需要想办法在创建之前嵌入，以便所有组的套接字立即拥有 item 默认值。Blender 自己是怎么做到的？
                    def fix_in_tree(tree: NodeTree):
                        for nd in tree.nodes:
                            if (nd.type == 'GROUP') and (nd.node_tree == self.tree):
                                for sk in nd.inputs:
                                    if sk.identifier == interface_sk.identifier:
                                        sk.default_value = from_sk.default_value

                    for ng in bpy.data.node_groups:
                        if is_builtin_tree(ng.bl_idname):
                            fix_in_tree(ng)
                    data_names = ['materials', 'scenes', 'worlds', 'textures', 'lights', 'linestyles']
                    if is_bl5_plus:
                        data_names.remove('scenes')
                    for att in data_names:  # 是这些，还是我忘了某个？
                        for dt in getattr(bpy.data, att):
                            if dt.node_tree:  # 对于 materials -- https://github.com/ugorek000/VoronoiLinker/issues/19; 我仍然不明白它怎么可能是 None。
                                fix_in_tree(dt.node_tree)
                return interface_sk

    def move_items(self, from_item: Any, to_item: Any, *, is_swap: bool = False):  # 本可以自行处理“按 item 移动”的复杂性，但这已经是调用方的责任了。
        match self.type:
            case 'SIM' | 'REP' | 'MENU' | 'BAKE' | 'CAPTURE':  # 小王-支持交换接口
                inx_from = -1
                inx_to = -1
                # 参见 get_socket() 中对 item 存在的检查。
                for cyc, item in enumerate(self.items):
                    if item == from_item:
                        inx_from = cyc
                    if item == to_item:
                        inx_to = cyc
                if inx_from == -1:
                    raise Exception(f"Index not found from `{from_item}`")
                if inx_to == -1:
                    raise Exception(f"Index not found from `{to_item}`")
                # self.items.move(inx_from, inx_to + (inx_from < inx_to))
                self.items.move(inx_from, inx_to)
                if is_swap:
                    self.items.move(inx_to + (1 - (inx_to > inx_from) * 2), inx_from)
            case 'CLASSIC' | 'GROUP':
                items_tree: B.bpy_prop_collection[B.NodeTreeInterfaceItem] = self.items
                interface: B.NodeTreeInterface = items_tree.data
                from_item: B.NodeTreeInterfaceItem
                to_item: B.NodeTreeInterfaceItem
                from_parent = from_item.parent
                from_pos = from_item.position
                to_parent = to_item.parent
                to_pos = to_item.position
                interface.move_to_parent(from_item, to_parent, to_pos)
                if is_swap:
                    interface.move_to_parent(to_item, from_parent, from_pos)

    def __init__(self, sk_or_nd: NodeSocket | Node):
        is_socket = hasattr(sk_or_nd, 'link_limit')
        tar_node: Node = sk_or_nd.node if is_socket else sk_or_nd  # type: ignore
        if tar_node.type not in self.support_types:
            raise Exception(f"Equestrian not found from `{sk_or_nd.path_from_id()}`")
        self.tree: NodeTree = sk_or_nd.id_data
        self.node: Node = tar_node
        tar_node = getattr(tar_node, 'paired_output', tar_node)

        if isinstance(tar_node, (B.NodeGroupInput, B.NodeGroupOutput)):
            self.type = 'CLASSIC'
            self.items = self.tree.interface.items_tree  # bpy_prop_collection[NodeTreeInterfaceItem]
        elif isinstance(tar_node, B.GeometryNodeSimulationOutput):
            self.type = 'SIM'
            self.items = tar_node.state_items
        elif isinstance(tar_node, B.GeometryNodeRepeatOutput):
            self.type = 'REP'
            self.items = tar_node.repeat_items
        # 小王-更改接口名称
        elif isinstance(tar_node, B.GeometryNodeMenuSwitch):
            self.type = 'MENU'
            self.items = tar_node.enum_items
        elif isinstance(tar_node, B.GeometryNodeIndexSwitch):
            self.type = 'INDEX'
            self.items = tar_node
        elif isinstance(tar_node, B.GeometryNodeBake):
            self.type = 'BAKE'
            self.items = tar_node.bake_items
        elif isinstance(tar_node, B.GeometryNodeCaptureAttribute):
            self.type = 'CAPTURE'
            self.items = tar_node.capture_items
        # elif isinstance(tar_node, B.GeometryNodeForeachGeometryElementInput):
        #     # for each zone 的重命名有点麻烦,不过这个目前优先级低
        #     self.type = 'FOREACH_IN'
        #     self.items = tar_node.input_items
        elif isinstance(tar_node, B.GeometryNodeForeachGeometryElementOutput):
            self.type = 'FOREACH_OUT'
            # self.items = tar_node.main_items
            self.items = tar_node.generation_items
        elif tar_node.type == "GROUP":
            # GeometryNodeGroup 不是 NodeGroup 的 子类
            tar_node: B.NodeGroup
            self.type = 'GROUP'
            if not tar_node.node_tree:
                raise Exception(f"Tree for nodegroup `{tar_node.path_from_id()}` not found, from `{sk_or_nd.path_from_id()}`")
            self.items = tar_node.node_tree.interface.items_tree
        else:
            raise Exception(f"Unhandled equestrian node type: `{type(tar_node).__name__}` (bl_idname=`{tar_node.bl_idname}`, node.type=`{tar_node.type}`) from `{sk_or_nd.path_from_id()}`")
