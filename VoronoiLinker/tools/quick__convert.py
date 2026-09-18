import bpy
from enum import Enum
from bpy.types import Context, Node, NodeSocket, NodeTree
from ..base_tool import BaseOperator
from ..common_class import VmtData

Convert_Data = VmtData()

CLOSURE_ZONE = '__CLOSURE_ZONE__'

# nodes.sockets_sync understands these; never call it while a transform modal is running.
_SYNC_NODE_TYPES = {
    'NodeCombineBundle', 'NodeSeparateBundle', 'NodeJoinBundle',
    'NodeEvaluateClosure', 'NodeClosureOutput', 'NodeClosureInput',
}

class Convert(Enum):
    combine_matrix = 'combine_matrix'
    separate_matrix = 'separate_matrix'
    rotation_to = 'rotation_to'
    to_rotation = 'to_rotation'
    bundle_from_out = 'bundle_from_out'
    bundle_from_in = 'bundle_from_in'
    closure_from_out = 'closure_from_out'
    closure_from_in = 'closure_from_in'


# Official Add > Utilities > Rotation, plus XYZ shortcuts used by the old convert pie.
_ROTATION_FROM_OUT = [
    ('Invert Rotation', 'FunctionNodeInvertRotation'),
    ('Rotate Rotation', 'FunctionNodeRotateRotation'),
    ('Align Rotation to Vector', 'FunctionNodeAlignRotationToVector'),
    ('Rotate Vector', 'FunctionNodeRotateVector'),
    ('Mix Rotation', 'ShaderNodeMix'),
    ('Rotation > Euler', 'FunctionNodeRotationToEuler'),
    ('Rotation > Axis Angle', 'FunctionNodeRotationToAxisAngle'),
    ('Rotation > Quaternion', 'FunctionNodeRotationToQuaternion'),
    ('Rotation > Separate XYZ', 'ShaderNodeSeparateXYZ'),
]

_ROTATION_TO_ROT = [
    ('Euler > Rotation', 'FunctionNodeEulerToRotation'),
    ('Axis Angle > Rotation', 'FunctionNodeAxisAngleToRotation'),
    ('Quaternion > Rotation', 'FunctionNodeQuaternionToRotation'),
    ('Axes to Rotation', 'FunctionNodeAxesToRotation'),
    ('Align Rotation to Vector', 'FunctionNodeAlignRotationToVector'),
    ('Invert Rotation', 'FunctionNodeInvertRotation'),
    ('Rotate Rotation', 'FunctionNodeRotateRotation'),
    ('Mix Rotation', 'ShaderNodeMix'),
    ('Input Rotation', 'FunctionNodeInputRotation'),
    ('Combine XYZ > Rotation', 'ShaderNodeCombineXYZ'),
]

PIE_MENU_ITEMS: dict[Convert, list[tuple[str, str]]] = {
    Convert.combine_matrix: [
        ('Combine Transform', 'FunctionNodeCombineTransform'),
        ('Combine Matrix', 'FunctionNodeCombineMatrix'),
    ],
    Convert.separate_matrix: [
        ('Separate Matrix', 'FunctionNodeSeparateMatrix'),
        ('Separate Transform', 'FunctionNodeSeparateTransform'),
    ],
    Convert.rotation_to: _ROTATION_FROM_OUT,
    Convert.to_rotation: _ROTATION_TO_ROT,
    Convert.bundle_from_out: [
        ('Separate Bundle', 'NodeSeparateBundle'),
        ('Join Bundle', 'NodeJoinBundle'),
        ('Store', 'NodeStoreBundleItem'),
        ('Get Bundle Item', 'NodeGetBundleItem'),
        ('Get Nested Bundle Path', 'NodeGetNestedBundlePaths'),
    ],
    Convert.bundle_from_in: [
        ('Combine Bundle', 'NodeCombineBundle'),
        ('Store', 'NodeStoreBundleItem'),
        ('Get Bundle Item', 'NodeGetBundleItem'),
        ('Get Nested Bundle Path', 'NodeGetNestedBundlePaths'),
        ('Join Bundle', 'NodeJoinBundle'),
    ],
    Convert.closure_from_out: [
        ('Evaluate Closure', 'NodeEvaluateClosure'),
        ('Set Default Closure', 'GeometryNodeSetClosureDefault'),
    ],
    Convert.closure_from_in: [
        ('Closure', CLOSURE_ZONE),
        ('Set Default Closure', 'GeometryNodeSetClosureDefault'),
        ('Evaluate Closure', 'NodeEvaluateClosure'),
    ],
}

current_pie = None


