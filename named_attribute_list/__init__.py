import bpy
import bpy.utils.previews
import os

bl_info = {
    "name" : "小王-几何节点命名属性列表",
    "author" : "小王", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 4, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}
a = "+-*/!@#$%^&*()"
# a = "abcdefghijklmnopqrstuvwxyz"
addon_keymaps = {}
_icons = None

domain_en = [
        'POINT',
        'EDGE',
        'FACE',
        'CORNER',
        'CURVE',
        'INSTANCE',
        'LAYER',
        ]
domain_cn = [
        '点',
        '边',
        '面',
        '面拐',
        '样条线',
        '实例',
        '层',
        ]
get_domain_cn = {k: v for k, v in zip(domain_en, domain_cn)}

data_types = [
            'BOOLEAN',
            'FLOAT',
            'INT',
            'FLOAT_VECTOR',
            'FLOAT_COLOR',
            'QUATERNION',
            ]
shader_date_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
png_list = [
            '域-布尔.png',
            '域-浮点.png',
            '域-整数.png',
            '域-矢量.png',
            '域-颜色.png',
            '域-旋转.png',
            ]
data_with_png = {k: v for k, v in zip(data_types, png_list)}

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

def sna_add_to_attr_list_mt_editor_menus(self, context):
    if context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree']:
        layout = self.layout
        layout.menu('ATTRLIST_MT_Menu', text='属性', icon_value=0)

class ATTRLIST_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = 'addon_59776'

    def draw(self, context):
        if not (False):
            layout = self.layout 
            layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
            layout.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='显示命名属性列表', full_event=True)


class ATTRLIST_MT_Menu(bpy.types.Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = "命名属性列表"

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        menu_text_icon_sort(layout, context)

class ATTRLIST_OT_Add_Node_Change_Name_Type_Hide(bpy.types.Operator):
    bl_idname = "sna.add_node_change_name_and_type"
    bl_label = "属性隐藏选项"
    bl_description = "快捷键Shift 2 "
    bl_options = {"REGISTER", "UNDO"}
    sna_attr_name:  bpy.props.StringProperty(name='attr_name', description='', default="", subtype='NONE')
    sna_attr_type:  bpy.props.StringProperty(name='attr_type', description='', default="", subtype='NONE')

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        data_type = self.sna_attr_type
        scene = context.scene
        if context.area.ui_type == 'GeometryNodeTree':
            scene.panel_info = "添加已命名属性节点"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = self.sna_attr_name
            attr_node.inputs["Name"].hide = scene.sna_hide_Name_socket
            attr_node.show_options = not scene.sna_hide_option
            attr_node.hide = scene.sna_hide_Node
            if scene.sna_rename_Node:
                attr_node.label = self.sna_attr_name
            if scene.sna_rename_Attr_socket:
                for socket in attr_node.outputs:
                    if socket.enabled and not socket.hide and socket.name=="Attribute":
                        socket.name = self.sna_attr_name
            attr_node.outputs["Exists"].hide = scene.sna_hide_Exists_socket
        if context.area.ui_type == 'ShaderNodeTree':
            scene.panel_info = "添加属性节点"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='ShaderNodeAttribute')
            # [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
            shader_attr_node = context.active_node
            shader_attr_node.attribute_name = self.sna_attr_name
            socket_order = { 'BOOLEAN'     : 2,
                             'FLOAT'       : 2,
                             'INT'         : 2,
                             'FLOAT_VECTOR': 1,
                             'FLOAT_COLOR' : 0,
                            }
            for i, out_soc in enumerate(shader_attr_node.outputs):
                if i != socket_order[data_type]:
                    out_soc.hide = True
            
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class ATTRLIST_PT_NPanel(bpy.types.Panel):
    bl_label = '命名属性列表'
    bl_idname = 'ATTRLIST_PT_NPanel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Node'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree']

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            info = "活动物体及节点树属性"
        if ui_type == 'ShaderNodeTree':
            info = "活动物体属性"
        a_node = context.active_node
        if a_node.bl_idname == "GeometryNodeObjectInfo" and a_node.select:
            obj_name = a_node.inputs[0].default_value.name
            info = obj_name + "的属性"
            # info = a_node.name
        layout.label(text=info, icon='GEOMETRY_NODES')

        arrow_show = "TRIA_RIGHT" if not scene.add_settings else "TRIA_DOWN"
        
        box = layout.box()
        box.scale_y = 0.8
        box.prop(scene, "add_settings", emboss=True, icon=arrow_show)
        if scene.add_settings:
            layout = box
            
            split1 = layout.split(factor=0.5)
            split1.label(text='快捷键:')
            split1.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)

            split = layout.split(factor=0.5)
            split.prop(scene, 'sna_hide_option',        toggle=True, text='隐藏节点选项')
            split.prop(scene, 'sna_hide_Exists_socket', toggle=True, text='隐藏存在接口')
            split = layout.split(factor=0.5)
            split.prop(scene, 'sna_hide_Name_socket',   toggle=True, text='隐藏名称接口')
            split.prop(scene, 'sna_rename_Attr_socket', toggle=True, text='重命名属性接口')
            split = layout.split(factor=0.5)
            split.prop(scene, 'sna_hide_Node',          toggle=True, text='折叠隐藏节点')
            split.prop(scene, 'sna_rename_Node',        toggle=True, text='重命名节点标签')
        
        arrow_add = "TRIA_RIGHT" if not scene.show_settings else "TRIA_DOWN"
        box = layout.box()
        box.scale_y = 0.8
        box.prop(scene, "show_settings", emboss=True, icon=arrow_add)
        if scene.show_settings:
            layout = box

            split2 = layout.split(factor=0.4)
            split2.label(text='列表排序方式')
            split2.prop(scene, 'sna_sort_list', text='')
            
            layout.label(text='属性列表里是否显示')
            split3 = layout.split(factor=0.05)
            split3.label(text="")
            split31 = split3.split(factor=0.35)
            split31.prop(scene, 'sna_show_vertex_group', toggle=True, text='顶点组')
            split32 = split31.split(factor=0.4)
            split32.prop(scene, 'sna_show_uv_map',       toggle=True, text='UV')
            split32.prop(scene, 'sna_show_color_attr',   toggle=True, text='颜色属性')
            
            layout.label(text='属性列表里是否隐藏')
            split4 = layout.split(factor=0.05)
            split4.label(text="")
            split41 = split4.split(factor=0.5)
            split41.prop(scene, 'only_show_used_attr', toggle=True, text='未使用属性')
            split41.prop(scene, 'hide_attr_of_group',  toggle=True, text='节点组内属性')

        menu_text_icon_sort(layout, context)
