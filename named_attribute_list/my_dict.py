from typing import Union, Optional
from dataclasses import dataclass, field

@dataclass
class Attr_Info:
    # 必选参数
    data_type: str
    """ ## data_type提示 """
    domain: list[str]
    domain_info: list[str] = field(default_factory=list)
    # 对于 list或dict这样的可变类型,必须这样, 直接写domain:list=[], 所有实例都会共享同一个列表
    group_name: Union[str, list[str]] = field(default_factory=list)
    group_node_name: list[str] = field(default_factory=list)
    group_name_parent: list[str] = field(default_factory=list)
    node_name: list[str] = field(default_factory=list)
    # "可能存在"的属性,Optional[bool] 是 Union[bool, None] 的简写
    if_instanced: Optional[bool] = None
    info: Optional[str] = None

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
