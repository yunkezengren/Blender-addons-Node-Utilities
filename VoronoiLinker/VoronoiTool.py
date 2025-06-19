from time import perf_counter, perf_counter_ns
from builtins import len as length # 我超爱三个字母的变量名.没有像"len"这样的名字, 我会感到非常伤心和孤独... 😭 还有 'Vector.length' 也是.
import bpy, ctypes, rna_keymap_ui, bl_keymap_utils
import blf, gpu, gpu_extras.batch
from math import pi, cos, sin
from mathutils import Vector as Vec
Vec2 = Color4 = Vec

from time import perf_counter, perf_counter_ns
from pprint import pprint
from bpy.types import (NodeSocket, UILayout, View2D, Area)

from .关于节点的函数 import GetNearestSocketsFtg, GetNearestNodesFtg, RestoreCollapsedNodes, SolderSkLinks
from .draw_in_view import DrawDebug, TemplateDrawNodeFull
from .C_Structure import RectBase
from .common_class import TryAndPass


class VoronoiOpTool(bpy.types.Operator):
    bl_options = {'UNDO'} # 手动创建的链接可以撤销, 所以在 VL 中也应如此. 对所有工具都一样.
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' # 不知道为什么需要这个, 但还是留着吧.

class VoronoiToolFillers: #-1
    usefulnessForCustomTree = None
    usefulnessForUndefTree = None
    usefulnessForNoneTree = None
    canDrawInAddonDiscl = None
    canDrawInAppearance = None
    def CallbackDrawTool(self, drata): pass
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): pass
    def ModalTool(self, event, prefs): pass
    #def MatterPurposePoll(self): return None
    def MatterPurposeTool(self, event, prefs, tree): pass
    def InitToolPre(self, event): return {}
    def InitTool(self, event, prefs, tree): return {}
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs): pass
    @classmethod
    def BringTranslations(cls): pass

