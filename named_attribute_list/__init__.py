from pprint import pprint
import bpy
import bpy.utils.previews
import os

bl_info = {
    "name" : "小王-几何节点命名属性列表",
    "author" : "小王", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 5, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}

# todo 重命名属性接口移过来 (小王-批量重命名节点和属性节点接口.py)

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

def add_to_attr_list_mt_editor_menus(self, context):
    if context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree']:
        layout = self.layout
        layout.menu('ATTRLIST_MT_Menu', text='属性', icon_value=0)

class ATTRLIST_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = 'addon_59776'

    def draw(self, context):
        layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
        
        if True:
            layout = self.layout 
            layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
            layout.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='显示命名属性列表', full_event=True)

class ATTRLIST_MT_Menu(bpy.types.Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = "小王-命名属性列表菜单"

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        sort_attrs_and_draw_menu(layout, context)

class ATTRLIST_OT_Add_Node_Change_Name_Type_Hide(bpy.types.Operator):
    bl_idname = "sna.add_node_change_name_and_type"
    bl_label = "属性隐藏选项"
    # bl_description = "快捷键Shift 2 "
    bl_options = {"REGISTER", "UNDO"}
    attr_name:  bpy.props.StringProperty(name='attr_name', description='', default="", subtype='NONE')
    attr_type:  bpy.props.StringProperty(name='attr_type', description='', default="", subtype='NONE')

    bl_description: bpy.props.StringProperty(default="快捷键Shift 2 ", options={"HIDDEN"})

    @classmethod
    def description(cls, context, props):
        if props:
            return props.bl_description

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        data_type = self.attr_type
        scene = context.scene
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            scene.panel_info = "添加已命名属性节点"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = self.attr_name
            attr_node.inputs["Name"].hide = scene.hide_Name_socket
            attr_node.show_options = not scene.hide_option
            if scene.rename_Attr_socket:
                if bpy.data.version >= (4, 1, 0):
                    attr_node.outputs["Attribute"].name = self.attr_name        # socket的identifier也是Attribute  socket[identifier] 优先
                else:
                    for socket in attr_node.outputs:        # 因为之前版本,已命名属性节点有多个Attribute输出接口
                        if socket.enabled and not socket.hide and socket.name=="Attribute":
                            socket.name = self.attr_name
            attr_node.outputs["Exists"].hide = scene.hide_Exists_socket

        if ui_type == 'ShaderNodeTree':
            scene.panel_info = "添加属性节点"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='ShaderNodeAttribute')
            # [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR']
            attr_node = context.active_node
            attr_node.attribute_name = self.attr_name
            attr_node.show_options = not scene.hide_Name_socket
            socket_order = { 'BOOLEAN'     : 2,
                             'FLOAT'       : 2,
                             'INT'         : 2,
                             'FLOAT_VECTOR': 1,
                             'FLOAT_COLOR' : 0,
                            }
            for i, out_soc in enumerate(attr_node.outputs):
                order = socket_order[data_type]
                if i == order:
                    out_soc.name = self.attr_name
                if i != order:
                    out_soc.hide = True
        
        if scene.rename_Node:
            attr_node.label = self.attr_name
        attr_node.hide = scene.hide_Node
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class ATTRLIST_PT_NPanel(bpy.types.Panel):
    bl_label = '小王-命名属性列表面板'      # 还作为在快捷键列表里名称
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
        
        a_node = context.active_node
        if a_node.bl_idname == "GeometryNodeObjectInfo" and a_node.select:
            obj_name = a_node.inputs[0].default_value.name
            info = obj_name + "的属性"
            # info = a_node.name
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            info = "活动物体及节点树属性"
            layout.label(text=info, icon='GEOMETRY_NODES')
        if ui_type == 'ShaderNodeTree':
            info = "活动物体属性"
            layout.label(text=info, icon='MATERIAL_DATA')

        arrow_show = "TRIA_RIGHT" if not scene.add_settings else "TRIA_DOWN"
        box1 = layout.box()
        box1.scale_y = 0.9
        box1.prop(scene, "add_settings", emboss=True, icon=arrow_show)
        if scene.add_settings:
            box1.label(text="已知限制: 无", icon='INFO')
            split = box1.split(factor=0.5)
            split.label(text='菜单快捷键 :')
            split.prop(find_user_keyconfig('唤出菜单快捷键'), 'type', text='', full_event=True)
            
            split = box1.split(factor=0.5)
            split.label(text='面板快捷键 :')
            split.prop(find_user_keyconfig('ATTRLIST_PT_NPanel'), 'type', text='', full_event=True)

            split = box1.split(factor=0.5)
            split.prop(scene, 'hide_option',        toggle=True, text='隐藏节点选项')
            split.prop(scene, 'hide_Exists_socket', toggle=True, text='隐藏存在接口')
            split = box1.split(factor=0.5)
            split.prop(scene, 'hide_Name_socket',   toggle=True, text='隐藏名称接口')
            split.prop(scene, 'rename_Attr_socket', toggle=True, text='重命名属性接口')
            split = box1.split(factor=0.5)
            split.prop(scene, 'hide_Node',          toggle=True, text='折叠节点')
            split.prop(scene, 'rename_Node',        toggle=True, text='重命名节点标签')
        
        arrow_add = "TRIA_RIGHT" if not scene.show_settings else "TRIA_DOWN"
        box2 = layout.box()
        box2.scale_y = 0.9
        box2.prop(scene, "show_settings", emboss=True, icon=arrow_add)
        if scene.show_settings:
            split2 = box2.split(factor=0.4)
            split2.label(text='列表排序方式')
            split2.prop(scene, 'sort_list', text='')
            
            box2.label(text='属性列表里是否显示')
            split3 = box2.split(factor=0.05)
            split3.label(text="")
            split31 = split3.split(factor=0.35)
            split31.prop(scene, 'show_vertex_group', toggle=True, text='顶点组')
            split32 = split31.split(factor=0.4)
            split32.prop(scene, 'show_uv_map',       toggle=True, text='UV')
            split32.prop(scene, 'show_color_attr',   toggle=True, text='颜色属性')
            
            box2.label(text='属性列表里是否隐藏')
            split4 = box2.split(factor=0.05)
            split4.label(text="")
            split41 = split4.split(factor=0.5)
            split41.prop(scene, 'only_show_used_attr', toggle=True, text='未使用属性')
            split41.prop(scene, 'hide_attr_of_group',  toggle=True, text='节点组内属性')
        
        box3 = layout.box()
        sort_attrs_and_draw_menu(box3, context)


