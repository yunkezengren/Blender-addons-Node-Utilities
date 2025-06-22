import bpy
from .获取接口位置 import sk_loc

class NODE_OT_print_socket_location(bpy.types.Operator):
    bl_idname = "node.print_socket_location"
    bl_label = "Print Socket Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        a_node = context.active_node
        if not a_node:
            self.report({'INFO'}, "No active node selected.")
            return {'CANCELLED'}
        print(f"\n--- Node: '{a_node.name}' (Type: {a_node.bl_idname}) ---")

        if a_node.inputs:
            print("Inputs:")
            for socket in a_node.inputs:
                print(f"  - {socket.name:20} {sk_loc(socket)}")
        else:
            print("Inputs: None")

        # 遍历输出接口
        if a_node.outputs:
            print("\nOutputs:")
            for socket in a_node.outputs:
                print(f"  - {socket.name:20} {sk_loc(socket)}")
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
