


fitVitModeItems = ( ('COPY',   "Copy",   "Copy a socket name to clipboard"),
                    ('PASTE',  "Paste",  "Paste the contents of clipboard into an interface name"),
                    ('SWAP',   "Swap",   "Swap a two interfaces"),
                    ('FLIP',   "Flip",   "Move the interface to a new location, shifting everyone else"),
                    ('NEW',    "New",    "Create an interface using virtual sockets"),
                    ('CREATE', "Create", "Create an interface from a selected socket, and paste it into a specified location"),
                    # ('DELETE', "Delete", "Delete one socket"),
                    ('SOC_TY', "Socket_Type", "Change socket type"),
                    )
class VoronoiInterfacerTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_interfacer'
    bl_label = "Voronoi Interfacer"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default='NEW', items=fitVitModeItems)
    def CallbackDrawTool(self, drata):
        # print(f"{self.toolMode = }")
        match self.toolMode:
            case 'NEW':
                TemplateDrawSksToolHh(drata, self.fotagoSkRosw, self.fotagoSkMain, isClassicFlow=True, tool_name="连到扩展接口")
            case 'CREATE':
                ftgMain = self.fotagoSkMain
                if ftgMain:
                    TemplateDrawSksToolHh(drata, ftgMain, sideMarkHh=-2, tool_name="插入接口")
                ftgNdTar = self.fotagoNdTar
                if ftgNdTar:
                    TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Interfacer")
                    # print(f"{type(ftgNdTar) = }")
                    # pprint(ftgNdTar.__dict__)
                    # print(f"{type(ftgMain) = }")
                    # pprint(ftgMain.__dict__)
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ftgNdTar.tar, cur_x_off=0)
                    # print("-" * 50)
                    # print(f"{type(list_ftgSksIn) = }")
                    # pprint(list_ftgSksIn)
                    # pprint(list_ftgSksIn[0].__dict__)
                    near_group_in = list_ftgSksIn[0]        # 接电阻可能没有输入接口:
                    # print(ftgNdTar.pos.y)

                    y = ftgNdTar.pos.y
                    boxHeiBound = Vec((y-7, y+7 ))
                    DrawVlSocketArea(drata, near_group_in.tar, boxHeiBound, Col4(GetSkColSafeTup4(ftgMain.tar)))
                    # DrawVlSocketArea(drata, near_group_in.tar, near_group_in.boxHeiBound, Col4(GetSkColSafeTup4(near_group_in.tar)))
            case 'FLIP':            # 失败
                # ftgMain = self.fotagoSkMain
                # if ftgMain:
                    # TemplateDrawSksToolHh(drata, ftgMain, isFlipSide=True, tool_name="")

                TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name="移动接口")
                ftgNdTar = self.fotagoNdTar
                if ftgNdTar:
                    # TemplateDrawNodeFull(drata, ftgNdTar, tool_name="Interfacer")
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ftgNdTar.tar, cur_x_off=0)
                    near_group_in = list_ftgSksIn[0]

                    y = ftgNdTar.pos.y
                    boxHeiBound = Vec((y-20, y+20 ))
                    DrawVlSocketArea(drata, near_group_in.tar, boxHeiBound, Col4(GetSkColSafeTup4(ftgMain.tar)))
                    # DrawVlSocketArea(drata, near_group_in.tar, near_group_in.boxHeiBound, Col4(GetSkColSafeTup4(near_group_in.tar)))
            case _:
                # 小王-模式名匹配
                name = {'COPY':  "复制接口名",
                        'PASTE': "粘贴接口名",
                        'SWAP':  "交换接口",
                        'SOC_TY':  "更改节口类型",
                        # 'FLIP':  "接口1移到接口2上",
                        }
                # todo 接口1移到接口2上  FLIP模式，在两个接口绘制名后加上 接口1 接口2
                mode= name[self.toolMode]
                TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw, tool_name=mode)
    def NextAssignmentToolCopyPaste(self, _isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        if (self.toolMode=='PASTE')and(not self.clipboard): #Ожидаемо; а ещё #https://projects.blender.org/blender/blender/issues/113860
            return #Todo0VV пройтись по версиям и указать, в каких крашится.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            # print(ftgNd)
            # pprint(ftgNd.__dict__)
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if (not prefs.vitPasteToAnySocket)and(self.toolMode=='PASTE')and(nd.type not in Equestrian.set_equestrianNodeTypes):
                break #Курсор должен быть рядом со всадником (или групповым нодом) (для не vitPasteToAnySocket). А ещё с `continue` не будет высокоуровневой отмены.
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            self.fotagoSkMain = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            if self.fotagoSkMain:
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkMain.tar.node==nd, flag=True)
            break
    def NextAssignmentToolSwapFlip(self, isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if nd.type not in Equestrian.set_equestrianNodeTypes:
                break #Курсор должен быть рядом со всадником (или групповым нодом); но отмену можно сделать и выбором одного и того же сокета, так что это не точно.
            if (self.fotagoSkRosw)and(self.fotagoSkRosw.tar.node!=nd):
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            if isFirstActivation:
                self.fotagoSkRosw = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkRosw, flag=True)
            skRosw = FtgGetTargetOrNone(self.fotagoSkRosw)
            if skRosw:
                for ftg in list_ftgSksOut if skRosw.is_output else list_ftgSksIn:
                    if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                        self.fotagoSkMain = ftg
                        break
                if (self.fotagoSkMain)and(self.fotagoSkMain.tar==skRosw):
                    self.fotagoSkMain = None
            break
    def NextAssignmentToolNewCreate(self, isFirstActivation, prefs, tree):
        set_eqSimRepBlids = {'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            match self.toolMode:
                case 'NEW':
                    self.fotagoSkMain = None
                    if isFirstActivation:
                        self.fotagoSkRosw = None
                        for ftg in list_ftgSksOut:
                            self.fotagoSkRosw = ftg
                            self.tglCrossVirt = ftg.blid=='NodeSocketVirtual'
                            break
                        CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkRosw, flag=True)
                    skRosw = FtgGetTargetOrNone(self.fotagoSkRosw)
                    if skRosw:
                        for ftg in list_ftgSksIn:
                            if (ftg.blid=='NodeSocketVirtual')^self.tglCrossVirt:
                                self.fotagoSkMain = ftg
                                break
                        if (self.fotagoSkMain)and(self.fotagoSkMain.tar.node==skRosw.node): #todo0NA обобщить такую проверку для всех; мб в класс.
                            self.fotagoSkMain = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkMain, flag=True)
                case 'CREATE':
                    if isFirstActivation:
                        ftgSkOut, ftgSkIn = None, None
                        for ftg in list_ftgSksIn:
                            if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkIn = ftg
                                break
                        for ftg in list_ftgSksOut:
                            if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkOut = ftg
                                break
                        self.fotagoSkMain = MinFromFtgs(ftgSkOut, ftgSkIn)
                    self.fotagoNdTar = None
                    skMain = FtgGetTargetOrNone(self.fotagoSkMain)
                    if skMain:
                        if nd==skMain.node: #Можно было бы и разрешить из своего нода тоже, но наверное лучше не стоит.
                            break
                        if nd.type not in Equestrian.set_equestrianNodeTypes:
                            continue
                        if (skMain.is_output)and(nd.type=='GROUP_INPUT'):
                            continue
                        if (not skMain.is_output)and(nd.type=='GROUP_OUTPUT'):
                            continue
                        if (skMain.is_output)and(nd.type=='GROUP_INPUT'):
                            continue
                        if (not skMain.is_output)and(nd.type=='GROUP_OUTPUT'):
                            continue
                        self.fotagoNdTar = ftgNd
            break
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        match self.toolMode:
            case 'COPY'|'PASTE':
                self.NextAssignmentToolCopyPaste(isFirstActivation, prefs, tree)
            case 'SWAP'|'FLIP':
                self.NextAssignmentToolSwapFlip(isFirstActivation, prefs, tree)
            case 'NEW'|'CREATE':
                self.NextAssignmentToolNewCreate(isFirstActivation, prefs, tree)
    def MatterPurposePoll(self):
        match self.toolMode:
            case 'COPY'|'PASTE':
                return not not self.fotagoSkMain
            case 'SWAP'|'FLIP':
                return self.fotagoSkRosw and self.fotagoSkMain
            case 'NEW':
                for dk, dv in self.dict_ndHidingVirtualIn.items():
                    dk.inputs[-1].hide = dv
                for dk, dv in self.dict_ndHidingVirtualOut.items():
                    dk.outputs[-1].hide = dv
                return self.fotagoSkRosw and self.fotagoSkMain
            case 'CREATE':
                return self.fotagoSkMain and self.fotagoNdTar
    def MatterPurposeTool(self, event, prefs, tree):
        match self.toolMode:
            case 'COPY':
                self.clipboard = GetSkLabelName(self.fotagoSkMain.tar)
            case 'PASTE':
                #tovo1v6 добавить клавишу, нажатие которой приведёт к "отмене" -- вставки не будет; поскольку этот режим гарантированно прилипает (см. опцию) к любому сокету, и нужно как-то обслужить желание "дать заднюю".
                skMain = self.fotagoSkMain.tar
                if (skMain.node.type not in Equestrian.set_equestrianNodeTypes)and(prefs.vitPasteToAnySocket):
                    skMain.name = self.clipboard
                else:
                    Equestrian(skMain).GetSkfFromSk(skMain).name = self.clipboard
            case 'SWAP'|'FLIP':
                skMain = self.fotagoSkMain.tar
                equr = Equestrian(skMain)
                skfFrom = equr.GetSkfFromSk(self.fotagoSkRosw.tar)
                skfTo = equr.GetSkfFromSk(skMain)
                equr.MoveBySkfs(skfFrom, skfTo, isSwap=self.toolMode=='SWAP')
            case 'NEW':
                DoLinkHh(self.fotagoSkRosw.tar, self.fotagoSkMain.tar)
            case 'CREATE':
                ftgNdTar = self.fotagoNdTar
                ndTar = ftgNdTar.tar
                equr = Equestrian(ndTar)
                skMain = self.fotagoSkMain.tar
                skfNew = equr.NewSkfFromSk(skMain, isFlipSide=ndTar.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'})
                can = True
                # if not equr.has_extend_socket:
                is_group = equr.node.type in ['GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT']
                if is_group:
                    for skf in equr.skfa:
                        if skf.item_type=='PANEL': #Нахрен эту головную боль. Шатайтесь с этим сами, а мне уже лень.
                            can = False #|4|.
                            break
                if can: #tovo0v6 и панели тоже.
                    nameSn = skfNew.name
                    ftgNearest = None# MinFromFtgs(list_ftgSksIn[0] if list_ftgSksIn else None, list_ftgSksOut[0] if list_ftgSksOut else None)
                    min = 16777216.0
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ndTar)
                    for ftg in list_ftgSksIn if skMain.is_output else list_ftgSksOut:
                        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(ndTar, ftg.tar)):
                            len = (ftgNdTar.pos-ftg.pos).length
                            if min>len:
                                min = len
                                ftgNearest = ftg
                    if ftgNearest and (not equr.is_index_switch):
                        skfTo = equr.GetSkfFromSk(ftgNearest.tar)
                        equr.MoveBySkfs(skfNew, skfTo, isSwap=False)
                        if (ftgNdTar.pos.y<ftgNearest.pos.y): #'True' -- далее по списку в группе, а не мироориентация.
                            if equr.has_extend_socket:
                                equr.MoveBySkfs(equr.GetSkfFromSk(ftgNearest.tar), skfTo, isSwap=None) #Осторожнее с skfTo.
                            else:
                                equr.MoveBySkfs(skfNew, skfTo, isSwap=None) #Гениально!
                    if ftgNearest and equr.is_index_switch:
                        links = tree.links
                        tar_input = ftgNearest.tar       # 要插入的位置的接口
                        inputs = tar_input.node.inputs
                        if tar_input.name == "Index":
                            tar_index =  1
                        else:
                            is_ = ftgNdTar.pos.y<ftgNearest.pos.y      # 例: 插入1/2之间,离2近时正确,离1近时插到1上了(这时判断为True,插入1/2之间)
                            tar_index = int(tar_input.name) + 1 + is_  # 接口名 + 1才是在输入接口列表里的序号,因为编号切换第一个接口是编号
                        max_index = int(skfNew.name) + 1               # 最后一个即新建接口的序号
                        for i in range(max_index, tar_index-1, -1):
                            link = inputs[i-1].links
                            if link:
                                links.new(link[0].from_socket, inputs[i])  # 建立新连线
                                links.remove(link[0])                      # 删除旧连线
                        links.new(skMain, inputs[i])


                if equr.has_extend_socket:
                    # print("from_socket ", skMain.name)
                    # print("from_socket.node ", skMain.node.name)
                    # # print("equr.skfa = ", equr.skfa)
                    # # print("equr.skfa.get(nameSn) = ", equr.skfa.get(nameSn))
                    # print("")
                    # # pprint(equr)
                    # pprint(equr.__dict__)
                    # # pprint(equr.skfa)
                    # # pprint(equr.type)
                    # # pprint(dir(equr))

                    # to_socket = equr.GetSkFromSkf(equr.skfa.get(nameSn), isOut=not skMain.is_output)
                    # print("to_socket   ", to_socket)
                    # # print("to_socket   ", to_socket.name)
                    # # print("to_socket.node   ", to_socket.node.name)
                    # print("")
                    # pprint(equr.__dict__)   {'node': "Menu Switch",'skfa': node.enum_items,'tree': , 'type': 'MENU
                    tree.links.new(skMain, equr.GetSkFromSkf(equr.skfa.get(nameSn), isOut=not skMain.is_output))
                if is_group:
                    tree.links.new(skMain, equr.GetSkFromSkf(skfNew, isOut=(skfNew.in_out=='OUTPUT')^(equr.type!='GROUP')))
    def InitTool(self, event, prefs, tree):
        self.fotagoSkMain = None
        self.fotagoSkRosw = None #RootSwap
        match self.toolMode:
            case 'NEW':
                self.dict_ndHidingVirtualIn = {}
                self.dict_ndHidingVirtualOut = {}
                #self.NextAssignmentRoot(True)
                #if self.fotagoSkRosw:
                #    nd = self.fotagoSkRosw.tar.node
                #    self.dict_ndHidingVirtualOut[nd] = nd.outputs[-1].hide
                #    nd.outputs[-1].hide = False
                #    self.NextAssignmentRoot(True)
                #    if self.fotagoSkRosw:
                #        tgl = self.fotagoSkRosw.blid!='NodeSocketVirtual'
                if True: #todo1v6 что-нибудь придумать с ^ этим ради эстетики.
                        for nd in tree.nodes:
                            if nd.bl_idname in set_utilEquestrianPortalBlids:
                                if nd.inputs:
                                    self.dict_ndHidingVirtualIn[nd] = nd.inputs[-1].hide
                                    nd.inputs[-1].hide = False
                                if nd.outputs:
                                    self.dict_ndHidingVirtualOut[nd] = nd.outputs[-1].hide
                                    nd.outputs[-1].hide = False
                self.tglCrossVirt = None
                #Какой-то баг, если не перерисовать, то первый найденный виртуальный не сможет выбраться корректно.
                bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
            case 'CREATE':
                self.fotagoNdTar = None #Омг.
        VoronoiInterfacerTool.clipboard = property(lambda _:bpy.context.window_manager.clipboard, lambda _,v:setattr(bpy.context.window_manager,'clipboard', v))
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vitPasteToAnySocket')
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.COPY.name) as dm:
            dm["ru_RU"] = "Копировать"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.COPY.description) as dm:
            dm["ru_RU"] = "Копировать имя сокета в буфер обмена."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.PASTE.name) as dm:
            dm["ru_RU"] = "Вставить"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.PASTE.description) as dm:
            dm["ru_RU"] = "Вставить содержимое буфера обмена в имя интерфейса."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SWAP.name) as dm:
            dm["ru_RU"] = "Поменять местами"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SWAP.description) as dm:
            dm["ru_RU"] = "Поменять местами два интерфейса."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.FLIP.name) as dm:
            dm["ru_RU"] = "Сдвинуть"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.FLIP.description) as dm:
            dm["ru_RU"] = "Переместить интерфейс на новое место, сдвигая всех остальных."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.NEW.name) as dm:
            dm["ru_RU"] = "Добавить"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.NEW.description) as dm:
            dm["ru_RU"] = "Добавить интерфейс с помощью виртуальных сокетов."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.CREATE.name) as dm:
            dm["ru_RU"] = "Создать"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.CREATE.description) as dm:
            dm["ru_RU"] = "Создать интерфейс из выбранного сокета, и вставить его на указанное место."
#            dm["zh_CN"] = ""
