import copy
from math import cos, pi, sin
from typing import Iterable
import bpy, blf, gpu, gpu_extras
from bpy.app.translations import pgettext_iface as _iface
from bpy.types import Context, NodeSocket
from ..Structure import View2D
from ..common_class import Target, float2, float4, Vec2 
from ..preference import VoronoiAddonPrefs
from .color import clamp_color, get_color_brightness, get_sk_color, get_sk_color_safe, set_alpha, power_color
from .node import node_abs_loc
from .solder import node_tag_color

Vec4 = Vec2
white = (1.0, 1.0, 1.0, 1.0)

class Drawer():
    shaderLine = None
    shaderArea = None
    worldZoom = 0.0

    def __init__(self, context: Context, cursorLoc: Vec2, uiScale: float, prefs: VoronoiAddonPrefs):
        self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        # POLYLINE_FLAT_COLOR, POLYLINE_SMOOTH_COLOR, POLYLINE_UNIFORM_COLOR, FLAT_COLOR, SMOOTH_COLOR, [UNIFORM_COLOR]
        self.shaderArea = gpu.shader.from_builtin('UNIFORM_COLOR')
        #self.shaderLine.uniform_float('lineSmooth', True) # 无需, 默认为 True.
        self.fontId = blf.load(prefs.dsFontFile)  # 持续设置字体是为了在更换主题时字体不消失.
        ##
        self.whereActivated = context.space_data
        self.uiScale = uiScale
        self.view_to_region = context.region.view2d.view_to_region
        self.cursorLoc = cursorLoc
        ##
        for prop in prefs.bl_rna.properties:
            if prop.identifier.startswith("ds"):
                setattr(self, prop.identifier, getattr(prefs, prop.identifier))
        match prefs.dsDisplayStyle:
            case 'CLASSIC':
                self.dsFrameDisplayType = 2
            case 'SIMPLIFIED':
                self.dsFrameDisplayType = 1
            case 'ONLY_TEXT':
                self.dsFrameDisplayType = 0
        ##
        self.dsUniformColor = Vec4(power_color(self.dsUniformColor))
        self.dsUniformNodeColor = Vec4(power_color(self.dsUniformNodeColor))
        self.dsCursorColor = Vec4(power_color(self.dsCursorColor))

    def draw_line_strip(self, positions: Iterable[float2], colors: Iterable[float4], width: float) -> None:
        gpu.state.blend_set('ALPHA')  # 绘制文本会重置 alpha 标记, 因此每次都设置.
        self.shaderLine.bind()
        self.shaderLine.uniform_float('lineWidth', width)
        self.shaderLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
        gpu_extras.batch.batch_for_shader(self.shaderLine, type='LINE_STRIP', content={
            'pos': positions,
            'color': colors
        }).draw(self.shaderLine)

    def draw_triangle_fan(self, positions: Iterable[float2], color: float4) -> None:
        gpu.state.blend_set('ALPHA')
        self.shaderArea.bind()
        self.shaderArea.uniform_float('color', color)
        #todo2v6 弄清楚如何为多边形也做平滑处理.
        gpu_extras.batch.batch_for_shader(self.shaderArea, type='TRI_FAN', content={'pos': positions}).draw(self.shaderArea)

    def ui_to_region(self, vec: Vec2) -> Vec2:
        vec = vec * self.uiScale
        return Vec2(self.view_to_region(vec.x, vec.y, clip=False))

    def draw_rect(self, bounds1: float2, bounds2: float2, color: float4) -> None:
        self.draw_triangle_fan(((bounds1[0], bounds1[1]), (bounds2[0], bounds1[1]), (bounds2[0], bounds2[1]), (bounds1[0], bounds2[1])),
                               color)

    def draw_circle(self, pos: float2, radius: float, resolution: int = 54, color: float4 = white) -> None:
        #第一个顶点自豪地在中心, 其他顶点在圆周上. 需要平滑伪影朝向中心, 而不是斜向某个方向
        self.draw_triangle_fan(
            ((pos[0], pos[1]), *[(pos[0] + radius * cos(cyc * 2.0 * pi / resolution), pos[1] + radius * sin(cyc * 2.0 * pi / resolution))
                                 for cyc in range(resolution + 1)]), color)

    def draw_ring(self,
                  pos: float2,
                  radius: float,
                  width: float,
                  resolution: int = 16,
                  color: float4 = white,
                  spin: float = 0.0) -> None:
        positions = tuple((radius * cos(cyc*2*pi/resolution + spin) + pos[0], radius * sin(cyc*2*pi/resolution + spin) + pos[1])
                          for cyc in range(resolution + 1))
        self.draw_line_strip(positions, (color, ) * (resolution+1), width)

    def draw_point_highlight(self,
                             pos: float2,
                             radius: float,
                             color1: float4 = white,
                             color2: float4 = white,
                             resolution: int = 54) -> None:
        colFacOut = Vec4((0.5, 0.5, 0.5, 0.4))
        self.draw_circle(pos, radius + 3.0, resolution, color1 * colFacOut)
        self.draw_circle(pos, radius, resolution, color1 * colFacOut)
        self.draw_circle(pos, radius / 1.5, resolution, color2)

