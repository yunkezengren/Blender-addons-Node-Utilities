bl_info = {
    "name"       : "Node Width Resize",
    "author"     : "Don Schnitzius",
    "version"    : (1, 4, 0),
    "blender"    : (3, 0, 0),
    "location"   : "Node Editor > Sidebar > Arrange",
    "description": "Assign a Fixed Width to Selected Nodes",
    "warning"    : "",
    "doc_url"   : "https://github.com/don1138/blender-qrn",
    "support"    : "COMMUNITY",
    "category"   : "Node",
}

import bpy
from bpy.types import Operator, Panel


def get_active_tree(context):
    tree = context.space_data.node_tree
    path = []
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
            path.append(tree)
    return tree, path


def get_nodes_links(context):
    tree, path = get_active_tree(context)
    return tree.nodes, tree.links


class RN_PT_NodePanel(Panel):
    bl_category = "节点树"
    bl_label = "Resize Nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        if context.selected_nodes is None:
            return
        layout = self.layout
        # node = context.space_data.node_tree.nodes.active
        node = context.selected_nodes
        # if node and node.select:
        if node:
            self.draw_panel(layout)
        else:
            layout.label(text="(No Node Selected)", icon='GHOST_DISABLED')

    def draw_panel(self, layout):
        row = layout.row()
        row.label(text="Set Node Width:")

        row = layout.row()
        row.operator('node.button_width_default')
        row = layout.row()
        row.operator('node.button_140')
        row = layout.row()
        row.operator('node.button_100')
        row.operator('node.button_160')
        row.operator('node.button_180')
        row.operator('node.button_200')
        row = layout.row(align=True)
        row.scale_x = 2.0
        row.operator('node.button_225')
        row.operator('node.button_250')
        row.operator('node.button_275')
        row.operator('node.button_300')
        row = layout.row(align=True)
        row.operator('node.button_325')
        row.operator('node.button_350')
        row.operator('node.button_375')
        row.operator('node.button_400')
        row = layout.row(align=True)
        row.operator('node.button_toggle_hidden')

class RN_OT__NodeButton_width_default(Operator):
    """Set node width to width_default"""
    bl_idname = 'node.button_width_default'
    bl_label = '默认宽度'

    def execute(self, context):
        for node in context.selected_nodes:
            node.width = node.bl_width_default
        return {'FINISHED'}

class RN_OT__NodeButton100(Operator):
    """Set node width to 100"""
    bl_idname = 'node.button_100'
    bl_label = '100'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 100
        return {'FINISHED'}

class RN_OT__NodeButton140(Operator):
    """Set node width to 140"""
    bl_idname = 'node.button_140'
    bl_label = '140'

    def execute(self, context):
        # node = context.space_data.node_tree.nodes.active
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 140
        return {'FINISHED'}

class RN_OT__NodeButton160(Operator):
    """Set node width to 160"""
    bl_idname = 'node.button_160'
    bl_label = '160'

    def execute(self, context):
        # node = context.space_data.node_tree.nodes.active
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 160
        return {'FINISHED'}

class RN_OT__NodeButton180(Operator):
    """Set node width to 180"""
    bl_idname = 'node.button_180'
    bl_label = '180'

    def execute(self, context):
        # node = context.space_data.node_tree.nodes.active
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 180
        return {'FINISHED'}

class RN_OT__NodeButton200(Operator):
    """Set node width to 200"""
    bl_idname = 'node.button_200'
    bl_label = '200'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 200
        return {'FINISHED'}

class RN_OT__NodeButton225(Operator):
    """Set node width to 225"""
    bl_idname = 'node.button_225'
    bl_label = '225'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 225
        return {'FINISHED'}

class RN_OT__NodeButton250(Operator):
    """Set node width to 250"""
    bl_idname = 'node.button_250'
    bl_label = '250'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 250
        return {'FINISHED'}

class RN_OT__NodeButton275(Operator):
    """Set node width to 275"""
    bl_idname = 'node.button_275'
    bl_label = '275'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 275
        return {'FINISHED'}

class RN_OT__NodeButton300(Operator):
    """Set node width to 300"""
    bl_idname = 'node.button_300'
    bl_label = '300'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 300
        return {'FINISHED'}

class RN_OT__NodeButton325(Operator):
    """Set node width to 325"""
    bl_idname = 'node.button_325'
    bl_label = '325'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 325
        return {'FINISHED'}

class RN_OT__NodeButton350(Operator):
    """Set node width to 350"""
    bl_idname = 'node.button_350'
    bl_label = '350'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 350
        return {'FINISHED'}

class RN_OT__NodeButton375(Operator):
    """Set node width to 375"""
    bl_idname = 'node.button_375'
    bl_label = '375'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 375
        return {'FINISHED'}

class RN_OT__NodeButton400(Operator):
    """Set node width to 400"""
    bl_idname = 'node.button_400'
    bl_label = '400'

    def execute(self, context):
        # nodes, links = get_nodes_links(context)
        for node in context.selected_nodes:
            node.width = 400
        return {'FINISHED'}

class RN_OT__NodeButtonHideToggle(Operator):
    """Toggle Hidden Node Sockets"""
    bl_idname = 'node.button_toggle_hidden'
    bl_label = 'Toggle Hidden Sockets (⌃H)'

    def execute(self, context):
        bpy.ops.node.hide_socket_toggle()
        return {'FINISHED'}


classes = [
    RN_PT_NodePanel,
    RN_OT__NodeButton_width_default,
    RN_OT__NodeButton100,
    RN_OT__NodeButton140,
    RN_OT__NodeButton160,
    RN_OT__NodeButton180,
    RN_OT__NodeButton200,
    RN_OT__NodeButton225,
    RN_OT__NodeButton250,
    RN_OT__NodeButton275,
    RN_OT__NodeButton300,
    RN_OT__NodeButton325,
    RN_OT__NodeButton350,
    RN_OT__NodeButton375,
    RN_OT__NodeButton400,
    RN_OT__NodeButtonHideToggle
]


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
