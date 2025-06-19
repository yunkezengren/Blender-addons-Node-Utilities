


class EdgePanData:
    area = None #Должен был быть 'context', но он всё время None.
    ctCur = None
    #Накостылил по-быстрому:
    isWorking = False
    view2d = None
    cursorPos = Vec2((0,0))
    uiScale = 1.0
    center = Vec2((0,0))
    delta = 0.0 #Ох уж эти ваши дельты.
    zoomFac = 0.5
    speed = 1.0

def EdgePanTimer():
    delta = perf_counter()-EdgePanData.delta
    vec = EdgePanData.cursorPos*EdgePanData.uiScale
    field0 = Vec2(EdgePanData.view2d.view_to_region(vec.x, vec.y, clip=False))
    zoomWorld = (EdgePanData.view2d.view_to_region(vec.x+1000, vec.y, clip=False)[0]-field0.x)/1000
    #Ещё немного реймарчинга:
    field1 = field0-EdgePanData.center
    field2 = Vec2(( abs(field1.x), abs(field1.y) ))
    field2 = field2-EdgePanData.center+Vec2((10, 10)) #Слегка уменьшить границы для курсора, находящегося вплотную к краю экрана.
    field2 = Vec2(( max(field2.x, 0), max(field2.y, 0) ))
    ##
    xi, yi, xa, ya = EdgePanData.ctCur.GetRaw()
    speedZoomSize = Vec2((xa-xi, ya-yi))/2.5*delta #125 без дельты.
    field1 = field1.normalized()*speedZoomSize*((zoomWorld-1)/1.5+1)*EdgePanData.speed*EdgePanData.uiScale
    if (field2.x!=0)or(field2.y!=0):
        EdgePanData.ctCur.TranslateScaleFac((field1.x, field1.y), fac=EdgePanData.zoomFac)
    EdgePanData.delta = perf_counter() #"Отправляется в неизвестность" перед следующим заходом.
    EdgePanData.area.tag_redraw()
    return 0.0 if EdgePanData.isWorking else None

def EdgePanInit(self, area):
    EdgePanData.area = area
    EdgePanData.ctCur = self.ctView2d.cur
    EdgePanData.isWorking = True
    EdgePanData.cursorPos = self.cursorLoc
    EdgePanData.uiScale = self.uiScale
    EdgePanData.view2d = self.region.view2d
    EdgePanData.center = Vec2((self.region.width/2, self.region.height/2))
    EdgePanData.delta = perf_counter() #..А ещё есть "слегка-границы".
    EdgePanData.zoomFac = 1.0-self.prefs.vEdgePanFac
    EdgePanData.speed = self.prefs.vEdgePanSpeed
    bpy.app.timers.register(EdgePanTimer, first_interval=0.0)


class VoronoiOpTool(bpy.types.Operator):
    bl_options = {'UNDO'} #Вручную созданные линки undo'тся, так что и в VL ожидаемо тоже. И вообще для всех.
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' #Не знаю, зачем это нужно, но пусть будет.

class VoronoiToolFillers: #-1
    usefulnessForCustomTree = None
    usefulnessForUndefTree = None
    usefulnessForNoneTree = None
    canDrawInAddonDiscl = None
    canDrawInAppearance = None
    def CallbackDrawTool(self, drata): pass
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): pass
    def ModalTool(self, event, prefs): pass
    #def MatterPurposePoll(self): return None
    def MatterPurposeTool(self, event, prefs, tree): pass
    def InitToolPre(self, event): return {}
    def InitTool(self, event, prefs, tree): return {}
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs): pass
    @classmethod
    def BringTranslations(cls): pass
