from .utils_node import RestoreCollapsedNodes
from .utils_solder import SolderSkLinks
from .utils_color import get_sk_color_safe, Color4
from .utils_translate import GetAnnotFromCls, VlTrMapForKey
from .v_tool import *
from .globals import *
from .utils_ui import *
from .utils_node import *
from .utils_color import *
from .utils_solder import *
from .utils_drawing import *
from .utils_translate import *
from .common_forward_func import *
from .common_forward_class import *
from .v_tool import VoronoiToolSk


viaverSkfMethod = -1 # 用于成功交互方法的切换开关. 本可以按版本分布到映射表中, 但"根据实际情况"尝试有其独特的美学魅力.

# 注意: ViaVer'ы 尚未更新.
def ViaVerNewSkf(tree, isSide, ess, name):
    if is_bl4_plus: # Todo1VV: 重新思考拓扑结构; 使用全局函数和方法, 以及一个指向成功方法的全局变量, 实现"完全锁定".
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        socketType = ess if type(ess)==str else sk_type_to_idname(ess)
        match viaverSkfMethod:
            case 1: skf = tree.interface.new_socket(name, in_out={'OUTPUT' if isSide else 'INPUT'}, socket_type=socketType)
            case 2: skf = tree.interface.new_socket(name, in_out='OUTPUT' if isSide else 'INPUT', socket_type=socketType)
    else:
        skf = (tree.outputs if isSide else tree.inputs).new(ess if type(ess)==str else ess.bl_idname, name)
    return skf

def ViaVerGetSkfa(tree, isSide):
    if is_bl4_plus:
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        match viaverSkfMethod:
            case 1: return tree.interface.ui_items
            case 2: return tree.interface.items_tree
    else:
        return (tree.outputs if isSide else tree.inputs)

def ViaVerGetSkf(tree, isSide, name):
    return ViaVerGetSkfa(tree, isSide).get(name)

def ViaVerSkfRemove(tree, isSide, name):
    if is_bl4_plus:
        tree.interface.remove(name)
    else:
        (tree.outputs if isSide else tree.inputs).remove(name)





class VptWayTree():
    def __init__(self, tree=None, nd=None):
        self.tree = tree
        self.nd = nd
        self.isUseExtAndSkPr = None # 为清理操作做的优化.
        self.finalLink = None # 为了在RvEe中更合理地组织.

def VptGetTreesPath(nd):
    list_path = [VptWayTree(pt.node_tree, pt.node_tree.nodes.active) for pt in bpy.context.space_data.path]
    # 据我判断, 节点编辑器的实现本身并不存储用户进入节点组时所通过的>节点<(但这不确定).
    # 因此, 如果活动节点不是节点组, 就用第一个找到的-按组的-节点替换它 (如果找不到, 则为无).
    for curWy, upWy in zip(list_path, list_path[1:]):
        if (not curWy.nd)or(curWy.nd.type!='GROUP')or(curWy.nd.node_tree!=upWy.tree): # 确定深度之间的连接缺失.
            curWy.nd = None # 摆脱当前不正确的节点. 最好是没有.
            for nd in curWy.tree.nodes:
                if (nd.type=='GROUP')and(nd.node_tree==upWy.tree): # 如果在当前深度中存在一个带有不正确节点的, 但其节点组是正确的节点组节点.
                    curWy.nd = nd
                    break # 这个深度的修复成功完成.
    return list_path

def VptGetGeoViewerFromTree(tree):
    #Todo1PR: 对于后续深度, 立即重新连接到查看器也很重要, 但请参见|1|, 当前的逻辑流程不适合这样做.
    # 因此不再支持, 因为只"解决"了一半. 所以老朋友锚点来帮忙.
    nameView = ""
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='SPREADSHEET':
                for space in area.spaces:
                    if space.type=='SPREADSHEET':
                        nameView = space.viewer_path.path[-1].ui_name #todo0VV
                        break
    if nameView:
        nd = tree.nodes.get(nameView)
    else:
        for nd in reversed(tree.nodes):
            if nd.type=='VIEWER':
                break # 只需要第一个遇到的查看器, 否则行为会不方便.
    if nd:
        if any(True for sk in nd.inputs[1:] if sk.vl_sold_is_final_linked_cou): # Todo1PR: 也许这需要一个选项. 总的来说, 这个查看器这里一团糟.
            return nd # 仅当查看器有用于查看字段的链接时才选择它.
    return None

