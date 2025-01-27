import bpy

dictionary = {
    "DEFAULT": {},
    "en_US": {
        "行": "Row",
        "列": "Column",
        "更改行数": "Change rows of selected nodes",
        "更改列数": "Change columns of selected nodes",
        "左对齐"   : "Align left",
        "右对齐"   : "Align right",
        "底对齐"   : "Align bottom",
        "顶对齐"   : "Align top",
        "节点对齐" : "Node align",
        "节点分布" : "Node distribute",
        "对齐高度" : "Align height",
        "对齐宽度" : "Align width",
        "拉直连线" : "Straighten links",
        "对齐方式" : "Alignment method",
        "行或列数" : "Number of rows or columns",
        "x方向间隔": "X direction spacing",
        "y方向间隔": "Y direction spacing",
        "改变行列数"  : "Change rows or columns",
        "垂直等距分布": "Distribute vertical",
        "水平等距分布": "Distribute horizontal",
        "水平垂直等距": "Distribute horizontal vertical",
        "等距对齐高度": "Evenly align height",
        "相对网格分布": "Relative grid distribute",
        "等距对齐宽度": "Evenly align width",
        "绝对网格分布": "Absolute grid distribute",
        "对齐节点高度": "Align node height",
        "等距对齐高度": "Evenly align height",
        "等距对齐宽度": "Evenly align width",
        "对齐节点宽度": "Align node width",
        "自定义分布间距": "Custom space",
        "对齐节点到顶部": "Align nodes to the top",
        "对齐节点到底部": "Align nodes to the bottom",
        "普通对齐饼菜单": "Basic align pie menu",
        "高级对齐饼菜单": "Pro align pie menu",
        "对齐-拉直连线"    : "Align - Straighten links",
        "对齐-改变行列数"  : "Align - Change the number of rows or columns",
        "对齐节点到最左侧" : "Align nodes to the left",
        "对齐节点到最右侧" : "Align nodes to the right",
        "对齐-水平等距分布": "Align - Distribute horizontally with evenly distribute",
        "对齐-垂直等距分布": "Align - Distribute vertically with evenly distribute",
        "对齐-水平垂直等距": "Align - Equal spacing in both horizontal and vertical directions",
        "对齐-相对网格分布": "Align - Relative grid distribute",
        "对齐-绝对网格分布": "Align - Absolute grid distribute",
        "水平+垂直等距分布": "Equal distribute in both horizontal and vertical directions",
        "对齐选中节点到顶部"   : "Align selected nodes to the top",
        "对齐选中节点到底部"   : "Align selected nodes to the bottom",
        "对齐节选中点到最左侧" : "Align selected nodes to the left",
        "对齐节选中点到最右侧" : "Align selected nodes to the right",
        "对齐高度+垂直等距分布": "Align height + Distribute vertically evenly",
        "对齐宽度+水平等距分布": "Align width + Distribute horizontally evenly",
        "x方向两个节点之间间隔": "Spacing between two nodes in the X direction",
        "y方向两个节点之间间隔": "Spacing between two nodes in the Y direction",
        "水平方向节点之间间距一致": "Same space between nodes in the horizontal direction",
        "垂直方向节点之间间距一致": "Same space between nodes in the vertical direction",
        "把选中节点改成多少行或列": "Change the selected nodes to a specified number of rows or columns",
        "等距及栅格分布启用自定义间距"      : "Enable custom spacing for evenly and grid distribute",
        "等距及栅格分布时的节点x方向间距"   : "Node spacing in the X direction for evenly and grid distribute",
        "等距及栅格分布时的节点y方向间距"   : "Node spacing in the Y direction for evenly and grid distribute",
        "栅格分布时判断是否在一列的宽度"    : "Determine if nodes are within the width of a column during grid distribute",
        "栅格分布时判断是否在一列的宽度"    : "Determine if nodes are within the width of a column during grid distribute",
        "等距及栅格分布时的节点x方向间距"   : "Node spacing in the X direction for evenly and grid distribute",
        "等距及栅格分布时的节点y方向间距"   : "Node spacing in the Y direction for evenly and grid distribute",
        "需要选中活动节点和要对齐的节点"    : "You need to select the active node and the nodes to align",
        "例:20行20列节点,改成10列就是40行"  : "Example: 20 rows and 20 columns of nodes, changing to 10 columns results in 40 rows",
        "对齐选中节点的高度中心,即居中分布" : "Align the height center of selected nodes, i.e., center distribute",
        "对齐选中节点的宽度中心,即居中分布" : "Align the width center of selected nodes, i.e., center distribute",
        "是否为等距及栅格分布启用自定义间距": "Enable custom spacing for evenly and grid distribute",
        "列模式:count=0是1行;行模式:列模式:count=0是1列"      : "Column mode: count=0 means 1 row; Row mode: count=0 means 1 column",
        "选中节点,以活动节点为中心,拉直输入输出接口之间的连线": "Select nodes, use the active node as the center, and straighten the links between input and output sockets",
        "每一列先垂直等距分布,各列之间水平等距分布,每列对齐宽度居中对齐": "First, distribute each column vertically evenly, then distribute columns horizontally evenly, and center-align the width of each column",
        "每一列先垂直等距分布,各列之间水平等距分布,每列对齐宽度居中对齐,每列最大最小高度一样": "First, distribute each column vertically evenly, then distribute columns horizontally evenly, center-align the width of each column, and ensure each column has the same maximum and minimum height",
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

