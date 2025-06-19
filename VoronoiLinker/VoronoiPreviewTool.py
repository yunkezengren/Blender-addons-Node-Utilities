




class VoronoiPreviewTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_preview'
    bl_label = "Voronoi Preview"
    usefulnessForCustomTree = True
    isSelectingPreviewedNode: bpy.props.BoolProperty(name="Select previewed node", default=True)
    isTriggerOnlyOnLink:      bpy.props.BoolProperty(name="Only linked",           default=False, description="Trigger only on linked socket") #Изначально было в prefs.
    isEqualAnchorType:        bpy.props.BoolProperty(name="Equal anchor type",     default=False, description="Trigger only on anchor type sockets")
    def CallbackDrawTool(self, drata):
        if (self.prefs.vptRvEeSksHighlighting)and(self.fotagoSk): #Помощь в реверс-инженеринге -- подсвечивать места соединения, и отображать имена этих сокетов, одновременно.
            SolderSkLinks(self.tree) #Иначе крашится на `ftg.tar==sk:`.
            #Определить масштаб для надписей:
            soldCursorLoc = drata.cursorLoc
            #Нарисовать:
            ndTar = self.fotagoSk.tar.node
            for isSide in (False, True):
                for skTar in ndTar.outputs if isSide else ndTar.inputs:
                    for lk in skTar.vl_sold_links_final:
                        sk = lk.to_socket if isSide else lk.from_socket
                        nd = sk.node
                        if (nd.type!='REROUTE')and(not nd.hide):
                            list_ftgSks = GenFtgsFromPuts(nd, not isSide, soldCursorLoc, drata.uiScale)
                            for ftg in list_ftgSks:
                                if ftg.tar==sk:
                                    #Хождение по рероутом не поддерживается. Потому что лень, и лень переделывать под это код.
                                    if drata.dsIsDrawSkArea:
                                        DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Col4(GetSkColSafeTup4(ftg.tar)))
                                    DrawVlSkText(drata, ftg.pos, (1-isSide*2, -0.5), ftg, fontSizeOverwrite=min(24*drata.worldZoom*self.prefs.vptHlTextScale, 25))
                                    break
                        nd.hide = False #Запись во время рисования. По крайней мере, не так как сильно как в VMLT.
                        #todo0SF: использование bpy.ops.wm.redraw_timer вызывает зависание намертво. Так что из-за этого здесь имеется ещё один "проскальзывающий кадр".
        TemplateDrawSksToolHh(drata, self.fotagoSk, isDrawMarkersMoreTharOne=True, tool_name="Preview")
    @staticmethod
    def OmgNodeColor(nd, col=None):
        set_omgApiNodesColor = {'FunctionNodeInputColor'} #https://projects.blender.org/blender/blender/issues/104909
        if nd.bl_idname in set_omgApiNodesColor:
            bn = BNode.GetFields(nd)
            if col:
                bn.color[0] = col[0]
                bn.color[1] = col[1]
                bn.color[2] = col[2]
            else:
                return (bn.color[0], bn.color[1], bn.color[2])
        else:
            if col:
                nd.color = col
            else:
                return nd.color.copy()
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        SolderSkLinks(tree) #Иначе крашится.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        if False:
            #我已经为Viever添加了一个粘附在字段上的功能，但后来我意识到没有API可以取代它的预览类型。又来了我们必须保持低启动。用于粘附到地理查看器的字段。
            # Уж было я добавил возможность цепляться к полям для виевера, но потом понял, что нет api на смену его типа предпросмотра. Опять. Придётся хранить на низком старте.
            isGeoViewer = False #Для цепляния к полям для гео-Viewer'a.
            if isGeoTree:
                for nd in tree.nodes:
                    if nd.type=='VIEWER':
                        isGeoViewer = True
                        break
        self.fotagoSk = None #Нет нужды, но сбрасывается для ясности картины. Было полезно для отладки.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            if (prefs.vptRvEeIsSavePreviewResults)and(nd.name==voronoiPreviewResultNdName): #Игнорировать готовый нод для переименования и тем самым сохраняя результаты предпросмотра.
                continue
            #Если в геометрических нодах, то игнорировать ноды без выходов геометрии
            if (isGeoTree)and(not self.isAnyAncohorExist):
                if not any(True for sk in nd.outputs if (sk.type=='GEOMETRY')and(not sk.hide)and(sk.enabled)): #Искать сокеты геометрии, которые видимы.
                    continue
            #Пропускать ноды если визуально нет сокетов; или есть, но только виртуальные. Для рероутов всё бесполезно.
            if (not any(True for sk in nd.outputs if (not sk.hide)and(sk.enabled)and(sk.bl_idname!='NodeSocketVirtual')))and(nd.type!='REROUTE'):
                continue
            #Всё выше нужно было для того, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента. По ощущениям получаются как "прозрачные" ноды.
            #Игнорировать свой собственный спец-рероут-якорь (проверка на тип и имя)
            if ( (nd.type=='REROUTE')and(nd.name==voronoiAnchorCnName) ):
                continue
            #В случае успеха переходить к сокетам:
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            for ftg in list_ftgSksOut:
                #Игнорировать свои сокеты мостов здесь. Нужно для нод нод-групп, у которых "торчит" сокет моста и к которому произойдёт прилипание без этой проверки; и после чего они будут удалены в VptPreviewFromSk().
                if ftg.tar.name==voronoiSkPreviewName:
                    continue
                #Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии.
                #Якорь притягивает на себя превиев; рероут может принимать любой тип; следовательно -- при наличии якоря отключать триггер только на геосокеты
                if (ftg.blid!='NodeSocketVirtual')and( (not isGeoTree)or(ftg.tar.type=='GEOMETRY')or(self.isAnyAncohorExist) ):
                    can = True
                    if rrAnch:=tree.nodes.get(voronoiAnchorCnName): #EqualAnchorType.
                        rrSkBlId = rrAnch.outputs[0].bl_idname
                        can = (not self.isEqualAnchorType)or(ftg.blid==rrSkBlId)or(rrSkBlId=='NodeSocketVirtual')
                    #todo1v6 для якорей близости тоже сделать выбор по типу?
                    can = (can)and(not ftg.tar.node.label==voronoiAnchorDtName) #ftg.tar.node not in self.list_distanceAnchors
                    if can:
                        if (not self.isTriggerOnlyOnLink)or(ftg.tar.vl_sold_is_final_linked_cou): #Помощь в реверс-инженеринге -- триггериться только на существующие линки; ускоряет процесс "чтения/понимания" дерева.
                            self.fotagoSk = ftg
                            break
            if self.fotagoSk: #Завершать в случае успеха. Иначе, например для игнорирования своих сокетов моста, если у нода только они -- остановится рядом и не найдёт других.
                break
        if self.fotagoSk:
            CheckUncollapseNodeAndReNext(nd, self, cond=True)
            if prefs.vptIsLivePreview:
                # print("."*100)
                # print(f"{self.fotagoSk = }")
                # print(f"{self.fotagoSk.tar = }")
                VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
            if prefs.vptRvEeIsColorOnionNodes: #Помощь в реверс-инженеринге -- вместо поиска глазами тоненьких линий, быстрое визуальное считывание связанных топологией нодов.
                SolderSkLinks(tree) #Без этого придётся окрашивать принимающий нод вручную, чтобы не "моргал".
                ndTar = self.fotagoSk.tar.node
                #Не париться с запоминанием последних и тупо выключать у всех каждый раз. Дёшево и сердито
                for nd in tree.nodes:
                    nd.use_custom_color = False
                def RecrRerouteWalkerPainter(sk, col):
                    for lk in sk.vl_sold_links_final:
                        nd = lk.to_node if sk.is_output else lk.from_node
                        if nd.type=='REROUTE':
                            RecrRerouteWalkerPainter(nd.outputs[0] if sk.is_output else nd.inputs[0], col)
                        else:
                            nd.use_custom_color = True
                            if (not prefs.vptRvEeIsSavePreviewResults)or(nd.name!=voronoiPreviewResultNdName): #Нод для сохранения результата не перекрашивать
                                self.OmgNodeColor(nd, col)
                            nd.hide = False #А также раскрывать их.
                for sk in ndTar.outputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorOut)
                for sk in ndTar.inputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorIn)
    def MatterPurposeTool(self, event, prefs, tree):
        SolderSkLinks(tree) #Иначе крашится.
        VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
        VlrtRememberLastSockets(self.fotagoSk.tar, None)
        if prefs.vptRvEeIsColorOnionNodes:
            for nd in tree.nodes:
                dv = self.dict_saveRestoreNodeColors.get(nd, None) #Точно так же, как и в RestoreCollapsedNodes.
                if dv:
                    nd.use_custom_color = dv[0]
                    self.OmgNodeColor(nd, dv[1])
    def InitTool(self, event, prefs, tree):
        #Если использование классического viewer'а разрешено, завершить инструмент с меткой пропуска, "передавая эстафету" оригинальному виеверу.
        match tree.bl_idname:
            case 'GeometryNodeTree':
                if (prefs.vptAllowClassicGeoViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
            case 'CompositorNodeTree':
                if (prefs.vptAllowClassicCompositorViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
        if prefs.vptRvEeIsColorOnionNodes:
            #Запомнить все цвета, и обнулить их всех:
            self.dict_saveRestoreNodeColors = {}
            for nd in tree.nodes:
                self.dict_saveRestoreNodeColors[nd] = (nd.use_custom_color, self.OmgNodeColor(nd))
                nd.use_custom_color = False
            #Заметка: Ноды сохранения результата с луковичными цветами обрабатываются как есть. Дублированный нод не будет оставаться незатрагиваемым.
        #Пайка:
        list_distAnchs = []
        for nd in tree.nodes:
            if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                list_distAnchs.append(nd)
                nd.label = voronoiAnchorDtName #А также используется для проверки на свои рероуты.
        self.list_distanceAnchors = list_distAnchs
        #Пайка:
        rrAnch = tree.nodes.get(voronoiAnchorCnName)
        #Некоторые пользователи в "начале знакомства" с инструментом захотят переименовать якорь.
        #Каждый призыв якоря одинаков по заголовку, а при повторном призыве заголовок всё равно меняется обратно на стандартный.
        #После чего пользователи поймут, что переименовывать якорь бесполезно.
        if rrAnch:
            rrAnch.label = voronoiAnchorCnName #Эта установка лишь ускоряет процесс осознания.
        self.isAnyAncohorExist = not not (rrAnch or list_distAnchs) #Для геонод; если в них есть якорь, то триггериться не только на геосокеты.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vptAllowClassicGeoViewer')
        LyAddLeftProp(col, prefs,'vptAllowClassicCompositorViewer')
        LyAddLeftProp(col, prefs,'vptIsLivePreview')
        row = col.row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeIsColorOnionNodes')
        if prefs.vptRvEeIsColorOnionNodes:
            row.prop(prefs,'vptOnionColorIn', text="")
            row.prop(prefs,'vptOnionColorOut', text="")
        else:
            LyAddNoneBox(row)
            LyAddNoneBox(row)
        row = col.row().row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeSksHighlighting')
        if True:#prefs.vptRvEeSksHighlighting:
            row = row.row(align=True)
            row.prop(prefs,'vptHlTextScale', text="Scale")
            row.active = prefs.vptRvEeSksHighlighting
        LyAddLeftProp(col, prefs,'vptRvEeIsSavePreviewResults')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectingPreviewedNode').name) as dm:
            dm["ru_RU"] = "Выделять предпросматриваемый нод"
            dm["zh_CN"] = "自动选择被预览的节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').name) as dm:
            dm["ru_RU"] = "Только подключённые"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').description) as dm:
            dm["ru_RU"] = "Цепляться только на подключённые сокеты"
            dm["zh_CN"] = "只预览已有连接的输出端口"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').name) as dm:
            dm["ru_RU"] = "Равный тип якоря"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').description) as dm:
            dm["ru_RU"] = "Цепляться только к сокетам типа якоря"
            dm["zh_CN"] = "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的端口类型一样才能被预览连接"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').name) as dm:
            dm["ru_RU"] = "Разрешить классический Viewer Геометрических узлов"
            dm["zh_CN"] = "几何节点里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').description) as dm:
            dm["ru_RU"] = "Разрешить использование классического Viewer'а геометрических нодов путём клика по ноду"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').name) as dm:
            dm["ru_RU"] = "Разрешить классический Viewer Композитора"
            dm["zh_CN"] = "合成器里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').description) as dm:
            dm["ru_RU"] = "Разрешить использование классического Viewer'а композиторных нодов путём клика по ноду"
            dm["zh_CN"] = "默认是按顺序轮选输出接口端无法直选第N个通道接口"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').name) as dm:
            dm["ru_RU"] = "Предварительный просмотр в реальном времени"
            dm["zh_CN"] = "实时预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').description) as dm:
            dm["ru_RU"] = "Предпросмотр в реальном времени"
            dm["zh_CN"] = "即使没松开鼠标也能观察预览结果"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').name) as dm:
            dm["ru_RU"] = "Луковичные цвета нод"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').description) as dm:
            dm["ru_RU"] = "Окрашивать топологически соединённые ноды"
            dm["zh_CN"] = "快速预览时将与预览的节点有连接关系的节点全部着色显示"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').name) as dm:
            dm["ru_RU"] = "Подсветка топологических соединений"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').description) as dm:
            dm["ru_RU"] = "Отображать имена сокетов, чьи линки подсоединены к ноду"
            dm["zh_CN"] = "快速预览时高亮显示连接到预览的节点的上级节点的输出端口"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').name) as dm:
            dm["ru_RU"] = "Сохранять результаты предпросмотра"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').description) as dm:
            dm["ru_RU"] = "Создавать предпросмотр через дополнительный нод, удобный для последующего копирования"
            dm["zh_CN"] = "保存预览结果,通过新建一个预览节点连接预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorIn').name) as dm:
            dm["ru_RU"] = "Луковичный цвет входа"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorOut').name) as dm:
            dm["ru_RU"] = "Луковичный цвет выхода"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptHlTextScale').name) as dm:
            dm["ru_RU"] = "Масштаб текста"
#            dm["zh_CN"] = ""

