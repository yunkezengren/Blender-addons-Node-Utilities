import ctypes, bpy, platform
from mathutils import Vector as Vec2
from bpy.types import NodeSocket

class StructBase(ctypes.Structure):
    _subclasses= []
    __annotations__ = {}
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

