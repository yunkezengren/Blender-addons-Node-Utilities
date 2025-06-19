
#Заметка: У DoLinkHh теперь слишком много других зависимостей, просто так его выдернуть уже будет сложнее.
#P.s. "HH" -- типа "High Level", но я с буквой промахнулся D:

def DoLinkHh(sko, ski, *, isReroutesToAnyType=True, isCanBetweenField=True, isCanFieldToShader=True): 
    #Какое неожиданное визуальное совпадение с порядковым номером "sk0" и "sk1".
    #Коль мы теперь высокоуровневые, придётся суетиться с особыми ситуациями:
    if not(sko and ski): #Они должны быть.
        raise Exception("One of the sockets is none")
    if sko.id_data!=ski.id_data: #Они должны быть в одном мире.
        raise Exception("Socket trees vary")
    if not(sko.is_output^ski.is_output): #Они должны быть разного гендера.
        raise Exception("Sockets `is_output` is same")
    if not sko.is_output: #Выход должен быть первым.
        sko, ski = ski, sko
    #Заметка: "высокоуровневый", но не для глупых юзеров; соединяться между виртуальными можно, чорт побери.
    tree = sko.id_data
    if tree.bl_idname=='NodeTreeUndefined': #Дерево не должно быть потерянным.
        return #В потерянном дереве линки вручную создаются, а через api нет; так что выходим.
    if sko.node==ski.node: #Для одного и того же нода всё очевидно бессмысленно, пусть и возможно. Более актуально для интерфейсов.
        return
    isSkoField = sko.type in set_utilTypeSkFields
    isSkoNdReroute = sko.node.type=='REROUTE'
    isSkiNdReroute = ski.node.type=='REROUTE'
    isSkoVirtual = (sko.bl_idname=='NodeSocketVirtual')and(not isSkoNdReroute) #Виртуальный актуален только для интерфейсов, нужно исключить "рероута-самозванца".
    isSkiVirtual = (ski.bl_idname=='NodeSocketVirtual')and(not isSkiNdReroute) #Заметка: У виртуального и у аддонских сокетов sk.type=='CUSTOM'.
    #Можно, если
    if not( (isReroutesToAnyType)and( (isSkoNdReroute)or(isSkiNdReroute) ) ): #Хотя бы один из них рероут.
        if not( (sko.bl_idname==ski.bl_idname)or( (isCanBetweenField)and(isSkoField)and(ski.type in set_utilTypeSkFields) ) ): #Одинаковый по блидам или между полями.
            if not( (isCanFieldToShader)and(isSkoField)and(ski.type=='SHADER') ): #Поле в шейдер.
                if not(isSkoVirtual or isSkiVirtual): #Кто-то из них виртуальный (для интерфейсов).
                    if (not IsClassicTreeBlid(tree.bl_idname))or( IsClassicSk(sko)==IsClassicSk(ski) ): #Аддонский сокет в классических деревьях; см. VLT.
                        return None #Низя между текущими типами.
    #Отсеивание некорректных завершено. Теперь интерфейсы:
    ndo = sko.node
    ndi = ski.node
    isProcSkfs = True
    #Для суеты с интерфейсами требуется только один виртуальный. Если их нет, то обычное соединение.
    #Но если они оба виртуальные, читать информацию не от кого; от чего суета с интерфейсами бесполезна.
    if not(isSkoVirtual^isSkiVirtual): #Два условия упакованы в один xor.
        isProcSkfs = False
    elif ndo.type==ndi.type=='REROUTE': #Между рероутами гарантированно связь. Этакий мини-островок безопасности, затишье перед бурей.
        isProcSkfs = False
    elif not( (ndo.bl_idname in set_utilEquestrianPortalBlids)or(ndi.bl_idname in set_utilEquestrianPortalBlids) ): #Хотя бы один из нодов должен быть всадником.
        isProcSkfs = False
    if isProcSkfs: #Что ж, буря оказалось не такой уж и бурей. Я ожидал больший спагетти-код. Как всё легко и ясно получается, если мозги-то включить.
        #Получить нод всадника виртуального сокета
        ndEq = ndo if isSkoVirtual else ndi #Исходим из того, что всадник вывода равновероятен со своим компаньоном.
        #Коллапсируем компаньнов
        ndEq = getattr(ndEq,'paired_output', ndEq)
        #Интересно, где-нибудь в параллельной вселенной существуют виртуальные мультиинпуты?.
        skTar = sko if isSkiVirtual else ski
        match ndEq.bl_idname:
            case 'NodeGroupInput':  typeEq = 0
            case 'NodeGroupOutput': typeEq = 1
            case 'GeometryNodeSimulationOutput': typeEq = 2
            case 'GeometryNodeRepeatOutput':     typeEq = 3
            # 小王-新建接口
            case 'GeometryNodeMenuSwitch':       typeEq = 4
            case 'GeometryNodeBake':             typeEq = 5
            case 'GeometryNodeCaptureAttribute': typeEq = 6
            case 'GeometryNodeIndexSwitch':      typeEq = 7
        #Неподдерживаемых всадником типы не обрабатывать:
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
        #Создать интерфейс
        match typeEq:
            case 0|1:
                equr = Equestrian(ski if isSkiVirtual else sko)
                skf = equr.NewSkfFromSk(skTar)
                skNew = equr.GetSkFromSkf(skf, isOut=skf.in_out!='OUTPUT') #* звуки страданий *
            case 2|3:       # [-2]  -1是扩展接口,-2是新添加的接口
                _skf = (ndEq.state_items if typeEq==2 else ndEq.repeat_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
                if True: #Перевыбор для SimRep'а тривиален; ибо у них нет панелей, и все новые сокеты появляются снизу.
                    skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
                else:
                    skNew = Equestrian(ski if isSkiVirtual else sko).GetSkFromSkf(_skf, isOut=isSkoVirtual)
            case 4:       # 小王-新建接口-菜单切换
                _skf = ndEq.enum_items.new(GetSkLabelName(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 5|6:       # 小王-新建接口-捕捉属性 烘焙
                _skf = (ndEq.bake_items if typeEq==5 else ndEq.capture_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
                skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
            case 7:         # 小王-新建接口-编号切换
                nodes = ski.node.id_data.nodes  # id_data是group/tree
                skNew = index_switch_add_input(nodes, ski.node)

        #Перевыбрать новый появившийся сокет
        if isSkiVirtual:
            ski = skNew
        else:
            sko = skNew
    #Путешествие успешно выполнено. Наконец-то переходим к самому главному:
    def DoLinkLL(tree, sko, ski):
        return tree.links.new(sko, ski) #hi.
    return DoLinkLL(tree, sko, ski)
    #Заметка: С версии b3.5 виртуальные инпуты теперь могут принимать в себя прям как мультиинпуты.
    # Они даже могут между собой по нескольку раз соединяться, офигеть. Разрабы "отпустили", так сказать, в свободное плаванье.

def DoMix(tree, isShift, isAlt, type):
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=type, use_transform=not VmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    aNd.width = 140
    txtFix = {'VALUE':'FLOAT'}.get(VmtData.skType, VmtData.skType)
    #Дважды switch case -- для комфортного кода и немножко экономии.
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
            #Для микса и переключателя искать с конца, потому что их сокеты для переключения имеют тип некоторых искомых. У нода сравнения всё наоборот.
            list_foundSk = [sk for sk in ( reversed(aNd.inputs) if tgl else aNd.inputs ) if sk.type==txtFix]
            NewLinkHhAndRemember(VmtData.sk0, list_foundSk[tgl^isShift]) #Из-за направления поиска, нужно выбирать их из списка также с учётом направления.
            if VmtData.sk1:
                NewLinkHhAndRemember(VmtData.sk1, list_foundSk[(not tgl)^isShift])
        case _:
            #Такая плотная суета ради мультиинпута -- для него нужно изменить порядок подключения.
            Mix_item = dict_vmtMixerNodesDefs[aNd.bl_idname]
            swap_link = 0       # sk0是矩阵,sk1是矢量,不交换(这是默认情况)
            if VmtData.sk1 and VmtData.sk1.type == "MATRIX" and VmtData.sk0.type != "MATRIX":
                swap_link = 1
            soc_in = aNd.inputs[Mix_item[1^isShift^swap_link]]
            is_multi_in = aNd.inputs[Mix_item[0]].is_multi_input
            if (VmtData.sk1)and(is_multi_in): #`0` здесь в основном из-за того, что в dict_vmtMixerNodesDefs у "нодов-мультиинпутов" всё по нулям.
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
            DoLinkHh( VmtData.sk0, aNd.inputs[Mix_item[0^isShift]^swap_link] ) #Заметка: Это не NewLinkHhAndRemember(), чтобы визуальный второй мультиинпута был последним в VlrtData.
            if (VmtData.sk1)and(not is_multi_in):
                NewLinkHhAndRemember( VmtData.sk1, soc_in)
    aNd.show_options = not VmtData.isHideOptions
    #Далее так же, как и в vqmt. У него первично; здесь дублировано для интуитивного соответствия.
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
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
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
                ly = ly.split(factor=Color_Bar_Width * VmtData.uiScale, align=True)      # 小王 饼菜单颜色条宽度
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
            #Если при выполнении колонка окажется пустой, то в ней будет отображаться только пустая точка-коробка. Два списка ниже нужны, чтобы починить это.
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
                    # # 小王-混合饼菜单对比较节点的额外支持
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
