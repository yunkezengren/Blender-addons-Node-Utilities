
class VoronoiLinksTransferTool(VoronoiToolPairNd): #Todo2v6 кандидат на слияние с VST и превращение в "PairAny".
    bl_idname = 'node.voronoi_links_transfer'
    bl_label = "Voronoi Links Transfer"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isByIndexes: bpy.props.BoolProperty(name="Transfer by indexes", default=False)
    def CallbackDrawTool(self, drata):
        #Паттерн VLT
        if not self.fotagoNd0:
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        elif (self.fotagoNd0)and(not self.fotagoNd1):
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1, tool_name="Transfer")
            TemplateDrawSksToolHh(drata, None, tool_name="Links Transfer")
        else:
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1, tool_name="Transfer")
            TemplateDrawNodeFull(drata, self.fotagoNd1, side=1, tool_name="Transfer")
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoNd0 = None
        self.fotagoNd1 = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=False, cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if isFirstActivation:
                self.fotagoNd0 = ftgNd
            self.fotagoNd1 = ftgNd
            if self.fotagoNd0.tar==self.fotagoNd1.tar:
                self.fotagoNd1 = None
            #Свершилось. Теперь у VL есть два нода.
            #Внезапно оказалось, что позиция "попадания" для нода буквально прилипает к нему, что весьма необычно наблюдать, когда тут вся тусовка про сокеты.
            # Должна ли она скользить вместо прилипания?. Скорее всего нет, ведь иначе неизбежны осеориентированные проекции, визуально "затирающие" информацию.
            # А также они оба будут изменяться от движения курсора, от чего не будет интуитивно понятно, кто первый, а кто второй,
            # В отличие от прилипания, когда точно понятно, что "вот этот вот первый"; что особенно актуально для этого инструмента, где важно, какой нод был выбран первым.
            if prefs.dsIsSlideOnNodes: #Не приспичило, но пусть будет.
                if self.fotagoNd0:
                    self.fotagoNd0.pos = GenFtgFromNd(self.fotagoNd0.tar, self.cursorLoc, self.uiScale).pos
            break
    def MatterPurposeTool(self, event, prefs, tree):
        ndFrom = self.fotagoNd0.tar
        ndTo = self.fotagoNd1.tar
        def NewLink(sk, lk):
            if sk.is_output:
                tree.links.new(sk, lk.to_socket)
                if lk.to_socket.is_multi_input:
                    tree.links.remove(lk)
            else:
                tree.links.new(lk.from_socket, sk)
                tree.links.remove(lk)
        def GetOnlyVisualSks(puts):
            return [sk for sk in puts if sk.enabled and not sk.hide]
        SolderSkLinks(tree) #Иначе на vl_sold_links_final будет '... has been removed'; но можно было обойтись и обычным 'sk.links'.
        if not self.isByIndexes:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for sk in putsFrom:
                    for lk in sk.vl_sold_links_final:
                        if not lk.is_muted:
                            skTar = putsTo.get(GetSkLabelName(sk))
                            if skTar:
                                NewLink(skTar, lk)
        else:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for zp in zip(GetOnlyVisualSks(putsFrom), GetOnlyVisualSks(putsTo)):
                    for lk in zp[0].vl_sold_links_final:
                        if not lk.is_muted:
                            NewLink(zp[1], lk)
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(VoronoiLinksTransferTool,'isByIndexes').name) as dm:
            dm["ru_RU"] = "Переносить по индексам"
            dm["zh_CN"] = "按顺序传输"
