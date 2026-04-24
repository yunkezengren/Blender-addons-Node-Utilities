import bpy
from mathutils import Vector as Vec2
from bpy.app.translations import pgettext_iface as _iface
from bpy.types import Node, NodeSocket, NodeTree
from ..Structure import BNodeSocket
from ..common_class import VqmtData
from ..common_class import Target
from ..globals import (dict_vqmtDefaultDefault, dict_vqmtDefaultValueOperation, dict_vqmtEditorNodes, is_bl4_plus, set_classicSocketsBlid,
                       set_utilEquestrianPortalBlids, sk_type_support_field, sk_type_idname_map)

def socket_label(sk: NodeSocket):
    if isinstance(sk.node, bpy.types.NodeReroute):
        # todo 如果是自动继承的label 还需要向前寻找
        return sk.node.label if sk.node.label else sk.name
    return sk.label if sk.label else sk.name

def node_show_name(node: Node):
    if node.type == "GROUP" and node.node_tree: return node.node_tree.name
    return node.label or node.bl_rna.name  # 因为 node.name 可以修改

def sk_type_to_idname(sk: NodeSocket):
    idname = sk_type_idname_map.get(sk.type, "")
    return idname if idname else "NodeSocket" + sk.type.capitalize()

def is_builtin_tree_idname(blid: str):
    set_quartetClassicTreeBlids = {'ShaderNodeTree', 'GeometryNodeTree', 'CompositorNodeTree', 'TextureNodeTree'}
    return blid in set_quartetClassicTreeBlids

def add_item_for_index_switch(node: Node):
    nodes = node.id_data.nodes
    old_active = nodes.active
    nodes.active = node
    bpy.ops.node.index_switch_item_add()
    nodes.active = old_active
    return node.inputs[-2]

def sk_loc_遗留(sk: NodeSocket):
    return Vec2(BNodeSocket.GetFields(sk).runtime.contents.location[:]) if (sk.enabled) and (not sk.hide) else Vec2((0, 0))

def sk_loc(socket: NodeSocket):
    """这是运行时数据,界面刷新时才更新"""
    try:
        import platform
        from ctypes import c_float, c_void_p
        runtime_offset = 520  # DNA_node_types.h    - bNodeSocket        - runtime
        location_offset = 16  # BKE_node_runtime.hh - bNodeSocketRuntime - location
        if platform.system() == 'Windows':
            location_offset += 8
        if bpy.app.version >= (5, 1, 0):
            runtime_offset = 456
        if bpy.app.version >= (5, 2, 0):
            location_offset = 32
        runtime = c_void_p.from_address(socket.as_pointer() + runtime_offset).value
        return Vec2((c_float * 2).from_address(runtime + location_offset))
    except:
        raise Exception("获取接口位置出错/Get socket location error")

def node_abs_loc(nd: Node) -> Vec2:
    return nd.location + node_abs_loc(nd.parent) if nd.parent else nd.location

def is_socket_visible(socket: NodeSocket):
    return socket.enabled and (not socket.hide) and socket.is_icon_visible

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

def GenTarFromNd(nd: Node, pos: Vec2, uiScale: float): # 从 nearest_nodes_tar 中提取出来, 本来没必要, 但 VLTT 逼我这么做.
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
    return Target(nd, distance=vec.length, pos=pos-vec)

def nearest_nodes_tar(nodes, samplePos, uiScale, includePoorNodes=True): # 返回最近的节点列表. 真实的距离场.
    # 几乎是真实的. 圆角没有计算. 它们的缺失不影响使用, 而计算需要更多的操作. 所以没必要炫技.
    # 另一方面, 圆角对于折叠的节点很重要, 但我鄙视它们, 所以...
    # 框架节点被跳过, 因为没有一个工具需要它们.没有插槽的节点--就像框架节点一样;可以在搜索阶段就忽略它们.

    valid_tars: list[Target] = []
    for nd in nodes:
        if nd.type == 'FRAME':
            continue
        if not includePoorNodes and not nd.inputs and not nd.outputs:
            continue

        tar_object = GenTarFromNd(nd, samplePos, uiScale)
        valid_tars.append(tar_object)

    return sorted(valid_tars, key=lambda tar: tar.distance)

    # return sorted([GenTarFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.distance)

# 我本想添加一个自制的加速结构, 但后来突然意识到, 还需要"第二近"的信息. 所以看来不完整处理是不行的.
# 如果你知道如何加速这个过程同时保留信息, 请与我分享.
# 另一方面, 自插件诞生以来, 从未遇到过性能问题, 所以... 只是为了美观.
# 而且还需要考虑折叠的节点, 愿它们见鬼去吧, 它们可能在过程中展开, 破坏了缓存的所有美好.

