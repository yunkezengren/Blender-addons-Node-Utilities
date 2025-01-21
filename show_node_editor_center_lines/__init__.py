bl_info = {
    "name" : "W_Cloud-小王-节点界面中心线",
    "author" : "小王", 
    "description" : "节点编辑器叠加层和标题栏-视图-移动节点到中心",
    "blender" : (3, 0, 0),
    "version" : (1, 3, 0),
    "category" : "Node" 
}

import bpy
import bpy.utils.previews
import gpu
import gpu_extras
import mathutils
import math
from bpy.app.handlers import persistent
from mathutils import Vector

addon_keymaps = {}
handler_9BAD2 = []

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

def update_attribute_show_center_line(self, context):
    # sna_updated_prop = self.sna_show_center_line # 先前的场景属性删了
    sna_updated_prop = bpy.context.preferences.addons[__name__].preferences.sna_show_line

    if sna_updated_prop:
        sna_func_CAEDF()
    else:
        if handler_9BAD2:
            bpy.types.SpaceNodeEditor.draw_handler_remove(handler_9BAD2[0], 'WINDOW')
            handler_9BAD2.pop(0)
            for a in bpy.context.screen.areas: 
                a.tag_redraw()

def sna_draw_CD78E():
    # addon_name = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
    # addon_name = __file__.split("\\")[-1].rsplit(".", 1)[0]
    addon_name = __name__
    addon_prefs = bpy.context.preferences.addons[addon_name].preferences
    lines = [(tuple(mathutils.Vector((addon_prefs.sna_x_length, 0)) * mathutils.Vector((-1.0, -1.0))), (addon_prefs.sna_x_length, 0))]
    coords = []
    indices = []
    # 这里是一直在运行
    # nodes = bpy.context.space_data.edit_tree.nodes
    # for node in nodes:
    #     node.width = math.floor(node.width / 20) * 20
        
    for i, line in enumerate(lines):
        coords.extend(line)
        indices.append((i*2, i*2+1))
    # shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'LINES', {"pos": coords}, indices=tuple(indices))
    shader.bind()
    shader.uniform_float("color", addon_prefs.sna_x_color)
    gpu.state.line_width_set(addon_prefs.sna_line_width)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    
    lines = [(tuple(mathutils.Vector((0, addon_prefs.sna_y_length)) * mathutils.Vector((-1.0, -1.0))), (0, addon_prefs.sna_y_length))]
    coords = []
    indices = []
    for i, line in enumerate(lines):
        coords.extend(line)
        indices.append((i*2, i*2+1))
    # shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'LINES', {"pos": coords}, indices=tuple(indices))
    shader.bind()
    shader.uniform_float("color", addon_prefs.sna_y_color)
    gpu.state.line_width_set(addon_prefs.sna_line_width)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)

def sna_func_CAEDF():
    handler_9BAD2.append(bpy.types.SpaceNodeEditor.draw_handler_add(sna_draw_CD78E, (), 'WINDOW', 'POST_VIEW'))
    for a in bpy.context.screen.areas: 
        a.tag_redraw()

@persistent
def load_post_handler_6764F(dummy):
    # bpy.context.scene.sna_show_center_line:
    # bpy.context.preferences.addons[__name__].preferences.sna_show_line
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.sna_show_line:
        prefs.sna_show_line = False
        prefs.sna_show_line = True
        # sna_func_CAEDF()   #不清楚为啥只用这个会不能取消显示