class VoronoiToolRoot(VoronoiOpTool, VoronoiToolFillers): #0
    usefulnessForUndefTree = False
    usefulnessForNoneTree = False
    canDrawInAddonDiscl = True
    canDrawInAppearance = False
    #Всегда неизбежно происходит кликанье в редакторе деревьев, где обитают ноды, поэтому для всех инструментов
    isPassThrough: bpy.props.BoolProperty(name="Pass through node selecting", default=False, description="Clicking over a node activates selection, not the tool")
    def CallbackDrawRoot(self, drata, context):
        if drata.whereActivated!=context.space_data: #Нужно, чтобы рисовалось только в активном редакторе, а не во всех у кого открыто то же самое дерево.
            return
        drata.worldZoom = self.ctView2d.GetZoom() #Получает каждый раз из-за EdgePan'а и колеса мыши. Раньше можно было бы обойтись и одноразовой пайкой.
        if self.prefs.dsIsFieldDebug:
            DrawDebug(self, drata)
        if self.tree: #Теперь для никакого дерева признаки жизни можно не подавать; выключено в связи с головной болью топологии, и пропуска инструмента для передачи хоткея в аддонских деревьях (?).
            self.CallbackDrawTool(drata)
    def ToolGetNearestNodes(self, includePoorNodes=False, cur_x_off=0):
        self.cursorLoc.x += cur_x_off    # 小王 唤起位置偏移
        return GetNearestNodesFtg(self.tree.nodes[:], self.cursorLoc, self.uiScale, includePoorNodes)
    def ToolGetNearestSockets(self, nd, cur_x_off=0):
        self.cursorLoc.x += cur_x_off    #     唤起位置偏移
        return GetNearestSocketsFtg(nd, self.cursorLoc, self.uiScale)
    def NextAssignmentRoot(self, flag):
        if self.tree:
            try:
                self.NextAssignmentTool(flag, self.prefs, self.tree)
            except:
                EdgePanData.isWorking = False #Сейчас актуально только для VLT. Возможно стоит сделать ~self.ErrorToolProc, и в VLT "давать заднюю".
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
                raise
    def ModalMouseNext(self, event, prefs):
        match event.type:
            case 'MOUSEMOVE':
                self.NextAssignmentRoot(False)
            case self.kmi.type|'ESC':
                if event.value=='RELEASE':
                    return True
        return False
    def modal(self, context, event):
        context.area.tag_redraw()
        if num:=(event.type=='WHEELUPMOUSE')-(event.type=='WHEELDOWNMOUSE'):
            self.ctView2d.cur.Zooming(self.cursorLoc, 1.0-num*0.15)
        self.ModalTool(event, self.prefs)
        if not self.ModalMouseNext(event, self.prefs):
            return {'RUNNING_MODAL'}
        #* Здесь начинается завершение инструмента *
        EdgePanData.isWorking = False
        if event.type=='ESC': #Собственно то, что и должна делать клавиша побега.
            return {'CANCELLED'}
        with TryAndPass(): #Он может оказаться уже удалённым, см. второй такой.
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
        tree = self.tree
        if not tree:
            return {'FINISHED'}
        RestoreCollapsedNodes(tree.nodes)
        if (tree)and(tree.bl_idname=='NodeTreeUndefined'): #Если дерево нодов от к.-н. аддона исчезло, то остатки имеют NodeUndefined и NodeSocketUndefined.
            return {'CANCELLED'} #Через api линки на SocketUndefined всё равно не создаются, да и делать в этом дереве особо нечего; поэтому выходим.
        ##
        if not self.MatterPurposePoll():
            return {'CANCELLED'}
        if result:=self.MatterPurposeTool(event, self.prefs, tree):
            return result
        return {'FINISHED'}
    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        self.tree = tree
        editorBlid = context.space_data.tree_type #Без нужды для `self.`?.
        self.isInvokeInClassicTree = IsClassicTreeBlid(editorBlid)
        if not(self.usefulnessForCustomTree or self.isInvokeInClassicTree):
            return {'PASS_THROUGH'} #'CANCELLED'?.
        if (not self.usefulnessForUndefTree)and(editorBlid=='NodeTreeUndefined'):
            return {'CANCELLED'} #Покидается с целью не-рисования.
        if not(self.usefulnessForNoneTree or tree):
            return {'FINISHED'}
        #Одинаковая для всех инструментов обработка пропуска выделения
        if (self.isPassThrough)and(tree)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): #Проверка на дерево вторым, для эстетической оптимизации.
            #Если хоткей вызова инструмента совпадает со снятием выделения, то выделенный строчкой выше нод будет де-выделен обратно после передачи эстафеты (но останется активным).
            #Поэтому для таких ситуаций нужно снять выделение, чтобы снова произошло переключение обратно на выделенный.
            tree.nodes.active.select = False #Но без условий, для всех подряд. Ибо ^иначе будет всегда выделение без переключения; и у меня нет идей, как бы я парился с распознаванием таких ситуаций.
            return {'PASS_THROUGH'}
        ##
        self.kmi = GetOpKmi(self, event)
        if not self.kmi:
            return {'CANCELLED'} #Если в целом что-то пошло не так, или оператор был вызван через кнопку макета.
        #Если в keymap в вызове оператора не указаны его свойства, они читаются от последнего вызова; поэтому их нужно устанавливать обратно по умолчанию.
        #Имеет смысл делать это как можно раньше; актуально для VQMT и VEST.
        for li in self.rna_type.properties:
            if li.identifier!='rna_type':
                #Заметка: Определить установленность в kmi -- наличие `kmi.properties[li.identifier]`.
                setattr(self, li.identifier, getattr(self.kmi.properties, li.identifier)) #Ради этого мне пришлось реверсинженерить Blender с отладкой. А ларчик просто открывался..
        ##
        self.prefs = Prefs() #"А ларчик просто открывался".
        self.uiScale = context.preferences.system.dpi/72
        self.cursorLoc = context.space_data.cursor_location #Это class Vector, копируется по ссылке; так что можно установить (привязать) один раз здесь и не париться.
        self.drata = VlDrawData(context, self.cursorLoc, self.uiScale, self.prefs)
        SolderThemeCols(context.preferences.themes[0].node_editor) #Так же, как и с fontId; хоть и в большинстве случаев тема не будет меняться во время всего сеанса.
        self.region = context.region
        self.ctView2d = View2D.GetFields(context.region.view2d)
        if self.prefs.vIsOverwriteZoomLimits:
            self.ctView2d.minzoom = self.prefs.vOwZoomMin
            self.ctView2d.maxzoom = self.prefs.vOwZoomMax
        ##
        if result:=self.InitToolPre(event): #Для 'Pre' менее актуально что-то возвращать.
            return result
        if result:=self.InitTool(event, self.prefs, tree): #Заметка: См. топологию: возвращение ничего равносильно возвращению `{'RUNNING_MODAL'}`.
            return result
        EdgePanInit(self, context.area)
        ##
        self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(self.CallbackDrawRoot, (self.drata, context,), 'WINDOW', 'POST_PIXEL')
        if tree: #Заметка: См. местную топологию, сам инструмент могёт, но каждый из них явно выключен для отсутствующих деревьев.
            SolderSkLinks(self.tree)
            SaveCollapsedNodes(tree.nodes)
            self.NextAssignmentRoot(True) #А всего-то нужно было перенести перед modal_handler_add(). #https://projects.blender.org/blender/blender/issues/113479
        ##
        context.area.tag_redraw() #Нужно, чтобы нарисовать при активации найденного при активации; при этом местный порядок не важен.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class VoronoiToolSk(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def InitToolPre(self, event):
        self.fotagoSk = None

