import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import Operator, AddonPreferences
from bpy.app.handlers import persistent

bl_info = {
    "name" : "小王-节点叠加层预览属性",
    "author" : "一尘不染", 
    "description" : "节点叠加层预览属性",
    "blender" : (3, 0, 0),
    "version" : (4, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Node" 
}


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

def pref():
    return bpy.context.preferences.addons[__name__].preferences

def get_view3d_overlays():
    return [area.spaces[0].overlay for area in bpy.context.screen.areas if area.type == "VIEW_3D"]

def update_show_attr_text(self, context):
    for overlay in get_view3d_overlays():
        if hasattr(overlay, 'show_viewer_text'):
            overlay.show_viewer_text = self.show_attr_text

def update_show_attr_color(self, context):
    for overlay in get_view3d_overlays():
        overlay.show_viewer_attribute = self.show_attr_color

def update_view_attr_opacity(self, context):
    for overlay in get_view3d_overlays():
        overlay.viewer_attribute_opacity = self.view_attr_opacity

class Attr_Text_AddonPrefs(AddonPreferences):
    bl_idname = __name__
    show_attr_text    : BoolProperty(name='show_attr_text',     default=False, update=update_show_attr_text)
    show_attr_color   : BoolProperty(name='show_attr_color',    default=False, update=update_show_attr_color)
    view_attr_opacity : FloatProperty(name='view_attr_opacity', default=1,     update=update_view_attr_opacity,
                                                        subtype='FACTOR', min=0, max=1, precision=1)
    def draw(self, context):
        layout = self.layout 
        split = layout.split(factor=0.4, align=False)
        split.label(text='预览文本', icon_value=0)
        split.prop(find_user_keyconfig('预览文本'), 'type', text='', full_event=True)

        split = layout.split(factor=0.4, align=False)
        split.label(text='预览透明度', icon_value=0)
        split.prop(find_user_keyconfig('预览透明度'), 'type', text='', full_event=True)

class NODE_OT_show_attr_text(Operator):
    bl_idname = "node.show_attr_text"
    bl_label = "小王-预览属性为文本"             # 显示在设置快捷键时的文本
    bl_description = "预览属性为文本"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        pref().show_attr_text = False if pref().show_attr_text else True
        return {"FINISHED"}

class NODE_OT_show_attr_color(Operator):
    bl_idname = "node.show_attr_color"
    bl_label = "小王-预览属性颜色"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        pref().show_attr_color = False if pref().show_attr_color else True
        return {"FINISHED"}

def draw_show_view_attr_text(self, context):
    if context.area.ui_type == "GeometryNodeTree":
        layout = self.layout
        for overlay in get_view3d_overlays():
            if hasattr(overlay, 'show_viewer_text'):
                theme = context.preferences.themes['Default']
                split1 = layout.split(factor=0.6, align=False)
                split1.prop(pref(), 'show_attr_text', text='预览文字')
                split1.prop(theme.view_3d.space, 'text_hi', text='')
                
                split2 = layout.split(factor=0.08, align=False)
                split2.prop(pref(), 'show_attr_color', text='')
                split2.prop(pref(), 'view_attr_opacity', text='预览透明度', emboss=pref().show_attr_color)
                
                if hasattr(theme.node_editor, "overlay_text_size"):
                    layout.prop(theme.node_editor, 'overlay_text_size', text='预览文本大小')
                else:
                    layout.prop(context.preferences.ui_styles[0].widget, 'points', text='预览文本大小')
                if hasattr(theme.node_editor, "overlay_text_decimals"):
                    layout.prop(theme.node_editor, 'overlay_text_decimals', text='预览小数位数')
                # bpy.context.preferences.themes['Default'].view_3d.space.header_text_hi

# ! 问题是: 新建文件时:预览文本是False,但是show_attr_text是True

@persistent
def load_post_handler(dummy):
    prefs = pref()
    # if not prefs.show_attr_text:
    #     prefs.show_attr_text = True
    #     prefs.show_attr_text = False
    # if prefs.show_attr_color:
    #     prefs.show_attr_color = False
    #     prefs.show_attr_color = True
    # if not prefs.show_attr_color:
    #     prefs.show_attr_color = True
    #     prefs.show_attr_color = False

classes =[
    Attr_Text_AddonPrefs,
    NODE_OT_show_attr_text,
    NODE_OT_show_attr_color
]

def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new('node.show_attr_text', 'THREE', 'PRESS', ctrl=True, alt=False, shift=False, repeat=True)
    addon_keymaps['预览文本'] = (km, kmi)

    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new('node.show_attr_color', 'THREE', 'PRESS', ctrl=False, alt=False, shift=True, repeat=True)
    addon_keymaps['预览透明度'] = (km, kmi)

    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.NODE_PT_overlay.append(draw_show_view_attr_text)
    bpy.app.handlers.load_post.append(load_post_handler)

def unregister():
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    for i in classes:
        bpy.utils.unregister_class(i)
    bpy.types.NODE_PT_overlay.remove(draw_show_view_attr_text)
    bpy.app.handlers.load_post.remove(load_post_handler)


