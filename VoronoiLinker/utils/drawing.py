import copy
from math import cos, pi, sin
from typing import Iterable
import bpy, blf, gpu, gpu_extras
from mathutils import Vector as Vec2
from bpy.app.translations import pgettext_iface as _iface
from bpy.types import Context, NodeSocket
from ..Structure import View2D
from ..common_class import Target
from ..preference import VoronoiAddonPrefs
from .color import Color4, clamp_color4, float4, get_color_black_alpha, get_sk_color, get_sk_color_safe, opaque_color4, power_color4
from .node import node_abs_loc
from .solder import node_tag_color

white_float4 = (1.0, 1.0, 1.0, 1.0)
float2 = tuple[float, float]

class Drawer():
    shaderLine = None
    shaderArea = None
    worldZoom = 0.0

    def __init__(self, context: Context, cursorLoc: Vec2, uiScale: float, prefs: VoronoiAddonPrefs):
        self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        # POLYLINE_FLAT_COLOR, POLYLINE_SMOOTH_COLOR, POLYLINE_UNIFORM_COLOR, FLAT_COLOR, SMOOTH_COLOR, [UNIFORM_COLOR]
        self.shaderArea = gpu.shader.from_builtin('UNIFORM_COLOR')
        #self.shaderLine.uniform_float('lineSmooth', True) # 无需, 默认为 True.
        self.fontId = blf.load(prefs.dsFontFile) # 持续设置字体是为了在更换主题时字体不消失.
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
        self.dsUniformColor = Color4(power_color4(self.dsUniformColor))
        self.dsUniformNodeColor = Color4(power_color4(self.dsUniformNodeColor))
        self.dsCursorColor = Color4(power_color4(self.dsCursorColor))

    def DrawPathLL(self, vpos: Iterable[float2], vcol: Iterable[float4], *, wid: float) -> None:
        gpu.state.blend_set('ALPHA') # 绘制文本会重置 alpha 标记, 因此每次都设置.
        self.shaderLine.bind()
        self.shaderLine.uniform_float('lineWidth', wid)
        self.shaderLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
        gpu_extras.batch.batch_for_shader(self.shaderLine, type='LINE_STRIP', content={'pos': vpos, 'color': vcol}).draw(self.shaderLine)

    def DrawAreaFanLL(self, vpos: Iterable[float2], col: float4) -> None:
        gpu.state.blend_set('ALPHA')
        self.shaderArea.bind()
        self.shaderArea.uniform_float('color', col)
        #todo2v6 弄清楚如何为多边形也做平滑处理.
        gpu_extras.batch.batch_for_shader(self.shaderArea, type='TRI_FAN', content={'pos': vpos}).draw(self.shaderArea)

    def VecUiViewToReg(self, vec: Vec2) -> Vec2:
        vec = vec * self.uiScale
        return Vec2(self.view_to_region(vec.x, vec.y, clip=False))

    def DrawRectangle(self, bou1: float2, bou2: float2, col: float4) -> None:
        self.DrawAreaFanLL(((bou1[0], bou1[1]), (bou2[0], bou1[1]), (bou2[0], bou2[1]), (bou1[0], bou2[1])), col)

    def DrawCircle(self, loc: float2, rad: float, *, resl: int = 54, col: float4 = white_float4) -> None:
        #第一个顶点自豪地在中心, 其他顶点在圆周上. 需要平滑伪影朝向中心, 而不是斜向某个方向
        self.DrawAreaFanLL(((loc[0], loc[1]), *[(loc[0] + rad * cos(cyc * 2.0 * pi / resl), loc[1] + rad * sin(cyc * 2.0 * pi / resl))
                                                for cyc in range(resl + 1)]), col)

    def DrawRing(self, pos: float2, rad: float, *, wid: float, resl: int = 16, col: float4 = white_float4, spin: float = 0.0) -> None:
        vpos = tuple((rad * cos(cyc*2*pi/resl + spin) + pos[0], rad * sin(cyc*2*pi/resl + spin) + pos[1]) for cyc in range(resl + 1))
        self.DrawPathLL(vpos, (col, ) * (resl+1), wid=wid)

    def DrawWidePoint(self, loc: float2, *, radHh: float, col1: float4 = white_float4, col2: float4 = white_float4, resl: int = 54) -> None:
        colFacOut = Color4((0.5, 0.5, 0.5, 0.4))
        self.DrawCircle(loc, radHh + 3.0, resl=resl, col=col1 * colFacOut)
        self.DrawCircle(loc, radHh, resl=resl, col=col1 * colFacOut)
        self.DrawCircle(loc, radHh / 1.5, resl=resl, col=col2)

