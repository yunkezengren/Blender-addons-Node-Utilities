


fitVstModeItems = ( ('SWAP', "Swap",     "All links from the first socket will be on the second, from the second on the first"),
                    ('ADD',  "Add",      "Add all links from the second socket to the first one"),
                    ('TRAN', "Transfer", "Move all links from the second socket to the first one with replacement") )
class VoronoiSwapperTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode:     bpy.props.EnumProperty(name="Mode", default='SWAP', items=fitVstModeItems)
    isCanAnyType: bpy.props.BoolProperty(name="Can swap with any socket type", default=False)
    def CallbackDrawTool(self, drata):      # 我模仿着加的
        # 小王-模式名匹配
        name = { 'SWAP': "交换连线",
                 'ADD':  "移动连线",
                 'TRAN': "移动并替换连线",
                }
        mode= name[self.toolMode]
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, tool_name=mode,)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            #За основу были взяты критерии от Миксера.
            if isFirstActivation:
                ftgSkOut, ftgSkIn = None, None
                for ftg in list_ftgSksOut: #todo0NA да это же Findanysk!?
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkOut = ftg
                        break
                for ftg in list_ftgSksIn:
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkIn = ftg
                        break
                #Разрешить возможность "добавлять" и для входов тоже, но только для мультиинпутов, ибо очевидное
                if (self.toolMode=='ADD')and(ftgSkIn):
                    #Проверка по типу, но не по 'is_multi_input', чтобы из обычного в мультиинпут можно было добавлять.
                    if (ftgSkIn.blid not in ('NodeSocketGeometry','NodeSocketString')):#or(not ftgSkIn.tar.is_multi_input): #Без второго условия больше возможностей.
                        ftgSkIn = None
                self.fotagoSk0 = MinFromFtgs(ftgSkOut, ftgSkIn)
            #Здесь вокруг аккумулировалось много странных проверок с None и т.п. -- результат соединения вместе многих типа высокоуровневых функций, что я понаизобретал.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut if skOut0.is_output else list_ftgSksIn:
                    if ftg.blid=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.bl_idname==ftg.blid)or(self.SkBetweenFieldsCheck(skOut0, ftg.tar)):
                        self.fotagoSk1 = ftg
                    if self.fotagoSk1: #В случае успеха прекращать поиск.
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                    self.fotagoSk1 = None
                    break #Ломать для isCanAnyType, когда isFirstActivation==False и сокет оказался самокопией; чтобы не находил сразу два нода.
                if not self.isCanAnyType:
                    if not(self.fotagoSk1 or isFirstActivation): #Если нет результата, продолжаем искать.
                        continue
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            break
    def MatterPurposePoll(self):
        return self.fotagoSk0 and self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        skIo0 = self.fotagoSk0.tar
        skIo1 = self.fotagoSk1.tar
        match self.toolMode:
            case 'SWAP':
                #Поменять местами все соединения у первого и второго сокета:
                list_memSks = []
                if skIo0.is_output: #Проверка одинаковости is_output -- забота для NextAssignmentTool().
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  Чтобы линк от нода не создался сам в себя. Проверять нужно у всех и таковые не обрабатывать.
                            list_memSks.append(lk.to_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.to_node!=skIo0.node: # T 0  ^
                            tree.links.new(skIo0, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Для мультиинпутов удалить.
                                tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(skIo1, li)
                else:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            list_memSks.append(lk.from_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.from_node!=skIo0.node: # F 0  ^
                            tree.links.new(lk.from_socket, skIo0)
                            tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(li, skIo1)
            case 'ADD'|'TRAN':
                #Просто добавить линки с первого сокета на второй. Aka объединение, добавление.
                if self.toolMode=='TRAN':
                    #Тоже самое, как и добавление, только с потерей связей у первого сокета.
                    for lk in skIo1.vl_sold_links_final:
                        tree.links.remove(lk)
                if skIo0.is_output:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  ^
                            tree.links.new(skIo1, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Без этого lk всё равно указывает на "добавленный" линк, от чего удаляется. Поэтому явная проверка для мультиинпутов.
                                tree.links.remove(lk)
                else: #Добавлено ради мультиинпутов.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            tree.links.new(lk.from_socket, skIo1)
                            tree.links.remove(lk)
        #VST VLRT же без нужды, да ведь?
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.SWAP.name) as dm:
            dm["ru_RU"] = "Поменять"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.SWAP.description) as dm:
            dm["ru_RU"] = "Все линки у первого сокета будут на втором, у второго на первом."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.ADD.name) as dm:
            dm["ru_RU"] = "Добавить"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.ADD.description) as dm:
            dm["ru_RU"] = "Добавить все линки со второго сокета на первый. Второй будет пустым."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.TRAN.name) as dm:
            dm["ru_RU"] = "Переместить"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(tran.TRAN.description) as dm:
            dm["ru_RU"] = "Переместить все линки со второго сокета на первый с заменой."
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanAnyType').name) as dm:
            dm["ru_RU"] = "Может меняться с любым типом"
            dm["zh_CN"] = "可以与任何类型交换"
