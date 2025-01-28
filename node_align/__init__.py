import os
import bpy
from bpy.props import BoolProperty, IntProperty
from bpy.types import AddonPreferences, Menu
from .op_align import *
from .translator import i18n as tr
# TODO 对齐Frame
# TODO 把我的 Alt+1 加上 Shift+x Shift+y
# TODO 根据左上角和右下角画格子,节点落在最近的的格子里
# TODO 自定义栅格分布判断列的间距(或者根据节点密度/数量自动判断)

bl_info = {
    "name" : "小王-Node Align",
    "author" : "一尘不染",
    "description" : "align node  Shift Q | Ctrl Q",
    "blender" : (2, 83, 0),
    "version" : (3, 0, 2),
    "location": "Nodes Editor",
    "category": "Node"
}

addon_keymaps = {}
_icons = None
# 按顺序可以换成自定义图片图标
images = [
    '左对齐-蓝双色',
    '右对齐-蓝双色',
    '下对齐-蓝双色',
    '上对齐-蓝双色',
    '上下居中对齐-蓝双色',
    '垂直等距分布-蓝双色',
    '左右居中对齐-蓝双色',
    '水平等距分布-蓝双色',
    '网格-绿方块',
    '网格-蓝方块',
    '网格-蓝线框',
    '直线-橙色虚线',
    '水平等距分布-蓝橙',
    '垂直等距分布-蓝橙',
]
images = [image + ".png" for image in images]

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

