from mathutils import Vector as Color4
import bpy
from bpy.types import NodeSocket

float4 = tuple[float, float, float, float]

def power_color4(arr: float4, *, pw=1/2.2) -> float4:
    # return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)  ||  map(lambda a: a**pw, arr)
    return tuple(i**pw for i in arr)

def opaque_color4(color, *, alpha=1.0) -> float4:
    return (color[0], color[1], color[2], alpha)

def clamp_color4(color) -> float4:
    return (max(color[0], 0), max(color[1], 0), max(color[2], 0), max(color[3], 0))

def get_color_black_alpha(color: Color4, *, pw: float) -> float:
    # (R, G, B)最大值通常代表了它的亮度, 亮 转 暗
    # return ( 1.0 - max(max(c[0], c[1]), c[2]) )**pw
    return ( 1 - max(color[:3]) )**pw

def get_sk_color(socket: NodeSocket):
    if socket.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(socket,'draw_color'):
        # 注意: 如果需要摆脱所有 `bpy.` 并实现所有 context 的正确路径, 那么首先要考虑这个问题.
        return socket.draw_color(bpy.context, socket.node)
    elif hasattr(socket,'draw_color_simple'):
        return socket.draw_color_simple()
    else:
        return (1, 0, 1, 1)

def get_sk_color_safe(socket: NodeSocket) -> float4:   # 不从插槽获取透明度; 并去掉插槽可能存在的负值.
    return opaque_color4(clamp_color4(get_sk_color(socket)))