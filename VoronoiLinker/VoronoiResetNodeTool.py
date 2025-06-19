


class VoronoiResetNodeTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_reset_node'
    bl_label = "Voronoi Reset Node"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isResetEnums: bpy.props.BoolProperty(name="Reset enums", default=False)
    isResetOnDrag: bpy.props.BoolProperty(name="Reset on grag (not recommended)", default=False)
    isSelectResetedNode: bpy.props.BoolProperty(name="Select reseted node", default=True)
    def CallbackDrawTool(self, drata):              # 小王-工具提示
        if self.isResetEnums:
            mode = "完全重置节点"
        else:
            mode = "重置节点"
        TemplateDrawNodeFull(drata, self.fotagoNd, tool_name=mode)
        # self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE', tool_name=name)
    def VrntDoResetNode(self, ndTar, tree):
        ndNew = tree.nodes.new(ndTar.bl_idname)
        ndNew.location = ndTar.location
        with TryAndPass(): #SimRep'ы.
            for cyc, sk in enumerate(ndTar.outputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(ndNew.outputs[cyc], lk.to_socket)
            for cyc, sk in enumerate(ndTar.inputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(lk.from_socket, ndNew.inputs[cyc])
        if ndNew.type=='GROUP':
            ndNew.node_tree = ndTar.node_tree
        if not self.isResetEnums: #Если не сбрасывать перечисления, то перенести их на новый нод.
            for li in ndNew.rna_type.properties.items():
                if (not li[1].is_readonly)and(getattr(li[1],'enum_items', None)):
                    setattr(ndNew, li[0], getattr(ndTar, li[0]))
        tree.nodes.remove(ndTar)
        tree.nodes.active = ndNew
        ndNew.select = self.isSelectResetedNode
        return ndNew
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        SolderSkLinks(tree)
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=True, cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE': #"Вы что, хотите пересоздавать рероуты?".
                continue
            self.fotagoNd = ftgNd
            if (self.isResetOnDrag)and(nd not in self.set_done):
                self.set_done.add(self.VrntDoResetNode(self.fotagoNd.tar, tree))
                self.NextAssignmentTool(isFirstActivation, prefs, tree)
                #В целом с 'isResetOnDrag' лажа -- нужно перерисовать для новосозданных нодов, чтобы получить их высоту; или у меня нет идей.
                #И точка цепляется в угол нодов на один кадр.
            break
    def MatterPurposePoll(self):
        return (not self.isResetOnDrag)and(self.fotagoNd)
    def MatterPurposeTool(self, event, prefs, tree):
        self.VrntDoResetNode(self.fotagoNd.tar, tree)
    def InitTool(self, event, prefs, tree):
        self.set_done = set() #Без этого будет очень "страшна"-поведение, а если переусердствовать, то скорее всего краш.
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetEnums').name) as dm:
            dm["ru_RU"] = "Восстанавливать свойства перечисления"
            dm["zh_CN"] = "恢复下拉列表里的选择"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetOnDrag').name) as dm:
            dm["ru_RU"] = "Восстанавливать при ведении курсора (не рекомендуется)"
#            dm["zh_CN"] = "悬停时恢复"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectResetedNode').name) as dm:
            dm["ru_RU"] = "Выделять восстановленный нод"
            dm["zh_CN"] = "选择重置的节点"
