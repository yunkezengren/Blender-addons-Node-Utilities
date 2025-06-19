

#"Массовый линкер" -- как линкер, только много за раз (ваш кэп).
#См. вики на гитхабе, чтобы посмотреть 5 примеров использования массового линкера. Дайте мне знать, если обнаружите ещё одно необычное применение этому инструменту.
class VoronoiMassLinkerTool(VoronoiToolRoot): #"Малыш котопёс", не ноды, не сокеты.
    bl_idname = 'node.voronoi_mass_linker'
    bl_label = "Voronoi MassLinker" #Единственный, у кого нет пробела. Потому что слишком котопёсный))00)0
    # А если серьёзно, то он действительно самый странный. Пародирует VLT с его dsIsAlwaysLine. SocketArea стакаются, если из нескольких в одного. Пишет в функции рисования...
    # А ещё именно он есть/будет на превью аддона, ибо обладает самой большой степенью визуальности из всех инструментов (причем без верхнего предела).
    usefulnessForCustomTree = True
    isIgnoreExistingLinks: bpy.props.BoolProperty(name="Ignore existing links", default=False)
    def CallbackDrawTool(self, drata):
        #Здесь нарушается местная VL'ская концепция чтения-записи, и CallbackDraw ищет и записывает найденные сокеты вместо того, чтобы просто читать и рисовать. Полагаю, так инструмент проще реализовать.
        self.list_equalFtgSks.clear() #Очищать каждый раз. P.s. важно делать это в начале, а не в ветке двух нод.
        if not self.ndTar0:
            TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True, tool_name="MassLinker")
        elif (self.ndTar0)and(not self.ndTar1):
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            if list_ftgSksOut:
                #Не известно, к кому это будет подсоединено и к кому получится -- рисовать от всех сокетов.
                TemplateDrawSksToolHh(drata, *list_ftgSksOut, isDrawText=False, isClassicFlow=True, tool_name="MassLinker") #"Всем к курсору!"
            else:
                TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True, tool_name="MassLinker")
        else:
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0]
            for ftgo in list_ftgSksOut:
                for ftgi in list_ftgSksIn:
                    #Т.к. "массовый" -- критерии приходится автоматизировать и сделать их едиными для всех.
                    if CompareSkLabelName(ftgo.tar, ftgi.tar, self.prefs.vmltIgnoreCase): #Соединяться только с одинаковыми по именам сокетами.
                        tgl = False
                        if self.isIgnoreExistingLinks: #Если соединяться без разбору, то исключить уже имеющиеся "желанные" связи. Нужно для эстетики.
                            for lk in ftgi.tar.vl_sold_links_final:
                                #Проверка is_linked нужна, чтобы можно было включить выключенные линки, перезаменив их.
                                if (lk.from_socket.is_linked)and(lk.from_socket==ftgo.tar):
                                    tgl = True
                            tgl = not tgl
                        else: #Иначе не трогать уже соединённых.
                            tgl = not ftgi.tar.vl_sold_is_final_linked_cou
                        if tgl:
                            self.list_equalFtgSks.append( (ftgo, ftgi) )
            if not self.list_equalFtgSks:
                DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) #Иначе вообще всё исчезнет.
            for li in self.list_equalFtgSks:
                #Т.к. поиск по именам, рисоваться здесь и подсоединяться ниже, возможно из двух (и больше) сокетов в один и тот же одновременно. Типа "конфликт" одинаковых имён.
                TemplateDrawSksToolHh(drata, li[0], li[1], isDrawText=False, isClassicFlow=True, tool_name="MassLinker") #*[ti for li in self.list_equalFtgSks for ti in li]
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            #Помимо свёрнутых также игнорируются и рероуты, потому что у них инпуты всегда одни и с одинаковыми именами.
            if nd.type=='REROUTE':
                continue
            self.ndTar1 = nd
            if isFirstActivation:
                self.ndTar0 = nd #Здесь нод-вывод устанавливается один раз.
            if self.ndTar0==self.ndTar1: #Проверка на самокопию.
                self.ndTar1 = None #Здесь нод-вход обнуляется каждый раз в случае неудачи.
            #Заметка: Первое нахождение ndTar1 -- list_equalFtgSks == [].
            if self.ndTar1:
                list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0] #Только ради условия раскрытия. Можно было и list_equalFtgSks, но опять проскальзывающие кадры.
                CheckUncollapseNodeAndReNext(nd, self, cond=list_ftgSksIn, flag=False)
            break
    def MatterPurposePoll(self):
        return self.list_equalFtgSks
    def MatterPurposeTool(self, event, prefs, tree):
        if True:
            #Если выходы нода и входы другого нода имеют в сумме 4 одинаковых сокета по названию, то происходит не ожидаемое от инструмента поведение.
            #Поэтому соединять только один линк на входной сокет (мультиинпуты не в счёт).
            set_alreadyDone = set()
            list_skipToEndEq = []
            list_skipToEndSk = []
            for li in self.list_equalFtgSks:
                sko = li[0].tar
                ski = li[1].tar
                if ski in set_alreadyDone:
                    continue
                if sko in list_skipToEndSk: #Заметка: Достаточно и линейного чтения, но пока оставлю так, чтоб наверняка.
                    list_skipToEndEq.append(li)
                    continue
                tree.links.new(sko, ski) #Заметка: Наверное лучше оставить безопасное "сырое" соединение, учитывая массовость соединения и неограниченность количества.
                VlrtRememberLastSockets(sko, ski) #Заметка: Эта и далее -- "последнее всегда последнее", эффективно-ниже проверками уже не опуститься; ну или по крайней мере на моём уровне знаний.
                if not ski.is_multi_input: #"Мультиинпуты бездонны!"
                    set_alreadyDone.add(ski)
                list_skipToEndSk.append(sko)
            #Далее обрабатываются пропущенные на предыдущем цикле.
            for li in list_skipToEndEq:
                sko = li[0].tar
                ski = li[1].tar
                if ski in set_alreadyDone:
                    continue
                set_alreadyDone.add(ski)
                tree.links.new(sko, ski)
                VlrtRememberLastSockets(sko, ski)
        else:
            for li in self.list_equalFtgSks:
                tree.links.new(li[0].tar, li[1].tar) #Соединить всех!
    def InitTool(self, event, prefs, tree):
        self.ndTar0 = None
        self.ndTar1 = None
        self.list_equalFtgSks = []
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmltIgnoreCase')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIgnoreExistingLinks').name) as dm:
            dm["ru_RU"] = "Игнорировать существующие связи"
            dm["zh_CN"] = "忽略现有链接"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmltIgnoreCase').name) as dm:
            dm["ru_RU"] = "Игнорировать регистр"
            dm["zh_CN"] = "忽略端口名称的大小写"
