import bpy
from pprint import pprint
from bpy.types import (Node, NodeSocket, UILayout)

def Prefs():
    return bpy.context.preferences.addons[__package__].preferences

def GetUserKmNe():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']


def GetFirstUpperLetters(txt):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)


def DisplayMessage(title: str, text, icon='NONE'):
    def PopupMessage(self, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')

def format_tool_set(cls: bpy.types.Operator):
    return cls.bl_label + " tool settings"

# 放在这避免循环导入
def sk_label_or_name(sk: NodeSocket):
    return sk.label if sk.label else sk.name

# 放在这避免循环导入
def index_switch_add_input(nodes, index_switch_node):
    old_active = nodes.active
    nodes.active = index_switch_node
    bpy.ops.node.index_switch_item_add()
    nodes.active = old_active
    return index_switch_node.inputs[-2]