def VptGetRootNd(tree):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            for nd in tree.nodes:
                if (nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD', 'OUTPUT_LIGHT', 'OUTPUT_LINESTYLE',
                                'OUTPUT'}) and (nd.is_active_output):
                    return nd
                if nd.type == 'NPR_OUTPUT':  # 小王-npr预览
                    return nd
        case 'GeometryNodeTree':
            if nd:=VptGetGeoViewerFromTree(tree):
                return nd
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    for sk in nd.inputs:
                        if sk.type=='GEOMETRY':
                            return nd
        case 'CompositorNodeTree':
            for nd in tree.nodes:
                if nd.type=='VIEWER':
                    return nd
            for nd in tree.nodes:
                if nd.type=='COMPOSITE':
                    return nd
        case 'TextureNodeTree':
            for nd in tree.nodes:
                if nd.type=='OUTPUT':
                    return nd
    return None

def VptGetRootSk(tree, ndRoot, skTar):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            inx = 0
            if ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD'}:
            # if ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD', 'NPR_OUTPUT'}:   # 小王-npr预览
                inx =  (skTar.name=="Volume")or(ndRoot.inputs[0].hide)
            else:
                for node in tree.nodes:
                    if node.type == 'NPR_OUTPUT':
                        return node.inputs[0]
            return ndRoot.inputs[inx]
        case 'GeometryNodeTree':
            for sk in ndRoot.inputs:
                if sk.type=='GEOMETRY':
                    return sk
    return ndRoot.inputs[0] # 注意: 这里也会接收到上面 GeometryNodeTree 的失败情况.


