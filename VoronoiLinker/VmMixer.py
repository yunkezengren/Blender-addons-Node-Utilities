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

def DoMix(tree, isShift, isAlt, type):
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=type, use_transform=not VmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    aNd.width = 140
    txtFix = {'VALUE':'FLOAT'}.get(VmtData.skType, VmtData.skType)
    # 两次 switch case -- 为了代码舒适和一点点节约.
    match aNd.bl_idname:
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath':
            aNd.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            aNd.operation = 'OR'
        case 'TextureNodeTexture':
            aNd.show_preview = False
        case 'GeometryNodeSwitch':
            aNd.input_type = txtFix
        case 'FunctionNodeCompare':
            aNd.data_type = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
            aNd.operation = 'EQUAL'
        case 'ShaderNodeMix':
            aNd.data_type = {'INT':'FLOAT', 'BOOLEAN':'FLOAT'}.get(txtFix, txtFix)
    match aNd.bl_idname:
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|2|.
            tgl = aNd.bl_idname!='FunctionNodeCompare'
            txtFix = VmtData.skType
            match aNd.bl_idname:
                case 'FunctionNodeCompare': txtFix = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
                case 'ShaderNodeMix':       txtFix = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(txtFix, txtFix)
            # 对于混合和切换器, 从末尾搜索, 因为它们的切换套接字类型与某些搜索的类型相同. 比较节点则相反.
            list_foundSk = [sk for sk in ( reversed(aNd.inputs) if tgl else aNd.inputs ) if sk.type==txtFix]
            NewLinkHhAndRemember(VmtData.sk0, list_foundSk[tgl^isShift]) # 由于搜索方向, 也需要根据方向从列表中选择它们.
            if VmtData.sk1:
                NewLinkHhAndRemember(VmtData.sk1, list_foundSk[(not tgl)^isShift])
        case _:
            # 这种密集的处理是为了多输入 -- 需要改变连接顺序.
            Mix_item = dict_vmtMixerNodesDefs[aNd.bl_idname]
            swap_link = 0       # sk0是矩阵,sk1是矢量,不交换(这是默认情况)
            if VmtData.sk1 and VmtData.sk1.type == "MATRIX" and VmtData.sk0.type != "MATRIX":
                swap_link = 1
            soc_in = aNd.inputs[Mix_item[1^isShift^swap_link]]
            is_multi_in = aNd.inputs[Mix_item[0]].is_multi_input
            if (VmtData.sk1)and(is_multi_in): # `0` 在这里主要是因为 dict_vmtMixerNodesDefs 中的“多输入节点”都是零.
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
            DoLinkHh( VmtData.sk0, aNd.inputs[Mix_item[0^isShift]^swap_link] ) # 注意: 这不是 NewLinkHhAndRemember(), 以便多输入的第二个视觉上是 VlrtData 中的最后一个.
            if (VmtData.sk1)and(not is_multi_in):
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
    aNd.show_options = not VmtData.isHideOptions
    # 接下来和 vqmt 中一样. 它的是主要的; 这里为了直观对应而复制.
    if isAlt:
        for sk in aNd.inputs:
            sk.hide = True

class VmtOpMixer(VoronoiOpTool):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = "Mixer Mixer"
    operation: bpy.props.StringProperty()
    def invoke(self, context, event):
        DoMix(context.space_data.edit_tree, event.shift, event.alt, self.operation)
        return {'FINISHED'}
