from .utils_translate import GetAnnotFromCls, VlTrMapForKey
from .utils_translate import *
from .utils_node import *
from .utils_ui import *
from .utils_color import *
from .VoronoiTool import *
from .utils_solder import *
from .globals import *
from .forward_class import *
from .forward_func import *
from .utils_drawing import *
from .VoronoiTool import VoronoiToolRoot


#"批量链接器" -- 就像链接器一样, 只是一次性处理多个 (显而易见).
#请查看 github 上的 wiki, 看看批量链接器的5个使用示例. 如果你发现这个工具还有其他不寻常的用法, 请告诉我.
class VoronoiMassLinkerTool(VoronoiToolRoot): #"猫狗合体", 既不是节点, 也不是接口.
    bl_idname = 'node.voronoi_mass_linker'
    bl_label = "Voronoi MassLinker" #唯一一个没有空格的. 因为它太像猫狗了))00)0
    # 说真的, 它的确是最奇怪的. 它模仿 VLT 的 dsIsAlwaysLine. 如果从多个连接到一个, SocketArea 会堆叠起来. 它在绘制函数中写入...
    # 而且, 正是它出现在/将出现在插件的预览图上, 因为它在所有工具中具有最大的视觉表现力 (而且没有上限).
    usefulnessForCustomTree = True
    isIgnoreExistingLinks: bpy.props.BoolProperty(name="Ignore existing links", default=False)
    def CallbackDrawTool(self, drata):
        #这里违反了本地 VL 的读写概念, CallbackDraw 会查找并记录找到的接口, 而不是简单地读取和绘制. 我想这样更容易实现这个工具.
        self.list_equalFtgSks.clear() #每次都清除. P.s. 在开始时执行此操作很重要, 而不是在两个节点的分支中.
        if not self.ndTar0:
            TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True, tool_name="MassLinker")
        elif (self.ndTar0)and(not self.ndTar1):
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            if list_ftgSksOut:
                #不知道它会连接到谁, 以及会成功连接到谁 -- 从所有接口开始绘制.
                TemplateDrawSksToolHh(drata, *list_ftgSksOut, isDrawText=False, isClassicFlow=True, tool_name="MassLinker") #"全体到光标!"
            else:
                TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True, tool_name="MassLinker")
        else:
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0]
            for ftgo in list_ftgSksOut:
                for ftgi in list_ftgSksIn:
                    #因为是“批量”的 -- 标准必须自动化, 并对所有情况都统一.
                    if CompareSkLabelName(ftgo.tar, ftgi.tar, self.prefs.vmltIgnoreCase): #只与名称相同的接口连接.
                        tgl = False
                        if self.isIgnoreExistingLinks: #如果是不分青红皂白地连接, 就排除已经存在的“期望”连接. 这是为了美观.
                            for lk in ftgi.tar.vl_sold_links_final:
                                #需要检查 is_linked, 以便可以启用已禁用的链接, 替换它们.
                                if (lk.from_socket.is_linked)and(lk.from_socket==ftgo.tar):
                                    tgl = True
                            tgl = not tgl
                        else: #否则, 不要动已经连接的.
                            tgl = not ftgi.tar.vl_sold_is_final_linked_cou
                        if tgl:
                            self.list_equalFtgSks.append( (ftgo, ftgi) )
            if not self.list_equalFtgSks:
                DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) #否则一切都会消失.
            for li in self.list_equalFtgSks:
                #因为是按名称搜索, 所以这里会绘制并可能在下面同时从两个 (或更多) 接口连接到同一个接口. 就像同名“冲突”一样.
                TemplateDrawSksToolHh(drata, li[0], li[1], isDrawText=False, isClassicFlow=True, tool_name="MassLinker") #*[ti for li in self.list_equalFtgSks for ti in li]
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            #除了折叠的节点, 还忽略了转接点, 因为它们的输入总是相同的, 并且名称相同.
            if nd.type=='REROUTE':
                continue
            self.ndTar1 = nd
            if isFirstActivation:
                self.ndTar0 = nd #这里的输出节点只设置一次.
            if self.ndTar0==self.ndTar1: #检查是否是自我复制.
                self.ndTar1 = None #这里的输入节点在失败时每次都会被清空.
            #注意: 第一次找到 ndTar1 时 -- list_equalFtgSks == [].
            if self.ndTar1:
                list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0] #仅为了展开的条件. 也可以用 list_equalFtgSks, 但又会有跳帧问题.
                CheckUncollapseNodeAndReNext(nd, self, cond=list_ftgSksIn, flag=False)
            break
    def MatterPurposePoll(self):
        return self.list_equalFtgSks
    def MatterPurposeTool(self, event, prefs, tree):
        if True:
            #如果一个节点的输出和另一个节点的输入总共有4个同名接口, 就会发生与工具预期不符的行为.
            #因此, 每个输入接口只连接一个链接 (多输入接口不计).
            set_alreadyDone = set()
            list_skipToEndEq = []
            list_skipToEndSk = []
            for li in self.list_equalFtgSks:
                sko = li[0].tar
                ski = li[1].tar
                if ski in set_alreadyDone:
                    continue
                if sko in list_skipToEndSk: #注意: 线性读取就足够了, 但暂时保持这样以确保万无一失.
                    list_skipToEndEq.append(li)
                    continue
                tree.links.new(sko, ski) #注意: 考虑到批量连接和数量不限, 最好还是保留安全的“原始”连接.
                VlrtRememberLastSockets(sko, ski) #注意: 这行和后面的 -- “最后一个永远是最后一个”, 更高效的下面检查已经无法实现了; 至少以我的知识水平是这样.
                if not ski.is_multi_input: #"多输入是无底洞!"
                    set_alreadyDone.add(ski)
                list_skipToEndSk.append(sko)
            #接下来处理上一个循环中跳过的.
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
                tree.links.new(li[0].tar, li[1].tar) #连接所有!
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
            dm["zh_CN"] = "忽略接口名称的大小写"