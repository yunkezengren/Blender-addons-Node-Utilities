import ctypes
import bpy
from .globals import is_win, is_bl4_plus, is_bl5_plus

class StructBase(ctypes.Structure):
    _subclasses = []
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
    def GetFields(cls, tar):
        return cls.from_address(tar.as_pointer())

class BNodeSocketRuntimeHandle(StructBase): # \source\blender\makesdna\DNA_node_types.h
    if is_win:
        _pad0             : ctypes.c_char*8
    declaration           : ctypes.c_void_p
    changed_flag          : ctypes.c_uint32
    total_inputs          : ctypes.c_short
    _pad1                 : ctypes.c_char*2
    location              : ctypes.c_float*2

class BNodeStack(StructBase):
    vec                   : ctypes.c_float*4
    min                   : ctypes.c_float
    max                   : ctypes.c_float
    data                  : ctypes.c_void_p
    hasinput              : ctypes.c_short
    hasoutput             : ctypes.c_short
    datatype              : ctypes.c_short
    sockettype            : ctypes.c_short
    is_copy               : ctypes.c_short
    external              : ctypes.c_short
    _pad                  : ctypes.c_char*4

class BNodeSocket(StructBase):
    next                  : ctypes.c_void_p    # lambda: ctypes.POINTER(BNodeSocket)
    prev                  : ctypes.c_void_p    # lambda: ctypes.POINTER(BNodeSocket)
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
    if (is_bl4_plus) and bpy.app.version < (5, 1, 0):
        short_label       : ctypes.c_char*64        #  2025-10-28 5.1移除 https://projects.blender.org/blender/blender/pulls/148940/files
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index              : ctypes.c_int
    link                  : ctypes.c_void_p
    ns: BNodeStack
    runtime               : ctypes.POINTER(BNodeSocketRuntimeHandle)

class BNodeType(StructBase):                # \source\blender\blenkernel\BKE_node.h
    # 从内存布局以及debug看,idname 等几个5.0改成了 std::string ,显示40字节,nclass 偏移量是168字节
    # 😡但是为什么std::string当做32字节才对啊,为什么从144开始读 nclass 才对
    idname                : ctypes.c_char*32 if is_bl5_plus else ctypes.c_char*64
    type                  : ctypes.c_int
    if is_bl5_plus:
        _pad1             : ctypes.c_char*4
    ui_name               : ctypes.c_char*32 if is_bl5_plus else ctypes.c_char*64
    ui_description        : ctypes.c_char*32 if is_bl5_plus else ctypes.c_char*256
    ui_icon               : ctypes.c_int
    _pad2                 : ctypes.c_char*4
    if bpy.app.version >= (4, 0, 0):
        enum_name_legacy  : ctypes.c_void_p
    width                 : ctypes.c_float
    minwidth              : ctypes.c_float
    maxwidth              : ctypes.c_float
    height                : ctypes.c_float
    minheight             : ctypes.c_float
    maxheight             : ctypes.c_float
    nclass                : ctypes.c_int16   # 参考链接: https://github.com/ugorek000/ManagersNodeTree

class BNode(StructBase):     # 用于VRT.
    next       : ctypes.c_void_p        # lambda: ctypes.POINTER(BNode)
    prev       : ctypes.c_void_p        # lambda: ctypes.POINTER(BNode)
    inputs     : ctypes.c_void_p*2
    outputs    : ctypes.c_void_p*2
    name       : ctypes.c_char*64
    identifier : ctypes.c_int
    flag       : ctypes.c_int
    idname     : ctypes.c_char*64
    typeinfo   : ctypes.POINTER(BNodeType)
    type       : ctypes.c_int16
    ui_order   : ctypes.c_int16
    custom1    : ctypes.c_int16
    custom2    : ctypes.c_int16
    custom3    : ctypes.c_float
    custom4    : ctypes.c_float
    id         : ctypes.c_void_p
    storage    : ctypes.c_void_p
    prop       : ctypes.c_void_p
    parent     : ctypes.c_void_p
    locx       : ctypes.c_float
    locy       : ctypes.c_float
    width      : ctypes.c_float
    height     : ctypes.c_float
    offsetx    : ctypes.c_float
    offsety    : ctypes.c_float
    label      : ctypes.c_char*64
    color      : ctypes.c_float*3

# 感谢昵称为 "Oxicid" 的用户贡献了这段关于 ctypes 的代码. "原来还可以这样操作吗?! 🤔".
# 唉, Blender的这些开发者啊 🤦; 我不得不自己动手添加获取节点插槽(socket)位置的功能. 
# 'Blender 4.0 alpha' 的一团乱麻真是把我逼到墙角了.结果这事儿用Python就搞定了, 难道官方提供一个API就那么难吗? 🤷
# P.S.为陨落的英雄们默哀一分钟 🙏, https://projects.blender.org/blender/blender/pulls/117809.

# 好了, 最难的部分已经过去了. 距离技术上支持折叠节点仅一步之遥了. 🚀
# 那些渴望这个功能的人会面无表情地快速来到这里, 拿走他们需要的东西, 然后自己去修改. 😎
# 致第一个实现这个功能的人: "干得漂亮, 兄弟! 👍 现在你可以连接到折叠节点的插槽了. 希望你幸福得合不拢腿." 😂

class RectBase(StructBase):

    def get_raw(self):
        return self.xmin, self.ymin, self.xmax, self.ymax

    def translate_raw(self, xy):
        self.xmin += xy[0]
        self.xmax += xy[0]
        self.ymin += xy[1]
        self.ymax += xy[1]

    def translate_scale_fac(self, xy, fac=0.5):
        if xy[0] > 0:
            self.xmin += xy[0]*fac
            self.xmax += xy[0]
        elif xy[0] < 0:
            self.xmin += xy[0]
            self.xmax += xy[0]*fac

        if xy[1] > 0:
            self.ymin += xy[1]*fac
            self.ymax += xy[1]
        elif xy[1] < 0:
            self.ymin += xy[1]
            self.ymax += xy[1]*fac

    def zoom(self, center=None, fac=1.0):
        if center:
            centerX = center[0]
            centerY = center[1]
        else:
            centerX = (self.xmax + self.xmin) / 2
            centerY = (self.ymax + self.ymin) / 2
        self.xmax = (self.xmax - centerX)*fac + centerX
        self.xmin = (self.xmin - centerX)*fac + centerX
        self.ymax = (self.ymax - centerY)*fac + centerY
        self.ymin = (self.ymin - centerY)*fac + centerY

class Rctf(RectBase):
    xmin : ctypes.c_float
    xmax : ctypes.c_float
    ymin : ctypes.c_float
    ymax : ctypes.c_float

class Rcti(RectBase):
    xmin : ctypes.c_int
    xmax : ctypes.c_int
    ymin : ctypes.c_int
    ymax : ctypes.c_int

class BView2D(StructBase):    # \source\blender\makesdna\DNA_view2d_types.h
    tot       : Rctf
    cur       : Rctf
    vert      : Rcti
    hor       : Rcti
    mask      : Rcti
    min       : ctypes.c_float*2
    max       : ctypes.c_float*2
    minzoom   : ctypes.c_float
    maxzoom   : ctypes.c_float
    scroll    : ctypes.c_short
    scroll_ui : ctypes.c_short
    keeptot   : ctypes.c_short
    keepzoom  : ctypes.c_short

    def get_zoom(self):
        return (self.mask.xmax - self.mask.xmin) / (self.cur.xmax - self.cur.xmin)  # 多亏了 keepzoom==3, 我们可以只从一个轴读取数据. ✅

StructBase._init_structs()
