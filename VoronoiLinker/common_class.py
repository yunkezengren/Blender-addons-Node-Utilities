import bpy
from builtins import len as length
from bpy.types import (NodeSocket, UILayout)

dict_typeSkToBlid = {
        'SHADER':    'NodeSocketShader',
        'RGBA':      'NodeSocketColor',
        'VECTOR':    'NodeSocketVector',
        'VALUE':     'NodeSocketFloat',
        'STRING':    'NodeSocketString',
        'INT':       'NodeSocketInt',
        'BOOLEAN':   'NodeSocketBool',
        'ROTATION':  'NodeSocketRotation',
        'GEOMETRY':  'NodeSocketGeometry',
        'OBJECT':    'NodeSocketObject',
        'COLLECTION':'NodeSocketCollection',
        'MATERIAL':  'NodeSocketMaterial',
        'TEXTURE':   'NodeSocketTexture',
        'IMAGE':     'NodeSocketImage',
        'MATRIX':    'NodeSocketMatrix',
        'CUSTOM':    'NodeSocketVirtual',
        }

def GetSkLabelName(sk):
    return sk.label if sk.label else sk.name

def index_switch_add_input(nodes, index_switch_node):
    old_active = nodes.active
    nodes.active = index_switch_node
    bpy.ops.node.index_switch_item_add()
    nodes.active = old_active
    return index_switch_node.inputs[-2]

def IsClassicTreeBlid(blid):
    set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}
    return blid in set_quartetClassicTreeBlids

def SkConvertTypeToBlid(sk):
    return dict_typeSkToBlid.get(sk.type, "Vl_Unknow")

