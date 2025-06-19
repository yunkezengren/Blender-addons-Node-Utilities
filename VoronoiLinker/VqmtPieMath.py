float_int_color = {"INT": (0.35, 0.55, 0.36, 1), "VALUE": (0.63, 0.63, 0.63, 1)}
floatIntColorInverse = {"INT": (0.63, 0.63, 0.63, 1), "VALUE": (0.35, 0.55, 0.36, 1)}
def DoQuickMath(event, tree, operation, isCombo=False):
    txt = dict_vqmtEditorNodes[VqmtData.qmSkType].get(tree.bl_idname, "")
    if not txt: #Если нет в списке, то этот нод не существует (по задумке списка) в этом типе редактора => "смешивать" нечем, поэтому выходим.
        return {'CANCELLED'}
    #Ядро быстрой математики, добавить нод и создать линки:
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=not VqmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    preset = operation.split("|")
    isPreset = length(preset)>1
    if isPreset:
        operation = preset[0]
    if VqmtData.qmSkType!='RGBA': #Ох уж этот цвет.
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
        #Теперь существует justPieCall, а значит пришло время скрывать значение первого сокета (но нужда в этом только для вектора).
        # if VqmtData.qmSkType=='VECTOR':
        #     aNd.inputs[0].hide_value = True
        #Идея с event.shift гениальна. Изначально ради одиночного линка во второй сокет, но благодаря визуальному поиску ниже, может и менять местами и два линка.
        bl4ofs = 2*gt_blender4*(tree.bl_idname in {'ShaderNodeTree','GeometryNodeTree'})
        skInx = aNd.inputs[0] if VqmtData.qmSkType!='RGBA' else aNd.inputs[-2-bl4ofs] #"Inx", потому что пародия на int "index", но потом понял, что можно сразу в сокет для линковки далее.
        if event.shift:
            for sk in aNd.inputs:
                if (sk!=skInx)and(sk.enabled):
                    if sk.type==skInx.type:
                        skInx = sk
                        break
        if VqmtData.sk0:
            NewLinkHhAndRemember(VqmtData.sk0, skInx)
            if VqmtData.sk1:
                #Второй ищется "визуально"; сделано ради операции 'SCALE'.
                for sk in aNd.inputs: #Ищется сверху вниз. Потому что ещё и 'MulAdd'.
                    if (sk.enabled)and(not sk.is_linked): #Заметка: "aNd" новосозданный; и паек нет. Поэтому is_linked.
                        #Ох уж этот скейл; единственный с двумя сокетами разных типов.
                        if (sk.type==skInx.type)or(operation=='SCALE'): #Искать одинаковый по типу. Актуально для RGBA Mix.
                            NewLinkHhAndRemember(VqmtData.sk1, sk)
                            break #Нужно соединить только в первый попавшийся, иначе будет соединено во все (например у 'MulAdd').
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
    #Установить значение по умолчанию для второго сокета (большинство нули). Нужно для красоты; и вообще это математика.
    #Заметка: Нод вектора уже создаётся по нулям, так что для него обнулять без нужды.
    tup_default = dict_vqmtDefaultDefault[VqmtData.qmSkType]
    if VqmtData.qmSkType!='RGBA':
        for cyc, sk in enumerate(aNd.inputs):
            #Здесь нет проверок на видимость и линки, пихать значение насильно. Потому что я так захотел.
            sk.default_value = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)[cyc]
    else: #Оптимизация для экономии в dict_vqmtDefaultValueOperation.
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
    #Скрыть все сокеты по запросу. На покерфейсе, ибо залинкованные сокеты всё равно не скроются; и даже без проверки 'sk.enabled'.
    if VqmtData.canProcHideSks: #Для justPieCall нет нужды и могут быть случайные нажатия, для qqm вообще не по концепции.
        if event.alt: #Удобненько получается для основного назначения, можно даже не отпускать Shift Alt.
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
        #Раньше нужно было очищать мост вручную, потому что он оставался равным последней записи. Сейчас уже не нужно.
        return {'FINISHED'}
    def invoke(self, context, event):
        #Заметка: Здесь использование ныне несуществующего ForseSetSelfNonePropToDefault() уже не работает задуманным образом для непрямого вызова оператора.
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
                                    #Заметка: те, у кого ничего нет, игнорируются выщестоящей топологией
                                    key = (nd.operation, *[li[0].default_value if type(li[0].default_value)==float else li[0].default_value[:] for li in list_sks if li[1]])
                                    VqmtData.dict_existingValues[key] = (nd, list_sks)
            case 1:
                assert VqmtData.isSpeedPie #См. ^ `+= 1`.
                VqmtData.list_speedPieDisplayItems = [ti[1] for ti in dict_vqmtQuickMathMain[VqmtData.qmSkType] if ti[0]==self.operation][0] #Заметка: Вычленяется кортеж из генератора.
            case 2:
                if VqmtData.isFirstDone:
                    return {'FINISHED'}
                VqmtData.isFirstDone = True
                #Запоминать нужно только и очевидно только здесь. В Tool только qqm и rlo. Для qqm не запоминается для удобства, и следованию логики rlo.
                VqmtData.dict_lastOperation[VqmtData.qmTrueSkType] = self.operation
                return DoQuickMath(event, tree, self.operation)
        VqmtData.depth += 1
        bpy.ops.wm.call_menu_pie(name=VqmtPieMath.bl_idname)
        return {'RUNNING_MODAL'}

class VqmtPieMath(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_quick_math_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, _context):
        def LyVqmAddOp(where: UILayout, text: str, icon='NONE'):
            #Автоматический перевод выключен, ибо оригинальные операции у нода математики тоже не переводятся; по крайней мере для Русского.
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
                if not li: #Для пустых записей в базе данных для быстрого пирога.
                    row = pie.row() #Ибо благодаря этому отображается никаким, но при этом занимает место.
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
