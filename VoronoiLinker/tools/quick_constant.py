import bpy
from bpy.types import NodeSocket, NodeTree, UILayout, Node
from ..base_tool import unhide_node_reassign, TripleSocketTool
from ..globals import AllQuickConstant, Cursor_X_Offset
from ..utils.drawing import draw_sockets_template
from ..utils.node import opt_tar_socket
from .matrix_convert import Convert_Data, PIE_MT_Combine_Matrix, PIE_MT_Convert_To_Rotation

B = bpy.types

def get_const_node(tree: NodeTree, sk_type: str):
    return AllQuickConstant.get(tree.bl_idname, None).get(sk_type, None)

# todo: 允许 同时从 浮点 整数 拉出 浮点/
class NODE_OT_voronoi_quick_constant(TripleSocketTool):
    bl_idname = 'node.voronoi_quick_constant'
    bl_label = "Voronoi Quick Constant"
    bl_description = "Tool for quickly adding constant value nodes.\nSupports various data types including vectors, colors, matrices and more."
    use_for_custom_tree = False
    can_draw_settings = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def callback_draw_tool(self, drawer):
        draw_sockets_template(drawer, self.target_sk0, self.target_sk1, self.target_sk2, tool_name="Quick Constant")
    def find_targets_tool(self, is_first_active, prefs, tree):
        if is_first_active:
            self.target_sk0 = None
        if not self.canPickThird:
            self.target_sk1 = None
        for tar_nd in self.get_nearest_nodes(cur_x_off= -Cursor_X_Offset):
            nd = tar_nd.tar
            tar_sks_out = self.get_nearest_sockets(nd, cur_x_off= -Cursor_X_Offset)[0]
            if not tar_sks_out:
                continue
            if is_first_active:
                for tar in tar_sks_out:
                    # ! AllQuickConstant 新的接口类型要在这里更新
                    if get_const_node(tree, tar.tar.type):
                        self.target_sk0 = tar
                        break
                unhide_node_reassign(nd, self, cond=True, flag=True)
                break
            unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
            sk_out0 = opt_tar_socket(self.target_sk0)
            if sk_out0:
                only_single_link = {'MENU'}
                if sk_out0.type in only_single_link:     # 小王 输出接口类型 不允许同时连到多个输入接口
                    break
                if not self.canPickThird:
                    for tar in tar_sks_out:
                        if tar.tar.type==sk_out0.type:
                            self.target_sk1 = tar
                            break
                    if (self.target_sk1)and(self.target_sk1.tar==sk_out0):
                        self.target_sk1 = None
                        break
                    unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
                    if self.target_sk1:
                        break
                else:
                    sk_out1 = opt_tar_socket(self.target_sk1)
                    for tar in tar_sks_out:
                        if tar.tar.type==sk_out0.type:
                            self.target_sk2 = tar
                            break
                    if (self.target_sk2) and ((self.target_sk2.tar == sk_out0) or (sk_out1) and (self.target_sk2.tar == sk_out1)):
                        self.target_sk2 = None
                        break
                    unhide_node_reassign(nd, self, cond=self.target_sk2, flag=False)
                    if self.target_sk2:
                        break
    def can_run(self):
        return not not self.target_sk0
    def run(self, event, prefs, tree):
        skIn0 = self.target_sk0.tar
        if skIn0.type in ["ROTATION", "MATRIX"]:
            Convert_Data.sk0 = skIn0
            if self.target_sk1:
                Convert_Data.sk1 = self.target_sk1.tar
            if self.target_sk2:
                Convert_Data.sk2 = self.target_sk2.tar
            if skIn0.type == "ROTATION":
                if hasattr(skIn0, "default_value"):
                    bpy.ops.wm.call_menu_pie(name=PIE_MT_Convert_To_Rotation.bl_idname)
                # return {'FINISHED'}       # 想松开按键确认
                # new_node.width = 200   # md这里不行，运行ops后立马运行下面的了？放在Rotation_Convert里的invoke就行了？ (那里放好这里忘删了找了半天错误)
            if skIn0.type == "MATRIX":
                bpy.ops.wm.call_menu_pie(name=PIE_MT_Combine_Matrix.bl_idname)
        else:
            node_type = get_const_node(tree, skIn0.type)
            if node_type == "NodeClosureOutput":
                bpy.ops.node.add_closure_zone('INVOKE_DEFAULT', use_transform=True)
            else:
                bpy.ops.node.add_node('INVOKE_DEFAULT', type=node_type, use_transform=not self.isPlaceImmediately)
            new_node = tree.nodes.active
            sk_out = new_node.outputs[0]

            tree.links.new(sk_out, skIn0)
            if self.target_sk1:
                tree.links.new(sk_out, self.target_sk1.tar)
            if self.target_sk2:
                tree.links.new(sk_out, self.target_sk2.tar)

            if isinstance(new_node, (B.NodeClosureOutput, B.NodeCombineBundle)):
                bpy.ops.node.sockets_sync()
                return

            if not hasattr(skIn0, "default_value"): return
            value = skIn0.default_value

            if isinstance(new_node, B.ShaderNodeValue):
                new_node.outputs[0].default_value = value
            elif isinstance(new_node, (B.FunctionNodeInputColor, B.ShaderNodeRGB)):
                new_node.value = value
            elif isinstance(new_node, B.FunctionNodeInputInt):
                new_node.integer = value
            elif isinstance(new_node, B.FunctionNodeInputBool):
                new_node.boolean = value
            elif isinstance(new_node, B.FunctionNodeInputString):
                new_node.string = value
            elif isinstance(new_node, B.GeometryNodeInputImage):
                new_node.image = value
            elif isinstance(new_node, B.GeometryNodeInputMaterial):
                new_node.material = value
            elif isinstance(new_node, B.GeometryNodeInputObject):
                new_node.object = value
            elif isinstance(new_node, B.GeometryNodeInputCollection):
                new_node.collection = value
            elif isinstance(new_node, B.FunctionNodeEulerToRotation):
                new_node.inputs[0].default_value = value
            elif isinstance(new_node, B.ShaderNodeCombineXYZ):
                dimension = len(value)
                if dimension == 4:  # todo 暂时不实现
                    pass
                if dimension == 2:
                    new_node.inputs[2].hide = True
                for i in range(dimension):
                    new_node.inputs[i].default_value = value[i]
            elif isinstance(new_node, B.GeometryNodeIndexSwitch):
                new_node.data_type = "MENU"
                new_node.show_options = False

                new_node.inputs[-1].hide = True
                items = get_menu_socket_items(skIn0)
                fill_index_switch_inputs(new_node, items)
                if skIn0.default_value != '':
                    new_node.inputs[0].default_value = items.index(skIn0.default_value)

def get_menu_socket_items(socket: bpy.types.NodeSocket) -> list[str]:
    try:
        socket.default_value = "__INVALID__"
    except TypeError as e:
        err_msg = str(e)
        start = err_msg.index("not found in (") + len("not found in (")
        end = err_msg.rindex(")")
        items_str = err_msg[start:end]
        if items_str:
            return [x.strip().strip("'\"") for x in items_str.split(",")]
    return []

def fill_index_switch_inputs(node: Node, items: list[str]):
    items_l = len(items)
    if items_l >= 2:
        for i in range(items_l - 2):
            bpy.ops.node.index_switch_item_add()
    for i in range(items_l):
        node.inputs[i + 1].default_value = items[i]