def draw_connection_line(drawer: Drawer, pos1: Vec2, pos2: Vec2, color1: float4, color2: float4) -> None:
    drawer.draw_line_strip((drawer.ui_to_region(pos1), drawer.ui_to_region(pos2)), (color1, color2), drawer.dsLineWidth)

def draw_socket_area(drawer: Drawer, socket: NodeSocket, bounds: float2, color: float4) -> None:
    loc = node_abs_loc(socket.node)
    pos1 = drawer.ui_to_region(Vec2((loc.x, bounds[0])))
    pos2 = drawer.ui_to_region(Vec2((loc.x + socket.node.width, bounds[1])))
    if drawer.dsIsColoredSkArea:
        color[3] = drawer.dsSocketAreaAlpha  # 注意: 这里总是收到不透明颜色; 所以可以覆盖而不是乘.
    else:
        color = drawer.dsUniformColor
    drawer.draw_rect(pos1, pos2, color)

def draw_socket_point(drawer: Drawer,
                      pos: Vec2,
                      color1: Vec4 = white,
                      color2: Vec4 = white,
                      resolution: int = 54,
                      forcibly_color: bool = False) -> None:  #"forcibly_color" 只用于 draw_debug_info.
    if not (drawer.dsIsColoredPoint or forcibly_color):
        color1 = color2 = drawer.dsUniformColor
    drawer.draw_point_highlight(drawer.ui_to_region(pos), ((6 * drawer.dsPointScale * drawer.worldZoom)**2 + 10)**0.5, color1, color2,
                                resolution)

def draw_link_marker(drawer: Drawer, pos: float2, color: float4, style: int) -> None:
    fac = get_color_brightness(color, power=1.5) * 0.625  #todo1v6 标记颜色在亮色和黑色之间看起来不美观; 需要想点办法.
    colSh = (fac, fac, fac, 0.5)  # 阴影
    colHl = (0.65, 0.65, 0.65, max(max(color[0], color[1]), color[2]) * 0.9 / (3.5, 5.75, 4.5)[style])  # 透明白色描边
    colMt = (color[0], color[1], color[2], 0.925)  # 彩色底
    resolution = (16, 16, 5)[style]
    ##
    drawer.draw_ring((pos[0] + 1.5, pos[1] + 3.5), 9.0, 3.0, resolution, colSh)
    drawer.draw_ring((pos[0] - 3.5, pos[1] - 5.0), 9.0, 3.0, resolution, colSh)

    def draw_marker_backlight(spin: float, color: float4) -> None:
        resolution = (16, 4, 16)[style]
        drawer.draw_ring((pos[0], pos[1] + 5.0), 9.0, 3.0, resolution, color, spin)
        drawer.draw_ring((pos[0] - 5.0, pos[1] - 3.5), 9.0, 3.0, resolution, color, spin)

    draw_marker_backlight(pi / resolution, colHl)  # 标记绘制时有"像素孔"伪影。通过旋转的重复绘制来修复它们。
    draw_marker_backlight(0.0, colHl)  # 但因此需要将白色描边的 alpha 减半。
    drawer.draw_ring((pos[0], pos[1] + 5.0), 9.0, 1.0, resolution, colMt)
    drawer.draw_ring((pos[0] - 5.0, pos[1] - 3.5), 9.0, 1.0, resolution, colMt)