def DrawWorldStick(drawer: Drawer, pos1: Vec2, pos2: Vec2, col1: float4, col2: float4) -> None:
    drawer.DrawPathLL( (drawer.VecUiViewToReg(pos1), drawer.VecUiViewToReg(pos2)), (col1, col2), wid=drawer.dsLineWidth )

def DrawVlSocketArea(drawer: Drawer, sk: NodeSocket, bou: float2, col: float4) -> None:
    loc = node_abs_loc(sk.node)
    pos1 = drawer.VecUiViewToReg(Vec2( (loc.x,               bou[0]) ))
    pos2 = drawer.VecUiViewToReg(Vec2( (loc.x+sk.node.width, bou[1]) ))
    if drawer.dsIsColoredSkArea:
        col[3] = drawer.dsSocketAreaAlpha # 注意: 这里总是收到不透明颜色; 所以可以覆盖而不是乘.
    else:
        col = drawer.dsUniformColor
    drawer.DrawRectangle(pos1, pos2, col)

def DrawVlWidePoint(drawer: Drawer, loc: Vec2, *, col1: Color4 = white_float4, col2: Color4 = white_float4, resl = 54, forciblyCol = False) -> None: #"forciblyCol" 只用于 DrawDebug.
    if not(drawer.dsIsColoredPoint or forciblyCol):
        col1 = col2 = drawer.dsUniformColor
    drawer.DrawWidePoint(drawer.VecUiViewToReg(loc), radHh=((6 * drawer.dsPointScale * drawer.worldZoom)**2 + 10)**0.5, col1=col1, col2=col2, resl=resl)

def DrawMarker(drawer: Drawer, loc: float2, col: float4, *, style: int) -> None:
    fac = get_color_black_alpha(col, pw=1.5)*0.625 #todo1v6 标记颜色在亮色和黑色之间看起来不美观; 需要想点办法.
    colSh = (fac, fac, fac, 0.5) # 阴影
    colHl = (0.65, 0.65, 0.65, max(max(col[0],col[1]),col[2])*0.9/(3.5, 5.75, 4.5)[style]) # 透明白色描边
    colMt = (col[0], col[1], col[2], 0.925) # 彩色底
    resl = (16, 16, 5)[style]
    ##
    drawer.DrawRing((loc[0]+1.5, loc[1]+3.5), 9.0, wid=3.0, resl=resl, col=colSh)
    drawer.DrawRing((loc[0]-3.5, loc[1]-5.0), 9.0, wid=3.0, resl=resl, col=colSh)
    def DrawMarkerBacklight(spin: float, col: float4) -> None:
        resl = (16, 4, 16)[style]
        drawer.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
        drawer.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
    DrawMarkerBacklight(pi/resl, colHl) # 标记绘制时有"像素孔"伪影。通过旋转的重复绘制来修复它们。
    DrawMarkerBacklight(0.0,     colHl) # 但因此需要将白色描边的 alpha 减半。
    drawer.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=1.0, resl=resl, col=colMt)
    drawer.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=1.0, resl=resl, col=colMt)

