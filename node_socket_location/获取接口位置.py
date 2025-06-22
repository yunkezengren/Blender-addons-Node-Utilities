
# 😂 https://github.com/neliut/VoronoiLinker/
# 😂 感谢昵称为 "Oxicid" 的用户贡献了这段关于 ctypes 的代码. "原来还可以这样操作吗?! 🤔".
# 😂 唉, Blender的这些开发者啊 🤦; 我不得不自己动手添加获取节点插槽(socket)位置的功能. 
# 😂 'Blender 4.0 alpha' 的一团乱麻真是把我逼到墙角了.结果这事儿用Python就搞定了, 难道官方提供一个API就那么难吗? 🤷
# 😂 P.S.为陨落的英雄们默哀一分钟 🙏, https://projects.blender.org/blender/blender/pulls/117809.

# 😍 好了, 最难的部分已经过去了. 距离技术上支持折叠节点仅一步之遥了. 🚀
# 😍 那些渴望这个功能的人会面无表情地快速来到这里, 拿走他们需要的东西, 然后自己去修改. 😎
# 😍 致第一个实现这个功能的人: "干得漂亮, 兄弟! 👍 现在你可以连接到折叠节点的插槽了. 希望你幸福得合不拢腿." 😂

import ctypes
import platform
from pprint import pprint
import bpy
from bpy.types import NodeSocket
from mathutils import Vector as Vec2
from typing import Self, Any, Type

is_win = platform.system() == 'Windows'
isBlender4 = bpy.app.version[0] == 4
is_bl4_plus = bpy.app.version[0] >= 4

# 👊🏿 Blender 的 Python API (bpy.types) 和 C/C++ 底层数据之间,通过内存地址这个唯一的“ID”进行关联.(参考不能全信)
# 👊🏿 ctypes 正是利用了这个关联,绕过了官方提供的有限的 API,直接通过内存地址去读取和解释 底层的,未经封装的原始数据.

# 延迟初始化: ctypes 要求结构体的 _fields_ 属性必须在类定义时就确定. 
# 但如果结构体之间有循环引用(A包含B的指针,B包含A的指针),直接定义会出错.
# 1.定义: 先把所有字段定义存在 __annotations__, ctypes 还不知道这些是结构体字段, 所以不会报错.
# 2.初始化: 调用StructBase._init_structs(),遍历所有子类的__annotations__字典,一次性为所有类创建真正的_fields_属性.
# 3.清理: 创建完 _fields_ 后, 调用 cls.__annotations__.clear()把临时的定义清空.
class StructBase(ctypes.Structure):
    # 该列表里存储的是类对象 (Class Objects), 比如 BNodeSocket 的类型,
    # 如果_subclasses: list[Self], 而不是这些类的实例(Self)
    # cls._fields_ = fields
    # [跳转到_fields_定义还会多一个到__setattr__, 因为实例的属性可能是后面设置的].
    _subclasses: list[type[Self]] = []
    # _subclasses: list[Type["StructBase"]] = []
    # __annotations__: dict[str, Any] = {}    # 不写好像也行啊
    """ 作者并没有用 __annotations__ 来做类型提示, 而是用它来声明 C 结构体的字段名和字段类型.
        借用它的内置机制, 自动把 {'declaration': ctypes.c_void_p} 这样的键值对存入 annotations字典中 """
    def __init_subclass__(cls):       # 每当一个新的类继承 StructBase 时, 这个方法就会自动运行
        cls._subclasses.append(cls)
    @staticmethod
    def _init_structs():
        functype = type(lambda: None)       # <class 'function'>     lambda: None: 创建最简单的匿名函数,不接受参数,什么也不做
        # 🤢 print("="*50)
        for sub_cls in StructBase._subclasses:
            # fields: list[tuple] = []
            fields: list[tuple[str, Type[ctypes._CData]]] = []
            # 🤢 print(sub_cls)
            # # print(type(sub_cls))
            # # pprint(sub_cls.__annotations__)     # pprint会输出给字典键排序后的
            for field, value in sub_cls.__annotations__.items():
                if isinstance(value, functype):
                    # 对于有循环引用的地方,可能会把它写成一个 lambda 函数: BNodeSocket.next
                    # 🤢 print(f"+-+-+- {field:25}, {value}")
                    value = value()
                # print(f"{field:25}, {value}")
                fields.append((field, value))
            if fields:
                # _fields_ 向 ctypes 声明一个 Python Structure 类如何精确地映射到一段 C 语言的内存布局。
                # 每个元组代表 C 结构体中的一个字段, ctypes 会严格按照 _fields_ 列表中的顺序来安排内存。
                sub_cls._fields_ = fields
            sub_cls.__annotations__.clear()
        print("")
        StructBase._subclasses.clear()
    @classmethod
    # 将“如何创建”的通用逻辑放在基类中,以实现代码复用和统一接口。
    # Self@StructBase 是StructBase类或者子类的实例  type[X] 表示类 X 本身, 而不是它的实例
    def get_struct_instance_from_bpy_object(cls, socket: NodeSocket):
        """ 并没有 get 一个已有的 Python对象, 而是根据地址创建了新的 ctypes Python 对象来映射它 """
        # >>> print(sk)
        # <bpy_struct, NodeSocketInt("Seed") at 0x000001D1886333A0>
        # >>> hex(sk.as_pointer())                  '0x1d1886333a0'
        # as_pointer() 返回的 int 是C结构体本身的地址吗?还是说是二级指针( #🤢令人疑惑).
        return cls.from_address(socket.as_pointer())   # 用地址和结构体蓝图创建一个 ctypes 代理对象