def draw_socket_marker(drawer: Drawer, pos: Vec2, offset: float2, color: float4) -> None:
    vec = drawer.ui_to_region(pos)
    dir = 1 if offset[0] > 0 else -1
    ofsX = dir * ((20 * drawer.dsIsDrawText + drawer.dsDistFromCursor) * 1.5 + drawer.dsFrameOffset) + 4
    color = color if drawer.dsIsColoredMarker else drawer.dsUniformColor
    draw_link_marker(drawer, (vec[0] + offset[0] + ofsX, vec[1] + offset[1]), color, drawer.dsMarkerStyle)

def draw_framed_text(drawer: Drawer, pos1: float2, pos2: float2, text: str, size: float, y_offset: float, text_color: float4,
                     frame_color: float4, bg_color: float4) -> float2:
    pos1x = ps1x = pos1[0]
    pos1y = ps1y = pos1[1]
    pos2x = ps2x = pos2[0]
    pos2y = ps2y = pos2[1]
    blur = 5
    # 文本框:
    match drawer.dsFrameDisplayType:
        case 2:  # 漂亮的边框
            gradResl = 12
            gradStripHei = (pos2y-pos1y) / gradResl
            # 透明渐变背景:
            LFx = lambda x, a, b: ((x+b) / (b+1))**0.6 * (1-a) + a
            for cyc in range(gradResl):
                drawer.draw_rect((pos1x, pos1y + cyc*gradStripHei), (pos2x, pos1y + cyc*gradStripHei + gradStripHei),
                                 (bg_color[0] / 2, bg_color[1] / 2, bg_color[2] / 2, LFx(cyc / gradResl, 0.2, 0.05) * bg_color[3]))
            # 明亮的主描边:
            drawer.draw_line_strip((pos1, (pos2x, pos1y), pos2, (pos1x, pos2y), pos1), (frame_color, ) * 5,
                                   1.0)  # 天啊, 如果 frame_color[0]==-1, 结果会包含复数. 那里发生了什么?
            # 额外的柔和描边 (连同角落), 增加美感:
            ps1x += .25
            ps1y += .25
            ps2x -= .25
            ps2y -= .25
            ofs = 2.0
            positions = ((ps1x, ps1y - ofs), (ps2x, ps1y - ofs), (ps2x + ofs, ps1y), (ps2x + ofs, ps2y), (ps2x, ps2y + ofs),
                         (ps1x, ps2y + ofs), (ps1x - ofs, ps2y), (ps1x - ofs, ps1y), (ps1x, ps1y - ofs))
            drawer.draw_line_strip(positions, ((frame_color[0], frame_color[1], frame_color[2], 0.375), ) * 9, 1.0)
        case 1:  # 给那些不喜欢漂亮边框的人. 他们不喜欢什么呢?.
            drawer.draw_rect((pos1x, pos1y), (pos2x, pos2y), (bg_color[0] / 2.4, bg_color[1] / 2.4, bg_color[2] / 2.4, 0.8 * bg_color[3]))
            drawer.draw_line_strip((pos1, (pos2x, pos1y), pos2, (pos1x, pos2y), pos1), ((0.1, 0.1, 0.1, 0.95), ) * 5, 1.0)
    # 文本:
    fontId = drawer.fontId
    blf.size(fontId, size)
    dim = blf.dimensions(fontId, text)
    cen = ((pos1x+pos2x) / 2, (pos1y+pos2y) / 2)
    blf.position(fontId, cen[0] - dim[0] / 2, cen[1] + y_offset, 0)
    blf.enable(fontId, blf.SHADOW)
    # 暗色套接字的背光:
    blf.shadow_offset(fontId, 1, -1)
    blf.shadow(fontId, blur, 1.0, 1.0, 1.0, get_color_brightness(text_color, power=3.0) * 0.75)
    blf.color(fontId, 0.0, 0.0, 0.0, 0.0)
    blf.draw(fontId, text)
    # 文本本身:
    if drawer.dsIsAllowTextShadow:
        color = drawer.dsShadowCol
        blf.shadow_offset(fontId, drawer.dsShadowOffset[0], drawer.dsShadowOffset[1])
        blf.shadow(fontId, (0, 3, 5)[drawer.dsShadowBlur], color[0], color[1], color[2], color[3])
    else:
        blf.disable(fontId, blf.SHADOW)
    blf.color(fontId, text_color[0], text_color[1], text_color[2], 1.0)
    blf.draw(fontId, text)
    return (pos2x - pos1x, pos2y - pos1y)

