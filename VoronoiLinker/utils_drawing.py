from .utils_node import node_abs_loc
from .utils_color import (Color4, power_color4, clamp_color4, opaque_color4, get_color_black_alpha,
                      get_sk_color_safe, get_sk_color)
from builtins import len as length
import gpu, gpu_extras, blf, copy
from mathutils import Vector as Vec2
from math import pi, cos, sin
from .C_Structure import View2D

from .utils_translate import *
from .utils_node import *
from .utils_ui import *
from .utils_color import *
from .VoronoiTool import *
from .utils_solder import *
from .globals import *
from .forward_class import *
from .forward_func import *
from .utils_drawing import *


tup_whiteCol4 = (1.0, 1.0, 1.0, 1.0)

class VlDrawData():
    shaderLine = None
    shaderArea = None
    worldZoom = 0.0
    def DrawPathLL(self, vpos, vcol, *, wid):
        gpu.state.blend_set('ALPHA') # 绘制文本会重置 alpha 标记, 因此每次都设置.
        self.shaderLine.bind()
        self.shaderLine.uniform_float('lineWidth', wid)
        self.shaderLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
        gpu_extras.batch.batch_for_shader(self.shaderLine, type='LINE_STRIP', content={'pos':vpos, 'color':vcol}).draw(self.shaderLine)

    def DrawAreaFanLL(self, vpos, col):
        gpu.state.blend_set('ALPHA')
        self.shaderArea.bind()
        self.shaderArea.uniform_float('color', col)
        #todo2v6 弄清楚如何为多边形也做平滑处理.
        gpu_extras.batch.batch_for_shader(self.shaderArea, type='TRI_FAN', content={'pos':vpos}).draw(self.shaderArea)
    def VecUiViewToReg(self, vec):
        vec = vec*self.uiScale
        return Vec2( self.view_to_region(vec.x, vec.y, clip=False) )
    ##
    def DrawRectangle(self, bou1, bou2, col):
        self.DrawAreaFanLL(( (bou1[0],bou1[1]), (bou2[0],bou1[1]), (bou2[0],bou2[1]), (bou1[0],bou2[1]) ), col)
    def DrawCircle(self, loc, rad, *, resl=54, col=tup_whiteCol4):
        #第一个顶点自豪地在中心, 其他顶点在圆周上. 需要平滑伪影朝向中心, 而不是斜向某个方向
        self.DrawAreaFanLL(( (loc[0],loc[1]), *[ (loc[0]+rad*cos(cyc*2.0*pi/resl), loc[1]+rad*sin(cyc*2.0*pi/resl)) for cyc in range(resl+1) ] ), col)
    def DrawRing(self, pos, rad, *, wid, resl=16, col=tup_whiteCol4, spin=0.0):
        vpos = tuple( ( rad*cos(cyc*2*pi/resl+spin)+pos[0], rad*sin(cyc*2*pi/resl+spin)+pos[1] ) for cyc in range(resl+1) )
        self.DrawPathLL(vpos, (col,)*(resl+1), wid=wid)
    def DrawWidePoint(self, loc, *, radHh, col1=Color4(tup_whiteCol4), col2=tup_whiteCol4, resl=54):
        colFacOut = Color4((0.5, 0.5, 0.5, 0.4))
        self.DrawCircle(loc, radHh+3.0, resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh,     resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh/1.5, resl=resl, col=col2)
    def __init__(self, context, cursorLoc, uiScale, prefs):
        # self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')        # 作者
        self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        # POLYLINE_FLAT_COLOR, POLYLINE_SMOOTH_COLOR, POLYLINE_UNIFORM_COLOR
        # FLAT_COLOR, SMOOTH_COLOR, [UNIFORM_COLOR]
        self.shaderArea = gpu.shader.from_builtin('UNIFORM_COLOR')
        #self.shaderLine.uniform_float('lineSmooth', True) # 无需, 默认为 True.
        self.fontId = blf.load(prefs.dsFontFile) # 持续设置字体是为了在更换主题时字体不消失.
        ##
        self.whereActivated = context.space_data
        self.uiScale = uiScale
        self.view_to_region = context.region.view2d.view_to_region
        self.cursorLoc = cursorLoc
        ##
        for pr in prefs.bl_rna.properties:
            if pr.identifier.startswith("ds"):
                setattr(self, pr.identifier, getattr(prefs, pr.identifier))
        match prefs.dsDisplayStyle:
            case 'CLASSIC':    self.dsFrameDisplayType = 2
            case 'SIMPLIFIED': self.dsFrameDisplayType = 1
            case 'ONLY_TEXT':  self.dsFrameDisplayType = 0
        ##
        self.dsUniformColor = Color4(power_color4(self.dsUniformColor))
        self.dsUniformNodeColor = Color4(power_color4(self.dsUniformNodeColor))
        self.dsCursorColor = Color4(power_color4(self.dsCursorColor))

