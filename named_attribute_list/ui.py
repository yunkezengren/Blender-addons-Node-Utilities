from bpy.types import Menu, Panel, Context, UILayout

from .constants import GROUPS, data_with_png, shader_date_types
from .preferences import pref
from .utils import get_attrs, get_hided_attrs_by_group, exist_node_tree, get_domain_list
from .operators import AL_OT_add_node, AT_OT_group_info
from .translator import i18n as tr

def draw_attr_menu(layout: UILayout, context: Context, attrs, is_panel=False):
    '''is_panel = True 时,在面板里额外绘制一些东西'''
    from . import _icons
    layout.operator_context = 'INVOKE_DEFAULT'
    ui_type = context.area.ui_type
    for attr_name, attr_info in attrs.items():
        data_type = attr_info.data_type
        if ui_type == 'ShaderNodeTree' and data_type not in shader_date_types: continue

        stored_domain_list = list(set(attr_info.domain_info))
        domain_list_to_str = " | ".join(sorted(stored_domain_list, key=lambda x: get_domain_list().index(x)))
        button_txt = attr_name + pref().show_attr_domain * f"  ({domain_list_to_str})"
        if_instanced = attr_info.if_instanced  or False
        if ui_type == 'ShaderNodeTree' and if_instanced:
            button_txt = button_txt[:-1] + " ->实例)"
        description = tr("属性所在域: ") + domain_list_to_str
        group_name = attr_info.group_name
        can_find_store_node = False
        if group_name != tr("物体属性"):
            description += f'\n{tr("所在节点组: ")}' + str(group_name)
            if group_name != tr("不确定"):
                can_find_store_node = True
        if group_name == tr("物体属性"):
            description += f'\n{tr("类型: ")}' + attr_info.info
        op: AL_OT_add_node = None
        if is_panel:
            split = layout.split(factor=0.9)
            op = split.operator('al.add_node_from_list', text=button_txt, icon_value=(_icons[data_with_png[data_type]].icon_id))
            icon = "HIDE_OFF" if can_find_store_node else "HIDE_ON"
            if ui_type == 'GeometryNodeTree':
                op_find = split.operator('node.view_stored_attribute_node', text="", emboss=can_find_store_node, icon=icon)
                op_find.node_name = (attr_info.node_name or "无属性")[0]
                group_name_list = attr_info.group_node_name or "无属性"
                op_find.group_node_name = str(group_name_list[0])
                op_find.parent_path = (attr_info.group_name_parent or "无属性")[0]
        else:
            op = layout.operator('al.add_node_from_list', text=button_txt, icon_value=(_icons[data_with_png[data_type]].icon_id))
        op.attr_name = attr_name
        op.attr_type = data_type
        op.domain = attr_info.domain[0]
        op.domain_str = domain_list_to_str
        op.if_instanced = if_instanced
        op.bl_description = description
        op.shader_node_type = "ShaderNodeAttribute"
        if group_name == tr("物体属性"):
            if attr_info.info == tr("颜色属性"):
                op.shader_node_type = "ShaderNodeVertexColor"
            if attr_info.info == tr("UV贴图"):
                op.shader_node_type = "ShaderNodeUVMap"

class ATTRLIST_MT_SubMenu(Menu):
    bl_idname = "ATTRLIST_MT_SubMenu"
    bl_label = "Hide Menu"

    def draw(self, context):
        if pref().hide_by_group:
            for group_key, group_label, group_icon, _ in GROUPS:
                attrs = get_hided_attrs_by_group(group_key)
                if attrs:
                    self.layout.menu(f"ATTRLIST_MT_SubMenu_{group_key.value}", text=group_label, icon=group_icon)
        else:
            attrs = get_attrs(get_hided=True)
            draw_attr_menu(self.layout, context, attrs)

def _make_submenu_draw(group, desc):
    def draw(self, context):
        layout = self.layout
        op = layout.operator(AT_OT_group_info.bl_idname, text=" ", icon='INFO', emboss=False)
        op.group_desc = desc
        attrs = get_hided_attrs_by_group(group)
        draw_attr_menu(layout, context, attrs)
    return draw

# 动态生成子菜单类
submenu_classes = []
for _group_key, _group_label, _group_icon, _group_desc in GROUPS:
    _cls = type(f"ATTRLIST_MT_SubMenu_{_group_key.value}", (Menu,), {
        "bl_idname": f"ATTRLIST_MT_SubMenu_{_group_key.value}",
        "bl_label": _group_label,
        "draw": _make_submenu_draw(_group_key, _group_desc),
    })
    submenu_classes.append(_cls)

class ATTRLIST_MT_Menu(Menu):
    bl_idname = "ATTRLIST_MT_Menu"
    bl_label = tr("命名属性菜单")
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    @classmethod
    def poll(cls, context):
        return exist_node_tree(context)

    def draw(self, context):
        self.bl_options = {'SEARCH_ON_KEY_PRESS'} if not pref().use_accelerator_key else set()
        if pref().hide_by_group:
            for group_key, group_label, group_icon, _ in GROUPS:
                attrs = get_hided_attrs_by_group(group_key)
                if attrs:
                    self.layout.menu(f"ATTRLIST_MT_SubMenu_{group_key.value}", text=group_label, icon=group_icon)
        else:
            if get_attrs(get_hided=True):
                self.layout.menu("ATTRLIST_MT_SubMenu", text="Hide", icon='GROUP')
        attrs = get_attrs()
        if attrs:
            self.layout.separator()
        draw_attr_menu(self.layout, context, attrs)

