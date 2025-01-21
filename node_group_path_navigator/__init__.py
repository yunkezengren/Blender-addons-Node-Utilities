import bpy
from pprint import pprint
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel, AddonPreferences

bl_info = {
    "name" : "W_Cloud-小王-节点组路径导航",
    "author" : "一尘不染", 
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (1, 0, 0),
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

class ATTRLIST_AddonPreferences(AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout 
        split = layout.split(factor=0.5)
        split.label(text='节点组路径面板快捷键 :')
        split.prop(find_user_keyconfig('唤出节点组路径面板'), 'type', text='', full_event=True)

def build_group_structure(node_tree, parent_path, stored_group=[], group_path="", depth=1):
    # node_name 即为 group_node_name_path
    group_structure = {}
    group_count = {}  # 用于存储每个组名出现的次数
    for node in node_tree.nodes:
        if node.type == "GROUP":
            tree = node.node_tree
            # parent_path = parent_path + "/" + tree.name if parent_path else tree.name
            # 使用了current_path来保存当前的parent_path，而不是直接修改parent_path。
            # 这样，每次递归调用时，parent_path都不会被修改，而是在递归返回时恢复到上一层的状态。
            group_name = tree.name
            if group_name in group_count:
                group_count[group_name] += 1
            else:
                group_count[group_name] = 1
            current_path = parent_path + "/" + group_name if parent_path else group_name
            temp_group_path = group_path + "/" + node.name if group_path else node.name
            # 将子组结构和出现次数存储在字典中
            group_structure[group_name] = {
                'name': node.name,
                'count': group_count[group_name],
                "parent_path": current_path,
                "group_path": temp_group_path,
                "depth": depth
                }
            # if group_name in stored_group:  continue      # 确实没出错，但是已存过的组，就不再显示自己的结构了
            n_d = [group_name, depth]
            if n_d not in stored_group:
                stored_group.append(n_d)
            subgroup_structure = build_group_structure(tree, current_path, stored_group, temp_group_path, depth+1)
            if subgroup_structure:
                group_structure[group_name]['subgroups'] = subgroup_structure
    return group_structure

def sort_dict_by_count(path_dict):
    sorted_d = {}
    for k, v in path_dict.items():
        if 'subgroups' in v:
            v['subgroups'] = sort_dict_by_count(v['subgroups'])
        sorted_d[k] = v
    return dict(sorted(sorted_d.items(), key=lambda item: item[1]['count'], reverse=False))

def draw_group_structure(layout, path_dict):
    for group_name, data in path_dict.items():
        depth = data["depth"]
        
        space = bpy.context.space_data
        tree_name = space.edit_tree.name
        if bpy.context.area.ui_type == "ShaderNodeTree":
            tree_name = space.path.to_string.split("/")[-1]     # 'Material/NodeGroup'
        depress = (group_name == tree_name)
        
        if depth == 0:
            op = layout.operator('node.group_path_navigator', text=group_name, depress=depress, icon="GEOMETRY_NODES")
            op.exit_root = True
        else:
            show_count = bpy.context.scene.show_group_count
            if show_count:
                split0 = layout.split(factor=0.88)
                split1 = split0
            else:
                split1 = layout
            for i in range(depth):
                split1 = split1.split(factor=0.05)
                split1.label(text="|")
            op = split1.operator('node.group_path_navigator', text=group_name, depress=depress, icon="NODETREE")
            op.group_path = data["group_path"]
            op.parent_path = data["parent_path"]
            op.exit_root = False
            if show_count:
                split0.label(text=f"×{data['count']}")


        if 'subgroups' in data:
            draw_group_structure(layout, data['subgroups'])

def print_group_structure(path_dict, prefix=""):
    for group_name, data in path_dict.items():
        print(prefix + f"{group_name}  × {data['count']}")
        if 'subgroups' in data:
            temp = "|   " * (data["depth"] + 1)
            print_group_structure(data['subgroups'], prefix=temp)

def get_context_tree_name():
    space = bpy.context.space_data
    # if bpy.context.area.ui_type == "ShaderNodeTree":          还可以这样
    #     tree_name = space.path.to_string.split("/")[-1]     # 'Material/NodeGroup'
    if type(space.id) ==  bpy.types.Material:
        tree_name = space.id.name
    else:
        tree_name = space.node_tree.name
    return tree_name

def build_root_tree_structure(path_dict):
    tree_name = get_context_tree_name()
    return {tree_name: {'count': 1,
                        'name': '顶层',
                        'depth': 0,
                        'subgroups': path_dict},
                }

def draw_tree_path_panel(self, context, is_npanel):
    space = context.space_data
    tree = space.node_tree
    layout = self.layout
    layout.label(text="节点组路径导航", icon="TRACKING_REFINE_FORWARDS")
    tree_name = get_context_tree_name()
    tree_path_dict = build_group_structure(tree, parent_path=tree_name, stored_group=[])
    sorted_path_dict = sort_dict_by_count(tree_path_dict)
    tree_path_dict = build_root_tree_structure(sorted_path_dict)
    # pprint(tree_path_dict)
    if is_npanel:
        split_key = layout.split(factor=0.5)
        split_key.label(text='快捷键 :')
        split_key.prop(find_user_keyconfig('唤出节点组路径面板'), 'type', text='', full_event=True)
        split_count = layout.split(factor=0.5)
        split_count.label(text='显示节点组数量 :')
        split_count.prop(context.scene, "show_group_count", text='显示数量', toggle=True)
        
    draw_group_structure(layout, tree_path_dict)

def string_width(text):
    width = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 检测中文字符
            width += 2
        else:
            width += 1
    return width

class NODE_OT_tree_path_panel(Operator):
    bl_idname = "node.draw_tree_path_panel"
    bl_label = "tree_path_panel"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        draw_tree_path_panel(self, context, is_npanel=False)
        
    def invoke(self, context, event):
        root_name = get_context_tree_name()
        group_name_list = [[root_name, 0]]
        build_group_structure(node_tree=context.space_data.node_tree,
                              parent_path=root_name, stored_group=group_name_list)
        # pprint(group_name_list)
        # width_list = []
        # for name, depth in group_name_list:
        #     name_width = string_width(name) + depth * 2
        #     width_list.append(name_width)
        # excess = max(width_list) - 14
        max_width = max(string_width(name)+depth*2 for name, depth in group_name_list)
        width = 200
        # excess = int(max_width - 20)
        # excess = int(max_width * 1.2 - 24)
        excess = int(max_width - 24)
        # 20 相当于width=200时的最大字符宽度
        if excess > 0:
            width += excess * 12
        return context.window_manager.invoke_popup(self, width=width)

class NODE_OT_Group_Path_Navigator(Operator):
    bl_idname = "node.group_path_navigator"
    bl_label = "节点组退回顶层"
    bl_description = "节点组退回顶层"
    exit_root : BoolProperty(name='exit_root', description='目标退到顶层', default=False)
    group_path :  StringProperty(name='group_path', description='group_node_name_path', default="", subtype='NONE')
    parent_path : StringProperty(name='parent_path', description='parent_tree_name_path', default="", subtype='NONE')

    def execute(self, context):
        exit_group_to_root()
        space = context.space_data
        # context.space_data.path.pop()
        if self.exit_root:  return {'FINISHED'}

        group_list = self.group_path.split("/")
        parent_list = self.parent_path.split("/")[:-1]       #  不加[:-1]也没问题
        # print(self.group_path)   # Group.003/Group.006/Group.001           3
        # print(self.parent_path)  # Geometry Nodes/step/应用约束/获取属性   4,多一级，for zip 循环3次，跳过最后一次
        i = 0
        for path, name in zip(parent_list, group_list):
            if i == 0 and type(space.id) ==  bpy.types.Material:
                i += 1
                nodes = bpy.data.materials[path].node_tree.nodes
            else:
                nodes = bpy.data.node_groups[path].nodes
            group_node = nodes[name]
            nodes.active = group_node
            bpy.ops.node.group_edit(exit=False)
        return {'FINISHED'}

class TREE_PATH_PT_NPanel(Panel):
    bl_label = '小王-节点组路径导航'            # 还作为在快捷键列表里名称
    bl_idname = 'TREE_PATH_PT_NPanel'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Group'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        edit_tree = context.space_data.edit_tree
        # return context.area.ui_type in ['GeometryNodeTree', 'ShaderNodeTree'] and edit_tree
        return edit_tree

    def draw(self, context):
        draw_tree_path_panel(self, context, is_npanel=True)

def exit_group_to_root():
    space = bpy.context.space_data
    tree_path = space.path.to_string.split("/")[1:]     # 只留下节点组的名字，不包括根名
    for i in range(len(tree_path)):
        space.path.pop()
        # bpy.ops.node.tree_path_parent()


classes = [
    NODE_OT_Group_Path_Navigator,
    TREE_PATH_PT_NPanel,
    ATTRLIST_AddonPreferences,
    NODE_OT_tree_path_panel
]
def register():
    S = bpy.types.Scene
    S.show_group_count   = BoolProperty(name='show_group_count', description='是否显示节点组数量', default=True)
    
    for cla in classes:
        bpy.utils.register_class(cla)

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

    kmi = km.keymap_items.new('node.draw_tree_path_panel', 'THREE', 'PRESS',
                    ctrl=False, alt=False, shift=False, repeat=False)
    
    addon_keymaps['唤出节点组路径面板'] = (km, kmi)
    
    # print("\nregister" + "-" * 50)
    # print(f"{len(km.keymap_items) = } ")
    # print("register" + "-" * 50)

def unregister():
    S = bpy.types.Scene
    # wm = bpy.context.window_manager
    # kc = wm.keyconfigs.addon
    # print("\nunregister" + "=" * 80)
    for km, kmi in addon_keymaps.values():
        # print(f"{len(km.keymap_items) = } ")
        # print(f"{km.name = } ")
        # print(f"{kmi.name   = } ")
        # print(f"{kmi.idname = } ")
        # for item in km.keymap_items:
        #     print(f"{item.name   = }")
        #     print(f"{item.idname = }")
        #     if item.idname == "node.draw_tree_path_panel":
        #         print("keymap_items 里 存在 node.draw_tree_path_panel")
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    # print(f"remove之后: {len(km.keymap_items) = } ")
    # print("unregister" + "=" * 50)
    
    del S.show_group_count
    for cla in classes:
        bpy.utils.unregister_class(cla)

