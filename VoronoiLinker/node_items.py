import bpy
from enum import Enum, auto
from bpy.types import Node, NodeSocket, NodeTree
from typing import Any
B = bpy.types

from .globals import is_bl5_plus

# 新建组接口时不要抄这些: 只读、身份信息、或依赖邻居/面板才可写的标志.
_INTERFACE_COPY_SKIP = {
    'rna_type', 'bl_rna', 'name', 'identifier', 'item_type', 'index', 'position',
    'socket_type', 'parent', 'in_out', 'select', 'is_panel_toggle',
    'join_to_next_parameter',  # 排在最后时只读, 抄了会把后面的默认值同步打断
}


def _snapshot_rna_value(val):
    if val is None or isinstance(val, (str, bytes, bool, int, float)):
        return val
    try:
        return val[:]
    except Exception:
        try:
            return tuple(val)
        except Exception:
            return val


def _assign_rna(dst, ident, value) -> bool:
    try:
        setattr(dst, ident, value)
        return True
    except Exception:
        return False


def _copy_default_value(dst, src) -> None:
    if src is None or not hasattr(dst, 'default_value') or not hasattr(src, 'default_value'):
        return
    _assign_rna(dst, 'default_value', _snapshot_rna_value(src.default_value))


def _copy_interface_props(dst, src) -> None:
    if src is None:
        return
    for pr in dst.rna_type.properties:
        ident = pr.identifier
        if ident == 'default_value' or ident in _INTERFACE_COPY_SKIP:
            continue
        if pr.is_readonly or pr.is_registered:
            continue
        if not hasattr(src, ident):
            continue
        _assign_rna(dst, ident, _snapshot_rna_value(getattr(src, ident)))
    _copy_default_value(dst, src)


def _sync_group_socket_defaults(group_tree: NodeTree, interface_sk, from_sk: NodeSocket) -> None:
    if not hasattr(interface_sk, 'default_value'):
        return
    default = _snapshot_rna_value(interface_sk.default_value)

    def fix_in_tree(tree: NodeTree):
        for nd in tree.nodes:
            if nd.type == 'GROUP' and nd.node_tree == group_tree:
                for sk in nd.inputs:
                    if sk.identifier == interface_sk.identifier and hasattr(sk, 'default_value'):
                        _assign_rna(sk, 'default_value', default)

    from .utils.node import is_builtin_tree
    for ng in bpy.data.node_groups:
        if is_builtin_tree(ng.bl_idname):
            fix_in_tree(ng)
    data_names = ['materials', 'scenes', 'worlds', 'textures', 'lights', 'linestyles']
    if is_bl5_plus:
        data_names.remove('scenes')
    for att in data_names:
        for dt in getattr(bpy.data, att):
            if dt.node_tree:
                fix_in_tree(dt.node_tree)
    try:
        group_tree.interface_update(bpy.context)
    except Exception:
        pass

node_has_items = {
    'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT', 'MENU_SWITCH', 'BAKE', 'CAPTURE_ATTRIBUTE',
    'INDEX_SWITCH'
}

