from .VoronoiTool import VoronoiToolSk


class VoronoiDummyTool(VoronoiToolSk):   # 快速便捷地添加新工具的模板
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    usefulnessForCustomTree = True
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=0):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=0)
            ftgSkIn = list_ftgSksIn[0] if list_ftgSksIn else None
            ftgSkOut = list_ftgSksOut[0] if list_ftgSksOut else None
            self.fotagoSk = MinFromFtgs(ftgSkOut, ftgSkIn)
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk, flag=False)
            break
        #todo0NA Я придумал что делать с концепцией, когда имеются разные критерии от isFirstActivation'а, и второй находится сразу рядом после первого моментально. Явное (и насильное) сравнение на своего и отмена.
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def MatterPurposeTool(self, event, prefs, tree):
        sk = self.fotagoSk.tar
        sk.name = sk.name if (sk.name)and(sk.name[0]=="\"") else f'"{sk.name}"'
        sk.node.label = "Hi i am vdt. See source code"
        VlrtRememberLastSockets(sk if sk.is_output else None, None)
    def InitTool(self, event, prefs, tree):
        self.fotagoSk = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddNiceColorProp(col, prefs,'vdtDummy')
    @classmethod
    def BringTranslations(cls):
        pass