# class ATTRLIST_PT_Add_Settings(bpy.types.Panel):
#     bl_idname = 'ATTRLIST_PT_Add_Settings'
#     bl_space_type = 'NODE_EDITOR'
#     bl_options = {'DEFAULT_CLOSED'}
#     bl_parent_id = 'ATTRLIST_PT_NPanel'
#     bl_label = '添加设置'
#     bl_region_type = 'UI'
#     bl_context = ''

#     @classmethod
#     def poll(cls, context):
#         return not (False)

#     def draw(self, context):
#         scene = context.scene
#         layout = self.layout

#         split1 = layout.split(factor=0.5)
#         split1.label(text='快捷键:')
#         split1.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)

#         split = layout.split(factor=0.5)
#         split.prop(scene, 'sna_hide_option',        text='隐藏节点选项')
#         split.prop(scene, 'sna_hide_Exists_socket', text='隐藏存在接口')
#         split = layout.split(factor=0.5)
#         split.prop(scene, 'sna_hide_Name_socket',   text='隐藏名称接口')
#         split.prop(scene, 'sna_rename_Attr_socket', text='重命名属性接口')
#         split = layout.split(factor=0.5)
#         split.prop(scene, 'sna_hide_Node',          text='折叠隐藏节点')
#         split.prop(scene, 'sna_rename_Node',        text='重命名节点标签')

# class ATTRLIST_PT_Show_Settings(bpy.types.Panel):
#     bl_idname = 'ATTRLIST_PT_Show_Settings'
#     bl_space_type = 'NODE_EDITOR'
#     bl_parent_id = 'ATTRLIST_PT_NPanel'
#     bl_label = '显示设置'
#     bl_region_type = 'UI'
#     bl_context = ''

#     @classmethod
#     def poll(cls, context):
#         return not (False)

#     def draw(self, context):
#         scene = context.scene
        
#         icon_1 = "TRIA_RIGHT" if not scene.add_settings else "TRIA_DOWN"
#         box = layout.box()
#         box.prop(scene, "add_settings", emboss=False, icon=icon_1)

#         if scene.add_settings:
#             layout = box

#             split2 = layout.split(factor=0.4)
#             split2.label(text='列表排序方式')
#             split2.prop(scene, 'sna_sort_list', text='')
            
#             split3 = layout.split(factor=0.28)
#             split3.label(text='是否显示')
#             split31 = split3.split(factor=0.35)
#             split31.prop(scene, 'sna_show_vertex_group', text='顶点组')
#             split32 = split31.split(factor=0.4)
#             split32.prop(scene, 'sna_show_uv_map', text='UV')
#             split32.prop(scene, 'sna_show_color_attr', text='颜色属性')
            
