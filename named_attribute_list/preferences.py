from bpy.types import AddonPreferences
from bpy.props import StringProperty, EnumProperty, BoolProperty

from .utils import pref, find_user_keyconfig
from .translator import i18n as tr

class ATTRLIST_AddonPrefs(AddonPreferences):
    bl_idname = __package__
    hide_option        : BoolProperty(description=tr('添加时是否隐藏选项'),           default=True)
    hide_Exists_socket : BoolProperty(description=tr('添加时是否隐藏输出存在接口'),   default=True)
    hide_Name_socket   : BoolProperty(description=tr('添加时是否隐藏输入名称接口'),   default=False)
    rename_Attr_socket : BoolProperty(description=tr('添加时是否重命名输出属性接口'), default=False)
    hide_Node          : BoolProperty(description=tr('添加时是否折叠节点'),           default=False)
    rename_Node        : BoolProperty(description=tr('添加时是否重命名节点为属性名'), default=False)
    hide_Store_Node    : BoolProperty(description=tr('添加时是否折叠节点'),           default=False)
    hide_Store_option  : BoolProperty(description=tr('添加时是否隐藏选项'),           default=False)
    hide_Select_socket : BoolProperty(description=tr('添加时是否隐藏输入名称接口'),   default=True)
    rename_Store_Node  : BoolProperty(description=tr('添加时是否重命名节点为属性名'), default=False)
    hide_by_prefix     : BoolProperty(description=tr('是否隐藏带有特定前缀的属性'),   default=False)
    show_set_panel     : BoolProperty(description=tr('显示设置'),                     default=True)
    if_scale_editor    : BoolProperty(description=tr('查找节点时适当缩放视图'),       default=True)
    hide_vertex_group  : BoolProperty(description=tr('是否在属性列表里隐藏顶点组'),   default=False)
    hide_uv_map        : BoolProperty(description=tr('是否在属性列表里隐藏UV贴图'),   default=False)
    hide_color_attr    : BoolProperty(description=tr('是否在属性列表里隐藏颜色属性'), default=False)
    hide_unused_attr   : BoolProperty(description=tr('todo-隐藏没连到组输出的存储属性节点的属性'), default=False)
    hide_attr_in_group : BoolProperty(description=tr('隐藏节点组里的属性'), default=False)
    hide_extra_attr    : BoolProperty(description=tr('隐藏额外的属性:\n--属性编辑器-数据-属性\n--物体/集合信息节点带的(和别的几何数据合并几何才显示顶点组)\n--存储属性节点名称接口连了线的\n--活动修改器之上的GN修改器的属性'), default=False)
    hide_by_group      : BoolProperty(description=tr('细化隐藏菜单,按类别分子菜单显示: 顶点组/UV/颜色属性/额外属性/未使用/组内/前缀'), default=True)
    add_settings       : BoolProperty(name=tr('添加节点选项'),   description=tr('添加节点选项'),       default=False)
    show_settings      : BoolProperty(name=tr('列表显示选项'),   description=tr('列表显示选项'),       default=True)
    show_attr_domain   : BoolProperty(description=tr('是否显示属性所在域'), default=True)
    use_accelerator_key: BoolProperty(description=tr('使用加速键'), default=True)
    panel_info         : StringProperty(description=tr('显示在n面板上的插件当前状态描述'), default="")
    rename_prefix      : StringProperty(description=tr('重命名节点时添加的前缀'), default="")
    prefix_to_hide     : StringProperty(description=tr('隐藏带有特定前缀的属性,以|分隔多种,例 .|_|-'), default=".")
    sort_type          : EnumProperty(description=tr('属性列表多种排序方式'),
                                        items=[ ('按类型排序1',      tr('按类型排序1'),      tr('布尔-浮点-整数-矢量-颜色-旋转-矩阵'), 0, 0),
                                                ('按类型排序1-反转', tr('按类型排序1-反转'), tr('矩阵-旋转-颜色-矢量-整数-浮点-布尔'), 0, 1),
                                                ('按类型排序2',      tr('按类型排序2'),      tr('整数-布尔-浮点-矢量-颜色-旋转-矩阵'), 0, 2),
                                                ('完全按字符串排序', tr('完全按字符串排序'), tr('首字-数字英文中文'), 0, 3)])

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.5)

        split.label(text=tr('命名属性菜单快捷键: '))
        split.prop(find_user_keyconfig('命名属性菜单快捷键'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text=tr('命名属性面板快捷键: '))
        split.prop(find_user_keyconfig('命名属性面板快捷键'), 'type', text='', full_event=True)

        split = layout.split(factor=0.5)
        split.label(text=tr('添加活动存储属性节点对应属性节点: '))
        split.prop(find_user_keyconfig('添加存储节点对应属性节点'), 'type', text='', full_event=True)

        box1 = layout.box()
        box1.label(text=tr("已知限制: "), icon='INFO')
        limit1 = " "*10 + tr("非网格域存储属性节点,名称接口由别的接口连接的话,可能识别不到")
        limit2 = " "*10 + tr("存储属性节点后经过了实例化或实现实例,在着色器添加属性,选项不一定正确")
        limit3 = " "*10 + tr("对于存了多次的属性,查找节点目前只能定位到其中之一")
        box1.label(text=limit1)
        box1.label(text=limit2)
        box1.label(text=limit3)
        box1.label(text="information outdated / 描述信息过时")
