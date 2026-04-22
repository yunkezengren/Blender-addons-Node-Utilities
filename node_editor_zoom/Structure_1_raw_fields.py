"""更原始的版本示例: 直接手写 `_fields_`。

这个版本比 `Structure_min_no_base.py` 更原始：
- 不使用类型注解
- 不使用 `__annotations__`
- 不做任何自动转换
- 直接写 ctypes 原生需要的 `_fields_`

优点是最直接、最贴近 ctypes 原生写法。
缺点是 IDE 的类型提示、补全和跳转体验会更差。
"""

import ctypes

class rctf(ctypes.Structure):
    _fields_ = [
        ("xmin", ctypes.c_float),
        ("xmax", ctypes.c_float),
        ("ymin", ctypes.c_float),
        ("ymax", ctypes.c_float),
    ]

class rcti(ctypes.Structure):
    _fields_ = [
        ("xmin", ctypes.c_int),
        ("xmax", ctypes.c_int),
        ("ymin", ctypes.c_int),
        ("ymax", ctypes.c_int),
    ]

class bView2D(ctypes.Structure):
    _fields_ = [
        ("tot", rctf),
        ("cur", rctf),
        ("vert", rcti),
        ("hor", rcti),
        ("mask", rcti),
        ("min", ctypes.c_float * 2),
        ("max", ctypes.c_float * 2),
        ("minzoom", ctypes.c_float),
        ("maxzoom", ctypes.c_float),
        ("scroll", ctypes.c_short),
        ("scroll_ui", ctypes.c_short),
        ("keeptot", ctypes.c_short),
        ("keepzoom", ctypes.c_short),
    ]
