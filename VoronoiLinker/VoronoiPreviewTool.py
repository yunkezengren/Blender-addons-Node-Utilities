


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
                                        DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Col4(GetSkColSafeTup4(ftg.tar)))
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
            dm["zh_CN"] = "只预览已有连接的输出端口"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').name) as dm:
            dm["ru_RU"] = "Равный тип якоря"
#            dm["zh_CN"] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').description) as dm:
            dm["ru_RU"] = "Цепляться только к сокетам типа якоря"
            dm["zh_CN"] = "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的端口类型一样才能被预览连接"
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
            dm["zh_CN"] = "快速预览时高亮显示连接到预览的节点的上级节点的输出端口"
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