def DrawWorldStick(drata, pos1, pos2, col1, col2):
    drata.DrawPathLL( (drata.VecUiViewToReg(pos1), drata.VecUiViewToReg(pos2)), (col1, col2), wid=drata.dsLineWidth )
def DrawVlSocketArea(drata, sk, bou, col):
    loc = node_abs_loc(sk.node)
    pos1 = drata.VecUiViewToReg(Vec2( (loc.x,               bou[0]) ))
    pos2 = drata.VecUiViewToReg(Vec2( (loc.x+sk.node.width, bou[1]) ))
    if drata.dsIsColoredSkArea:
        col[3] = drata.dsSocketAreaAlpha # 注意: 这里总是收到不透明颜色; 所以可以覆盖而不是乘.
    else:
        col = drata.dsUniformColor
    drata.DrawRectangle(pos1, pos2, col)
def DrawVlWidePoint(drata, loc, *, col1=Color4(tup_whiteCol4), col2=tup_whiteCol4, resl=54, forciblyCol=False): #"forciblyCol" 只用于 DrawDebug.
    if not(drata.dsIsColoredPoint or forciblyCol):
        col1 = col2 = drata.dsUniformColor
    drata.DrawWidePoint(drata.VecUiViewToReg(loc), radHh=( (6*drata.dsPointScale*drata.worldZoom)**2+10 )**0.5, col1=col1, col2=col2, resl=resl)

def DrawMarker(drata, loc, col, *, style):
    fac = get_color_black_alpha(col, pw=1.5)*0.625 #todo1v6 标记颜色在亮色和黑色之间看起来不美观; 需要想点办法.
    colSh = (fac, fac, fac, 0.5) # 阴影
    colHl = (0.65, 0.65, 0.65, max(max(col[0],col[1]),col[2])*0.9/(3.5, 5.75, 4.5)[style]) # 透明白色描边
    colMt = (col[0], col[1], col[2], 0.925) # 彩色底
    resl = (16, 16, 5)[style]
    ##
    drata.DrawRing((loc[0]+1.5, loc[1]+3.5), 9.0, wid=3.0, resl=resl, col=colSh)
    drata.DrawRing((loc[0]-3.5, loc[1]-5.0), 9.0, wid=3.0, resl=resl, col=colSh)
    def DrawMarkerBacklight(spin, col):
        resl = (16, 4, 16)[style]
        drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
        drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
    DrawMarkerBacklight(pi/resl, colHl) # 标记绘制时有“像素孔”伪影。通过旋转的重复绘制来修复它们。
    DrawMarkerBacklight(0.0,     colHl) # 但因此需要将白色描边的 alpha 减半。
    drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=1.0, resl=resl, col=colMt)
    drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=1.0, resl=resl, col=colMt)
def DrawVlMarker(drata, loc, *, ofsHh, col):
    vec = drata.VecUiViewToReg(loc)
    dir = 1 if ofsHh[0]>0 else -1
    ofsX = dir*( (20*drata.dsIsDrawText+drata.dsDistFromCursor)*1.5+drata.dsFrameOffset )+4
    col = col if drata.dsIsColoredMarker else drata.dsUniformColor
    DrawMarker(drata, (vec[0]+ofsHh[0]+ofsX, vec[1]+ofsHh[1]), col, style=drata.dsMarkerStyle)

