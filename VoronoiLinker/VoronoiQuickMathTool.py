

set_vqmtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION', 'MATRIX'}
fitVqmtRloDescr = "Bypassing the pie call, activates the last used operation for the selected socket type.\n"+\
                  "Searches for sockets only from an available previous operations that were performed for the socket type.\n"+\
                  "Just a pie call, and the fast fast math is not remembered as the last operations"
class VoronoiQuickMathTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    quickOprFloat:         bpy.props.StringProperty(name="Float (quick)",  default="") #Они в начале, чтобы в kmi отображалось выровненным.
    quickOprInt:           bpy.props.StringProperty(name="Int (quick)",  default="") #Они в начале, чтобы в kmi отображалось выровненным.
    quickOprVector:        bpy.props.StringProperty(name="Vector (quick)", default="") #quick вторым, чтобы при нехватке места отображалось первое слово, от чего пришлось заключить в скобки.
    isCanFromOne:          bpy.props.BoolProperty(name="Can from one socket", default=True)
    isRepeatLastOperation: bpy.props.BoolProperty(name="Repeat last operation", default=False, description=fitVqmtRloDescr) #Что ж, квартет qqm теперь вынуждает их постоянно выравнивать.
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
            #Этот инструмент триггерится только на выходы поля.
            if isFirstActivation:
                isSucessOut = False
                for ftg in list_ftgSksOut:
                    if not self.isRepeatLastOperation:
                        if not self.isQuickQuickMath:
                            if ftg.tar.type in set_vqmtSkTypeFields:
                                self.fotagoSk0 = ftg
                                isSucessOut = True
                                break
                        else: #Для isQuickQuickMath цепляться только к типам сокетов от явно указанных операций.
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
                    continue #Искать нод для isFirstActivation'а, у которого попадёт на сокет поля.
                #Для следующего `continue`, ибо если далее будет неудача с последующей активацией continue, то произойдёт перевыбор isFirstActivation
                isFirstActivation = False #Но в связи с текущей топологией выбора, это без нужды.
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk0, flag=True) #todo0NA см. строчку выше, этот 'cond' должен быть не от isFirstActivation.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if isNotCanPickThird:
                #Для второго по условиям:
                if skOut0:
                    for ftg in list_ftgSksOut:
                        if self.SkBetweenFieldsCheck(skOut0, ftg.tar):
                            self.fotagoSk1 = ftg
                            break
                    if not self.fotagoSk1:
                        continue #Чтобы ноды без сокетов полей были прозрачными.
                    if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            else:
                self.fotagoSk2 = None #Обнулять для удобства высокоуровневой отмены.
                #Для третьего, если не ноды двух предыдущих.
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
    def ModalMouseNext(self, event, prefs): #Копия-алерт, у VLT такое же.
        if event.type==prefs.vqmtRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState:
                self.NextAssignmentRoot(True)
                self.canPickThird = False #В целом хреновая идея добавить возможность перевыбора для инструмента, у которого есть третий сокет; управление инструментом стало сложно-контролируемее.
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
        VqmtData.qmSkType = VqmtData.sk0.type #Заметка: Наличие только сокетов поля -- забота на уровень выше.
        VqmtData.qmTrueSkType = VqmtData.qmSkType #Эта информация нужна для "последней операции".
        self.int_default_float = False
        match VqmtData.sk0.type:
            # case 'INT':      VqmtData.qmSkType = 'VALUE' #И только целочисленный обделён своим нодом математики. Может его добавят когда-нибудь?.
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
            case 'ROTATION': VqmtData.qmSkType = 'VECTOR' #Больше шансов, что для математика для кватерниона будет первее.
            case 'MATRIX':   VqmtData.qmSkType = 'MATRIX' #Больше шансов, что для математика для кватерниона будет первее.
            #case 'ROTATION': return {'FINISHED'} #Однако странно, почему с RGBA линки отмечаются некорректными, ведь оба Arr4... Зачем тогда цвету альфа?
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
        VqmtData.canProcHideSks = False #Сразу для двух DoQuickMath выше и оператора ниже.
        if self.justPieCall:
            match tree.bl_idname:
                case 'ShaderNodeTree': can = self.justPieCall in {1,2,4}
                case 'GeometryNodeTree': can = True
                case 'CompositorNodeTree'|'TextureNodeTree': can = self.justPieCall in {1,4}
            if not can:
                DisplayMessage(self.bl_label, txt_vqmtThereIsNothing)
                return {'CANCELLED'}
            VqmtData.sk0 = None #Обнулять для полноты картины и для GetSkCol.
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
        #VoronoiMixerTool.__dict__['LyDrawInAppearance'].__func__(cls, colLy, prefs) #Чума. Обход из-за @classmethod. Но теперь без нужды, потому что появился vqmtPieScaleExtra.
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
        #* Перевод isPlaceImmediately уже есть в VMT *
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
        #См. перевод vqmtRepickKey в VLT.
        #Переводы vqmtPie такие же, как и в VMT.
