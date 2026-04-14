import bpy
from bpy.types import KeyMap, Node, NodeSocket, Operator, Panel, UILayout
from bpy.app.translations import pgettext_iface as _iface

from .globals import sk_type_idname_map
from .common_class import PieRootData

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 将 VoronoiAddonPrefs 的导入移至 TYPE_CHECKING 块中，并将函数签名改为字符串类型注解，避免循环导入。
    from .preference import VoronoiAddonPrefs
    from .base_tool import BaseTool

def user_node_keymap() -> KeyMap:
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']

def get_first_upper_letters(txt: str):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)

def display_message(title: str, text: str, icon='NONE'):
    def popup_message(self: Panel, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(popup_message, title=title, icon='NONE')

def format_tool_label(cls: type[Operator]):
    return _iface(cls.bl_label) + _iface(" tool settings")

# ======================放在这避免循环导入
# 关于节点的函数 和 common_class 都用到了
def sk_label_or_name(sk: NodeSocket):
    return sk.label if sk.label else sk.name

def sk_type_to_idname(sk: NodeSocket):
    idname = sk_type_idname_map.get(sk.type, "")
    return idname if idname else "NodeSocket" + sk.type.capitalize()

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

def set_pie_data(self: "BaseTool", toolData: PieRootData, prefs: "VoronoiAddonPrefs", col: UILayout):

    def get_pie_pref(name):
        return getattr(prefs, self.vlTripleName.lower() + name)

    toolData.isSpeedPie = get_pie_pref("PieType") == 'SPEED'
    # todo1v6: 已经有 toolData.prefs 了, 所以可以干掉这个; 并且把这一切都做得更优雅些. 还有 SolderClsToolNames() 里的注释.
    toolData.pieScale = get_pie_pref("PieScale")
    toolData.pieDisplaySocketTypeInfo = get_pie_pref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = get_pie_pref("PieDisplaySocketColor")
    toolData.pieAlignment = get_pie_pref("PieAlignment")
    toolData.uiScale = self.uiScale
    toolData.prefs = prefs
    prefs.vaDecorColSkBack = col  # 这句在 vaDecorColSk 之前很重要; 参见 VaUpdateDecorColSk().
    prefs.vaDecorColSk = col