def DrawFramedText(drata, pos1, pos2, txt, *, siz, adj, colTx, colFr, colBg):
    pos1x = ps1x = pos1[0]
    pos1y = ps1y = pos1[1]
    pos2x = ps2x = pos2[0]
    pos2y = ps2y = pos2[1]
    blur = 5
    # 文本框:
    match drata.dsFrameDisplayType:
        case 2: # 漂亮的边框
            gradResl = 12
            gradStripHei = (pos2y-pos1y)/gradResl
            # 透明渐变背景:
            LFx = lambda x,a,b: ((x+b)/(b+1))**0.6*(1-a)+a
            for cyc in range(gradResl):
                drata.DrawRectangle( (pos1x, pos1y+cyc*gradStripHei),
                                     (pos2x, pos1y+cyc*gradStripHei+gradStripHei),
                                     (colBg[0]/2, colBg[1]/2, colBg[2]/2, LFx(cyc/gradResl,0.2,0.05)*colBg[3]) )
            # 明亮的主描边:
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), (colFr,)*5, wid=1.0) # 天啊, 如果 colFr[0]==-1, 结果会包含复数. 那里发生了什么?
            # 额外的柔和描边 (连同角落), 增加美感:
            ps1x += .25
            ps1y += .25
            ps2x -= .25
            ps2y -= .25
            ofs = 2.0
            vpos = (  (ps1x, ps1y-ofs),  (ps2x, ps1y-ofs),  (ps2x+ofs, ps1y),  (ps2x+ofs, ps2y),
                      (ps2x, ps2y+ofs),  (ps1x, ps2y+ofs),  (ps1x-ofs, ps2y),  (ps1x-ofs, ps1y),  (ps1x, ps1y-ofs)  )
            drata.DrawPathLL( vpos, ((colFr[0], colFr[1], colFr[2], 0.375),)*9, wid=1.0)
        case 1: # 给那些不喜欢漂亮边框的人. 他们不喜欢什么呢?.
            drata.DrawRectangle( (pos1x, pos1y), (pos2x, pos2y), (colBg[0]/2.4, colBg[1]/2.4, colBg[2]/2.4, 0.8*colBg[3]) )
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), ((0.1, 0.1, 0.1, 0.95),)*5, wid=1.0)
    # 文本:
    fontId = drata.fontId
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
    if drata.dsIsAllowTextShadow:
        col = drata.dsShadowCol
        blf.shadow_offset(fontId, drata.dsShadowOffset[0], drata.dsShadowOffset[1])
        blf.shadow(fontId, (0, 3, 5)[drata.dsShadowBlur], col[0], col[1], col[2], col[3])
    else:
        blf.disable(fontId, blf.SHADOW)
    blf.color(fontId, colTx[0], colTx[1], colTx[2], 1.0)
    blf.draw(fontId, txt)
    return (pos2x-pos1x, pos2y-pos1y)