class VoronoiToolRoot(VoronoiOpTool, VoronoiToolFillers): #0
    usefulnessForUndefTree = False
    usefulnessForNoneTree = False
    canDrawInAddonDiscl = True
    canDrawInAppearance = False
    # 点击节点编辑器总是不可避免的, 那里有节点, 所以对于所有工具
    isPassThrough: bpy.props.BoolProperty(name="Pass through node selecting", default=False, description="Clicking over a node activates selection, not the tool")
    def CallbackDrawRoot(self, drata, context):
        if drata.whereActivated!=context.space_data: # 需要只在活动的编辑器中绘制, 而不是在所有打开相同树的编辑器中绘制.
            return
        drata.worldZoom = self.ctView2d.GetZoom() # 每次都从 EdgePan 和鼠标滚轮获取. 以前可以一次性焊接.
        if self.prefs.dsIsFieldDebug:
            DrawDebug(self, drata)
        if self.tree: # 现在对于没有树的情况可以不显示任何迹象; 由于拓扑结构的头疼问题以及在插件树中传递热键时工具的跳过问题而关闭 (?).
            self.CallbackDrawTool(drata)
    def ToolGetNearestNodes(self, includePoorNodes=False, cur_x_off=0):
        self.cursorLoc.x += cur_x_off    # 唤起位置偏移
        return GetNearestNodesFtg(self.tree.nodes[:], self.cursorLoc, self.uiScale, includePoorNodes)
    def ToolGetNearestSockets(self, nd, cur_x_off=0):
        self.cursorLoc.x += cur_x_off    #     唤起位置偏移
        return GetNearestSocketsFtg(nd, self.cursorLoc, self.uiScale)
    def NextAssignmentRoot(self, flag):
        if self.tree:
            try:
                self.NextAssignmentTool(flag, self.prefs, self.tree)
            except:
                EdgePanData.isWorking = False # 现在只对 VLT 有效. 也许应该做个 ~self.ErrorToolProc, 并在 VLT 中 "退后一步".
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
                raise
    def ModalMouseNext(self, event, prefs):
        match event.type:
            case 'MOUSEMOVE':
                self.NextAssignmentRoot(False)
            case self.kmi.type|'ESC':
                if event.value=='RELEASE':
                    return True
        return False
    def modal(self, context, event):
        context.area.tag_redraw()
        if num:=(event.type=='WHEELUPMOUSE')-(event.type=='WHEELDOWNMOUSE'):
            self.ctView2d.cur.Zooming(self.cursorLoc, 1.0-num*0.15)
        self.ModalTool(event, self.prefs)
        if not self.ModalMouseNext(event, self.prefs):
            return {'RUNNING_MODAL'}
        #* 工具的结束从这里开始 *
        EdgePanData.isWorking = False
        if event.type=='ESC': # 这正是 Escape 键应该做的.
            return {'CANCELLED'}
        with TryAndPass(): # 它可能已经被删除了, 参见第二个这样的情况.
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
        tree = self.tree
        if not tree:
            return {'FINISHED'}
        RestoreCollapsedNodes(tree.nodes)
        if (tree)and(tree.bl_idname=='NodeTreeUndefined'): # 如果来自某个插件的节点树消失了, 那么剩下的就是 NodeUndefined 和 NodeSocketUndefined.
            return {'CANCELLED'} # 通过 API 无法创建到 SocketUndefined 的链接, 在这个树里也没什么可做的; 所以退出.
        ##
        if not self.MatterPurposePoll():
            return {'CANCELLED'}
        if result:=self.MatterPurposeTool(event, self.prefs, tree):
            return result
        return {'FINISHED'}
    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        self.tree = tree
        editorBlid = context.space_data.tree_type # 无需 `self.`?.
        self.isInvokeInClassicTree = IsClassicTreeBlid(editorBlid)
        if not(self.usefulnessForCustomTree or self.isInvokeInClassicTree):
            return {'PASS_THROUGH'} #'CANCELLED'?.
        if (not self.usefulnessForUndefTree)and(editorBlid=='NodeTreeUndefined'):
            return {'CANCELLED'} # 为了不绘制而离开.
        if not(self.usefulnessForNoneTree or tree):
            return {'FINISHED'}
        # 对所有工具相同的跳过选择处理
        if (self.isPassThrough)and(tree)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): # 检查树是第二位的, 为了美学优化.
            # 如果调用工具的热键与取消选择的热键相同, 那么上面一行选择的节点在交接后会重新取消选择 (但仍然是活动的).
            # 因此, 对于这种情况, 需要取消选择, 以便再次切换回已选择的节点.
            tree.nodes.active.select = False # 但没有条件, 对所有情况都适用. 因为 ^ 否则将永远是选择而不切换; 我没有想法如何处理这种情况.
            return {'PASS_THROUGH'}
        ##
        self.kmi = GetOpKmi(self, event)
        if not self.kmi:
            return {'CANCELLED'} # 如果总体上出了问题, 或者操作符是通过布局按钮调用的.
        # 如果在 keymap 调用操作符时未指定其属性, 它们会从上次调用中读取; 所以需要将它们设置回默认值.
        # 尽早这样做是有意义的; 对 VQMT 和 VEST 有效.
        for li in self.rna_type.properties:
            if li.identifier!='rna_type':
                # 注意: 判断是否在 kmi 中设置 -- `kmi.properties[li.identifier]` 的存在.
                setattr(self, li.identifier, getattr(self.kmi.properties, li.identifier)) # 为了这个我不得不反向工程 Blender 并进行调试. 原来是这么简单..
        ##
        self.prefs = Prefs() # "原来是这么简单".
        self.uiScale = context.preferences.system.dpi/72
        self.cursorLoc: Vec2 = context.space_data.cursor_location # 这是 class Vector, 通过引用复制; 所以可以在这里设置(绑定)一次, 就不用担心了.
        self.drata = VlDrawData(context, self.cursorLoc, self.uiScale, self.prefs)
        SolderThemeCols(context.preferences.themes[0].node_editor) # 和 fontId 一样; 虽然在大多数情况下主题在整个会话期间不会改变.
        self.region = context.region
        self.ctView2d = View2D.GetFields(context.region.view2d)
        if self.prefs.vIsOverwriteZoomLimits:
            self.ctView2d.minzoom = self.prefs.vOwZoomMin
            self.ctView2d.maxzoom = self.prefs.vOwZoomMax
        ##
        if result:=self.InitToolPre(event): # 对于 'Pre' 返回某些内容不太重要.
            return result
        if result:=self.InitTool(event, self.prefs, tree): # 注意: 参见拓扑结构: 不返回任何东西等同于返回 `{'RUNNING_MODAL'}`.
            return result
        EdgePanInit(self, context.area)
        ##
        self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(self.CallbackDrawRoot, (self.drata, context,), 'WINDOW', 'POST_PIXEL')
        if tree: # 注意: 参见本地拓扑结构, 工具本身可以, 但每个工具都明确地对缺失的树禁用了.
            SolderSkLinks(self.tree)
            SaveCollapsedNodes(tree.nodes)
            self.NextAssignmentRoot(True) # 原来只需要在 modal_handler_add() 之前移动它. #https://projects.blender.org/blender/blender/issues/113479
        ##
        context.area.tag_redraw() # 需要在激活时绘制找到的; 本地顺序不重要.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class VoronoiToolSk(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def InitToolPre(self, event):
        self.fotagoSk = None