class Node_Align_AddonPrefs(AddonPreferences):
    bl_idname = __package__
    is_custom_space: BoolProperty(name="is_custom_space", default=False, description=tr("是否为等距及栅格分布启用自定义间距"))
    space_x  : IntProperty(name="space_x",   default=40,  description=tr("等距及栅格分布时的节点x方向间距"))
    space_y  : IntProperty(name="space_y",   default=40,  description=tr("等距及栅格分布时的节点y方向间距"))
    col_width: IntProperty(name="col_width", default=140, description=tr("栅格分布时判断是否在一列的宽度"))

    def draw(self, context):
        layout = self.layout
        layout = self.layout
        split = layout.split(factor=0.5)
        split.label(text=tr("普通对齐饼菜单"))
        split.prop(find_user_keyconfig('ALIGN_MT_align_pie'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text=tr("高级对齐饼菜单"))
        split.prop(find_user_keyconfig('ALIGN_MT_align_pie_pro'), 'type', text='', full_event=True)

        split = layout.split(factor=0.75)
        split.label(text=tr("栅格分布时判断是否在一列的宽度"))
        split.prop(self, 'col_width', text='')

        split = layout.split(factor=0.75)
        split.label(text=tr("等距及栅格分布启用自定义间距"))
        split.prop(self, 'is_custom_space', text='')

        split = layout.split(factor=0.75)
        split.label(text=tr("等距及栅格分布时的节点x方向间距"))
        split.prop(self, 'space_x', text='')

        split = layout.split(factor=0.75)
        split.label(text=tr("等距及栅格分布时的节点y方向间距"))
        split.prop(self, 'space_y', text='')

def draw_align_menu(layout):
    layout.operator("node.align_left",            text=tr("左对齐"),       icon_value=_icons[images[0]].icon_id)
    layout.operator("node.align_right",           text=tr("右对齐"),       icon_value=_icons[images[1]].icon_id)
    layout.operator("node.align_bottom",          text=tr("底对齐"),       icon_value=_icons[images[2]].icon_id)
    layout.operator("node.align_top",             text=tr("顶对齐"),       icon_value=_icons[images[3]].icon_id)
    layout.operator("node.align_height_center",   text=tr("对齐高度"),     icon_value=_icons[images[4]].icon_id)
    layout.operator("node.distribute_vertical",   text=tr("垂直等距分布"), icon_value=_icons[images[5]].icon_id)
    layout.operator("node.align_width_center",    text=tr("对齐宽度"),     icon_value=_icons[images[6]].icon_id)
    layout.operator("node.distribute_horizontal", text=tr("水平等距分布"), icon_value=_icons[images[7]].icon_id)

def draw_align_menu_pro(layout):
    # pie里默认出现顺序 左 右 底 顶 左上 右上 左下 右下
    layout.prop(pref(), "is_custom_space",                 text=tr("自定义分布间距"))
    layout.operator("node.distribute_horizontal_vertical", text=tr("水平垂直等距"), icon_value=_icons[images[10]].icon_id)
    layout.operator("node.distribute_row_column",    text=tr("改变行列数"), icon_value=_icons[images[10]].icon_id)
    layout.operator("node.align_link",               text=tr("拉直连线"),     icon_value=_icons[images[11]].icon_id)
    layout.operator("node.align_height_horizontal",  text=tr("等距对齐高度"), icon_value=_icons[images[13]].icon_id)
    layout.operator("node.distribute_grid_relative", text=tr("相对网格分布"), icon_value=_icons[images[8]].icon_id)
    layout.operator("node.align_width_vertical",     text=tr("等距对齐宽度"), icon_value=_icons[images[12]].icon_id)
    layout.operator("node.distribute_grid_absolute", text=tr("绝对网格分布"), icon_value=_icons[images[9]].icon_id)

class ALIGN_MT_align_pie(Menu):
    bl_idname = "ALIGN_MT_align_pie"
    bl_label = tr("节点对齐")

    def draw(self, context):
        pie = self.layout.menu_pie()     # 默认出现顺序 左 右 底 顶 左上 右上 左下 右下
        draw_align_menu(pie)

class ALIGN_MT_align_pie_pro(Menu):
    bl_idname = "ALIGN_MT_align_pie_pro"
    bl_label = tr("节点分布")

    def draw(self, context):
        pie = self.layout.menu_pie()     # 默认出现顺序 左 右 底 顶 左上 右上 左下 右下
        draw_align_menu_pro(pie)

class NODE_MT_align(Menu):
    bl_idname = "NODE_MT_align"
    bl_label = "右键菜单-对齐"

    @classmethod
    def poll(cls, context):
        return bool(context.selected_nodes)

    def draw(self, context):
        layout = self.layout
        draw_align_menu(layout)
        layout.separator()
        draw_align_menu_pro(layout)

def add_align_op_to_node_mt_context_menu(self, context):
    layout = self.layout
    layout.menu('NODE_MT_align', text=tr("节点对齐"), icon_value=_icons[images[9]].icon_id)

classes = [
    Node_Align_AddonPrefs,
    ALIGN_MT_align_pie,
    ALIGN_MT_align_pie_pro,
    NODE_MT_align,

    NODE_OT_align_bottom,
    NODE_OT_align_top,
    NODE_OT_align_right,
    NODE_OT_align_left,
    NODE_OT_align_heightcenter,
    NODE_OT_align_widthcenter,
    NODE_OT_distribute_horizontal,
    NODE_OT_distribute_vertical,
    NODE_OT_align_width_vertical,
    NODE_OT_align_height_horizontal,
    NODE_OT_distribute_horizontal_vertical,
    NODE_OT_distribute_row_column,
    NODE_OT_distribute_grid_relative,
    NODE_OT_distribute_grid_absolute,
    NODE_OT_align_link,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    for image in images:
        _icons.load(image, os.path.join(os.path.dirname(__file__), 'icons', image), "IMAGE")

    for cls in classes:
        bpy.utils.register_class(cls)

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new("wm.call_menu_pie", type="Q", value="PRESS", shift=True)
    kmi.properties.name = "ALIGN_MT_align_pie"
    addon_keymaps['ALIGN_MT_align_pie'] = (km, kmi)
    
    kmi = km.keymap_items.new("wm.call_menu_pie", type="Q", value="PRESS", ctrl=True)
    kmi.properties.name = "ALIGN_MT_align_pie_pro"
    addon_keymaps['ALIGN_MT_align_pie_pro'] = (km, kmi)
    
    bpy.types.NODE_MT_context_menu.append(add_align_op_to_node_mt_context_menu)

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)

    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.NODE_MT_context_menu.remove(add_align_op_to_node_mt_context_menu)
