bl_info = {
    "name" : "小王-命名属性列表",
    "author" : "Your Name", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 2, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}


import bpy
import bpy.utils.previews
import time
import os


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


def sna_add_to_node_mt_editor_menus_38B6B(self, context):
    if not (False):
        layout = self.layout
        layout.menu('SNA_MT_32345', text='属性', icon_value=0)


class SNA_MT_32345(bpy.types.Menu):
    bl_idname = "SNA_MT_32345"
    bl_label = "命名属性列表菜单"

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = "INVOKE_DEFAULT"
        layout_function = layout
        sna_func_CE60A(layout_function, )


class SNA_OT_My_Generic_Operator_83155(bpy.types.Operator):
    bl_idname = "sna.my_generic_operator_83155"
    bl_label = "属性隐藏选项"
    bl_description = "快捷键Shift 2 "
    bl_options = {"REGISTER", "UNDO"}
    sna_new_property: bpy.props.IntProperty(name='New Property', description='', default=0, subtype='NONE')

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        bpy.ops.node.add_node('INVOKE_DEFAULT', use_transform=True, type='GeometryNodeInputNamedAttribute')
        Variable = self.sna_new_property
        is_hide_option = bpy.context.scene.sna_is_hide
        print(Variable)       # 变量属性名
        attribute_node = context.active_node
        #attribute_node.data_type = data_type
        #attribute_node.inputs["Name"].default_value = attribute_name
        if is_hide_option:
            attribute_node.show_options = False
        context.active_node.outputs["Exists"].hide = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_AddonPreferences_97A0C(bpy.types.AddonPreferences):
    bl_idname = 'addon_59776'

    def draw(self, context):
        if not (False):
            layout = self.layout 
            layout.label(text='标题栏和N面板显示属性列表', icon_value=24)
            layout.prop(find_user_keyconfig('D0D59'), 'type', text='显示命名属性列表', full_event=True)


class SNA_PT__CC787(bpy.types.Panel):
    bl_label = '命名属性列表'
    bl_idname = 'SNA_PT__CC787'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Node'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        split_0DA57 = layout.split(factor=0.6000000238418579, align=True)
        split_0DA57.alert = False
        split_0DA57.enabled = True
        split_0DA57.active = True
        split_0DA57.use_property_split = False
        split_0DA57.use_property_decorate = False
        split_0DA57.scale_x = 1.0
        split_0DA57.scale_y = 1.0
        split_0DA57.alignment = 'Right'.upper()
        if not True: split_0DA57.operator_context = "EXEC_DEFAULT"
        split_AD291 = split_0DA57.split(factor=0.30000001192092896, align=True)
        split_AD291.alert = False
        split_AD291.enabled = True
        split_AD291.active = True
        split_AD291.use_property_split = False
        split_AD291.use_property_decorate = False
        split_AD291.scale_x = 1.0
        split_AD291.scale_y = 1.0
        split_AD291.alignment = 'Right'.upper()
        if not True: split_AD291.operator_context = "EXEC_DEFAULT"
        split_AD291.label(text='快捷键:', icon_value=0)
        split_AD291.prop(find_user_keyconfig('D0D59'), 'type', text='', full_event=True)
        split_0DA57.prop(bpy.context.scene, 'sna_is_hide', text='是否隐藏选项', icon_value=0, emboss=True)
        layout_function = layout
        sna_func_CE60A(layout_function, )


def sna_func_CE60A(layout_function, ):
    for i_5DFC1 in range(len(bpy.context.area.spaces[0].node_tree.inputs)):
        op = layout_function.operator('sna.my_generic_operator_83155', text=str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]), icon_value=(_icons['域-旋转.png'].icon_id if '旋转' in str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]) else (_icons['域-颜色.png'].icon_id if '颜色' in str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]) else (_icons['域-矢量.png'].icon_id if '矢量' in str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]) else (_icons['域-整数.png'].icon_id if '浮点' in str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]) else (_icons['域-浮点.png'].icon_id if '布尔' in str(bpy.context.area.spaces[0].node_tree.inputs[i_5DFC1]) else _icons['域-布尔.png'].icon_id))))), emboss=True, depress=False)
        op.sna_new_property = i_5DFC1


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.Scene.sna_is_hide = bpy.props.BoolProperty(name='is_hide', description='是否添加隐藏接口选项的', default=True)
    bpy.types.NODE_MT_editor_menus.append(sna_add_to_node_mt_editor_menus_38B6B)
    bpy.utils.register_class(SNA_MT_32345)
    bpy.utils.register_class(SNA_OT_My_Generic_Operator_83155)
    bpy.utils.register_class(SNA_AddonPreferences_97A0C)
    bpy.utils.register_class(SNA_PT__CC787)
    if not '域-旋转.png' in _icons: _icons.load('域-旋转.png', os.path.join(os.path.dirname(__file__), 'icons', '域-旋转.png'), "IMAGE")
    if not '域-颜色.png' in _icons: _icons.load('域-颜色.png', os.path.join(os.path.dirname(__file__), 'icons', '域-颜色.png'), "IMAGE")
    if not '域-矢量.png' in _icons: _icons.load('域-矢量.png', os.path.join(os.path.dirname(__file__), 'icons', '域-矢量.png'), "IMAGE")
    if not '域-整数.png' in _icons: _icons.load('域-整数.png', os.path.join(os.path.dirname(__file__), 'icons', '域-整数.png'), "IMAGE")
    if not '域-布尔.png' in _icons: _icons.load('域-布尔.png', os.path.join(os.path.dirname(__file__), 'icons', '域-布尔.png'), "IMAGE")
    if not '域-浮点.png' in _icons: _icons.load('域-浮点.png', os.path.join(os.path.dirname(__file__), 'icons', '域-浮点.png'), "IMAGE")
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'PRESS',
        ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'SNA_MT_32345'
    addon_keymaps['D0D59'] = (km, kmi)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.sna_is_hide
    bpy.types.NODE_MT_editor_menus.remove(sna_add_to_node_mt_editor_menus_38B6B)
    bpy.utils.unregister_class(SNA_MT_32345)
    bpy.utils.unregister_class(SNA_OT_My_Generic_Operator_83155)
    bpy.utils.unregister_class(SNA_AddonPreferences_97A0C)
    bpy.utils.unregister_class(SNA_PT__CC787)
