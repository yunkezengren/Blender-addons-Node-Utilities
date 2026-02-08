from ..C_Structure import BNodeSocket
from ..globals import is_bl4_plus, set_classicSocketsBlid, set_utilTypeSkFields, set_utilEquestrianPortalBlids, dict_vqmtDefaultDefault, dict_vqmtDefaultValueOperation, dict_vqmtEditorNodes
from ..common_forward_class import Node_Items_Manager, Fotago, VqmtData
from bpy.types import (NodeTree, Node, NodeSocket)
import bpy
from mathutils import Vector as Vec2
from ..common_forward_func import sk_label_or_name, add_item_for_index_switch, is_builtin_tree_idname, sk_type_to_idname
from bpy.app.translations import pgettext_iface as _iface

def sk_loc(sk: NodeSocket):
    return Vec2(BNodeSocket.GetFields(sk).runtime.contents.location[:]) if (sk.enabled) and (not sk.hide) else Vec2((0, 0))

def node_abs_loc(nd: Node) -> Vec2:
    return nd.location + node_abs_loc(nd.parent) if nd.parent else nd.location

# 提供对折叠节点的支持:
# 终于等到了... 当然, 这不是"真正的支持". 我鄙视折叠起来的节点; 我也不想去处理圆角和随之改变的绘制逻辑.
# 所以, 在官方提供获取插槽位置的API之前, 这就是最好的办法了. 我们翘首以盼. 🙏
dict_collapsedNodes = {}

def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide

# 我没有只展开最近的节点, 而是做了一个"痕迹".
# 为了不让这一切变成混乱的, 不断"抽搐"的场面, 而是可以引导, 展开, 冷静下来, 看到"当前情况", 分析, 然后 спокойно 地连接需要的东西.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, None): # 工具在过程中可能会创建节点; 例如 vptRvEeIsSavePreviewResults.
            nd.hide = dict_collapsedNodes[nd]


def GenFtgFromNd(nd: Node, pos: Vec2, uiScale: float): # 从 GetNearestNodesFtg 中提取出来, 本来没必要, 但 VLTT 逼我这么做.
    def DistanceField(field0: Vec2, boxbou: Vec2): # 感谢 RayMarching, 没有它我不会想到这个.
        field1 = Vec2(( (field0.x>0)*2-1, (field0.y>0)*2-1 ))
        field0 = Vec2(( abs(field0.x), abs(field0.y) ))-boxbou/2
        field2 = Vec2(( max(field0.x, 0.0), max(field0.y, 0.0) ))
        field3 = Vec2(( abs(field0.x), abs(field0.y) ))
        field3 = field3*Vec2((field3.x<=field3.y, field3.x>field3.y))
        field3 = field3*-( (field2.x+field2.y)==0.0 )
        return (field2+field3)*field1
    isReroute = nd.type=='REROUTE'
    # 重路由节点的技术尺寸被明确地重写为其实际大小的1/4.
    # 据我所知, 重路由节点与其他节点不同, 它的大小不会随着 uiScale 的改变而改变. 所以它不需要除以 'uiScale'.
    ndSize = Vec2((4, 4)) if isReroute else nd.dimensions/uiScale
    # 对于节点, 位置在节点中心. 对于重路由节点, 位置已经在其视觉中心.
    ndCenter = node_abs_loc(nd).copy() if isReroute else node_abs_loc(nd)+ndSize/2*Vec2((1.0, -1.0))
    if nd.hide: # 对于 VHT, 一个利用现有能力的 "快速补丁".
        ndCenter.y += ndSize.y/2-10 # 需要小心这个写入操作(write), 因为如果上一个节点是重路由节点, 它可能是一个直接的指针, (https://github.com/ugorek000/VoronoiLinker/issues/16).
    # 构建距离场
    vec = DistanceField(pos-ndCenter, ndSize)
    # 将处理过的节点添加到列表中
    return Fotago(nd, dist=vec.length, pos=pos-vec)

