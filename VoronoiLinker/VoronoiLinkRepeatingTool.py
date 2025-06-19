



fitVlrtModeItems = ( ('SOCKET', "For socket", "Using the last link created by some from the tools, create the same for the specified socket"),
                     ('NODE',   "For node",   "Using name of the last socket, find and connect for a selected node") )
class VoronoiLinkRepeatingTool(VoronoiToolAny): #Вынесено в отдельный инструмент, чтобы не осквернять святая святых спагетти-кодом (изначально был только для VLT).
    bl_idname = 'node.voronoi_link_repeating'
    bl_label = "Voronoi Link Repeating"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVlrtModeItems)
    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE')
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        def IsSkBetweenFields(sk1, sk2):
            return (sk1.type in set_utilTypeSkFields)and( (sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
        skLastOut = self.skLastOut
        skLastIn = self.skLastIn
        if not skLastOut:
            return
        SolderSkLinks(tree) #Вроде и без перепайки работает.
        self.fotagoAny = None
        cur_x_off_repeat = -Cursor_X_Offset if self.toolMode=='SOCKET' else 0     # 小王 这个有点特殊
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=cur_x_off_repeat):
            nd = ftgNd.tar
            if nd==skLastOut.node: #Исключить само-нод.
                break #continue
            if self.toolMode=='SOCKET':
                list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=-Cursor_X_Offset)
                if skLastOut:
                    for ftg in list_ftgSksIn:
                        if (skLastOut.bl_idname==ftg.blid)or(IsSkBetweenFields(skLastOut, ftg.tar)):
                            can = True
                            for lk in ftg.tar.vl_sold_links_final:
                                if lk.from_socket==skLastOut: #Определить уже имеющийся линк, и не выбирать таковой сокет.
                                    can = False
                            if can:
                                self.fotagoAny = ftg
                                break
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny, flag=False)
            else:
                if skLastIn:
                    if nd.inputs:
                        self.fotagoAny = ftgNd
                    for sk in nd.inputs:
                        if CompareSkLabelName(sk, skLastIn):
                            if (sk.enabled)and(not sk.hide):
                                tree.links.new(skLastOut, sk) #Заметка: Не высокоуровневый; зачем для повторения по нодам нужны интерфейсы?.
            break
    def MatterPurposeTool(self, event, prefs, tree):
        if self.toolMode=='SOCKET':
            #Здесь нет нужды проверять на одинаковость дерева сокетов, проверка на это уже есть в NextAssignmentTool().
            #Также нет нужды проверять существование skLastOut, см. его топологию в NextAssignmentTool().
            #Заметка: Проверка одинаковости `.id_data` имеется у VlrtRememberLastSockets().
            #Заметка: Нет нужды проверять существование дерева, потому что если прицепившийся сокет тут существует, то уже где-то.
            DoLinkHh(self.skLastOut, self.fotagoAny.tar)
            VlrtRememberLastSockets(self.skLastOut, self.fotagoAny.tar) #Потому что. И вообще.. "саморекурсия"?.
    def InitTool(self, event, prefs, tree):
        for txt in "Out", "In":
            txtAttSkLast = 'skLast'+txt
            txtAttReprLastSk = 'reprLastSk'+txt #В случае неудачи записывать ничего.
            setattr(self, txtAttSkLast, None) #Инициализировать для инструмента и присвоить ниже.
            if reprTxtSk:=getattr(VlrtData, txtAttReprLastSk):
                try:
                    sk = eval(reprTxtSk)
                    if sk.id_data==tree:
                        setattr(self, txtAttSkLast, sk)
                    else:
                        setattr(VlrtData, txtAttReprLastSk, "")
                except:
                    setattr(VlrtData, txtAttReprLastSk, "")
        #Заметка: Оказывается, Ctrl-Z делает (глобально сохранённую) ссылку на tree 'ReferenceError: StructRNA of type ShaderNodeTree has been removed'.
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.SOCKET.name) as dm:
            dm["ru_RU"] = "Для сокета"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SOCKET.description) as dm:
            dm["ru_RU"] = "Используя последний линк, созданный каким-н. из инструментов, создать такой же для указанного сокета."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.NODE.name) as dm:
            dm["ru_RU"] = "Для нода"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.NODE.description) as dm:
            dm["ru_RU"] = "Используя имя последнего сокета, найти и соединить для выбранного нода."
            dm["zh_CN"] = "鼠标移动到节点旁自动恢复节点的连接"
