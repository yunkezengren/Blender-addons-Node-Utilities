import bpy
from bpy.types import Operator, Context, Nodes
from bpy.props import StringProperty, BoolProperty

from .constants import sub_data_type
from .preferences import pref
from .utils import exit_group_to_root, proper_scroll_view
from .translator import i18n as tr

class AL_OT_add_node(Operator):
    bl_idname = "al.add_node_from_list"
    bl_label = "属性隐藏选项"
    bl_options = {"REGISTER", "UNDO"}
    bl_description   : StringProperty(default="快捷键Shift 2 ", options={"HIDDEN"})
    attr_name        : StringProperty(description='', default="", subtype='NONE')
    attr_type        : StringProperty(description='', default="FLOAT", subtype='NONE')
    domain           : StringProperty(default="", description='该属性所在域,例：面 | 实例', options={"HIDDEN"})
    domain_str       : StringProperty(default="", description='该属性所在域,例：面 | 实例', options={"HIDDEN"})
    shader_node_type : StringProperty(description='', default="", subtype='NONE')
    if_instanced     : BoolProperty(description='该属性是否转到了实例域上', default=False)

    _shift = False

    @classmethod
    def description(cls, context: Context, props):
        ui_type = context.area.ui_type
        key_des =""
        if ui_type == "GeometryNodeTree":
            key_des = tr("● 默认:  添加命名属性节点 \n● Shift: 添加存储属性节点 \n")
        if ui_type == 'ShaderNodeTree' and props.shader_node_type != "ShaderNodeAttribute":
            key_des = tr("● 默认:  添加属性节点 \n● Shift: 添加UV贴图或颜色属性节点 \n")
        return key_des + props.bl_description if props else ""

    @classmethod
    def poll(cls, context):
        return context.area.type == "NODE_EDITOR"

    def invoke(self, context, event):
        self._shift = event.shift
        return self.execute(context)

    def execute(self, context):
        prefs = pref()
        data_type2 = self.attr_type
        if data_type2 in sub_data_type:
            data_type2 = sub_data_type[data_type2]
        ui_type = context.area.ui_type
        if ui_type == 'GeometryNodeTree':
            prefs.panel_info = tr("添加已命名属性节点")
            node_type = 'GeometryNodeStoreNamedAttribute' if self._shift else 'GeometryNodeInputNamedAttribute'
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type=node_type)
            attr_node = context.active_node
            attr_node.inputs["Name"].default_value = self.attr_name
            if self._shift:
                if self.attr_type == "INT16_2D":
                    self.attr_type = "FLOAT2"
                attr_node.data_type = self.attr_type
                attr_node.domain = self.domain
                attr_node.inputs["Selection"].hide = prefs.hide_select_socket
                attr_node.show_options = not prefs.hide_store_option
            else:
                attr_node.data_type = data_type2
                attr_node.inputs["Name"].hide = prefs.hide_name_socket
                attr_node.show_options = not prefs.hide_option
                if prefs.rename_attr_socket:
                    if bpy.data.version >= (4, 1, 0):
                        attr_node.outputs["Attribute"].name = self.attr_name
                    else:
                        for socket in attr_node.outputs:
                            if socket.enabled and not socket.hide and socket.name=="Attribute":
                                socket.name = self.attr_name
                attr_node.outputs["Exists"].hide = prefs.hide_exists_socket

        if ui_type == 'ShaderNodeTree':
            prefs.panel_info = tr("添加属性节点")
            node_type = self.shader_node_type
            if not self._shift:
                node_type = "ShaderNodeAttribute"
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type=node_type)
            attr_node = context.active_node
            if node_type == "ShaderNodeAttribute":
                if self.domain_str == tr("实例") or self.if_instanced:
                    attr_node.attribute_type = "INSTANCER"
                attr_node.attribute_name = self.attr_name
                socket_order = {'BOOLEAN'     : 2,
                                'FLOAT'       : 2,
                                'INT'         : 2,
                                'FLOAT_VECTOR': 1,
                                'FLOAT_COLOR' : 0,
                                }
                for i, out_soc in enumerate(attr_node.outputs):
                    order = socket_order[data_type2]
                    if i == order and prefs.rename_attr_socket:
                        out_soc.name = self.attr_name
                    if i != order:
                        out_soc.hide = True
            if node_type == "ShaderNodeVertexColor":
                attr_node.layer_name = self.attr_name
            if node_type == "ShaderNodeUVMap":
                attr_node.uv_map = self.attr_name
            attr_node.show_options = not prefs.hide_name_socket

        if node_type == "GeometryNodeStoreNamedAttribute":
            attr_node.label = (prefs.rename_prefix + self.attr_name) if prefs.rename_store_node else ""
            attr_node.hide = prefs.hide_store_node
        else:
            attr_node.label = (prefs.rename_prefix + self.attr_name) if prefs.rename_node else ""
            attr_node.hide = prefs.hide_node
        return {"FINISHED"}

