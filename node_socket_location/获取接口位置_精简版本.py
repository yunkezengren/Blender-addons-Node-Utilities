import ctypes
from bpy.types import NodeSocket
from mathutils import Vector as Vec2
from pprint import pprint

def sk_loc(socket: NodeSocket):
    return Vec2((ctypes.c_float * 2).from_address(ctypes.c_void_p.from_address(socket.as_pointer() + 520).value + 24))

def sk_loc(socket: NodeSocket):
    runtime_address = socket.as_pointer() + 520
    runtime_pointer = ctypes.c_void_p.from_address(runtime_address)
    loc_address = runtime_pointer.value + 24
    Float2 = ctypes.c_float * 2
    loc = Float2.from_address(loc_address)
    return Vec2(loc[:])


import bpy
def is_active_viewer(node: bpy.types.Node):
    if node.type != "VIEWER": return False
    import ctypes
    flag_offset = 116
    import platform
    if platform.system() == 'Windows':
        flag_offset += 8
    flag = ctypes.c_int.from_address(node.as_pointer() + flag_offset).value
    return bool(flag & (1 << 6))

node = bpy.data.node_groups["Combine Matrix.001"].nodes["Viewer.001"]
print(is_active_viewer(node))

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

component_map = {
    0: "Mesh",
    1: "PointCloud",
    2: "Instance",
    3: "Volume",
    4: "Curve",
    5: "Edit",
    6: "GreasePencil",
}

from ctypes import c_int, c_void_p

def sk_support_types(socket: NodeSocket):
    if socket.type != "GEOMETRY": return
    runtime_ptr_addr = socket.as_pointer() + 520
    runtime_addr = c_void_p.from_address(runtime_ptr_addr).value
    declare_ptr_addr = runtime_addr + 8
    declare_addr = c_void_p.from_address(declare_ptr_addr).value
    declare_addr -= 8 * 5
    support_type_addr = declare_addr + 424 - 8 * 2
    begain_addr = c_void_p.from_address(support_type_addr).value
    end_addr = c_void_p.from_address(support_type_addr + 8).value

    support_num = int((end_addr - begain_addr) / 4)
    types: list[str] = []
    if support_num:
        for i in range(support_num):
            support_type = c_int.from_address(begain_addr + i*4).value
            types.append(component_map[support_type])
    else:
        types.append("支持全部类型")
    return types


""" 
😍 as_pointer + 520 是 runtime 指针成员在 bNodeSocket 里的地址
😍 declare_ptr 是 runtime(bNodeTreeRuntime) 类里的第一个成员, +8 虚函数表指针?
🤢 不知道为什么VS 查看类内存布局不准确,in_out 前有5 个40/48字节的, 难道每个多了8字节?
🤢 不准确 + 1, support_type 前有2 个64 字节的, 难道每个多了8字节?
😍 424 是 Geometry 里第一个成员, 但是继承,所以起始地址 424 (class Geometry : SocketDeclaration) """

def sk_support_types(socket: NodeSocket):
    if socket.type != "GEOMETRY": return
    runtime_ptr_addr = socket.as_pointer() + 520
    runtime_addr = c_void_p.from_address(runtime_ptr_addr).value
    declare_ptr_addr = runtime_addr + 8
    declare_addr = c_void_p.from_address(declare_ptr_addr).value
    declare_addr -= 8 * 5
    # in_out         = c_int.from_address(declare_addr + 224)
    # align_pre_sk   = c_bool.from_address(declare_addr + 240).value
    # return in_out, f"{align_pre_sk=}"
    support_type_addr = declare_addr + 424 - 8 * 2
    # supported_types_ 是 blender::Vector<Component::Type>, begain_ 和 end_ 是Vector里前两个指针成员
    begain_addr = c_void_p.from_address(support_type_addr).value
    end_addr = c_void_p.from_address(support_type_addr + 8).value

    support_num = int((end_addr - begain_addr) / 4)
    types: list[str] = []
    if support_num:
        for i in range(support_num):
            support_type = c_int.from_address(begain_addr + i*4).value
            types.append(component_map[support_type])
    else:
        types.append("支持全部类型")
    return types


# - source\blender\blenkernel\BKE_geometry_set.hh
# class GeometryComponent : public ImplicitSharingMixin {
#  public:
#   enum class Type {
#     Mesh = 0,
#     PointCloud = 1,
#     Instance = 2,
#     Volume = 3,
#     Curve = 4,
#     Edit = 5,
#     GreasePencil = 6,
#   }; ......}

#👊🏿 处理 SocketDeclaration
# class ItemDeclaration                                 # - source\blender\nodes\NOD_node_declaration.hh
# class SocketDeclaration : public ItemDeclaration
# class Geometry : public SocketDeclaration             # - source\blender\nodes\NOD_socket_declarations_geometry.hh
# ItemDeclaration     16字节
# SocketDeclaration  416字节
# Geometry           480字节       supported_types_偏移量416,大小56
# geometry_decl = SocketDeclarationGeometry.from_address(declaration_obj_addr)





# class Geometry : public SocketDeclaration {
#  private:
#   blender::Vector<bke::GeometryComponent::Type> supported_types_;
#   bool only_realized_data_ = false;
#   bool only_instances_ = false;
#   friend GeometryBuilder;
#  public:
#   static constexpr eNodeSocketDatatype static_socket_type = SOCK_GEOMETRY;
#   using Builder = GeometryBuilder;
#   bNodeSocket &build(bNodeTree &ntree, bNode &node) const override;
#   bool matches(const bNodeSocket &socket) const override;
#   bool can_connect(const bNodeSocket &socket) const override;
#   Span<bke::GeometryComponent::Type> supported_types() const;
#   bool only_realized_data() const;
#   bool only_instances() const;
# };
#

# class bNodeSocketRuntime : NonCopyable, NonMovable {
#  public:
#   const nodes::SocketDeclaration *declaration = nullptr;
#   uint32_t changed_flag = 0;
#   short total_inputs = 0;
#   float2 location;   ......}



#👊🏿 c++里是这样写的获取 supported_types
# static std::optional<std::string> create_declaration_inspection_string(const bNodeSocket &socket){
#   fmt::memory_buffer buf;
#   if (const nodes::decl::Geometry *socket_decl = dynamic_cast<const nodes::decl::Geometry *>(socket.runtime->declaration)){
#       create_inspection_string_for_geometry_socket(buf, socket_decl); }  ......}


# static void create_inspection_string_for_geometry_socket(fmt::memory_buffer &buf, const nodes::decl::Geometry *socket_decl){
#   if (socket_decl == nullptr || socket_decl->in_out == SOCK_OUT) { return;}

#   Span<bke::GeometryComponent::Type> supported_types = socket_decl->supported_types();
#   if (supported_types.is_empty()) {
#     fmt::format_to(fmt::appender(buf), "{}", TIP_("Supported: All Types"));
#     return;
#   }
#   fmt::format_to(fmt::appender(buf), "{}", TIP_("Supported: "));
#   for (bke::GeometryComponent::Type type : supported_types) {
#     switch (type) {
#       case bke::GeometryComponent::Type::Mesh: {
#         fmt::format_to(fmt::appender(buf), "{}", TIP_("Mesh"));
#         break;
#       }
#       case bke::GeometryComponent::Type::PointCloud: {
#         fmt::format_to(fmt::appender(buf), "{}", TIP_("Point Cloud"));
#         break;
#       }
# ......}