def draw_world_text(drawer: Drawer,
                    pos: Vec2,
                    offset: float2,
                    text: str,
                    text_color: float4,
                    bg_color: float4,
                    font_size_override: float = 0) -> float2:  # font_size_override 仅用于 vptRvEeSksHighlighting.
    size = drawer.dsFontSize * (not font_size_override) + font_size_override
    blf.size(drawer.fontId, size)
    # 不计算"实际文本"的高度, 因为那样每个框每次的高度都会不同.
    # 需要特殊字符作为"通用情况"来覆盖最大高度. 其他字符用于可能比"█"高的特殊字体.
    dimDb = (blf.dimensions(drawer.fontId, text)[0], blf.dimensions(drawer.fontId, "█GJKLPgjklp!?")[1])
    pos = drawer.ui_to_region(pos)
    frameOffset = drawer.dsFrameOffset
    ofsGap = 10
    pos = (pos[0] - (dimDb[0] + frameOffset + ofsGap) * (offset[0] < 0) + (frameOffset+1) * (offset[0] > -1), pos[1] + frameOffset)
    # 我已经完全忘了我搞了什么鬼以及它是如何工作的; 但它工作了 -- 这就很好, "能工作就别动":
    placePosY = round((dimDb[1] + frameOffset*2) * offset[1])  # 不四舍五入, 水平线的美感会消失.
    pos1 = (pos[0] + offset[0] - frameOffset, pos[1] + placePosY - frameOffset)
    pos2 = (pos[0] + offset[0] + ofsGap + dimDb[0] + frameOffset, pos[1] + placePosY + dimDb[1] + frameOffset)
    ##
    # 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
    # return draw_framed_text(drawer, pos1, pos2, text, size=size, y_offset=dimDb[1]*drawer.dsManualAdjustment, text_color=power_color(text_color, power=1/1.975), frame_color=power_color(bg_color, power=1/1.5), bg_color=bg_color)
    return draw_framed_text(drawer, pos1, pos2, text, size, dimDb[1] * drawer.dsManualAdjustment, text_color, bg_color, bg_color)  # 绘制颜色加深

def draw_socket_text(drawer: Drawer,
                     pos: Vec2,
                     offset: float2,
                     target: Target,
                     font_size_override: float = 0,
                     tool_color: float4 = (0, 0, 0, 0)) -> float2:
    # 注意: `pos` 总是为了 drawer.cursorLoc, 但请参见 vptRvEeSksHighlighting.
    if not drawer.dsIsDrawText:
        return (1, 0)  #'1' 需要用于保存标记位置的方向信息.
    if drawer.dsIsColoredText:
        text_color = get_sk_color_safe(target.tar)
        bg_color = clamp_color(get_sk_color(target.tar))
    else:
        text_color = bg_color = drawer.dsUniformColor
    return draw_world_text(drawer, pos, offset, target.soldText, text_color, bg_color, font_size_override)

