# SPDX-FileCopyrightText: 2026 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Node Editor Zoom",
    "author": "Blender Foundation",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "Node Editor > Sidebar > Zoom",
    "description": "实验性提高节点编辑器最大缩放限制",
    "warning": "实验性功能：会直接改写当前节点编辑器的 View2D 内存",
    "support": 'TESTING',
    "category": "Node",
}

import ctypes
from collections.abc import Iterator
from typing import Final

import bpy
from bpy.props import FloatProperty
from bpy.types import Area, Context, Panel, Region, WindowManager

from .Structure_1_raw_fields import bView2D
# from .Structure import bView2D

SUPPORTED_VERSION: Final[tuple[int, int, int]] = (5, 2, 0)
SUPPORTED_VERSION_LABEL: Final[str] = "5.2.x"

EXPECTED_LAYOUT: Final[dict[str, int]] = {
    "size": 112,
    "minzoom": 96,
    "maxzoom": 100,
    "keepzoom": 110,
}

def is_supported_version() -> bool:
    return bpy.app.version[:2] == SUPPORTED_VERSION[:2]

def has_expected_layout() -> bool:
    return (ctypes.sizeof(bView2D) == EXPECTED_LAYOUT["size"] and bView2D.minzoom.offset == EXPECTED_LAYOUT["minzoom"]
            and bView2D.maxzoom.offset == EXPECTED_LAYOUT["maxzoom"] and bView2D.keepzoom.offset == EXPECTED_LAYOUT["keepzoom"])

def node_editor_window_regions(window_manager: WindowManager) -> Iterator[tuple[Area, Region]]:
    for window in window_manager.windows:
        screen = window.screen
        # if screen is None:  # type: ignore
        #     continue
        for area in screen.areas:
            if area.type != 'NODE_EDITOR':
                continue
            for region in area.regions:
                if region.type == 'WINDOW':
                    yield area, region

def active_node_editor_window_region(context: Context) -> Region | None:
    area = context.area
    if area is None or area.type != 'NODE_EDITOR':
        return None

    for region in area.regions:
        if region.type == 'WINDOW':
            return region
    return None

def view2d_from_region(region: Region) -> bView2D:
    address = region.view2d.as_pointer()
    # `Region.view2d` 虽然能从 RNA 拿到，但 `maxzoom/minzoom` 并没有公开可写接口。
    # 所以这里把原始地址按上面的 C 结构体布局重新解释，再直接修改内存里的字段。
    return bView2D.from_address(address)

def current_zoom_from_view2d(view2d: bView2D) -> float:
    mask_width = (view2d.mask.xmax - view2d.mask.xmin) + 1
    view_width = view2d.cur.xmax - view2d.cur.xmin
    return float(mask_width) / view_width

def tag_node_editor_redraw(window_manager: WindowManager) -> None:
    for area, _region in node_editor_window_regions(window_manager):
        area.tag_redraw()

def apply_node_editor_max_zoom(window_manager: WindowManager, target_zoom: float) -> int:
    if not is_supported_version():
        raise RuntimeError(f"此插件只针对 Blender {SUPPORTED_VERSION_LABEL}；当前版本是 {bpy.app.version_string}")

    if not has_expected_layout():
        raise RuntimeError("bView2D 布局校验失败，当前版本不再匹配 5.2.x")

    updated_regions = 0
    for _area, region in node_editor_window_regions(window_manager):
        view2d = view2d_from_region(region)
        view2d.maxzoom = target_zoom
        updated_regions += 1

    tag_node_editor_redraw(window_manager)
    return updated_regions

def update_max_zoom(wm: WindowManager, context: Context | None) -> None:
    try:
        updated_regions = apply_node_editor_max_zoom(wm, wm.node_editor_max_zoom)
        if updated_regions == 0:
            print("[node_editor_zoom] 没有找到可更新的节点编辑器区域")
    except Exception as ex:
        print(f"[node_editor_zoom] 更新最大缩放失败: {ex}")

class NODE_PT_experimental_zoom_limit(Panel):
    bl_idname = "NODE_PT_experimental_zoom_limit"
    bl_label = "实验性缩放限制"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Zoom"

    def draw(self, context: Context) -> None:
        layout = self.layout

        col = layout.column(align=True)
        col.prop(context.window_manager, "node_editor_max_zoom", text="最大缩放")

        info_col = layout.column(align=True)
        region = active_node_editor_window_region(context)
        if region:
            view2d = view2d_from_region(region)
            current_zoom = current_zoom_from_view2d(view2d)
            info_col.label(text=f"缩放: 最小:{view2d.minzoom:.2f} 最大:{view2d.maxzoom:.2f} 当前:{current_zoom:.2f}")

        # version_col = layout.column(align=True)
        # version_col.label(text=f"目标 Blender: {SUPPORTED_VERSION_LABEL}")
        # version_col.label(text=f"当前版本: {bpy.app.version_string}")

classes = (NODE_PT_experimental_zoom_limit, )

def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.node_editor_max_zoom = FloatProperty(
        default=10.0,
        min=0.01,
        max=1000.0,
        soft_max=500.0,
        options={'SKIP_SAVE'},
        update=update_max_zoom,
        description="实验性修改当前已打开节点编辑器区域的 bView2D 最大缩放",
    )

def unregister() -> None:
    del bpy.types.WindowManager.node_editor_max_zoom

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