def VptPreviewFromSk(self, prefs, skTar):
    if not(skTar and skTar.is_output):
        return
    list_way = DoPreviewCore(skTar, self.list_distanceAnchors, self.cursorLoc)
    if self.isSelectingPreviewedNode:
        SelectAndActiveNdOnly(skTar.node) # 不仅要只选择它, 还要让它成为活动节点, 这很重要.
    if not self.in_builtin_tree:
        return
    # 我天才般地想到在预览后删除接口; 这得益于在上下文路径中不删除它们. 现在可以更自由地使用它们了.
    if (True)or(not self.tree.nodes.get(voronoiAnchorCnName)): # 关于 'True' 请阅读下文.
        # 如果当前树中有锚点, 则不删除任何 voronoiSkPreviewName; 这使得工具的另一种特殊用法成为可能.
        # 这本应是"撞到锚点后终止"的逻辑延续, 但我直到现在才想到.
        # P.s. 我忘了是哪个了. 现在它们不会从上下文路径中被删除, 所以信息丢失了 D:
        dict_treeNext = dict({(wy.tree, wy.isUseExtAndSkPr) for wy in list_way})
        dict_treeOrder = dict({(wy.tree, cyc) for cyc, wy in enumerate(reversed(list_way))}) # 路径有链接, 中间不知道尾部, 所以从当前深度到根, 以便"级联"正确处理.
        for ng in sorted(bpy.data.node_groups, key=lambda a: dict_treeOrder.get(a,-1)):
            # 删除所有先前使用该工具的痕迹, 对于所有与当前编辑器类型相同的节点组.
            if ng.bl_idname==self.tree.bl_idname:
                # 但不删除上下文路径树的桥梁 (如果它们的插槽为空则删除).
                sk = dict_treeNext.get(ng, None) # 对于Ctrl-F: isUseExtAndSkPr 在这里使用.
                if (ng not in dict_treeNext)or((not sk.vl_sold_is_final_linked_cou) if sk else None)or( (ng==self.tree)and(sk) ):
                    sk = True
                    while sk: # 按名称搜索. 用户可能会创建副本, 导致没有 while 的话每次激活预览都会消失一个.
                        sk = ViaVerGetSkf(ng, True, voronoiSkPreviewName)
                        if sk:
                            ViaVerSkfRemove(ng, True, sk)
    if (prefs.vptRvEeIsSavePreviewResults)and(not self.isAnyAncohorExist): # 帮助逆向工程 -- 保存当前查看的插槽以供后续"管理".
        def GetTypeOfNodeSave(sk):
            match sk.type:
                case 'GEOMETRY': return 2
                case 'SHADER': return 1
                case _: return 0
        finalLink = list_way[-1].finalLink
        idSave = GetTypeOfNodeSave(finalLink.from_socket)
        pos = finalLink.to_node.location
        pos = (pos[0]+finalLink.to_node.width+40, pos[1])
        ndRvSave = self.tree.nodes.get(voronoiPreviewResultNdName)
        if ndRvSave:
            if ndRvSave.label!=voronoiPreviewResultNdName:
                ndRvSave.name += "_"+ndRvSave.label
                ndRvSave = None
            elif GetTypeOfNodeSave(ndRvSave.outputs[0])!=idSave: # 如果这是另一种保存类型的节点.
                pos = ndRvSave.location.copy() # 切换类型时保存"活动"保存节点的位置. 注意: 不要忘记 .copy(), 因为之后节点会被删除.
                self.tree.nodes.remove(ndRvSave)
                ndRvSave = None
        if not ndRvSave:
            match idSave:
                case 0: txt = "MixRGB" # 因为它可以在所有编辑器中使用; 还有 Shift+G > Type.
                case 1: txt = "AddShader"
                case 2: txt = "SeparateGeometry" # 需要一个影响(负载)最小且支持所有几何类型的节点, (并且没有多输入).
            ndRvSave = self.tree.nodes.new(self.tree.bl_idname.replace("Tree","")+txt)
            ndRvSave.location = pos
        ndRvSave.name = voronoiPreviewResultNdName
        ndRvSave.select = False
        ndRvSave.label = ndRvSave.name
        ndRvSave.use_custom_color = True
        # 给保存节点上色
        match idSave:
            case 0:
                ndRvSave.color = SoldThemeCols.color_node3
                ndRvSave.show_options = False
                ndRvSave.blend_type = 'ADD'
                ndRvSave.inputs[0].default_value = 0
                ndRvSave.inputs[1].default_value = power_color4(SoldThemeCols.color_node4, pw=2.2)
                ndRvSave.inputs[2].default_value = ndRvSave.inputs[1].default_value # 有点多余.
                ndRvSave.inputs[0].hide = True
                ndRvSave.inputs[1].name = "Color"
                ndRvSave.inputs[2].hide = True
            case 1:
                ndRvSave.color = SoldThemeCols.shader_node3
                ndRvSave.inputs[1].hide = True
            case 2:
                ndRvSave.color = SoldThemeCols.geometry_node3
                ndRvSave.show_options = False
                ndRvSave.inputs[1].hide = True
                ndRvSave.outputs[0].name = "Geometry"
                ndRvSave.outputs[1].hide = True
        self.tree.links.new(finalLink.from_socket, ndRvSave.inputs[not idSave])
        self.tree.links.new(ndRvSave.outputs[0], finalLink.to_socket)

