from mathutils import Vector as Color4
from bpy.types import NodeSocket

const_float4 = tuple[float, float, float, float]

def power_color4(arr: const_float4, *, pw=1/2.2) -> const_float4:
    # return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)  ||  map(lambda a: a**pw, arr)
    return (i**pw for i in arr)

def opaque_color4(c, *, alpha=1.0) -> const_float4:
    return (c[0], c[1], c[2], alpha)

def clamp_color4(c) -> const_float4:
    return (max(c[0], 0), max(c[1], 0), max(c[2], 0), max(c[3], 0))

def get_color_black_alpha(c: Color4, *, pw: float) -> float:
    # (R, G, B)最大值通常代表了它的亮度, 亮 转 暗
    # return ( 1.0 - max(max(c[0], c[1]), c[2]) )**pw
    return ( 1 - max(c[:3]) )**pw

def get_sk_color(sk: NodeSocket):
    if sk.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        # 注意: 如果需要摆脱所有 `bpy.` 并实现所有 context 的正确路径, 那么首先要考虑这个问题.
        return sk.draw_color(bpy.context, sk.node)
    elif hasattr(sk,'draw_color_simple'):
        return sk.draw_color_simple()
    else:
        return (1, 0, 1, 1)

def get_sk_color_safe(sk: NodeSocket) -> const_float4:   # 不从插槽获取透明度; 并去掉插槽可能存在的负值.
    return opaque_color4(clamp_color4(get_sk_color(sk)))