def GetNearestNodesFtg(nodes, samplePos, uiScale, includePoorNodes=True): # 返回最近的节点列表. 真实的距离场.
    # 几乎是真实的. 圆角没有计算. 它们的缺失不影响使用, 而计算需要更多的操作. 所以没必要炫技.
    # 另一方面, 圆角对于折叠的节点很重要, 但我鄙视它们, 所以...
    # 框架节点被跳过, 因为没有一个工具需要它们.没有插槽的节点--就像框架节点一样;可以在搜索阶段就忽略它们.
    
    valid_ftgs: list[Fotago] = []
    for nd in nodes:
        if nd.type == 'FRAME':
            continue
        if not includePoorNodes and not nd.inputs and not nd.outputs:
            continue

        ftg_object = GenFtgFromNd(nd, samplePos, uiScale)
        valid_ftgs.append(ftg_object)

    return sorted(valid_ftgs, key=lambda ftg: ftg.dist)
    
    # return sorted([GenFtgFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.dist)

# 我本想添加一个自制的加速结构, 但后来突然意识到, 还需要"第二近"的信息. 所以看来不完整处理是不行的.
# 如果你知道如何加速这个过程同时保留信息, 请与我分享.
# 另一方面, 自插件诞生以来, 从未遇到过性能问题, 所以... 只是为了美观.
# 而且还需要考虑折叠的节点, 愿它们见鬼去吧, 它们可能在过程中展开, 破坏了缓存的所有美好.

def GenFtgsFromPuts(nd: Node, isSide, samplePos, uiScale): # 为 vptRvEeSksHighlighting 提取出来.
    # 注意: 这个函数应该自己从标记中获取方向, 因为 `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk: NodeSocket):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    results: list[Fotago] = []
    ndDim = Vec2(nd.dimensions/uiScale) # "nd.dimensions" 已经包含了界面缩放的校正, 所以把它返回到世界坐标系.
    for sk in nd.outputs if isSide else reversed(nd.inputs):
        # 忽略禁用和隐藏的
        if (sk.enabled)and(not sk.hide):
            pos = sk_loc(sk)/uiScale # 该死, 这太棒了. 告别了过去版本的自制垃圾.
            # 但插槽也没有布局高度的API, 所以只能点对点地打补丁; 直到想出其他办法.
            hei = 0
            if (not isSide)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if "VectorDirection" in str(sk.rna_type):
                    hei = 2
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not is_bl4_plus) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3
            boxHeiBound = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = _iface(sk_label_or_name(sk)) if sk.bl_idname!='NodeSocketVirtual' else _iface("Virtual" if not sk.name else sk_label_or_name(sk))
            results.append(Fotago(sk, dist=(samplePos-pos).length, pos=pos, dir= 1 if sk.is_output else -1 , boxHeiBound=boxHeiBound, text=txt))
    return results

def GetNearestSocketsFtg(nd: Node, samplePos, uiScale): # 返回"最近的插槽"列表. 真实的 Voronoi 图单元距离场. 没错, 这个插件就是因此得名的.
    if nd.type == 'REROUTE':
        def ftg_route(sk: NodeSocket):
            loc = node_abs_loc(nd)
            # 这样的话 鼠标位置在转接点左是输入,在转接点有是输出
            distance = (samplePos - loc - Vec2((sk.is_output, 0))).length
            direction = 1 if sk.is_output else -1
            label = nd.label or _iface(sk.name)
            return [Fotago(sk, dist=distance, pos=loc, dir=direction, boxHeiBound=(-1, -1), text=label)]
        return ftg_route(nd.inputs[0]), ftg_route(nd.outputs[0])
        # ftg_route = lambda sk: Fotago(sk, dist=(samplePos - loc - Vec2((sk.is_output, 0))).length, pos=loc, dir=1 if sk.is_output else -1, boxHeiBound=(-1, -1), text=nd.label if nd.label else _iface(sk.name))
        # return [ftg_route(nd.inputs[0])], [ftg_route(nd.outputs[0])]

    ftg_sks_in = GenFtgsFromPuts(nd, False, samplePos, uiScale)
    ftg_sks_out = GenFtgsFromPuts(nd, True, samplePos, uiScale)
    ftg_sks_in.sort(key=lambda a: a.dist)
    ftg_sks_out.sort(key=lambda a: a.dist)
    return ftg_sks_in, ftg_sks_out