def DrawWorldText(drata, pos, ofsHh, text, *, colText, colBg, fontSizeOverwrite=0): # fontSizeOverwrite 仅用于 vptRvEeSksHighlighting.
    siz = drata.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite
    blf.size(drata.fontId, siz)
    # 不计算“实际文本”的高度, 因为那样每个框每次的高度都会不同.
    # 需要特殊字符作为“通用情况”来覆盖最大高度. 其他字符用于可能比“█”高的特殊字体.
    dimDb = (blf.dimensions(drata.fontId, text)[0], blf.dimensions(drata.fontId, "█GJKLPgjklp!?")[1])
    pos = drata.VecUiViewToReg(pos)
    frameOffset = drata.dsFrameOffset
    ofsGap = 10
    pos = (pos[0]-(dimDb[0]+frameOffset+ofsGap)*(ofsHh[0]<0)+(frameOffset+1)*(ofsHh[0]>-1), pos[1]+frameOffset)
    # 我已经完全忘了我搞了什么鬼以及它是如何工作的; 但它工作了 -- 这就很好, "能工作就别动":
    placePosY = round( (dimDb[1]+frameOffset*2)*ofsHh[1] ) # 不四舍五入, 水平线的美感会消失.
    pos1 = (pos[0]+ofsHh[0]-frameOffset,               pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofsHh[0]+ofsGap+dimDb[0]+frameOffset, pos[1]+placePosY+dimDb[1]+frameOffset)
    ##
    # 这个更像影响全体 这里使得Ctrl Shift E / Ctrl E / Alt E 等显示太浅
    # return DrawFramedText(drata, pos1, pos2, text, siz=siz, adj=dimDb[1]*drata.dsManualAdjustment, colTx=power_color4(colText, pw=1/1.975), colFr=power_color4(colBg, pw=1/1.5), colBg=colBg)
    return DrawFramedText(drata, pos1, pos2, text, siz=siz, adj=dimDb[1]*drata.dsManualAdjustment, colTx=colText, colFr=colBg, colBg=colBg)   # 绘制颜色加深

def DrawVlSkText(drata, pos, ofsHh, ftg, *, fontSizeOverwrite=0): # 注意: `pos` 总是为了 drata.cursorLoc, 但请参见 vptRvEeSksHighlighting.
    if not drata.dsIsDrawText:
        return (1, 0) #'1' 需要用于保存标记位置的方向信息.
    if drata.dsIsColoredText:
        colText = get_sk_color_safe(ftg.tar)
        colBg = clamp_color4(get_sk_color(ftg.tar))
    else:
        colText = colBg = drata.dsUniformColor
    return DrawWorldText(drata, pos, ofsHh, ftg.soldText, colText=colText, colBg=colBg, fontSizeOverwrite=fontSizeOverwrite)

def DrawDebug(self, drata):
    def DebugTextDraw(pos, txt, r, g, b):
        blf.size(0,18)
        blf.position(0, pos[0]+10,pos[1], 0)
        blf.color(0, r,g,b,1.0)
        blf.draw(0, txt)
    DebugTextDraw(drata.VecUiViewToReg(drata.cursorLoc), "Cursor position here.", 1, 1, 1)
    if not self.tree:
        return
    col = Color4((1.0, 0.5, 0.5, 1.0))
    list_ftgNodes = self.ToolGetNearestNodes(cur_x_off=0)
    if not list_ftgNodes:
        return
    DrawWorldStick(drata, drata.cursorLoc, list_ftgNodes[0].pos, col, col)
    for cyc, li in enumerate(list_ftgNodes):
        DrawVlWidePoint(drata, li.pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(li.pos), str(cyc)+" Node goal here", col.x, col.y, col.z)
    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(list_ftgNodes[0].tar)
    if list_ftgSksIn:
        col = Color4((0.5, 1, 0.5, 1))
        DrawVlWidePoint(drata, list_ftgSksIn[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksIn[0].pos), "Nearest socketIn here", 0.5, 1, 0.5)
    if list_ftgSksOut:
        col = Color4((0.5, 0.5, 1, 1))
        DrawVlWidePoint(drata, list_ftgSksOut[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksOut[0].pos), "Nearest socketOut here", 0.75, 0.75, 1)