class VoronoiToolPairSk(VoronoiToolSk): #2
    isCanBetweenFields: bpy.props.BoolProperty(name="Can between fields", default=True, description="Tool can connecting between different field types")
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1)
    def SkBetweenFieldsCheck(self, sk1, sk2):
        # 注意: 考虑到此函数的目的和名称, sk1 和 sk2 无论如何都应该是来自字段, 且仅来自字段.
        return (sk1.type in set_utilTypeSkFields)and( (self.isCanBetweenFields)and(sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
    def InitToolPre(self, event):
        self.fotagoSk0 = None
        self.fotagoSk1 = None


class VoronoiToolTripleSk(VoronoiToolPairSk): #3
    def ModalTool(self, event, prefs):
        if (self.isStartWithModf)and(not self.canPickThird): # 谁会真的通过按下和释放某个修饰键来切换到选择第三个套接字呢?.
            # 因为这代价太高了; 既然选择了没有修饰键的热键, 那就满足于有限的功能吧. 或者自己动手.
            self.canPickThird = not(event.shift or event.ctrl or event.alt)
    def InitToolPre(self, event):
        self.fotagoSk2 = None
        self.canPickThird = False
        self.isStartWithModf = (event.shift)or(event.ctrl)or(event.alt)

class VoronoiToolNd(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawNodeFull(drata, self.fotagoNd, tool_name="隐藏选项")
    def MatterPurposePoll(self):
        return not not self.fotagoNd
    def InitToolPre(self, event):
        self.fotagoNd = None

class VoronoiToolPairNd(VoronoiToolSk): #2
    def MatterPurposePoll(self):
        return self.fotagoNd0 and self.fotagoNd1
    def InitToolPre(self, event):
        self.fotagoNd0 = None
        self.fotagoNd1 = None

class VoronoiToolAny(VoronoiToolSk, VoronoiToolNd): #2
    @staticmethod
    def TemplateDrawAny(drata, ftg, *, cond, tool_name=""):
        if cond:
            TemplateDrawNodeFull(drata, ftg, tool_name=tool_name)
        else:
            TemplateDrawSksToolHh(drata, ftg, tool_name=tool_name)      # 绘制工具提示
    def MatterPurposePoll(self):
        return self.fotagoAny
    def InitToolPre(self, event):
        self.fotagoAny = None


class EdgePanData:
    area: Area = None # 本应是 'context', 但它总是 None.
    ctCur: RectBase = None
    # 快速凑合的:
    isWorking = False
    view2d: View2D = None
    cursorPos: Vec2 = Vec2((0,0))
    uiScale = 1.0
    center: Vec2 = Vec2((0,0))
    delta = 0.0   # 哦, 这些增量.
    zoomFac = 0.5
    speed = 1.0

def EdgePanTimer():
    delta = perf_counter()-EdgePanData.delta
    vec = EdgePanData.cursorPos*EdgePanData.uiScale
    field0 = Vec2(EdgePanData.view2d.view_to_region(vec.x, vec.y, clip=False))
    zoomWorld = (EdgePanData.view2d.view_to_region(vec.x+1000, vec.y, clip=False)[0]-field0.x)/1000
    # 再来点光线步进:
    field1 = field0-EdgePanData.center
    field2 = Vec2(( abs(field1.x), abs(field1.y) ))
    field2 = field2-EdgePanData.center+Vec2((10, 10)) # 稍微减小光标紧贴屏幕边缘的边界.
    field2 = Vec2(( max(field2.x, 0), max(field2.y, 0) ))
    ##
    xi, yi, xa, ya = EdgePanData.ctCur.GetRaw()
    speedZoomSize = Vec2((xa-xi, ya-yi))/2.5*delta # 没有 delta 时是 125.
    field1 = field1.normalized()*speedZoomSize*((zoomWorld-1)/1.5+1)*EdgePanData.speed*EdgePanData.uiScale
    if (field2.x!=0)or(field2.y!=0):
        EdgePanData.ctCur.TranslateScaleFac((field1.x, field1.y), fac=EdgePanData.zoomFac)
    EdgePanData.delta = perf_counter() # 在下一次进入前 "发送到未知处".
    EdgePanData.area.tag_redraw()
    return 0.0 if EdgePanData.isWorking else None

def EdgePanInit(self: VoronoiToolRoot, area: Area):
    EdgePanData.area = area
    EdgePanData.ctCur = self.ctView2d.cur
    EdgePanData.isWorking = True
    EdgePanData.cursorPos = self.cursorLoc
    EdgePanData.uiScale = self.uiScale
    EdgePanData.view2d = self.region.view2d
    EdgePanData.center = Vec2((self.region.width/2, self.region.height/2))
    EdgePanData.delta = perf_counter() #..还有 "轻微边界".
    EdgePanData.zoomFac = 1.0-self.prefs.vEdgePanFac
    EdgePanData.speed = self.prefs.vEdgePanSpeed
    bpy.app.timers.register(EdgePanTimer, first_interval=0.0)