def draw_debug_info(self, drawer: Drawer) -> None:

    def draw_debug_text(pos: float2, text: str, r: float, g: float, b: float) -> None:
        blf.size(0, 18)
        blf.position(0, pos[0] + 10, pos[1], 0)
        blf.color(0, r, g, b, 1.0)
        blf.draw(0, text)

    draw_debug_text(drawer.ui_to_region(drawer.cursorLoc), "Cursor position here.", 1, 1, 1)
    if not self.tree:
        return
    color = Vec4((1.0, 0.5, 0.5, 1.0))
    list_tarNodes = self.get_nearest_nodes(cur_x_off=0)
    if not list_tarNodes:
        return
    draw_connection_line(drawer, drawer.cursorLoc, list_tarNodes[0].pos, color, color)
    for cyc, li in enumerate(list_tarNodes):
        draw_socket_point(drawer, li.pos, color, color, 4, True)
        draw_debug_text(drawer.ui_to_region(li.pos), str(cyc) + " Node goal here", color.x, color.y, color.z)
    tar_sks_in, tar_sks_out = self.get_nearest_sockets(list_tarNodes[0].tar)
    if tar_sks_in:
        color = Vec4((0.5, 1, 0.5, 1))
        draw_socket_point(drawer, tar_sks_in[0].pos, color, color, 4, True)
        draw_debug_text(drawer.ui_to_region(tar_sks_in[0].pos), "Nearest socketIn here", 0.5, 1, 0.5)
    if tar_sks_out:
        color = Vec4((0.5, 0.5, 1, 1))
        draw_socket_point(drawer, tar_sks_out[0].pos, color, color, 4, True)
        draw_debug_text(drawer.ui_to_region(tar_sks_out[0].pos), "Nearest socketOut here", 0.75, 0.75, 1)

# 模板重新思考过了; 很好. 现在它变得像其他所有的一样了.. 至少没有旧版本中的意大利面条式代码了.
def draw_node_template(drawer: Drawer, target_node: Target | None, side: int = 1, tool_name: str = "") -> None:
    #todo1v6 模板只有一个 tar, 没有分层, 两个调用会从一个绘制点和线到另一个的文本上方.
    if target_node:
        node_target = target_node.tar
        if drawer.dsIsColoredNodes:  # 嗯.. 现在节点终于有颜色了; 感谢 ctypes.
            color_line = node_tag_color(node_target)
            # color_line[0] += 0.5
            # color_line[1] += 0.5
            # color_line[2] += 0.5
            color_point = color_line
            color_text = color_line
        else:
            color_uncolored = drawer.dsUniformNodeColor
            color_line = color_uncolored if drawer.dsIsColoredLine else drawer.dsUniformColor
            color_point = color_uncolored if drawer.dsIsColoredPoint else drawer.dsUniformColor
            # color_text = color_uncolored if drawer.dsIsColoredText else drawer.dsUniformColor
            color_text = color_uncolored
        if drawer.dsIsDrawLine:
            draw_connection_line(drawer, drawer.cursorLoc, target_node.pos, color_line, color_line)
        if drawer.dsIsDrawPoint:
            draw_socket_point(drawer, target_node.pos, color_point, color_point)
        if (drawer.dsIsDrawText) and (drawer.dsIsDrawNodeNameLabel):
            text = node_target.label if node_target.label else node_target.bl_rna.name
            if node_target.type == "GROUP":
                text = node_target.node_tree.name  # 优化-绘制节点组名字
            else:
                text = node_target.label

            draw_world_text(drawer, drawer.cursorLoc, (drawer.dsDistFromCursor * side, -0.5), text, color_text, color_text)
            draw_world_text(drawer, drawer.cursorLoc, (drawer.dsDistFromCursor * side, 1), _iface(tool_name), color_text, color_text)
            # # 额外绘制
            # print(f"{text = }")
            # print(f"{(drawer.dsDistFromCursor*side, -0.5) = }")
            # draw_world_text(drawer, drawer.cursorLoc, (0, 1), tool_name, text_color=color_text, bg_color=color_text)
    elif drawer.dsIsDrawPoint:
        color = white  # 唯一剩下的未定义颜色. 'dsCursorColor' 在这里按设计不适合 (整个插件都是为了套接字, 对吧?).
        draw_socket_point(drawer, drawer.cursorLoc, Vec4(color), color)