vptFeatureUsingExistingPath = True
# 注意: 不考虑模拟和重复区域的接口, 处理它们需要搜索树中的每个节点, 会导致 BigO 警告.
# Todo1PR: 需要全部重新梳理; 但首先要做所有可能的深度, 锚点, 几何查看器, 节点缺失, "已有路径"等组合的测试 (还有插件节点树), 以及本地的 BigO.
def DoPreviewCore(skTar, list_distAnchs, cursorLoc):
    def NewLostNode(type, ndTar=None):
        ndNew = tree.nodes.new(type)
        if ndTar:
            ndNew.location = ndTar.location
            ndNew.location.x += ndTar.width*2
        return ndNew
    list_way = VptGetTreesPath(skTar.node)
    higWay = length(list_way)-1
    list_way[higWay].nd = skTar.node # 通过默认的保证-流程进入的深度, 目标节点不会被处理, 所以需要明确指定. (别忘了把这段精灵语翻译成中文 😂)
    ##
    previewSkType = "RGBA" # 颜色, 而不是着色器 -- 因为有时需要在预览路径上插入节点.
    # 但如果链接是着色器类型的 -- 准备好失望吧. 所以用颜色 (这也是 NW 最初的方式).
    isGeoTree = list_way[0].tree.bl_idname=='GeometryNodeTree'
    if isGeoTree:
        previewSkType = "GEOMETRY"
    elif skTar.type=='SHADER':
        previewSkType = "SHADER"
    dnfLastSkEx = '' # 用于 vptFeatureUsingExistingPath.
    def GetBridgeSk(puts):
        sk = puts.get(voronoiSkPreviewName)
        if (sk)and(sk.type!=previewSkType):
            ViaVerSkfRemove(tree, True, ViaVerGetSkf(tree, True, voronoiSkPreviewName))
            return None
        return sk
    def GetTypeSkfBridge():
        match previewSkType:
            case 'GEOMETRY': return "NodeSocketGeometry"
            case 'SHADER':   return "NodeSocketShader"
            case 'RGBA':     return "NodeSocketColor"
    ##
    isInClassicTrees = is_builtin_tree_idname(skTar.id_data.bl_idname)
    for cyc in reversed(range(higWay+1)):
        curWay = list_way[cyc]
        tree = curWay.tree
        # 确定发送节点:
        portalNdFrom = curWay.nd # skTar.node 已经包含在 cyc==higWay 的路径中.
        isCreatedNgOut = False
        if not portalNdFrom:
            portalNdFrom = tree.nodes.new(tree.bl_idname.replace("Tree","Group"))
            portalNdFrom.node_tree = list_way[cyc+1].tree
            isCreatedNgOut = True # 为了从接收节点设置节点位置, 而接收节点现在未知.
        assert portalNdFrom
        # 确定接收节点:
        portalNdTo = None
        if not cyc: # 根节点.
            portalNdTo = VptGetRootNd(tree)
            if (not portalNdTo)and(isInClassicTrees):
                # "视觉通知", 表明没有地方可以连接. 本可以手动添加, 但懒得折腾 ShaderNodeTree 的接收节点.
                portalNdTo = NewLostNode('NodeReroute', portalNdFrom) # "我无能为力".
        else: # 后续深度.
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    portalNdTo = nd
                    break
            if not portalNdTo:
                # 自己创建组输出, 而不是停下来不知所措.
                portalNdTo = NewLostNode('NodeGroupOutput', portalNdFrom)
            if isGeoTree:
                # 现在查看器的存在行为类似于锚点.
                if nd:=VptGetGeoViewerFromTree(tree):
                    portalNdTo = nd
        if isCreatedNgOut:
            portalNdFrom.location = portalNdTo.location-Vec2((portalNdFrom.width+40, 0))
        assert portalNdTo or not isInClassicTrees
        # 确定发送插槽:
        portalSkFrom = None
        if (vptFeatureUsingExistingPath)and(dnfLastSkEx):
            for sk in portalNdFrom.outputs:
                if sk.identifier==dnfLastSkEx:
                    portalSkFrom = sk
                    break
            dnfLastSkEx = '' # 清空很重要. 选择的插槽可能没有链接或连接到下一个门户, 从而导致下一个深度不匹配.
        if not portalSkFrom:
            if cyc==higWay:
                portalSkFrom = skTar
            else:
                try:
                    portalSkFrom = GetBridgeSk(portalNdFrom.outputs)
                except:
                    return list_way
        assert portalSkFrom
        # 确定接收插槽:
        portalSkTo = None
        if (isGeoTree)and(portalNdTo.type=='VIEWER'):
            portalSkTo = portalNdTo.inputs[0]
        if (not portalSkTo)and(vptFeatureUsingExistingPath)and(cyc): # 对于非根节点记录才有意义.
            # 我的改进发明 -- 如果连接已经存在, 为什么要旁边创建另一个相同的?.
            # 这在美学上很舒服, 也有助于在不离开目标深度的情况下清理预览的后果 (添加了条件, 见清理部分).
            for lk in portalSkFrom.vl_sold_links_final:
                # 由于接口不被删除, 它将从这里获得, 而不是下面的主流方式 (结果也一样), 所以第二次检查是为了 isUseExtAndSkPr.
                if (lk.to_node==portalNdTo)and(lk.to_socket.name!=voronoiSkPreviewName):
                    portalSkTo = lk.to_socket
                    dnfLastSkEx = portalSkTo.identifier # 节点组节点的输出和组输出的输入是匹配的. 保存信息以供下一个深度继续.
                    curWay.isUseExtAndSkPr = GetBridgeSk(portalNdTo.inputs) # 用于清理. 如果没有链接, 就删除. 清理时不会实际搜索它们, 因为 BigO.
        if (not portalSkTo)and(isInClassicTrees): # 主要获取方式.
            portalSkTo = VptGetRootSk(tree, portalNdTo, skTar) if not cyc else GetBridgeSk(portalNdTo.inputs) # |1|.
        if (not portalSkTo)and(cyc): # 后续深度 -- 总是组, 需要为它们生成 skf. `cyc` 的检查不是必须的, 根节点的插槽(因为重路由)总是会有的.
            # 如果上面无法从节点组节点的输入中获取插槽, 那么接口也不存在. 因此 `not tree.outputs.get(voronoiSkPreviewName)` 的检查没有必要.
            ViaVerNewSkf(tree, True, GetTypeSkfBridge(), voronoiSkPreviewName).hide_value = True
            portalSkTo = GetBridgeSk(portalNdTo.inputs) # 重新选择新创建的.
        # 处理锚点, 模拟显式指定经典输出:
        if (cyc==higWay)and(VptData.reprSkAnchor):
            skAnchor = None
            try:
                skAnchor = eval(VptData.reprSkAnchor)
                if skAnchor.id_data!=skTar.id_data:
                    skAnchor = None
                    VptData.reprSkAnchor = ""
            except:
                VptData.reprSkAnchor = ""
            if (skAnchor):# and(skAnchor.node!=skTar.node):
                portalSkTo = skAnchor
        assert portalSkTo or not isInClassicTrees
        # 连接:
        ndAnchor = tree.nodes.get(voronoiAnchorCnName)
        if (cyc==higWay)and(not ndAnchor)and(list_distAnchs): # 最近的从光标处搜索; 非目标深度从哪里获取光标?.
            min = 32768
            for nd in list_distAnchs:
                len = (nd.location-cursorLoc).length
                if min>len:
                    min = len
                    ndAnchor = nd
        if ndAnchor: # 锚点使"计划有变", 并将流重定向到自己身上.
            lk = tree.links.new(portalSkFrom, ndAnchor.inputs[0])
            # print(f"0 {ndAnchor = }")
            #tree.links.new(ndAnchor.outputs[0], portalSkTo)
            curWay.finalLink = lk
            break # 撞到锚点后终止, 提高了锚点的使用可能性, 使其更酷. 如果你对 Voronoi_Anchor 有好感, 我理解你. 我也是.
            # 终止允许从带有锚点的深度到根节点有用户自定义的连接, 而不破坏它们.
        elif (portalSkFrom)and(portalSkTo): # assert portalSkFrom and portalSkTo # 否则是常规的路由连接.
            lk = tree.links.new(portalSkFrom, portalSkTo)
            # view_node = portalSkTo.node       # 小王-想让预览器自动激活
            # if view_node.bl_idname == "GeometryNodeViewer":
            #     view_node.hide = True
            #     print(f"1 {view_node.bl_idname = }")
            curWay.finalLink = lk
    return list_way


class VoronoiPreviewTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_preview'
    bl_label = "Voronoi Preview"
    usefulnessForCustomTree = True
    isSelectingPreviewedNode: bpy.props.BoolProperty(name="Select previewed node", default=True)
    isTriggerOnlyOnLink:      bpy.props.BoolProperty(name="Only linked",           default=False, description="Trigger only on linked socket") #最初在 prefs 中.
    isEqualAnchorType:        bpy.props.BoolProperty(name="Equal anchor type",     default=False, description="Trigger only on anchor type sockets")
    def CallbackDrawTool(self, drata):
        if (self.prefs.vptRvEeSksHighlighting)and(self.fotagoSk): #帮助逆向工程 -- 高亮连接点, 并同时显示这些接口的名称.
            SolderSkLinks(self.tree) #否则在 `ftg.tar==sk:` 上会崩溃.
            #确定标签的缩放比例:
            soldCursorLoc = drata.cursorLoc
            #绘制:
            ndTar = self.fotagoSk.tar.node
            for isSide in (False, True):
                for skTar in ndTar.outputs if isSide else ndTar.inputs:
                    for lk in skTar.vl_sold_links_final:
                        sk = lk.to_socket if isSide else lk.from_socket
                        nd = sk.node
                        if (nd.type!='REROUTE')and(not nd.hide):
                            list_ftgSks = GenFtgsFromPuts(nd, not isSide, soldCursorLoc, drata.uiScale)
                            for ftg in list_ftgSks:
                                if ftg.tar==sk:
                                    #不支持遍历转接点. 因为懒, 而且懒得为此重写代码.
                                    if drata.dsIsDrawSkArea:
                                        DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Color4(get_sk_color_safe(ftg.tar)))
                                    DrawVlSkText(drata, ftg.pos, (1-isSide*2, -0.5), ftg, fontSizeOverwrite=min(24*drata.worldZoom*self.prefs.vptHlTextScale, 25))
                                    break
                        nd.hide = False #在绘制时写入. 至少不像 VMLT 中那么严重.
                        #todo0SF: 使用 bpy.ops.wm.redraw_timer 会导致死锁. 所以这里还有另一个“跳帧”.
        TemplateDrawSksToolHh(drata, self.fotagoSk, isDrawMarkersMoreTharOne=True, tool_name="Preview")
    @staticmethod
    def OmgNodeColor(nd, col=None):
        set_omgApiNodesColor = {'FunctionNodeInputColor'} #https://projects.blender.org/blender/blender/issues/104909
        if nd.bl_idname in set_omgApiNodesColor:
            bn = BNode.GetFields(nd)
            if col:
                bn.color[0] = col[0]
                bn.color[1] = col[1]
                bn.color[2] = col[2]
            else:
                return (bn.color[0], bn.color[1], bn.color[2])
        else:
            if col:
                nd.color = col
            else:
                return nd.color.copy()
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        SolderSkLinks(tree) #否则会崩溃.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        if False:
            #我已经为Viewer添加了一个粘附在字段上的功能, 但后来我意识到没有API可以取代它的预览类型. 又来了. 我们必须保持低调. 用于粘附到几何查看器的字段.
            # 我已经添加了为查看器附加到字段的功能, 但后来我意识到没有API可以更改其预览类型. 又来了. 不得不保持低调.
            isGeoViewer = False #用于为几何查看器附加到字段.
            if isGeoTree:
                for nd in tree.nodes:
                    if nd.type=='VIEWER':
                        isGeoViewer = True
                        break
        self.fotagoSk = None #没必要, 但为了清晰起见重置. 对调试很有用.
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            if (prefs.vptRvEeIsSavePreviewResults)and(nd.name==voronoiPreviewResultNdName): #忽略准备好的节点以进行重命名, 从而保存预览结果.
                continue
            #如果在几何节点中, 则忽略没有几何输出的节点
            if (isGeoTree)and(not self.isAnyAncohorExist):
                if not any(True for sk in nd.outputs if (sk.type=='GEOMETRY')and(not sk.hide)and(sk.enabled)): #寻找可见的几何接口.
                    continue
            #如果视觉上没有接口, 或者有但只有虚拟接口, 则跳过节点. 对于转接点, 一切都无用.
            if (not any(True for sk in nd.outputs if (not sk.hide)and(sk.enabled)and(sk.bl_idname!='NodeSocketVirtual')))and(nd.type!='REROUTE'):
                continue
            #以上所有都是为了让点不只是挂在那里, 节点不干扰工具的方便使用. 感觉就像“透明”节点.
            #忽略自己的特殊转接点锚点 (检查类型和名称)
            if ( (nd.type=='REROUTE')and(nd.name==voronoiAnchorCnName) ):
                continue
            #如果成功, 则转到接口:
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            for ftg in list_ftgSksOut:
                #在这里忽略自己的桥接接口. 这对于节点组节点是必要的, 它们的桥接接口“伸出”并且没有这个检查就会被粘住; 之后它们将在 VptPreviewFromSk() 中被删除.
                if ftg.tar.name==voronoiSkPreviewName:
                    continue
                #这个工具会触发除虚拟接口外的任何输出. 在几何节点中只寻找几何输出.
                #锚点吸引预览; 转接点可以接受任何类型; 因此 -- 如果有锚点, 则禁用仅对几何接口的触发
                if (ftg.blid!='NodeSocketVirtual')and( (not isGeoTree)or(ftg.tar.type=='GEOMETRY')or(self.isAnyAncohorExist) ):
                    can = True
                    if rrAnch:=tree.nodes.get(voronoiAnchorCnName): #EqualAnchorType.
                        rrSkBlId = rrAnch.outputs[0].bl_idname
                        can = (not self.isEqualAnchorType)or(ftg.blid==rrSkBlId)or(rrSkBlId=='NodeSocketVirtual')
                    #todo1v6 对于邻近锚点也按类型选择?
                    can = (can)and(not ftg.tar.node.label==voronoiAnchorDtName) #ftg.tar.node not in self.list_distanceAnchors
                    if can:
                        if (not self.isTriggerOnlyOnLink)or(ftg.tar.vl_sold_is_final_linked_cou): #帮助逆向工程 -- 仅在现有链接上触发; 加快“读取/理解”树的过程.
                            self.fotagoSk = ftg
                            break
            if self.fotagoSk: #如果成功则完成. 否则, 例如忽略自己的桥接接口, 如果节点只有它们 -- 将停在旁边而找不到其他.
                break
        if self.fotagoSk:
            CheckUncollapseNodeAndReNext(nd, self, cond=True)
            if prefs.vptIsLivePreview:
                # print("."*100)
                # print(f"{self.fotagoSk = }")
                # print(f"{self.fotagoSk.tar = }")
                VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
            if prefs.vptRvEeIsColorOnionNodes: #帮助逆向工程 -- 不是用眼睛寻找细线, 而是快速视觉读取拓扑连接的节点.
                SolderSkLinks(tree) #没有这个, 将不得不手动为接收节点着色, 以免“闪烁”.
                ndTar = self.fotagoSk.tar.node
                #不要费心记住最后一个, 每次都把它们全部关闭. 简单粗暴
                for nd in tree.nodes:
                    nd.use_custom_color = False
                def RecrRerouteWalkerPainter(sk, col):
                    for lk in sk.vl_sold_links_final:
                        nd = lk.to_node if sk.is_output else lk.from_node
                        if nd.type=='REROUTE':
                            RecrRerouteWalkerPainter(nd.outputs[0] if sk.is_output else nd.inputs[0], col)
                        else:
                            nd.use_custom_color = True
                            if (not prefs.vptRvEeIsSavePreviewResults)or(nd.name!=voronoiPreviewResultNdName): #不重新着色用于保存结果的节点
                                self.OmgNodeColor(nd, col)
                            nd.hide = False #并展开它们.
                for sk in ndTar.outputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorOut)
                for sk in ndTar.inputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorIn)
    def MatterPurposeTool(self, event, prefs, tree):
        SolderSkLinks(tree) #否则会崩溃.
        VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
        VlrtRememberLastSockets(self.fotagoSk.tar, None)
        if prefs.vptRvEeIsColorOnionNodes:
            for nd in tree.nodes:
                dv = self.dict_saveRestoreNodeColors.get(nd, None) #与 RestoreCollapsedNodes 中完全相同.
                if dv:
                    nd.use_custom_color = dv[0]
                    self.OmgNodeColor(nd, dv[1])
    def InitTool(self, event, prefs, tree):
        #如果允许使用经典查看器, 则用跳过标记完成工具, “将接力棒传给”原始查看器.
        match tree.bl_idname:
            case 'GeometryNodeTree':
                if (prefs.vptAllowClassicGeoViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
            case 'CompositorNodeTree':
                if (prefs.vptAllowClassicCompositorViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
        if prefs.vptRvEeIsColorOnionNodes:
            #记住所有颜色, 并将它们全部重置:
            self.dict_saveRestoreNodeColors = {}
            for nd in tree.nodes:
                self.dict_saveRestoreNodeColors[nd] = (nd.use_custom_color, self.OmgNodeColor(nd))
                nd.use_custom_color = False
            #注意: 带有洋葱皮颜色的保存结果节点按原样处理. 重复的节点不会保持不受影响.
        #焊接:
        list_distAnchs = []
        for nd in tree.nodes:
            if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                list_distAnchs.append(nd)
                nd.label = voronoiAnchorDtName #也用于检查自己的转接点.
        self.list_distanceAnchors = list_distAnchs
        #焊接:
        rrAnch = tree.nodes.get(voronoiAnchorCnName)
        #一些用户在“初次接触”工具时会想重命名锚点.
        #每次调用锚点的标题都是一样的, 再次调用时标题仍然会变回标准标题.
        #之后用户会明白重命名锚点是没用的.
        if rrAnch:
            rrAnch.label = voronoiAnchorCnName #这个设置只是加速了意识到的过程.
        self.isAnyAncohorExist = not not (rrAnch or list_distAnchs) #对于几何节点; 如果其中有锚点, 则不仅触发几何接口.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vptAllowClassicGeoViewer')
        LyAddLeftProp(col, prefs,'vptAllowClassicCompositorViewer')
        LyAddLeftProp(col, prefs,'vptIsLivePreview')
        row = col.row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeIsColorOnionNodes')
        if prefs.vptRvEeIsColorOnionNodes:
            row.prop(prefs,'vptOnionColorIn', text="")
            row.prop(prefs,'vptOnionColorOut', text="")
        else:
            LyAddNoneBox(row)
            LyAddNoneBox(row)
        row = col.row().row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeSksHighlighting')
        if True:#prefs.vptRvEeSksHighlighting:
            row = row.row(align=True)
            row.prop(prefs,'vptHlTextScale', text="Scale")
            row.active = prefs.vptRvEeSksHighlighting
        LyAddLeftProp(col, prefs,'vptRvEeIsSavePreviewResults')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectingPreviewedNode').name) as dm:
            dm["ru_RU"] = "Выделять предпросматриваемый нод"
            dm["zh_CN"] = "自动选择被预览的节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').name) as dm:
            dm["ru_RU"] = "Только подключённые"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').description) as dm:
            dm["ru_RU"] = "Цепляться только на подключённые сокеты"
            dm["zh_CN"] = "只预览已有连接的输出接口"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').name) as dm:
            dm["ru_RU"] = "Равный тип якоря"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').description) as dm:
            dm["ru_RU"] = "Цепляться только к сокетам типа якоря"
            dm["zh_CN"] = "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的接口类型一样才能被预览连接"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').name) as dm:
            dm["ru_RU"] = "Разрешить классический Viewer Геометрических узлов"
            dm["zh_CN"] = "几何节点里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').description) as dm:
            dm["ru_RU"] = "Разрешить использование классического Viewer'а геометрических нодов путём клика по ноду"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').name) as dm:
            dm["ru_RU"] = "Разрешить классический Viewer Композитора"
            dm["zh_CN"] = "合成器里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').description) as dm:
            dm["ru_RU"] = "Разрешить использование классического Viewer'а композиторных нодов путём клика по ноду"
            dm["zh_CN"] = "默认是按顺序轮选输出接口端无法直选第N个通道接口"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').name) as dm:
            dm["ru_RU"] = "Предварительный просмотр в реальном времени"
            dm["zh_CN"] = "实时预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').description) as dm:
            dm["ru_RU"] = "Предпросмотр в реальном времени"
            dm["zh_CN"] = "即使没松开鼠标也能观察预览结果"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').name) as dm:
            dm["ru_RU"] = "Луковичные цвета нод"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').description) as dm:
            dm["ru_RU"] = "Окрашивать топологически соединённые ноды"
            dm["zh_CN"] = "快速预览时将与预览的节点有连接关系的节点全部着色显示"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').name) as dm:
            dm["ru_RU"] = "Подсветка топологических соединений"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').description) as dm:
            dm["ru_RU"] = "Отображать имена сокетов, чьи линки подсоединены к ноду"
            dm["zh_CN"] = "快速预览时高亮显示连接到预览的节点的上级节点的输出接口"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').name) as dm:
            dm["ru_RU"] = "Сохранять результаты предпросмотра"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').description) as dm:
            dm["ru_RU"] = "Создавать предпросмотр через дополнительный нод, удобный для последующего копирования"
            dm["zh_CN"] = "保存预览结果,通过新建一个预览节点连接预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorIn').name) as dm:
            dm["ru_RU"] = "Луковичный цвет входа"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorOut').name) as dm:
            dm["ru_RU"] = "Луковичный цвет выхода"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptHlTextScale').name) as dm:
            dm["ru_RU"] = "Масштаб текста"
#            dm["zh_CN"] = ""