#             split4 = layout.split(factor=0.28)
#             split4.label(text='是否隐藏')
#             split41 = split4.split(factor=0.5)
#             split41.prop(scene, 'only_show_used_attr', text='未使用属性')
#             split41.prop(scene, 'hide_attr_of_group',  text='节点组内属性')



def is_node_linked(node):
    soc_out = node.outputs
    if len(soc_out):
        for soc in soc_out:
            if soc.is_linked:
                return True
    return False

def get_attributes(tree, show_unused=True):
    # show_unused=False的话，接下来判断is_node_linked
    # print("tree", tree)
    # print("tree.name", tree.name)
    # print(tree.nodes)
    nodes = tree.nodes
    links = tree.links
    attributes = {}
    # 第一种
    for node in nodes:
        is_pass = not bpy.context.scene.hide_attr_of_group
        if node.type == "GROUP" and node.node_tree and is_pass:
            if show_unused or is_node_linked(node):
                attributes.update(get_attributes(node.node_tree))
        if node.bl_idname in ['GeometryNodeInputNamedAttribute', 'GeometryNodeStoreNamedAttribute']:
            if show_unused or is_node_linked(node):
                data_type = node.data_type
                if data_type == "BYTE_COLOR":
                    data_type = "FLOAT_COLOR"
                if data_type == "FLOAT2":
                    data_type = "FLOAT_VECTOR"
                n_input = node.inputs["Name"]
                socket_name = n_input.default_value
                if socket_name and not n_input.is_linked:   # n_input.links
                    attributes[socket_name] = data_type
                if n_input.is_linked:
                    for link in links:
                        to_node = link.to_node; from_node = link.from_node
                        if to_node.name == node.name and from_node.bl_idname == 'FunctionNodeInputString':
                            attributes[from_node.string] = data_type
    # print(attributes)
    """ # # 第二种
    # context = bpy.context
    # box = context.evaluated_depsgraph_get()
    # obj = context.object.evaluated_get(box)
    # attrs = obj.data.attributes
    # exclude_list = ["position", "sharp_face", "material_index", "id",
    #                 ".edge_verts", ".corner_vert", ".corner_edge", 
    #                 ".select_vert", ".select_edge", ".select_poly",
    #                 ".sculpt_face_set",
    #                 ]
    # for attr in attrs:
    #     if attr.name in exclude_list:
    #         continue
    #     data_type = attr.data_type
    #     if data_type == "BYTE_COLOR":
    #         data_type = "FLOAT_COLOR"
    #     if data_type == "FLOAT2":
    #         data_type = "FLOAT_VECTOR"
    #     attributes[attr.name] = data_type """
    
    return attributes

def custom_sort(attrs, sort_types):
    sorted_list = []
    for value in sort_types:
        for key in attrs.keys():
            if attrs[key] == value:
                sorted_list.append((key, value))
    attrs = {k: v for k, v in sorted_list}
    return attrs

