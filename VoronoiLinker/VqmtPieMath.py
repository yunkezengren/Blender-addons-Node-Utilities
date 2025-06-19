from .关于翻译的函数 import *
from .关于节点的函数 import *
from .关于ui的函数 import *
from .关于颜色的函数 import *
from .VoronoiTool import *
from .关于sold的函数 import *
from .globals import *
from .common_class import *
from .common_func import *
from .draw_in_view import *
from .VoronoiTool import VoronoiOpTool
from .关于颜色的函数 import power_color4, get_sk_color
from .globals import is_blender4plus


class VqmtOpMain(VoronoiOpTool):
    bl_idname = 'node.voronoi_quick_math_main'
    bl_label = "Quick Math"
    operation: bpy.props.StringProperty()
    isCombo: bpy.props.BoolProperty(default=False)
    def modal(self, _context, event):
        #以前需要手动清除桥接数据，因为它会保留最后一次的记录。现在已经不需要了。
        return {'FINISHED'}
    def invoke(self, context, event):
        #注意：这里使用现在已不存在的ForseSetSelfNonePropToDefault()对于间接调用操作符已无法按预期工作。
        tree = context.space_data.edit_tree
        #if not tree: return {'CANCELLED'}
        if self.operation == "切换浮点/整数菜单":   #  这时候类型只会是下面两种
            _switch = {"VALUE":"INT", "INT":"VALUE"}
            VqmtData.qmSkType = _switch[VqmtData.qmSkType]
            color = power_color4(float_int_color[VqmtData.qmSkType], pw=2.2)
            Prefs().vaDecorColSkBack = color
            Prefs().vaDecorColSk = color

            VqmtData.test_bool = True
            _x = event.mouse_region_x
            _y = event.mouse_region_y - 120
            context.window.cursor_warp(_x, _y)
            bpy.ops.wm.call_menu_pie(name=VqmtPieMath.bl_idname)
            return {'RUNNING_MODAL'}
        match VqmtData.depth:
            case 0:
                if VqmtData.isSpeedPie:
                    VqmtData.list_speedPieDisplayItems = [ti[0] for ti in dict_vqmtQuickMathMain[VqmtData.qmSkType]]
                else:
                    VqmtData.depth += 1
                    VqmtData.dict_existingValues.clear()
                    if VqmtData.prefs.vqmtIncludeExistingValues:
                        for nd in tree.nodes:
                            if (VqmtData.qmSkType=='VECTOR')and(nd.type=='VECT_MATH')or(VqmtData.qmSkType=='VALUE')and(nd.type=='MATH'):
                                list_sks = []
                                canLk = False
                                canSk = False
                                for sk in nd.inputs:
                                    tgl = not sk.vl_sold_is_final_linked_cou
                                    if sk.enabled:
                                        canLk |= not tgl
                                        canSk |= tgl
                                    list_sks.append((sk, tgl))
                                if (canLk and canSk)and(length(list_sks)>1):
                                    #注意：那些什么都没有的，会被上层拓扑忽略
                                    key = (nd.operation, *[li[0].default_value if type(li[0].default_value)==float else li[0].default_value[:] for li in list_sks if li[1]])
                                    VqmtData.dict_existingValues[key] = (nd, list_sks)
            case 1:
                assert VqmtData.isSpeedPie #见上方 `+= 1`.
                VqmtData.list_speedPieDisplayItems = [ti[1] for ti in dict_vqmtQuickMathMain[VqmtData.qmSkType] if ti[0]==self.operation][0] #注意：元组是从生成器中提取的。
            case 2:
                if VqmtData.isFirstDone:
                    return {'FINISHED'}
                VqmtData.isFirstDone = True
                #只需要也显然只在这里进行记忆。在Tool中只有qqm和rlo。为方便起见，并且遵循rlo的逻辑，qqm不进行记忆。
                VqmtData.dict_lastOperation[VqmtData.qmTrueSkType] = self.operation
                return DoQuickMath(event, tree, self.operation)
        VqmtData.depth += 1
        bpy.ops.wm.call_menu_pie(name=VqmtPieMath.bl_idname)
        return {'RUNNING_MODAL'}

