import os
import bpy
from bpy.props import FloatProperty, PointerProperty
from .op_align import *
from .op_xxx import *

bl_info = {
    "name" : "小王-Node Align",
    "author" : "一尘不染",
    "description" : "align node  Shift Q | Ctrl Q",
    "blender" : (2, 83, 0),
    "version" : (2, 0, 0),
    "location": "Nodes Editor",
    "category": "Node"
}

addon_keymaps = {}
_icons = None
# 按顺序可以换成自定义图片图标
# images = [ '左对齐-蓝色',
#            '右对齐-蓝色',
#            '下对齐-蓝色',
#            '上对齐-蓝色',
#            '上下居中对齐-蓝色',
#            '垂直等距分布-蓝黑',
#            '左右居中对齐-蓝色',
#            '水平等距分布-蓝黑',]
images = [ '左对齐-蓝双色',
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

class Node_Align_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout = self.layout
        split = layout.split(factor=0.5)
        split.label(text="饼菜单1")
        split.prop(find_user_keyconfig('APN_MT_align_pie'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text="饼菜单2")
        split.prop(find_user_keyconfig('ALIGN_MT_align_pie'), 'type', text='', full_event=True)

class ALIGN_MT_align_pie(bpy.types.Menu):
    bl_idname = "ALIGN_MT_align_pie"
    bl_label = "节点对齐"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 左 右 底 顶 左上 右上 左下 右下
        pie.operator("node.align_left",   text="左对齐", icon_value=_icons[images[0]].icon_id)
        pie.operator("node.align_right",  text="右对齐", icon_value=_icons[images[1]].icon_id)
        pie.operator("node.align_bottom", text="底对齐", icon_value=_icons[images[2]].icon_id)
        pie.operator("node.align_top",    text="顶对齐", icon_value=_icons[images[3]].icon_id)
        pie.operator("node.align_height_center",   text="对齐高度",     icon_value=_icons[images[4]].icon_id)
        pie.operator("node.distribute_vertical",   text="垂直等距分布", icon_value=_icons[images[5]].icon_id)
        pie.operator("node.align_width_center",    text="对齐宽度",     icon_value=_icons[images[6]].icon_id)
        pie.operator("node.distribute_horizontal", text="水平等距分布", icon_value=_icons[images[7]].icon_id)

class ALIGN_MT_xxx_pie(bpy.types.Menu):
    bl_idname = "APN_MT_align_pie"
    bl_label = "节点分布"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # 左 右 底 顶 左上 右上 左下 右下
        pie.operator("node.align_dependencies", text="左相连向上等距对齐", icon="ANCHOR_RIGHT")
        pie.operator("node.align_dependent_nodes", text="右相连向上等距对齐", icon="ANCHOR_LEFT")
        pie.operator("node.stake_down_selection_nodes", text="向下等距对齐", icon="ANCHOR_TOP")
        pie.operator("node.straight_link", text="拉直连线", icon_value=_icons[images[11]].icon_id)
        # pie.operator("node.stake_up_selection_nodes",       text = "向上等距对齐",    icon = "ANCHOR_BOTTOM")
        pie.operator("node.align_left_side_selection_nodes", text="向左水平分布", icon="TRIA_LEFT_BAR")
        pie.operator("node.distribute_grid_relative", text="相对网格分布", icon_value=_icons[images[8]].icon_id)
        pie.operator("node.align_right_side_selection_nodes", text="向右水平分布", icon="TRIA_RIGHT_BAR")
        pie.operator("node.distribute_grid_absolute", text="绝对网格分布", icon_value=_icons[images[9]].icon_id)


classes = [
    Node_Align_AddonPrefs,
    ALIGN_MT_xxx_pie,
    ALIGN_MT_align_pie,
    AlignDependentNodes,
    AlignDependenciesNodes,
    StakeUpSelectionNodes,
    StakeDownSelectionNodes,
    # AlignTopSelectionNodes,
    AlignRightSideSelectionNodes,
    AlignLeftSideSelectionNodes,
    
    NODE_OT_align_bottom,
    NODE_OT_align_top,
    NODE_OT_align_right,
    NODE_OT_align_left,
    NODE_OT_align_heightcenter,
    NODE_OT_align_widthcenter,
    NODE_OT_distribute_horizontal,
    NODE_OT_distribute_vertical,
    NODE_OT_distribute_grid_relative,
    NODE_OT_distribute_grid_absolute,
    NODE_OT_straight_link,
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
    # Align Pie Menu
    kmi = km.keymap_items.new("wm.call_menu_pie", type="Q", value="PRESS", ctrl=True)
    kmi.properties.name = "APN_MT_align_pie"
    addon_keymaps['APN_MT_align_pie'] = (km, kmi)
    # Snap Pie Menu
    kmi = km.keymap_items.new("wm.call_menu_pie", type="Q", value="PRESS", shift=True)
    kmi.properties.name = "ALIGN_MT_align_pie"
    addon_keymaps['ALIGN_MT_align_pie'] = (km, kmi)

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)

    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
