from bpy.types import Node, NodeSocket
from mathutils import Vector as Vec2
from collections.abc import Sequence

float2 = Sequence[float]
float4 = Sequence[float]

class Target():  # Found Target Goal (找到的目标), "剩下的你们自己看着办".
    # def __getattr__(self, att): # 天才. 仅次于 '(*args): return Vector((args))'.
    #    return getattr(self.target, att) # 但要小心, 它的速度慢了大约5倍.
    def __init__(self, target: Node | NodeSocket, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        self.tar = target  # 可能是 node 或 socket
        #self.sk = target                  # Target.sk = property(lambda a:a.target)
        #self.nd = target                  # Target.nd = property(lambda a:a.target)
        self.blid: str = target.bl_idname  # Target.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        # 下面的仅用于插槽.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text  # 用于支持其他语言的翻译. 每次绘制时都获取翻译太不方便了, 所以直接"焊接"上去.

class VestData:
    list_enumProps = []                      # 节点的下拉菜单/选项用于焊接，并在调用前检查是否存在。
    list_menu_socket: list[NodeSocket] = []  # 节点的菜单输入接口
    domain_item_list = []
    list_length: int = 0
    nd = None
    boxScale = 1.0 # 如果忘记设置，至少盒子不会坍缩为零。
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False

class VptData:
    reprSkAnchor = ""

class PieRootData:
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
    pieDisplaySocketColor = 0
    pieAlignment = 0
    uiScale = 1.0

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
    lastLastExecError = "" # 用于用户编辑 vlnstLastExecError, 不能添加或修改, 但可以删除.
    isUpdateWorking = False

def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnstLastExecError = ""
    elif self.vlnstLastExecError:
        if self.vlnstLastExecError!=VlnstData.lastLastExecError: # 注意: 谨防堆栈溢出.
            self.vlnstLastExecError = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False
