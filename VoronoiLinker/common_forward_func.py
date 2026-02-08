import bpy
from bpy.types import Node, NodeSocket, Panel, Operator
from bpy.app.translations import pgettext_iface as _iface
from .globals import dict_typeSkToBlid

def Prefs():        # 很多局部变量也是prefs 还是改大写好点
    return bpy.context.preferences.addons[__package__].preferences # type: ignore

def user_node_keymaps():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']

def GetFirstUpperLetters(txt: str):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)

def DisplayMessage(title: str, text: str, icon='NONE'):
    def PopupMessage(self: Panel, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')
 
def format_tool_set(cls: Operator):
    return _iface(cls.bl_label) + _iface(" tool settings")

# ======================放在这避免循环导入
# 关于节点的函数 和 common_class 都用到了
def sk_label_or_name(sk: NodeSocket):
    return sk.label if sk.label else sk.name

def sk_type_to_idname(sk: NodeSocket):
    """ 接口.label 是'',有特例吗? """
    return dict_typeSkToBlid.get(sk.type, "Vl_Unknow")

def is_builtin_tree_idname(blid: str):
    set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}
    return blid in set_quartetClassicTreeBlids

def add_item_for_index_switch(node: Node):
    nodes = node.id_data.nodes
    old_active = nodes.active
    nodes.active = node
    bpy.ops.node.index_switch_item_add()
    nodes.active = old_active
    return node.inputs[-2]
    # old_active = nodes.active
    # nodes.active = index_switch_node
    # bpy.ops.node.index_switch_item_add()
    # nodes.active = old_active
    # return index_switch_node.inputs[-2]

# ========================================

def SetPieData(self: Operator, toolData, prefs, col):
# def SetPieData(self: Operator, toolData: "VmtData", prefs, col):
    def GetPiePref(name):
        return getattr(prefs, self.vlTripleName.lower()+name)
    toolData.isSpeedPie = GetPiePref("PieType")=='SPEED'
    # todo1v6: 已经有 toolData.prefs 了, 所以可以干掉这个; 并且把这一切都做得更优雅些. 还有 SolderClsToolNames() 里的注释.
    toolData.pieScale = GetPiePref("PieScale") 
    toolData.pieDisplaySocketTypeInfo = GetPiePref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = GetPiePref("PieDisplaySocketColor")
    toolData.pieAlignment = GetPiePref("PieAlignment")
    toolData.uiScale = self.uiScale
    toolData.prefs = prefs
    prefs.vaDecorColSkBack = col # 这句在 vaDecorColSk 之前很重要; 参见 VaUpdateDecorColSk().
    prefs.vaDecorColSk = col