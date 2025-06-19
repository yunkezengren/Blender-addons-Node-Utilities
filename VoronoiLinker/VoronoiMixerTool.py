

class VoronoiMixerTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #Стоит первым, чтобы быть похожим на VQMT в kmi.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None #Нужно обнулять из-за наличия двух continue ниже.
        self.fotagoSk1 = None
        soldReroutesCanInAnyType = prefs.vmtReroutesCanInAnyType
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            if not list_ftgSksOut:
                continue
            #В фильтре нод нет нужды.
            #Этот инструмент триггерится на любой выход (теперь кроме виртуальных) для первого.
            if isFirstActivation:
                self.fotagoSk0 = list_ftgSksOut[0] if list_ftgSksOut else None
            #Для второго по условиям:
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut:
                    skOut1 = ftg.tar
                    if skOut0==skOut1:
                        break
                    orV = (skOut1.bl_idname=='NodeSocketVirtual')or(skOut0.bl_idname=='NodeSocketVirtual')
                    #Теперь VMT к виртуальным снова может
                    tgl = (skOut1.bl_idname=='NodeSocketVirtual')^(skOut0.bl_idname=='NodeSocketVirtual')
                    tgl = (tgl)or( self.SkBetweenFieldsCheck(skOut0, skOut1)or( (skOut1.bl_idname==skOut0.bl_idname)and(not orV) ) )
                    tgl = (tgl)or( (skOut0.node.type=='REROUTE')or(skOut1.node.type=='REROUTE') )and(soldReroutesCanInAnyType)
                    if tgl:
                        self.fotagoSk1 = ftg
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                    self.fotagoSk1 = None
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            #Не смотря на то, что в фильтре нод нет нужды и и так прекрасно работает на первом попавшемся, всё равно нужно продолжать поиск, если первый сокет найден не был.
            #Потому что если первым(ближайшим) окажется нод с неудачным результатом поиска, цикл закончится и инструмент ничего не выберет, даже если рядом есть подходящий.
            if self.fotagoSk0: #Особенно заметно с активным ныне несуществующим isCanReOut; без этого результат будет выбираться успешно/неуспешно в зависимости от положения курсора.
                break
    def MatterPurposePoll(self):
        if not self.fotagoSk0:
            return False
        if self.isCanFromOne:
            return (self.fotagoSk0.blid!='NodeSocketVirtual')or(self.fotagoSk1)
        else:
            return self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        VmtData.sk0 = self.fotagoSk0.tar
        socket1 = FtgGetTargetOrNone(self.fotagoSk1)
        VmtData.sk1 = socket1
        #Поддержка виртуальных выключена; читается только из первого
        VmtData.skType = VmtData.sk0.type if VmtData.sk0.bl_idname!='NodeSocketVirtual' else socket1.type
        VmtData.isHideOptions = self.isHideOptions
        VmtData.isPlaceImmediately = self.isPlaceImmediately
        _sk = VmtData.sk0
        if socket1 and socket1.type == "MATRIX":
            VmtData.skType = "MATRIX"
            _sk = VmtData.sk1
        SetPieData(self, VmtData, prefs, PowerArr4(GetSkColSafeTup4(_sk), pw=2.2))
        if not self.isInvokeInClassicTree: #В связи с usefulnessForCustomTree, бесполезная проверка.
            return {'CANCELLED'} #Если место действия не в классических редакторах, то просто выйти. Ибо классические редакторы у всех одинаковые, а аддонских есть бесчисленное множество.

        tup_nodes = dict_vmtTupleMixerMain.get(tree.bl_idname, False).get(VmtData.skType, None)
        if tup_nodes:
            if length(tup_nodes)==1: #Если выбор всего один, то пропустить его и сразу переходить к смешиванию.
                DoMix(tree, False, False, tup_nodes[0]) #При моментальной активации можно и не отпустить модификаторы. Поэтому DoMix() получает не event, а вручную.
            else: #Иначе предоставить выбор
                bpy.ops.wm.call_menu_pie(name=VmtPieMixer.bl_idname)
        else: #Иначе для типа сокета не определено (например шейдер в геонодах).
            DisplayMessage(self.bl_label, txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmtReroutesCanInAnyType')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Pie")+f" ({cls.vlTripleName})")
        tlw = cls.vlTripleName.lower()
        LyAddHandSplitProp(colBox, prefs,f'{tlw}PieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieScale')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieAlignment')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieDisplaySocketColor')
        colProps.active = getattr(prefs,f'{tlw}PieType')=='CONTROL'
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanFromOne').name) as dm:
            dm["ru_RU"] = "Может от одного сокета"
            dm["zh_CN"] = "从一个端口连接"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPlaceImmediately').name) as dm:
            dm["ru_RU"] = "Размещать моментально"
            dm["zh_CN"] = "立即添加节点到鼠标位置"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmtReroutesCanInAnyType').name) as dm:
            dm["ru_RU"] = "Рероуты могут смешиваться с любым типом"
            dm["zh_CN"] = "快速混合不限定端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType').name) as dm:
            dm["ru_RU"] = "Тип пирога"
            dm["zh_CN"] = "饼菜单类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',0).name) as dm:
            dm["ru_RU"] = "Контроль"
            dm["zh_CN"] = "控制(自定义)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',1).name) as dm:
            dm["ru_RU"] = "Скорость"
            dm["zh_CN"] = "速度型(多层菜单)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieScale').name) as dm:
            dm["ru_RU"] = "Размер пирога"
            dm["zh_CN"] = "饼菜单大小"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').name) as dm:
            dm["ru_RU"] = "Выравнивание между элементами"
#            dm["zh_CN"] = "元素对齐方式"?
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').description) as dm:
            dm["ru_RU"] = "0 – Гладко.\n1 – Скруглённые состыкованные.\n2 – Зазор"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').name) as dm:
            dm["ru_RU"] = "Отображение типа сокета"
            dm["zh_CN"] = "显示端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').description) as dm:
            dm["ru_RU"] = "0 – Выключено.\n1 – Сверху.\n-1 – Снизу (VMT)"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').name) as dm:
            dm["ru_RU"] = "Отображение цвета сокета"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').description) as dm:
            dm["ru_RU"] = "Знак – сторона цвета. Значение – ширина цвета"
#            dm["zh_CN"] = ""