class VoronoiToolPairSk(VoronoiToolSk): #2
    isCanBetweenFields: bpy.props.BoolProperty(name="Can between fields", default=True, description="Tool can connecting between different field types")
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1)
    def SkBetweenFieldsCheck(self, sk1, sk2):
        #Заметка: Учитывая предназначение и название этой функции, sk1 и sk2 в любом случае должны быть из полей, и только из них.
        return (sk1.type in set_utilTypeSkFields)and( (self.isCanBetweenFields)and(sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
    def InitToolPre(self, event):
        self.fotagoSk0 = None
        self.fotagoSk1 = None


class VoronoiToolTripleSk(VoronoiToolPairSk): #3
    def ModalTool(self, event, prefs):
        if (self.isStartWithModf)and(not self.canPickThird): #Кто будет всерьёз переключаться на выбор третьего сокета путём нажатия и отжатия к-н. модификатора?.
            # Ибо это адски дорого; коль уж выбрали хоткей без модификаторов, довольствуйтесь обрезанными возможностями. Или сделайте это себе сами.
            self.canPickThird = not(event.shift or event.ctrl or event.alt)
    def InitToolPre(self, event):
        self.fotagoSk2 = None
        self.canPickThird = False
        self.isStartWithModf = (event.shift)or(event.ctrl)or(event.alt)

class VoronoiToolNd(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawNodeFull(drata, self.fotagoNd, tool_name="隐藏选项")
    def MatterPurposePoll(self):
        return not not self.fotagoNd
    def InitToolPre(self, event):
        self.fotagoNd = None

class VoronoiToolPairNd(VoronoiToolSk): #2
    def MatterPurposePoll(self):
        return self.fotagoNd0 and self.fotagoNd1
    def InitToolPre(self, event):
        self.fotagoNd0 = None
        self.fotagoNd1 = None

class VoronoiToolAny(VoronoiToolSk, VoronoiToolNd): #2
    @staticmethod
    def TemplateDrawAny(drata, ftg, *, cond, tool_name=""):
        if cond:
            TemplateDrawNodeFull(drata, ftg, tool_name=tool_name)
        else:
            TemplateDrawSksToolHh(drata, ftg, tool_name=tool_name)      # 小王-绘制工具提示
    def MatterPurposePoll(self):
        return self.fotagoAny
    def InitToolPre(self, event):
        self.fotagoAny = None