class VmtPieMixer(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_mixer_pie'
    bl_label = "" # 这里的文本将显示在饼菜单的中心.
    def draw(self, context):
        def LyVmAddOp(where: UILayout, txt):
            where.operator(VmtOpMixer.bl_idname, text=TranslateIface(dict_vmtMixerNodesDefs[txt][2])).operation = txt
        def LyVmAddItem(where: UILayout, txt):
            ly = where.row(align=VmtData.pieAlignment==0)
            soldPdsc = VmtData.pieDisplaySocketColor
            if soldPdsc:
                # ly = ly.split(factor=( abs( (soldPdsc>0)- 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VmtData.uiScale, align=True)
                # print("."*50)
                # print(f"{ VmtData.uiScale = }")
                # print(f"{ soldPdsc>0 = }")
                # print(f"{ abs(soldPdsc) = }")
                # print(f"{ 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) = }")
                # print(f"{ ( abs( (soldPdsc>0)- 0.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VmtData.uiScale = }")
                # ly = ly.split(factor=0.05, align=True)
                ly = ly.split(factor=Color_Bar_Width * VmtData.uiScale, align=True)      # 饼菜单颜色条宽度
            if soldPdsc<0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
            LyVmAddOp(ly, txt)
            if soldPdsc>0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        editorBlid = context.space_data.tree_type
        tup_nodes = dict_vmtTupleMixerMain[editorBlid][VmtData.skType]
        if VmtData.isSpeedPie:
            for ti in tup_nodes:
                if ti!=vmtSep:
                    LyVmAddOp(pie, ti)
        else:
            # 如果执行时列为空, 则只显示一个空的点框. 下面两个列表是为了修复这个问题.
            list_cols = [pie.row(), pie.row(), pie.row() if VmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]
            def LyGetPieCol(inx):
                if list_done[inx]:
                    return list_cols[inx]
                box = list_cols[inx].box()
                col = box.column(align=VmtData.pieAlignment<2)
                col.ui_units_x = 6*((VmtData.pieScale-1)/2+1)
                col.scale_y = VmtData.pieScale
                list_cols[inx] = col
                list_done[inx] = True
                return col
            sk0_type = VmtData.sk0.type
            sk1_type = VmtData.sk1.type if VmtData.sk1 else None
            vec_mat_math = False    # 有矢量和矩阵输入接口的节点
            # 连接了两个接口，且一矩阵一不是矩阵
            # if VmtData.sk1 and ((sk0_type != "MATRIX" and sk1_type == "MATRIX") or (sk0_type == "MATRIX" and sk1_type != "MATRIX")):
            if VmtData.sk1 and (sk0_type == "MATRIX") != (sk1_type == "MATRIX"):
                vec_mat_math = True
            mat_mat_math = True if (sk0_type == "MATRIX" and sk1_type == "MATRIX") else False
            match editorBlid:
                case 'ShaderNodeTree':
                    row2 = LyGetPieCol(0).row(align=VmtData.pieAlignment==0)
                    row2.enabled = False
                    LyVmAddItem(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    col = LyGetPieCol(0)
                    row1 = col.row(align=VmtData.pieAlignment==0)
                    row2 = col.row(align=VmtData.pieAlignment==0)
                    row3 = col.row(align=VmtData.pieAlignment==0)
                    row1.enabled = False
                    row2.enabled = False
                    row3.enabled = False
                    LyVmAddItem(row1, 'GeometryNodeSwitch')
                    if VmtData.skType != "MATRIX":  # 暂时只是让矩阵接口的混合饼菜单不显示 混合和比较节点
                        LyVmAddItem(row2, 'ShaderNodeMix')
                        LyVmAddItem(row3, 'FunctionNodeCompare')
                    # # 混合饼菜单对比较节点的额外支持
                    # row4 = col.row(align=VmtData.pieAlignment==0)
                    # row5 = col.row(align=VmtData.pieAlignment==0)
                    # LyVmAddItem(row4, 'FunctionNodeCompare')
                    # LyVmAddItem(row5, 'FunctionNodeCompare')
            sco = 0
            for ti in tup_nodes:
                match ti:
                    case 'GeometryNodeSwitch':  row1.enabled = True
                    case 'ShaderNodeMix':       row2.enabled = True
                    case 'FunctionNodeCompare': row3.enabled = True
                    case _:
                        col = LyGetPieCol(1)
                        if ti==vmtSep:
                            if sco:
                                col.separator()
                        else:
                            if vec_mat_math and ti in ["FunctionNodeMatrixMultiply", "FunctionNodeMatrixDeterminant", "FunctionNodeInvertMatrix"]:
                                continue
                            if mat_mat_math and ti not in ["FunctionNodeMatrixMultiply"]: continue
                            LyVmAddItem(col, ti)
                            sco += 1
            if VmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=GetSkColorRaw(VmtData.sk0))
                row.label(text=VmtData.sk0.bl_label)