from .my_dataclass import AttrGroup
from .translator import i18n as tr

domain_en_list = [ 'POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE',  'INSTANCE', 'LAYER' ]
domain_lower_list = ["Point", "Edge", "Face", "Corner", "Curve", "Instance", "Layer"]
domain_cn_list = [ '点',    '边',   '面',   '面拐',   '样条线', '实例',     '层'    ]
# 先从英文大写翻译成中文,再根据语言决定是否翻译成英文小写
get_domain_cn = {k: v for k, v in zip(domain_en_list, domain_cn_list)}

data_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'QUATERNION', 'FLOAT4X4',
             'INT8', 'FLOAT2', 'INT16_2D', 'BYTE_COLOR']
png_list = ['域-布尔.png', '域-浮点.png', '域-整数.png', '域-矢量.png', '域-颜色.png', '域-旋转.png', '域-矩阵.png']
data_with_png = {k: v for k, v in zip(data_types, png_list+['域-整数.png', '域-矢量.png', '域-矢量.png', '域-颜色.png'])}

shader_date_types = ['BOOLEAN', 'FLOAT', 'INT', 'FLOAT_VECTOR', 'FLOAT_COLOR', 'INT8', 'FLOAT2', 'BYTE_COLOR']
# data_type:命名属性7种,存储属性10种
sub_data_type = {"BYTE_COLOR": "FLOAT_COLOR", "FLOAT2": "FLOAT_VECTOR", "INT8": "INT", 'INT16_2D': 'FLOAT_VECTOR'}

common_l = [['INT16_2D', 'FLOAT2', 'FLOAT_VECTOR'], ['BYTE_COLOR', 'FLOAT_COLOR'], 'QUATERNION', 'FLOAT4X4']
sort_key_l1: list[str | list] = ['BOOLEAN', 'FLOAT', ['INT8', 'INT']] + common_l
sort_key_l2: list[str | list] = [['INT8', 'INT'], 'BOOLEAN', 'FLOAT'] + common_l

HIDE_GROUPS = [
    (AttrGroup.VERTEX_GROUP, tr("顶点组"),     "GROUP_VERTEX"),
    (AttrGroup.UV_MAP,       tr("UV贴图"),     "UV"),
    (AttrGroup.COLOR_ATTR,   tr("颜色属性"),   "COLOR"),
    (AttrGroup.EXTRA_ATTR,   tr("额外属性"),   "CON_GEOMETRYATTRIBUTE"),
    (AttrGroup.UNUSED,       tr("未使用的"),   "OUTLINER_DATA_POINTCLOUD"),
    (AttrGroup.GROUP,        tr("组内属性"),   "NODETREE"),
    (AttrGroup.PREFIX,       tr("隐藏前缀"),   "INDIRECT_ONLY_OFF"),
]
