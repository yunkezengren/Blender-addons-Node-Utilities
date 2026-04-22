import ctypes

# 增加了 类型提示 和 跳转
# 失去了对成员的类型提示, bView2D._CField 比如: bView2D.maxzoom.offset

class StructBase(ctypes.Structure):
    # `__annotations__` 是 Python 存放类型注解的地方。 就算这里不手写， 也会自动为子类创建各自的 `__annotations__` 字典。
    # 这里显式写一个空字典，主要是为了把“这个基类依赖注解来生成 `_fields_`”这件事表达得更直白。
    __annotations__ = {}
    _sub_classes: list[type["StructBase"]] = []

    def __init_subclass__(cls) -> None:
        # `__init_subclass__` 是 Python 在“子类类对象已经创建好，并挂到继承链上之后”自动调用的钩子。
        StructBase._sub_classes.append(cls)

    @staticmethod
    def build_struct_fields() -> None:
        for sub in StructBase._sub_classes:
            sub._fields_ = list(sub.__annotations__.items())
            sub.__annotations__.clear()
        StructBase._sub_classes.clear()

class rctf(StructBase):  # C++ 结构体定义: source/blender/makesdna/DNA_vec_types.h:87
    xmin: ctypes.c_float
    xmax: ctypes.c_float
    ymin: ctypes.c_float
    ymax: ctypes.c_float

class rcti(StructBase):  # C++ 结构体定义: source/blender/makesdna/DNA_vec_types.h:70
    xmin: ctypes.c_int
    xmax: ctypes.c_int
    ymin: ctypes.c_int
    ymax: ctypes.c_int

# yapf: disable
class bView2D(StructBase):  # C++ 结构体定义: source/blender/makesdna/DNA_view2d_types.h:125
    # 这里只镜像到 `keepzoom` 为止，因为修改 `maxzoom` 只需要前半段布局。
    tot      : rctf
    cur      : rctf
    vert     : rcti
    hor      : rcti
    mask     : rcti
    min      : ctypes.c_float * 2
    max      : ctypes.c_float * 2
    minzoom  : ctypes.c_float
    maxzoom  : ctypes.c_float
    scroll   : ctypes.c_short
    scroll_ui: ctypes.c_short
    keeptot  : ctypes.c_short
    keepzoom : ctypes.c_short
# yapf: enable

StructBase.build_struct_fields()
