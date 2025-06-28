# print("=" * 100)
# print("=" * 100)
# print("=" * 100)

import bpy, ctypes
from bpy.types import Operator, NodeSocket

# from .获取接口位置_精简版本 import sk_loc2
from .test_bpy import print_bpy
# from mathutils import Vector


# a = 255
# print(f"{a:b}")
# print(f"{a:#b}")
# print(f"{a:#o}")
# print(f"{a:x}")
# print(f"{a:#X}")        # #会添加 0b 0o 0x 前缀

# print("[[fill]align][sign][#][0][width][,][.precision][type]")
# print("[[fill]align] 表示: align 是可选的，但 fill 只有在 align 存在的情况下才能使用")

# print(f"{1024:#016b}")
# print(f"{1024:#016o}")
# print(f"{1024:#016X}")

# def group_string(s: str, group_size: int, separator: str = ' ') -> str:
#     """从右向左按指定大小分组字符串"""
#     if len(s) <= group_size: return s
#     s_reversed = s[::-1]
#     grouped = separator.join(s_reversed[i:i + group_size] for i in range(0, len(s_reversed), group_size))
#     return grouped[::-1]

# print(group_string(f"{1024:#018b}", 4))
# print(group_string(f"{1024:#018o}", 4))
# print(group_string(f"{1024:#018X}", 4))


def sk_loc2(socket: NodeSocket):
    # return Vec2((ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24))
    arr = (ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24)
    return f" Vector({arr[0]:5}, {arr[1]:5})"
    # return f" Vector({arr[0]:*5.0f}, {arr[1]:*5.0f})"


class NODE_OT_print_socket_location(Operator):
    bl_idname = "node.print_socket_location"
    bl_label = "Print Socket Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print_bpy()
        a_node = context.active_node
        if not a_node:
            self.report({'INFO'}, "No active node selected.")
            return {'CANCELLED'}
        print(f"\n--- Node: '{a_node.name}' (Type: {a_node.bl_idname}) ---")

        if a_node.inputs:
            print("Inputs:")
            for socket in a_node.inputs:
                print(f"  - {socket.name:20} {sk_loc2(socket)}")
        else:
            print("Inputs: None")

        if a_node.outputs:
            print("Outputs:")
            for socket in a_node.outputs:
                print(f"  - {socket.name:20} {sk_loc2(socket)}")
        else:
            print("Outputs: None")
        print("-------------------------------------------------")

        return {'FINISHED'}

class NODE_PT_socket_printer_panel(bpy.types.Panel):
    bl_label = "Socket Printer"
    bl_idname = "NODE_PT_socket_printer"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Socket Printer"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(NODE_OT_print_socket_location.bl_idname)

classes = (
    NODE_OT_print_socket_location,
    NODE_PT_socket_printer_panel,
)

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(NODE_OT_print_socket_location.bl_idname, 'P', 'PRESS', ctrl=True, alt=True, shift=False)
    addon_keymaps.append((km, kmi))

def unregister():
    # 注销快捷键
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # 以相反的顺序注销所有类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
