


float_int_color = {"INT": (0.35, 0.55, 0.36, 1), "VALUE": (0.63, 0.63, 0.63, 1)}
floatIntColorInverse = {"INT": (0.63, 0.63, 0.63, 1), "VALUE": (0.35, 0.55, 0.36, 1)}
def DoQuickMath(event, tree, operation, isCombo=False):
    txt = dict_vqmtEditorNodes[VqmtData.qmSkType].get(tree.bl_idname, "")
    if not txt: #如果不在列表中，则表示此节点在该类型的编辑器中不存在（根据列表的设计）=> 没有什么可以“混合”的，所以退出。
        return {'CANCELLED'}
    #快速数学的核心，添加节点并创建连接：
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=not VqmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    preset = operation.split("|")
    isPreset = length(preset)>1
    if isPreset:
        operation = preset[0]
    if VqmtData.qmSkType!='RGBA': #哦，这个颜色。
        aNd.operation = operation
    else:
        if aNd.bl_idname=='ShaderNodeMix':
            aNd.data_type = 'RGBA'
            aNd.clamp_factor = False
        aNd.blend_type = operation
        aNd.inputs[0].default_value = 1.0
        aNd.inputs[0].hide = operation in {'ADD','SUBTRACT','DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION','VALUE','SATURATION','HUE','COLOR'}
    ##
    if not isPreset:
        #现在存在justPieCall，这意味着是时候隐藏第一个接口的值了（但这只对向量有必要）。
        # if VqmtData.qmSkType=='VECTOR':
        #     aNd.inputs[0].hide_value = True
        #使用event.shift的想法很棒。最初是为了单个连接到第二个接口，但由于下面的可视化搜索，它也可以交换两个连接。
        bl4ofs = 2*gt_blender4*(tree.bl_idname in {'ShaderNodeTree','GeometryNodeTree'})
        skInx = aNd.inputs[0] if VqmtData.qmSkType!='RGBA' else aNd.inputs[-2-bl4ofs] #"Inx"，因为它是对整数“index”的模仿，但后来我意识到可以直接使用socket进行后续连接。
        if event.shift:
            for sk in aNd.inputs:
                if (sk!=skInx)and(sk.enabled):
                    if sk.type==skInx.type:
                        skInx = sk
                        break
        if VqmtData.sk0:
            NewLinkHhAndRemember(VqmtData.sk0, skInx)
            if VqmtData.sk1:
                #第二个是“可视化地”搜索的；这是为了'SCALE'（缩放）操作。
                for sk in aNd.inputs: #从上到下搜索。因为还有'MulAdd'（乘加）。
                    if (sk.enabled)and(not sk.is_linked): #注意：“aNd”是新创建的；并且没有连接。因此使用is_linked。
                        #哦，这个缩放；唯一一个具有两种不同类型接口的。
                        if (sk.type==skInx.type)or(operation=='SCALE'): #寻找相同类型的。对 RGBA Mix 有效。
                            NewLinkHhAndRemember(VqmtData.sk1, sk)
                            break #只需要连接到找到的第一个，否则会连接到所有（例如在'MulAdd'中）。
            elif isCombo:
                for sk in aNd.inputs:
                    if (sk.type==skInx.type)and(not sk.is_linked):
                        NewLinkHhAndRemember(VqmtData.sk0, sk)
                        break
            if VqmtData.sk2:
                for sk in aNd.outputs:
                    if (sk.enabled)and(not sk.hide):
                        NewLinkHhAndRemember(sk, VqmtData.sk2)
                        break
    #为第二个接口设置默认值（大多数为零）。这是为了美观；而且这毕竟是数学运算。
    #注意：向量节点创建时已经为零，所以不需要再为它清零。
    tup_default = dict_vqmtDefaultDefault[VqmtData.qmSkType]
    if VqmtData.qmSkType!='RGBA':
        for cyc, sk in enumerate(aNd.inputs):
            #这里没有可见性和连接的检查，强制赋值。因为我就是这么想的。
            sk.default_value = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)[cyc]
    else: #为了节省dict_vqmtDefaultValueOperation中的空间而进行的优化。
        tup_col = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)
        aNd.inputs[-2-bl4ofs].default_value = tup_col[0]
        aNd.inputs[-1-bl4ofs].default_value = tup_col[1]
    ##
    if isPreset:
        for zp in zip(aNd.inputs, preset[1:]):
            if zp[1]:
                if zp[1]=="x":
                    if VqmtData.sk0:
                        NewLinkHhAndRemember(VqmtData.sk0, zp[0])
                else:
                    zp[0].default_value = eval(f"{zp[1]}")
    #根据请求隐藏所有接口。面无表情地做，因为已连接的接口反正也隐藏不了；甚至不用检查'sk.enabled'。
    if VqmtData.canProcHideSks: #对于justPieCall没必要，而且可能会有意外点击，对于qqm则完全不符合其设计理念。
        if event.alt: #对于主要用途来说很方便，甚至可以不用松开Shift Alt。
            for sk in aNd.inputs:
                sk.hide = True
    aNd.show_options = not VqmtData.isHideOptions
    return {'FINISHED'}
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
            color = PowerArr4(float_int_color[VqmtData.qmSkType], pw=2.2)
            pref().vaDecorColSkBack = color
            pref().vaDecorColSk = color

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
                        color=GetSkColorRaw(_sk0)       # 原先情况：整数接口浮点饼是整数的颜色
                    row.template_node_socket(color=color)
                match VqmtData.qmSkType:
                    case 'VALUE':   txt = txt_FloatQuickMath
                    case 'INT':     txt = txt_IntQuickMath
                    case 'VECTOR':  txt = txt_VectorQuickMath
                    case 'BOOLEAN': txt = txt_BooleanQuickMath
                    case 'RGBA':    txt = txt_ColorQuickMode
                    case 'MATRIX':  txt = txt_MatrixQuickMath
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