def TemplateDrawNodeFull(drata, ftgNd, *, side=1, tool_name=""): # 模板重新思考过了; 很好. 现在它变得像其他所有的一样了.. 至少没有旧版本中的意大利面条式代码了.
    #todo1v6 模板只有一个 ftg, 没有分层, 两个调用会从一个绘制点和线到另一个的文本上方.
    if ftgNd:
        ndTar = ftgNd.tar
        if drata.dsIsColoredNodes: # 嗯.. 现在节点终于有颜色了; 感谢 ctypes.
            colLn = GetNdThemeNclassCol(ndTar)
            # colLn[0] += 0.5
            # colLn[1] += 0.5
            # colLn[2] += 0.5
            colPt = colLn
            colTx = colLn
            # print(f"{colLn = }")
            # 这里也能更改颜色
            # colTx = drata.dsUniformNodeColor
        else:
            colUnc = drata.dsUniformNodeColor
            colLn = colUnc if drata.dsIsColoredLine else drata.dsUniformColor
            colPt = colUnc if drata.dsIsColoredPoint else drata.dsUniformColor
            # colTx = colUnc if drata.dsIsColoredText else drata.dsUniformColor
            colTx = colUnc
        if drata.dsIsDrawLine:
            DrawWorldStick(drata, drata.cursorLoc, ftgNd.pos, colLn, colLn)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, ftgNd.pos, col1=colPt, col2=colPt)
        if (drata.dsIsDrawText)and(drata.dsIsDrawNodeNameLabel):
            txt = ndTar.label if ndTar.label else ndTar.bl_rna.name
            if ndTar.type == "GROUP":
                txt = ndTar.node_tree.name   # 优化-绘制节点组名字
            else:
                txt = ndTar.label
            
            DrawWorldText(drata, drata.cursorLoc, (drata.dsDistFromCursor*side, -0.5), txt, colText=colTx, colBg=colTx)
            DrawWorldText(drata, drata.cursorLoc, (drata.dsDistFromCursor*side, 1   ), tool_name, colText=colTx, colBg=colTx)
            # # 额外绘制
            # print(f"{txt = }")
            # print(f"{(drata.dsDistFromCursor*side, -0.5) = }")
            # DrawWorldText(drata, drata.cursorLoc, (0, 1), tool_name, colText=colTx, colBg=colTx)
    elif drata.dsIsDrawPoint:
        col = tup_whiteCol4 # 唯一剩下的未定义颜色. 'dsCursorColor' 在这里按设计不适合 (整个插件都是为了套接字, 对吧?).
        DrawVlWidePoint(drata, drata.cursorLoc, col1=Color4(col), col2=col)

