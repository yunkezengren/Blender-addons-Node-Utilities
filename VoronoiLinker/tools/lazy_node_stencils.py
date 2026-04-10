import copy
import bpy
from mathutils import Vector as Vec2
from ..base_tool import unhide_node_reassign, PairSocketTool
from ..common_class import VlnstData
from ..common_func import sk_label_or_name
from ..globals import sk_type_idname_map
from ..utils.drawing import DrawVlWidePoint, TemplateDrawSksToolHh
from ..utils.node import MinFromFtgs, opt_tar_socket, sk_type_to_idname
from ..utils.ui import LyAddNiceColorProp, draw_hand_split_prop

# 突然发现, 我以前对"懒人延续"工具的想法被封装在了这个工具里. 真是出乎意料.
# 这个工具, 和 ^ (其中插槽和节点明确决定了下一个节点) 一样, 只不过是针对两个插槽的; 而且可能性更多!

lzAny = '!any'
class LazyKey():
    def __init__(self, fnb, fst, fsn, fsg, snb=lzAny, sst=lzAny, ssn=lzAny, ssg=lzAny):
        self.firstNdBlid = fnb
        self.firstSkBlid = sk_type_idname_map.get(fst, fst)
        self.firstSkName = fsn
        self.firstSkGend = fsg
        self.secondNdBlid = snb
        self.secondSkBlid = sk_type_idname_map.get(sst, sst)
        self.secondSkName = ssn
        self.secondSkGend = ssg
class LazyNode():
    # 黑魔法警告! 🧙‍ 如果在 __init__ 中使用 list_props=[] 作为默认参数, 那么在一个实例上使用 nd.list_props += [..] 会修改所有实例的 lzSt. 这简直是黑魔法; 保证让你做噩梦.
    def __init__(self, blid, list_props, ofsPos=(0,0), hhoSk=0, hhiSk=0):
        self.blid = blid
        # list_props 也包含对插槽的处理.
        # 指向插槽 (在 list_props 和 lzHh_Sk 中) -- 索引+1, 符号表示方向; => 0 不使用.
        self.list_props = list_props
        self.lzHhOutSk = hhoSk
        self.lzHhInSk = hhiSk
        self.locloc = Vec2(ofsPos) # "Local location"; 以及离世界中心的偏移.
class LazyStencil():
    def __init__(self, key, csn=2, name="", prior=0.0):
        self.lzkey = key
        self.prior = prior # 越高越重要.
        self.name = name
        self.trees = {} # 这也像是密钥的一部分.
        self.isTwoSkNeeded = csn==2
        self.list_nodes = []
        self.list_links = [] # 序号节点 / 插槽, 以及同样的输入.
        self.isSameLink = False
        self.txt_exec = ""

list_vlnstDataPool = []

# 数据库:
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VECTOR','Normal',False), 2, "Fast Color NormalMap")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeNormalMap', [], hhiSk=-2, hhoSk=1) )
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VALUE',lzAny,False), 2, "Lazy Non-Color data to float socket")
lzSt.trees = {'ShaderNodeTree'}
lzSt.isSameLink = True
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',False), 1, "NW TexCord Parody")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexImage', [(2,'hide',True)], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,0,1,0) ]
list_vlnstDataPool.append(lzSt)
lzSt = copy.deepcopy(lzSt)
lzSt.lzkey.firstSkName = "Base Color"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'VECTOR','Vector',False), 1, "NW TexCord Parody Half")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], hhoSk=-1, ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0) ]
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA',lzAny,True, lzAny,'SHADER',lzAny,False), 2, "Insert Emission")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeEmission', [], hhiSk=-1, hhoSk=1) )
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey('ShaderNodeBackground','RGBA','Color',False), 1, "World env texture", prior=1.0)
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexEnvironment', [], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeTexCoord', [('show_options',False)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,3,1,0) ]
list_vlnstDataPool.append(lzSt)
##

list_vlnstDataPool.sort(key=lambda a:a.prior, reverse=True)

def DoLazyStencil(tree, skFirst, skSecond, lzSten):
    list_result = []
    firstCenter = None
    for li in lzSten.list_nodes:
        nd = tree.nodes.new(li.blid)
        nd.location += li.locloc
        list_result.append(nd)
        for pr in li.list_props:
            if len(pr)==2:
                setattr(nd, pr[0], pr[1])
            else:
                setattr( (nd.outputs if pr[0]>0 else nd.inputs)[abs(pr[0])-1], pr[1], pr[2] )
        if li.lzHhOutSk:
            tree.links.new(nd.outputs[abs(li.lzHhOutSk)-1], skFirst if li.lzHhOutSk<0 else skSecond)
        if li.lzHhInSk:
            tree.links.new(skFirst if li.lzHhInSk<0 else skSecond, nd.inputs[abs(li.lzHhInSk)-1])
    # 对于单个节点还行, 但考虑到多样性和灵活性, 最好还是不用 remember_add_link(), 直接原生连接.
    for li in lzSten.list_links:
        tree.links.new(list_result[li[0]].outputs[li[1]], list_result[li[2]].inputs[li[3]])
    if lzSten.isSameLink:
        tree.links.new(skFirst, skSecond)
    return list_result
def LzCompare(a, b):
    return (a==b)or(a==lzAny)