def is_node_linked(node):
    soc_out = node.outputs
    if len(soc_out):
        for soc in soc_out:
            if soc.is_linked:
                return True
    return False

def get_attrs_dict(tree, show_unused=True):
    # show_unused=False的话，接下来判断is_node_linked
    # print("tree", tree)
    # print("tree.name", tree.name)
    # print(tree.nodes)
    context = bpy.context
    nodes = tree.nodes
    links = tree.links
    attrs_dict = {}         # {attr_name_str: data_type_str}
    # # 第一种
    data_dict = {   "BYTE_COLOR": "FLOAT_COLOR",
                    "FLOAT2": "FLOAT_VECTOR"}
    for node in nodes:
        is_pass = not context.scene.hide_attr_of_group
        if node.type == "GROUP" and node.node_tree and is_pass:
            if show_unused or is_node_linked(node):
                attrs_dict.update(get_attrs_dict(node.node_tree))
        if node.bl_idname in ['GeometryNodeInputNamedAttribute', 'GeometryNodeStoreNamedAttribute']:
            if show_unused or is_node_linked(node):
                data_type = node.data_type
                if data_type in data_dict:
                    data_type = data_dict[data_type]
                n_input = node.inputs["Name"]
                attr_name = n_input.default_value
                if attr_name and not n_input.is_linked:   # n_input.links
                    attrs_dict[attr_name] = data_type
                if n_input.is_linked:
                    for link in links:
                        to_node = link.to_node; from_node = link.from_node
                        if to_node.name == node.name and from_node.bl_idname == 'FunctionNodeInputString':
                            attrs_dict[from_node.string] = data_type            # from_node.string获取的字符串输入节点的字符串值
    # 第二种
    box = context.evaluated_depsgraph_get()
    obj = context.object.evaluated_get(box)
    attrs = obj.data.attributes
    exclude_list = ["position", "sharp_face", "material_index",              # "id",
                    ".edge_verts", ".corner_vert", ".corner_edge", 
                    ".select_vert", ".select_edge", ".select_poly",
                    ".sculpt_face_set",
                    ]
    for attr in attrs:
        if attr.name in exclude_list:
            continue
        data_type = attr.data_type
        if data_type in data_dict:
            data_type = data_dict[data_type]
        attrs_dict[attr.name] = data_type
    
    return attrs_dict

def custom_sort(attrs, sort_types):
    sorted_list = []
    for value in sort_types:
        for key in attrs.keys():
            if attrs[key] == value:
                sorted_list.append((key, value))
    attrs = {k: v for k, v in sorted_list}
    return attrs