class ATTRLIST_PT_NPanel(Panel):
    bl_label = tr('命名属性面板')
    bl_idname = 'ATTRLIST_PT_NPanel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Node'
    bl_order = 5
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return exist_node_tree(context)

    def draw(self, context):
        layout = self.layout
        prefs = pref()
        a_node = context.active_node
        if a_node:
            if a_node.bl_idname == "GeometryNodeObjectInfo" and a_node.select:
                obj_name = a_node.inputs[0].default_value.name
                info = obj_name + "的属性"
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            info = tr("活动物体及节点树属性")
            icon='GEOMETRY_NODES'
        if ui_type == 'ShaderNodeTree':
            info = tr("活动物体属性")
            icon='MATERIAL_DATA'
        top_row = layout.row()
        top_row.label(text=info, icon=icon)
        top_row.operator("preferences.addon_show", icon='PREFERENCES').module = __package__
        top_row.prop(prefs, 'show_set_panel', toggle=True, text='', icon="TOOL_SETTINGS")

        if prefs.show_set_panel:
            arrow_show = "TRIA_DOWN" if prefs.add_settings else "TRIA_RIGHT"
            box1 = layout.box()
            box1.scale_y = 0.9
            box1.prop(prefs, "add_settings", emboss=True, icon=arrow_show)
            if prefs.add_settings:
                box1.label(text="——→"+tr("属性节点:"))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_option',        toggle=True, text=tr('隐藏节点选项'))
                split.prop(prefs, 'hide_exists_socket', toggle=True, text=tr('隐藏存在接口'))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_name_socket',   toggle=True, text=tr('隐藏名称接口'))
                split.prop(prefs, 'rename_attr_socket', toggle=True, text=tr('重命名属性接口'))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_node',          toggle=True, text=tr('折叠节点'))
                split.prop(prefs, 'rename_node',        toggle=True, text=tr('重命名节点标签'))
                split = box1.split(factor=0.5)
                split.label(text=tr('重命名添加前缀: '))
                split.prop(prefs, 'rename_prefix', text="")

                box1.label(text="——→"+tr("存储属性节点:"))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_store_option',  toggle=True, text=tr('隐藏节点选项'))
                split.prop(prefs, 'hide_select_socket', toggle=True, text=tr('隐藏选中项接口'))
                split = box1.split(factor=0.5)
                split.prop(prefs, 'hide_store_node',    toggle=True, text=tr('折叠节点'))
                split.prop(prefs, 'rename_store_node',  toggle=True, text=tr('重命名节点标签'))

            arrow_add = "TRIA_DOWN" if prefs.show_settings else "TRIA_RIGHT"
            box1.prop(prefs, "show_settings", toggle=True, icon=arrow_add)
            if prefs.show_settings:
                split2 = box1.split(factor=0.4)
                split2.label(text=tr('列表排序方式'))
                split2.prop(prefs, 'sort_type', text='')

                hide_row = box1.row().split(factor=0.6)
                hide_row.label(text=tr('属性列表里隐藏'))
                hide_row.prop(prefs, 'hide_by_group', toggle=True, text=tr('按类别分类'))

                split3 = box1.split(factor=0.05)
                split3.label(text="")
                split31 = split3.split(factor=0.35)
                split31.prop(prefs, 'hide_vertex_group',  toggle=True, text=tr('顶点组'))
                split32 = split31.split(factor=0.4)
                split32.prop(prefs, 'hide_uv_map',        toggle=True, text=tr('UV'))
                split32.prop(prefs, 'hide_color_attr',    toggle=True, text=tr('颜色属性'))

                split4 = box1.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.33)
                split41.prop(prefs, 'hide_extra_attr', toggle=True, text=tr('额外属性'))
                split42 = split41.split(factor=0.5)
                split42.prop(prefs, 'hide_unevaluated_attr', toggle=True, text=tr('未评估'))
                split42.prop(prefs, 'hide_attr_in_group', toggle=True, text=tr('组内属性'))

                split4 = box1.split(factor=0.05)
                split4.label(text="")
                split41 = split4.split(factor=0.5)
                split41.prop(prefs, 'hide_by_prefix', toggle=True, text=tr('隐藏前缀'))
                if prefs.hide_by_prefix:
                    split41.prop(prefs, 'prefix_to_hide', text='')

                split5 = box1.split(factor=0.5)
                split5.label(text=tr('属性列表文本设置'))
                split5.prop(prefs, 'show_attr_domain', toggle=True, text=tr('显示所在域'))

                split6 = box1.split(factor=0.5)
                split6.label(text=tr('查找节点设置'))
                split6.prop(prefs, 'if_scale_editor', toggle=True, text=tr('适当缩放视图'))

                split7 = box1.split(factor=0.5)
                split7.label(text=tr('使用加速键'))
                split7.prop(prefs, 'use_accelerator_key', toggle=True, text=tr('使用加速键'))


        if prefs.hide_unevaluated_attr and hasattr(layout, "panel"):
            box3 = layout.box()
            panel, body = box3.panel("未使用", default_closed=True)
            panel.label(text=tr('未使用'))
            if body:
                draw_attr_menu(body, context, get_attrs(get_hided=True))

        draw_attr_menu(layout.box(), context, get_attrs(), is_panel=True)
