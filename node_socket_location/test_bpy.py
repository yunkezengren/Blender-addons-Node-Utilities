import bpy
from pprint import pprint

def print_bpy():
    modules = [
        bpy,
        bpy.ops,
        # bpy.utils,
        bpy.types,
        bpy.props,
        bpy.path,
        bpy.msgbus,
    ]
    # for module in modules:
    #     print(module)
    #     print(f"{type(module)=}")
    #     print(f"\ndir({module})")
    #     print(dir(module))
    #     pprint(module.__dict__)

    datas = [
        bpy.context,
        bpy.data,
        bpy.app,
    ]
    # for data in datas:
    #     print(data)
    #     print(f"{type(data)=}")
    #     # print(f"\ndir({data})")
    #     # print(dir(data))
    #     # pprint(data.__dict__)             # 没 __dict__
    #     # pprint(type(data).__slot__)       # 没, 虽然 '__slots__': (), 仍会采用 slotted 模式来创建实例,实例对象不会被分配 __dict__ 字典
    #     pprint(type(data).__dict__)


    # bpy.data/app/context object has no attribute '__dict__',因为使用了__slot__ 类属性
    # 像 context 和 data 这样的核心对象在 Blender 运行期间是长期存在的，而且它们的结构是固定的，不需要用户在运行时动态添加属性。
    # 使用 __slots__ 可以减少内存占用并提高访问效率。
    # 类 __dict__ 和实例 __dict__ 是两个完全独立、用途也截然不同的字典。

    # print(bpy.utils.previews)