class SNA_AddonPreferences_Draw_Center_Line(bpy.types.AddonPreferences):
    bl_idname = __name__
    sna_show_line:    bpy.props.BoolProperty(name='显示中心线', description='', default=False, update=update_attribute_show_center_line)
    sna_x_length:     bpy.props.IntProperty(name='X-长度', description='正半轴长度', default=20000, subtype='NONE')
    sna_y_length:     bpy.props.IntProperty(name='Y-长度', description='正半轴长度', default=10000, subtype='NONE')
    sna_line_width:   bpy.props.FloatProperty(name='Line_Width', description='', default=1.0, subtype='NONE', unit='NONE', step=10, precision=2)
    sna_x_color:      bpy.props.FloatVectorProperty(name='X_Color', description='', size=4, default=(1.0, 0.0, 0.0, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=1, precision=0)
    sna_y_color:      bpy.props.FloatVectorProperty(name='Y_Color', description='', size=4, default=(0.0, 1.0, 0.0, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=1, precision=0)

    def draw(self, context):
        layout = self.layout 
        
        split = layout.split(factor=0.5)
        split.label(text='显示中心线快捷键')
        split.prop(find_user_keyconfig('show_center_line_key'), 'type', text='', full_event=True)
        
        split0 = layout.split(factor=0.5)
        split0.label(text='显示中心线')
        split0.prop(self, 'sna_show_line', text='')
        
        split1 = layout.split(factor=0.5)
        split1.label(text='线宽度')
        split1.prop(self, 'sna_line_width', text='')
        
        split2 = layout.split(factor=0.5)
        split2.label(text='横线颜色')
        split2.prop(self, 'sna_x_color', text='')
        
        split3 = layout.split(factor=0.5)
        split3.label(text='竖线颜色')
        split3.prop(self, 'sna_y_color', text='')
        
        split6 = layout.split(factor=0.5)
        split6.label(text='X-长度')
        split6.prop(self, 'sna_x_length', text='')
        
        split7 = layout.split(factor=0.5)
        split7.label(text='Y-长度')
        split7.prop(self, 'sna_y_length', text='')

def add_move_node_to_node_mt(self, context):
    layout = self.layout
    layout.separator(factor=1.0)
    # layout.prop(bpy.context.scene, 'sna_show_center_line', text='显示中心线')
    layout.prop(context.preferences.addons[__name__].preferences, 'sna_show_line', text='显示中心线')
    layout.operator('sna.move_select_nodes', text='选定节点到中心', icon_value=256)
    layout.operator('sna.move_all_nodes', text='全部节点到中心', icon_value=48)
    layout.operator('sna.move_all_node_groups', text='全部节点树节点到中心', icon_value=48)

def add_show_center_line_to_node_pt_overlay(self, context):
    layout = self.layout
    layout.prop(context.preferences.addons[__name__].preferences, 'sna_show_line', text='显示中心线')

def node_final_loc(node):
    return node.location + node_final_loc(node.parent) if node.parent else node.location

def move_nodes_to_center(nodes):
    if nodes:     #  没有节点不运行
        locs = []
        for node in nodes:
            node.select = True
            if node.bl_idname == "NodeFrame": continue
            location = node_final_loc(node)
            # center = location + Vector((node.width / 2, -node.dimensions.y / 2))
            center = [location.x, location.x + node.width, location.y, location.y -node.dimensions.y]
            locs.append(center)
        print([[l[0], l[1]] for l in locs])
        # # 选中节点重心位置
        # center_x = sum(x for x, y in locs) / len(nodes); center_y = sum(y for x, y in locs) / len(nodes)
        # # 选中节点中心位置
        # center_x1 = (max(x for x, y in locs) + min(x for x, y in locs)) / 2: center_y1 = (max(y for x, y in locs) + min(y for x, y in locs)) / 2
        center_x1 = (min(l[0] for l in locs) + max(l[1] for l in locs)) / 2
        center_y1 = (max(l[2] for l in locs) + min(l[3] for l in locs)) / 2
        for node in nodes:
            # if node.bl_idname != "NodeFrame":
            if node.bl_idname != "NodeFrame":
                node.location -= Vector((center_x1, center_y1))

class SNA_OT_Move_Select_Nodes(bpy.types.Operator):
    bl_idname = "sna.move_select_nodes"
    bl_label = "选定节点到中心"
    bl_description = "选定节点移动到界面中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0):
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        nodes = context.selected_nodes
        move_nodes_to_center(nodes)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class SNA_OT_Move_All_Nodes(bpy.types.Operator):
    bl_idname = "sna.move_all_nodes"
    bl_label = "全部节点到中心"
    bl_description = "全部节点移动到界面中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        nodes = context.space_data.edit_tree.nodes
        move_nodes_to_center(nodes)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class SNA_OT_Move_All_Node_Groups(bpy.types.Operator):
    bl_idname = "sna.move_all_node_groups"
    bl_label = "全部节点树节点到中心"
    bl_description = "全部几何节点和材质节点树节点移动到界面中心"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0):
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        for tree in bpy.data.node_groups:
            nodes = tree.nodes
            move_nodes_to_center(nodes)
        for material in bpy.data.materials:
            tree = material.node_tree
            if tree:
                nodes = tree.nodes
                move_nodes_to_center(nodes)

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class SNA_OT_Key_Show_Center_Line(bpy.types.Operator):
    bl_idname = "sna.show_center_line"
    bl_label = "小王-显示界面中心线"
    bl_description = "显示界面中心线"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if prefs.sna_show_line:
            prefs.sna_show_line = False
        else:
            prefs.sna_show_line = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

classes = [
    SNA_AddonPreferences_Draw_Center_Line,
    SNA_OT_Move_Select_Nodes,
    SNA_OT_Move_All_Nodes,
    SNA_OT_Move_All_Node_Groups,
    SNA_OT_Key_Show_Center_Line
]

def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new('sna.show_center_line', 'FOUR', 'PRESS',
        ctrl=False, alt=False, shift=False, repeat=True)
    addon_keymaps['show_center_line_key'] = (km, kmi)
    
    bpy.app.handlers.load_post.append(load_post_handler_6764F)
    bpy.types.NODE_MT_view.append(add_move_node_to_node_mt)
    bpy.types.NODE_PT_overlay.append(add_show_center_line_to_node_pt_overlay)
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    if handler_9BAD2:
        bpy.types.SpaceNodeEditor.draw_handler_remove(handler_9BAD2[0], 'WINDOW')
        handler_9BAD2.pop(0)
    bpy.app.handlers.load_post.remove(load_post_handler_6764F)
    bpy.types.NODE_MT_view.remove(add_move_node_to_node_mt)
    bpy.types.NODE_PT_overlay.remove(add_show_center_line_to_node_pt_overlay)

    for c in classes:
        bpy.utils.unregister_class(c)
