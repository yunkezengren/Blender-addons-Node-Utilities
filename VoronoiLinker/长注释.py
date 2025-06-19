# 或许某天应该在工具属性里添加一个按键, 用来在工具运行时修改其行为, 比如 VQDT 的 Alt+D 操作中的 Alt 选项. 现在对 VWT 来说这个功能更重要了.
# 在注释中, "редактор типа"(编辑器类型) 和 "тип дерева"(节点树类型) 是同义词; 指的是4种经典的内置编辑器, 也就是那几种节点树类型.

# 对于某些工具, 存在一些彼此相同的常量, 但它们有自己的前缀; 这样做是为了方便, 以免"借用"其他工具的常量.

# VL 当前需要但(可能)只能通过非公开API实现的需求:
# 1. GeoViewer 是否处于活动状态 (通过标题判断) 和/或当前是否正在积极预览? (在底层判断, 而不是从电子表格读取)
# 2. 在编辑器上下文中, 明确判断用户是通过哪个上层节点进入当前节点组的.
# 3. 如何区分通用的类枚举(enum)和特定于某个节点的独有枚举?
# 4. 更改几何节点 Viewer 预览的字段类型.
# 5. 插槽(socket)布局的高度 (自从我添加了 Draw Socket Area 后, 我早就后悔了, 只有美学价值能让它免于被删除).
# 6. 通过API新创建的接口现在必须遍历所有现有的节点树, 寻找它的"实例"来设置 `default_value`, 模拟传统的非API方式.
# 7. 完全访问接口面板及其所有功能. 参见 |4|.

# 插件在其他插件节点树中的(理论)用处表 (默认--有用):
# VLT, VRT, VST, VHT, VMLT, VEST, VLRT, VLTT, VWT, VRNT
# VPT, VPAT    部分有用
# VMT, VQMT, VQDT, VLNST    没用
# VICT   绝对没用!


# 本插件代码中的命名约定:
# sk -- 插槽(socket)
# skf -- 插槽接口(socket-interface)
# skin -- 输入插槽 (ski)
# skout -- 输出插槽 (sko)
# skfin -- 输入插槽接口
# skfout -- 输出插槽接口
# skfa -- 节点树的接口集合 (tree.interface.items_tree), 包括 simrep
# skft -- 节点树的接口基础 (tree.interface)
# nd -- 节点(node)
# rr -- 重路由节点(reroute)
##
# blid -- bl_idname
# blab -- bl_label
# dnf -- identifier
##
# 未使用的变量名前加 "_下划线".