def DrawVlMarker(drawer: Drawer, loc: Vec2, *, ofsHh: float2, col: float4) -> None:
    vec = drawer.VecUiViewToReg(loc)
    dir = 1 if ofsHh[0]>0 else -1
    ofsX = dir*( (20*drawer.dsIsDrawText+drawer.dsDistFromCursor)*1.5+drawer.dsFrameOffset )+4
    col = col if drawer.dsIsColoredMarker else drawer.dsUniformColor
    DrawMarker(drawer, (vec[0]+ofsHh[0]+ofsX, vec[1]+ofsHh[1]), col, style=drawer.dsMarkerStyle)

def DrawFramedText(drawer: Drawer, pos1: float2, pos2: float2, txt: str, *, siz: float, adj: float, colTx: float4, colFr: float4, colBg: float4) -> float2:
    pos1x = ps1x = pos1[0]
    pos1y = ps1y = pos1[1]
    pos2x = ps2x = pos2[0]
    pos2y = ps2y = pos2[1]
    blur = 5
    # 文本框:
    match drawer.dsFrameDisplayType:
        case 2: # 漂亮的边框
            gradResl = 12
            gradStripHei = (pos2y-pos1y)/gradResl
            # 透明渐变背景:
            LFx = lambda x,a,b: ((x+b)/(b+1))**0.6*(1-a)+a
            for cyc in range(gradResl):
                drawer.DrawRectangle( (pos1x, pos1y+cyc*gradStripHei),
                                     (pos2x, pos1y+cyc*gradStripHei+gradStripHei),
                                     (colBg[0]/2, colBg[1]/2, colBg[2]/2, LFx(cyc/gradResl,0.2,0.05)*colBg[3]) )
            # 明亮的主描边:
            drawer.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), (colFr,)*5, wid=1.0) # 天啊, 如果 colFr[0]==-1, 结果会包含复数. 那里发生了什么?
            # 额外的柔和描边 (连同角落), 增加美感:
            ps1x += .25
            ps1y += .25
            ps2x -= .25
            ps2y -= .25
            ofs = 2.0
            vpos = (  (ps1x, ps1y-ofs),  (ps2x, ps1y-ofs),  (ps2x+ofs, ps1y),  (ps2x+ofs, ps2y),
                      (ps2x, ps2y+ofs),  (ps1x, ps2y+ofs),  (ps1x-ofs, ps2y),  (ps1x-ofs, ps1y),  (ps1x, ps1y-ofs)  )
            drawer.DrawPathLL( vpos, ((colFr[0], colFr[1], colFr[2], 0.375),)*9, wid=1.0)
        case 1: # 给那些不喜欢漂亮边框的人. 他们不喜欢什么呢?.
            drawer.DrawRectangle( (pos1x, pos1y), (pos2x, pos2y), (colBg[0]/2.4, colBg[1]/2.4, colBg[2]/2.4, 0.8*colBg[3]) )
            drawer.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), ((0.1, 0.1, 0.1, 0.95),)*5, wid=1.0)
    # 文本:
    fontId = drawer.fontId
    blf.size(fontId, siz)
    dim = blf.dimensions(fontId, txt)
    cen = ( (pos1x+pos2x)/2, (pos1y+pos2y)/2 )
    blf.position(fontId, cen[0]-dim[0]/2, cen[1]+adj, 0)
    blf.enable(fontId, blf.SHADOW)
    # 暗色套接字的背光:
    blf.shadow_offset(fontId, 1, -1)
    blf.shadow(fontId, blur, 1.0, 1.0, 1.0, get_color_black_alpha(colTx, pw=3.0)*0.75)
    blf.color(fontId, 0.0, 0.0, 0.0, 0.0)
    blf.draw(fontId, txt)
    # 文本本身:
    if drawer.dsIsAllowTextShadow:
        col = drawer.dsShadowCol
        blf.shadow_offset(fontId, drawer.dsShadowOffset[0], drawer.dsShadowOffset[1])
        blf.shadow(fontId, (0, 3, 5)[drawer.dsShadowBlur], col[0], col[1], col[2], col[3])
    else:
        blf.disable(fontId, blf.SHADOW)
    blf.color(fontId, colTx[0], colTx[1], colTx[2], 1.0)
    blf.draw(fontId, txt)
    return (pos2x-pos1x, pos2y-pos1y)

