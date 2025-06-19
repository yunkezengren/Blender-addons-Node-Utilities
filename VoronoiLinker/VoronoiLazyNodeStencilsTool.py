from .VoronoiTool import VoronoiToolPairSk

class VoronoiLazyNodeStencilsTool(VoronoiToolPairSk): # 第一个应外部请求而非个人意愿创建的工具.
    bl_idname = 'node.voronoi_lazy_node_stencils'
    bl_label = "Voronoi Lazy Node Stencils" # 每个工具三个字母, 真是够了.
    def CallbackDrawTool(self, drata):
        # 注意: 对于不同的性别, 文本侧与套接字性别的对应关系不明显. 大概要接受了.
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, tool_name="Lazy Node Stencils")
        if ( (not not self.fotagoSk0)^(not not self.fotagoSk1) )and(drata.dsIsDrawPoint):
            DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) # 为了美观.
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
        # 由于其目的, 这个工具保证会获取第一个遇到的套接字.
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