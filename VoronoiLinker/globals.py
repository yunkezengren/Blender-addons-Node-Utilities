import platform
from math import pi
import bpy

# 这两个变量会被更改,别的不会
prefsTran = None
dict_vlHhTranslations = {}      # 再多个文件配合使用

Color_Bar_Width = 0.015     # 小王 饼菜单颜色条宽度
Cursor_X_Offset = -50       # 小王 这样更舒服,在输入或输出接口方面加强

isWin = platform.system() == 'Windows'
#isLinux = platform.system()=='Linux'

voronoiAnchorCnName = 'Voronoi_Anchor'           # 不支持翻译, 就这样一起吧.
voronoiAnchorDtName = 'Voronoi_Anchor_Dist'      # 不支持翻译! 请参考相关的拓扑结构.
voronoiSkPreviewName = 'voronoi_preview'         # 不支持翻译, 不想每次读取都用 _iface() 包裹一下.
voronoiPreviewResultNdName = 'SavePreviewResult' # 不支持翻译, 就这样一起吧.


float_int_color = {'INT': (0.35, 0.55, 0.36, 1), 'VALUE': (0.63, 0.63, 0.63, 1)}
floatIntColorInverse = {'INT': (0.63, 0.63, 0.63, 1), 'VALUE': (0.35, 0.55, 0.36, 1)}

# 用于支持在旧版本中工作. 这样在被迫切换到旧版本时, 心里能舒坦点, 不用那么紧张,
# 还能因为插件能在不同API的不同版本中运行而获得额外的内啡肽. 😎
#Todo0VV: 尽可能地向更低版本兼容. 目前能保证的是: b4.0 和 b4.1? 🤔
is_bl4_plus = bpy.app.version[0] >= 4
is_bl5_plus = bpy.app.version >= (5, 0, 0)

sk_type_idname_map = {
    'SHADER':    'NodeSocketShader',
    'RGBA':      'NodeSocketColor',
    'VECTOR':    'NodeSocketVector',
    'VALUE':     'NodeSocketFloat',
    'STRING':    'NodeSocketString',
    'INT':       'NodeSocketInt',
    'BOOLEAN':   'NodeSocketBool',
    'ROTATION':  'NodeSocketRotation',
    'GEOMETRY':  'NodeSocketGeometry',
    'OBJECT':    'NodeSocketObject',
    'COLLECTION':'NodeSocketCollection',
    'MATERIAL':  'NodeSocketMaterial',
    'TEXTURE':   'NodeSocketTexture',
    'IMAGE':     'NodeSocketImage',
    'MATRIX':    'NodeSocketMatrix',
    'CUSTOM':    'NodeSocketVirtual',
}

sk_types_no_convert = ['MENU', 'STRING', 'GEOMETRY', 'OBJECT', 'COLLECTION', 'MATERIAL', 'TEXTURE', 'IMAGE', 'BUNDLE', 'CLOSURE','FONT','SOUND','MASK','SCENE']

base_types = ['VALUE', 'RGBA', 'VECTOR', 'INT_VECTOR', 'INT', 'BOOLEAN', "SHADER"]

implicit_convert_map = {
        "BOOLEAN" : base_types,
        "VALUE" : base_types,
        "INT" : base_types,
        "VECTOR" : base_types + ['ROTATION'],
        "INT_VECTOR" : base_types + ['ROTATION'], # todo 不确定是否支持
        "RGBA" : base_types,
        "MATRIX" : ["ROTATION"],
        "ROTATION" : ["MATRIX", "VECTOR"],
}

set_utilTypeSkFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION', 'STRING', 'MATRIX'}       # Alt D 等多个操作 支持的接口

set_classicSocketsBlid = {
    'NodeSocketShader',
    'NodeSocketColor',
    'NodeSocketVector',
    'NodeSocketFloat',
    'NodeSocketString',
    'NodeSocketInt',
    'NodeSocketBool',
    'NodeSocketRotation',
    'NodeSocketGeometry',
    'NodeSocketObject',
    'NodeSocketCollection',
    'NodeSocketMaterial',
    'NodeSocketTexture',
    'NodeSocketImage',
    'NodeSocketMatrix',
}

