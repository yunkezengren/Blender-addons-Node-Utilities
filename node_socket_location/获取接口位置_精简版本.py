import ctypes
from bpy.types import NodeSocket
from mathutils import Vector as Vec2
from pprint import pprint

def sk_loc(socket: NodeSocket):
    
    Vec2(
        (ctypes.c_float * 2).from_address(
            ctypes.c_void_p.from_address(
                socket.as_pointer() + 520
                ).value + 24
            )
        )
    
    return Vec2((ctypes.c_float*2).from_address(ctypes.c_void_p.from_address(socket.as_pointer()+520).value+24))
    # return Vec2((ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24))

def sk_loc(socket: NodeSocket):
    runtime_address = socket.as_pointer() + 520
    runtime_pointer = ctypes.c_void_p.from_address(runtime_address)
    loc_address = runtime_pointer.value + 24
    Float2 = ctypes.c_float * 2
    loc = Float2.from_address(loc_address)
    return Vec2(loc[:])

def sk_loc(socket: NodeSocket):
    """ 直接从地址创建最终的目标类型对象 """
    #😍 offset 偏移量 是一个字段相对于其结构体起始位置的字节距离
    #😡 runtime 字段在 bNodeSocket 中的偏移量是 520, location 在 bNodeSocketRuntime 里的偏移量是 24
    runtime_address = socket.as_pointer() + 520
    #🤢 void* 不包含类型信息, 是 C/C++的“通用/泛型指针”,任何类型的指针都可以被安全隐式地转换成 void* 类型
    runtime_pointer = ctypes.c_void_p.from_address(runtime_address)
    loc_address = runtime_pointer.value + 24
    #👊🏿 Float2 是一个自定义的 ctypes 数组类型
    Float2 = ctypes.c_float * 2
    # 创建一个数组类型对象,在这个类型对象上调用 from_address 方法
    loc = Float2.from_address(loc_address)
    return Vec2(loc[:])


