bl_info = {
    "name" : "小王-复制节点带驱动器和关键帧",
    "author" : "小王", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 1, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}


import bpy
import bpy.utils.previews

addon_keymaps = {}

def find_user_keyconfig(key):
    km, kmi = addon_keymaps[key]
    for item in bpy.context.window_manager.keyconfigs.user.keymaps[km.name].keymap_items:
        found_item = False
        if kmi.idname == item.idname:
            found_item = True
            for name in dir(kmi.properties):
                if not name in ["bl_rna", "rna_type"] and not name[0] == "_":
                    if name in kmi.properties and name in item.properties and not kmi.properties[name] == item.properties[name]:
                        found_item = False
        if found_item:
            return item
    print(f"Couldn't find keymap item for {key}, using addon keymap instead. This won't be saved across sessions!")
    return kmi


class SNA_OT_My_Generic_Operator_Dcb80(bpy.types.Operator):
    bl_idname = "sna.my_generic_operator_dcb80"
    bl_label = "小王-复制节点带驱动器和关键帧"
    bl_description = "复制节点带驱动器和关键帧"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0):
            cls.poll_message_set('')
        return True

    def execute(self, context):
        if context.selected_nodes:
            o_node = bpy.ops.node
            nodes = context.space_data.edit_tree.nodes
            tem_location = context.space_data.cursor_location
            o_node.group_make('INVOKE_DEFAULT')
            o_node.tree_path_parent('INVOKE_DEFAULT')
            context.active_node.node_tree.name = ".辅助复制节点驱动器组"
            context.active_node.name = ".辅助复制节点驱动器组节点"
            o_node.clipboard_copy('INVOKE_DEFAULT')
            o_node.group_ungroup('INVOKE_DEFAULT')
            if context.active_node:
                context.active_node.select = False
            o_node.clipboard_paste()     # 粘贴后待在原地不动
            # o_node.clipboard_paste('INVOKE_DEFAULT')     # INVOKE_DEFAULT 正常应该粘贴到鼠标位置，却有位置加上鼠标位置的偏移量
            nodes.active = nodes[".辅助复制节点驱动器组节点"]
            nodes.active.location = context.space_data.cursor_location
            o_node.group_ungroup('INVOKE_DEFAULT')
            bpy.data.node_groups.remove(bpy.data.node_groups[".辅助复制节点驱动器组"])
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_add_to_node_mt_node_E9FCE(self, context):
    if not (False):
        layout = self.layout
        op = layout.operator('sna.my_generic_operator_dcb80', text='复制节点带驱动器和关键帧', icon_value=519, emboss=True, depress=False)
        layout.separator(factor=1.0)


class SNA_AddonPreferences_7AF95(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        if not (False):
            layout = self.layout 
            split = layout.split(factor=0.5, align=False)
            split.label(text='复制节点带驱动器和关键帧:', icon_value=519)
            split.prop(find_user_keyconfig('D6F5D'), 'type', text='', full_event=True)

def register():
    bpy.types.NODE_MT_select.prepend(sna_add_to_node_mt_node_E9FCE)
    bpy.utils.register_class(SNA_OT_My_Generic_Operator_Dcb80)
    bpy.utils.register_class(SNA_AddonPreferences_7AF95)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new('sna.my_generic_operator_dcb80', 'SIX', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    addon_keymaps['D6F5D'] = (km, kmi)

def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.types.NODE_MT_select.remove(sna_add_to_node_mt_node_E9FCE)
    bpy.utils.unregister_class(SNA_OT_My_Generic_Operator_Dcb80)
    bpy.utils.unregister_class(SNA_AddonPreferences_7AF95)
