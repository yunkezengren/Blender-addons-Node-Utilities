


class VoronoiLazyNodeStencilsTool(VoronoiToolPairSk): #Первый инструмент, созданный по запросам извне, а не по моим личным хотелкам.
    bl_idname = 'node.voronoi_lazy_node_stencils'
    bl_label = "Voronoi Lazy Node Stencils" #Три буквы на инструмент, дожили.
    def CallbackDrawTool(self, drata):
        #Заметка: Для разных гендеров получается не очевидное соответствие стороне текста гендеру сокета. Наверное, придётся смириться.
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, tool_name="Lazy Node Stencils")
        if ( (not not self.fotagoSk0)^(not not self.fotagoSk1) )and(drata.dsIsDrawPoint):
            DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) #Для эстетики.
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        def FindAnySk():
            ftgSkOut, ftgSkIn = None, None
            for ftg in list_ftgSksOut:
                ftgSkOut = ftg
                break
            for ftg in list_ftgSksIn:
                ftgSkIn = ftg
                break
            return MinFromFtgs(ftgSkOut, ftgSkIn)
        self.fotagoSk1 = None
        #Из-за своего предназначения, этот инструмент гарантированно получает первый попавшийся сокет.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            if isFirstActivation:
                self.fotagoSk0 = FindAnySk()
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk0, flag=True)
            skFirst = FtgGetTargetOrNone(self.fotagoSk0)
            if skFirst:
                self.fotagoSk1 = FindAnySk()
                if self.fotagoSk1:
                    if skFirst==self.fotagoSk1.tar:
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        VlnstLazyTemplate(prefs, tree, FtgGetTargetOrNone(self.fotagoSk0), FtgGetTargetOrNone(self.fotagoSk1), self.cursorLoc)
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddNiceColorProp(col, prefs,'vlnstNonColorName')
        LyAddNiceColorProp(col, prefs,'vlnstLastExecError', ico='ERROR' if prefs.vlnstLastExecError else 'NONE', decor=0)
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetPrefsRnaProp('vlnstNonColorName').name) as dm:
            dm["ru_RU"] = "Название \"Не-цветовых данных\""
            dm["zh_CN"] = "图片纹理色彩空间名称"
        with VlTrMapForKey(GetPrefsRnaProp('vlnstLastExecError').name) as dm:
            dm["ru_RU"] = "Последняя ошибка выполнения"
            dm["zh_CN"] = "上次运行时错误"
