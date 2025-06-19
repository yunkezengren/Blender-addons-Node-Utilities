from math import pi, cos, sin

Color_Bar_Width = 0.015     # 小王 饼菜单颜色条宽度
Cursor_X_Offset = -50       # 小王 这样更舒服,在输入或输出接口方面加强


dict_typeSkToBlid = {
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

set_utilTypeSkFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION', 'STRING', 'MATRIX'}       # 小王-Alt D 等多个操作 支持的接口

set_classicSocketsBlid = {'NodeSocketShader',  'NodeSocketColor',   'NodeSocketVector','NodeSocketFloat',     'NodeSocketString',  'NodeSocketInt',    'NodeSocketBool',
                            'NodeSocketRotation','NodeSocketGeometry','NodeSocketObject','NodeSocketCollection','NodeSocketMaterial','NodeSocketTexture','NodeSocketImage',
                            'NodeSocketMatrix'}

# 小王-新建接口-用到了
set_utilEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 
                                 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 
                                 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                                 'GeometryNodeMenuSwitch', 'GeometryNodeBake',
                                 'GeometryNodeCaptureAttribute', 'GeometryNodeIndexSwitch'
                                 }
inline_socket_node_list = [ # 小王-自动隐藏接口优化-inline
                            'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 
                            'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput',
                            'GeometryNodeForeachGeometryElementInput', 'GeometryNodeForeachGeometryElementOutput', 
                            'GeometryNodeCaptureAttribute',
                            ]

set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}

