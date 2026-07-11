import bpy, os
import bpy.utils.previews

from .constants import png_list
from .preferences import ATTRLIST_AddonPrefs
from .operators import AL_OT_add_node_from_list, NODE_OT_View_Stored_Attribute_Node, NODE_OT_Add_Named_Attribute
from .ui import ATTRLIST_MT_SubMenu, ATTRLIST_MT_Menu, ATTRLIST_PT_NPanel, submenu_classes
from .utils import add_to_attr_list_mt_editor_menus

addon_keymaps = {}
_icons = None

classes = [
    AL_OT_add_node_from_list,
    ATTRLIST_MT_SubMenu,
    ATTRLIST_MT_Menu,
    ATTRLIST_PT_NPanel,
    ATTRLIST_AddonPrefs,
    NODE_OT_View_Stored_Attribute_Node,
    NODE_OT_Add_Named_Attribute,
] + submenu_classes

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.NODE_MT_editor_menus.append(add_to_attr_list_mt_editor_menus)

    for cla in classes:
        bpy.utils.register_class(cla)

    for png in png_list:
        _icons.load(png, os.path.join(os.path.dirname(__file__), 'icons', png), "IMAGE")

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'PRESS', ctrl=False, alt=False, shift=False, repeat=False)
    kmi.properties.name = 'ATTRLIST_MT_Menu'
    addon_keymaps['命名属性菜单快捷键'] = (km, kmi)

    kmi = km.keymap_items.new('wm.call_panel', 'TWO', 'PRESS', ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'ATTRLIST_PT_NPanel'
    kmi.properties.keep_open = True
    addon_keymaps['命名属性面板快捷键'] = (km, kmi)

    kmi = km.keymap_items.new('node.add_named_attribute_node', 'TWO', 'PRESS', ctrl=True, alt=False, shift=False, repeat=False)
    addon_keymaps['添加存储节点对应属性节点'] = (km, kmi)

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.types.NODE_MT_editor_menus.remove(add_to_attr_list_mt_editor_menus)
    for cla in classes:
        bpy.utils.unregister_class(cla)
