import bpy
from mathutils import Vector as Vec
from bpy.types import Node, NodeSocket, NodeTree, NodeLink, ThemeNodeEditor
from ..Structure import BNode
from ..utils.ui import get_first_upper_letters
from ..globals import sk_type_color_map
from .color import set_alpha, power_color
Vec4 = Vec

from typing import TYPE_CHECKING
if TYPE_CHECKING:  # 避免循环导入
    from ..base_tool import ModelBaseTool

_dict_sold_links_final: dict[NodeSocket, list[NodeLink]] = {}
_dict_sold_link_count: dict[NodeSocket, int] = {}

def _get_sold_links_final(self: NodeSocket) -> list:
    return _dict_sold_links_final.get(self, [])

def _get_sold_link_count(self: NodeSocket) -> int:
    return _dict_sold_link_count.get(self, 0)

def solder_sk_links(tree: NodeTree):
    def update_link_dict(link_dict: dict[NodeSocket, list[NodeLink]], link: NodeLink):
        link_dict.setdefault(link.from_socket, []).append(link)
        link_dict.setdefault(link.to_socket, []).append(link)

    _dict_sold_links_final.clear()
    _dict_sold_link_count.clear()

    for link in tree.links:
        if link.is_valid and not (link.is_muted or link.is_hidden):
            update_link_dict(_dict_sold_links_final, link)
            _dict_sold_link_count.setdefault(link.from_socket, 0)
            _dict_sold_link_count[link.from_socket] += 1
            _dict_sold_link_count.setdefault(link.to_socket, 0)
            _dict_sold_link_count[link.to_socket] += 1

for key, value in sk_type_color_map.items():
    sk_type_color_map[key] = power_color(value, power=2.2)

class SoldThemeCols:
    node_class_map = {0: 'input_node',        1:  'output_node',  3: 'color_node',
                      4: 'vector_node',       5:  'filter_node',  6: 'group_node',
                      8: 'converter_node',    9:  'matte_node',   10:'distor_node',
                      12:'pattern_node',      13: 'texture_node', 32:'script_node',
                      33:'group_socket_node', 40: 'shader_node',  41:'geometry_node',
                      42:'attribute_node',    100:'layout_node'}
    node_backdrop4 : Vec4
    node_backdrop4pw : Vec4

def solder_theme_cols(theme_editor: ThemeNodeEditor):

    def get_nice_color(col4: Vec4):
        # return Vec4(power_color(col4, power=1/1.75))   # 小王 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
        return Vec4(col4)

    def mix_theme_color(col1: Vec4, col2: Vec4, fac=0.4):  # \source\blender\editors\space_node\node_draw.cc : node_draw_basis() : "Header"
        return col1 * (1-fac) + col2*fac

    SoldThemeCols.node_backdrop4 = Vec4(theme_editor.node_backdrop)
    SoldThemeCols.node_backdrop4pw = Vec4(SoldThemeCols.node_backdrop4)  # 对于Ctrl-F: 它被使用了, 参见下面的 `+"4pw"`.

    for prop in theme_editor.bl_rna.properties:
        identity = prop.identifier
        if identity.endswith("_node"):
            # 和背景混合使得偏亮
            # col4 = mix_theme_color(SoldThemeCols.node_backdrop4, Vec4(set_alpha(getattr(theme_editor, identity))))
            col4 = Vec4(set_alpha(getattr(theme_editor, identity)))
            # col4 = mix_theme_color(SoldThemeCols.node_backdrop4, Vec4(set_alpha(getattr(theme_editor, identity))))
            setattr(SoldThemeCols, identity + "4", col4)
            setattr(SoldThemeCols, identity + "4pw", col4)
            setattr(SoldThemeCols, identity + "3", Vec(col4[:3]))  # 用于 vpt_rv_ee_is_save_preview_results.

def node_tag_color(node: Node):
    if bpy.app.version >= (5, 0, 0):
        color_tag = node.color_tag.lower()
        if color_tag == "interface":
            color_tag = "group_socket"
        color_tag += "_node"
        color = getattr(bpy.context.preferences.themes[0].node_editor, color_tag).copy()
        color.s *= 1.5
        color.v *= 0.9
        return Vec((*color, 1))
    else:
        if isinstance(node, bpy.types.ShaderNodeMix):
            match node.data_type:
                case 'RGBA':   return SoldThemeCols.color_node4pw
                case 'VECTOR': return SoldThemeCols.vector_node4pw
                case _:        return SoldThemeCols.converter_node4pw
        else:
            return getattr(SoldThemeCols, SoldThemeCols.node_class_map.get(BNode.GetFields(node).typeinfo.contents.nclass, 'node_backdrop')+"4pw")

def assign_tool_class_names(class_list: list[type["ModelBaseTool"]]):
    """为工具类分配名称属性，用于偏好设置中的折叠面板"""
    for cls in class_list:
        cls.vl_triple_name = get_first_upper_letters(cls.bl_label)+"T" # 最初创建是"因为好玩", 但现在需要了; 参见 set_pie_data().
        cls.discl_box_prop_name = cls.vl_triple_name[:-1].lower()+"BoxDiscl"
        cls.discl_box_prop_name_info = cls.discl_box_prop_name+"Info"

def register_socket_properties():
    """为 NodeSocket 注册扩展属性，用于缓存链接信息"""
    txtDoc = "Property from and only for VoronoiLinker addon."
    NodeSocket.vl_sold_links_final = property(_get_sold_links_final)
    NodeSocket.vl_sold_is_final_linked_cou = property(_get_sold_link_count)
    NodeSocket.vl_sold_links_final.__doc__ = txtDoc
    NodeSocket.vl_sold_is_final_linked_cou.__doc__ = txtDoc

def unregister_socket_properties():
    """注销 NodeSocket 扩展属性"""
    del NodeSocket.vl_sold_links_final
    del NodeSocket.vl_sold_is_final_linked_cou