# 高级套接字绘制模板. 现在名称中有"Sk", 因为节点已完全进入 VL.
# 在旧版本中的硬核之后, 使用这个模板简直是享受 (甚至不要看那里, 那里简直是地狱).
# 模板重新思考过了, 万岁. 感觉上并没有变得更好.
def draw_sockets_template(
    drawer: Drawer,
    *args_targets: Target | None,
    side_mark_offset: int = 1,
    is_draw_text: bool = True,
    is_classic_flow: bool = False,
    is_draw_markers_more_than_one: bool = False,
    tool_name: str = "",
) -> None:

    def get_pos_from_target(target: Target) -> Vec2:
        return target.pos + Vec2((drawer.dsPointOffsetX * target.dir, 0.0))

    target_sockets = [ar for ar in args_targets if ar]
    cursor_loc = drawer.cursorLoc
    # 缺少目标
    if not target_sockets:  # 方便地只为了现在不存在的 DrawDoubleNone() 使用模板, 通过向 args_targets 发送 `None, None`.
        color = drawer.dsCursorColor if drawer.dsIsColoredPoint else drawer.dsUniformColor
        is_pair = len(args_targets) == 2
        vec = Vec2((drawer.dsPointOffsetX * 0.75, 0)) if (is_pair) and (is_classic_flow) else Vec2((0.0, 0.0))
        if (is_pair) and (drawer.dsIsDrawLine) and (drawer.dsIsAlwaysLine):
            draw_connection_line(drawer, cursor_loc - vec, cursor_loc + vec, color, color)
        if drawer.dsIsDrawPoint:
            draw_socket_point(drawer, cursor_loc - vec, color, color)
            if (is_pair) and (is_classic_flow):
                draw_socket_point(drawer, cursor_loc + vec, color, color)
        return
    # 经典流程线
    if (is_classic_flow) and (drawer.dsIsDrawLine) and (len(target_sockets) == 2):
        target1 = target_sockets[0]
        target2 = target_sockets[1]
        if target1.dir * target2.dir < 0:  # 对于 VMLT, 为了不为它的两个套接字绘制, 它们在同一侧.
            if drawer.dsIsColoredLine:
                color1 = get_sk_color_safe(target1.tar)
                color2 = get_sk_color_safe(target2.tar)
            else:
                color1 = color2 = drawer.dsUniformColor
            draw_connection_line(drawer, get_pos_from_target(target1), get_pos_from_target(target2), color1, color2)
    # 主要部分:
    is_one = len(target_sockets) == 1

    for target in target_sockets:
        if (drawer.dsIsDrawLine) and ((not is_classic_flow) or (is_one and drawer.dsIsAlwaysLine)):
            if drawer.dsIsColoredLine:
                color1 = get_sk_color_safe(target.tar)
                color2 = drawer.dsCursorColor if (is_one + (drawer.dsCursorColorAvailability - 1)) > 0 else color1
            else:
                color1 = color2 = drawer.dsUniformColor
            draw_connection_line(drawer, get_pos_from_target(target), cursor_loc, color1, color2)
        if drawer.dsIsDrawSkArea:
            draw_socket_area(drawer, target.tar, target.boxHeiBound, Vec4(get_sk_color_safe(target.tar)))
        if drawer.dsIsDrawPoint:
            draw_socket_point(drawer, get_pos_from_target(target), Vec4(clamp_color(get_sk_color(target.tar))),
                              Vec4(get_sk_color_safe(target.tar)))
    # 文本
    if is_draw_text:  # 文本应该在所有其他 ^ 之上.
        targets_in = [target for target in target_sockets if target.dir < 0]
        targets_out = [target for target in target_sockets if target.dir > 0]
        x_offset = 0
        sold_override_dir = abs(side_mark_offset) > 1 and (1 if side_mark_offset > 0 else -1)
        for list_targets in targets_in, targets_out:  # "累积", 天才! 意大利面条式代码的头疼消失了.
            hig = len(list_targets) - 1
            for cyc, target in enumerate(list_targets):
                ofs_y = 0.75*hig - 1.5*cyc
                dir = sold_override_dir if sold_override_dir else target.dir * side_mark_offset
                x_offset = drawer.dsDistFromCursor * dir
                frame_dim = draw_socket_text(drawer, cursor_loc, (drawer.dsDistFromCursor * dir, ofs_y - 0.5), target)
                if (drawer.dsIsDrawMarker) and ((target.tar.vl_sold_is_final_linked_cou) and (not is_draw_markers_more_than_one) or
                                                (target.tar.vl_sold_is_final_linked_cou > 1)):
                    draw_socket_marker(drawer, cursor_loc, (frame_dim[0] * dir, frame_dim[1] * ofs_y), get_sk_color_safe(target.tar))
            # 绘制工具提示
            target_show_name = copy.copy(target)
            target_show_name.soldText = _iface(tool_name).capitalize()
            if x_offset != 0:
                cursor_loc2 = cursor_loc.copy() + Vec2((0, 50))  # 额外绘制
                draw_socket_text(drawer, cursor_loc2, (x_offset, 0), target_show_name)
                # draw_socket_text(drawer, cursor_loc, (20, 50), target_show_name)
    # todo tool_name 的绘制和接口文本的绘制要分开,tool_name 要始终绘制,不要受 is_draw_text 影响
    # todo 但是如果在下面绘制,批量连线时只绘制一根线(虽然正常连接)
    # if not is_draw_text:      # 屎山的形成
    #     cursor_loc2 = cursor_loc.copy() + Vec2((0, 50))
    #     target_show_name = copy.copy(target)
    #     txt_col = node_tag_color(target_sockets[0].tar.node)
    #     draw_socket_text(drawer, cursor_loc2, (0, 0), target_show_name, tool_color=txt_col)
    #     # draw_world_text(drawer, drawer.cursorLoc, (0, 0), tool_name, text_color=colTx, colBg=colTx)

    # 经典流程的光标下点
    if (is_classic_flow and is_one) and (drawer.dsIsDrawPoint):
        draw_socket_point(drawer, cursor_loc, drawer.dsCursorColor, drawer.dsCursorColor)

