from .C_Structure import BNode
from .globals import *
from .utils_color import Color4, opaque_color4, power_color4
from .forward_func import GetFirstUpperLetters
from mathutils import Vector as Vec
import bpy
# from .C_Structure import bpy.types.NodeSocket


dict_solderedSkLinksFinal = {}
def SkGetSolderedLinksFinal(self): # .vl_sold_links_final
    return dict_solderedSkLinksFinal.get(self, [])

dict_solderedSkIsFinalLinkedCount = {}
def SkGetSolderedIsFinalLinkedCount(self): # .vl_sold_is_final_linked_cou
    return dict_solderedSkIsFinalLinkedCount.get(self, 0)

def SolderSkLinks(tree):
    def Update(dict_data, lk):
        dict_data.setdefault(lk.from_socket, []).append(lk)
        dict_data.setdefault(lk.to_socket, []).append(lk)
    #dict_solderedSkLinksRaw.clear()
    dict_solderedSkLinksFinal.clear()
    dict_solderedSkIsFinalLinkedCount.clear()
    for lk in tree.links:
        #Update(dict_solderedSkLinksRaw, lk)
        if (lk.is_valid)and not(lk.is_muted or lk.is_hidden):
            Update(dict_solderedSkLinksFinal, lk)
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.from_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.from_socket] += 1
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.to_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.to_socket] += 1


for key, value in dict_skTypeHandSolderingColor.items():
    dict_skTypeHandSolderingColor[key] = power_color4(value, pw=2.2)

class SoldThemeCols:
    dict_mapNcAtt = {0: 'input_node',        1:  'output_node',  3: 'color_node',
                     4: 'vector_node',       5:  'filter_node',  6: 'group_node',
                     8: 'converter_node',    9:  'matte_node',   10:'distor_node',
                     12:'pattern_node',      13: 'texture_node', 32:'script_node',
                     33:'group_socket_node', 40: 'shader_node',  41:'geometry_node',
                     42:'attribute_node',    100:'layout_node'}
def SolderThemeCols(themeNe):
    def GetNiceColNone(col4):
        return Color4(col4)
        # return Color4(power_color4(col4, pw=1/1.75))   # 小王 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
    def MixThCol(col1, col2, fac=0.4): # \source\blender\editors\space_node\node_draw.cc : node_draw_basis() : "Header"
        return col1*(1-fac)+col2*fac
    SoldThemeCols.node_backdrop4 = Color4(themeNe.node_backdrop)
    SoldThemeCols.node_backdrop4pw = GetNiceColNone(SoldThemeCols.node_backdrop4) # 对于Ctrl-F: 它被使用了, 参见下面的 `+"4pw"`.

    # theme = C.preferences.themes[0].node_editor
    # getattr(theme, "attribute_node")
    # for pr in theme.bl_rna.properties:
    #     dnf = pr.identifier
    #     if dnf.endswith("_node"):
    #         print(f"{dnf = }")
    # themeNe 是 context.preferences.themes[0].node_editor
    # print("." * 50)
    for pr in themeNe.bl_rna.properties:
        dnf = pr.identifier
        if dnf.endswith("_node"):
            # print(f"{dnf = }")
            # print(f"{getattr(themeNe, dnf) = }")                            # type  Color
            # print(f"{opaque_color4(getattr(themeNe, dnf)) = }")            # type  tuple
            # print(f"{Color4(opaque_color4(getattr(themeNe, dnf))) = }")     # type  Vector
            # print(f" 混合后 {col4 = }")
            # 和背景混合使得偏亮
            # col4 = MixThCol(SoldThemeCols.node_backdrop4, Color4(opaque_color4(getattr(themeNe, dnf))))
            col4 = Color4(opaque_color4(getattr(themeNe, dnf)))   # 小王 解决 Ctrl Shift E / Ctrl E / Alt E 等显示太浅
            # 5.0.2里这样写的
            # col4 = MixThCol(SoldThemeCols.node_backdrop4, Color4(opaque_color4(getattr(themeNe, dnf))))
            setattr(SoldThemeCols, dnf+"4", col4)
            setattr(SoldThemeCols, dnf+"4pw", GetNiceColNone(col4))
            setattr(SoldThemeCols, dnf+"3", Vec(col4[:3])) # 用于 vptRvEeIsSavePreviewResults.

def GetNdThemeNclassCol(ndTar):
    if ndTar.bl_idname=='ShaderNodeMix':
        match ndTar.data_type:
            case 'RGBA':   return SoldThemeCols.color_node4pw
            case 'VECTOR': return SoldThemeCols.vector_node4pw
            case _:        return SoldThemeCols.converter_node4pw
    else:
        # 小王
        return getattr(SoldThemeCols, SoldThemeCols.dict_mapNcAtt.get(BNode.GetFields(ndTar).typeinfo.contents.nclass, 'node_backdrop')+"4pw")

def SolderClsToolNames(class_dict: dict):
    for cls in class_dict:
        cls.vlTripleName = GetFirstUpperLetters(cls.bl_label)+"T" # 最初创建是"因为好玩", 但现在需要了; 参见 SetPieData().
        cls.disclBoxPropName = cls.vlTripleName[:-1].lower()+"BoxDiscl"
        cls.disclBoxPropNameInfo = cls.disclBoxPropName+"Info"

def RegisterSolderings():
    txtDoc = "Property from and only for VoronoiLinker addon."
    #bpy.types.NodeSocket.vl_sold_links_raw = property(SkGetSolderedLinksRaw)
    bpy.types.NodeSocket.vl_sold_links_final = property(SkGetSolderedLinksFinal)
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou = property(SkGetSolderedIsFinalLinkedCount)
    #bpy.types.NodeSocket.vl_sold_links_raw.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_links_final.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou.__doc__ = txtDoc

def UnregisterSolderings():
    #del bpy.types.NodeSocket.vl_sold_links_raw
    del bpy.types.NodeSocket.vl_sold_links_final
    del bpy.types.NodeSocket.vl_sold_is_final_linked_cou