# 高级套接字绘制模板. 现在名称中有“Sk”, 因为节点已完全进入 VL.
# 在旧版本中的硬核之后, 使用这个模板简直是享受 (甚至不要看那里, 那里简直是地狱).
def TemplateDrawSksToolHh(drata, *args_ftgSks, sideMarkHh=1, isDrawText=True, 
                          isClassicFlow=False, isDrawMarkersMoreTharOne=False, tool_name=""): # 模板重新思考过了, 万岁. 感觉上并没有变得更好.
    def GetPosFromFtg(ftg):
        return ftg.pos+Vec2((drata.dsPointOffsetX*ftg.dir, 0.0))
    list_ftgSks = [ar for ar in args_ftgSks if ar]
    cursorLoc = drata.cursorLoc
    # 缺少目标
    if not list_ftgSks: # 方便地只为了现在不存在的 DrawDoubleNone() 使用模板, 通过向 args_ftgSks 发送 `None, None`.
        col = drata.dsCursorColor if drata.dsIsColoredPoint else drata.dsUniformColor
        isPair = length(args_ftgSks)==2
        vec = Vec2((drata.dsPointOffsetX*0.75, 0)) if (isPair)and(isClassicFlow) else Vec2((0.0, 0.0))
        if (isPair)and(drata.dsIsDrawLine)and(drata.dsIsAlwaysLine):
            DrawWorldStick(drata, cursorLoc-vec, cursorLoc+vec, col, col)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, cursorLoc-vec, col1=col, col2=col)
            if (isPair)and(isClassicFlow):
                DrawVlWidePoint(drata, cursorLoc+vec, col1=col, col2=col)
        return
    # 经典流程线
    if (isClassicFlow)and(drata.dsIsDrawLine)and(length(list_ftgSks)==2):
        ftg1 = list_ftgSks[0]
        ftg2 = list_ftgSks[1]
        if ftg1.dir*ftg2.dir<0: # 对于 VMLT, 为了不为它的两个套接字绘制, 它们在同一侧.
            if drata.dsIsColoredLine:
                col1 = get_sk_color_safe(ftg1.tar)
                col2 = get_sk_color_safe(ftg2.tar)
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg1), GetPosFromFtg(ftg2), col1, col2)
    # 主要部分:
    isOne = length(list_ftgSks)==1
    
    # print("." * 100)
    # print(list_ftgSks)
    for ftg in list_ftgSks:
        # print(f"{type(ftg) = }")
        # print("ftg.__dict__")
        # pprint(ftg.__dict__)      # ftg.pos 这是接口的位置
        if (drata.dsIsDrawLine)and( (not isClassicFlow)or(isOne and drata.dsIsAlwaysLine) ):
            if drata.dsIsColoredLine:
                col1 = get_sk_color_safe(ftg.tar)
                col2 = drata.dsCursorColor if (isOne+(drata.dsCursorColorAvailability-1))>0 else col1
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg), cursorLoc, col1, col2)
        if drata.dsIsDrawSkArea:
            DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Color4(get_sk_color_safe(ftg.tar)))
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, GetPosFromFtg(ftg), col1=Color4(clamp_color4(get_sk_color(ftg.tar))), col2=Color4(get_sk_color_safe(ftg.tar)))
    # 文本
    if isDrawText: # 文本应该在所有其他 ^ 之上.
        list_ftgSksIn = [ftg for ftg in list_ftgSks if ftg.dir<0]
        list_ftgSksOut = [ftg for ftg in list_ftgSks if ftg.dir>0]
        x_offset = 0
        soldOverrideDir = abs(sideMarkHh)>1 and (1 if sideMarkHh>0 else -1)
        for list_ftgs in list_ftgSksIn, list_ftgSksOut: # "累积", 天才! 意大利面条式代码的头疼消失了.
            hig = length(list_ftgs)-1
            for cyc, ftg in enumerate(list_ftgs):
                ofsY = 0.75*hig-1.5*cyc
                dir = soldOverrideDir if soldOverrideDir else ftg.dir*sideMarkHh
                x_offset = drata.dsDistFromCursor*dir
                frameDim = DrawVlSkText(drata, cursorLoc, (drata.dsDistFromCursor*dir, ofsY-0.5), ftg)
                if (drata.dsIsDrawMarker)and( (ftg.tar.vl_sold_is_final_linked_cou)and(not isDrawMarkersMoreTharOne)or(ftg.tar.vl_sold_is_final_linked_cou>1) ):
                    DrawVlMarker(drata, cursorLoc, ofsHh=(frameDim[0]*dir, frameDim[1]*ofsY), col=get_sk_color_safe(ftg.tar))
            # 绘制工具提示
            ftg_show_name = copy.copy(ftg)
            ftg_show_name.soldText = tool_name.capitalize()
            # print(f"{x_offset = }")
            if x_offset != 0:
                cursorLoc2 = cursorLoc.copy() + Vec((0, 50))     # 额外绘制
                DrawVlSkText(drata, cursorLoc2, (x_offset, 0), ftg_show_name)
                # DrawVlSkText(drata, cursorLoc, (20, 50), ftg_show_name)
    # 经典流程的光标下点
    if (isClassicFlow and isOne)and(drata.dsIsDrawPoint):
        DrawVlWidePoint(drata, cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor)

#Todo0SF "滑帧"的头疼!! Debug, Collapse, Alt, 以及所有地方.

