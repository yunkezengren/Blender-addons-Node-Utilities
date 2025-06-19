import bpy
from builtins import len as length
from bpy.types import (NodeSocket, UILayout)
# from .common_func import sk_label_or_name, index_switch_add_input
from .common_forward_func import *


# Equestrian 的意思是"骑手"或"马术的",取其驾驭、控制的寓意.似乎是专门用来操作管理有 item 的节点, 比如:
# 这些节点都有一个共同点: 它们内部有自己的items, 可以动态地添加、删除、移动它们上面的插槽 (socket).
# 提供了一套统一的 API 来驾驭它们的内部接口, 抽象成了统一的操作
class Node_Items_Manager():
    set_equestrianNodeTypes = {'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT', 
                               'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 
                               'REPEAT_INPUT', 'REPEAT_OUTPUT',
                               "FOREACH_GEOMETRY_ELEMENT_INPUT", "FOREACH_GEOMETRY_ELEMENT_OUTPUT",
                               'MENU_SWITCH', 'BAKE', 'CAPTURE_ATTRIBUTE', 'INDEX_SWITCH'               # 小王-更改接口名称
                               }
    # is_simrep = property(lambda a: a.type in ('SIM','REP'))     # 小王-插入接口
    has_extend_socket = property(lambda a: a.type in ('SIM','REP', 'MENU', 'CAPTURE', 'BAKE'))
    is_index_switch = property(lambda a: a.type =='INDEX')      # 编号切换单独判断
    @staticmethod
    def IsSocketDefinitely(ess):
        base = ess.bl_rna
        while base:
            dnf = base.identifier
            base = base.base
        if dnf=='NodeSocket':
            return True
        if dnf=='Node':
            return False
        return None
    @staticmethod
    def IsSimRepCorrectSk(node, skTar: NodeSocket):
        node_has_items = {'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT', 
                          'MENU_SWITCH', 'BAKE', 'CAPTURE_ATTRIBUTE', 'INDEX_SWITCH'}       # 'INDEX_SWITCH' 在这里还没用到
        if (skTar.bl_idname=='NodeSocketVirtual')and(node.type in node_has_items):
            return False
        match node.type:            # 小王-让一些接口不被判定
            case 'SIMULATION_INPUT':
                return skTar!=node.outputs[0]
            case 'SIMULATION_OUTPUT'|'REPEAT_INPUT':
                return skTar!=node.inputs[0]
            case 'MENU_SWITCH':
                return skTar not in {node.inputs[0], node.outputs[0]}
            case 'CAPTURE_ATTRIBUTE':
                return hasattr(node, "capture_items") and skTar not in {node.inputs[0], node.outputs[0]}
            case _:
                return True # raise Exception("IsSimRepCorrectSk() 调用时未针对 SimRep")
    def IsContainsSkf(self, skfTar):
        for skf in self.skfa: # 没有这个 API (或者至少我没找到)，所以不得不“实际”检查匹配。
            if skf==skfTar:
                return True
        return False
    def GetSkfFromSk(self, skTar):
        if skTar.node!=self.node:
            raise Exception(f"Equestrian node is not equal `{skTar.path_from_id()}`")
        match self.type:
            case 'SIM'|'REP':
                match self.type: # 检查套接字是否是 SimRep 的“内置”套接字。
                    case 'SIM':
                        if self.node.type=='SIMULATION_INPUT':
                            if skTar==self.node.outputs[0]:
                                raise Exception("Socket \"Delta Time\" does not have interface.")
                        else:
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Skip\" does not have interface.")
                    case 'REP':
                        if self.node.type=='REPEAT_INPUT':
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Iterations\" does not have interface.")
                for skf in self.skfa:
                    if skf.name==skTar.name:
                        return skf
                raise Exception(f"Interface not found from `{skTar.path_from_id()}`")  # 如果套接字在节点上直接重命名，而不是通过接口。
            case 'CLASSIC'|'GROUP':
                for skf in self.skfa:
                    if (skf.item_type=='SOCKET')and(skf.identifier==skTar.identifier):
                        return skf
            # 小王-更改接口名称
            case 'MENU' | 'BAKE' | 'CAPTURE' | 'FOREACH_OUT':
                for skf in self.skfa:
                    if skf.name==skTar.name:
                        return skf

    def GetSkFromSkf(self, skfTar, *, isOut):
        if not self.IsContainsSkf(skfTar):
            raise Exception(f"Equestrian items does not contain `{skfTar}`")
        match self.type:
            # 小王-插入接口会用到
            case 'SIM' | 'REP' | 'CAPTURE' | 'BAKE':
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.name==skfTar.name:
                        return sk
            case 'MENU' | 'INDEX':
                # for sk in (self.node.outputs if isOut else self.node.inputs):
                for sk in self.node.inputs:
                    if sk.name==skfTar.name:
                        return sk
                raise Exception(f"Not found socket for `{skfTar}`")
            case 'CLASSIC'|'GROUP':
                if skfTar.item_type=='PANEL':
                    raise Exception(f"`Panel cannot be used for search: {skfTar}`")
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.identifier==skfTar.identifier:
                        return sk
                raise Exception(f"`Socket for node side not found: {skfTar}`")

    def NewSkfFromSk(self, skTar, isFlipSide=False):
        newName = sk_label_or_name(skTar)
        match self.type:
            case 'SIM':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION', 'MATRIX','STRING','RGBA','GEOMETRY'}: # TODO1v6 最好是能反向找到它们在哪里，而不是硬编码。
                    raise Exception(f"Socket type is not supported by Simulation: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            # case 'REP':
            case 'REP' | 'BAKE' | 'CAPTURE':       # 小王-插入接口
                # ('FLOAT', 'INT', 'BOOLEAN', 'VECTOR', 'ROTATION', 'MATRIX', 'STRING', 'MENU', 
                #  'RGBA', 'OBJECT', 'IMAGE', 'GEOMETRY', 'COLLECTION','TEXTURE', 'MATERIAL')
                # 'BAKE' 没必要判断
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION', 'MATRIX','STRING','RGBA','GEOMETRY',
                                      'OBJECT','IMAGE','COLLECTION','MATERIAL'}:
                    raise Exception(f"Socket type is not supported by Repeating: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            case 'MENU' :
                return self.skfa.new(newName)
            case 'INDEX' :
                input_soc = index_switch_add_input(self.tree.nodes, index_switch_node=self.node)
                return input_soc
            case 'CLASSIC'|'GROUP':
                skfNew = self.skfa.data.new_socket(newName, socket_type=sk_type_to_idname(skTar), in_out='OUTPUT' if (skTar.is_output^isFlipSide) else 'INPUT')
                skfNew.hide_value = skTar.hide_value
                if hasattr(skfNew,'default_value'):
                    skfNew.default_value = skTar.default_value
                    if hasattr(skfNew,'min_value'):
                        nd = skTar.node
                        if (nd.type in {'GROUP_INPUT', 'GROUP_OUTPUT'})or( (nd.type=='GROUP')and(nd.node_tree) ): # 如果套接字来自另一个节点组，则完全复制。
                            skf = Node_Items_Manager(nd).GetSkfFromSk(skTar)
                            for pr in skfNew.rna_type.properties:
                                if not(pr.is_readonly or pr.is_registered):
                                    setattr(skfNew, pr.identifier, getattr(skf, pr.identifier))
                    # tovo2v6 用于 `skfNew.subtype =` 的套接字 blid 替换映射。
                    # TODO0 需要想办法在创建之前嵌入，以便所有组的套接字立即拥有 sfk 默认值。Blender 自己是怎么做到的？
                    def FixInTree(tree):
                        for nd in tree.nodes:
                            if (nd.type=='GROUP')and(nd.node_tree==self.tree):
                                for sk in nd.inputs:
                                    if sk.identifier==skfNew.identifier:
                                        sk.default_value = skTar.default_value
                    for ng in bpy.data.node_groups:
                        if is_builtin_tree_idname(ng.bl_idname):
                            FixInTree(ng)
                    for att in ('materials','scenes','worlds','textures','lights','linestyles'): # 是这些，还是我忘了某个？
                        for dt in getattr(bpy.data, att):
                            if dt.node_tree: # 对于 materials -- https://github.com/ugorek000/VoronoiLinker/issues/19; 我仍然不明白它怎么可能是 None。
                                FixInTree(dt.node_tree)
                return skfNew
    
    def MoveBySkfs(self, skfFrom, skfTo, *, isSwap=False): # 本可以自行处理“BySks”的复杂性，但这已经是调用方的责任了。
        match self.type:
            case 'SIM' | 'REP' | 'MENU' | 'BAKE' | 'CAPTURE':       # 小王-支持交换接口
                inxFrom = -1
                inxTo = -1
                # 参见 GetSkFromSkf() 中对 skf 存在的检查。
                for cyc, skf in enumerate(self.skfa):
                    if skf==skfFrom:
                        inxFrom = cyc
                    if skf==skfTo:
                        inxTo = cyc
                if inxFrom==-1:
                    raise Exception(f"Index not found from `{skfFrom}`")
                if inxTo==-1:
                    raise Exception(f"Index not found from `{skfTo}`")
                self.skfa.move(inxFrom, inxTo)
                if isSwap:
                    self.skfa.move(inxTo+(1-(inxTo>inxFrom)*2), inxFrom)
            case 'CLASSIC'|'GROUP':
                if not self.IsContainsSkf(skfFrom):
                    raise Exception(f"Equestrian tree is not equal for `{skfFrom}`")
                if not self.IsContainsSkf(skfTo):
                    raise Exception(f"Equestrian tree is not equal for `{skfTo}`")
                # 我不知道有什么方法可以“正常地”实现这一点，而无需重新连接面板。尽管我觉得这是唯一的方法。
                list_panels = [ [None, None, None, None, ()] ]
                skfa = self.skfa
                # 记住面板：
                scos = {False:0, True:0}
                for skf in skfa:
                    if skf.item_type=='PANEL':
                        list_panels[-1][4] = (scos[False], scos[True])
                        list_panels.append( [None, skf.name, skf.description, skf.default_closed, (0, 0)] )
                        scos = {False:0, True:0}
                    else:
                        scos[skf.in_out=='OUTPUT'] += 1
                list_panels[-1][4] = (scos[False], scos[True])
                # 删除面板：
                skft = skfa.data
                tgl = True
                while tgl:
                    tgl = False
                    for skf in skfa:
                        if skf.item_type=='PANEL':
                            skft.remove(skf)
                            tgl = True
                            break
                # 进行移动：
                inxFrom = skfFrom.index
                inxTo = skfTo.index
                isDir = inxTo>inxFrom
                skft.move(skfa[inxFrom], inxTo+isDir)
                if isSwap:
                    skft.move(skfa[inxTo+(1-isDir*2)], inxFrom+(not isDir))
                # 恢复面板：
                for li in list_panels[1:]:
                    li[0] = skft.new_panel(li[1], description=li[2], default_closed=li[3])
                scoSkf = 0
                scoPanel = length(list_panels)-1
                tgl = False
                for skf in reversed(skfa): # 从尾部开始，否则会多次遍历已移动到面板的项目。
                    if skf.item_type=='SOCKET':
                        if (skf.in_out=='OUTPUT')and(not tgl):
                            tgl = True
                            scoSkf = 0
                            scoPanel = length(list_panels)-1
                        if scoSkf==list_panels[scoPanel][4][tgl]:
                            scoPanel -= 1
                            while (scoPanel>0)and(not list_panels[scoPanel][4][tgl]): # 面板可能包含零个其侧的套接字。
                                scoPanel -= 1
                            scoSkf = 0
                        if scoPanel>0:
                            skft.move_to_parent(skf, list_panels[scoPanel][0], 0) # 因为 'reversed(skfa)'，位置问题得以解决，这里只需 '0'；令人惊叹的方便巧合。
                        scoSkf += 1
    
    def __init__(self, snkd): #"snkd" = 套接字或节点。
        isSk = hasattr(snkd,'link_limit') # self.IsSocketDefinitely(snkd)
        ndEq = snkd.node if isSk else snkd
        if ndEq.type not in self.set_equestrianNodeTypes:
            raise Exception(f"Equestrian not found from `{snkd.path_from_id()}`")
        self.tree = snkd.id_data
        self.node = ndEq
        ndEq = getattr(ndEq,'paired_output', ndEq)
        match ndEq.type:
            case 'GROUP_OUTPUT'|'GROUP_INPUT':
                self.type = 'CLASSIC'
                self.skfa = ndEq.id_data.interface.items_tree
            case 'SIMULATION_OUTPUT':
                self.type = 'SIM'
                self.skfa = ndEq.state_items
            case 'REPEAT_OUTPUT':
                self.type = 'REP'
                self.skfa = ndEq.repeat_items
            # 小王-更改接口名称
            case 'MENU_SWITCH':
                self.type = 'MENU'
                self.skfa = ndEq.enum_items
            case 'INDEX_SWITCH':
                self.type = 'INDEX'
                self.skfa = ndEq
            case 'BAKE':
                self.type = 'BAKE'
                self.skfa = ndEq.bake_items
            case 'CAPTURE_ATTRIBUTE':
                self.type = 'CAPTURE'
                self.skfa = ndEq.capture_items
                # if hasattr(ndEq, "capture_items"):
            # for each zone 的重命名有点麻烦,不过这个目前优先级低
            # case 'FOREACH_GEOMETRY_ELEMENT_INPUT':
            #     self.type = 'FOREACH_IN'
            #     self.skfa = ndEq.input_items
            case 'FOREACH_GEOMETRY_ELEMENT_OUTPUT':
                self.type = 'FOREACH_OUT'
                # self.skfa = ndEq.main_items
                self.skfa = ndEq.generation_items
            case 'GROUP':
                self.type = 'GROUP'
                if not ndEq.node_tree:
                    raise Exception(f"Tree for nodegroup `{ndEq.path_from_id()}` not found, from `{snkd.path_from_id()}`")
                self.skfa = ndEq.node_tree.interface.items_tree

class Fotago(): # Found Target Goal (找到的目标), "剩下的你们自己看着办".
    #def __getattr__(self, att): # 天才. 仅次于 '(*args): return Vector((args))'.
    #    return getattr(self.target, att) # 但要小心, 它的速度慢了大约5倍.
    def __init__(self, target: NodeSocket, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        #self.target = target
        self.tar = target
        #self.sk = target #Fotago.sk = property(lambda a:a.target)
        #self.nd = target #Fotago.nd = property(lambda a:a.target)
        self.blid: str = target.bl_idname  #Fotago.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        # 下面的仅用于插槽.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text # 用于支持其他语言的翻译. 每次绘制时都获取翻译太不方便了, 所以直接"焊接"上去.

class PieRootData:
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
    pieDisplaySocketColor = 0
    pieAlignment = 0
    uiScale = 1.0

class VmtData(PieRootData):
    sk0: NodeSocket = None
    sk1: NodeSocket = None
    sk2: NodeSocket = None  # 小王 
    skType = ""
    isHideOptions = False
    isPlaceImmediately = False

class VqmtData(PieRootData):
    list_speedPieDisplayItems = []
    sk0: NodeSocket = None
    sk1: NodeSocket = None
    depth = 0
    qmSkType = ''
    qmTrueSkType = ''
    isHideOptions = False
    isPlaceImmediately = False
    isJustPie = False # 无需。
    canProcHideSks = True
    dict_lastOperation = {}
    isFirstDone = False # https://github.com/ugorek000/VoronoiLinker/issues/20
    dict_existingValues = {}
    test_bool = False

class VestData:
    list_enumProps = [] # 用于焊接，并在调用前检查是否存在。
    domain_item_list = []
    nd = None
    boxScale = 1.0 # 如果忘记设置，至少盒子不会坍缩为零。
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False

class VptData:
    reprSkAnchor = ""

class TryAndPass():
    def __enter__(self):
        pass
    def __exit__(self, *_):
        return True


class VlnstData:
    lastLastExecError = "" # 用于用户编辑 vlnstLastExecError, 不能添加或修改, 但可以删除.
    isUpdateWorking = False

def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnstLastExecError = ""
    elif self.vlnstLastExecError:
        if self.vlnstLastExecError!=VlnstData.lastLastExecError: # 注意: 谨防堆栈溢出.
            self.vlnstLastExecError = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False