dict_skTypeHandSolderingColor = { #Для VQMT.
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


vmtSep = 'MixerItemsSeparator123'
# 小王-新接口类型的Mix饼菜单
dict_vmtTupleMixerMain = { #Порядок важен; самые частые (в этом списке) идут первее (кроме MixRGB).
        'ShaderNodeTree':     {'SHADER':     ('ShaderNodeMixShader','ShaderNodeAddShader'),
                               'VALUE':      ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath'),
                               'RGBA':       ('ShaderNodeMixRGB',  'ShaderNodeMix'),
                               'VECTOR':     ('ShaderNodeMixRGB',  'ShaderNodeMix',                                       'ShaderNodeVectorMath'),
                               'INT':        ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath')},
                               ##
        'GeometryNodeTree':   {'VALUE':      ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'RGBA':       ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare'),
                               'VECTOR':     ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare',                 'ShaderNodeVectorMath'),
                               'STRING':     ('GeometryNodeSwitch',                'FunctionNodeCompare',
                                              'GeometryNodeStringJoin',   # 小王-字符串接口 Alt Shift 左键
                                              "FunctionNodeStringLength", "FunctionNodeReplaceString", ),
                               'INT':        ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'BOOLEAN':    ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath',                       'FunctionNodeBooleanMath'),
                               'ROTATION':   ('GeometryNodeSwitch','ShaderNodeMix'),
                               'MATRIX':     ('GeometryNodeSwitch', 
                                              "FunctionNodeMatrixMultiply", "FunctionNodeInvertMatrix", 
                                              "FunctionNodeTransformPoint", "FunctionNodeTransformDirection", "FunctionNodeProjectPoint",
                                              "FunctionNodeMatrixDeterminant",),
                               'OBJECT':     ('GeometryNodeSwitch',),
                               'MATERIAL':   ('GeometryNodeSwitch',),
                               'COLLECTION': ('GeometryNodeSwitch',),
                               'TEXTURE':    ('GeometryNodeSwitch',),
                               'IMAGE':      ('GeometryNodeSwitch',),
                               'GEOMETRY':   ('GeometryNodeSwitch','GeometryNodeJoinGeometry','GeometryNodeInstanceOnPoints','GeometryNodeCurveToMesh','GeometryNodeMeshBoolean','GeometryNodeGeometryToInstance')},
                               ##
        'CompositorNodeTree': {'VALUE':      ('CompositorNodeMath',     vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'RGBA':       ('CompositorNodeAlphaOver',vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'VECTOR':     (                          vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'INT':        ('CompositorNodeMath',     vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView')},
                               ##
        'TextureNodeTree':    {'VALUE':      ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath'),
                               'RGBA':       ('TextureNodeMixRGB','TextureNodeTexture'),
                               'VECTOR':     ('TextureNodeMixRGB',                                        'TextureNodeDistance'),
                               'INT':        ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath')}}
dict_vmtMixerNodesDefs = { #'-1' означают визуальную здесь метку, что их сокеты подключения высчитываются автоматически (см. |2|), а не указаны явно в этом списке
        #Отсортировано по количеству в "базе данных" выше.
        'GeometryNodeSwitch':             (-1, -1, "Switch  "),
        'ShaderNodeMix':                  (-1, -1, "Mix  "),
        'FunctionNodeCompare':            (-1, -1, "Compare  "),
        'ShaderNodeMath':                 (0, 1, "Max Float "),
        'ShaderNodeMixRGB':               (1, 2, "Mix RGB "),
        'CompositorNodeMixRGB':           (1, 2, "Mix Col "),
        'CompositorNodeSwitch':           (0, 1, "Switch "),
        'CompositorNodeSplitViewer':      (0, 1, "Split Viewer "),
        'CompositorNodeSwitchView':       (0, 1, "Switch View "),
        'TextureNodeMixRGB':              (1, 2, "Mix Col "),
        'TextureNodeTexture':             (0, 1, "Texture "),
        'ShaderNodeVectorMath':           (0, 1, "Max Vector "),
        'CompositorNodeMath':             (0, 1, "Max Float "),
        'TextureNodeMath':                (0, 1, "Max Float "),
        'ShaderNodeMixShader':            (1, 2, "Mix Shader "),
        'ShaderNodeAddShader':            (0, 1, "Add Shader "),
        # 小王-字符串接口 Alt Shift 左键
        'GeometryNodeStringJoin':         (1, 1, "Join String "),
        "FunctionNodeStringLength":       (0, 0, "String Length "),
        "FunctionNodeReplaceString":      (0, 1, "Replace String "),
        # .......................................
        'FunctionNodeBooleanMath':        (0, 1, "Or "),
        'CompositorNodeAlphaOver':        (1, 2, "Alpha Over "),
        'TextureNodeDistance':            (0, 1, "Distance "),
        'GeometryNodeJoinGeometry':       (0, 0, "Join "),
        'GeometryNodeInstanceOnPoints':   (0, 2, "Instance on Points "),
        'GeometryNodeCurveToMesh':        (0, 1, "Curve to Mesh "),
        'GeometryNodeMeshBoolean':        (0, 1, "Boolean "),
        'GeometryNodeGeometryToInstance': (0, 0, "To Instance "),
        'FunctionNodeMatrixMultiply':     (0, 1, "Multiply"),
        'FunctionNodeInvertMatrix':       (0, 0, "Invert"),
        'FunctionNodeTransformPoint':     (1, 0, "Transform Point"),
        'FunctionNodeTransformDirection': (1, 0, "Transform Direction"),
        'FunctionNodeProjectPoint':       (1, 0, "Project Point"),
        'FunctionNodeMatrixDeterminant':  (0, 0, "Determinant"),
        }


#Быстрая математика.
#Заполучить нод с нужной операцией и автоматическим соединением в сокеты, благодаря мощностям VL'а.
#Неожиданно для меня оказалось, что пирог может рисовать обычный layout. От чего добавил дополнительный тип пирога "для контроля".
#А также сам буду пользоваться им, потому что за то время, которое экономится при двойном пироге, отдохнуть как-то всё равно не получается.

#Важная эстетическая ценность двойного пирога -- визуальная неперегруженность вариантами. Вместо того, чтобы вываливать всё сразу, показываются только по 8 штук за раз.

#todo00 с приходом популярности, посмотреть кто использует быстрый пирог, а потом аннигилировать его за ненадобностью; настолько распинаться о нём было бессмысленно. Мб опрос(голосование) сделать на BA.
#Заметка для меня: сохранять поддержку двойного пирога чёрт возьми, ибо эстетика. Но выпилить его с каждым разом хочется всё больше D:

#Было бы бездумно разбросать их как попало, поэтому я пытался соблюсти некоторую логическую последовательность. Например, расставляя пары по смыслу диаметрально противоположными.
#Пирог Блендера располагает в себе элементы следующим образом: лево, право, низ, верх, после чего классическое построчное заполнение.
#"Compatible..." -- чтобы у векторов и у математики одинаковые операции были на одинаковых местах (кроме тригонометрических).
#За исключением примитивов, где прослеживается супер очевидная логика (право -- плюс -- add, лево -- минус -- sub; всё как на числовой оси), лево и низ у меня более простые, чем обратная сторона.
#Например, length проще, чем distance. Всем же остальным не очевидным и не осе-ориентированным досталось как получится.

tup_vqmtQuickMathMapValue = (
        ("Advanced ",              ('SQRT',       'POWER',        'EXPONENT',   'LOGARITHM',   'INVERSE_SQRT','PINGPONG',    'FLOORED_MODULO' )),
        ("Compatible Primitives ", ('SUBTRACT',   'ADD',          'DIVIDE'   ,  'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ("Rounding ",              ('SMOOTH_MIN', 'SMOOTH_MAX',   'LESS_THAN',  'GREATER_THAN','SIGN',        'COMPARE',     'TRUNC',  'ROUND')),
        ("Compatible Vector ",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACT',       'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ("", ()), #Важны дубликаты и порядок, поэтому не словарь а список.
        ("", ()),
        ("Other ",                 ('COSH',       'RADIANS',      'DEGREES',    'SINH',        'TANH'                                         )),
        ("Trigonometric ",         ('SINE',       'COSINE',       'TANGENT',    'ARCTANGENT',  'ARCSINE',     'ARCCOSINE',   'ARCTAN2'        )) )
tup_vqmtQuickMathMapVector = (
        ("Advanced ",              ('SCALE',      'NORMALIZE',    'LENGTH',     'DISTANCE',    'SINE',        'COSINE',      'TANGENT'        )),
        ("Compatible Primitives ", ('SUBTRACT',   'ADD',          'DIVIDE',     'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ("Rays ",                  ('DOT_PRODUCT','CROSS_PRODUCT','PROJECT',    'FACEFORWARD', 'REFRACT',     'REFLECT'                       )),
        ("Compatible Vector ",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACTION',    'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ("", ()),
        ("", ()),
        ("", ()),
        ("", ()) )
tup_vqmtQuickMathMapBoolean = (
        ("High ",  ('NOR','NAND','XNOR','XOR','IMPLY','NIMPLY')),
        ("Basic ", ('OR', 'AND', 'NOT'                        )) )
tup_vqmtQuickModeMapColor = (
        #Для операции 'MIX' используйте VMT.
        ("Math ", ('SUBTRACT','ADD',       'DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION'                    )), #'EXCLUSION' не влез в "Art"; и было бы неплохо узнать его предназначение.
        ("Art ",  ('DARKEN',  'LIGHTEN','   DODGE', 'SCREEN',  'SOFT_LIGHT','LINEAR_LIGHT','BURN','OVERLAY')),
        ("Raw ",  ('VALUE',   'SATURATION','HUE',   'COLOR'                                                )) ) #Хотел переназвать на "Overwrite", но передумал.
dict_vqmtQuickMathMain = {
        'VALUE':   tup_vqmtQuickMathMapValue,
        'VECTOR':  tup_vqmtQuickMathMapVector,
        'BOOLEAN': tup_vqmtQuickMathMapBoolean,
        'RGBA':    tup_vqmtQuickModeMapColor}
#Ассоциация нода для типа редактора и сокета
dict_vqmtEditorNodes = {
        'VALUE':   {'ShaderNodeTree':     'ShaderNodeMath',
                    'GeometryNodeTree':   'ShaderNodeMath',
                    'CompositorNodeTree': 'CompositorNodeMath',
                    'TextureNodeTree':    'TextureNodeMath'},
        ##
        'VECTOR':  {'ShaderNodeTree':     'ShaderNodeVectorMath',
                    'GeometryNodeTree':   'ShaderNodeVectorMath'},
        ##
        'BOOLEAN': {'GeometryNodeTree':   'FunctionNodeBooleanMath'},
        'INT':     {'GeometryNodeTree':   'FunctionNodeIntegerMath'},
        ##
        'RGBA':    {'ShaderNodeTree':     'ShaderNodeMix',
                    'GeometryNodeTree':   'ShaderNodeMix',
                    'CompositorNodeTree': 'CompositorNodeMixRGB',
                    'TextureNodeTree':    'TextureNodeMixRGB'} }
#Значения по умолчанию для сокетов в зависимости от операции
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
dict_vqmtDefaultDefault = { #Можно было оставить без изменений, но всё равно обнуляю. Ради чего был создан VQMT?.
        #Заметка: Основано на типе нода, а не на типе сокета. Повезло, что они одинаковые.
        'VALUE': (0.0, 0.0, 0.0),
        'INT': (0, 0, 0),
        'VECTOR': ((0,0,0), (0,0,0), (0,0,0), 0.0),
        'BOOLEAN': (False, False),
        'RGBA': ( (.25,.25,.25,1), (.5,.5,.5,1) ) }
dict_vqmtQuickPresets = {
        'VALUE': {"ADD|x|x": "x + x",
                  "MULTIPLY|x|x": "x * x",
                  "SUBTRACT|0|x": "-x", #"x * -1"
                  "DIVIDE|1|x": "1 / x",
                  "SUBTRACT|1|x": "1 - x",
                  #"ADD|x|0.5": "x + 0.5",
                  #"SUBTRACT|x|0.5": "x - 0.5",
                  "ADD|x|6.283185307179586": "x + tau",
                  "ADD|x|3.141592653589793": "x + pi",
                  "ADD|x|1.5707963267948966": "x + pi/2"},
        'VECTOR': {"ADD|x|x": "x + x",
                   "MULTIPLY|x|x": "x * x",
                   "SUBTRACT|0,0,0|x": "-x", #"x * -1"
                   "DIVIDE|1,1,1|x": "1 / x",
                   "SUBTRACT|x|0.5,0.5,0": "x - (0.5, 0.5)",
                   "ADD|x|pi*2,pi*2,pi*2": "x + tau",
                   "ADD|x|pi,pi,pi": "x + pi",
                   "ADD|x|pi/2,pi/2,pi/2": "x + pi/2"} }


dict_vqdtQuickDimensionsMain = {
        'ShaderNodeTree':    {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('ShaderNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ','ShaderNodeCombineColor'),
                              'INT':      ('ShaderNodeCombineXYZ',)},
        'GeometryNodeTree':  {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('FunctionNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ','FunctionNodeCombineColor','FunctionNodeQuaternionToRotation'),
                              'INT':      ('ShaderNodeCombineXYZ',),
                              'BOOLEAN':  ('ShaderNodeCombineXYZ',),
                              'STRING':   ('GeometryNodeStringToCurves',),   # 小王-Alt D 字符串接口
                              'MATRIX':   ('FunctionNodeSeparateTransform',),   # 小王-Alt D 矩阵接口
                              'ROTATION': ('FunctionNodeRotationToQuaternion',),
                              'GEOMETRY': ('GeometryNodeSeparateGeometry',)}, #Зато одинаковый по смыслу. Воспринимать как мини-рофл.
                            #   'GEOMETRY': ('GeometryNodeSeparateComponents',)}, #Зато одинаковый по смыслу. Воспринимать как мини-рофл.
        'CompositorNodeTree':{'VECTOR':   ('CompositorNodeSeparateXYZ',),
                              'RGBA':     ('CompositorNodeSeparateColor',),
                              'VALUE':    ('CompositorNodeCombineXYZ','CompositorNodeCombineColor'),
                              'INT':      ('CompositorNodeCombineXYZ',)},
        'TextureNodeTree':   {'VECTOR':   ('TextureNodeSeparateColor',),
                              'RGBA':     ('TextureNodeSeparateColor',),
                              'VALUE':    ('TextureNodeCombineColor',''), #Нет обработок отсутствия второго, поэтому пусто; см. |3|.
                              'INT':      ('TextureNodeCombineColor',)}}

dict_vqdtQuickConstantMain = {
        'GeometryNodeTree':  {'BOOLEAN':  'FunctionNodeInputBool',
                              'VALUE':    'ShaderNodeValue',
                              'INT':      'FunctionNodeInputInt',
                              'VECTOR':   'ShaderNodeCombineXYZ',
                              'RGBA':     'FunctionNodeInputColor',
                              'STRING':   'FunctionNodeInputString',
                              'MENU':     'GeometryNodeIndexSwitch',
                              'MATRIX':   'FunctionNodeCombineTransform',
                              'ROTATION': ["FunctionNodeEulerToRotation", 
                                           "FunctionNodeAxisAngleToRotation", 
                                           "FunctionNodeQuaternionToRotation" ]
                              }, 
        'ShaderNodeTree':    {'VALUE':    'ShaderNodeValue',
                              'VECTOR':   'ShaderNodeCombineXYZ',
                              'RGBA':     'ShaderNodeRGB'     },
        'CompositorNodeTree':{'VALUE':    'CompositorNodeValue',
                              'VECTOR':   'CompositorNodeCombineXYZ',
                              'RGBA':     'CompositorNodeRGB'     },
        'TextureNodeTree':   { }
        }











