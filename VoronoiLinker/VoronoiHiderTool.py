

#Нужен только для наведения порядка и эстетики в дереве.
#Для тех, кого (например меня) напрягают "торчащие без дела" пустые сокеты выхода, или нулевые (чьё значение 0.0, чёрный, и т.п.) незадействованные сокеты входа.
fitVhtModeItems = ( ('NODE',      "Auto-node",    "Automatically processing of hiding of sockets for a node"),
                    ('SOCKET',    "Socket",       "Hiding the socket"),
                    ('SOCKETVAL', "Socket value", "Switching the visibility of a socket contents") )
class VoronoiHiderTool(VoronoiToolAny):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVhtModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    def CallbackDrawTool(self, drata):
        # 小王-模式名匹配
        name = { 'NODE'     : "自动隐藏/显示接口",
                 'SOCKET'   : "隐藏接口",
                 'SOCKETVAL': "隐藏/显示接口值",
                }
        mode= name[self.toolMode]
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE', tool_name=mode)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoAny = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            self.fotagoAny = ftgNd
            match self.toolMode:
                case 'SOCKET'|'SOCKETVAL':
                    #Для режима сокетов обработка свёрнутости такая же, как у всех.
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
                    def GetNotLinked(list_ftgSks): #Findanysk.
                        for ftg in list_ftgSks:
                            if not ftg.tar.vl_sold_is_final_linked_cou:
                                return ftg
                    ftgSkIn = GetNotLinked(list_ftgSksIn)
                    ftgSkOut = GetNotLinked(list_ftgSksOut)
                    if self.toolMode=='SOCKET':
                        self.fotagoAny = MinFromFtgs(ftgSkOut, ftgSkIn)
                    else:
                        self.fotagoAny = ftgSkIn
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.
                case 'NODE':
                    #Для режима нод нет разницы, раскрывать все подряд под курсором, или нет.
                    if prefs.vhtIsToggleNodesOnDrag:
                        if self.firstResult is None:
                            #Если активация для нода ничего не изменила, то для остальных хочется иметь сокрытие, а не раскрытие. Но текущая концепция не позволяет,
                            # информации об этом тупо нет. Поэтому реализовал это точечно вовне (здесь), а не модификацией самой реализации.
                            LGetVisSide = lambda puts: [sk for sk in puts if sk.enabled and not sk.hide]
                            list_visibleSks = [LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]
                            self.firstResult = HideFromNode(prefs, nd, True, False)
                            HideFromNode(prefs, nd, self.firstResult, True) #Заметка: Изменить для нода (для проверки ниже), но не трогать 'self.firstResult'.
                            if list_visibleSks==[LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]:
                                self.firstResult = True
                        HideFromNode(prefs, nd, self.firstResult, True)
                        #См. в вики, почему опция isReDrawAfterChange была удалена.
                        #Todo0v6SF Единственное возможное решение, так это сделать изменение нода _после_ отрисовки одного кадра.
                        #^ Т.е. цепляться к новому ноду на один кадр, а потом уже обработать его сразу с поиском нового нода и рисовки к нему (как для примера в вики).
            break
    def MatterPurposeTool(self, event, prefs, tree):
        match self.toolMode:
            case 'NODE':
                if not prefs.vhtIsToggleNodesOnDrag:
                    #Во время сокрытия сокета нужно иметь информацию обо всех, поэтому выполняется дважды. В первый заход собирается, во второй выполняется.
                    HideFromNode(prefs, self.fotagoAny.tar, HideFromNode(prefs, self.fotagoAny.tar, True), True)
            case 'SOCKET':
                tar_socket = self.fotagoAny.tar
                tar_socket.hide = True
                # 小王-自动隐藏接口优化-inline
                inline_socket_node_list = [ 
                        'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 
                        'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                        'GeometryNodeForeachGeometryElementInput', 'GeometryNodeForeachGeometryElementOutput', 
                        "GeometryNodeCaptureAttribute", "GeometryNodeBake", 
                                        ]
                try:
                    tar_node = tar_socket.node
                    socket_identifier = tar_socket.identifier
                    if tar_node.bl_idname == "GeometryNodeCaptureAttribute":
                        socket_identifier = tar_socket.name
                    if tar_node.bl_idname in inline_socket_node_list:
                        if tar_socket.is_output:
                            tar_node.inputs[socket_identifier].hide = True
                        else:
                            tar_node.outputs[socket_identifier].hide = True
                except:
                    pass
            case 'SOCKETVAL':
                # self.fotagoAny.tar.hide_value = not self.fotagoAny.tar.hide_value    # 插件作者方法,他对节点组方法不对,只要撤销就恢复了隐藏的接口值
                # 小王-隐藏接口值-节点组
                # # type(self)             <class 'VoronoiLinker.VoronoiHiderTool'>
                # # type(self.fotagoAny)   <class 'VoronoiLinker.Fotago'>
                # print("开始" * 30)
                # # pprint("self.__dict__")
                # # pprint(self.__dict__)
                # pprint("self.fotagoAny.__dict__")
                # pprint(self.fotagoAny.__dict__)
                # print("结束" * 30)
                socket = self.fotagoAny.tar
                node = socket.node
                # if node.bl_idname == "GeometryNodeGroup":
                if node.type == "GROUP":
                    for i in node.node_tree.interface.items_tree:
                        if i.item_type == 'SOCKET':   # Panel没有identifier属性-AttributeError: 'NodeTreeInterfacePanel' object has no attribute 'identifier'
                            if i.identifier == socket.identifier:
                                i.hide_value = not socket.hide_value
                else:
                    socket.hide_value = not socket.hide_value

    def InitTool(self, event, prefs, tree):
        self.firstResult = None #Получить действие у первого нода "свернуть" или "развернуть", а потом транслировать его на все остальные попавшиеся.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddHandSplitProp(col, prefs,'vhtHideBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtHideHiddenBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtNeverHideGeometry')
        LyAddHandSplitProp(col, prefs,'vhtIsUnhideVirtual', forceBoolean=2)
        LyAddLeftProp(col, prefs,'vhtIsToggleNodesOnDrag')
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.NODE.name) as dm:
            dm["ru_RU"] = "Авто-нод"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.NODE.description) as dm:
            dm["ru_RU"] = "Автоматически обработать сокрытие сокетов для нода."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SOCKET.description) as dm:
            dm["ru_RU"] = "Сокрытие сокета."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SOCKETVAL.name) as dm:
            dm["ru_RU"] = "Значение сокета"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SOCKETVAL.description) as dm:
            dm["ru_RU"] = "Переключение видимости содержимого сокета."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnCollapsedNodes').name) as dm:
            dm["ru_RU"] = "Триггериться на свёрнутые ноды"
            dm["zh_CN"] = "仅触发已折叠节点"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket').name) as dm:
            dm["ru_RU"] = "Скрывать Boolean сокеты"
            dm["zh_CN"] = "隐藏布尔端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideHiddenBoolSocket').name) as dm:
            dm["ru_RU"] = "Скрывать скрытые Boolean сокеты"
            dm["zh_CN"] = "隐藏已隐藏的布尔端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket',1).name) as dm:
            dm["ru_RU"] = "Если True"
            dm["zh_CN"] = "如果为True"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket',3).name) as dm:
            dm["ru_RU"] = "Если False"
            dm["zh_CN"] = "如果为False"
        with VlTrMapForKey(GetPrefsRnaProp('vhtNeverHideGeometry').name) as dm:
            dm["ru_RU"] = "Никогда не скрывать входные сокеты геометрии"
            dm["zh_CN"] = "永不隐藏几何输入端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtNeverHideGeometry',1).name) as dm:
            dm["ru_RU"] = "Только первый"
            dm["zh_CN"] = "仅第一个端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtIsUnhideVirtual').name) as dm:
            dm["ru_RU"] = "Показывать виртуальные сокеты"
            dm["zh_CN"] = "显示虚拟端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtIsToggleNodesOnDrag').name) as dm:
            dm["ru_RU"] = "Переключать ноды при ведении курсора" #"Обрабатывать ноды в реальном времени"
            dm["zh_CN"] = "移动光标时切换节点"
