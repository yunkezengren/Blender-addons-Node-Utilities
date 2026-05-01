from bpy.types import Node, NodeSocket, UILayout
from mathutils import Vector as Vec2
from collections.abc import Sequence

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 将 VoronoiAddonPrefs 的导入移至 TYPE_CHECKING 块中，并将函数签名改为字符串类型注解，避免循环导入。
    from .preference import VoronoiAddonPrefs
    from .base_tool import ModelBaseTool

float2 = Sequence[float]
float4 = Sequence[float]

class Target():
    def __init__(self, target: Node | NodeSocket, *, distance=0.0, pos=Vec2((0.0, 0.0)), side=0, bottom_top=(0.0, 0.0), text=""):
        self.tar = target
        self.idname = target.bl_idname # Blender ID名称: 用于标识节点/接口的类型
        self.distance = distance       # 距离: 从光标/采样点到目标对象的距离(用于排序最近目标)
        self.pos = pos                 # 位置: 目标对象在屏幕/世界坐标系中的位置
        self.side = side               # 1=输出(节点右侧), -1=输入(节点左侧), 0=默认节点本身
        self.bottom_top = bottom_top   # 绘制区域垂直边界: (底部Y坐标, 顶部Y坐标), 用于高亮显示接口区域
        self.text = text               # 显示文本: 预缓存的翻译后文本(如接口名称)

class VestData:
    enum_props = []                      # 节点的下拉菜单/选项用于焊接，并在调用前检查是否存在。
    menu_sockets: list[NodeSocket] = []  # 节点的菜单输入接口
    domain_items = []
    list_length: int = 0
    nd = None
    boxScale = 1.0 # 如果忘记设置，至少盒子不会坍缩为零。
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False

class VptData:
    reprSkAnchor = ""

class PieRootData:
    isSpeedPie: bool = False
    pieScale: int = 0
    pieDisplaySocketTypeInfo: int = 0
    pieDisplaySocketColor: int = 0
    pieAlignment: int = 0
    ui_scale: int = 1.0
    prefs: "VoronoiAddonPrefs"

class VmtData(PieRootData):
    sk0: NodeSocket | None = None
    sk1: NodeSocket | None = None
    sk2: NodeSocket | None = None  # 小王
    skType = ""
    isHideOptions = False
    isPlaceImmediately = False

class VqmtData(PieRootData):
    list_speedPieDisplayItems = []
    sk0: NodeSocket | None = None
    sk1: NodeSocket | None = None
    depth = 0
    qmSkType = ''
    qmTrueSkType = ''
    isHideOptions = False
    isPlaceImmediately = False
    isJustPie = False # 无需。
    canProcHideSks = True
    dict_lastOperation = {}
    isFirstDone = False # https://github.com/ugorek000/VoronoiLinker/issues/20
    dict_existingValues = {}
    test_bool = False

class TryAndPass():
    def __enter__(self):
        pass
    def __exit__(self, *_):
        return True

class VlnstData:
    lastLastExecError = "" # 用于用户编辑 vlnst_last_exec_error, 不能添加或修改, 但可以删除.
    isUpdateWorking = False

def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnst_last_exec_error = ""
    elif self.vlnst_last_exec_error:
        if self.vlnst_last_exec_error!=VlnstData.lastLastExecError: # 注意: 谨防堆栈溢出.
            self.vlnst_last_exec_error = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False

def set_pie_data(self: "ModelBaseTool", toolData: PieRootData, prefs: "VoronoiAddonPrefs", col: UILayout):

    def get_pie_pref(name):
        return getattr(prefs, self.vl_triple_name.lower() + name)

    toolData.isSpeedPie = get_pie_pref("PieType") == 'SPEED'
    toolData.pieScale = get_pie_pref("PieScale")
    toolData.pieDisplaySocketTypeInfo = get_pie_pref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = get_pie_pref("PieDisplaySocketColor")
    toolData.pieAlignment = get_pie_pref("PieAlignment")
    toolData.ui_scale = self.ui_scale
    toolData.prefs = prefs
    prefs.va_decor_col_skBack = col
    prefs.va_decor_col_sk = col