def menu_text_icon_sort(layout, context):
    scene = context.scene
    a_object = context.active_object
    sort_types1 = [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]
    sort_types2 = [ 'INT', 'BOOLEAN', 'FLOAT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]
    # todo 合理解决这个
    # tree = context.space_data.edit_tree
    tree = context.active_object.modifiers.active.node_group
    if context.area.ui_type == 'ShaderNodeTree':
        tree = context.active_object.modifiers.active.node_group
    show_unused = not context.scene.only_show_used_attr
    attrs = get_attributes(tree, show_unused)

    if scene.sna_show_vertex_group:
        for v_g in a_object.vertex_groups:
            attrs[v_g.name] = 'FLOAT'
    if scene.sna_show_uv_map:
        for uv in a_object.data.uv_layers:
            attrs[uv.name] = 'FLOAT_VECTOR'
    if scene.sna_show_color_attr:
        for color in a_object.data.color_attributes:
            attrs[color.name] = 'FLOAT_COLOR'

    attrs = {k: attrs[k] for k in sorted(attrs)}
    if scene.sna_sort_list == '按类型排序1':
        attrs = custom_sort(attrs, sort_types1)
    if scene.sna_sort_list == '按类型排序1-反转':
        sort_types = reversed(sort_types1)
        attrs = custom_sort(attrs, sort_types)
    if scene.sna_sort_list == '按类型排序2':
        attrs = custom_sort(attrs, sort_types2)
    # if scene.sna_sort_list == '完全按字符串排序':
    #     attrs = attrs
    for attr_name, attr_type in attrs.items():
        ui_type = context.area.ui_type
        if ui_type == 'ShaderNodeTree' and attr_type not in shader_date_types:
            continue
        op = layout.operator('sna.add_node_change_name_and_type', text=str(attr_name),
                                    icon_value=(_icons[data_with_png[attr_type]].icon_id ) )
        
        op.sna_attr_name = attr_name
        op.sna_attr_type = attr_type

classes = [
    ATTRLIST_OT_Add_Node_Change_Name_Type_Hide,
    ATTRLIST_MT_Menu,
    ATTRLIST_PT_NPanel,
    ATTRLIST_AddonPreferences,
    # ATTRLIST_PT_Add_Settings,
    # ATTRLIST_PT_Show_Settings,
]
def register():
    global _icons
    _icons = bpy.utils.previews.new()
    s = bpy.types.Scene
    p = bpy.props
    bpy.types.NODE_MT_editor_menus.append(sna_add_to_attr_list_mt_editor_menus)
    s.sna_hide_option        = p.BoolProperty(name='hide_option',        description='添加时是否隐藏选项',         default=True)
    s.sna_hide_Exists_socket = p.BoolProperty(name='hide_Exists_socket', description='添加时是否隐藏输出接口存在',     default=True)
    s.sna_hide_Name_socket   = p.BoolProperty(name='hide_Name_socket',   description='添加时是否隐藏输入接口名称',     default=False)
    s.sna_rename_Attr_socket = p.BoolProperty(name='rename_Attr_socket', description='添加时是否命名输出接口属性',     default=True)
    s.sna_hide_Node          = p.BoolProperty(name='hide_Node',          description='添加时是否折叠节点',         default=False)
    s.sna_rename_Node        = p.BoolProperty(name='rename_Node',        description='添加时是否重命名节点',        default=False)
    s.only_show_used_attr    = p.BoolProperty(name='only_show_used_attr',description='只显示用到的属性,连了线的属性节点',  default=True)
    s.hide_attr_of_group     = p.BoolProperty(name='hide_attr_of_group', description='隐藏节点组里的属性',  default=False)
    s.add_settings           = p.BoolProperty(name='添加节点选项',      description='',  default=False)
    s.show_settings          = p.BoolProperty(name='列表显示选项',      description='',  default=True)
    s.panel_info             = p.StringProperty(name='显示在面板上的描述', description='显示在面板上的描述',  default="aaa")
    
    s.sna_show_vertex_group  = p.BoolProperty(name='Show_Vertex_Group',  description='是否在属性列表里显示顶点组',      default=True)
    s.sna_show_uv_map        = p.BoolProperty(name='Show_UV_Map',        description='是否在属性列表里显示UV贴图',     default=False)
    s.sna_show_color_attr    = p.BoolProperty(name='Show_Color_Attr',    description='是否在属性列表里显示颜色属性',     default=False)
    s.sna_sort_list          = p.EnumProperty(name='列表排序方式',        description='属性列表多种排序方式', 
                                                 items=[('按类型排序1', '按类型排序1', '布尔-浮点-整数-矢量-颜色-旋转', 0, 0), 
                                                        ('按类型排序1-反转', '按类型排序1-反转', '旋转-颜色-矢量-整数-浮点-布尔', 0, 1), 
                                                        ('按类型排序2', '按类型排序2', '整数-布尔-浮点-矢量-颜色-旋转', 0, 2), 
                                                        ('完全按字符串排序', '完全按字符串排序', '首字-数字英文中文', 0, 3)])
    for cla in classes:
        bpy.utils.register_class(cla)
    for png in png_list: 
        _icons.load(png, os.path.join(os.path.dirname(__file__), 'icons', png), "IMAGE")
    
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    
    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'ATTRLIST_MT_Menu'
    addon_keymaps['唤出菜单快捷键'] = (km, kmi)
    
    kmi = km.keymap_items.new('wm.call_panel', 'TWO', 'PRESS', ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'ATTRLIST_PT_NPanel'
    kmi.properties.keep_open = True
    addon_keymaps['ATTRLIST_PT_NPanel'] = (km, kmi)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    del bpy.types.Scene.sna_hide_option
    del bpy.types.Scene.sna_hide_Exists_socket
    del bpy.types.Scene.sna_hide_Name_socket
    del bpy.types.Scene.sna_rename_Attr_socket
    del bpy.types.Scene.sna_hide_Node
    del bpy.types.Scene.sna_rename_Node
    del bpy.types.Scene.only_show_used_attr
    del bpy.types.Scene.hide_attr_of_group
    del bpy.types.Scene.add_settings
    del bpy.types.Scene.show_settings
    del bpy.types.Scene.panel_info
    del bpy.types.Scene.sna_show_vertex_group
    del bpy.types.Scene.sna_show_uv_map
    del bpy.types.Scene.sna_show_color_attr
    del bpy.types.Scene.sna_sort_list
    
    bpy.types.NODE_MT_editor_menus.remove(sna_add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)

