from dataclasses import dataclass, field
from enum import Enum

# field(default_factory=list) 作用：为数据类的每个新实例/对象 创建一个全新的、独立的空列表作为默认值。
# 创建一个 Attr_Info 对象时，如果没给 domain_info 传值，它都会得到一个属于自己的、新的空列表。
# 默认值只在函数/类定义时创建一次;所有实例共享同一个默认值;修改一个，影响所有

class Group(Enum):
    VERTEX_GROUP = "vertex_group"
    UV_MAP = "uv_map"
    COLOR_ATTR = "color_attr"
    EXTRA_ATTR = "extra_attr"
    UNEVALUATED = "unevaluated"
    GROUP = "group"
    PREFIX = "prefix"

@dataclass
class Attr_Info:
    # 必选参数
    data_type: str
    """ ## data_type提示 """

    domain: list[str]

    domain_info: list[str] = field(default_factory=list)
    """ ### todo 应该可以删掉 domain_info,在需要的地方再 domain -> domain_info """

    # 对于 list或dict这样的可变类型,必须这样, 直接写domain:list=[], 所有实例都会共享同一个列表
    group_name: str | list[str] = field(default_factory=list)

    group_node_name: list[str] = field(default_factory=list)

    group_name_parent: list[str] = field(default_factory=list)

    node_name: list[str] = field(default_factory=list)

    # "可能存在"的属性
    if_instanced: bool | None = None

    info: str | None = None

    # 隐藏原因分组
    attr_group: Group | None = None

Attr_Dict = dict[str, Attr_Info]

_example = {
    '-Value0': {
        'data_type': 'FLOAT',
        'domain': ['EDGE'],
        'domain_info': ['边'],
        'group_name': ['测试.001'],
        'group_name_parent': ['顶层节点树无父级/wrapper'],
        'group_node_name': ['当前group是顶层节点树/Group'],
        'if_instanced': False,
        'node_name': ['Store Named Attribute.007']
    },
    '1111111': {
        'data_type': 'FLOAT',
        'domain': ['POINT'],
        'domain_info': ['点'],
        'group_name': '不确定'
    },
    'Group': {
        'data_type': 'FLOAT',
        'domain': ['POINT'],
        'domain_info': ['点'],
        'group_name': '物体属性',
        'info': '顶点组'
    },
    '查找': {
        'data_type': 'INT',
        'domain': ['POINT', 'POINT'],
        'domain_info': ['点', '点'],
        'group_name': ['测试.001', '测试.001'],
        'group_name_parent': ['顶层节点树无父级/wrapper', '顶层节点树无父级/wrapper'],
        'group_node_name': ['当前group是顶层节点树/Group', '当前group是顶层节点树/Group'],
        'if_instanced': False,
        'node_name': ['Store Named Attribute.008', 'Store Named Attribute.011']
    },
}
