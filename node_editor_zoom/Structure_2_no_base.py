"""最简版本示例: 不使用 StructBase(ctypes.Structure)。

这个版本最直接：
1. 先写类型注解字段
2. 再手动把 `__annotations__` 转成 `_fields_`

优点是没有额外基类和自动注册逻辑。
缺点是每个结构体都要手动调用一次初始化。
"""

import ctypes

class rctf(ctypes.Structure):
    xmin: ctypes.c_float
    xmax: ctypes.c_float
    ymin: ctypes.c_float
    ymax: ctypes.c_float

rctf._fields_ = list(rctf.__annotations__.items())

class rcti(ctypes.Structure):
    xmin: ctypes.c_int
    xmax: ctypes.c_int
    ymin: ctypes.c_int
    ymax: ctypes.c_int

rcti._fields_ = list(rcti.__annotations__.items())

class bView2D(ctypes.Structure):
    tot: rctf
    cur: rctf
    vert: rcti
    hor: rcti
    mask: rcti
    min: ctypes.c_float * 2
    max: ctypes.c_float * 2
    minzoom: ctypes.c_float
    maxzoom: ctypes.c_float
    scroll: ctypes.c_short
    scroll_ui: ctypes.c_short
    keeptot: ctypes.c_short
    keepzoom: ctypes.c_short

bView2D._fields_ = list(bView2D.__annotations__.items())
