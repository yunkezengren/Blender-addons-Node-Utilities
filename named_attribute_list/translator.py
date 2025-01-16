import bpy

dictionary = {
    "DEFAULT": {},
    "en_US": {
        "点": "Point",
        "边": "Edge",
        "面": "Face",
        "面拐": "Corner",
        "样条线": "Curve",
        "实例": "Instance",
        "层": "Layer",
        "UV": "UV",
        "顶点组": "Vertex Group",
        "UV贴图": "UV Map",
        "属性": "Attribute",
        "不确定": "Unknown",
        "颜色属性": "Color Attribute",
        "物体属性": "Object Attribute",
        "菜单快捷键: ": "Menu Shortcut: ",
        "面板快捷键: ": "Panel Shortcut: ",
        "命名属性菜单快捷键: ": "Named Attribute Menu Shortcut: ",
        "命名属性面板快捷键: ": "Named Attribute Panel Shortcut: ",

        "添加活动存储属性节点对应属性节点: ": "Add Corresponding Attribute Nodes for Selected Active Stored Attribute Node: ",
        "快速添加选中的活动存储属性节点相应的已命名属性节点: ": "Quickly Add Corresponding Named Attribute Node for Selected Active Stored Attribute Nodes: ",
        "已知限制: ": "Known Limitations: ",
        "非网格域存储属性节点,名称接口由别的接口连接的话,可能识别不到": "For non-mesh domain attribute nodes, if the name socket is connected by other socket, it may not be recognized.",
        "存储属性节点后经过了实例化或实现实例,在着色器添加属性,选项不一定正确": "After store attribute node, instanced or realizing instances, adding attributes in the shader may not necessarily result in correct options.",
        "对于存了多次的属性,查找节点目前只能定位到其中之一": "For attributes stored multiple times, find node currently can only locate one of them.",
        "隐藏节点选项": "Hide Node Options",
        "隐藏存在接口": "Hide Existing Socket",
        "隐藏名称接口": "Hide Name Socket",
        "重命名属性接口": "Rename Attribute Socket",
        "折叠节点": "Collapse Nodes",
        "重命名节点标签": "Rename Node Labels",
        "前缀": "Prefix",
        "重命名添加前缀: ": "If Rename Add Prefix: ",
        "隐藏前缀": "Hide Prefix",
        "列表排序方式": "List Sorting Method",
        "属性列表里是否显示": "Show in Attribute List",
        "属性列表里是否隐藏": "Hide in Attribute List",
        "未使用属性": "Unused Attributes",
        "节点组内属性": "Attributes in Node Groups",
        "属性列表文本设置": "Attribute List Text Settings",
        "显示所在域": "Show Domain",
        "查找节点设置": "Node Search Settings",
        "适当缩放视图": "Zoom View Appropriately",
        "添加节点选项": "Add Node Options",
        "列表显示选项": "List Display Options",
        "添加已命名属性节点": "Add Named Attribute Node",
        "添加属性节点": "Add Attribute Node",
        "框选节点": "Box Select Nodes",
        "类型: ": "Type: ",
        "属性所在域: ": "Attribute Domain: ",
        "所在节点组: ": "in which groups: ",
        "属性隐藏选项": "Attribute Hiding Options",
        "命名属性列表菜单": "Named Attribute List Menu",
        "命名属性列表面板": "Named Attribute List Panel",
        "几何节点命名属性列表": "Geometry Nodes Named Attribute List",
        "快速添加命名属性节点": "Quickly Add Named Attribute Node",
        "小王-命名属性列表菜单": "Named Attribute List Menu",
        "小王-命名属性列表面板": "Named Attribute List Panel",
        "小王-几何节点命名属性列表": "Geometry Nodes Named Attribute List",
        "小王-快速添加命名属性节点": "Quickly Add Named Attribute Node",
        "该属性所在域,例：面 | 实例": "The domain of this attribute, e.g., Face | Instance",
        "该属性是否转到了实例域上": "Whether this attribute has been moved to the Instance domain",
        "存储属性节点目标": "Store Attribute Node Target",
        "活动物体属性": "Active Object Attributes",
        "活动物体及节点树属性": "Active Object and Node Tree Attributes",
        "目标退到顶层": "Target Move to Top Level",
        "添加时是否隐藏选项": "Hide Options When Adding",
        "添加时是否隐藏输出接口存在": "Hide Output Sockets When Adding",
        "添加时是否隐藏输入接口名称": "Hide Input Socket Names When Adding",
        "添加时是否命名输出接口属性": "Name Output Sockets When Adding",
        "添加时是否折叠节点": "Collapse Nodes When Adding",
        "添加时是否重命名节点为属性名": "Rename Nodes to Attribute Names When Adding",
        "重命名节点时添加的前缀": "Prefix to Add When Renaming Nodes",
        "隐藏带有特定前缀的属性,以|分隔多种,例 .|-|_": "Hide Attributes with Specific Prefixes, separated by |, e.g., .|-|_",
        "是否隐藏带有特定前缀的属性": "Hide Attributes with Specific Prefixes",
        "显示设置": "Display Settings",
        "查找节点时适当缩放视图": "Zoom View Appropriately When Finding for Nodes",
        "只显示用到的属性,连了线的属性节点": "Only Show Used Attributes, Connected Attribute Nodes",
        "隐藏节点组里的属性": "Hide Attributes in Node Groups",
        "是否显示属性所在域": "Show Attribute Domain",
        "显示在n面板上的插件当前状态描述": "Plugin Description Shown in N-Panel",
        "是否在属性列表里显示顶点组": "Show Vertex Groups in Attribute List",
        "是否在属性列表里显示UV贴图": "Show UV Maps in Attribute List",
        "是否在属性列表里显示颜色属性": "Show Color Attributes in Attribute List",
        "属性列表多种排序方式": "Multiple Sorting Methods for Attribute List",
        "按类型排序1": "Sort by Type 1",
        "布尔-浮点-整数-矢量-颜色-旋转-矩阵": "Boolean-Float-Integer-Vector-Color-Rotation-Matrix",
        "按类型排序1-反转": "Sort by Type 1 - Reversed",
        "矩阵-旋转-颜色-矢量-整数-浮点-布尔": "Matrix-Rotation-Color-Vector-Integer-Float-Boolean",
        "按类型排序2": "Sort by Type 2",
        "整数-布尔-浮点-矢量-颜色-旋转-矩阵": "Integer-Boolean-Float-Vector-Color-Rotation-Matrix",
        "完全按字符串排序": "Sort Completely by String",
        "首字-数字英文中文": "First Character - Numbers English Chinese",
        "查找命名属性节点": "Find Stored Named Attribute Node",
        "跳转到已命名属性节点位置": "Find Stored Named Attribute Node",
    },
}


def i18n(text: str) -> str:
    view = bpy.context.preferences.view
    language = view.language
    trans_interface = view.use_translate_interface

    if language in ["zh_CN", "zh_HANS"] and trans_interface:
        return text
    else:
        if text in dictionary["en_US"]:
            return dictionary["en_US"][text]
        else:
            return text