def DrawWorldText(drawer: Drawer, pos: Vec2, ofsHh: float2, text: str, *, text_color: float4, colBg: float4, fontSizeOverwrite: float = 0) -> float2: # fontSizeOverwrite 仅用于 vptRvEeSksHighlighting.
    siz = drawer.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite
    blf.size(drawer.fontId, siz)
    # 不计算"实际文本"的高度, 因为那样每个框每次的高度都会不同.
    # 需要特殊字符作为"通用情况"来覆盖最大高度. 其他字符用于可能比"█"高的特殊字体.
    dimDb = (blf.dimensions(drawer.fontId, text)[0], blf.dimensions(drawer.fontId, "█GJKLPgjklp!?")[1])
    pos = drawer.VecUiViewToReg(pos)
    frameOffset = drawer.dsFrameOffset
    ofsGap = 10
    pos = (pos[0]-(dimDb[0]+frameOffset+ofsGap)*(ofsHh[0]<0)+(frameOffset+1)*(ofsHh[0]>-1), pos[1]+frameOffset)
    # 我已经完全忘了我搞了什么鬼以及它是如何工作的; 但它工作了 -- 这就很好, "能工作就别动":
    placePosY = round( (dimDb[1]+frameOffset*2)*ofsHh[1] ) # 不四舍五入, 水平线的美感会消失.
    pos1 = (pos[0]+ofsHh[0]-frameOffset,               pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofsHh[0]+ofsGap+dimDb[0]+frameOffset, pos[1]+placePosY+dimDb[1]+frameOffset)
    ##
    # 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
    # return DrawFramedText(drawer, pos1, pos2, txt, siz=siz, adj=dimDb[1]*drawer.dsManualAdjustment, colTx=power_color4(text_color, pw=1/1.975), colFr=power_color4(colBg, pw=1/1.5), colBg=colBg)
    return DrawFramedText(drawer, pos1, pos2, text, siz=siz, adj=dimDb[1]*drawer.dsManualAdjustment, colTx=text_color, colFr=colBg, colBg=colBg)   # 绘制颜色加深

def DrawVlSkText(drawer: Drawer, pos: Vec2, ofsHh: float2, tar: Target, *, fontSizeOverwrite: float = 0, tool_color: float4 = (0, 0, 0, 0)) -> float2: # 注意: `pos` 总是为了 drawer.cursorLoc, 但请参见 vptRvEeSksHighlighting.
    if not drawer.dsIsDrawText:
        return (1, 0) #'1' 需要用于保存标记位置的方向信息.
    if drawer.dsIsColoredText:
        text_color = get_sk_color_safe(tar.tar)
        colBg = clamp_color4(get_sk_color(tar.tar))
    else:
        text_color = colBg = drawer.dsUniformColor
    return DrawWorldText(drawer, pos, ofsHh, tar.soldText, text_color=text_color, colBg=colBg, fontSizeOverwrite=fontSizeOverwrite)

