import ctypes, bpy, platform
from mathutils import Vector as Vec2
from bpy.types import NodeSocket

class StructBase(ctypes.Structure):
    _subclasses = []
    # __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    @staticmethod
    def _init_structs():
        functype = type(lambda: None)
        for cls in StructBase._subclasses:
            fields = []
            for field, value in cls.__annotations__.items():
                if isinstance(value, functype):
                    value = value()
                fields.append((field, value))
            if fields:
                cls._fields_ = fields
            cls.__annotations__.clear()
        StructBase._subclasses.clear()
    @classmethod
    def get_struct_instance_from_bpy_object(cls, tar: NodeSocket):
        return cls.from_address(tar.as_pointer())

class BNodeSocketRuntimeHandle(StructBase):
    if platform.system() == 'Windows':
        _pad0   : ctypes.c_char * 8
    declaration : ctypes.c_void_p
    changed_flag: ctypes.c_uint32
    total_inputs: ctypes.c_short
    _pad1       : ctypes.c_char * 2
    location    : ctypes.c_float * 2

class BNodeStack(StructBase):
    vec        : ctypes.c_float * 4
    min        : ctypes.c_float
    max        : ctypes.c_float
    data       : ctypes.c_void_p
    hasinput   : ctypes.c_short
    hasoutput  : ctypes.c_short
    datatype   : ctypes.c_short
    sockettype : ctypes.c_short
    is_copy    : ctypes.c_short
    external   : ctypes.c_short
    _pad       : ctypes.c_char * 4

class BNodeSocket(StructBase):
    next                  : ctypes.c_void_p         # 其实是 BNodeSocket 结构体指针
    prev                  : ctypes.c_void_p         # 其实是 BNodeSocket 结构体指针
    prop                  : ctypes.c_void_p
    identifier            : ctypes.c_char*64
    name                  : ctypes.c_char*64
    storage               : ctypes.c_void_p
    in_out                : ctypes.c_short
    typeinfo              : ctypes.c_void_p
    idname                : ctypes.c_char*64
    default_value         : ctypes.c_void_p
    _pad                  : ctypes.c_char*4
    label                 : ctypes.c_char*64
    description           : ctypes.c_char*64
    if (bpy.app.version[0] >= 4) and (bpy.app.version_string != '4.0.0 Alpha'):
        short_label       : ctypes.c_char*64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index              : ctypes.c_int
    link                  : ctypes.c_void_p
    ns                    : BNodeStack
    runtime               : ctypes.POINTER(BNodeSocketRuntimeHandle)

StructBase._init_structs()

def sk_loc(sk: NodeSocket):
    """ 如果接口已启用且未隐藏,则返回 Vec2(位置),否则返回 None """
    if sk.enabled and (not sk.hide):
        return Vec2(BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime.contents.location[:])
    return None


# import bpy
# # fake_bpy_modules\bpy\__init__.pyi

# # fake_bpy_modules\bpy\utils\__init__.pyi
# # utils\__init__ 里 from . import previews as previews
# # utils\__init__ 里 from . import units as units
# # fake_bpy_modules\bpy\utils\previews\__init__.pyi

# # fake_bpy_modules\bpy\ops\__init__.pyi
# # ops\__init__ 里from . import node as node
# # fake_bpy_modules\bpy\ops\node\__init__.pyi

# import bpy.utils.previews
# bpy.utils.previews.new()

# bpy.ops.node.add_node()
# bpy, utils, node, previews, node都是module
# 为什么这一行 bpy.utils.previews.new() 要import bpy.utils.previews 才是正确用法
# bpy.ops.node.add_node() 好像就不用


import pprint

def print_struct_layout(struct_class: type[StructBase]):
    print(f"--- 内存布局: {struct_class.__name__} ---")

    for field_name, field_type in struct_class._fields_:
        field_descriptor = getattr(struct_class, field_name)
        offset = field_descriptor.offset
        size = field_descriptor.size
        print(f"  - 字段: {field_name[0:15]:<25} | 偏移量: {offset:>4} | 大小: {size:>3} 字节")

    total_size = ctypes.sizeof(struct_class)
    print(f"结构体总大小: {total_size} 字节\n")


sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]


bpy.context.space_data.edit_tree

editor: bpy.types.SpaceNodeEditor = bpy.context.space_data
editor.edit_tree


print_struct_layout(BNodeSocket)
b_sk = BNodeSocket.get_struct_instance_from_bpy_object(sk)
b_sk = BNodeSocket.default_attribute_name
b_sk = BNodeSocket.description


a = list(10)
a.clear()
a= tuple(10)

a= dict(10)
a.clear()

b = len(a)
c = type(a)
print(a, b, c)
pprint.pprint("aaaaaaaaaaaa")
e = "aaaaaaaaaaaaaaaa"
e.capitalize()



def simple_sk_loc(socket: NodeSocket):
    
    Vec2(
        (ctypes.c_float * 2).from_address(
            ctypes.c_void_p.from_address(
                socket.as_pointer() + 520
                ).value + 24
            )
        )

    return Vec2((ctypes.c_float*2).from_address(ctypes.c_void_p.from_address(socket.as_pointer()+520).value+24))
    # return Vec2((ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24))

class Computer:

    def __init__(self):
        self.__maxprice = 900

    def sell(self):
        print(f'Selling Price: {self.__maxprice}')

    def setMaxPrice(self, price):
        self.__maxprice = price

cccccc = Computer()
c = Computer()
c.sell()

# change the price
c.__maxprice = 1000
c.sell()

# using setter function
c.setMaxPrice(1000)
c.sell()

simple_sk_loc()
pprint(simple_sk_loc())

getattr(Vec2, "aaa")

aaaaaaaa

