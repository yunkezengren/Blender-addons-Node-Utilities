from .common_class import VmtData
from .common_func import DisplayMessage
from .VoronoiTool import VoronoiToolPairSk
from .关于颜色的函数 import power_color4, get_sk_color_safe
from .关于翻译的函数 import GetAnnotFromCls, VlTrMapForKey


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




viaverSkfMethod = -1 # 用于成功交互方法的切换开关. 本可以按版本分布到映射表中, 但"根据实际情况"尝试有其独特的美学魅力.

# 注意: ViaVer'ы 尚未更新.
def ViaVerNewSkf(tree, isSide, ess, name):
    if gt_blender4: # Todo1VV: 重新思考拓扑结构; 使用全局函数和方法, 以及一个指向成功方法的全局变量, 实现"完全锁定".
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
    if gt_blender4:
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
    if gt_blender4:
        tree.interface.remove(name)
    else:
        (tree.outputs if isSide else tree.inputs).remove(name)



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
            dm["zh_CN"] = "从一个接口连接"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPlaceImmediately').name) as dm:
            dm["ru_RU"] = "Размещать моментально"
            dm["zh_CN"] = "立即添加节点到鼠标位置"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmtReroutesCanInAnyType').name) as dm:
            dm["ru_RU"] = "Рероуты могут смешиваться с любым типом"
            dm["zh_CN"] = "快速混合不限定接口类型"
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
            # dm["zh_CN"] = "元素对齐方式"?
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').description) as dm:
            dm["ru_RU"] = "0 – Гладко.\n1 – Скруглённые состыкованные.\n2 – Зазор"
            # dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').name) as dm:
            dm["ru_RU"] = "Отображение типа сокета"
            dm["zh_CN"] = "显示接口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').description) as dm:
            dm["ru_RU"] = "0 – Выключено.\n1 – Сверху.\n-1 – Снизу (VMT)"
            # dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').name) as dm:
            dm["ru_RU"] = "Отображение цвета сокета"
            # dm["zh_CN"] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').description) as dm:
            dm["ru_RU"] = "Знак – сторона цвета. Значение – ширина цвета"
            # dm["zh_CN"] = ""


