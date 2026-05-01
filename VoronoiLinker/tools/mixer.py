import bpy
from bpy.app.translations import pgettext_iface as _iface
from ..base_tool import unhide_node_reassign, TripleSocketTool
from ..common_class import VmtData, set_pie_data
from ..utils.ui import display_message
from ..globals import Cursor_X_Offset
from ..utils.color import get_sk_color_safe, power_color
from ..utils.drawing import draw_sockets_template
from ..utils.node import opt_tar_socket
from ..utils.ui import split_prop, draw_panel_column, split_prop
from .mixer_sub import DoMix, mixer_default, mixer_tree_sk_nodes, NODE_MT_mixer_pie

class NODE_OT_voronoi_mixer(TripleSocketTool):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    bl_description = "The canonical tool for frequent mixing needs.\nMost likely 70% will go to using \"Instance on Points\"."
    use_for_custom_tree = False
    can_draw_appearance = True
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #放在第一位, 以便在 kmi 中与 VQMT 类似.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    def callback_draw(self, drawer):
        draw_sockets_template(drawer, self.target_sk0, self.target_sk1, self.target_sk2, tool_name="Quick Mix")
    def find_targets(self, is_first_active, prefs, tree):
        if is_first_active:
            self.target_sk0 = None # 需要清空, 因为下面有两个 continue.
        if not self.can_pick_third:
            self.target_sk1 = None
        soldReroutesCanInAnyType = prefs.vmt_reroutes_can_in_any_type
        tar_sockets = self.nearest_target_sockets(only_output=True)
        # todo 逻辑有点混乱 tar_sockets 双重循环了
        for tar_sks_out in tar_sockets:
            # 节点过滤器没有必要.这个工具会触发第一个遇到的任何输出 (现在除了虚拟接口).
            nd = tar_sks_out.tar.node
            if is_first_active:
                self.target_sk0 = tar_sks_out
            unhide_node_reassign(nd, self, cond=is_first_active, flag=True)
            #对于第二个, 根据条件:
            skOut0 = opt_tar_socket(self.target_sk0)
            # todo 做一些接口类型判断,比如 一个是 geometry 剩下的也要是
            if skOut0:
                if not self.can_pick_third:
                    for tar in tar_sockets:
                        skOut1 = tar.tar
                        if skOut0 == skOut1:
                            break
                        orV = (skOut1.bl_idname == 'NodeSocketVirtual') or (skOut0.bl_idname == 'NodeSocketVirtual')
                        #现在 VMT 又可以连接到虚拟接口了
                        tgl = (skOut1.bl_idname == 'NodeSocketVirtual') ^ (skOut0.bl_idname == 'NodeSocketVirtual')
                        tgl = tgl or (self.check_between_sk_fields(skOut0, skOut1) or ((skOut1.bl_idname == skOut0.bl_idname) and (not orV)))
                        tgl = tgl or ((skOut0.node.type == 'REROUTE') or (skOut1.node.type == 'REROUTE')) and (soldReroutesCanInAnyType)
                        if tgl:
                            self.target_sk1 = tar
                            break
                    if (self.target_sk1) and (skOut0 == self.target_sk1.tar): #检查是否是自我复制.
                        self.target_sk1 = None
                    unhide_node_reassign(nd, self, cond=self.target_sk1, flag=False)
                    if self.target_sk1:
                        break
                else:
                    skOut1 = opt_tar_socket(self.target_sk1)
                    for tar in tar_sockets:
                        self.target_sk2 = tar
                        if (tar.tar == skOut0) or (tar.tar == skOut1):
                            self.target_sk2 = None
                        break
                    unhide_node_reassign(nd, self, cond=self.target_sk2, flag=False)
                    if self.target_sk2:
                        break
            #尽管节点过滤器没有必要, 并且在第一个遇到的节点上工作得很好, 但如果第一个接口没有找到, 仍然需要继续搜索.
            #因为如果第一个(最近的)节点搜索结果失败, 循环将结束, 工具将不会选择任何东西, 即使旁边有合适的.
            if self.target_sk0:  # 在使用现在不存在的 isCanReOut 时尤其明显; 如果没有这个, 结果会根据光标位置成功/不成功地选择.
                break
    def can_run(self):
        if not self.target_sk0:
            return False
        if self.isCanFromOne:
            return (self.target_sk0.idname!='NodeSocketVirtual')or(self.target_sk1)
        else:
            return self.target_sk1
    def run(self, event, prefs, tree):
        VmtData.sk0 = self.target_sk0.tar
        socket1 = opt_tar_socket(self.target_sk1)
        VmtData.sk1 = socket1
        #对虚拟接口的支持已关闭; 只从第一个读取
        VmtData.sk2 = opt_tar_socket(self.target_sk2)
        VmtData.skType = VmtData.sk0.type if VmtData.sk0.bl_idname!='NodeSocketVirtual' else socket1.type
        VmtData.isHideOptions = self.isHideOptions
        VmtData.isPlaceImmediately = self.isPlaceImmediately
        _sk = VmtData.sk0
        if socket1 and socket1.type == "MATRIX":
            VmtData.skType = "MATRIX"
            _sk = VmtData.sk1
        set_pie_data(self, VmtData, prefs, power_color(get_sk_color_safe(_sk), power=2.2))
        if not self.in_builtin_tree: #由于 use_for_custom_tree, 这是个无用的检查.
            return {'CANCELLED'} #如果操作地点不在经典编辑器中, 就直接退出. 因为经典编辑器对所有人都一样, 而插件编辑器有无数种.

        default_nodes = mixer_default.get(tree.bl_idname, None)
        tup_nodes = mixer_tree_sk_nodes.get(tree.bl_idname, False).get(VmtData.skType, default_nodes)
        if tup_nodes:
            if len(tup_nodes) == 1:  #如果只有一个选择, 就跳过它直接进行混合.
                DoMix(tree, False, False, tup_nodes[0])  #在即时激活时, 可能没有释放修饰键. 因此 DoMix() 接收的是手动设置而不是 event.
            else: #否则提供选择
                bpy.ops.wm.call_menu_pie(name=NODE_MT_mixer_pie.bl_idname)
        else: #否则接口类型未定义 (例如几何节点中的着色器).
            # ! 草
            txt_vmtNoMixingOptions = "No mixing options"
            display_message(self.bl_label, txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
    @staticmethod
    def draw_pref_settings(col, prefs):
        split_prop(col, prefs,'vmt_reroutes_can_in_any_type')
    @staticmethod
    def draw_pref_appearance(col, prefs):
        if body_col := draw_panel_column(col, "Mix Pie"):
            split_prop(body_col, prefs, 'vmt_pie_type')
            col_group = body_col.column(align=True)
            split_prop(col_group, prefs, 'vmt_pie_scale')
            split_prop(col_group, prefs, 'vmt_pie_alignment')
            split_prop(col_group, prefs, 'vmt_pie_socket_display_type')
            split_prop(col_group, prefs, 'vmt_pie_display_socket_color')
            col_group.active = getattr(prefs, 'vmt_pie_type') == 'CONTROL'
