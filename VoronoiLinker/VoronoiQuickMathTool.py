


set_vqmtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION', 'MATRIX'}
fitVqmtRloDescr = "Bypassing the pie call, activates the last used operation for the selected socket type.\n"+\
                  "Searches for sockets only from an available previous operations that were performed for the socket type.\n"+\
                  "Just a pie call, and the fast fast math is not remembered as the last operations"
class VoronoiQuickMathTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
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
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2, tool_name="Quick Math")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        isNotCanPickThird = not self.canPickThird if prefs.vqmtIncludeThirdSk else True
        if isNotCanPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)
            if not list_ftgSksOut:
                continue
            #这个工具只触发字段输出.
            if isFirstActivation:
                isSucessOut = False
                for ftg in list_ftgSksOut:
                    if not self.isRepeatLastOperation:
                        if not self.isQuickQuickMath:
                            if ftg.tar.type in set_vqmtSkTypeFields:
                                self.fotagoSk0 = ftg
                                isSucessOut = True
                                break
                        else: #对于 isQuickQuickMath, 只附加到明确指定操作的套接字类型.
                            match ftg.tar.type:
                                # case 'VALUE'|'INT':         isSucessOut = self.quickOprFloat
                                case 'VALUE':         isSucessOut = self.quickOprFloat
                                # case 'INT':           isSucessOut = self.quickOprInt
                                case 'VECTOR' | "ROTATION": isSucessOut = self.quickOprVector
                                case 'BOOLEAN':             isSucessOut = self.quickOprBool
                                case 'RGBA':                isSucessOut = self.quickOprColor
                            if isSucessOut:
                                self.fotagoSk0 = ftg
                                break
                    else:
                        isSucessOut = VqmtData.dict_lastOperation.get(ftg.tar.type, '')
                        if isSucessOut:
                            self.fotagoSk0 = ftg
                            break
                if not isSucessOut:
                    continue #寻找 isFirstActivation 的节点, 该节点将命中字段套接字.
                #对于下一个 `continue`, 因为如果接下来激活 continue 失败, 将会重新选择 isFirstActivation
                isFirstActivation = False #但考虑到当前的选择拓扑, 这没有必要.
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk0, flag=True) #todo0NA 参见上面一行, 这个 'cond' 不应该来自 isFirstActivation.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if isNotCanPickThird:
                #对于第二个, 根据条件:
                if skOut0:
                    for ftg in list_ftgSksOut:
                        if self.SkBetweenFieldsCheck(skOut0, ftg.tar):
                            self.fotagoSk1 = ftg
                            break
                    if not self.fotagoSk1:
                        continue #以便没有字段套接字的节点是透明的.
                    if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #检查是否是自我复制.
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            else:
                self.fotagoSk2 = None #为了方便高级取消而清空.
                #对于第三个, 如果不是前两个的节点.
                skOut1 = FtgGetTargetOrNone(self.fotagoSk1)
                for ftg in list_ftgSksIn:
                    skIn = ftg.tar
                    if skIn.type in set_vqmtSkTypeFields:
                        tgl0 = (not skOut0)or(skOut0.node!=skIn.node)
                        tgl1 = (not skOut1)or(skOut1.node!=skIn.node)
                        if (tgl0)and(tgl1):
                            self.fotagoSk2 = ftg
                            break
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
            break
    def VqmSetPieData(self, prefs, col):
        SetPieData(self, VqmtData, prefs, col)
        VqmtData.isHideOptions = self.isHideOptions
        VqmtData.isPlaceImmediately = self.isPlaceImmediately
        VqmtData.depth = 0
        VqmtData.isFirstDone = False
    def ModalMouseNext(self, event, prefs): #复制警报, VLT 也有一个.
        if event.type==prefs.vqmtRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState:
                self.NextAssignmentRoot(True)
                self.canPickThird = False #为有第三个套接字的工具添加重新选择功能, 总体上是个糟糕的主意; 工具的控制变得更难了.
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState:
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    if event.value=='RELEASE':
                        return True
        return False
    def MatterPurposePoll(self):
        return (self.fotagoSk0)and(self.isCanFromOne or self.fotagoSk1)
    def MatterPurposeTool(self, event, prefs, tree):
        VqmtData.sk0 = self.fotagoSk0.tar
        VqmtData.sk1 = FtgGetTargetOrNone(self.fotagoSk1)
        VqmtData.sk2 = FtgGetTargetOrNone(self.fotagoSk2)
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
            case 'ROTATION': VqmtData.qmSkType = 'VECTOR' #更有可能的是, 四元数的数学节点会先出现.
            case 'MATRIX':   VqmtData.qmSkType = 'MATRIX' #更有可能的是, 四元数的数学节点会先出现.
            #case 'ROTATION': return {'FINISHED'} #但奇怪的是, 为什么与 RGBA 的链接被标记为不正确, 明明都是 Arr4... 那颜色为什么需要 alpha?
        match tree.bl_idname:
            case 'ShaderNodeTree':     VqmtData.qmSkType = {'BOOLEAN':'VALUE'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
            case 'GeometryNodeTree':   pass
            case 'CompositorNodeTree': VqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
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
        # self.VqmSetPieData(prefs, PowerArr4(GetSkColSafeTup4(VqmtData.sk0), pw=2.2))
        self.VqmSetPieData(prefs, PowerArr4(GetSkColSafeTup4(VqmtData.sk0), pw=2.2))
        if self.int_default_float:     # 整数接口浮点饼
            color = PowerArr4(float_int_color["VALUE"], pw=2.2)
            pref().vaDecorColSkBack = color
            pref().vaDecorColSk = color
        VqmtData.isJustPie = False
        VqmtData.canProcHideSks = True
        bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
    def InitTool(self, event, prefs, tree):
        self.repickState = False
        VqmtData.canProcHideSks = False #立即用于上面的两个 DoQuickMath 和下面的操作符.
        if self.justPieCall:
            match tree.bl_idname:
                case 'ShaderNodeTree': can = self.justPieCall in {1,2,4}
                case 'GeometryNodeTree': can = True
                case 'CompositorNodeTree'|'TextureNodeTree': can = self.justPieCall in {1,4}
            if not can:
                DisplayMessage(self.bl_label, txt_vqmtThereIsNothing)
                return {'CANCELLED'}
            VqmtData.sk0 = None #为了完整性和 GetSkCol 而清空.
            VqmtData.sk1 = None
            VqmtData.sk2 = None
            VqmtData.qmSkType = ('VALUE','VECTOR','BOOLEAN','RGBA', 'INT')[self.justPieCall-1]
            self.VqmSetPieData(prefs, dict_skTypeHandSolderingColor[VqmtData.qmSkType])
            VqmtData.isJustPie = True
            bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
            return {'FINISHED'}
        self.isQuickQuickMath = not not( (self.quickOprFloat)or(self.quickOprVector)or(self.quickOprBool)or(self.quickOprColor) )
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vqmtIncludeThirdSk')
        tgl = prefs.vqmtPieType=='CONTROL'
        LyAddLeftProp(col, prefs,'vqmtIncludeQuickPresets',   active=tgl)
        LyAddLeftProp(col, prefs,'vqmtIncludeExistingValues', active=tgl)
        LyAddLeftProp(col, prefs,'vqmtDisplayIcons',          active=tgl)
        LyAddKeyTxtProp(col, prefs,'vqmtRepickKey')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        #VoronoiMixerTool.__dict__['LyDrawInAppearance'].__func__(cls, colLy, prefs) #该死. 由于 @classmethod 而绕过. 但现在没必要了, 因为有了 vqmtPieScaleExtra.
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Pie")+" (VQMT)")
        LyAddHandSplitProp(colBox, prefs,'vqmtPieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,'vqmtPieScale')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieScaleExtra')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieAlignment')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieDisplaySocketColor')
        colProps.active = getattr(prefs,'vqmtPieType')=='CONTROL'
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isHideOptions').name) as dm:
            dm["ru_RU"] = "Скрывать опции нода"
            dm["zh_CN"] = "隐藏节点选项"
        #* isPlaceImmediately 的翻译已在 VMT 中 *
        with VlTrMapForKey(GetAnnotFromCls(cls,'justPieCall').name) as dm:
            dm["ru_RU"] = "Просто вызвать пирог"
            dm["zh_CN"] = "仅调用饼图"
        with VlTrMapForKey(GetAnnotFromCls(cls,'justPieCall').description) as dm:
            dm["ru_RU"] = "Вызвать пирог для добавления нода, минуя выбор сокетов.\n0 – Выключено.\n1 – Float.\n2 – Vector.\n3 – Boolean.\n4 – Color"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isRepeatLastOperation').name) as dm:
            dm["ru_RU"] = "Повторить последнюю операцию"
            dm["zh_CN"] = "重复上一操作"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isRepeatLastOperation').description) as dm:
            dm["ru_RU"] = "Минуя вызов пирога, активирует последнюю использованную операцию для выбранного типа сокета.\n"+\
                        "Ищет сокеты только из доступных предыдущих операций, которые были свершены для типа сокета.\n"+\
                        "Просто вызов пирога и быстрая быстрая математика, не запоминаются как последние операции"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprFloat').name) as dm:
            dm["ru_RU"] = "Скаляр (быстро)"
            dm["zh_CN"] = "浮点（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprVector').name) as dm:
            dm["ru_RU"] = "Вектор (быстро)"
            dm["zh_CN"] = "矢量（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprBool').name) as dm:
            dm["ru_RU"] = "Логический (быстро)"
            dm["zh_CN"] = "布尔（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprColor').name) as dm:
            dm["ru_RU"] = "Цвет (быстро)"
            dm["zh_CN"] = "颜色（快速）"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeThirdSk').name) as dm:
            dm["ru_RU"] = "Разрешить третий сокет"
            dm["zh_CN"] = "包括第三个端口"
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeQuickPresets').name) as dm:
            dm["ru_RU"] = "Включить быстрые пресеты"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeExistingValues').name) as dm:
            dm["ru_RU"] = "Включить существующие значения"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vqmtDisplayIcons').name) as dm:
            dm["ru_RU"] = "Отображать иконки"
#            dm[zh_CN] = ""
        #参见 vqmtRepickKey 在 VLT 中的翻译.
        #vqmtPie 的翻译与 VMT 中的相同.