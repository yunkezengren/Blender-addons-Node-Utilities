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
from .VoronoiTool import VoronoiToolPairSk


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
            #基于Mixer的标准.
            if isFirstActivation:
                ftgSkOut, ftgSkIn = None, None
                for ftg in list_ftgSksOut: #todo0NA 但这不就是Findanysk吗!?
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkOut = ftg
                        break
                for ftg in list_ftgSksIn:
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkIn = ftg
                        break
                #也允许对输入接口使用“添加”功能，但仅限于多输入接口，因为这很明显
                if (self.toolMode=='ADD')and(ftgSkIn):
                    #按类型检查，而不是按'is_multi_input'，这样就可以从常规输入添加到多输入.
                    if (ftgSkIn.blid not in ('NodeSocketGeometry','NodeSocketString')):#or(not ftgSkIn.tar.is_multi_input): #没有第二个条件可能性更多.
                        ftgSkIn = None
                self.fotagoSk0 = MinFromFtgs(ftgSkOut, ftgSkIn)
            #这里积累了很多奇怪的关于None等的检查 -- 这是我将自己发明的许多高级函数连接在一起的结果.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut if skOut0.is_output else list_ftgSksIn:
                    if ftg.blid=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.bl_idname==ftg.blid)or(self.SkBetweenFieldsCheck(skOut0, ftg.tar)):
                        self.fotagoSk1 = ftg
                    if self.fotagoSk1: #如果成功则停止搜索.
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #检查是否为自我复制.
                    self.fotagoSk1 = None
                    break #当isFirstActivation==False且接口为自我复制时，为isCanAnyType中断循环；以免一次找到两个节点.
                if not self.isCanAnyType:
                    if not(self.fotagoSk1 or isFirstActivation): #如果没有结果，则继续搜索.
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
                #交换第一个和第二个接口的所有连接:
                list_memSks = []
                if skIo0.is_output: #检查 is_output 的一致性是 NextAssignmentTool() 的任务.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  以防止节点创建指向自身的连接。需要检查所有情况并且不处理此类连接.
                            list_memSks.append(lk.to_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.to_node!=skIo0.node: # T 0  ^
                            tree.links.new(skIo0, lk.to_socket)
                            if lk.to_socket.is_multi_input: #对于多输入接口则删除.
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
                #只需将第一个接口的连接添加到第二个接口。即合并、添加.
                if self.toolMode=='TRAN':
                    #与添加相同，只是第一个接口会丢失连接.
                    for lk in skIo1.vl_sold_links_final:
                        tree.links.remove(lk)
                if skIo0.is_output:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  ^
                            tree.links.new(skIo1, lk.to_socket)
                            if lk.to_socket.is_multi_input: #没有这个，lk仍然会指向“已添加”的连接，从而被删除。因此需要对多输入进行显式检查.
                                tree.links.remove(lk)
                else: #为了多输入接口而添加.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            tree.links.new(lk.from_socket, skIo1)
                            tree.links.remove(lk)
        #VST VLRT是不需要的，对吧？
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.SWAP.name) as dm:
            dm["ru_RU"] = "Поменять"
            dm["zh_CN"] = "交换"
        with VlTrMapForKey(tran.SWAP.description) as dm:
            dm["ru_RU"] = "Все линки у первого сокета будут на втором, у второго на первом."
            dm["zh_CN"] = "第一个接口的所有连线将移至第二个，第二个的将移至第一个。"
        with VlTrMapForKey(tran.ADD.name) as dm:
            dm["ru_RU"] = "Добавить"
            dm["zh_CN"] = "添加"
        with VlTrMapForKey(tran.ADD.description) as dm:
            dm["ru_RU"] = "Добавить все линки со второго сокета на первый. Второй будет пустым."
            dm["zh_CN"] = "将第二个接口的所有连线添加到第一个。第二个将变为空。"
        with VlTrMapForKey(tran.TRAN.name) as dm:
            dm["ru_RU"] = "Переместить"
            dm["zh_CN"] = "转移"
        with VlTrMapForKey(tran.TRAN.description) as dm:
            dm["ru_RU"] = "Переместить все линки со второго сокета на первый с заменой."
            dm["zh_CN"] = "将第二个接口的所有连线转移到第一个并替换现有连线。"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanAnyType').name) as dm:
            dm["ru_RU"] = "Может меняться с любым типом"
            dm["zh_CN"] = "可以与任何类型交换"