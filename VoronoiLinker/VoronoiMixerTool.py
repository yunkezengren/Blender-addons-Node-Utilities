from .common_class import VmtData
from .VoronoiTool import VoronoiToolPairSk
from .关于颜色的函数 import power_color4, get_sk_color_safe


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
    previewSkType = "Color4" # 颜色, 而不是着色器 -- 因为有时需要在预览路径上插入节点.
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
            case 'Color4':     return "NodeSocketColor"
    ##
    isInClassicTrees = IsClassicTreeBlid(skTar.id_data.bl_idname)
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
def VptPreviewFromSk(self, prefs, skTar):
    if not(skTar and skTar.is_output):
        return
    list_way = DoPreviewCore(skTar, self.list_distanceAnchors, self.cursorLoc)
    if self.isSelectingPreviewedNode:
        SelectAndActiveNdOnly(skTar.node) # 不仅要只选择它, 还要让它成为活动节点, 这很重要.
    if not self.isInvokeInClassicTree:
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


class VoronoiMixerTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #放在第一位, 以便在 kmi 中与 VQMT 类似.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None #需要清空, 因为下面有两个 continue.
        self.fotagoSk1 = None
        soldReroutesCanInAnyType = prefs.vmtReroutesCanInAnyType
        for ftgNd in self.ToolGetNearestNodes(cur_x_off=Cursor_X_Offset):
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksOut = self.ToolGetNearestSockets(nd, cur_x_off=Cursor_X_Offset)[1]
            if not list_ftgSksOut:
                continue
            #节点过滤器没有必要.
            #这个工具会触发第一个遇到的任何输出 (现在除了虚拟接口).
            if isFirstActivation:
                self.fotagoSk0 = list_ftgSksOut[0] if list_ftgSksOut else None
            #对于第二个, 根据条件:
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut:
                    skOut1 = ftg.tar
                    if skOut0==skOut1:
                        break
                    orV = (skOut1.bl_idname=='NodeSocketVirtual')or(skOut0.bl_idname=='NodeSocketVirtual')
                    #现在 VMT 又可以连接到虚拟接口了
                    tgl = (skOut1.bl_idname=='NodeSocketVirtual')^(skOut0.bl_idname=='NodeSocketVirtual')
                    tgl = (tgl)or( self.SkBetweenFieldsCheck(skOut0, skOut1)or( (skOut1.bl_idname==skOut0.bl_idname)and(not orV) ) )
                    tgl = (tgl)or( (skOut0.node.type=='REROUTE')or(skOut1.node.type=='REROUTE') )and(soldReroutesCanInAnyType)
                    if tgl:
                        self.fotagoSk1 = ftg
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #检查是否是自我复制.
                    self.fotagoSk1 = None
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            #尽管节点过滤器没有必要, 并且在第一个遇到的节点上工作得很好, 但如果第一个接口没有找到, 仍然需要继续搜索.
            #因为如果第一个(最近的)节点搜索结果失败, 循环将结束, 工具将不会选择任何东西, 即使旁边有合适的.
            if self.fotagoSk0: #在使用现在不存在的 isCanReOut 时尤其明显; 如果没有这个, 结果会根据光标位置成功/不成功地选择.
                break
    def MatterPurposePoll(self):
        if not self.fotagoSk0:
            return False
        if self.isCanFromOne:
            return (self.fotagoSk0.blid!='NodeSocketVirtual')or(self.fotagoSk1)
        else:
            return self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        VmtData.sk0 = self.fotagoSk0.tar
        socket1 = FtgGetTargetOrNone(self.fotagoSk1)
        VmtData.sk1 = socket1
        #对虚拟接口的支持已关闭; 只从第一个读取
        VmtData.skType = VmtData.sk0.type if VmtData.sk0.bl_idname!='NodeSocketVirtual' else socket1.type
        VmtData.isHideOptions = self.isHideOptions
        VmtData.isPlaceImmediately = self.isPlaceImmediately
        _sk = VmtData.sk0
        if socket1 and socket1.type == "MATRIX":
            VmtData.skType = "MATRIX"
            _sk = VmtData.sk1
        SetPieData(self, VmtData, prefs, power_color4(get_sk_color_safe(_sk), pw=2.2))
        if not self.isInvokeInClassicTree: #由于 usefulnessForCustomTree, 这是个无用的检查.
            return {'CANCELLED'} #如果操作地点不在经典编辑器中, 就直接退出. 因为经典编辑器对所有人都一样, 而插件编辑器有无数种.

        tup_nodes = dict_vmtTupleMixerMain.get(tree.bl_idname, False).get(VmtData.skType, None)
        if tup_nodes:
            if length(tup_nodes)==1: #如果只有一个选择, 就跳过它直接进行混合.
                DoMix(tree, False, False, tup_nodes[0]) #在即时激活时, 可能没有释放修饰键. 因此 DoMix() 接收的是手动设置而不是 event.
            else: #否则提供选择
                bpy.ops.wm.call_menu_pie(name=VmtPieMixer.bl_idname)
        else: #否则接口类型未定义 (例如几何节点中的着色器).
            DisplayMessage(self.bl_label, txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmtReroutesCanInAnyType')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Pie")+f" ({cls.vlTripleName})")
        tlw = cls.vlTripleName.lower()
        LyAddHandSplitProp(colBox, prefs,f'{tlw}PieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieScale')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieAlignment')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieDisplaySocketColor')
        colProps.active = getattr(prefs,f'{tlw}PieType')=='CONTROL'
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanFromOne').name) as dm:
            dm["ru_RU"] = "Может от одного сокета"
            dm["zh_CN"] = "从一个端口连接"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPlaceImmediately').name) as dm:
            dm["ru_RU"] = "Размещать моментально"
            dm["zh_CN"] = "立即添加节点到鼠标位置"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmtReroutesCanInAnyType').name) as dm:
            dm["ru_RU"] = "Рероуты могут смешиваться с любым типом"
            dm["zh_CN"] = "快速混合不限定端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType').name) as dm:
            dm["ru_RU"] = "Тип пирога"
            dm["zh_CN"] = "饼菜单类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',0).name) as dm:
            dm["ru_RU"] = "Контроль"
            dm["zh_CN"] = "控制(自定义)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',1).name) as dm:
            dm["ru_RU"] = "Скорость"
            dm["zh_CN"] = "速度型(多层菜单)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieScale').name) as dm:
            dm["ru_RU"] = "Размер пирога"
            dm["zh_CN"] = "饼菜单大小"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').name) as dm:
            dm["ru_RU"] = "Выравнивание между элементами"
#            dm["zh_CN"] = "元素对齐方式"?
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').description) as dm:
            dm["ru_RU"] = "0 – Гладко.\n1 – Скруглённые состыкованные.\n2 – Зазор"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').name) as dm:
            dm["ru_RU"] = "Отображение типа сокета"
            dm["zh_CN"] = "显示端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').description) as dm:
            dm["ru_RU"] = "0 – Выключено.\n1 – Сверху.\n-1 – Снизу (VMT)"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').name) as dm:
            dm["ru_RU"] = "Отображение цвета сокета"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').description) as dm:
            dm["ru_RU"] = "Знак – сторона цвета. Значение – ширина цвета"
#            dm["zh_CN"] = ""