def convert_key_for_socket(sk: NodeSocket):
    if sk is None:
        return None
    if sk.is_output:
        return {
            'ROTATION': Convert.rotation_to,
            'MATRIX': Convert.separate_matrix,
            'BUNDLE': Convert.bundle_from_out,
            'CLOSURE': Convert.closure_from_out,
        }.get(sk.type)
    return {
        'ROTATION': Convert.to_rotation,
        'MATRIX': Convert.combine_matrix,
        'BUNDLE': Convert.bundle_from_in,
        'CLOSURE': Convert.closure_from_in,
    }.get(sk.type)


def call_convert_pie_for_socket(sk: NodeSocket, *extra: NodeSocket | None) -> bool:
    key = convert_key_for_socket(sk)
    if not key:
        return False
    Convert_Data.sk0 = sk
    Convert_Data.sk1 = extra[0] if len(extra) > 0 else None
    Convert_Data.sk2 = extra[1] if len(extra) > 1 else None
    call_convert_pie(key)
    return True


def call_convert_pie(menu_key: Convert) -> None:
    global current_pie
    current_pie = menu_key
    bpy.ops.wm.call_menu_pie(name=NODE_MT_voronoi_convert.bl_idname)


def _node_type_available(node_type: str, tree_idname: str) -> bool:
    if node_type == CLOSURE_ZONE:
        return hasattr(bpy.ops.node, 'add_closure_zone') and tree_idname in {
            'GeometryNodeTree', 'ImageNodeTree', '',
        }
    if node_type == 'NodeGetNestedBundlePaths' and tree_idname not in {'GeometryNodeTree', ''}:
        return False
    if node_type == 'GeometryNodeSetClosureDefault' and tree_idname not in {'GeometryNodeTree', ''}:
        return False
    return hasattr(bpy.types, node_type)


def _pie_items(context: Context) -> list[tuple[str, str]]:
    items = PIE_MENU_ITEMS.get(current_pie) or []
    tree_idname = getattr(getattr(context, 'space_data', None), 'tree_type', '') or ''
    return [(text, node_type) for text, node_type in items if _node_type_available(node_type, tree_idname)]


class NODE_MT_voronoi_convert(bpy.types.Menu):
    bl_label = "Voronoi Convert"
    bl_idname = "NODE_MT_voronoi_convert"

    def draw(self, context):
        items = _pie_items(context)
        pie = self.layout.menu_pie()
        if len(items) <= 8:
            for text, node_type in items:
                op = pie.operator(NODE_OT_voronoi_convert.bl_idname, text=text)
                op.node_type = node_type
            return
        left = pie.box().column(align=True)
        right = pie.box().column(align=True)
        mid = (len(items) + 1) // 2
        for i, (text, node_type) in enumerate(items):
            col = left if i < mid else right
            op = col.operator(NODE_OT_voronoi_convert.bl_idname, text=text)
            op.node_type = node_type


def _first_socket(socks, sk_type: str | None = None) -> NodeSocket | None:
    typed = []
    for sk in socks:
        if getattr(sk, 'is_unavailable', False):
            continue
        if sk_type and sk.type != sk_type:
            continue
        if sk.enabled:
            return sk
        typed.append(sk)
    if typed:
        return typed[0]
    return None


def _try_link(tree: NodeTree, a: NodeSocket, b: NodeSocket) -> bool:
    if not (a and b):
        return False
    try:
        tree.links.new(a, b, handle_dynamic_sockets=True)
        return True
    except TypeError:
        try:
            tree.links.new(a, b)
            return True
        except Exception:
            return False
    except Exception:
        return False


def _start_transform() -> None:
    try:
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
    except Exception:
        pass


def _resolve_socket(tree: NodeTree, node_name: str | None, identifier: str | None, is_output: bool) -> NodeSocket | None:
    if not (node_name and identifier):
        return None
    node = tree.nodes.get(node_name)
    if node is None:
        return None
    socks = node.outputs if is_output else node.inputs
    for sk in socks:
        if sk.identifier == identifier:
            return sk
    return None


def _sync_selected_node(tree: NodeTree, node: Node) -> None:
    if node is None or node.bl_idname not in _SYNC_NODE_TYPES:
        return
    for nd in tree.nodes:
        nd.select = False
    node.select = True
    tree.nodes.active = node
    try:
        bpy.ops.node.sockets_sync(node_name=node.name)
    except Exception:
        pass