def LzNodeDoubleCheck(zk, a, b): 
    return LzCompare(zk.firstNdBlid, a.bl_idname if a else "")          and LzCompare(zk.secondNdBlid, b.bl_idname if b else "")
def LzTypeDoubleCheck(zk, a, b): 
    return LzCompare(zk.firstSkBlid, sk_type_to_idname(a) if a else "") and LzCompare(zk.secondSkBlid, sk_type_to_idname(b) if b else "") # 不是'type', 而是blid's; 用于插件节点树.
def LzNameDoubleCheck(zk, a, b): 
    return LzCompare(zk.firstSkName, sk_label_or_name(a) if a else "")  and LzCompare(zk.secondSkName, sk_label_or_name(b) if b else "")
def LzGendDoubleCheck(zk, a, b): 
    return LzCompare(zk.firstSkGend, a.is_output if a else "")          and LzCompare(zk.secondSkGend, b.is_output if b else "")
def LzLazyStencil(prefs, tree, skFirst, skSecond):
    if not skFirst:
        return []
    ndOut = skFirst.node
    ndIn = skSecond.node if skSecond else None
    for li in list_vlnstDataPool:
        if (li.isTwoSkNeeded)^(not skSecond): # 对于单插槽情况必须没有第二个, 对于双插槽情况必须有.
            if (not li.trees)or(tree.bl_idname in li.trees): # 必须支持节点树类型.
                zk = li.lzkey
                if LzNodeDoubleCheck(zk, ndOut, ndIn): # 节点匹配.
                    for cyc in (False, True):
                        skF = skFirst
                        skS = skSecond
                        if cyc: # 两个输出和两个输入, 但不同的性别顺序可能不同. 但交换对 txt_exec 的内容有影响.
                            skF, skS = skSecond, skFirst
                        if LzTypeDoubleCheck(zk, skF, skS): # 插槽的Blid匹配.
                            if LzNameDoubleCheck(zk, skF, skS): # 插槽的名称/标签匹配.
                                if LzGendDoubleCheck(zk, skF, skS): # 性别匹配.
                                    result = DoLazyStencil(tree, skF, skS, li)
                                    if li.txt_exec:
                                        try:
                                            exec(li.txt_exec) # 警报!1, 哦不.. 别慌, 这是内部的. 一切仍然安全.
                                        except Exception as ex:
                                            VlnstData.lastLastExecError = str(ex)
                                            prefs.vlnstLastExecError = VlnstData.lastLastExecError
                                    return result
def VlnstLazyTemplate(prefs, tree, skFirst, skSecond, cursorLoc):
    list_nodes = LzLazyStencil(prefs, tree, skFirst, skSecond)
    if list_nodes:
        bpy.ops.node.select_all(action='DESELECT')
        firstOffset = cursorLoc-list_nodes[0].location
        for nd in list_nodes:
            nd.select = True
            nd.location += firstOffset
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')

class NODE_OT_voronoi_lazy_node_stencils(PairSocketTool):  # 第一个应外部请求而非个人意愿创建的工具.
    bl_idname = 'node.voronoi_lazy_node_stencils'
    bl_label = "Voronoi Lazy Node Stencils"  # 每个工具三个字母, 真是够了.
    bl_description = "Power. Three letters for a tool, we've come to this... Encapsulates Ctrl-T from\nNodeWrangler, and the never-implemented 'VoronoiLazyNodeContinuationTool'."
    def callback_draw_tool(self, drata):
        # 注意: 对于不同的性别, 文本侧与套接字性别的对应关系不明显. 大概要接受了.
        TemplateDrawSksToolHh(drata, self.target_sk0, self.target_sk1, tool_name="Lazy Node Stencils")
        if ( (not not self.target_sk0)^(not not self.target_sk1) )and(drata.dsIsDrawPoint):
            DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) # 为了美观.
    def find_targets_tool(self, isFirstActivation, prefs, tree):
        def FindAnySk():
            tar_sk_out, tar_sk_in = None, None
            for ftg in tar_sks_out:
                tar_sk_out = ftg
                break
            for ftg in tar_sks_in:
                tar_sk_in = ftg
                break
            return MinFromFtgs(tar_sk_out, tar_sk_in)
        self.target_sk1 = None
        # 由于其目的, 这个工具保证会获取第一个遇到的套接字.
        for tar_nd in self.get_nearest_nodes(cur_x_off=0):
            nd = tar_nd.tar
            tar_sks_in, tar_sks_out = self.get_nearest_sockets(nd, cur_x_off=0)
            if isFirstActivation:
                self.target_sk0 = FindAnySk()
                unhide_node_reassign(nd, self, cond=self.target_sk0, flag=True)
            skFirst = opt_tar_socket(self.target_sk0)
            if skFirst:
                self.target_sk1 = FindAnySk()
                if self.target_sk1:
                    if skFirst==self.target_sk1.tar:
                        self.target_sk1 = None
                    unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
            break
    def can_run(self):
        return not not self.target_sk0
    def run(self, event, prefs, tree):
        VlnstLazyTemplate(prefs, tree, opt_tar_socket(self.target_sk0), opt_tar_socket(self.target_sk1), self.cursorLoc)
    @staticmethod
    def draw_in_pref_settings(col: bpy.types.UILayout, prefs):
        draw_hand_split_prop(col, prefs,'vlnstNonColorName')
        if prefs.vlnstLastExecError:
            draw_hand_split_prop(col, prefs,'vlnstLastExecError')
