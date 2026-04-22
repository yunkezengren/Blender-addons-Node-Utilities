"""最简版本示例: 使用 classmethod 版本的 StructBase。

这个版本和正式版相比更朴素：
- 不维护子类注册表
- 每个结构体自己调用 `init_struct()`
"""

import ctypes

class StructBase(ctypes.Structure):

    @classmethod
    def init_struct(cls) -> None:
        cls._fields_ = list(cls.__annotations__.items())

class rctf(StructBase):
    xmin: ctypes.c_float
    xmax: ctypes.c_float
    ymin: ctypes.c_float
    ymax: ctypes.c_float

class rcti(StructBase):
    xmin: ctypes.c_int
    xmax: ctypes.c_int
    ymin: ctypes.c_int
    ymax: ctypes.c_int

class bView2D(StructBase):
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

rctf.init_struct()
rcti.init_struct()
bView2D.init_struct()
