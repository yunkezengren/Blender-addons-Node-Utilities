if "bpy" in locals():
    import importlib
    # importlib.reload(获取接口位置)
    print("bpy in locals()")
    print("+++++++++++++++++++测试")
    # importlib.reload(获取接口位置)
print("+++++++++++++++++++测试000000000")
import bpy
import ctypes
# from .获取接口位置 import sk_loc




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
    """ 如果接口已启用且未隐藏, 则返回 Vec2(位置), 否则返回 None """
    # return Vec2(BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime.contents.location[:]) if sk.enabled and (not sk.hide) else Vec2((0, 0))
    if sk.enabled and (not sk.hide):
        print("="*50 + "sk_loc:")
        
        # print(f"    sk.as_pointer()        {hex(sk.as_pointer()):17} {sk.as_pointer()}")
        b_sk = BNodeSocket.get_struct_instance_from_bpy_object(sk)
        base_address = ctypes.addressof(b_sk)
        print(f"    addressof(b_sk)           {hex(ctypes.addressof(b_sk)):17} {ctypes.addressof(b_sk)}")
        runtime_c = b_sk.runtime.contents
        print(f"    addressof(runtime_c)      {hex(ctypes.addressof(runtime_c)):17} {ctypes.addressof(runtime_c)}")
        print(b_sk.runtime)
        print(b_sk.runtime.contents)
        print(f"    addressof(runtime_c.location)      {hex(ctypes.addressof(runtime_c.location)):17} {ctypes.addressof(runtime_c.location)}")
        
        runtime_p: ctypes._Pointer[BNodeSocketRuntimeHandle] = BNodeSocket.get_struct_instance_from_bpy_object(sk).runtime
        # print(runtime_p)
        # print(runtime_p)
        # print(runtime_p.contents)
        # 解引用: 使用 contents 来获取指针"指向"的那个实际的 BNodeSocketRuntimeHandle 对象,[:]把ctypes数组转为Python列表(不转也行)
        return Vec2(runtime_p.contents.location[:])
    return None


class NODE_OT_print_socket_location(bpy.types.Operator):
    bl_idname = "node.print_socket_location"
    bl_label = "Print Socket Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        P_VOID = ctypes.c_void_p
        # 指向 float 的指针类型
        P_FLOAT = ctypes.POINTER(ctypes.c_float)

        # --- 第一步: 获取 runtime 指针的值 (地址 A) ---
        sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]

        # 1.2 计算 runtime 字段的地址 (基地址 + 偏移量)
        # 我们已经知道 runtime 字段在 BNodeSocket 中的偏移量是 520
        runtime_address = sk.as_pointer() + 520

        # 1.3 从这个地址读取一个 "void*" 指针
        # from_address 返回一个 ctypes 指针对象
        runtime_p = P_VOID.from_address(runtime_address)
        print("=" * 50)
        print(sk)
        print(f"    runtime_address    {hex(runtime_address)}  {runtime_address}")
        # print(type(runtime_p))
        print(f"{runtime_p=}")          # <class 'ctypes.c_void_p'>
        
        # # 1.4 获取这个指针对象所存储的值, 也就是我们梦寐以求的地址 A
        # # 如果指针是 NULL, .value 会是 0 或 None
        runtime_a = runtime_p.value
        print(f"    runtime_p.value  {hex(runtime_p.value)}  {runtime_p.value} ")
        # print(runtime_a)
        if not runtime_a:
            print("警告: runtime 指针为 NULL.")
        
        # # 3.1 将 location_field_address 强制转换 (cast) 成一个浮点数指针
        # # 告诉 ctypes: "请把这个地址当作一个浮点数序列的开头"
        # location_ptr = ctypes.cast(loc_address, P_FLOAT)
        
        P_VOID = ctypes.c_void_p
        runtime_p = P_VOID.from_address(runtime_address)
        runtime_a = runtime_p.value
        loc_address = runtime_a + 8 + 16
        # b_sk = BNodeSocket.get_struct_instance_from_bpy_object(sk)
        # loc_address2 = ctypes.addressof(b_sk.runtime.contents)
        # runtime_a 是正确的, 和loc_address2一样
        # ✨ 关键点 2: 直接从地址创建最终的目标类型对象 ✨
        # 不要分步 cast 再索引, 而是直接创建我们想要的最终类型 (float[2] 数组) 同样, 用一个变量 location_array_obj 来“接住”它, 保证其生命周期
        Float2 = ctypes.c_float * 2
        location_ptr = Float2.from_address(loc_address)
        loc_x = location_ptr[0]
        loc_y = location_ptr[1]
        print(loc_x, loc_y)     #  还是不对啊  0.0 0.0 
        
        print(sk_loc(sk))
        
        # a_node = context.active_node
        # if not a_node:
        #     self.report({'INFO'}, "No active node selected.")
        #     return {'CANCELLED'}
        # print(f"\n--- Node: '{a_node.name}' (Type: {a_node.bl_idname}) ---")

        # if a_node.inputs:
        #     print("Inputs:")
        #     for socket in a_node.inputs:
        #         print(f"  - {socket.name:20} {sk_loc(socket)}")
        # else:
        #     print("Inputs: None")

        # # 遍历输出接口
        # if a_node.outputs:
        #     print("Outputs:")
        #     for socket in a_node.outputs:
        #         print(f"  - {socket.name:20} {sk_loc(socket)}")
        # else:
        #     print("Outputs: None")
        # print("-------------------------------------------------")

        return {'FINISHED'}

# import bpy, ctypes
# sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]

# loc_address = ctypes.c_void_p.from_address(sk.as_pointer() + 520).value + 24
# Float2 = ctypes.c_float * 2
# loc_ptr = Float2.from_address(loc_address)
# loc_x = loc_ptr[0]
# loc_y = loc_ptr[1]
# print(loc_x, loc_y)


import bpy, ctypes
sk = bpy.data.node_groups["Geometry Nodes"].nodes["Math"].inputs[0]

loc_address = ctypes.c_void_p.from_address(sk.as_pointer() + 520).value + 24
Float2 = ctypes.c_float * 2
loc = Float2.from_address(loc_address)[:]
print(loc)

print(Float2.from_address(loc_address)[:])






class NODE_PT_socket_printer_panel(bpy.types.Panel):
    bl_label = "Socket Printer"
    bl_idname = "NODE_PT_socket_printer"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Socket Printer"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(NODE_OT_print_socket_location.bl_idname)

classes = (
    NODE_OT_print_socket_location,
    NODE_PT_socket_printer_panel,
)

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(NODE_OT_print_socket_location.bl_idname, 'P', 'PRESS', ctrl=True, alt=True, shift=False)
    addon_keymaps.append((km, kmi))

def unregister():
    # 注销快捷键
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # 以相反的顺序注销所有类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
