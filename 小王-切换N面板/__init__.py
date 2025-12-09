bl_info = {
    "name": "小王-切换几何节点N面板",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0), # 最低支持的 Blender 版本
    "location": "Node Editor > Press N",
    "description": "Quickly switch N-Panel categories using a pie menu.",
    "warning": "",
    "doc_url": "",
    "category": "Node",
}


import bpy
from bpy.types import Menu, Operator

addon_keymaps = []

# --- 核心: 饼菜单类 ---
class NODE_MT_n_panel_pie(Menu):
    bl_label = "Switch N-Panel"
    bl_idname = "NODE_MT_n_panel_pie"

    # draw 方法负责绘制菜单内容
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator() # LEFT
        # RIGHT
        op = pie.operator("pme.switch_n_panel_category", text="N 面板", icon='MENU_PANEL')
        op.category_name = "切换N面板"

        pie.separator() # BOTTOM
        pie.separator() # TOP
        pie.separator() # TOP_LEFT

        # TOP_RIGHT (右上)
        op = pie.operator("pme.switch_n_panel_category", text="Group", icon='NODETREE')
        op.category_name = "Group"

        # BOTTOM_LEFT (左下)
        pie.separator()

        # BOTTOM_RIGHT (右下)
        op = pie.operator("pme.switch_n_panel_category", text="Node", icon='NODE')
        op.category_name = "Node"


# --- 切换分类的操作符 ---
class PME_OT_switch_n_panel_category(Operator):
    """操作符: 切换节点编辑器 N 面板的分类"""
    bl_idname = "pme.switch_n_panel_category"
    bl_label = "Switch N-Panel Category"

    category_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'NODE_EDITOR'

    def execute(self, context):
        area = context.area
        if self.category_name == "切换N面板":
            if context.space_data.show_region_ui == True:
                context.space_data.show_region_ui = False
            else:
                context.space_data.show_region_ui = True
            return {'FINISHED'}

        if context.space_data.show_region_ui == False:
            context.space_data.show_region_ui = True
        ui_region = next((region for region in area.regions if region.type == 'UI'), None)
        ui_region.active_panel_category = self.category_name
        context.area.tag_redraw()

        return {'FINISHED'}


classes = (
    NODE_MT_n_panel_pie,
    PME_OT_switch_n_panel_category,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # --- 添加快捷键 ---
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu_pie', type='TAB', value="CLICK_DRAG")
        kmi.properties.name = NODE_MT_n_panel_pie.bl_idname
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