class NODE_OT_view_stored_attribute_node(Operator):
    bl_idname = "node.view_stored_attribute_node"
    bl_label = tr("跳转到已命名属性节点位置")
    bl_description = tr("对于存了多次的属性,查找节点目前只能定位到其中之一")
    node_name       : StringProperty(name='node_name', description='存储属性节点目标', default="无", subtype='NONE')
    parent_path     : StringProperty(name='parent_path', description='parent_path', default="", subtype='NONE')
    group_node_path : StringProperty(name='group_node_path', description='group_node_path', default="", subtype='NONE')

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'GeometryNodeTree'

    def execute(self, context):
        if self.node_name == "无":
            return {'FINISHED'}
        exit_group_to_root()

        path_list = self.parent_path.split("/")[1:]
        name_list = self.group_node_path.split("/")[1:]

        for path, name in zip(path_list, name_list):
            nodes = bpy.data.node_groups[path].nodes
            group_node = nodes[name]
            nodes.active = group_node
            bpy.ops.node.group_edit(exit=False)

        bpy.ops.node.select_all(action='DESELECT')
        nodes: Nodes = context.space_data.edit_tree.nodes
        tar_node = nodes[self.node_name]
        tar_node.select = True
        nodes.active = tar_node
        region = [region for region in context.area.regions if region.type == "WINDOW"][0]
        with bpy.context.temp_override(area=context.area, region=region):
            proper_scroll_view()
            bpy.ops.node.view_selected()
        return {'FINISHED'}

class NODE_OT_quick_add_named_attribute(Operator):
    bl_idname = "node.quick_add_named_attribute"
    bl_label = tr("快速添加命名属性节点")
    bl_description = tr("快速添加选中的活动存储属性节点相应的已命名属性节点")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'GeometryNodeTree'

    def execute(self, context):
        active_node = context.active_node
        prefs = pref()
        if active_node and active_node.bl_idname == 'GeometryNodeStoreNamedAttribute':
            attr_name = active_node.inputs["Name"].default_value
            data_type = active_node.data_type
            if data_type in sub_data_type:
                data_type = sub_data_type[data_type]
            bpy.ops.node.add_node('INVOKE_REGION_WIN', use_transform=True, type='GeometryNodeInputNamedAttribute')
            attr_node = context.active_node
            attr_node.data_type = data_type
            attr_node.inputs["Name"].default_value = attr_name
            attr_node.inputs["Name"].hide = prefs.hide_name_socket
            attr_node.show_options = not prefs.hide_option
            attr_node.hide = prefs.hide_node
            if prefs.rename_node:
                attr_node.label = prefs.rename_prefix + attr_name
            if prefs.rename_attr_socket:
                if bpy.data.version >= (4, 1, 0):
                    attr_node.outputs["Attribute"].name = attr_name
                else:
                    for socket in attr_node.outputs:
                        if socket.enabled and not socket.hide and socket.name=="Attribute":
                            socket.name = attr_name
            attr_node.outputs["Exists"].hide = prefs.hide_exists_socket
        else:
            bpy.ops.node.add_node('INVOKE_DEFAULT', use_transform=True, type='GeometryNodeInputNamedAttribute')
        return {"FINISHED"}

class AT_OT_group_info(Operator):
    bl_idname = "attrlist.group_info"
    bl_label = ""
    bl_options = {'INTERNAL'}
    group_desc : StringProperty(options={'HIDDEN'})

    @classmethod
    def description(cls, context, props):
        return props.group_desc if props else ""

    @classmethod
    def poll(cls, context):
        return context.area.type == "NODE_EDITOR"

    def execute(self, context):
        return {'PASS_THROUGH'}
