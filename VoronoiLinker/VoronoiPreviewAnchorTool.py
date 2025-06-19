


class VoronoiPreviewAnchorTool(VoronoiToolSk): #Что ж, теперь это полноценный инструмент; для которого даже есть нужда в новой отдельной категории в раскладке, наверное.
    bl_idname = 'node.voronoi_preview_anchor'
    bl_label = "Voronoi Preview Anchor"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    anchorType: bpy.props.IntProperty(name="Anchor type", default=0, min=0, max=2)
    isActiveAnchor: bpy.props.BoolProperty(name="Active anchor", default=True)
    isSelectAnchor: bpy.props.BoolProperty(name="Select anchor", default=True)
    isDeleteNonCanonAnchors: bpy.props.IntProperty(name="Clear anchors", default=0, min=0, max=2)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)[0]
            for ftg in list_ftgSksOut:
                if ftg.blid!='NodeSocketVirtual':
                    self.fotagoSk = ftg
                    break
            if self.fotagoSk:
                break
    def MatterPurposeTool(self, event, prefs, tree):
        VptData.reprSkAnchor = repr(self.fotagoSk.tar)
    def InitTool(self, event, prefs, tree):
        if self.isDeleteNonCanonAnchors:
            for nd in tree.nodes:
                if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                    tree.nodes.remove(nd)
            if self.isDeleteNonCanonAnchors==2:
                if nd:=tree.nodes.get(voronoiAnchorCnName):
                    tree.nodes.remove(nd)
            return {'FINISHED'}
        if self.anchorType:
            for nd in tree.nodes:
                nd.select = False
            match self.anchorType:
                case 1:
                    rrAnch = tree.nodes.get(voronoiAnchorCnName)
                    isFirstApr = not rrAnch #Метка для обработки при первом появлении.
                    rrAnch = rrAnch or tree.nodes.new('NodeReroute')
                    rrAnch.name = voronoiAnchorCnName
                    rrAnch.label = voronoiAnchorCnName
                case 2:
                    sco = 0
                    tgl = True
                    while tgl:
                        sco += 1
                        name = voronoiAnchorDtName+str(sco)
                        tgl = not not tree.nodes.get(name, None)
                    isFirstApr = True
                    rrAnch = tree.nodes.new('NodeReroute')
                    rrAnch.name = name
                    rrAnch.label = voronoiAnchorDtName
            if self.isActiveAnchor:
                tree.nodes.active = rrAnch
            rrAnch.location = self.cursorLoc
            rrAnch.select = self.isSelectAnchor
            if isFirstApr:
                #Почему бы и нет. Зато красивый.
                rrAnch.inputs[0].type = 'COLLECTION' if self.anchorType==2 else 'MATERIAL' #Для аддонских деревьев, потому что в них "напролом" ниже не работает.
                rrAnch.outputs[0].type = rrAnch.inputs[0].type #Чтобы цвет выхода у линка был таким же.
                if self.anchorType==1:
                    #Установка напрямую `.type = 'CUSTOM'` не работает, поэтому идём напролом; спасибо обновлению Blender 3.5:
                    nd = tree.nodes.new('NodeGroupInput')
                    tree.links.new(nd.outputs[-1], rrAnch.inputs[0])
                    tree.nodes.remove(nd)
            return {'FINISHED'}
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'anchorType').name) as dm:
            dm["ru_RU"] = "Тип якоря"
            dm["zh_CN"] = "转接点的类型"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isActiveAnchor').name) as dm:
            dm["ru_RU"] = "Делать якорь активным"
            dm["zh_CN"] = "转接点设置为活动项"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectAnchor').name) as dm:
            dm["ru_RU"] = "Выделять якорь"
            dm["zh_CN"] = "转接点高亮显示"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isDeleteNonCanonAnchors').name) as dm:
            dm["ru_RU"] = "Удалить имеющиеся якори"
#            dm["zh_CN"] = ""