def GetListOfNdEnums(node: Node):   # 小王-判断节点是否有下拉列表
    enum_l = []
    for p in node.rna_type.properties:
        if (p.type == 'ENUM') and (p.name != "Warning Propagation") and (not (p.is_readonly or p.is_registered)):
            enum_l.append(p)
    return enum_l

# 小王-显示节点选项优化-根据选项重命名节点-domain
def node_domain_item_list(node: Node):
    enum_list = []
    for p in node.rna_type.properties:
        if p.type == 'ENUM' and p.identifier == "domain":
            enum_list = [item for item in p.enum_items]
            # enum_list = [item.identifier for item in p.enum_items]
            # enum_list = [[item.name, item.identifier] for item in p.enum_items]
    return enum_list

def node_visible_menu_inputs(node: Node) -> list[NodeSocket]:
    return [socket for socket in node.inputs if (socket.type == 'MENU' and socket.is_icon_visible)]

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""

def opt_ftg_socket(ftg: Fotago) -> NodeSocket:
    return ftg.tar if ftg else None

def IsClassicSk(sk: NodeSocket):
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return sk_type_to_idname(sk) in set_classicSocketsBlid

def CompareSkLabelName(sk1, sk2, ignore_upper_lower=False):
    if ignore_upper_lower:
        return sk_label_or_name(sk1).upper()==sk_label_or_name(sk2).upper()
    else:
        return sk_label_or_name(sk1)==sk_label_or_name(sk2)

def SelectAndActiveNdOnly(ndTar: Node):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar
    ndTar.select = True

def MinFromFtgs(ftg1, ftg2):
    # print(type(ftg1))   # <class Fotago>
    if (ftg1)or(ftg2): # 如果至少有一个存在.
        if not ftg2: # 如果其中一个不存在,
            return ftg1
        elif not ftg1: # 那么另一个就是唯一的选择.
            return ftg2
        else: # 否则选择最近的那个.
            return ftg1 if ftg1.dist<ftg2.dist else ftg2
    return None

def FindAnySk(nd: Node, list_ftgSksIn, list_ftgSksOut): # Todo0NA: 需要泛化!, 用 lambda. 并且外部循环遍历列表, 而不是两个循环.
    ftgSkOut, ftgSkIn = None, None
    for ftg in list_ftgSksOut:
        if (ftg.blid!='NodeSocketVirtual')and(Node_Items_Manager.IsSimRepCorrectSk(nd, ftg.tar)): # todo1v6: 这个函数到处都和 !=NodeSocketVirtual 一起使用, 需要重做拓扑.
            ftgSkOut = ftg
            break
    for ftg in list_ftgSksIn:
        if (ftg.blid!='NodeSocketVirtual')and(Node_Items_Manager.IsSimRepCorrectSk(nd, ftg.tar)):
            ftgSkIn = ftg
            break
    return MinFromFtgs(ftgSkOut, ftgSkIn)

# 注意: DoLinkHh 现在有太多其他依赖项, 想要把它单独抽离出来会更困难.
# P.s. "HH" -- 意思是 "High Level", 但我打错字母了 D:

def DoLinkHh(sko: NodeSocket, ski: NodeSocket, *, isReroutesToAnyType=True, isCanBetweenField=True, isCanFieldToShader=True):
    # 多么意外的视觉巧合, 与 "sk0" 和 "sk1" 的序列号.
    # 既然我们现在是高级别的, 就得处理特殊情况:
    if not(sko and ski): # 它们必须存在.
        raise Exception("One of the sockets is none")
    if sko.id_data!=ski.id_data: # 它们必须在同一个世界里.
        raise Exception("Socket trees vary")
    if not(sko.is_output^ski.is_output): # 它们必须是不同的性别.
        raise Exception("Sockets `is_output` is same")
    if not sko.is_output: # 输出必须是第一个.
        sko, ski = ski, sko
    # 注意: "高级别", 但不是为傻瓜用户准备的; 天哪, 可以在虚拟之间连接.
    tree: NodeTree = sko.id_data
    # 下面好复杂的逻辑啊,暂时这样看看会不会出问题
    tree.links.new(sko, ski, handle_dynamic_sockets=True)
    return
    if tree.bl_idname=='NodeTreeUndefined': # 树不应该是丢失的.
        return # 在丢失的树中, 链接可以手动创建, 但通过 API不行; 所以退出.
    if sko.node==ski.node: # 对于同一个节点, 显然是无意义的, 尽管可能. 对接口更重要.
        return
    isSkoField = sko.type in set_utilTypeSkFields
    isSkoNdReroute = sko.node.type=='REROUTE'
    isSkiNdReroute = ski.node.type=='REROUTE'
    isSkoVirtual = (sko.bl_idname=='NodeSocketVirtual')and(not isSkoNdReroute) # 虚拟只对接口有效, 需要排除"冒名顶替的 reroute".
    isSkiVirtual = (ski.bl_idname=='NodeSocketVirtual')and(not isSkiNdReroute) # 注意: 虚拟和插件套接字的 sk.type=='CUSTOM'.
    # 如果可以
    if not( (isReroutesToAnyType)and( (isSkoNdReroute)or(isSkiNdReroute) ) ): # 至少一个是 reroute.
        if not( (sko.bl_idname==ski.bl_idname)or( (isCanBetweenField)and(isSkoField)and(ski.type in set_utilTypeSkFields) ) ): # blid 相同或在字段之间.
            if not( (isCanFieldToShader)and(isSkoField)and(ski.type=='SHADER') ): # 字段到 shader.
                if not(isSkoVirtual or isSkiVirtual): # 它们中有一个是虚拟的 (用于接口).
                    if (not is_builtin_tree_idname(tree.bl_idname))or( IsClassicSk(sko)==IsClassicSk(ski) ): # 经典树中的插件套接字; 参见 VLT.
                        return None # 当前类型之间不允许.
    # 不正确的筛选完成. 现在是接口:
    ndo = sko.node
    ndi = ski.node
    isProcSkfs = True
    # 与接口的交互只需要一个虚拟的. 如果没有, 就是普通连接.
    # 但如果它们都是虚拟的, 就无法读取信息; 因此与接口的交互无用.
    if not(isSkoVirtual^isSkiVirtual): # 两个条件打包成一个 xor.
        isProcSkfs = False
    elif ndo.type==ndi.type=='REROUTE': # reroute 之间保证连接. 这是一个小小的安全岛, 风暴前的宁静.
        isProcSkfs = False
    elif not( (ndo.bl_idname in set_utilEquestrianPortalBlids)or(ndi.bl_idname in set_utilEquestrianPortalBlids) ): # 至少一个节点应该是骑士.
        isProcSkfs = False

    if isProcSkfs: # 嗯, 风暴原来没那么大. 我预想了更多的意大利面条代码. 如果动动脑筋, 一切都变得如此简单明了.
        # 获取虚拟套接字的骑士节点
        ndEq = ndo if isSkoVirtual else ndi # 基于输出骑士与其同伴等概率的假设.
        # 折叠同伴
        ndEq = getattr(ndEq,'paired_output', ndEq)
        # 有趣的是, 在某个平行宇宙中是否存在虚拟的多输入?.
        skTar = sko if isSkiVirtual else ski
        match ndEq.bl_idname:
            case 'NodeGroupInput':  typeEq = 0
            case 'NodeGroupOutput': typeEq = 1
            case 'GeometryNodeSimulationOutput': typeEq = 2
            case 'GeometryNodeRepeatOutput':     typeEq = 3
            # 新建接口
            case 'GeometryNodeMenuSwitch':       typeEq = 4
            case 'GeometryNodeBake':             typeEq = 5
            case 'GeometryNodeCaptureAttribute': typeEq = 6
            case 'GeometryNodeIndexSwitch':      typeEq = 7
        # 不处理骑士不支持的类型:
        can = True
        match typeEq:
            case 2:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','GEOMETRY'}
            case 3:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL'}
            case 4:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL','TEXTURE'}
            case 5:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','MATRIX','STRING','RGBA','GEOMETRY'}
            case 6:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','MATRIX','STRING','RGBA'}
            case 7:
                can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL','TEXTURE','MENU'}
        if not can:
            return None
        # 创建接口
        match typeEq:
            case 0|1:
                equr = Node_Items_Manager(ski if isSkiVirtual else sko)
                skf = equr.NewSkfFromSk(skTar)
                skNew = equr.GetSkFromSkf(skf, isOut=skf.in_out!='OUTPUT') # * 痛苦的声音 *
            case 2|3:       # [-2]  -1是扩展接口,-2是新添加的接口
                _skf = (ndEq.state_items if typeEq==2 else ndEq.repeat_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), sk_label_or_name(skTar))
                if True: # SimRep 的重新选择是微不足道的; 因为它们没有面板, 所有新套接字都出现在底部.
                    skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
                else:
                    skNew = Node_Items_Manager(ski if isSkiVirtual else sko).GetSkFromSkf(_skf, isOut=isSkoVirtual)
            case 4:       # 新建接口-菜单切换
                _skf = ndEq.enum_items.new(sk_label_or_name(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 5|6:       # 新建接口-捕捉属性 烘焙
                _skf = (ndEq.bake_items if typeEq==5 else ndEq.capture_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), sk_label_or_name(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 7:         # 新建接口-编号切换
                skNew = add_item_for_index_switch(ski.node)

        # 重新选择新出现的套接字
        if isSkiVirtual:
            ski = skNew
        else:
            sko = skNew
    # 旅程成功完成. 终于到了最重要的一步:
    def DoLinkLL(tree, sko, ski):
        return tree.links.new(sko, ski) #hi.
    return DoLinkLL(tree, sko, ski)
    # 注意: 从 b3.5 版本开始, 虚拟输入现在可以直接像多输入一样接收.
    # 它们甚至可以相互多次连接, 太棒了. 开发者可以说"放手了", 让它自由发展.

def VlrtRememberLastSockets(sko: NodeSocket, ski: NodeSocket):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        # ski 对 VLRT 来说, 如果没有 sko 就没用
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)

def remember_add_link(sko: NodeSocket, ski: NodeSocket):
    DoLinkHh(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)

def DoQuickMath(event, tree: NodeTree, operation, isCombo=False):
    txt = dict_vqmtEditorNodes[VqmtData.qmSkType].get(tree.bl_idname, "")
    if not txt: #如果不在列表中，则表示此节点在该类型的编辑器中不存在（根据列表的设计）=> 没有什么可以"混合"的，所以退出。
        return {'CANCELLED'}
    #快速数学的核心，添加节点并创建连接：
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=not VqmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    preset = operation.split("|")
    isPreset = len(preset)>1
    if isPreset:
        operation = preset[0]
    if VqmtData.qmSkType!='RGBA': #哦，这个颜色。
        aNd.operation = operation
    else:
        if aNd.bl_idname=='ShaderNodeMix':
            aNd.data_type = 'RGBA'
            aNd.clamp_factor = False
        aNd.blend_type = operation
        aNd.inputs[0].default_value = 1.0
        aNd.inputs[0].hide = operation in {'ADD','SUBTRACT','DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION','VALUE','SATURATION','HUE','COLOR'}
    ##
    if not isPreset:
        #现在存在justPieCall，这意味着是时候隐藏第一个接口的值了（但这只对向量有必要）。
        # if VqmtData.qmSkType=='VECTOR':
        #     aNd.inputs[0].hide_value = True
        #使用event.shift的想法很棒。最初是为了单个连接到第二个接口，但由于下面的可视化搜索，它也可以交换两个连接。
        bl4ofs = 2 * is_bl4_plus        # byd 搞版本兼容真麻烦,删掉
        #"Inx"，因为它是对整数"index"的模仿，但后来我意识到可以直接使用socket进行后续连接。
        skInx = aNd.inputs[0] if VqmtData.qmSkType != 'RGBA' else aNd.inputs[-2 - bl4ofs]
        if event.shift:
            for sk in aNd.inputs:
                if (sk!=skInx)and(sk.enabled):
                    if sk.type==skInx.type:
                        skInx = sk
                        break
        if VqmtData.sk0:
            remember_add_link(VqmtData.sk0, skInx)
            if VqmtData.sk1:
                #第二个是"可视化地"搜索的；这是为了'SCALE'（缩放）操作。
                for sk in aNd.inputs: #从上到下搜索。因为还有'MulAdd'（乘加）。
                    if (sk.enabled)and(not sk.is_linked): #注意："aNd"是新创建的；并且没有连接。因此使用is_linked。
                        #哦，这个缩放；唯一一个具有两种不同类型接口的。
                        if (sk.type==skInx.type)or(operation=='SCALE'): #寻找相同类型的。对 RGBA Mix 有效。
                            remember_add_link(VqmtData.sk1, sk)
                            break #只需要连接到找到的第一个，否则会连接到所有（例如在'MulAdd'中）。
            elif isCombo:
                for sk in aNd.inputs:
                    if (sk.type==skInx.type)and(not sk.is_linked):
                        remember_add_link(VqmtData.sk0, sk)
                        break
            if VqmtData.sk2:
                for sk in aNd.outputs:
                    if (sk.enabled)and(not sk.hide):
                        remember_add_link(sk, VqmtData.sk2)
                        break
    #为第二个接口设置默认值（大多数为零）。这是为了美观；而且这毕竟是数学运算。
    #注意：向量节点创建时已经为零，所以不需要再为它清零。
    tup_default = dict_vqmtDefaultDefault[VqmtData.qmSkType]
    if VqmtData.qmSkType!='RGBA':
        for cyc, sk in enumerate(aNd.inputs):
            #这里没有可见性和连接的检查，强制赋值。因为我就是这么想的。
            sk.default_value = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)[cyc]
    else: #为了节省dict_vqmtDefaultValueOperation中的空间而进行的优化。
        pass
        # 为颜色输入接口设置默认值, 有的有alpha有的没,麻烦不管了
        # tup_col = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)
        # aNd.inputs[-2-bl4ofs].default_value = tup_col[0]
        # aNd.inputs[-1-bl4ofs].default_value = tup_col[1]
    ##
    if isPreset:
        for zp in zip(aNd.inputs, preset[1:]):
            if zp[1]:
                if zp[1]=="x":
                    if VqmtData.sk0:
                        remember_add_link(VqmtData.sk0, zp[0])
                else:
                    zp[0].default_value = eval(f"{zp[1]}")
    #根据请求隐藏所有接口。面无表情地做，因为已连接的接口反正也隐藏不了；甚至不用检查'sk.enabled'。
    if VqmtData.canProcHideSks: #对于justPieCall没必要，而且可能会有意外点击，对于qqm则完全不符合其设计理念。
        if event.alt: #对于主要用途来说很方便，甚至可以不用松开Shift Alt。
            for sk in aNd.inputs:
                sk.hide = True
    aNd.show_options = not VqmtData.isHideOptions
    return {'FINISHED'}