""" using bNodeSocketRuntimeHandle = blender::bke::bNodeSocketRuntime;
class bNodeSocketRuntime : NonCopyable, NonMovable {
 public:
  const nodes::SocketDeclaration *declaration = nullptr;
  uint32_t changed_flag = 0;
  short total_inputs = 0;
  float2 location;
  Vector<bNodeLink *> directly_linked_links;
  Vector<bNodeSocket *> directly_linked_sockets;
  Vector<bNodeSocket *> logically_linked_sockets;
  Vector<bNodeSocket *> logically_linked_skipped_sockets;
  bNode *owner_node = nullptr;
  bNodeSocket *internal_link_input = nullptr;
  int index_in_node = -1;
  int index_in_all_sockets = -1;
  int index_in_inout_sockets = -1;
}; """

class BNodeSocketRuntimeHandle(StructBase): # \source\blender\blenkernel\BKE_node_runtime.hh -> bNodeSocketRuntime
    if is_win:
        vptr    : ctypes.c_char*8     # vtable_pointer虚函数表指针
    declaration : ctypes.c_void_p
    changed_flag: ctypes.c_uint32
    total_inputs: ctypes.c_short
    _pad1       : ctypes.c_char*2
    location    : ctypes.c_float*2

class BNodeStack(StructBase):               # \source\blender\makesdna\DNA_node_types.h
    vec        : ctypes.c_float*4
    min        : ctypes.c_float
    max        : ctypes.c_float
    data       : ctypes.c_void_p
    hasinput   : ctypes.c_short
    hasoutput  : ctypes.c_short
    datatype   : ctypes.c_short
    sockettype : ctypes.c_short
    is_copy    : ctypes.c_short
    external   : ctypes.c_short
    _pad       : ctypes.c_char*4


""" 三个地方不完全对应,c里都是8个字节"""
""" typedef struct bNodeSocket {
  struct bNodeSocket *next, *prev;
  IDProperty *prop;
  char identifier[64];
  char name[64];
  void *storage;
  😡 ▼▼▼▼   in_out: c_short
  short type;
  short flag;
  short limit;
  short in_out;
  😡 ▲▲▲▲
  bNodeSocketTypeHandle *typeinfo;
  char idname[64];
  void *default_value;
  😡 ▼▼▼▼   _pad: c_char*4
  short stack_index;
  char display_shape;
  char attribute_domain;
  char _pad[4];
  😡 ▲▲▲▲
  char label[64];
  char short_label[64];
  char description[64];
  char *default_attribute_name;
  😡 ▼▼▼▼   to_index: c_int
  int own_index DNA_DEPRECATED;
  int to_index DNA_DEPRECATED;
  😡 ▲▲▲▲
  struct bNodeLink *link;
  bNodeStack ns DNA_DEPRECATED;
  bNodeSocketRuntimeHandle *runtime;
} """
# BNodeSocket 528字节, 但是输入/出接口列表里,接口起始地址偏移量部分是640
class BNodeSocket(StructBase):              # \source\blender\makesdna\DNA_node_types.h
    next                  : ctypes.c_void_p     # lambda: ctypes.POINTER(BNodeSocket)   ctypes.POINTER(BNodeSocket)在类里还没定义,但可以用lambda
    prev                  : ctypes.c_void_p     # lambda: ctypes.POINTER(BNodeSocket)
    prop                  : ctypes.c_void_p
    identifier            : ctypes.c_char*64
    name                  : ctypes.c_char*64
    storage               : ctypes.c_void_p
    in_out                : ctypes.c_short   *4   # 😡 虽然缺了点,但没事,会自动8字节对齐?
    typeinfo              : ctypes.c_void_p
    idname                : ctypes.c_char*64
    default_value         : ctypes.c_void_p
    _pad                  : ctypes.c_char*4   *2  # 😡
    label                 : ctypes.c_char*64
    if is_bl4_plus and (bpy.app.version_string != '4.0.0 Alpha'):
        short_label       : ctypes.c_char*64
    description           : ctypes.c_char*64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index              : ctypes.c_int       *2 # 😡
    link                  : ctypes.c_void_p
    ns                    : BNodeStack
    runtime               : ctypes.POINTER(BNodeSocketRuntimeHandle)

