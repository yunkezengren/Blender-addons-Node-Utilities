

from mathutils import Vector as Vec
Vec2 = Color4 = Vec


const_float4 = tuple[float, float, float, float]
def PowerArr4(arr: const_float4, *, pw=1/2.2):
    # return Vec(map(lambda a: a**pw, arr))
    return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def OpaqueCol3Tup4(col, *, al=1.0):
    return (col[0], col[1], col[2], al)
def clamp_Color4(col) -> const_float4:
    return (max(col[0], 0), max(col[1], 0), max(col[2], 0), max(col[3], 0))

def GetSkColorRaw(sk: NodeSocket):
    if sk.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        # 注意: 如果需要摆脱所有 `bpy.` 并实现所有 context 的正确路径, 那么首先要考虑这个问题.
        return sk.draw_color(bpy.context, sk.node)
    elif hasattr(sk,'draw_color_simple'):
        return sk.draw_color_simple()
    else:
        return (1, 0, 1, 1)

def GetSkColorSafeTup4(sk: NodeSocket): # 不从插槽获取透明度; 并去掉插件插槽可能存在的负值.
    return OpaqueCol3Tup4(clamp_Color4(GetSkColorRaw(sk)))


def GetBlackAlphaFromCol(c: Color4, *, pw: float) -> Color3:
    # return ( 1.0 - max(max(c[0], c[1]), c[2]) )**pw
    return ( 1.0 - max(c[:3]) )**pw