def GenTarsFromPuts(nd: Node, isSide, samplePos, uiScale): # 为 vptRvEeSksHighlighting 提取出来.
    # 注意: 这个函数应该自己从标记中获取方向, 因为 `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk: NodeSocket):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    results: list[Target] = []
    ndDim = Vec2(nd.dimensions/uiScale) # "nd.dimensions" 已经包含了界面缩放的校正, 所以把它返回到世界坐标系.
    for sk in nd.outputs if isSide else reversed(nd.inputs):
        # 忽略禁用和隐藏的
        # todo 如果是被面板隐藏的话,动态开合最近的面板
        # todo 折叠节点如果展开导致重叠,就不展开?
        if is_socket_visible(sk):
            pos = sk_loc(sk)/uiScale # 该死, 这太棒了. 告别了过去版本的自制垃圾.
            # 但插槽也没有布局高度的API, 所以只能点对点地打补丁; 直到想出其他办法.
            hei = 0
            if (not isSide)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if "VectorDirection" in str(sk.bl_rna):
                    hei = 2
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not is_bl4_plus) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3
            height_box = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = _iface(socket_label(sk)) if sk.bl_idname!='NodeSocketVirtual' else _iface("Virtual" if not sk.name else socket_label(sk))
            results.append(Target(sk, distance=(samplePos-pos).length, pos=pos, side= 1 if sk.is_output else -1 , bottom_top=height_box, text=txt))
    return results

def nearest_sockets_tar(nd: Node, samplePos, uiScale): # 返回"最近的插槽"列表. 真实的 Voronoi 图单元距离场. 没错, 这个插件就是因此得名的.
    if nd.type == 'REROUTE':
        def tar_route(sk: NodeSocket):
            loc = node_abs_loc(nd)
            # 这样的话 鼠标位置在转接点左是输入,在转接点有是输出
            distance = (samplePos - loc - Vec2((sk.is_output, 0))).length
            direction = 1 if sk.is_output else -1
            label = nd.label or _iface(sk.name)
            return [Target(sk, distance=distance, pos=loc, side=direction, bottom_top=(-1, -1), text=label)]
        return tar_route(nd.inputs[0]), tar_route(nd.outputs[0])

    tar_sks_in = GenTarsFromPuts(nd, False, samplePos, uiScale)
    tar_sks_out = GenTarsFromPuts(nd, True, samplePos, uiScale)
    tar_sks_in.sort(key=lambda tar: tar.distance)
    tar_sks_out.sort(key=lambda tar: tar.distance)
    return tar_sks_in, tar_sks_out

# 弃用?
def node_domain_item_list(node: Node):
    enum_list = []
    for prop in node.bl_rna.properties:
        if prop.type == 'ENUM' and prop.identifier == "domain":
            enum_list = [item for item in prop.enum_items]
    return enum_list

def node_enum_props(node: Node) -> list[bpy.types.EnumProperty]:   # 小王-判断节点是否有下拉列表
    enum_l = []
    for prop in node.bl_rna.properties:
        if (prop.type == 'ENUM') and (prop.identifier != "warning_propagation") and (not prop.identifier.startswith("note_")) and (not (prop.is_readonly or prop.is_registered)):
            enum_l.append(prop)
    return enum_l

def node_visible_menu_inputs(node: Node) -> list[NodeSocket]:
    return [socket for socket in node.inputs if (socket.type == 'MENU' and socket.is_icon_visible)]

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""

def opt_tar_socket(tar: Target) -> NodeSocket | None:
    return tar.tar if tar else None

def IsClassicSk(sk: NodeSocket):
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return sk_type_to_idname(sk) in set_classicSocketsBlid

def compare_sk_label(sk1: NodeSocket, sk2: NodeSocket, ignore_case=False):
    if ignore_case:
        return socket_label(sk1).upper() == socket_label(sk2).upper()
    else:
        return socket_label(sk1) == socket_label(sk2)

def SelectAndActiveNdOnly(ndTar: Node):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar
    ndTar.select = True

def pick_near_target(tar1: Target, tar2: Target):
    if tar1 and tar2:
        return tar1 if tar1.distance < tar2.distance else tar2
    return tar1 or tar2

def FindAnySk(nd: Node, tar_sks_in, tar_sks_out): # Todo0NA: 需要泛化!, 用 lambda. 并且外部循环遍历列表, 而不是两个循环.
    from ..node_items import NodeItemsUtils  # 延迟导入避免循环导入
    tar_sk_out, tar_sk_in = None, None
    for tar in tar_sks_out:
        if (tar.idname!='NodeSocketVirtual')and(NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)): # todo1v6: 这个函数到处都和 !=NodeSocketVirtual 一起使用, 需要重做拓扑.
            tar_sk_out = tar
            break
    for tar in tar_sks_in:
        if (tar.idname!='NodeSocketVirtual')and(NodeItemsUtils.IsSimRepCorrectSk(nd, tar.tar)):
            tar_sk_in = tar
            break
    return pick_near_target(tar_sk_out, tar_sk_in)

def link_new_pro(sk_out: NodeSocket, sk_in: NodeSocket):
    if not (sk_out and sk_in):
        raise Exception("One of the sockets is none")
    if not (sk_out.is_output ^ sk_in.is_output):
        raise Exception("Sockets `is_output` is same")
    if sk_in.is_output:
        sk_out, sk_in = sk_in, sk_out
    tree: NodeTree = sk_out.id_data
    tree.links.new(sk_out, sk_in, handle_dynamic_sockets=True)

def VlrtRememberLastSockets(sko: NodeSocket, ski: NodeSocket):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        # ski 对 VLRT 来说, 如果没有 sko 就没用
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)

def remember_add_link(sko: NodeSocket, ski: NodeSocket):
    link_new_pro(sko, ski)
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