class Equestrian():
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
        node_interface = {'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT', 
                          'MENU_SWITCH', 'BAKE', 'CAPTURE_ATTRIBUTE', 'INDEX_SWITCH'}       # 'INDEX_SWITCH' 在这里还没用到
        if (skTar.bl_idname=='NodeSocketVirtual')and(node.type in node_interface):
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
                return True #raise Exception("IsSimRepCorrectSk() was called not for SimRep")
    def IsContainsSkf(self, skfTar):
        for skf in self.skfa: #На это нет api (или по крайней мере я не нашёл), поэтому пришлось проверять соответствие "по факту".
            if skf==skfTar:
                return True
        return False
    def GetSkfFromSk(self, skTar):
        if skTar.node!=self.node:
            raise Exception(f"Equestrian node is not equal `{skTar.path_from_id()}`")
        match self.type:
            case 'SIM'|'REP':
                match self.type: #Проверить, если сокет является "встроенным" для SimRep'а.
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
                raise Exception(f"Interface not found from `{skTar.path_from_id()}`") #Если сокет был как-то переименован у нода напрямую, а не через интерфейсы.
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
        newName = GetSkLabelName(skTar)
        match self.type:
            case 'SIM':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION', 'MATRIX','STRING','RGBA','GEOMETRY'}: #todo1v6 неплохо было бы отреветь где они находятся, а не хардкодить.
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
                skfNew = self.skfa.data.new_socket(newName, socket_type=SkConvertTypeToBlid(skTar), in_out='OUTPUT' if (skTar.is_output^isFlipSide) else 'INPUT')
                skfNew.hide_value = skTar.hide_value
                if hasattr(skfNew,'default_value'):
                    skfNew.default_value = skTar.default_value
                    if hasattr(skfNew,'min_value'):
                        nd = skTar.node
                        if (nd.type in {'GROUP_INPUT', 'GROUP_OUTPUT'})or( (nd.type=='GROUP')and(nd.node_tree) ): #Если сокет от другой группы нодов, то полная копия.
                            skf = Equestrian(nd).GetSkfFromSk(skTar)
                            for pr in skfNew.rna_type.properties:
                                if not(pr.is_readonly or pr.is_registered):
                                    setattr(skfNew, pr.identifier, getattr(skf, pr.identifier))
                    #tovo2v6 карта замен блида сокета для `skfNew.subtype =`.
                    #Todo0 нужно придумать как внедриться до создания, чтобы у всех групп появился сокет со значением сразу же от sfk default. Как это делает сам Blender?
                    def FixInTree(tree):
                        for nd in tree.nodes:
                            if (nd.type=='GROUP')and(nd.node_tree==self.tree):
                                for sk in nd.inputs:
                                    if sk.identifier==skfNew.identifier:
                                        sk.default_value = skTar.default_value
                    for ng in bpy.data.node_groups:
                        if IsClassicTreeBlid(ng.bl_idname):
                            FixInTree(ng)
                    for att in ('materials','scenes','worlds','textures','lights','linestyles'): #Это все или я кого-то забыл?
                        for dt in getattr(bpy.data, att):
                            if dt.node_tree: #Для materials -- https://github.com/ugorek000/VoronoiLinker/issues/19; Я так и не понял, каким образом оно может быть None.
                                FixInTree(dt.node_tree)
                return skfNew
    def MoveBySkfs(self, skfFrom, skfTo, *, isSwap=False): #Можно было бы и взять на себя запары с "BySks", но это уже забота вызывающей стороны.
        match self.type:
            case 'SIM' | 'REP' | 'MENU' | 'BAKE' | 'CAPTURE':       # 小王-支持交换接口
                inxFrom = -1
                inxTo = -1
                #См. проверку наличия skf в GetSkFromSkf().
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
                #Я не знаю способа, как по-нормальному(?) это реализовать честным образом без пересоединения от/к панелям. Хотя что-то мне подсказывает, что это единственный способ.
                list_panels = [ [None, None, None, None, ()] ]
                skfa = self.skfa
                #Запомнить панели:
                scos = {False:0, True:0}
                for skf in skfa:
                    if skf.item_type=='PANEL':
                        list_panels[-1][4] = (scos[False], scos[True])
                        list_panels.append( [None, skf.name, skf.description, skf.default_closed, (0, 0)] )
                        scos = {False:0, True:0}
                    else:
                        scos[skf.in_out=='OUTPUT'] += 1
                list_panels[-1][4] = (scos[False], scos[True])
                #Удалить панели:
                skft = skfa.data
                tgl = True
                while tgl:
                    tgl = False
                    for skf in skfa:
                        if skf.item_type=='PANEL':
                            skft.remove(skf)
                            tgl = True
                            break
                #Сделать перемещение:
                inxFrom = skfFrom.index
                inxTo = skfTo.index
                isDir = inxTo>inxFrom
                skft.move(skfa[inxFrom], inxTo+isDir)
                if isSwap:
                    skft.move(skfa[inxTo+(1-isDir*2)], inxFrom+(not isDir))
                #Восстановить панели:
                for li in list_panels[1:]:
                    li[0] = skft.new_panel(li[1], description=li[2], default_closed=li[3])
                scoSkf = 0
                scoPanel = length(list_panels)-1
                tgl = False
                for skf in reversed(skfa): #С конца, иначе по перемещённым в панели будет проходиться больше одного раза.
                    if skf.item_type=='SOCKET':
                        if (skf.in_out=='OUTPUT')and(not tgl):
                            tgl = True
                            scoSkf = 0
                            scoPanel = length(list_panels)-1
                        if scoSkf==list_panels[scoPanel][4][tgl]:
                            scoPanel -= 1
                            while (scoPanel>0)and(not list_panels[scoPanel][4][tgl]): #Панель может содержать ноль сокетов своей стороны.
                                scoPanel -= 1
                            scoSkf = 0
                        if scoPanel>0:
                            skft.move_to_parent(skf, list_panels[scoPanel][0], 0) #Из-за 'reversed(skfa)' отпала головная боль с позицией, и тут просто '0'; потрясающе удобное совпадение.
                        scoSkf += 1
    def __init__(self, snkd): #"snkd" = sk или nd.
        isSk = hasattr(snkd,'link_limit') #self.IsSocketDefinitely(snkd)
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
    sk0 = None
    sk1 = None
    depth = 0
    qmSkType = ''
    qmTrueSkType = ''
    isHideOptions = False
    isPlaceImmediately = False
    isJustPie = False #Без нужды.
    canProcHideSks = True
    dict_lastOperation = {}
    isFirstDone = False #https://github.com/ugorek000/VoronoiLinker/issues/20
    dict_existingValues = {}
    test_bool = False



class VestData:
    list_enumProps = [] #Для пайки, и проверка перед вызовом, есть ли вообще что.
    domain_item_list = []
    nd = None
    boxScale = 1.0 #Если забыть установить, то хотя бы коробка не сколлапсируется в ноль.
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False