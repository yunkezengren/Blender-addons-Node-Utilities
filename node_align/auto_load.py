import os
import bpy
from . import keymap
from . import preferences
from . preferences import *
from . snap_op import *
from . align_op import *
# from . snap_pie_mt import *
# from . align_pie_mt import *

module = keymap
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

class SnapPieMenu(bpy.types.Menu):
    bl_idname = "SPN_MT_snap_pie"
    bl_label = "节点对齐"
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 左
        pie.operator("node.snap_left_side_selection_nodes",      text = "左对齐",    icon_value=_icons[images[0]].icon_id)
        # 右
        pie.operator("node.snap_right_side_selection_nodes",     text = "右对齐",    icon_value=_icons[images[1]].icon_id)
        # 底
        pie.operator("node.snap_bottom_side_selection_nodes",    text = "底对齐",     icon_value=_icons[images[2]].icon_id)
        # 顶
        pie.operator("node.snap_top_side_selection_nodes",       text = "顶对齐",     icon_value=_icons[images[3]].icon_id)
        # 左上
        pie.operator("node.snap_height_center_selection_nodes",  text = "对齐高度",     icon_value=_icons[images[4]].icon_id)
        # 右上
        pie.operator("node.distribute_vertical",                 text = "垂直等距分布",    icon_value=_icons[images[5]].icon_id)
        # 左下
        pie.operator("node.snap_width_center_selection_nodes",   text = "对齐宽度",     icon_value=_icons[images[6]].icon_id)
        # 右下
        pie.operator("node.distribute_horizontal",               text = "水平等距分布",     icon_value=_icons[images[7]].icon_id)

class AlignPieMenu(bpy.types.Menu):
    bl_idname = "APN_MT_align_pie"
    bl_label = "节点分布"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # 左
        pie.operator("node.align_dependencies",               text = "左相连向上等距对齐", icon = "ANCHOR_RIGHT")
        # 右
        pie.operator("node.align_dependent_nodes",            text = "右相连向上等距对齐", icon = "ANCHOR_LEFT")
        # 底
        pie.operator("node.stake_down_selection_nodes",       text = "向下等距对齐",    icon = "ANCHOR_TOP")
        # 顶
        pie.operator("node.straight_link",                    text = "拉直连线",       icon_value=_icons[images[11]].icon_id)
        # pie.operator("node.stake_up_selection_nodes",       text = "向上等距对齐",    icon = "ANCHOR_BOTTOM")
        # 左上
        pie.operator("node.align_left_side_selection_nodes",  text = "向左水平分布",    icon = "TRIA_LEFT_BAR")
        # 右上
        pie.operator("node.distribute_grid_relative",         text = "相对网格分布",    icon_value=_icons[images[8]].icon_id)
        # 左下
        pie.operator("node.align_right_side_selection_nodes", text = "向右水平分布",    icon = "TRIA_RIGHT_BAR")
        # 右下
        pie.operator("node.distribute_grid_absolute",         text = "绝对网格分布",    icon_value=_icons[images[9]].icon_id)

ordered_classes = [AlignPieMenuProperties,             AlignNodesPreferences,  AlignPieMenu, SnapPieMenu,
                   AlignDependentNodes,                AlignDependenciesNodes, StakeUpSelectionNodes,
                   StakeDownSelectionNodes,            AlignTopSelectionNodes, AlignRightSideSelectionNodes,
                   AlignLeftSideSelectionNodes, 
                   SnapBottomSideSelectionNodes,       SnapTopSideSelectionNodes, 
                   SnapRightSideSelectionNodes,        SnapLeftSideSelectionNodes, 
                   SnapHeightCenterSideSelectionNodes, SnapWidthCenterSideSelectionNodes,
                   Distribute_Horizontal,              Distribute_Vertical, 
                   Distribute_Grid_Relative,           Distribute_Grid_Absolute,
                   Straight_Link
                   ]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    for image in images:
        # if not image in _icons: 
        _icons.load(image, os.path.join(os.path.dirname(__file__), 'icons', image), "IMAGE")

    for cls in ordered_classes:
        bpy.utils.register_class(cls)

    bpy.types.AddonPreferences.alignPieMenuProp = bpy.props.PointerProperty(type = AlignPieMenuProperties)

    if module.__name__ == __name__:
            pass
    if hasattr(module, "register"):
        module.register()

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)

    del bpy.types.AddonPreferences.alignPieMenuProp
    for cls in reversed(ordered_classes):
        bpy.utils.unregister_class(cls)

    if module.__name__ == __name__:
            pass
    if hasattr(module, "unregister"):
        module.unregister()

if __name__ == "__main__":
    register()
