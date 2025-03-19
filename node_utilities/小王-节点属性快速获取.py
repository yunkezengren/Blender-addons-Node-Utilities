bl_info = {
    "name" : "小王-节点属性快速获取",
    "author" : "一尘不染", 
    "description" : "节点N面板-节点-属性-(数据路径 bl_idname type)",
    "blender" : (3, 0, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}


import bpy

class SNA_PT_panel_AEA7A(bpy.types.Panel):
    bl_label = 'API属性'
    bl_idname = 'SNA_PT_panel_AEA7A'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = ''
    bl_order = 0
    bl_parent_id = 'NODE_PT_active_node_generic'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        node = context.active_node
        layout = self.layout

        op = layout.operator("wm.context_set_string", text="数据路径", icon="FILE_SCRIPT")
        op.data_path = "window_manager.clipboard"
        op.value = ".".join([repr(node.id_data), node.path_from_id()])
        op.value = repr(node.id_data) + "." + node.path_from_id()

        op = layout.operator("wm.context_set_string", text="bl_idname: "+node.bl_idname)
        op.data_path = "window_manager.clipboard"
        # op.value = repr(node.bl_idname).replace("'", "")
        # op.value = node.bl_idname
        op.value = '"' + node.bl_idname + '"'
        # op.value = '"' + node.bl_idname + '"'
        # op.value = f'"{node.bl_idname}"'
        
        op = layout.operator("wm.context_set_string", text="type: "+node.type)
        op.data_path = "window_manager.clipboard"
        # op.value = repr(node.type).replace("'", "")
        op.value = node.type
        
        # # todo 突然不想搞了
        # if node.bl_idname == "GeometryNodeGroup" and bpy.app.version >= (4, 2, 0):
        #     # bpy.data.node_groups["NodeGroup.001"].color_tag
        #     op = layout.operator("wm.context_set_string", text="type: "+node.type)
        #     op.data_path = "window_manager.clipboard"
        #     # op.value = repr(node.type).replace("'", "")
        #     op.value = node.type

def add_color_tag_to_active_node_panel(self, context):
    layout = self.layout
    node = context.active_node
    if node.bl_idname == "GeometryNodeGroup":
        layout.prop(node.node_tree, 'color_tag', text='Color Tag')
    
def add_bl_idname_to_active_node_panel(self, context):
    layout = self.layout
    nodes = context.selected_nodes
    active_node_idname = context.active_node.bl_idname
    text = ""
    # print(nodes)
    # print(len(nodes))
    if len(nodes) == 1:
        text = active_node_idname
        # text = '"' + active_node_idname + '"'
    else:
        for node in nodes:
            text += '"' + node.bl_idname + '"' + ", \n"
        
    op = layout.operator("wm.context_set_string", text=active_node_idname, icon="FILE_SCRIPT")
    op.data_path = "window_manager.clipboard"
    op.value = text
    # op.value = text.replace("'", "")


def register():

    # bpy.types.Scene.color_tag  = bpy.props.EnumProperty(name='列表排序方式', description='属性列表多种排序方式', 
    #                                         items=[ ('按类型排序1',      '按类型排序1',      '布尔-浮点-整数-矢量-颜色-旋转', 0, 0), 
    #                                                 ('按类型排序1-反转', '按类型排序1-反转', '旋转-颜色-矢量-整数-浮点-布尔', 0, 1), 
    #                                                 ('按类型排序2',      '按类型排序2',      '整数-布尔-浮点-矢量-颜色-旋转', 0, 2), 
    #                                                 ('完全按字符串排序', '完全按字符串排序', '首字-数字英文中文',             0, 3)])

    bpy.utils.register_class(SNA_PT_panel_AEA7A)
    bpy.types.NODE_PT_active_node_generic.append(add_color_tag_to_active_node_panel)
    bpy.types.NODE_PT_active_node_generic.append(add_bl_idname_to_active_node_panel)


def unregister():

    bpy.types.NODE_PT_active_node_generic.remove(add_color_tag_to_active_node_panel)
    bpy.types.NODE_PT_active_node_generic.remove(add_bl_idname_to_active_node_panel)
    bpy.utils.unregister_class(SNA_PT_panel_AEA7A)
