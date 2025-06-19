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

def FtgGetTargetOrNone(ftg) -> NodeSocket:
    return ftg.tar if ftg else None

def Prefs():
    return bpy.context.preferences.addons[__package__].preferences