def sort_attrs_and_draw_menu(layout, context):
    scene = context.scene
    a_object = context.active_object
    sort_types1 = [ 'BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]
    sort_types2 = [ 'INT', 'BOOLEAN', 'FLOAT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION' ]

    # tree = context.space_data.edit_tree
    
    # tree = context.active_object.modifiers.active.node_group
    
    # GeometryNodeTree 里 context.space_data.id 是 bpy.data.materials["Material"]
    # ShaderNodeTree   里 context.space_data.id 是 bpy.data.materials["Material"]
    ui_type = context.area.ui_type
    if ui_type == 'GeometryNodeTree':
        tree = context.space_data.id.modifiers.active.node_group
    if ui_type == 'ShaderNodeTree':
        tree = context.active_object.modifiers.active.node_group
    show_unused = not context.scene.only_show_used_attr
    attrs = get_attrs_dict(tree, show_unused)
    # from pprint import pprint
    # pprint("-" * 30)
    # print(context.space_data.id)
    # context.area.spaces.active.path[-1].node_tree
    # context.space_data.edit_tree
    # pprint(attrs)
    if scene.show_vertex_group:
        for v_g in a_object.vertex_groups:
            attrs[v_g.name] = 'FLOAT'
    if scene.show_uv_map:
        for uv in a_object.data.uv_layers:
            attrs[uv.name] = 'FLOAT_VECTOR'
    if scene.show_color_attr:
        for color in a_object.data.color_attributes:
            attrs[color.name] = 'FLOAT_COLOR'

    attrs = {k: attrs[k] for k in sorted(attrs)}
    # if scene.sort_list == '按类型排序1':
    #     attrs = custom_sort(attrs, sort_types1)
    # if scene.sort_list == '按类型排序1-反转':
    #     sort_types = reversed(sort_types1)
    #     attrs = custom_sort(attrs, sort_types)
    # if scene.sort_list == '按类型排序2':
    #     attrs = custom_sort(attrs, sort_types2)
    # if scene.sort_list == '完全按字符串排序':
    #     attrs = attrs
    for attr_name, attr_type in attrs.items():
        ui_type = context.area.ui_type
        if attr_type not in data_types:
            continue
        if ui_type == 'ShaderNodeTree' and attr_type not in shader_date_types:
            continue
        op = layout.operator('sna.add_node_change_name_and_type', text=str(attr_name),
                                    icon_value=(_icons[data_with_png[attr_type]].icon_id ) )
        op.attr_name = attr_name
        op.attr_type = attr_type
        op.bl_description = attr_name
        
        # from pprint import pprint
        # print("*-+" * 30)
        # print(type(op))     # <class 'bpy.types.NODE_PIE_OT_add_node'>
        # pprint("dict(op)")
        # pprint(dict(op))
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
    bpy.types.NODE_MT_editor_menus.append(add_to_attr_list_mt_editor_menus)
    s.hide_option        = p.BoolProperty(name='hide_option',        description='添加时是否隐藏选项',         default=True)
    s.hide_Exists_socket = p.BoolProperty(name='hide_Exists_socket', description='添加时是否隐藏输出接口存在',     default=True)
    s.hide_Name_socket   = p.BoolProperty(name='hide_Name_socket',   description='添加时是否隐藏输入接口名称',     default=False)
    s.rename_Attr_socket = p.BoolProperty(name='rename_Attr_socket', description='添加时是否命名输出接口属性',     default=True)
    s.hide_Node          = p.BoolProperty(name='hide_Node',          description='添加时是否折叠节点',         default=False)
    s.rename_Node        = p.BoolProperty(name='rename_Node',        description='添加时是否重命名节点',        default=False)
    s.only_show_used_attr    = p.BoolProperty(name='only_show_used_attr',description='只显示用到的属性,连了线的属性节点',  default=True)
    s.hide_attr_of_group     = p.BoolProperty(name='hide_attr_of_group', description='隐藏节点组里的属性',  default=False)
    s.add_settings           = p.BoolProperty(name='添加节点选项',      description='',  default=False)
    s.show_settings          = p.BoolProperty(name='列表显示选项',      description='',  default=True)
    s.panel_info             = p.StringProperty(name='显示在面板上的描述', description='显示在面板上的描述',  default="aaa")
    
    s.show_vertex_group  = p.BoolProperty(name='Show_Vertex_Group',  description='是否在属性列表里显示顶点组',      default=True)
    s.show_uv_map        = p.BoolProperty(name='Show_UV_Map',        description='是否在属性列表里显示UV贴图',     default=False)
    s.show_color_attr    = p.BoolProperty(name='Show_Color_Attr',    description='是否在属性列表里显示颜色属性',     default=False)
    s.sort_list          = p.EnumProperty(name='列表排序方式',        description='属性列表多种排序方式', 
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
    
    del bpy.types.Scene.hide_option
    del bpy.types.Scene.hide_Exists_socket
    del bpy.types.Scene.hide_Name_socket
    del bpy.types.Scene.rename_Attr_socket
    del bpy.types.Scene.hide_Node
    del bpy.types.Scene.rename_Node
    del bpy.types.Scene.only_show_used_attr
    del bpy.types.Scene.hide_attr_of_group
    del bpy.types.Scene.add_settings
    del bpy.types.Scene.show_settings
    del bpy.types.Scene.panel_info
    del bpy.types.Scene.show_vertex_group
    del bpy.types.Scene.show_uv_map
    del bpy.types.Scene.show_color_attr
    del bpy.types.Scene.sort_list
    
    bpy.types.NODE_MT_editor_menus.remove(add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)