class eType(Enum):
    # `auto()` 会自动为每个枚举成员分配一个唯一值; 这里我们只关心“成员身份”, 不关心具体数值. 枚举成员不强制全大写, 但全大写是常见约定, 看起来更像一组固定常量.
    CLASSIC = auto()
    SIM = auto()
    REP = auto()
    MENU = auto()
    INDEX = auto()
    BAKE = auto()
    CAPTURE = auto()
    GROUP = auto()
    FOREACH_OUT = auto()

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
    has_extend_socket = property(lambda self: self.type in {eType.SIM, eType.REP, eType.MENU, eType.CAPTURE, eType.BAKE})
    is_index_switch = property(lambda self: self.type == eType.INDEX)  # 编号切换单独判断

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
            case eType.SIM | eType.REP:
                for item in self.items:
                    if item.name == from_sk.name:
                        return item
                raise Exception(f"Interface not found from `{from_sk.path_from_id()}`")  # 如果套接字在节点上直接重命名，而不是通过接口。
            case eType.CLASSIC | eType.GROUP:
                for item in self.items:
                    if (item.item_type == 'SOCKET') and (item.identifier == from_sk.identifier):
                        return item
            case eType.MENU | eType.BAKE | eType.CAPTURE | eType.FOREACH_OUT:
                for item in self.items:
                    if item.name == from_sk.name:
                        return item

    def get_socket(self, item: Any, *, is_out: bool):
        """ get_socket_from_item """
        # 不知道干什么用的,会导致节点组连到组输入报错
        # if not self.contains_item(item): raise Exception(f"Equestrian items does not contain `{item}`")
        match self.type:
            case eType.SIM | eType.REP | eType.CAPTURE | eType.BAKE | eType.MENU:
                for sk in (self.node.outputs if is_out else self.node.inputs):
                    if sk.name == item.name:
                        return sk
            case eType.INDEX:
                for sk in self.node.inputs:
                    if sk.name == item.name:
                        return sk
            case eType.CLASSIC | eType.GROUP:
                if item.item_type == 'PANEL':
                    raise Exception(f"`Panel cannot be used for search: {item}`")
                for sk in (self.node.outputs if is_out else self.node.inputs):
                    if sk.identifier == item.identifier:
                        return sk
                raise Exception(f"`Socket for node side not found: {item}`")

    def new_item_from_socket(self, from_sk: NodeSocket, is_flip_side: bool = False):
        from .utils.node import socket_label, sk_type_to_idname, add_item_for_index_switch
        sk_name = socket_label(from_sk)
        sk_type = from_sk.type
        match self.type:
            case eType.SIM | eType.REP | eType.BAKE | eType.CAPTURE:
                if sk_type == 'VALUE':
                    sk_type = 'FLOAT'
                geometry_items: B.NodeGeometrySimulationOutputItems | B.NodeGeometryRepeatOutputItems | B.NodeGeometryBakeItems | B.NodeGeometryCaptureAttributeItems = self.items
                # todo 过滤不支持的接口类型
                try:
                    return geometry_items.new(sk_type, sk_name)
                except:
                    pass
            case eType.MENU:
                menu_items: B.NodeMenuSwitchItems = self.items
                return menu_items.new(sk_name)
            case eType.INDEX:
                if from_sk.is_output:
                    return add_item_for_index_switch(self.node)
                return
            case eType.CLASSIC | eType.GROUP:
                # self.items 是 tree.interface.items_tree  是 bpy_prop_collection[NodeTreeInterfaceItem]
                data: B.NodeTreeInterface = self.items.data
                interface_sk = data.new_socket(sk_name,
                                               socket_type=sk_type_to_idname(from_sk),
                                               in_out='OUTPUT' if (from_sk.is_output ^ is_flip_side) else 'INPUT')
                interface_sk.hide_value = from_sk.hide_value
                nd = from_sk.node
                source_item = None
                if (nd.type in {'GROUP_INPUT', 'GROUP_OUTPUT'}) or ((nd.type == 'GROUP') and (nd.node_tree)):
                    source_item = NodeItemsUtils(nd).get_item(from_sk)
                # 先写当前插座默认值; 组接口再抄 subtype/min/max, 最后覆盖 default_value.
                # join_to_next_parameter 等只读属性跳过, 避免打断后面的默认值.
                if from_sk.type != "MENU":
                    _copy_default_value(interface_sk, from_sk)
                if source_item:
                    _copy_interface_props(interface_sk, source_item)
                _sync_group_socket_defaults(self.tree, interface_sk, from_sk)
                return interface_sk

    def move_items(self, from_item: Any, to_item: Any, *, is_swap: bool = False):  # 本可以自行处理“按 item 移动”的复杂性，但这已经是调用方的责任了。
        match self.type:
            case eType.SIM | eType.REP | eType.MENU | eType.BAKE | eType.CAPTURE:
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
            case eType.CLASSIC | eType.GROUP:
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
            self.type = eType.CLASSIC
            self.items = self.tree.interface.items_tree  # bpy_prop_collection[NodeTreeInterfaceItem]
        elif isinstance(tar_node, B.GeometryNodeSimulationOutput):
            self.type = eType.SIM
            self.items = tar_node.state_items
        elif hasattr(B, "GeometryNodeRepeatOutput") and isinstance(tar_node, B.GeometryNodeRepeatOutput):
            self.type = eType.REP
            self.items = tar_node.repeat_items
        elif hasattr(B, "GeometryNodeMenuSwitch") and isinstance(tar_node, B.GeometryNodeMenuSwitch):
            self.type = eType.MENU
            self.items = tar_node.enum_items
        elif hasattr(B, "GeometryNodeIndexSwitch") and isinstance(tar_node, B.GeometryNodeIndexSwitch):
            self.type = eType.INDEX
            self.items = tar_node
        elif hasattr(B, "GeometryNodeBake") and isinstance(tar_node, B.GeometryNodeBake):
            self.type = eType.BAKE
            self.items = tar_node.bake_items
        elif hasattr(B, "GeometryNodeCaptureAttribute") and isinstance(tar_node, B.GeometryNodeCaptureAttribute):
            self.type = eType.CAPTURE
            self.items = tar_node.capture_items
        # elif hasattr(B, "GeometryNodeForeachGeometryElementInput") and isinstance(tar_node, B.GeometryNodeForeachGeometryElementInput):
        #     # for each zone 的重命名有点麻烦,不过这个目前优先级低
        #     self.type = eType.FOREACH_IN
        #     self.items = tar_node.input_items
        elif hasattr(B, "GeometryNodeForeachGeometryElementOutput") and isinstance(tar_node, B.GeometryNodeForeachGeometryElementOutput):
            self.type = eType.FOREACH_OUT
            # self.items = tar_node.main_items
            self.items = tar_node.generation_items
        elif tar_node.type == "GROUP":
            # GeometryNodeGroup 不是 NodeGroup 的 子类
            tar_node: B.NodeGroup
            self.type = eType.GROUP
            if not tar_node.node_tree:
                raise Exception(f"Tree for nodegroup `{tar_node.path_from_id()}` not found, from `{sk_or_nd.path_from_id()}`")
            # 后续同步实例 socket 时要匹配被修改的节点组树，而不是当前外层编辑树。
            self.tree = tar_node.node_tree
            self.items = tar_node.node_tree.interface.items_tree
        else:
            raise Exception(f"Unhandled equestrian node type: `{type(tar_node).__name__}` (bl_idname=`{tar_node.bl_idname}`, node.type=`{tar_node.type}`) from `{sk_or_nd.path_from_id()}`")