#Todo0SF "滑帧"的头疼!! Debug, Collapse, Alt, 以及所有地方.

class TestDraw:

    @classmethod
    def GetNoise(cls, w):
        from mathutils.noise import noise
        return noise((cls.time, w, cls.rand))

    @classmethod
    def Toggle(cls, context: Context, tgl):
        import random
        stNe = bpy.types.SpaceNodeEditor
        if tgl:
            cls.rand = random.random() * 32.0
            cls.time = 0.0
            cls.state = [0.5, 0.5, 0.5, 0.5]
            stNe.nsReg = stNe.nsReg if hasattr(stNe, 'nsReg') else -2
            stNe.nsCur = stNe.nsReg
            stNe.handle = stNe.draw_handler_add(cls.CallbackDrawTest, (context, ), 'WINDOW', 'POST_PIXEL')
        elif hasattr(stNe, 'handle'):
            stNe.draw_handler_remove(stNe.handle, 'WINDOW')
            del stNe.handle
            del stNe.nsCur
            del stNe.nsReg

    @classmethod
    def CallbackDrawTest(cls, context: Context):
        from math import atan2
        from ..preference import pref
        prefs = pref()
        stNe = bpy.types.SpaceNodeEditor
        if stNe.nsCur != stNe.nsReg:
            # 重新关闭并打开:
            prefs.dsIsTestDrawing = False
            # 该死的拓扑!
            prefs.dsIsTestDrawing = True
            return  # 不知道是否必须退出.
        drawer = Drawer(context, context.space_data.cursor_location, context.preferences.system.dpi / 72, prefs)
        cls.ctView2d = View2D.GetFields(context.region.view2d)
        drawer.worldZoom = cls.ctView2d.GetZoom()
        ##
        for cyc in range(4):
            noise = cls.GetNoise(cyc)
            fac = 1.0  # if cyc<4 else (1.0 if noise>0 else cls.state[cyc])
            cls.state[cyc] = min(max(cls.state[cyc] + noise, 0.0), 1.0) * fac
        ##
        drawer.draw_line_strip(((0, 0), (1000, 1000)), (white, white), 0.0)
        for cycWid in range(9):
            ofsWid = cycWid * 45
            for cycAl in range(4):
                col = (1, 1, 1, .25 * (1+cycAl))
                ofsAl = cycAl * 8
                for cyc5 in range(2):
                    ofs5x = 65 * cyc5
                    ofs5y = 0.5 * cyc5
                    drawer.draw_line_strip(((100 + ofs5x, 100 + ofsWid + ofsAl + ofs5y), (165 + ofs5x, 100 + ofsWid + ofsAl + ofs5y)),
                                           (col, col), 0.5 * (1+cycWid))
        ##
        col = Vec4(cls.state)
        drawer.cursorLoc = context.space_data.cursor_location
        cursorReg = drawer.ui_to_region(drawer.cursorLoc)
        vec = cursorReg - Vec2((500, 500))
        drawer.draw_ring((500, 500), vec.length, cursorReg.x / 200, max(3, int(cursorReg.y / 20)), white, pi/2 - atan2(vec.x, vec.y))
        # 混乱:
        center = Vec2((context.region.width / 2, context.region.height / 2))
        txt = "a.¯\_(- _-)_/¯"
        draw_framed_text(drawer, (300, 300), (490, 330), txt, 24, (555-525) * -.2, white, white, white)
        txt = bpy.context.window_manager.clipboard
        txt = txt[0] if txt else "a."
        draw_framed_text(drawer, (375, 170), (400, 280), txt, 24, 0, white, white, white)
        draw_framed_text(drawer, (410, 200), (435, 250), txt, 24, 0, white, white, white)
        #draw_framed_text(drawer, (445,200), (470,250), txt, size=24, y_offset=0, text_color=white_4, frame_color=white_4, bg_color=white_4)
        loc = context.space_data.edit_tree.view_center
        col2 = col.copy()
        col2.w = max(0, (cursorReg.y - center.y / 2) / 150)
        draw_world_text(drawer, loc, (-1, 2), "█GJKLPgjklp!?", col, col)
        draw_world_text(drawer, loc, (-1, .33), "abcdefghijklmnopqrstuvwxyz", white, col)
        draw_world_text(drawer, loc, (0, -.33), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", col2, col2)
        vec = Vec2((0, -192 / drawer.worldZoom))
        draw_world_text(drawer, loc + vec, (0, 0), "абфуabfy", col, col)
        draw_world_text(drawer, loc + vec, (200, 0), "аa", col, col)
        draw_world_text(drawer, loc + vec, (300, 0), "абab", col, col)
        draw_world_text(drawer, loc + vec, (500, 0), "ауay", col, col)
        draw_link_marker(drawer, center + Vec2((-50, -60)), col, 0)
        draw_link_marker(drawer, center + Vec2((-100, -60)), col, 1)
        draw_link_marker(drawer, center + Vec2((-150, -60)), col, 2)
        drawer.draw_line_strip((center + Vec2((0, -60)), center + Vec2((100, -60))), (set_alpha(col), set_alpha(col)),
                               drawer.dsLineWidth)
        drawer.draw_line_strip((center + Vec2((100, -60)), center + Vec2((200, -60))), (set_alpha(col), set_alpha(col, alpha=0.0)),
                               drawer.dsLineWidth)
        drawer.draw_point_highlight(center + Vec2((0, -60)), ((6 * drawer.dsPointScale + 1)**2 + 10)**0.5, Vec4(set_alpha(col)),
                                    Vec4(set_alpha(col)))
        drawer.draw_point_highlight(center + Vec2((100, -60)), ((6 * drawer.dsPointScale + 1)**2 + 10)**0.5, col,
                                    Vec4(set_alpha(col)))
        import gpu_extras.presets
        gpu_extras.presets.draw_circle_2d((256, 256), (1, 1, 1, 1), 10)
        ##
        cls.time += 0.01
        bpy.context.space_data.backdrop_zoom = bpy.context.space_data.backdrop_zoom  # 火. 但有没有更"直接"的方法? 备受赞誉的 area.tag_redraw() 不起作用.