def DrawDebug(self, drawer: Drawer) -> None:
    def DebugTextDraw(pos: float2, txt: str, r: float, g: float, b: float) -> None:
        blf.size(0,18)
        blf.position(0, pos[0]+10,pos[1], 0)
        blf.color(0, r,g,b,1.0)
        blf.draw(0, txt)
    DebugTextDraw(drawer.VecUiViewToReg(drawer.cursorLoc), "Cursor position here.", 1, 1, 1)
    if not self.tree:
        return
    col = Color4((1.0, 0.5, 0.5, 1.0))
    list_tarNodes = self.get_nearest_nodes(cur_x_off=0)
    if not list_tarNodes:
        return
    DrawWorldStick(drawer, drawer.cursorLoc, list_tarNodes[0].pos, col, col)
    for cyc, li in enumerate(list_tarNodes):
        DrawVlWidePoint(drawer, li.pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drawer.VecUiViewToReg(li.pos), str(cyc)+" Node goal here", col.x, col.y, col.z)
    tar_sks_in, tar_sks_out = self.get_nearest_sockets(list_tarNodes[0].tar)
    if tar_sks_in:
        col = Color4((0.5, 1, 0.5, 1))
        DrawVlWidePoint(drawer, tar_sks_in[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drawer.VecUiViewToReg(tar_sks_in[0].pos), "Nearest socketIn here", 0.5, 1, 0.5)
    if tar_sks_out:
        col = Color4((0.5, 0.5, 1, 1))
        DrawVlWidePoint(drawer, tar_sks_out[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drawer.VecUiViewToReg(tar_sks_out[0].pos), "Nearest socketOut here", 0.75, 0.75, 1)

def TemplateDrawNodeFull(drawer: Drawer, tar_nd: Target | None, *, side: int = 1, tool_name: str = "") -> None: # 模板重新思考过了; 很好. 现在它变得像其他所有的一样了.. 至少没有旧版本中的意大利面条式代码了.
    #todo1v6 模板只有一个 tar, 没有分层, 两个调用会从一个绘制点和线到另一个的文本上方.
    if tar_nd:
        ndTar = tar_nd.tar
        if drawer.dsIsColoredNodes: # 嗯.. 现在节点终于有颜色了; 感谢 ctypes.
            colLn = node_tag_color(ndTar)
            # colLn[0] += 0.5
            # colLn[1] += 0.5
            # colLn[2] += 0.5
            colPt = colLn
            colTx = colLn
        else:
            colUnc = drawer.dsUniformNodeColor
            colLn = colUnc if drawer.dsIsColoredLine else drawer.dsUniformColor
            colPt = colUnc if drawer.dsIsColoredPoint else drawer.dsUniformColor
            # colTx = colUnc if drawer.dsIsColoredText else drawer.dsUniformColor
            colTx = colUnc
        if drawer.dsIsDrawLine:
            DrawWorldStick(drawer, drawer.cursorLoc, tar_nd.pos, colLn, colLn)
        if drawer.dsIsDrawPoint:
            DrawVlWidePoint(drawer, tar_nd.pos, col1=colPt, col2=colPt)
        if (drawer.dsIsDrawText)and(drawer.dsIsDrawNodeNameLabel):
            txt = ndTar.label if ndTar.label else ndTar.bl_rna.name
            if ndTar.type == "GROUP":
                txt = ndTar.node_tree.name   # 优化-绘制节点组名字
            else:
                txt = ndTar.label

            DrawWorldText(drawer, drawer.cursorLoc, (drawer.dsDistFromCursor*side, -0.5), txt, text_color=colTx, colBg=colTx)
            DrawWorldText(drawer, drawer.cursorLoc, (drawer.dsDistFromCursor*side, 1   ), _iface(tool_name), text_color=colTx, colBg=colTx)
            # # 额外绘制
            # print(f"{txt = }")
            # print(f"{(drawer.dsDistFromCursor*side, -0.5) = }")
            # DrawWorldText(drawer, drawer.cursorLoc, (0, 1), tool_name, text_color=colTx, colBg=colTx)
    elif drawer.dsIsDrawPoint:
        col = white_float4 # 唯一剩下的未定义颜色. 'dsCursorColor' 在这里按设计不适合 (整个插件都是为了套接字, 对吧?).
        DrawVlWidePoint(drawer, drawer.cursorLoc, col1=Color4(col), col2=col)

# 高级套接字绘制模板. 现在名称中有"Sk", 因为节点已完全进入 VL.
# 在旧版本中的硬核之后, 使用这个模板简直是享受 (甚至不要看那里, 那里简直是地狱).
def TemplateDrawSksToolHh(
    drawer: Drawer,
    *args_tarSks: Target | None,
    sideMarkHh=1,
    isDrawText=True,
    isClassicFlow=False,
    isDrawMarkersMoreTharOne=False,
    tool_name="",
) -> None:  # 模板重新思考过了, 万岁. 感觉上并没有变得更好.
    def GetPosFromTar(tar: Target) -> Vec2:
        return tar.pos+Vec2((drawer.dsPointOffsetX*tar.dir, 0.0))
    tar_sks = [ar for ar in args_tarSks if ar]
    cursorLoc = drawer.cursorLoc
    # 缺少目标
    if not tar_sks: # 方便地只为了现在不存在的 DrawDoubleNone() 使用模板, 通过向 args_tarSks 发送 `None, None`.
        col = drawer.dsCursorColor if drawer.dsIsColoredPoint else drawer.dsUniformColor
        isPair = len(args_tarSks)==2
        vec = Vec2((drawer.dsPointOffsetX*0.75, 0)) if (isPair)and(isClassicFlow) else Vec2((0.0, 0.0))
        if (isPair)and(drawer.dsIsDrawLine)and(drawer.dsIsAlwaysLine):
            DrawWorldStick(drawer, cursorLoc-vec, cursorLoc+vec, col, col)
        if drawer.dsIsDrawPoint:
            DrawVlWidePoint(drawer, cursorLoc-vec, col1=col, col2=col)
            if (isPair)and(isClassicFlow):
                DrawVlWidePoint(drawer, cursorLoc+vec, col1=col, col2=col)
        return
    # 经典流程线
    if (isClassicFlow)and(drawer.dsIsDrawLine)and(len(tar_sks)==2):
        tar1 = tar_sks[0]
        tar2 = tar_sks[1]
        if tar1.dir*tar2.dir<0: # 对于 VMLT, 为了不为它的两个套接字绘制, 它们在同一侧.
            if drawer.dsIsColoredLine:
                col1 = get_sk_color_safe(tar1.tar)
                col2 = get_sk_color_safe(tar2.tar)
            else:
                col1 = col2 = drawer.dsUniformColor
            DrawWorldStick(drawer, GetPosFromTar(tar1), GetPosFromTar(tar2), col1, col2)
    # 主要部分:
    isOne = len(tar_sks)==1

    for tar in tar_sks:
        if (drawer.dsIsDrawLine)and( (not isClassicFlow)or(isOne and drawer.dsIsAlwaysLine) ):
            if drawer.dsIsColoredLine:
                col1 = get_sk_color_safe(tar.tar)
                col2 = drawer.dsCursorColor if (isOne+(drawer.dsCursorColorAvailability-1))>0 else col1
            else:
                col1 = col2 = drawer.dsUniformColor
            DrawWorldStick(drawer, GetPosFromTar(tar), cursorLoc, col1, col2)
        if drawer.dsIsDrawSkArea:
            DrawVlSocketArea(drawer, tar.tar, tar.boxHeiBound, Color4(get_sk_color_safe(tar.tar)))
        if drawer.dsIsDrawPoint:
            DrawVlWidePoint(drawer, GetPosFromTar(tar), col1=Color4(clamp_color4(get_sk_color(tar.tar))), col2=Color4(get_sk_color_safe(tar.tar)))
    # 文本
    if isDrawText:  # 文本应该在所有其他 ^ 之上.
        tar_sks_in = [tar for tar in tar_sks if tar.dir < 0]
        tar_sks_out = [tar for tar in tar_sks if tar.dir > 0]
        x_offset = 0
        soldOverrideDir = abs(sideMarkHh) > 1 and (1 if sideMarkHh > 0 else -1)
        for list_tars in tar_sks_in, tar_sks_out:  # "累积", 天才! 意大利面条式代码的头疼消失了.
            hig = len(list_tars) - 1
            for cyc, tar in enumerate(list_tars):
                ofsY = 0.75*hig - 1.5*cyc
                dir = soldOverrideDir if soldOverrideDir else tar.dir * sideMarkHh
                x_offset = drawer.dsDistFromCursor * dir
                frameDim = DrawVlSkText(drawer, cursorLoc, (drawer.dsDistFromCursor * dir, ofsY - 0.5), tar)
                if (drawer.dsIsDrawMarker) and ((tar.tar.vl_sold_is_final_linked_cou) and (not isDrawMarkersMoreTharOne) or
                                               (tar.tar.vl_sold_is_final_linked_cou > 1)):
                    DrawVlMarker(drawer, cursorLoc, ofsHh=(frameDim[0] * dir, frameDim[1] * ofsY), col=get_sk_color_safe(tar.tar))
            # 绘制工具提示
            tar_show_name = copy.copy(tar)
            tar_show_name.soldText = _iface(tool_name).capitalize()
            if x_offset != 0:
                cursorLoc2 = cursorLoc.copy() + Vec2((0, 50))  # 额外绘制
                DrawVlSkText(drawer, cursorLoc2, (x_offset, 0), tar_show_name)
                # DrawVlSkText(drawer, cursorLoc, (20, 50), tar_show_name)
    # todo tool_name 的绘制和接口文本的绘制要分开,tool_name 要始终绘制,不要受 isDrawText 影响
    # todo 但是如果在下面绘制,批量连线时只绘制一根线(虽然正常连接)
    # if not isDrawText:      # 屎山的形成
    #     cursorLoc2 = cursorLoc.copy() + Vec2((0, 50))
    #     tar_show_name = copy.copy(tar)
    #     txt_col = node_tag_color(tar_sks[0].tar.node)
    #     DrawVlSkText(drawer, cursorLoc2, (0, 0), tar_show_name, tool_color=txt_col)
    #     # DrawWorldText(drawer, drawer.cursorLoc, (0, 0), tool_name, text_color=colTx, colBg=colTx)

    # 经典流程的光标下点
    if (isClassicFlow and isOne)and(drawer.dsIsDrawPoint):
        DrawVlWidePoint(drawer, cursorLoc, col1=drawer.dsCursorColor, col2=drawer.dsCursorColor)

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
            cls.rand = random.random()*32.0
            cls.time = 0.0
            cls.state = [0.5, 0.5, 0.5, 0.5]
            stNe.nsReg = stNe.nsReg if hasattr(stNe,'nsReg') else -2
            stNe.nsCur = stNe.nsReg
            stNe.handle = stNe.draw_handler_add(cls.CallbackDrawTest, (context,), 'WINDOW', 'POST_PIXEL')
        elif hasattr(stNe,'handle'):
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
        if stNe.nsCur!=stNe.nsReg:
            # 重新关闭并打开:
            prefs.dsIsTestDrawing = False
            # 该死的拓扑!
            prefs.dsIsTestDrawing = True
            return # 不知道是否必须退出.
        drawer = Drawer(context, context.space_data.cursor_location, context.preferences.system.dpi/72, prefs)
        cls.ctView2d = View2D.GetFields(context.region.view2d)
        drawer.worldZoom = cls.ctView2d.GetZoom()
        ##
        for cyc in range(4):
            noise = cls.GetNoise(cyc)
            fac = 1.0# if cyc<4 else (1.0 if noise>0 else cls.state[cyc])
            cls.state[cyc] = min(max(cls.state[cyc]+noise, 0.0), 1.0)*fac
        ##
        drawer.DrawPathLL(( (0,0),(1000,1000) ), (white_float4, white_float4), wid=0.0)
        for cycWid in range(9):
            ofsWid = cycWid*45
            for cycAl in range(4):
                col = (1,1,1,.25*(1+cycAl))
                ofsAl = cycAl*8
                for cyc5 in range(2):
                    ofs5x = 65*cyc5
                    ofs5y = 0.5*cyc5
                    drawer.DrawPathLL(( (100+ofs5x,100+ofsWid+ofsAl+ofs5y),(165+ofs5x,100+ofsWid+ofsAl+ofs5y) ), (col, col), wid=0.5*(1+cycWid))
        ##
        col = Color4(cls.state)
        drawer.cursorLoc = context.space_data.cursor_location
        cursorReg = drawer.VecUiViewToReg(drawer.cursorLoc)
        vec = cursorReg-Vec2((500,500))
        drawer.DrawRing((500,500), vec.length, wid=cursorReg.x/200, resl=max(3, int(cursorReg.y/20)), col=white_float4, spin=pi/2-atan2(vec.x, vec.y))
        # 混乱:
        center = Vec2((context.region.width/2, context.region.height/2))
        txt = "a.¯\_(- _-)_/¯"
        DrawFramedText(drawer, (300,300), (490,330), txt, siz=24, adj=(555-525)*-.2, colTx=white_float4, colFr=white_float4, colBg=white_float4)
        txt = bpy.context.window_manager.clipboard
        txt = txt[0] if txt else "a."
        DrawFramedText(drawer, (375,170), (400,280), txt, siz=24, adj=0, colTx=white_float4, colFr=white_float4, colBg=white_float4)
        DrawFramedText(drawer, (410,200), (435,250), txt, siz=24, adj=0, colTx=white_float4, colFr=white_float4, colBg=white_float4)
        #DrawFramedText(drawer, (445,200), (470,250), txt, siz=24, adj=0, colTx=white_4, colFr=white_4, colBg=white_4)
        loc = context.space_data.edit_tree.view_center
        col2 = col.copy()
        col2.w = max(0, (cursorReg.y-center.y/2)/150)
        DrawWorldText(drawer, loc, (-1, 2), "█GJKLPgjklp!?", text_color=col, colBg=col)
        DrawWorldText(drawer, loc, (-1, .33), "abcdefghijklmnopqrstuvwxyz", text_color=white_float4, colBg=col)
        DrawWorldText(drawer, loc, (0, -.33), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", text_color=col2, colBg=col2)
        vec = Vec2((0,-192/drawer.worldZoom))
        DrawWorldText(drawer, loc+vec, (0, 0), "абфуabfy", text_color=col, colBg=col)
        DrawWorldText(drawer, loc+vec, (200, 0), "аa", text_color=col, colBg=col)
        DrawWorldText(drawer, loc+vec, (300, 0), "абab", text_color=col, colBg=col)
        DrawWorldText(drawer, loc+vec, (500, 0), "ауay", text_color=col, colBg=col)
        DrawMarker(drawer, center+Vec2((-50,-60)), col, style=0)
        DrawMarker(drawer, center+Vec2((-100,-60)), col, style=1)
        DrawMarker(drawer, center+Vec2((-150,-60)), col, style=2)
        drawer.DrawPathLL( (center+Vec2((0,-60)), center+Vec2((100,-60))), (opaque_color4(col), opaque_color4(col)), wid=drawer.dsLineWidth )
        drawer.DrawPathLL( (center+Vec2((100,-60)), center+Vec2((200,-60))), (opaque_color4(col), opaque_color4(col, alpha=0.0)), wid=drawer.dsLineWidth )
        drawer.DrawWidePoint(center+Vec2((0,-60)), radHh=( (6*drawer.dsPointScale+1)**2+10 )**0.5, col1=Color4(opaque_color4(col)), col2=Color4(opaque_color4(col)))
        drawer.DrawWidePoint(center+Vec2((100,-60)), radHh=( (6*drawer.dsPointScale+1)**2+10 )**0.5, col1=col, col2=Color4(opaque_color4(col)))
        import gpu_extras.presets; gpu_extras.presets.draw_circle_2d((256,256),(1,1,1,1),10)
        ##
        cls.time += 0.01
        bpy.context.space_data.backdrop_zoom = bpy.context.space_data.backdrop_zoom # 火. 但有没有更"直接"的方法? 备受赞誉的 area.tag_redraw() 不起作用.
