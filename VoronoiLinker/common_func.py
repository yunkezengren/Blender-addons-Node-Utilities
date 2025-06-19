import bpy
from pprint import pprint
from bpy.types import (Node, NodeSocket, UILayout)

def CheckUncollapseNodeAndReNext(nd: Node, self, *, cond: bool, flag=None): # 我是多么鄙视折叠起来的节点啊.
    if nd.hide and cond:
        nd.hide = False
        # 注意: 在 NextAssignmentTool 的拓扑结构中要小心无限循环.
        # 警告! type='DRAW_WIN' 会导致某些罕见的带有折叠节点的节点树崩溃! 如果知道如何重现, 最好能报个bug.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        # todo0: 如果连续展开了多个节点, 应该只重绘一次; 但没必要. 如果发生了这种情况, 说明这个工具的搜索拓扑很糟糕.
        self.NextAssignmentRoot(flag)

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