def _add_closure_zone(tree: NodeTree, sk_in: NodeSocket | None, use_transform: bool) -> Node | None:
    """Create a Closure zone without a live transform modal.

    ``add_closure_zone(INVOKE, use_transform=True)`` starts
    ``translate_attach_remove_on_cancel``, which deletes the zone on cancel and
    holds node pointers. ``sockets_sync`` (especially when the new Closure
    Output is already linked to Evaluate Closure) rebuilds sockets and may copy
    a default zone into the tree. Doing that during the modal crashes Blender.
    """
    sk_name = sk_in.node.name if sk_in else None
    sk_ident = getattr(sk_in, 'identifier', None) if sk_in else None
    sk_is_out = sk_in.is_output if sk_in else False
    existing = {nd.name for nd in tree.nodes}

    try:
        bpy.ops.node.add_closure_zone('EXEC_DEFAULT', use_transform=False)
    except Exception:
        return None

    out_nd = None
    in_nd = None
    for nd in tree.nodes:
        if nd.name in existing:
            continue
        if nd.bl_idname == 'NodeClosureOutput':
            out_nd = nd
        elif nd.bl_idname == 'NodeClosureInput':
            in_nd = nd
    if out_nd is None:
        for nd in tree.nodes:
            if not nd.select:
                continue
            if nd.bl_idname == 'NodeClosureOutput':
                out_nd = nd
            elif nd.bl_idname == 'NodeClosureInput':
                in_nd = nd
    if out_nd is None:
        return None

    target = _resolve_socket(tree, sk_name, sk_ident, sk_is_out)
    if target is not None:
        closure_sk = _first_socket(out_nd.outputs, 'CLOSURE')
        _try_link(tree, closure_sk, target)

    _sync_selected_node(tree, out_nd)

    for nd in tree.nodes:
        nd.select = nd.name not in existing
    if in_nd is not None:
        in_nd.select = True
    out_nd.select = True
    tree.nodes.active = out_nd
    if use_transform:
        _start_transform()
    return out_nd


def _prepare_new_node(node: Node, sk0: NodeSocket) -> None:
    if node.bl_idname == 'ShaderNodeMix' and sk0.type == 'ROTATION':
        try:
            node.data_type = 'ROTATION'
        except Exception:
            pass
        for sk in node.inputs:
            ident = getattr(sk, 'identifier', '') or ''
            if ident in {'Factor_Float', 'Fac'} or (sk.type == 'VALUE' and sk.name in {'Factor', 'Fac'}):
                try:
                    sk.default_value = 0.5
                except Exception:
                    pass


def _copy_rotation_default(node: Node, sk0: NodeSocket) -> None:
    if not hasattr(sk0, 'default_value'):
        return
    value = sk0.default_value
    if node.bl_idname == 'FunctionNodeEulerToRotation':
        try:
            node.inputs[0].default_value = value
        except Exception:
            pass
    elif node.bl_idname == 'FunctionNodeInputRotation':
        try:
            if hasattr(node, 'rotation'):
                node.rotation = value
            else:
                node.outputs[0].default_value = value
        except Exception:
            pass
    elif node.bl_idname == 'ShaderNodeCombineXYZ':
        try:
            node.inputs[0].default_value = value[0]
            node.inputs[1].default_value = value[1]
            node.inputs[2].default_value = value[2]
        except Exception:
            pass


def _run_node_convert(context: Context, shift: bool, alt: bool, node_type: str):
    tree: NodeTree = context.space_data.edit_tree
    sk0 = Convert_Data.sk0
    sk1 = Convert_Data.sk1
    sk2 = Convert_Data.sk2
    extras = [sk for sk in (sk1, sk2) if sk and sk0 and sk.type == sk0.type]

    if node_type == CLOSURE_ZONE:
        target = sk0 if (sk0 and not sk0.is_output) else None
        _add_closure_zone(tree, target, use_transform=True)
        return

    needs_sync = node_type in _SYNC_NODE_TYPES
    try:
        bpy.ops.node.add_node(
            'EXEC_DEFAULT' if needs_sync else 'INVOKE_DEFAULT',
            type=node_type,
            use_transform=not needs_sync,
        )
    except Exception:
        return
    new_node = context.active_node
    if new_node is None:
        return
    _prepare_new_node(new_node, sk0)

    if sk0 is not None and not sk0.is_output:
        src = _first_socket(new_node.outputs, sk0.type) or _first_socket(new_node.outputs)
        _try_link(tree, src, sk0)
        for extra in extras:
            _try_link(tree, src, extra)
        _copy_rotation_default(new_node, sk0)
    elif sk0 is not None:
        dst = _first_socket(new_node.inputs, sk0.type) or _first_socket(new_node.inputs)
        _try_link(tree, sk0, dst)
        for i, extra in enumerate(extras):
            same = [sk for sk in new_node.inputs if sk.type == extra.type and sk.enabled]
            if len(same) > i + 1:
                _try_link(tree, extra, same[i + 1])
            elif dst:
                _try_link(tree, extra, dst)

    if needs_sync:
        _sync_selected_node(tree, new_node)
        new_node.select = True
        tree.nodes.active = new_node
        _start_transform()


class NODE_OT_voronoi_convert(BaseOperator):
    bl_idname = "node.voronoi_convert"
    bl_label = "Voronoi Convert"
    node_type: bpy.props.StringProperty()

    def invoke(self, context, event):
        _run_node_convert(context, event.shift, event.alt, self.node_type)
        return {'FINISHED'}
