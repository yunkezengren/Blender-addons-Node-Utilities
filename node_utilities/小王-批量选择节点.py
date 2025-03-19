bl_info = {
    "name" : "小王-批量选择节点",
    "author" : "小王", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}


import bpy
import bpy.utils.previews


addon_keymaps = {}
_icons = None


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


class SNA_OT_Select_By_Selected_Nodes_Type(bpy.types.Operator):
    bl_idname = "sna.select_by_selected_nodes_type"
    bl_label = "Selected_Nodes_Type"
    bl_description = "遍历选中节点类型"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        tree = context.space_data.edit_tree
        for selected_node in context.selected_nodes:
            for node in tree.nodes:
                if node.bl_idname == selected_node.bl_idname:
                    node.select = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_By_Type_Operation(bpy.types.Operator):
    bl_idname = "sna.select_by_type_operation"
    bl_label = "Select_Type_Operation"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        active_node = context.active_node
        tree = context.space_data.edit_tree
        nodes =  tree.nodes
        if active_node and active_node.select and hasattr(active_node, "operation"):
            for node in nodes:
                if node.bl_idname == active_node.bl_idname and node.operation == active_node.operation:
                    node.select = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_By_Label(bpy.types.Operator):
    bl_idname = "sna.select_by_label"
    bl_label = "Select_By_Label"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        active_node = context.active_node
        tree = context.space_data.edit_tree
        nodes =  tree.nodes
        if active_node and active_node.select:
            for node in nodes:
                if node.label == active_node.label:
                    node.select = True
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_By_Group(bpy.types.Operator):
    bl_idname = "sna.select_by_group"
    bl_label = "Select_Group"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        active_node = context.active_node
        tree = context.space_data.edit_tree
        nodes =  tree.nodes
        if active_node.bl_idname == "GeometryNodeGroup":
            for node in nodes:
                if node.bl_idname == "GeometryNodeGroup" and node.node_tree.name == active_node.node_tree.name:
                    node.select = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Select_By_Active_node_In_SelectNodes(bpy.types.Operator):
    bl_idname = "sna.select_by_active_node_in_selectnodes"
    bl_label = "Select_Group"
    bl_description = "选中节点里的活动节点"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        active_node = context.active_node
        tree = context.space_data.edit_tree
        nodes = tree.nodes
        for node in nodes:
            if active_node.bl_idname != node.bl_idname:
                node.select = False
            # if active_node.bl_idname == "GeometryNodeGroup" and node.bl_idname == "GeometryNodeGroup":
            if active_node.bl_idname == node.bl_idname == "GeometryNodeGroup":
                if node.node_tree.name != active_node.node_tree.name:
                    node.select = False
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_MT_Select_Menu(bpy.types.Menu):
    bl_idname = "SNA_MT_Select_Menu"
    bl_label = "小王-增强批量选择节点"

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('node.select_grouped', text='类型')
        op.type = 'TYPE'
        op = layout.operator('sna.select_by_selected_nodes_type', text='选中节点类型')
        op = layout.operator('sna.select_by_active_node_in_selectnodes', text='选中节点里的活动节点')
        op = layout.operator('sna.select_by_type_operation', text='类型+选项')
        op = layout.operator('sna.select_by_label', text='标签')
        op = layout.operator('sna.select_by_group', text='节点组名字')
        op = layout.operator('node.select_grouped', text='颜色')
        op.type = 'COLOR'
        op = layout.operator('node.select_grouped', text='名称前缀')
        op.type = 'PREFIX'
        op = layout.operator('node.select_grouped', text='名称后缀')
        op.type = 'SUFFIX'


class SNA_AddonPreferences_3ADFD(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout 
        split = layout.split(factor=0.5)
        split.label(text='批量选择节点快捷键', icon_value=0)
        split.prop(find_user_keyconfig('F980C'), 'type', text='', full_event=True)

classes = [
    SNA_OT_Select_By_Selected_Nodes_Type,
    SNA_OT_Select_By_Active_node_In_SelectNodes,
    SNA_OT_Select_By_Type_Operation,
    SNA_OT_Select_By_Label,
    SNA_OT_Select_By_Group,
    SNA_MT_Select_Menu,
    SNA_AddonPreferences_3ADFD,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    for i in classes:
        bpy.utils.register_class(i)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new('wm.call_menu', 'G', 'PRESS',
        ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'SNA_MT_Select_Menu'
    addon_keymaps['F980C'] = (km, kmi)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    for i in classes:
        bpy.utils.unregister_class(i)