class VqmtPieMath(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_quick_math_pie'
    bl_label = "" #此处的文本将显示在饼菜单的中心。
    def draw(self, _context):
        def LyVqmAddOp(where: UILayout, text: str, icon='NONE'):
            #自动翻译已关闭，因为数学节点的原始操作也没有被翻译；至少对于俄语是这样。
            # label = text.replace("_"," ").capitalize()
            label = text.replace("_"," ").title()
            # 小王- 快速饼菜单按钮文本
            if text == "RADIANS":
                label = "To Randians"
            if text == "DEGREES":
                label = "To Degrees"
            where.operator(VqmtOpMain.bl_idname, text=label, icon=icon, translate=False).operation = text
        soldCanIcons = VqmtData.prefs.vqmtDisplayIcons
        def LyVqmAddItem(where: UILayout, txt, ico='NONE'):
            ly = where.row(align=VqmtData.pieAlignment==0)
            soldPdsc = VqmtData.pieDisplaySocketColor# if not VqmtData.isJustPie else 0
            if soldPdsc:
                # ly = ly.split(factor=( abs( (soldPdsc>0)-.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VqmtData.uiScale, align=True)
                ly = ly.split(factor=Color_Bar_Width * VqmtData.uiScale, align=True)  # 小王 饼菜单颜色条宽度
            if soldPdsc<0:
                ly.prop(VqmtData.prefs,'vaDecorColSk', text="")
            LyVqmAddOp(ly, text=txt, icon=ico if soldCanIcons else 'NONE')
            if soldPdsc>0:
                ly.prop(VqmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        if VqmtData.isSpeedPie:
            for li in VqmtData.list_speedPieDisplayItems:
                if not li: #用于快速饼菜单数据库中的空条目.
                    row = pie.row() #因为这样它虽然不显示任何东西，但仍会占用空间。
                    continue
                LyVqmAddOp(pie, li)
        else:
            isGap = VqmtData.pieAlignment<2
            uiUnitsX = 5.75*((VqmtData.pieScale-1)/2+1)
            def LyGetPieCol(where):
                col = where.column(align=isGap)
                col.ui_units_x = uiUnitsX
                col.scale_y = VqmtData.pieScale
                return col
            colLeft = LyGetPieCol(pie)
            colRight = LyGetPieCol(pie)
            colCenter = LyGetPieCol(pie)
            if VqmtData.pieDisplaySocketTypeInfo==1:
                colLabel = pie.column()
                box = colLabel.box()
                row = box.row(align=True)
                # _ TODO 如何对整数接口，浮点饼菜单就浮点的颜色
                _math_type = VqmtData.qmSkType
                _sk0 = VqmtData.sk0
                float_or_int = False
                if _sk0:
                    if VqmtData.qmSkType in ["VALUE", "INT"]:
                        float_or_int = True
                        # print("=="*20)
                        # print(VqmtData.qmSkType)
                        color = float_int_color[VqmtData.qmSkType]   # 只影响提示的接口颜色
                    else:
                        color=get_sk_color(_sk0)       # 原先情况：整数接口浮点饼是整数的颜色
                    row.template_node_socket(color=color)
                match VqmtData.qmSkType:
                    case 'VALUE':   txt = "txt_FloatQuickMath"  # ! 草
                    case 'INT':     txt = "txt_IntQuickMath"  # ! 草
                    case 'VECTOR':  txt = "txt_VectorQuickMath"  # ! 草
                    case 'BOOLEAN': txt = "txt_BooleanQuickMath"  # ! 草
                    case 'RGBA':    txt = "txt_ColorQuickMode"  # ! 草
                    case 'MATRIX':  txt = "txt_MatrixQuickMath"  # ! 草
                row.label(text=txt)
                row.alignment = 'CENTER'
                
                if float_or_int:
                    info = "浮点" if _math_type == "INT" else "整数"
                    box2 = colLabel.box()
                    row2 = box2.row(align=True)
                    row2.template_node_socket(color=floatIntColorInverse[_math_type])   # 只影响提示的接口颜色
                    row2.operator(VqmtOpMain.bl_idname, text="切换"+info).operation = "切换浮点/整数菜单"
                    box2.scale_y = 1.2
            ##
            def DrawForValVec(isVec):
                if True:
                    nonlocal colRight
                    dict_presets = dict_vqmtQuickPresets[VqmtData.qmSkType]
                    canPreset = (VqmtData.prefs.vqmtIncludeQuickPresets)and(dict_presets)
                    if canPreset:
                        colRight.ui_units_x *= 1.55
                    rowRigth = colRight.row()
                    colRight = rowRigth.column(align=isGap)
                    colRight.ui_units_x = uiUnitsX
                    if canPreset:
                        colRightQp = rowRigth.column(align=isGap)
                        colRightQp.ui_units_x = uiUnitsX/2
                        colRightQp.scale_y = VqmtData.prefs.vqmtPieScaleExtra/VqmtData.pieScale
                        for dk, dv in dict_presets.items():
                            ly = colRightQp.row() if VqmtData.pieAlignment else colRightQp
                            ly.operator(VqmtOpMain.bl_idname, text=dv.replace(" ",""), translate=False).operation = dk
                    ##
                    nonlocal colLeft
                    canExist = (VqmtData.prefs.vqmtIncludeExistingValues)and(VqmtData.dict_existingValues)
                    if canExist:
                        colLeft.ui_units_x *= 2.05
                    rowLeft = colLeft.row()
                    if canExist:
                        colLeftExt = rowLeft.column(align=isGap)
                        colLeftExt.ui_units_x = uiUnitsX
                        colLeftExt.scale_y = VqmtData.prefs.vqmtPieScaleExtra/VqmtData.pieScale
                        for nd, list_sks in list(VqmtData.dict_existingValues.values())[-16:]:
                            ly = colLeftExt.row() if VqmtData.pieAlignment else colLeftExt
                            rowItem = ly.row(align=True)
                            rowAdd = rowItem.row(align=True)
                            rowAdd.scale_x = 1.5
                            rowItem.separator()
                            rowVal = rowItem.row(align=True)
                            #rowVal.enabled = False
                            txt = ""
                            for sk, tgl in list_sks:
                                rowProp = rowVal.row(align=True)
                                txt += "|"
                                if tgl:
                                    if sk.enabled:
                                        if type(sk.default_value)==float:
                                            txt += str(sk.default_value)
                                        else:
                                            txt += str(tuple(sk.default_value))[1:-1]
                                        rowProp.column(align=True).prop(sk,'default_value', text="")
                                else:
                                    txt += "x"
                                    rowProp.operator(VqmtOpMain.bl_idname, text="")
                                    rowProp.enabled = False
                            rowAdd.ui_units_x = 2
                            rowAdd.operator(VqmtOpMain.bl_idname, text=str(nd.operation)[:3]).operation = nd.operation+txt
                    colLeft = rowLeft.column(align=isGap)
                    colLeft.ui_units_x = uiUnitsX
                ##
                LyVqmAddItem(colRight,'ADD','ADD')
                LyVqmAddItem(colRight,'SUBTRACT','REMOVE')
                ##
                LyVqmAddItem(colRight,'MULTIPLY','SORTBYEXT')
                LyVqmAddItem(colRight,'DIVIDE','FIXED_SIZE') #ITALIC  FIXED_SIZE
                ##
                colRight.separator()
                LyVqmAddItem(colRight, 'MULTIPLY_ADD')
                LyVqmAddItem(colRight, 'ABSOLUTE')
                colRight.separator()
                for li in ('SINE','COSINE','TANGENT'):
                    LyVqmAddItem(colCenter, li, 'FORCE_HARMONIC')
                if not isVec:
                    for li in ('POWER','SQRT','EXPONENT','LOGARITHM','INVERSE_SQRT','PINGPONG'):
                        LyVqmAddItem(colRight, li)
                    colRight.separator()
                    LyVqmAddItem(colRight, 'RADIANS')
                    LyVqmAddItem(colRight, 'DEGREES')
                    LyVqmAddItem(colLeft, 'FRACT', 'IPO_LINEAR')
                    for li in ('ARCTANGENT','ARCSINE','ARCCOSINE'):
                        LyVqmAddItem(colCenter, li, 'RNA')
                    for li in ('ARCTAN2','SINH','COSH','TANH'):
                        LyVqmAddItem(colCenter, li)
                else:
                    for li in ('SCALE','NORMALIZE','LENGTH','DISTANCE'):
                        LyVqmAddItem(colRight, li)
                    colRight.separator()
                    LyVqmAddItem(colLeft, 'FRACTION', 'IPO_LINEAR')
                LyVqmAddItem(colLeft,'FLOOR','IPO_CONSTANT')
                LyVqmAddItem(colLeft,'CEIL')
                LyVqmAddItem(colLeft,'MAXIMUM','NONE') #SORT_DESC  TRIA_UP_BAR
                LyVqmAddItem(colLeft,'MINIMUM','NONE') #SORT_ASC  TRIA_DOWN_BAR
                for li in ('MODULO', 'FLOORED_MODULO', 'SNAP', 'WRAP'):
                    LyVqmAddItem(colLeft, li)
                colLeft.separator()
                if not isVec:
                    for li in ('GREATER_THAN','LESS_THAN','TRUNC','SIGN','SMOOTH_MAX','SMOOTH_MIN','ROUND','COMPARE'):
                        LyVqmAddItem(colLeft, li)
                else:
                    LyVqmAddItem(colLeft,'DOT_PRODUCT',  'LAYER_ACTIVE')
                    LyVqmAddItem(colLeft,'CROSS_PRODUCT','ORIENTATION_LOCAL') #OUTLINER_DATA_EMPTY  ORIENTATION_LOCAL  EMPTY_ARROWS
                    LyVqmAddItem(colLeft,'PROJECT',      'CURVE_PATH') #SNAP_OFF  SNAP_ON  MOD_SIMPLIFY  CURVE_PATH
                    LyVqmAddItem(colLeft,'FACEFORWARD',  'ORIENTATION_NORMAL')
                    LyVqmAddItem(colLeft,'REFRACT',      'NODE_MATERIAL') #MOD_OFFSET  NODE_MATERIAL
                    LyVqmAddItem(colLeft,'REFLECT',      'INDIRECT_ONLY_OFF') #INDIRECT_ONLY_OFF  INDIRECT_ONLY_ON
            def DrawForBool():
                LyVqmAddItem(colRight,'AND')
                LyVqmAddItem(colRight,'OR')
                LyVqmAddItem(colRight,'NOT')
                LyVqmAddItem(colLeft,'NAND')
                LyVqmAddItem(colLeft,'NOR')
                LyVqmAddItem(colLeft,'XOR')
                LyVqmAddItem(colLeft,'XNOR')
                LyVqmAddItem(colCenter,'IMPLY')
                LyVqmAddItem(colCenter,'NIMPLY')
            def DrawForMatrix():
                LyVqmAddItem(colRight,'FunctionNodeMatrixMultiply')
                LyVqmAddItem(colRight,'FunctionNodeInvertMatrix')
                LyVqmAddItem(colRight,'FunctionNodeMatrixDeterminant')
                LyVqmAddItem(colLeft,'FunctionNodeTransformPoint')
                LyVqmAddItem(colLeft,'FunctionNodeTransformDirection')
                LyVqmAddItem(colLeft,'FunctionNodeProjectPoint')
            def DrawForCol():
                for li in ('LIGHTEN','DARKEN','SCREEN','DODGE','LINEAR_LIGHT','SOFT_LIGHT','OVERLAY','BURN'):
                    LyVqmAddItem(colRight, li)
                for li in ('MIX', 'ADD','SUBTRACT','MULTIPLY','DIVIDE','DIFFERENCE','EXCLUSION'):
                    LyVqmAddItem(colLeft, li)
                for li in ('VALUE','SATURATION','HUE','COLOR'):
                    LyVqmAddItem(colCenter, li)
            def DrawForInt():
                LyVqmAddItem(colRight,'ADD','ADD')
                LyVqmAddItem(colRight,'SUBTRACT','REMOVE')
                LyVqmAddItem(colRight,'MULTIPLY','SORTBYEXT')
                LyVqmAddItem(colRight,'DIVIDE','FIXED_SIZE')
                colRight.separator()
                LyVqmAddItem(colRight, 'MULTIPLY_ADD')
                LyVqmAddItem(colRight, 'ABSOLUTE')
                for li in ("POWER", "NEGATE"):
                    LyVqmAddItem(colRight, li)
                for li in ("MODULO", "FLOORED_MODULO", "SIGN", "DIVIDE_FLOOR", "DIVIDE_CEIL", "DIVIDE_ROUND", "GCD", "LCM"):
                    LyVqmAddItem(colLeft, li)
                for li in ("MINIMUM", "MAXIMUM"):
                    LyVqmAddItem(colCenter, li)
            match VqmtData.qmSkType:
                case 'VALUE'|'VECTOR': DrawForValVec(VqmtData.qmSkType=='VECTOR')
                case 'BOOLEAN': DrawForBool()
                case 'RGBA': DrawForCol()
                case 'INT':  DrawForInt()
                case 'MATRIX': DrawForMatrix()