class TestDraw:
    @classmethod
    def GetNoise(cls, w):
        from mathutils.noise import noise
        return noise((cls.time, w, cls.rand))
    @classmethod
    def Toggle(cls, context, tgl):
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
    def CallbackDrawTest(cls, context):
        from math import atan2
        stNe = bpy.types.SpaceNodeEditor
        if stNe.nsCur!=stNe.nsReg:
            # 重新关闭并打开:
            Prefs().dsIsTestDrawing = False
            # 该死的拓扑!
            Prefs().dsIsTestDrawing = True
            return # 不知道是否必须退出.
        drata = VlDrawData(context, context.space_data.cursor_location, context.preferences.system.dpi/72, Prefs())
        cls.ctView2d = View2D.GetFields(context.region.view2d)
        drata.worldZoom = cls.ctView2d.GetZoom()
        ##
        for cyc in range(4):
            noise = cls.GetNoise(cyc)
            fac = 1.0# if cyc<4 else (1.0 if noise>0 else cls.state[cyc])
            cls.state[cyc] = min(max(cls.state[cyc]+noise, 0.0), 1.0)*fac
        ##
        drata.DrawPathLL(( (0,0),(1000,1000) ), (tup_whiteCol4, tup_whiteCol4), wid=0.0)
        for cycWid in range(9):
            ofsWid = cycWid*45
            for cycAl in range(4):
                col = (1,1,1,.25*(1+cycAl))
                ofsAl = cycAl*8
                for cyc5 in range(2):
                    ofs5x = 65*cyc5
                    ofs5y = 0.5*cyc5
                    drata.DrawPathLL(( (100+ofs5x,100+ofsWid+ofsAl+ofs5y),(165+ofs5x,100+ofsWid+ofsAl+ofs5y) ), (col, col), wid=0.5*(1+cycWid))
        ##
        col = Color4(cls.state)
        drata.cursorLoc = context.space_data.cursor_location
        cursorReg = drata.VecUiViewToReg(drata.cursorLoc)
        vec = cursorReg-Vec2((500,500))
        drata.DrawRing((500,500), vec.length, wid=cursorReg.x/200, resl=max(3, int(cursorReg.y/20)), col=tup_whiteCol4, spin=pi/2-atan2(vec.x, vec.y))
        # 混乱:
        center = Vec2((context.region.width/2, context.region.height/2))
        txt = "a.¯\_(- _-)_/¯"
        DrawFramedText(drata, (300,300), (490,330), txt, siz=24, adj=(555-525)*-.2, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        txt = bpy.context.window_manager.clipboard
        txt = txt[0] if txt else "a."
        DrawFramedText(drata, (375,170), (400,280), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        DrawFramedText(drata, (410,200), (435,250), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        #DrawFramedText(drata, (445,200), (470,250), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        loc = context.space_data.edit_tree.view_center
        col2 = col.copy()
        col2.w = max(0, (cursorReg.y-center.y/2)/150)
        DrawWorldText(drata, loc, (-1, 2), "█GJKLPgjklp!?", colText=col, colBg=col)
        DrawWorldText(drata, loc, (-1, .33), "abcdefghijklmnopqrstuvwxyz", colText=tup_whiteCol4, colBg=col)
        DrawWorldText(drata, loc, (0, -.33), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", colText=col2, colBg=col2)
        vec = Vec2((0,-192/drata.worldZoom))
        DrawWorldText(drata, loc+vec, (0, 0), "абфуabfy", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (200, 0), "аa", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (300, 0), "абab", colText=col, colBg=col)
        DrawWorldText(drata, loc+vec, (500, 0), "ауay", colText=col, colBg=col)
        DrawMarker(drata, center+Vec2((-50,-60)), col, style=0)
        DrawMarker(drata, center+Vec2((-100,-60)), col, style=1)
        DrawMarker(drata, center+Vec2((-150,-60)), col, style=2)
        drata.DrawPathLL( (center+Vec2((0,-60)), center+Vec2((100,-60))), (opaque_color4(col), opaque_color4(col)), wid=drata.dsLineWidth )
        drata.DrawPathLL( (center+Vec2((100,-60)), center+Vec2((200,-60))), (opaque_color4(col), opaque_color4(col, al=0.0)), wid=drata.dsLineWidth )
        drata.DrawWidePoint(center+Vec2((0,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=Color4(opaque_color4(col)), col2=Color4(opaque_color4(col)))
        drata.DrawWidePoint(center+Vec2((100,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=col, col2=Color4(opaque_color4(col)))
        import gpu_extras.presets; gpu_extras.presets.draw_circle_2d((256,256),(1,1,1,1),10)
        ##
        cls.time += 0.01
        bpy.context.space_data.backdrop_zoom = bpy.context.space_data.backdrop_zoom # 火. 但有没有更“直接”的方法? 备受赞誉的 area.tag_redraw() 不起作用.