StructBase._init_structs()

def sk_loc(sk: NodeSocket):
    """ 如果接口已启用且未隐藏, 则返回 Vec2(位置), 否则返回 None """
    # return Vec2(BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime.contents.location[:]) if sk.enabled and (not sk.hide) else Vec2((0, 0))
    if sk.enabled and (not sk.hide):
        print("----sk_loc:")
        # print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        
        # print(f"    sk.as_pointer()        {hex(sk.as_pointer()):17} {sk.as_pointer()}")
        b_sk = BNodeSocket.get_struct_instance_from_bpy_object(sk)
        print(f"    id(b_sk)               {hex(id(b_sk)):17} {id(b_sk)}")
        print(f"    id(b_sk.identifier)               {hex(id(b_sk.identifier)):17} {id(b_sk.identifier)}")
        base_address = ctypes.addressof(b_sk)
        print(f"    ctypes.addressof(b_sk) {hex(ctypes.addressof(b_sk)):17} {ctypes.addressof(b_sk)}")
        print(f"    ctypes.addressof(b_sk.identifier) {hex(ctypes.addressof(b_sk.identifier)):17} {ctypes.addressof(b_sk.identifier)}")
        
        runtime_p: ctypes._Pointer[BNodeSocketRuntimeHandle] = BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime
        # print(runtime_p)
        # print(runtime_p)
        # print(runtime_p.contents)
        # 解引用: 使用 contents 来获取指针"指向"的那个实际的 BNodeSocketRuntimeHandle 对象,[:]把ctypes数组转为Python列表(不转也行)
        return Vec2(runtime_p.contents.location[:])
    return None



def print_struct_layout(struct_class: type[StructBase]):
    """ 打印一个 ctypes 结构体所有字段的偏移量和大小. """
    print(f"--- 内存布局: {struct_class.__name__} ---")

    for field_name, field_type in struct_class._fields_:
        # 通过 getattr 从类中获取字段描述符
        # field_name 是 str 不能直接.field_name  struct_class.field_name
        field_descriptor = getattr(struct_class, field_name)
        
        offset = field_descriptor.offset
        size = field_descriptor.size
        
        print(f"  - 字段: {field_name[0:15]:<25} | 偏移量: {offset:>4} | 大小: {size:>3} 字节")
        
    total_size = ctypes.sizeof(struct_class)
    print("---------------------------------")
    print(f"结构体总大小: {total_size} 字节\n")



if __name__ == "__main__":

    sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]
    # print("="*60)
    # print(sk_loc(sk))

    print_struct_layout(BNodeSocket)

    b_sk = BNodeSocket.get_struct_instance_from_bpy_object(sk)
    runtime_p: "ctypes._Pointer[BNodeSocketRuntimeHandle]" = b_sk.runtime
    print(b_sk)
    print(runtime_p)

    print(f"identifier, {type(b_sk.identifier)}, {b_sk.identifier}")
    print(f"name      , {type(b_sk.name)}, {b_sk.name}")
    print(f"idname    , {type(b_sk.idname)}, {b_sk.idname}")

    # ? addressof + offset
    base_address = ctypes.addressof(b_sk)
    print(f"{base_address=}")
    # 😍 offset 是一个字段相对于其结构体起始位置的字节距离
    next_offset       = BNodeSocket.next.offset
    identifier_offset = BNodeSocket.identifier.offset
    identifier_offset = BNodeSocket.identifier.offset
    name_offset =       BNodeSocket.name.offset
    storage_offset =    BNodeSocket.storage.offset
    ns_offset =         BNodeSocket.ns.offset
    runtime_offset =    BNodeSocket.runtime.offset

    print(f"next 的偏移量: {next_offset:3}, 地址: {hex(base_address + next_offset)}")
    print(f"identifier 的偏移量: {identifier_offset:3}, 地址: {hex(base_address + identifier_offset)}")
    print(f"name 的偏移量      : {name_offset:3}, 地址: {hex(base_address + name_offset)}")
    print(f"storage 的偏移量   : {storage_offset:3}, 地址: {hex(base_address + storage_offset)}")
    print(f"ns 的偏移量        : {ns_offset:3}, 地址: {hex(base_address + ns_offset)}")
    print(f"runtime 的偏移量   : {runtime_offset:3}, 地址: {hex(base_address + runtime_offset)}")


    # ? from_address


# 🤢 bpy 的 NodeSocket 如何和 C 的结构体 对上的