# 新建接口-用到了
set_utilEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput',
                                 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput',
                                 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                                 'GeometryNodeMenuSwitch', 'GeometryNodeBake',
                                 'GeometryNodeCaptureAttribute', 'GeometryNodeIndexSwitch'
                                 }
inline_socket_node_list = [ # 自动隐藏接口优化-inline
                            'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput',
                            'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                            'GeometryNodeForeachGeometryElementInput', 'GeometryNodeForeachGeometryElementOutput',
                            'GeometryNodeCaptureAttribute',
                            ]

dict_skTypeHandSolderingColor = { # 用于 VQMT.
    'BOOLEAN':    (0.800000011920929,   0.6499999761581421,  0.8399999737739563,  1.0),
    'COLLECTION': (0.9599999785423279,  0.9599999785423279,  0.9599999785423279,  1.0),
    'RGBA':       (0.7799999713897705,  0.7799999713897705,  0.1599999964237213,  1.0),
    'VALUE':      (0.6299999952316284,  0.6299999952316284,  0.6299999952316284,  1.0),
    'GEOMETRY':   (0.0,                 0.8399999737739563,  0.6399999856948853,  1.0),
    'IMAGE':      (0.38999998569488525, 0.2199999988079071,  0.38999998569488525, 1.0),
    'INT':        (0.3499999940395355,  0.550000011920929,   0.36000001430511475, 1.0),
    'MATERIAL':   (0.9200000166893005,  0.46000000834465027, 0.5099999904632568,  1.0),
    'OBJECT':     (0.9300000071525574,  0.6200000047683716,  0.36000001430511475, 1.0),
    'ROTATION':   (0.6499999761581421,  0.38999998569488525, 0.7799999713897705,  1.0),
    'SHADER':     (0.38999998569488525, 0.7799999713897705,  0.38999998569488525, 1.0),
    'STRING':     (0.4399999976158142,  0.699999988079071,   1.0,                 1.0),
    'TEXTURE':    (0.6200000047683716,  0.3100000023841858,  0.6399999856948853,  1.0),
    'VECTOR':     (0.38999998569488525, 0.38999998569488525, 0.7799999713897705,  1.0),
    'CUSTOM':     (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 1.0) }

node_support_all_gn_sk = ('GeometryNodeSwitch', 'GeometryNodeIndexSwitch', 'GeometryNodeMenuSwitch')
_support_data_type = node_support_all_gn_sk + ('FunctionNodeCompare', 'ShaderNodeMix')

mixer_default: dict[str, tuple[str]] = {
    'ShaderNodeTree':     ('GeometryNodeMenuSwitch', ),
    'GeometryNodeTree':   node_support_all_gn_sk,
    'CompositorNodeTree': ('GeometryNodeMenuSwitch', ),
}

# geo_sk_type = [
#     'VALUE', 'RGBA', 'VECTOR', 'STRING', 'INT', 'BOOLEAN', 'ROTATION', 'MATRIX',
#     'OBJECT', 'MATERIAL', 'COLLECTION', 'TEXTURE', 'IMAGE', 'GEOMETRY', 'BUNDLE', 'CLOSURE'
# ]

