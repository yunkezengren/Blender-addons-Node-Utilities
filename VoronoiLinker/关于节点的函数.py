from .C_Structure import BNode, BNodeSocket
from .common_class import Equestrian
from bpy.types import (Node, NodeSocket, UILayout)

from mathutils import Vector as Vec
Vec2 = Color4 = Vec

def sk_loc(sk):
    return Vec2(BNodeSocket.GetFields(sk).runtime.contents.location[:]) if (sk.enabled) and (not sk.hide) else Vec2((0, 0))

def node_abs_loc(nd):
    return nd.location+node_abs_loc(nd.parent) if nd.parent else nd.location



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

class Fotago(): # Found Target Goal (找到的目标), "剩下的你们自己看着办".
    #def __getattr__(self, att): # 天才. 仅次于 '(*args): return Vector((args))'.
    #    return getattr(self.target, att) # 但要小心, 它的速度慢了大约5倍.
    def __init__(self, target, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        #self.target = target
        self.tar = target
        #self.sk = target #Fotago.sk = property(lambda a:a.target)
        #self.nd = target #Fotago.nd = property(lambda a:a.target)
        self.blid = target.bl_idname #Fotago.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        # 下面的仅用于插槽.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text # 用于支持其他语言的翻译. 每次绘制时都获取翻译太不方便了, 所以直接"焊接"上去.

def GenFtgFromNd(nd, pos, uiScale): # 从 GetNearestNodesFtg 中提取出来, 本来没必要, 但 VLTT 逼我这么做.
    def DistanceField(field0, boxbou): # 感谢 RayMarching, 没有它我不会想到这个.
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
    return sorted([GenFtgFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.dist)

# 我本想添加一个自制的加速结构, 但后来突然意识到, 还需要"第二近"的信息. 所以看来不完整处理是不行的.
# 如果你知道如何加速这个过程同时保留信息, 请与我分享.
# 另一方面, 自插件诞生以来, 从未遇到过性能问题, 所以... 只是为了美观.
# 而且还需要考虑折叠的节点, 愿它们见鬼去吧, 它们可能在过程中展开, 破坏了缓存的所有美好.

def GenFtgsFromPuts(nd, isSide, samplePos, uiScale): # 为 vptRvEeSksHighlighting 提取出来.
    # 注意: 这个函数应该自己从标记中获取方向, 因为 `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    list_result = []
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
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not gt_blender4) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3
            boxHeiBound = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = TranslateIface(GetSkLabelName(sk)) if sk.bl_idname!='NodeSocketVirtual' else TranslateIface("Virtual" if not sk.name else GetSkLabelName(sk))
            list_result.append(Fotago(sk, dist=(samplePos-pos).length, pos=pos, dir= 1 if sk.is_output else -1 , boxHeiBound=boxHeiBound, text=txt))
    return list_result

def GetNearestSocketsFtg(nd, samplePos, uiScale): # 返回"最近的插槽"列表. 真实的 Voronoi 图单元距离场. 没错, 这个插件就是因此得名的.
    # 如果是重路由节点, 那么情况很简单, 不需要计算; 输入和输出都只有一个, 插槽的位置就是它本身.
    if nd.type=='REROUTE':
        loc = node_abs_loc(nd)
        L = lambda a: Fotago(a, dist=(samplePos-loc).length, pos=loc, dir=1 if a.is_output else -1, boxHeiBound=(-1, -1), text=nd.label if nd.label else TranslateIface(a.name))
        return [L(nd.inputs[0])], [L(nd.outputs[0])]
    list_ftgSksIn = GenFtgsFromPuts(nd, False, samplePos, uiScale)
    list_ftgSksOut = GenFtgsFromPuts(nd, True, samplePos, uiScale)
    list_ftgSksIn.sort(key=lambda a:a.dist)
    list_ftgSksOut.sort(key=lambda a:a.dist)
    return list_ftgSksIn, list_ftgSksOut

def GetListOfNdEnums(node):   # 小王-判断节点是否有下拉列表
    enum_l = []
    for p in node.rna_type.properties:
        if (p.type == 'ENUM') and (p.name != "Warning Propagation") and (not (p.is_readonly or p.is_registered)):
            enum_l.append(p)
    return enum_l

# 小王-显示节点选项优化-根据选项重命名节点-domain
# def get_node_enum_item_list_dict(node):
#     enum_dict = {}
#     for p in node.rna_type.properties:
#         if (p.type == 'ENUM') and (p.name != "Warning Propagation") and (not (p.is_readonly or p.is_registered)):
#             enum_dict[p.identifier] = [item.name for item in p.enum_items]
#     return enum_dict

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""



# 注意: DoLinkHh 现在有太多其他依赖项, 想要把它单独抽离出来会更困难.
# P.s. "HH" -- 意思是 "High Level", 但我打错字母了 D:

def DoLinkHh(sko, ski, *, isReroutesToAnyType=True, isCanBetweenField=True, isCanFieldToShader=True): 
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
    tree = sko.id_data
    if tree.bl_idname=='NodeTreeUndefined': # 树不应该是丢失的.
        return # 在丢失的树中, 链接可以手动创建, 但通过 API不行; 所以退出.
    if sko.node==ski.node: # 对于同一个节点, 显然是无意义的, 尽管可能. 对接口更重要.
        return
    isSkoField = sko.type in set_utilTypeSkFields
    isSkoNdReroute = sko.node.type=='REROUTE'
    isSkiNdReroute = ski.node.type=='REROUTE'
    isSkoVirtual = (sko.bl_idname=='NodeSocketVirtual')and(not isSkoNdReroute) # 虚拟只对接口有效, 需要排除“冒名顶替的 reroute”.
    isSkiVirtual = (ski.bl_idname=='NodeSocketVirtual')and(not isSkiNdReroute) # 注意: 虚拟和插件套接字的 sk.type=='CUSTOM'.
    # 如果可以
    if not( (isReroutesToAnyType)and( (isSkoNdReroute)or(isSkiNdReroute) ) ): # 至少一个是 reroute.
        if not( (sko.bl_idname==ski.bl_idname)or( (isCanBetweenField)and(isSkoField)and(ski.type in set_utilTypeSkFields) ) ): # blid 相同或在字段之间.
            if not( (isCanFieldToShader)and(isSkoField)and(ski.type=='SHADER') ): # 字段到 shader.
                if not(isSkoVirtual or isSkiVirtual): # 它们中有一个是虚拟的 (用于接口).
                    if (not IsClassicTreeBlid(tree.bl_idname))or( IsClassicSk(sko)==IsClassicSk(ski) ): # 经典树中的插件套接字; 参见 VLT.
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
                equr = Equestrian(ski if isSkiVirtual else sko)
                skf = equr.NewSkfFromSk(skTar)
                skNew = equr.GetSkFromSkf(skf, isOut=skf.in_out!='OUTPUT') # * 痛苦的声音 *
            case 2|3:       # [-2]  -1是扩展接口,-2是新添加的接口
                _skf = (ndEq.state_items if typeEq==2 else ndEq.repeat_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
                if True: # SimRep 的重新选择是微不足道的; 因为它们没有面板, 所有新套接字都出现在底部.
                    skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
                else:
                    skNew = Equestrian(ski if isSkiVirtual else sko).GetSkFromSkf(_skf, isOut=isSkoVirtual)
            case 4:       # 新建接口-菜单切换
                _skf = ndEq.enum_items.new(GetSkLabelName(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 5|6:       # 新建接口-捕捉属性 烘焙
                _skf = (ndEq.bake_items if typeEq==5 else ndEq.capture_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 7:         # 新建接口-编号切换
                nodes = ski.node.id_data.nodes  # id_data是group/tree
                skNew = index_switch_add_input(nodes, ski.node)

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
    # 它们甚至可以相互多次连接, 太棒了. 开发者可以说“放手了”, 让它自由发展.



def VlrtRememberLastSockets(sko, ski):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        # ski 对 VLRT 来说, 如果没有 sko 就没用
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)
def NewLinkHhAndRemember(sko, ski):
    DoLinkHh(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)


def CheckUncollapseNodeAndReNext(nd: Node, self, *, cond: bool, flag=None): # 我是多么鄙视折叠起来的节点啊.
    if nd.hide and cond:
        nd.hide = False
        # 注意: 在 NextAssignmentTool 的拓扑结构中要小心无限循环.
        # 警告! type='DRAW_WIN' 会导致某些罕见的带有折叠节点的节点树崩溃! 如果知道如何重现, 最好能报个bug.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        # todo0: 如果连续展开了多个节点, 应该只重绘一次; 但没必要. 如果发生了这种情况, 说明这个工具的搜索拓扑很糟糕.
        self.NextAssignmentRoot(flag)


def FtgGetTargetOrNone(ftg) -> NodeSocket:
    return ftg.tar if ftg else None

