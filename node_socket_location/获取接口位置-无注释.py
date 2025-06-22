# https://github.com/neliut/VoronoiLinker/wiki
# 感谢昵称为 "Oxicid" 的用户提供的这段关于 ctypes 的代码.  “什么,原来还能这样？”
# 唉,这些开发者；不得不自己添加获取接口(socket)位置的功能. 'Blender 4.0 alpha' 的混乱把我逼得没办法,迫使我这么做. 
# ..这竟然用 Python 就搞定了,难道提供(暴露)一个 API 就那么难吗？
# 附言：为陨落的英雄们默哀一分钟,https://projects.blender.org/blender/blender/pulls/117809. 
# 好吧,最难的部分已经过去了. 距离技术上能够支持折叠节点只有一步之遥了. 
# 那些渴望这个功能的人会很快地板着扑克脸来到这里,拿走他们需要的东西,然后为自己修改. 
# 第一个这样做的人,我给你的留言是：“好吧,干得不错. 现在你可以‘勾搭’上折叠节点的接口了. 希望你高兴得不得了”. 

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

def SkGetLocVec(sk: NodeSocket):
    """ 如果接口已启用且未隐藏,则返回 Vec2(位置),否则返回 Vec2((0, 0)) """
    return Vec2(BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime.contents.location[:]) if sk.enabled and (not sk.hide) else Vec2((0, 0))

# sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]
# print(SkGetLocVec(sk))