SEPARATE = 'MixerItemsSeparator123'               # 字符串比较后当 separator()
# 新接口类型的Mix饼菜单
# 顺序很重要; 最常用的 (在此列表中) 优先显示 (MixRGB 除外).
mixer_tree_sk_nodes: dict[str, dict[str, tuple[str]]] = {
        'ShaderNodeTree':     {
                'SHADER':     ('ShaderNodeMixShader', 'ShaderNodeAddShader'),
                'VALUE':      ('ShaderNodeCombineXYZ', 'ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath'),
                'RGBA':       ('ShaderNodeMixRGB',  'ShaderNodeMix'),
                'VECTOR':     ('ShaderNodeMixRGB',  'ShaderNodeMix',                                       'ShaderNodeVectorMath'),
                'INT':        ('ShaderNodeCombineXYZ', 'ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath')},
                ##
        'GeometryNodeTree':   {
                'VALUE':      node_support_all_gn_sk + ( 'ShaderNodeMix', 'ShaderNodeCombineXYZ', 'FunctionNodeCompare', 'ShaderNodeMath'),
                'RGBA':       _support_data_type,
                'VECTOR':     _support_data_type+ ('ShaderNodeVectorMath', ),
                'STRING':     node_support_all_gn_sk + ('FunctionNodeCompare', 'GeometryNodeStringJoin',
                                                   'FunctionNodeStringLength', 'FunctionNodeReplaceString', ),
                'INT':        node_support_all_gn_sk + ( 'ShaderNodeMix', 'ShaderNodeCombineXYZ', 'FunctionNodeCompare', 'ShaderNodeMath'),
                'BOOLEAN':    _support_data_type+ ( 'ShaderNodeMath',                       'FunctionNodeBooleanMath'),
                'ROTATION':   node_support_all_gn_sk + ( 'ShaderNodeMix', ),
                'MATRIX':     node_support_all_gn_sk + ( 'FunctionNodeMatrixMultiply', SEPARATE,
                                'FunctionNodeTransposeMatrix', 'FunctionNodeInvertMatrix', 'FunctionNodeMatrixDeterminant', SEPARATE,
                                'FunctionNodeTransformPoint', 'FunctionNodeTransformDirection', 'FunctionNodeProjectPoint', SEPARATE,
                                'FunctionNodeSeparateTransform', 'FunctionNodeSeparateMatrix'),
                'GEOMETRY':   node_support_all_gn_sk + ('GeometryNodeJoinGeometry', 'GeometryNodeInstanceOnPoints', 'GeometryNodeCurveToMesh',
                                                   'GeometryNodeMeshBoolean', 'GeometryNodeGeometryToInstance')},
                ##
        'CompositorNodeTree': {
                'VALUE':      ('ShaderNodeMix', SEPARATE, 'ShaderNodeCombineXYZ' , 'ShaderNodeMath',      'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView'),
                'RGBA':       ('ShaderNodeMix', SEPARATE, 'CompositorNodeAlphaOver', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView'),
                'VECTOR':     ('ShaderNodeMix', SEPARATE,                           'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView'),
                'INT':        ('ShaderNodeMix', SEPARATE, 'ShaderNodeCombineXYZ', 'ShaderNodeMath',      'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView')},
                                ##
        'TextureNodeTree':    {
                'VALUE':       ('ShaderNodeCombineXYZ' , 'TextureNodeMixRGB', 'TextureNodeTexture', 'TextureNodeMath'),
                'RGBA':       ('TextureNodeMixRGB', 'TextureNodeTexture'),
                'VECTOR':     ('TextureNodeMixRGB',                                        'TextureNodeDistance'),
                'INT':        ('TextureNodeMixRGB', 'TextureNodeTexture', 'TextureNodeMath')}}

# ! 混合饼菜单在这里加不如改进 VoronoiLinker和NodePie联动
# 按一次Shift 多一个接口
dict_vmtMixerNodesDefs = { # '-1' 表示这里的视觉标记，它们的连接套接字是自动计算的（参见 |2|），而不是在此列表中明确指定
        # 按照上面“数据库”中的数量排序。        加空格是防止翻译的
        'GeometryNodeSwitch':             (-1, -1, 'Switch  '),
        'ShaderNodeMix':                  (-1, -1, 'Mix  '),
        'FunctionNodeCompare':            (-1, -1, 'Compare  '),
        'ShaderNodeMath':                 (0, 1, 'Max Float '),
        'ShaderNodeMixRGB':               (1, 2, 'Mix RGB '),
        'ShaderNodeMix':           (1, 2, 'Mix '),
        'CompositorNodeSwitch':           (0, 1, 'Switch '),
        'CompositorNodeSplitViewer':      (0, 1, 'Split Viewer '),
        'CompositorNodeSwitchView':       (0, 1, 'Switch View '),
        'TextureNodeMixRGB':              (1, 2, 'Mix '),
        'TextureNodeTexture':             (0, 1, 'Texture '),
        'ShaderNodeVectorMath':           (0, 1, 'Max Vector '),
        'ShaderNodeMath':             (0, 1, 'Max Float '),
        'TextureNodeMath':                (0, 1, 'Max Float '),
        'ShaderNodeMixShader':            (1, 2, 'Mix Shader '),
        'ShaderNodeAddShader':            (0, 1, 'Add Shader '),
        'GeometryNodeIndexSwitch':        (1, 2, 'Index Switch '),
        'GeometryNodeMenuSwitch':         (1, 2, 'Menu Switch  '),
        'ShaderNodeCombineXYZ':           (0, 1, 'Combine XYZ'),
        # 字符串接口 Alt Shift 左键
        'GeometryNodeStringJoin':         (1, 1, 'Join String '),
        'FunctionNodeStringLength':       (0, 0, 'String Length '),
        'FunctionNodeReplaceString':      (0, 1, 'Replace String '),
        # .......................................
        'FunctionNodeBooleanMath':        (0, 1, 'Or '),
        'CompositorNodeAlphaOver':        (1, 2, 'Alpha Over '),
        'TextureNodeDistance':            (0, 1, 'Distance '),
        'GeometryNodeJoinGeometry':       (0, 0, 'Join '),
        'GeometryNodeInstanceOnPoints':   (0, 2, 'Instance on Points '),
        'GeometryNodeCurveToMesh':        (0, 1, 'Curve to Mesh '),
        'GeometryNodeMeshBoolean':        (0, 1, 'Boolean '),
        'GeometryNodeGeometryToInstance': (0, 0, 'To Instance '),
        'FunctionNodeMatrixMultiply':     (0, 1, 'Multiply'),
        'FunctionNodeTransposeMatrix':    (0, 0, 'Transpose Matrix'),
        'FunctionNodeInvertMatrix':       (0, 0, 'Invert Matrix'),
        'FunctionNodeTransformPoint':     (1, 0, 'Transform Point'),
        'FunctionNodeTransformDirection': (1, 0, 'Transform Direction'),
        'FunctionNodeProjectPoint':       (1, 0, 'Project Point'),
        'FunctionNodeMatrixDeterminant':  (0, 0, 'Determinant'),
        'FunctionNodeSeparateTransform':  (0, 0, 'Separate Transform'),
        'FunctionNodeSeparateMatrix':     (0, 0, 'Separate Matrix'),
        'FunctionNodeCombineTransform':   (0, 1, 'Combine Transform'),
        'FunctionNodeCombineMatrix':      (0, 1, 'Combine Matrix'),
        }


# 快速数学运算.
# 通过 VL 的强大功能获取具有所需操作和自动套接字连接的节点。
# 令人意想不到的是，饼菜单可以绘制普通的布局。因此，添加了额外的“控制”饼菜单类型。
# 我自己也会用它，因为双层饼菜单节省的时间仍然无法让我得到休息。

# 双层饼菜单重要的美学价值是：选项视觉上不那么拥挤。它一次只显示 8 个选项，而不是一次性全部显示。

# TODO00 随着它的流行，看看谁在使用快速饼菜单，然后如果它不必要，就删除它；如此吹嘘它是毫无意义的。也许可以在 BA 上做个调查（投票）。
# 给我自己的备注：天哪，保持双层饼菜单的支持，因为它的美学。但每次都越来越想把它删掉 D:

# 我试图遵守一定的逻辑顺序，而不是随意放置它们。例如，将意义上对立的对放置在相对的位置。
# Blender 的饼菜单按以下方式排列元素：左、右、下、上，然后是经典的逐行填充。
# 除了那些非常明显的原始类型（右 - 加 - add，左 - 减 - sub；就像数轴一样），我的左边和下边比反面更简单。
# 例如，length 比 distance 简单。所有其他不明显且非轴向的元素都随意放置。

tup_vqmtQuickMathMapValue = (
        ('Advanced ',              ('SQRT',       'POWER',        'EXPONENT',   'LOGARITHM',   'INVERSE_SQRT', 'PINGPONG',    'FLOORED_MODULO' )),
        ('Compatible Primitives ', ('SUBTRACT',   'ADD',          'DIVIDE'   ,  'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ('Rounding ',              ('SMOOTH_MIN', 'SMOOTH_MAX',   'LESS_THAN',  'GREATER_THAN', 'SIGN',        'COMPARE',     'TRUNC',  'ROUND')),
        ('Compatible Vector ',     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACT',       'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ('', ()), # 重要的是重复和顺序，所以是列表而不是字典。
        ('', ()),
        ('', ()),
        ('Other ',                 ('COSH',       'RADIANS',      'DEGREES',    'SINH',        'TANH'                                         )),
        ('Trigonometric ',         ('SINE',       'COSINE',       'TANGENT',    'ARCTANGENT',  'ARCSINE',     'ARCCOSINE',   'ARCTAN2'        )) )
tup_vqmtQuickMathMapVector = (
        ('Advanced ',              ('SCALE',      'NORMALIZE',    'LENGTH',     'DISTANCE',    'SINE',        'COSINE',      'TANGENT'        )),
        ('Compatible Primitives ', ('SUBTRACT',   'ADD',          'DIVIDE',     'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ('Rays ',                  ('DOT_PRODUCT', 'CROSS_PRODUCT', 'PROJECT',    'FACEFORWARD', 'REFRACT',     'REFLECT'                       )),
        ('Compatible Vector ',     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACTION',    'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ('', ()),
        ('', ()),
        ('', ()),
        ('', ()) )
tup_vqmtQuickMathMapBoolean = (
        ('High ',  ('NOR', 'NAND', 'XNOR', 'XOR', 'IMPLY', 'NIMPLY')),
        ('Basic ', ('OR', 'AND', 'NOT'                        )) )
tup_vqmtQuickModeMapColor = (
        # 对于 'MIX' 操作，请使用 VMT。
        ('Math ', ('SUBTRACT', 'ADD',       'DIVIDE', 'MULTIPLY', 'DIFFERENCE', 'EXCLUSION'                    )), #'EXCLUSION' 不适合放在 'Art' 里; 最好知道它的目的。
        ('Art ',  ('DARKEN',  'LIGHTEN', '   DODGE', 'SCREEN',  'SOFT_LIGHT', 'LINEAR_LIGHT', 'BURN', 'OVERLAY')),
        ('Raw ',  ('VALUE',   'SATURATION', 'HUE',   'COLOR'                                                )) ) # 曾想改名为“Overwrite”，但改变了主意。
dict_vqmtQuickMathMain = {
        'VALUE':   tup_vqmtQuickMathMapValue,
        'VECTOR':  tup_vqmtQuickMathMapVector,
        'BOOLEAN': tup_vqmtQuickMathMapBoolean,
        'RGBA':    tup_vqmtQuickModeMapColor}
# 节点类型与编辑器和套接字类型的关联
dict_vqmtEditorNodes = {
        'VALUE':   {'ShaderNodeTree':     'ShaderNodeMath',
                    'GeometryNodeTree':   'ShaderNodeMath',
                    'CompositorNodeTree': 'ShaderNodeMath',
                    'TextureNodeTree':    'TextureNodeMath'},
        ##
        'VECTOR':  {'ShaderNodeTree':     'ShaderNodeVectorMath',
                    'GeometryNodeTree':   'ShaderNodeVectorMath',
                    'CompositorNodeTree': 'ShaderNodeVectorMath',
                    },
        ##
        'BOOLEAN': {'GeometryNodeTree':   'FunctionNodeBooleanMath'},
        'INT':     {'GeometryNodeTree':   'FunctionNodeIntegerMath'},
        ##
        'RGBA':    {'ShaderNodeTree':     'ShaderNodeMix',
                    'GeometryNodeTree':   'ShaderNodeMix',
                    'CompositorNodeTree': 'ShaderNodeMix',
                    'TextureNodeTree':    'TextureNodeMixRGB'} }
# 根据操作的套接字默认值
dict_vqmtDefaultValueOperation = {
        'VALUE': {'MULTIPLY':(1.0, 1.0, 1.0),
                  'DIVIDE':  (1.0, 1.0, 1.0),
                  'POWER':   (2.0, 1/3, 0.0),
                  'SQRT':    (2.0, 2.0, 2.0),
                  'ARCTAN2': (pi, pi, pi)},
        'INT':   {'ADD':      (0, 1, 0),
                  'SUBTRACT': (0, 1, 0),
                  'MODULO':   (0, 2, 0),
                  'MULTIPLY': (0, 2, 0),
                },
        'VECTOR': {'MULTIPLY':     ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'DIVIDE':       ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'CROSS_PRODUCT':( (0,0,1), (0,0,1), (0,0,1), 1.0 ),
                   'SCALE':        ( (0,0,0), (0,0,0), (0,0,0), pi )},
        'BOOLEAN': {'AND': (True, True),
                    'NOR': (True, True),
                    'XOR': (False, True),
                    'XNOR': (False, True),
                    'IMPLY': (True, False),
                    'NIMPLY': (True, False)},
        'RGBA': {'ADD':       ( (0,0,0,1), (0,0,0,1) ),
                 'SUBTRACT':  ( (0,0,0,1), (0,0,0,1) ),
                 'MULTIPLY':  ( (1,1,1,1), (1,1,1,1) ),
                 'DIVIDE':    ( (1,1,1,1), (1,1,1,1) ),
                 'DIFFERENCE':( (0,0,0,1), (1,1,1,1) ),
                 'EXCLUSION': ( (0,0,0,1), (1,1,1,1) ),
                 'VALUE':     ( (1,1,1,1), (1,1,1,1) ),
                 'SATURATION':( (1,1,1,1), (0,0,1,1) ),
                 'HUE':       ( (1,1,1,1), (0,1,0,1) ),
                 'COLOR':     ( (1,1,1,1), (1,0,0,1) )} }
dict_vqmtDefaultDefault = { # 可以保持不变，但我仍然将其归零。VQMT 是为了什么而创建的？
        # 注意：基于节点类型，而不是套接字类型。幸运的是它们是相同的。
        'VALUE': (0.0, 0.0, 0.0),
        'INT': (0, 0, 0),
        'VECTOR': ((0,0,0), (0,0,0), (0,0,0), 0.0),
        'BOOLEAN': (False, False),
        'RGBA': ( (.25,.25,.25,1), (.5,.5,.5,1) ) }
dict_vqmtQuickPresets = {
        'VALUE': {'ADD|x|x': 'x + x',
                  'MULTIPLY|x|x': 'x * x',
                  'SUBTRACT|0|x': '-x', #'x * -1'
                  'DIVIDE|1|x': '1 / x',
                  'SUBTRACT|1|x': '1 - x',
                  #'ADD|x|0.5': 'x + 0.5',
                  #'SUBTRACT|x|0.5': 'x - 0.5',
                  'ADD|x|6.283185307179586': 'x + tau',
                  'ADD|x|3.141592653589793': 'x + pi',
                  'ADD|x|1.5707963267948966': 'x + pi/2'},
        'VECTOR': {'ADD|x|x': 'x + x',
                   'MULTIPLY|x|x': 'x * x',
                   'SUBTRACT|0,0,0|x': '-x', #'x * -1'
                   'DIVIDE|1,1,1|x': '1 / x',
                   'SUBTRACT|x|0.5,0.5,0': 'x - (0.5, 0.5)',
                   'ADD|x|pi*2,pi*2,pi*2': 'x + tau',
                   'ADD|x|pi,pi,pi': 'x + pi',
                   'ADD|x|pi/2,pi/2,pi/2': 'x + pi/2'} }


AllQuickDimensions = {
        'ShaderNodeTree':    {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('ShaderNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ', 'ShaderNodeCombineColor'),
                              'INT':      ('ShaderNodeCombineXYZ',),
                              'BUNDLE':   ('NodeSeparateBundle', ),
                              'CLOSURE':  ('NodeEvaluateClosure', ),
                              },
        'GeometryNodeTree':  {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('FunctionNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ', 'FunctionNodeCombineColor', 'FunctionNodeQuaternionToRotation'),
                              'INT':      ('ShaderNodeCombineXYZ',),
                              'BOOLEAN':  ('ShaderNodeCombineXYZ',),
                              'STRING':   ('GeometryNodeStringToCurves',),   # Alt D 字符串接口
                              'MATRIX':   ('FunctionNodeSeparateTransform',),   # Alt D 矩阵接口
                              'ROTATION': ('FunctionNodeRotationToQuaternion',),
                              'GEOMETRY': ('GeometryNodeSeparateGeometry',), # GeometryNodeSeparateComponents更合适, 但SeparateGeometry更常用
                              'BUNDLE':   ('NodeSeparateBundle', ),
                              'CLOSURE':  ('NodeEvaluateClosure', ),
                              },

        'CompositorNodeTree':{'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('CompositorNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ', 'CompositorNodeCombineColor'),
                              'INT':      ('ShaderNodeCombineXYZ',),
                              },
        'TextureNodeTree':   {'VECTOR':   ('TextureNodeSeparateColor',),
                              'RGBA':     ('TextureNodeSeparateColor',),
                              'VALUE':    ('TextureNodeCombineColor', ''), # 无法处理缺少第二个的情况，因此留空；参见 |3|。
                              'INT':      ('TextureNodeCombineColor',),
                              }
        }

base_constant = {
        'BOOLEAN':   'FunctionNodeInputBool',
        'VALUE':     'ShaderNodeValue',
        'INT':       'FunctionNodeInputInt',
        'VECTOR':    'ShaderNodeCombineXYZ',
        'MENU':      'GeometryNodeIndexSwitch',
        'BUNDLE':    'NodeCombineBundle',
        'CLOSURE':   'NodeClosureOutput',
        'MATRIX':    'FunctionNodeCombineTransform',
        'ROTATION': ['FunctionNodeEulerToRotation',
                     'FunctionNodeAxisAngleToRotation',
                     'FunctionNodeQuaternionToRotation' ],
        'OBJECT':    'GeometryNodeInputObject',
}

geo_constant = {
    'RGBA': 'FunctionNodeInputColor',
    'STRING': 'FunctionNodeInputString',
    'MATERIAL': 'GeometryNodeInputMaterial',
    'COLLECTION': 'GeometryNodeInputCollection',
    'IMAGE': 'GeometryNodeInputImage',
}
geo_constant.update(base_constant)

shader_constant = {
    'RGBA':      'ShaderNodeRGB',
}
shader_constant.update(base_constant)

cmp_constant = {
    'RGBA': 'CompositorNodeRGB',
}
cmp_constant.update(base_constant)


AllQuickConstant: dict[str, dict[str, str | list]] = {
        'GeometryNodeTree':  geo_constant,
        'ShaderNodeTree':    shader_constant,
        'CompositorNodeTree':cmp_constant,
        'TextureNodeTree':   { }
        }
