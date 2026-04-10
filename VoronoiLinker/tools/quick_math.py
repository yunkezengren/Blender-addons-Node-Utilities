import bpy
from ..base_tool import unhide_node_reassign, TemplateDrawSksToolHh, TripleSocketTool
from ..common_class import VqmtData
from ..common_func import DisplayMessage, SetPieData
from ..preference import pref
from ..globals import Cursor_X_Offset, float_int_color
from ..utils.color import get_sk_color_safe, power_color4
from ..utils.node import DoQuickMath, opt_tar_socket
from ..utils.solder import dict_skTypeHandSolderingColor
from ..utils.ui import draw_hand_split_prop, draw_panel_column

set_vqmtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}
fitVqmtRloDescr = "Bypassing the pie call, activates the last used operation for the selected socket type.\n"+\
                  "Searches for sockets only from an available previous operations that were performed for the socket type.\n"+\
                  "Just a pie call, and the fast fast math is not remembered as the last operations"
class NODE_OT_voronoi_quick_math(TripleSocketTool):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    bl_description = "A full-fledged branch from VMT. Quick and quick-quick math at speeds.\nHas additional mini-functionality. Also see \"Quick quick math\" in the layout."
    use_for_custom_tree = False
    can_draw_in_appearence = True
    quickOprFloat:         bpy.props.StringProperty(name="Float (quick)",  default="") #它们在前面, 以便在 kmi 中对齐显示.
    quickOprInt:           bpy.props.StringProperty(name="Int (quick)",  default="") #它们在前面, 以便在 kmi 中对齐显示.
    quickOprVector:        bpy.props.StringProperty(name="Vector (quick)", default="") #quick 在第二位, 以便在空间不足时显示第一个词, 所以不得不用括号括起来.
    isCanFromOne:          bpy.props.BoolProperty(name="Can from one socket", default=True)
    isRepeatLastOperation: bpy.props.BoolProperty(name="Repeat last operation", default=False, description=fitVqmtRloDescr) #嗯, qqm 四重奏现在迫使它们不断对齐.
    isHideOptions:         bpy.props.BoolProperty(name="Hide node options",   default=True)
    isPlaceImmediately:    bpy.props.BoolProperty(name="Place immediately",   default=False)
    quickOprBool:          bpy.props.StringProperty(name="Bool (quick)",   default="")
    quickOprColor:         bpy.props.StringProperty(name="Color (quick)",  default="")
    justPieCall:           bpy.props.IntProperty(name="Just call pie", default=0, min=0, max=5,
                                                 description="Call pie to add a node, bypassing the sockets selection.\n0–Disable.\n1–Float.\n2–Vector.\n3–Boolean.\n4–Color.\n5–Int")
    def callback_draw_tool(self, drata):
        TemplateDrawSksToolHh(drata, self.target_sk0, self.target_sk1, self.target_sk2, tool_name="Quick Math")
    def find_targets_tool(self, is_first_active, prefs, tree):
        if is_first_active:
            self.target_sk0 = None
        isNotCanPickThird = not self.canPickThird if prefs.vqmtIncludeThirdSk else True
        if isNotCanPickThird:
            self.target_sk1 = None
        for tar_nd in self.get_nearest_nodes(cur_x_off=Cursor_X_Offset):
            nd = tar_nd.tar
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=Cursor_X_Offset)
            if not tar_sks_out:
                continue
            #这个工具只触发字段输出.
            if is_first_active:
                isSucessOut = False
                for tar in tar_sks_out:
                    if not self.isRepeatLastOperation:
                        if not self.isQuickQuickMath:
                            if tar.tar.type in set_vqmtSkTypeFields:
                                self.target_sk0 = tar
                                isSucessOut = True
                                break
                        else: #对于 isQuickQuickMath, 只附加到明确指定操作的套接字类型.
                            match tar.tar.type:
                            # case 'VALUE'|'INT':         isSucessOut = self.quickOprFloat
                                case 'VALUE':         isSucessOut = self.quickOprFloat
                                # case 'INT':           isSucessOut = self.quickOprInt
                                case 'VECTOR' | "ROTATION": isSucessOut = self.quickOprVector
                                case 'BOOLEAN':             isSucessOut = self.quickOprBool
                                case 'RGBA':                isSucessOut = self.quickOprColor
                            if isSucessOut:
                                self.target_sk0 = tar
                                break
                    else:
                        isSucessOut = VqmtData.dict_lastOperation.get(tar.tar.type, '')
                        if isSucessOut:
                            self.target_sk0 = tar
                            break
                if not isSucessOut:
                    continue #寻找 is_first_active 的节点, 该节点将命中字段套接字.
                #对于下一个 `continue`, 因为如果接下来激活 continue 失败, 将会重新选择 is_first_active
                is_first_active = False #但考虑到当前的选择拓扑, 这没有必要.
            unhide_node_reassign(nd, self, cond=self.target_sk0, flag=True) #todo0NA 参见上面一行, 这个 'cond' 不应该来自 is_first_active.
            skOut0 = opt_tar_socket(self.target_sk0)
            if isNotCanPickThird:
                #对于第二个, 根据条件:
                if skOut0:
                    for tar in tar_sks_out:
                        if self.check_between_sk_fields(skOut0, tar.tar):
                            self.target_sk1 = tar
                            break
                    if not self.target_sk1:
                        continue #以便没有字段套接字的节点是透明的.
                    if (self.target_sk1)and(skOut0==self.target_sk1.tar): #检查是否是自我复制.
                        self.target_sk1 = None
                    unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
            else:
                self.target_sk2 = None #为了方便高级取消而清空.
                #对于第三个, 如果不是前两个的节点.
                skOut1 = opt_tar_socket(self.target_sk1)
                for tar in tar_sks_in:
                    skIn = tar.tar
                    if skIn.type in set_vqmtSkTypeFields:
                        tgl0 = (not skOut0)or(skOut0.node!=skIn.node)
                        tgl1 = (not skOut1)or(skOut1.node!=skIn.node)
                        if (tgl0)and(tgl1):
                            self.target_sk2 = tar
                            break
                unhide_node_reassign(nd, self, cond=self.target_sk2, flag=False)
            break
    def VqmSetPieData(self, prefs, col):
        SetPieData(self, VqmtData, prefs, col)
        VqmtData.isHideOptions = self.isHideOptions
        VqmtData.isPlaceImmediately = self.isPlaceImmediately
        VqmtData.depth = 0
        VqmtData.isFirstDone = False
    def modal_handle_mouse(self, event, prefs): #复制警报, VLT 也有一个.
        if event.type==prefs.vqmtRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState:
                self.find_targets_base(True)
                self.canPickThird = False #为有第三个套接字的工具添加重新选择功能, 总体上是个糟糕的主意; 工具的控制变得更难了.
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState:
                        self.find_targets_base(True)
                    else:
                        self.find_targets_base(False)
                case self.kmi.type|'ESC':
                    if event.value=='RELEASE':
                        return True
        return False
    def can_run(self):
        return (self.target_sk0)and(self.isCanFromOne or self.target_sk1)
    def run(self, event, prefs, tree):
        VqmtData.sk0 = self.target_sk0.tar
        VqmtData.sk1 = opt_tar_socket(self.target_sk1)
        VqmtData.sk2 = opt_tar_socket(self.target_sk2)
        VqmtData.qmSkType = VqmtData.sk0.type #注意: 只有字段套接字是更高级别的问题.
        VqmtData.qmTrueSkType = VqmtData.qmSkType #这个信息对于“最后的操作”是必需的.
        self.int_default_float = False
        match VqmtData.sk0.type:
        # case 'INT':      VqmtData.qmSkType = 'VALUE' #只有整数被剥夺了它自己的数学节点. 也许以后会添加?.
            case 'INT':
                # 为的是除了两个接口都是整数，一个接口是整数，默认浮点饼菜单
                if VqmtData.sk1:
                    if VqmtData.sk1.type=="INT":
                        VqmtData.qmSkType = 'INT'
                    if VqmtData.sk1.type=="VALUE":
                        VqmtData.qmSkType = 'VALUE'
                        self.int_default_float = True
                else:
                    # VqmtData.qmSkType = 'VALUE'   # 整数接口浮点饼
                    # self.int_default_float = True
                    VqmtData.qmSkType = 'INT'
            case 'ROTATION': VqmtData.qmSkType = 'VECTOR'
            # case 'MATRIX':   VqmtData.qmSkType = 'MATRIX'
            #case 'ROTATION': return {'FINISHED'} #但奇怪的是, 为什么与 RGBA 的链接被标记为不正确, 明明都是 Arr4... 那颜色为什么需要 alpha?
        match tree.bl_idname:
            case 'ShaderNodeTree':     VqmtData.qmSkType = {'BOOLEAN':'VALUE'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
            case 'GeometryNodeTree':   pass
            case 'CompositorNodeTree': VqmtData.qmSkType = {'BOOLEAN':'VALUE'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
            case 'TextureNodeTree':    VqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
        if self.isRepeatLastOperation:
            return DoQuickMath(event, tree, VqmtData.dict_lastOperation[VqmtData.qmTrueSkType])
        if self.isQuickQuickMath:
            match VqmtData.qmSkType:
                case 'VALUE':   opr = self.quickOprFloat
                case 'VECTOR':  opr = self.quickOprVector
                case 'BOOLEAN': opr = self.quickOprBool
                case 'RGBA':    opr = self.quickOprColor
                # case 'INT':     opr = self.quickOprInt
            return DoQuickMath(event, tree, opr)
        # print('这里只在绘制连线时调用一次,切换饼菜单不会刷新这里')
        self.VqmSetPieData(prefs, power_color4(get_sk_color_safe(VqmtData.sk0), pw=2.2))
        if self.int_default_float:     # 整数接口浮点饼
            color = power_color4(float_int_color["VALUE"], pw=2.2)
            pref().vaDecorColSkBack = color
            pref().vaDecorColSk = color
        VqmtData.isJustPie = False
        VqmtData.canProcHideSks = True
        bpy.ops.node.quick_math_sub('INVOKE_DEFAULT')
    def initialize(self, event, prefs, tree):
        self.repickState = False
        VqmtData.canProcHideSks = False #立即用于上面的两个 DoQuickMath 和下面的操作符.
        if self.justPieCall:
            match tree.bl_idname:
                case 'ShaderNodeTree' | 'CompositorNodeTree':
                    can = self.justPieCall in {1, 2, 4}
                case 'GeometryNodeTree':
                    can = True
                case 'TextureNodeTree':
                    can = self.justPieCall in {1, 4}
            if not can:
                txt_vqmtThereIsNothing = "There is nothing"  # ! 草
                DisplayMessage(self.bl_label, txt_vqmtThereIsNothing)
                return {'CANCELLED'}
            VqmtData.sk0 = None #为了完整性和 GetSkColor 而清空.
            VqmtData.sk1 = None
            VqmtData.sk2 = None
            VqmtData.qmSkType = ('VALUE','VECTOR','BOOLEAN','RGBA', 'INT')[self.justPieCall-1]
            self.VqmSetPieData(prefs, dict_skTypeHandSolderingColor[VqmtData.qmSkType])
            VqmtData.isJustPie = True
            bpy.ops.node.quick_math_sub('INVOKE_DEFAULT')
            return {'FINISHED'}
        self.isQuickQuickMath = not not( (self.quickOprFloat)or(self.quickOprVector)or(self.quickOprBool)or(self.quickOprColor) )
    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        draw_hand_split_prop(col, prefs,'vqmtIncludeThirdSk')
        tgl = prefs.vqmtPieType=='CONTROL'
        draw_hand_split_prop(col, prefs,'vqmtIncludeQuickPresets',   active=tgl)
        draw_hand_split_prop(col, prefs,'vqmtIncludeExistingValues', active=tgl)
        draw_hand_split_prop(col, prefs,'vqmtDisplayIcons',          active=tgl)
        draw_hand_split_prop(col, prefs,'vqmtRepickKey', link_btn=True)
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        #VoronoiMixerTool.__dict__['LyDrawInAppearance'].__func__(cls, colLy, prefs) #该死. 由于 @classmethod 而绕过. 但现在没必要了, 因为有了 vqmtPieScaleExtra.
        if p_col := draw_panel_column(colLy, "Quick Math Pie"):
            draw_hand_split_prop(p_col, prefs,'vqmtPieType')
            colProps = p_col.column(align=True)
            draw_hand_split_prop(colProps, prefs,'vqmtPieScale')
            # 预设(隐藏了) 比如 +-*/ 的 缩放,暂时用不到
            # draw_hand_split_prop(colProps, prefs,'vqmtPieScaleExtra')
            draw_hand_split_prop(colProps, prefs,'vqmtPieAlignment')
            draw_hand_split_prop(colProps, prefs,'vqmtPieSocketDisplayType')
            draw_hand_split_prop(colProps, prefs,'vqmtPieDisplaySocketColor')
            colProps.active = getattr(prefs,'vqmtPieType')=='CONTROL'

