import bpy
from bpy.types import NodeSocket
from collections.abc import Sequence
float4 = Sequence[float]

def power_color(color: float4, *, power: float = 1 / 2.2) -> float4:
    """对颜色进行幂运算调整. power: 幂指数, 默认为 1/2.2 (标准 Gamma 校正)."""
    return tuple(channel**power for channel in color)

def set_alpha(color: float4, *, alpha: float = 1.0) -> float4:
    """设置颜色的透明度通道."""
    return (color[0], color[1], color[2], alpha)

def clamp_color(color: float4) -> float4:
    """将颜色值限制为非负数."""
    return (max(color[0], 0.0), max(color[1], 0.0), max(color[2], 0.0), max(color[3], 0.0))

def get_color_brightness(color: float4, *, power: float) -> float:
    """基于 RGB 最大值计算亮度, 亮转暗. 用于根据背景色亮度决定阴影强度.
    Returns:
        0.0 ~ 1.0 之间的暗度系数, 越亮的颜色返回值越大(越需要加暗)
    """
    brightness = max(color[:3])  # RGB 最大值代表亮度
    return (1.0 - brightness)**power

def get_sk_color(socket: NodeSocket) -> float4:
    """获取节点插槽的显示颜色."""
    if socket.bl_idname == 'NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(socket, 'draw_color'):
        # 注意: 如果需要摆脱所有 `bpy.` 并实现所有 context 的正确路径, 那么首先要考虑这个问题.
        return socket.draw_color(bpy.context, socket.node)
    elif hasattr(socket, 'draw_color_simple'):
        return socket.draw_color_simple()
    else:
        return (1.0, 0.0, 1.0, 1.0)

def get_sk_color_safe(socket: NodeSocket) -> float4:
    """安全地获取节点插槽颜色.
    - 所有通道值 >= 0 (通过 clamp_color)
    - 完全不透明 (alpha = 1.0, 不获取插槽的透明度)
    """
    return set_alpha(clamp_color(get_sk_color(socket)))
