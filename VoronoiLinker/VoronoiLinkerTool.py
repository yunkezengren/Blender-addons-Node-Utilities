


def is_unlink_route(node):
    if node.type == 'REROUTE' and (not (node.inputs[0].links or node.outputs[0].links)):
        return True       # 转接点没连线
    return False
link_same_socket_types = ['SHADER', 'STRING', 'GEOMETRY','OBJECT', 'COLLECTION', 'MATERIAL', 'TEXTURE', 'IMAGE']
#На самых истоках весь аддон создавался только ради этого инструмента. А то-то вы думаете названия одинаковые.
#Но потом я подахренел от обузданных возможностей, и меня понесло... понесло на создание мейнстримной троицы. Но этого оказалось мало, и теперь инструментов больше чем 7. Чума!
#Дублирующие комментарии есть только здесь (и в целом по убыванию). При спорных ситуациях обращаться к VLT для подражания, как к истине в последней инстанции.
class VoronoiLinkerTool(VoronoiToolPairSk): #Святая святых. То ради чего. Самый первый. Босс всех инструментов. Во славу великому полю расстояния!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSkOut, self.fotagoSkIn, sideMarkHh=-1, isClassicFlow=True, tool_name="Linker")
    @staticmethod
    def SkPriorityIgnoreCheck(sk): #False -- игнорировать.
        #Эта функция была добавлена по запросам извне (как и VLNST).
        set_ndBlidsWithAlphaSk = {'ShaderNodeTexImage', 'GeometryNodeImageTexture', 'CompositorNodeImage', 'ShaderNodeValToRGB', 'CompositorNodeValToRGB'}
        if sk.node.bl_idname in set_ndBlidsWithAlphaSk:
            return sk.name!="Alpha" #sk!=sk.node.outputs[1]
        return True
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): #Todo0NA ToolAssignmentFirst, Next, /^Root/; несколько NA(), нод сокет на первый, нод сокет на второй.
        #В случае не найденного подходящего предыдущий выбор остаётся, отчего не получится вернуть курсор обратно и "отменить" выбор, что очень неудобно.
        self.fotagoSkIn = None #Поэтому обнуляется каждый раз перед поиском.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=-20):
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=-20)
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    if (self.isFirstCling)or(ftg.blid!='NodeSocketVirtual')and( (not prefs.vltPriorityIgnoring)or(self.SkPriorityIgnoreCheck(ftg.tar)) ):
                        self.fotagoSkOut = ftg
                        break
            self.isFirstCling = True
            #Получить вход по условиям:
            skOut = FtgGetTargetOrNone(self.fotagoSkOut)
            if skOut: #Первый заход всегда isFirstActivation==True, однако нод может не иметь выходов.
                #Заметка: Нод сокета активации инструмента (isFirstActivation==True) в любом случае нужно разворачивать.
                #Свёрнутость для рероутов работает, хоть и не отображается визуально; но теперь нет нужды обрабатывать, ибо поддержка свёрнутости введена.
                CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
                #На этом этапе условия для отрицания просто найдут другой результат. "Прицепится не к этому, так к другому".
                for ftg in list_ftgSksIn:
                    #Заметка: Оператор `|=` всё равно заставляет вычисляться правый операнд.
                    skIn = ftg.tar
                    #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет с обеих сторон, минуя различные типы
                    tgl = self.SkBetweenFieldsCheck(skIn, skOut)or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(prefs.vltReroutesCanInAnyType)
                    #Работа с интерфейсами переехала в VIT, теперь только между виртуальными
                    tgl = (tgl)or( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') )
                    #Если имена типов одинаковые
                    tgl = (tgl)or(skIn.bl_idname==skOut.bl_idname) #Заметка: Включая аддонские сокеты.
                    #Если аддонские сокеты в классических деревьях -- можно и ко всем классическим, классическим можно ко всем аддонским
                    tgl = (tgl)or(self.isInvokeInClassicTree)and(IsClassicSk(skOut)^IsClassicSk(skIn))
                    # 小王-限制旋转和矩阵接口
                    if skOut.type == "MATRIX":
                        tgl = (skIn.type in ["MATRIX", "ROTATION"])
                    if skOut.type == "ROTATION":
                        tgl = (skIn.type in ["ROTATION", "MATRIX", "VECTOR"])
                    # 小王-只能连到相同类型的接口上
                    if skOut.type in link_same_socket_types:
                        tgl = skIn.type==skOut.type
                    if skIn.type in link_same_socket_types:
                        tgl = skIn.type==skOut.type
                    # 没连线的转接点,就都可以连
                    if is_unlink_route(skOut.node):
                        tgl = True
                    if is_unlink_route(skIn.node):      # from_socket 
                        tgl = True
                    #Заметка: SkBetweenFieldsCheck() проверяет только меж полями, поэтому явная проверка одинаковости `bl_idname`.
                    if tgl:
                        self.fotagoSkIn = ftg
                        break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
                #На этом этапе условия для отрицания сделают результат никаким. Типа "Ничего не нашлось"; и будет обрабатываться соответствующим рисованием.
                if self.fotagoSkIn:
                    if self.fotagoSkOut.tar.node==self.fotagoSkIn.tar.node: #Если для выхода ближайший вход -- его же нод
                        self.fotagoSkIn = None
                    elif self.fotagoSkOut.tar.vl_sold_is_final_linked_cou: #Если выход уже куда-то подсоединён, даже если это выключенные линки (но из-за пайки их там нет).
                        for lk in self.fotagoSkOut.tar.vl_sold_links_final:
                            if lk.to_socket==self.fotagoSkIn.tar: #Если ближайший вход -- один из подсоединений выхода, то обнулить => "желаемое" соединение уже имеется.
                                self.fotagoSkIn = None
                                #Используемый в проверке выше "self.fotagoSkIn" обнуляется, поэтому нужно выходить, иначе будет попытка чтения из несуществующего элемента следующей итерацией.
                                break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkIn, flag=False) #"Мейнстримная" обработка свёрнутости.
            break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
    def ModalMouseNext(self, event, prefs):
        if event.type==prefs.vltRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState: #Дублирование от ниже. Не знаю как придумать это за один заход.
                self.NextAssignmentRoot(True)
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState: #Заметка: Требует существования, забота вызывающей стороны.
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    if event.value=='RELEASE':
                        return True
        return False
    def MatterPurposePoll(self):
        return self.fotagoSkOut and self.fotagoSkIn
    def MatterPurposeTool(self, event, prefs, tree):
        sko = self.fotagoSkOut.tar
        ski = self.fotagoSkIn.tar
        ##
        tree.links.new(sko, ski) #Самая важная строчка снова стала низкоуровневой.
        ##
        if ski.is_multi_input: #Если мультиинпут, то реализовать адекватный порядок подключения.
            #Моя личная хотелка, которая чинит странное поведение, и делает его логически-корректно-ожидаемым. Накой смысол последние соединённые через api лепятся в начало?
            list_skLinks = []
            for lk in ski.vl_sold_links_final:
                #Запомнить все имеющиеся линки по сокетам, и удалить их:
                list_skLinks.append((lk.from_socket, lk.to_socket, lk.is_muted))
                tree.links.remove(lk)
            #До версии b3.5 обработка ниже нужна была, чтобы новый io группы дважды не создавался.
            #Теперь без этой обработки Блендер или крашнется, или линк из виртуального в мультиинпут будет невалидным
            if sko.bl_idname=='NodeSocketVirtual':
                sko = sko.node.outputs[-2]
            tree.links.new(sko, ski) #Соединить очередной первым.
            for li in list_skLinks: #Восстановить запомненные. #todo0VV для поддержки старых версий: раньше было [:-1], потому что последний в списке уже являлся желанным, что был соединён строчкой выше.
                tree.links.new(li[0], li[1]).is_muted = li[2]
        VlrtRememberLastSockets(sko, ski) #Запомнить сокеты для VLRT, которые теперь являются "последними использованными".
        if prefs.vltSelectingInvolved:
            for nd in tree.nodes:
                nd.select = False
            sko.node.select = True
            ski.node.select = True
            tree.nodes.active = sko.node #P.s. не знаю, почему именно он; можно было и от ski. А делать из этого опцию как-то так себе.
    def InitTool(self, event, prefs, tree):
        self.fotagoSkOut = None
        self.fotagoSkIn = None
        self.repickState = False
        self.isFirstCling = False #Для SkPriorityIgnoreCheck и перевобора на виртуальные.
        if prefs.vltDeselectAllNodes:
            bpy.ops.node.select_all(action='DESELECT')
            tree.nodes.active = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vltRepickKey')
        LyAddLeftProp(col, prefs,'vltReroutesCanInAnyType')
        LyAddLeftProp(col, prefs,'vltDeselectAllNodes')
        LyAddLeftProp(col, prefs,'vltPriorityIgnoring')
        LyAddLeftProp(col, prefs,'vltSelectingInvolved')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetPrefsRnaProp('vltRepickKey').name) as dm:
            dm["ru_RU"] = "Клавиша перевыбора"
            dm["zh_CN"] = "重选快捷键"
        with VlTrMapForKey(GetPrefsRnaProp('vltReroutesCanInAnyType').name) as dm:
            dm["ru_RU"] = "Рероуты могут подключаться в любой тип"
            dm["zh_CN"] = "重新定向节点可以连接到任何类型的节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltDeselectAllNodes').name) as dm:
            dm["ru_RU"] = "Снять выделение со всех нодов при активации"
            dm["zh_CN"] = "快速连接时取消选择所有节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').name) as dm:
            dm["ru_RU"] = "Приоритетное игнорирование"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').description) as dm:
            dm["ru_RU"] = "Высокоуровневое игнорирование \"надоедливых\" сокетов при первом поиске.\n(Сейчас только \"Alpha\"-сокет у нод изображений)"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltSelectingInvolved').name) as dm:
            dm["ru_RU"] = "Выделять задействованные ноды"
            dm["zh_CN"] = "快速连接后自动选择连接的节点"
