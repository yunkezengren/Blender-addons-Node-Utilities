context_s = str
locale_s = str

_translations_dict: dict[tuple[context_s, str], dict[locale_s, str]] = {
    # Addon description
    ("*", "Various utilities for nodes connecting, based on distance field."): {
        "zh_HANS": "基于距离场的多种节点连接辅助工具。",
        "ru_RU": "Разнообразные помогалочки для соединения нодов, основанные на поле расстояний.",
    },
    ("*", "For Blender versions: "): {
        "ru_RU": "Для версий Блендера: ",
    },
    ("*", "Only .ttf or .otf format"): {
        "zh_HANS": "只支持.ttf或.otf格式",
        "ru_RU": "Только .ttf или .otf формат",
    },

    # Operators
    ("Operator", "Copy addon settings as .py script"): {
        "zh_HANS": "将插件设置复制为'.py'脚本,复制到粘贴板里",
        "ru_RU": "Скопировать настройки аддона как '.py' скрипт",
    },
    ("Operator", "Check for updates yourself"): {
        "zh_HANS": "自行检查更新",
        "ru_RU": "Проверяйте обновления самостоятельно",
    },
    ("Operator", "Restore"): {
        "zh_HANS": "恢复",
        "ru_RU": "Восстановить",
    },
    ("Operator", "Add New"): {
        "zh_HANS": "添加",
        "ru_RU": "Добавить",
    },
    ("Operator", "Auto-node"): {
        "zh_HANS": "自动节点",
        "ru_RU": "Авто-нод",
    },
    ("Operator", "For socket"): {
        "zh_HANS": "针对接口",
        "ru_RU": "Для сокета",
    },
    ("Operator", "For node"): {
        "zh_HANS": "针对节点",
        "ru_RU": "Для нода",
    },
    ("Operator", "Swap"): {
        "zh_HANS": "交换",
        "ru_RU": "Поменять",
    },
    ("Operator", "Add"): {
        "zh_HANS": "添加",
        "ru_RU": "Добавить",
    },
    ("Operator", "Transfer"): {
        "zh_HANS": "转移",
        "ru_RU": "Переместить",
    },
    ("Operator", "Copy"): {
        "zh_HANS": "复制",
        "ru_RU": "Копировать",
    },
    ("Operator", "Paste"): {
        "zh_HANS": "粘贴",
        "ru_RU": "Вставить",
    },
    ("Operator", "Flip"): {
        "zh_HANS": "移动",
        "ru_RU": "Сдвинуть",
    },
    ("Operator", "New"): {
        "zh_HANS": "新建",
        "ru_RU": "Добавить",
    },
    ("Operator", "Create"): {
        "zh_HANS": "创建",
        "ru_RU": "Создать",
    },

    # Tool labels
    ("*", "Voronoi Linker"): {
        "zh_HANS": "Voronoi快速连接",
        "ru_RU": "Voronoi Linker",
    },
    ("*", "Voronoi Preview"): {
        "zh_HANS": "Voronoi快速预览",
        "ru_RU": "Voronoi Preview",
    },
    ("*", "Voronoi Preview Anchor"): {
        "zh_HANS": "Voronoi新建预览转接点",
        "ru_RU": "Voronoi Preview Anchor",
    },
    ("*", "Voronoi Mixer"): {
        "zh_HANS": "Voronoi快速混合饼菜单",
        "ru_RU": "Voronoi Mixer",
    },
    ("*", "Voronoi Quick Math"): {
        "zh_HANS": "Voronoi快速数学运算",
        "ru_RU": "Voronoi Quick Math",
    },
    ("*", "Voronoi RANTO"): {
        "zh_HANS": "Voronoi自动对齐节点",
        "ru_RU": "Voronoi RANTO",
    },
    ("*", "Voronoi Swapper"): {
        "zh_HANS": "Voronoi交换接口连线",
        "ru_RU": "Voronoi Swapper",
    },
    ("*", "Voronoi Hider"): {
        "zh_HANS": "Voronoi快速隐藏显示接口",
        "ru_RU": "Voronoi Hider",
    },
    ("*", "Voronoi MassLinker"): {
        "zh_HANS": "Voronoi批量连接同名接口",
        "ru_RU": "Voronoi MassLinker",
    },
    ("*", "Voronoi Enum Selector"): {
        "zh_HANS": "Voronoi快速切换节点菜单选项",
        "ru_RU": "Voronoi Enum Selector",
    },
    ("*", "Voronoi Link Repeating"): {
        "zh_HANS": "Voronoi重复上次连线的输出到目标输入",
        "ru_RU": "Voronoi Link Repeating",
    },
    ("*", "Voronoi Quick Dimensions"): {
        "zh_HANS": "Voronoi快速分离/合并",
        "ru_RU": "Voronoi Quick Dimensions",
    },
    ("*", "Voronoi Quick Constant"): {
        "zh_HANS": "Voronoi快速常量",
        "ru_RU": "Voronoi Quick Constant",
    },
    ("*", "Voronoi Interfacer"): {
        "zh_HANS": "Voronoi新建交换移动接口",
        "ru_RU": "Voronoi Interfacer",
    },
    ("*", "Voronoi Links Transfer"): {
        "zh_HANS": "Voronoi移动节点连线到另一个节点",
        "ru_RU": "Voronoi Links Transfer",
    },
    ("*", "Voronoi Warper"): {
        "zh_HANS": "Voronoi聚焦某条线",
        "ru_RU": "Voronoi Warper",
    },
    ("*", "Voronoi Lazy Node Stencils"): {
        "zh_HANS": "Voronoi在材质某些矢量和颜色输入接口添加几个节点",
        "ru_RU": "Voronoi Lazy Node Stencils",
    },
    ("*", "Voronoi Reset Node"): {
        "zh_HANS": "Voronoi快速恢复节点默认参数",
        "ru_RU": "Voronoi Reset Node",
    },
    ("*", "Mixer Mixer"): {
        "zh_HANS": "混合饼菜单",
        "ru_RU": "Mixer Mixer",
    },
    ("*", "Quick Math"): {
        "zh_HANS": "快速数学运算",
        "ru_RU": "Quick Math",
    },
    ("*", "Voronoi Call Node Pie"): {
        "zh_HANS": "Voronoi联动节点饼菜单插件",
        "ru_RU": "Voronoi Call Node Pie",
    },

    # Base tool properties
    ("*", "Pass through node selecting"): {
        "zh_HANS": "单击输出接口预览(而不是自动根据鼠标位置自动预览)",
        "ru_RU": "Пропускать через выделение нода",
    },
    ("*", "Clicking over a node activates selection, not the tool"): {
        "zh_HANS": "单击输出接口才连接预览而不是根据鼠标位置动态预览",
        "ru_RU": "Клик над нодом активирует выделение, а не инструмент",
    },
    ("*", "Can between fields"): {
        "zh_HANS": "接口类型可以不一样",
        "ru_RU": "Может между полями",
    },
    ("*", "Tool can connecting between different field types"): {
        "zh_HANS": "工具可以连接不同类型的接口",
        "ru_RU": "Инструмент может искать сокеты между различными типами полей",
    },

    # Common texts
    ("*", "No mixing options"): {
        "zh_HANS": "没有可混合的选项",
        "ru_RU": "Варианты смешивания отсутствуют",
    },
    ("*", "There is nothing"): {
        "zh_HANS": "空",
        "ru_RU": "Ничего нет",
    },
    ("*", "This tool is empty"): {
        "zh_HANS": "该工具是空的",
        "ru_RU": "Этот инструмент пуст",
    },
    ("*", "Virtual"): {
        "zh_HANS": "虚拟",
        "ru_RU": "Виртуальный",
    },
    ("*", "Mode"): {
        "zh_HANS": "模式",
        "ru_RU": "Режим",
    },
    ("*", "Socket"): {
        "zh_HANS": "接口",
        "ru_RU": "Сокет",
    },
    ("*", "Pie"): {
        "zh_HANS": "饼菜单",
        "ru_RU": "Пирог",
    },
    ("*", "Special"): {
        "zh_HANS": "特殊",
        "ru_RU": "Специальное",
    },
    ("*", "Customization"): {
        "zh_HANS": "自定义",
        "ru_RU": "Кастомизация",
    },
    ("*", "Colored"): {
        "zh_HANS": "接口动态颜色:",
        "ru_RU": "Цветной",
    },

    # VMT mixer labels
    ("*", "Switch  "): {
        "zh_HANS": "S切换",
        "ru_RU": "Переключение",
    },
    ("*", "Mix  "): {
        "ru_RU": "Смешивание",
    },
    ("*", "Compare  "): {
        "zh_HANS": "C 比较",
        "ru_RU": "Сравнение",
    },
    ("*", "Max Float "): {
        "zh_HANS": "最大浮点",
        "ru_RU": "Max Float ",
    },
    ("*", "Mix RGB "): {
        "zh_HANS": "M 混合颜色",
        "ru_RU": "Mix RGB ",
    },
    ("*", "Mix "): {
        "zh_HANS": "M 混合",
        "ru_RU": "Mix ",
    },
    ("*", "Split Viewer "): {
        "zh_HANS": "分离查看器",
        "ru_RU": "Split Viewer ",
    },
    ("*", "Switch View "): {
        "zh_HANS": "切换查看",
        "ru_RU": "Switch View ",
    },
    ("*", "Texture "): {
        "zh_HANS": "纹理",
        "ru_RU": "Texture ",
    },
    ("*", "Max Vector "): {
        "zh_HANS": "最大矢量",
        "ru_RU": "Max Vector ",
    },
    ("*", "Mix Shader "): {
        "zh_HANS": "混合着色器",
        "ru_RU": "Mix Shader ",
    },
    ("*", "Add Shader "): {
        "zh_HANS": "相加着色器",
        "ru_RU": "Add Shader ",
    },
    ("*", "Index Switch "): {
        "zh_HANS": "I 索引切换",
        "ru_RU": "Index Switch ",
    },
    ("*", "Menu Switch  "): {
        "zh_HANS": "M 菜单切换",
        "ru_RU": "Menu Switch  ",
    },
    ("*", "Join String "): {
        "zh_HANS": "J 连接字符串",
        "ru_RU": "Join String ",
    },
    ("*", "String Length "): {
        "zh_HANS": "字符串长度",
        "ru_RU": "String Length ",
    },
    ("*", "Replace String "): {
        "zh_HANS": "替换字符串",
        "ru_RU": "Replace String ",
    },
    ("*", "Or "): {
        "zh_HANS": "或",
        "ru_RU": "Or ",
    },
    ("*", "Alpha Over "): {
        "zh_HANS": "Alpha叠加",
        "ru_RU": "Alpha Over ",
    },
    ("*", "Distance "): {
        "zh_HANS": "D 距离",
        "ru_RU": "Distance ",
    },
    ("*", "Join "): {
        "zh_HANS": "J 合并",
        "ru_RU": "Join ",
    },
    ("*", "Instance on Points "): {
        "zh_HANS": "实例化与点上",
        "ru_RU": "Instance on Points ",
    },
    ("*", "Curve to Mesh "): {
        "zh_HANS": "曲线转网格",
        "ru_RU": "Curve to Mesh ",
    },
    ("*", "Boolean "): {
        "zh_HANS": "布尔",
        "ru_RU": "Boolean ",
    },
    ("*", "To Instance "): {
        "zh_HANS": "G 几何转实例",
        "ru_RU": "To Instance ",
    },

    # Quick Math labels
    ("*", "Float Quick Math"): {
        "zh_HANS": "快速浮点运算",
    },
    ("*", "Vector Quick Math"): {
        "zh_HANS": "快速矢量运算",
    },
    ("*", "Integer Quick Math"): {
        "zh_HANS": "快速整数运算",
    },
    ("*", "Boolean Quick Math"): {
        "zh_HANS": "快速布尔运算",
    },
    ("*", "Matrix Quick Math"): {
        "zh_HANS": "快速矩阵运算",
    },
    ("*", "Color Quick Mode"): {
        "zh_HANS": "快速颜色运算",
    },

    # VoronoiLinkerTool
    ("*", "Repick Key"): {
        "zh_HANS": "重选快捷键",
        "ru_RU": "Клавиша перевыбора",
    },
    ("*", "Reroutes can be connected to any type"): {
        "zh_HANS": "重新定向节点可以连接到任何类型的节点",
        "ru_RU": "Рероуты могут подключаться в любой тип",
    },
    ("*", "Deselect all nodes on activate"): {
        "zh_HANS": "快速连接时取消选择所有节点",
        "ru_RU": "Снять выделение со всех нодов при активации",
    },
    ("*", "Priority ignoring"): {
        "zh_HANS": "忽略优先级",
        "ru_RU": "Приоритетное игнорирование",
    },
    ("*", "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"): {
        "zh_HANS": "在首次搜索时高级忽略\"烦人\"的接口。(目前只有图像节点的\"Alpha\"接口)",
        "ru_RU": "Высокоуровневое игнорирование \"надоедливых\" сокетов при первом поиске.\n(Сейчас только \"Alpha\"-сокет у нод изображений)",
    },
    ("*", "Selecting involved nodes"): {
        "zh_HANS": "快速连接后自动选择连接的节点",
        "ru_RU": "Выделять задействованные ноды",
    },

    # VoronoiPreviewTool
    ("*", "Select previewed node"): {
        "zh_HANS": "自动选择被预览的节点",
        "ru_RU": "Выделять предпросматриваемый нод",
    },
    ("*", "Only linked"): {
        "zh_HANS": "只预览已有连接的输出接口",
        "ru_RU": "Только подключённые",
    },
    ("*", "Trigger only on linked socket"): {
        "zh_HANS": "只预览已有连接的输出接口",
        "ru_RU": "Цепляться только на подключённые сокеты",
    },
    ("*", "Equal anchor type"): {
        "zh_HANS": "只预览同类型接口",
        "ru_RU": "Равный тип якоря",
    },
    ("*", "Trigger only on anchor type sockets"): {
        "zh_HANS": "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的接口类型一样才能被预览连接",
        "ru_RU": "Цепляться только к сокетам типа якоря",
    },
    ("*", "Allow classic GeoNodes Viewer"): {
        "zh_HANS": "几何节点里使用默认预览方式",
        "ru_RU": "Разрешить классический Viewer Геометрических узлов",
    },
    ("*", "Allow use of classic GeoNodes Viewer by clicking on node"): {
        "zh_HANS": "几何节点里使用默认预览方式",
        "ru_RU": "Разрешить использование классического Viewer'а геометрических нодов путём клика по ноду",
    },
    ("*", "Allow classic Compositor Viewer"): {
        "zh_HANS": "合成器里使用默认预览方式",
        "ru_RU": "Разрешить классический Viewer Композитора",
    },
    ("*", "Allow use of classic Compositor Viewer by clicking on node"): {
        "zh_HANS": "合成器里使用默认预览方式",
        "ru_RU": "Разрешить использование классического Viewer'а композиторных нодов путём клика по ноду",
    },
    ("*", "Live Preview"): {
        "zh_HANS": "实时预览",
        "ru_RU": "Предварительный просмотр в реальном времени",
    },
    ("*", "Real-time preview"): {
        "zh_HANS": "即使没松开鼠标也能观察预览结果",
        "ru_RU": "Предпросмотр в реальном времени",
    },
    ("*", "Node onion colors"): {
        "zh_HANS": "节点洋葱色",
        "ru_RU": "Луковичные цвета нод",
    },
    ("*", "Coloring topologically connected nodes"): {
        "zh_HANS": "快速预览时将与预览的节点有连接关系的节点全部着色显示",
        "ru_RU": "Окрашивать топологически соединённые ноды",
    },
    ("*", "Topology connected highlighting"): {
        "zh_HANS": "拓扑连接高亮",
        "ru_RU": "Подсветка топологических соединений",
    },
    ("*", "Display names of sockets whose links are connected to a node"): {
        "zh_HANS": "快速预览时高亮显示连接到预览的节点的上级节点的输出接口",
        "ru_RU": "Отображать имена сокетов, чьи линки подсоединены к ноду",
    },
    ("*", "Save preview results"): {
        "zh_HANS": "保存预览结果",
        "ru_RU": "Сохранять результаты предпросмотра",
    },
    ("*", "Create a preview through an additional node, convenient for copying"): {
        "zh_HANS": "保存预览结果,通过新建一个预览节点连接预览",
        "ru_RU": "Создавать предпросмотр через дополнительный нод, удобный для последующего копирования",
    },
    ("*", "Onion color entrance"): {
        "zh_HANS": "洋葱色入口",
        "ru_RU": "Луковичный цвет входа",
    },
    ("*", "Onion color exit"): {
        "zh_HANS": "洋葱色出口",
        "ru_RU": "Луковичный цвет выхода",
    },
    ("*", "Text scale"): {
        "zh_HANS": "文字缩放",
        "ru_RU": "Масштаб текста",
    },

    # VoronoiMixerTool
    ("*", "Can from one socket"): {
        "zh_HANS": "从一个接口连接",
        "ru_RU": "Может от одного сокета",
    },
    ("*", "Place immediately"): {
        "zh_HANS": "立即添加节点到鼠标位置",
        "ru_RU": "Размещать моментально",
    },
    ("*", "Reroutes can be mixed to any type"): {
        "zh_HANS": "快速混合不限定接口类型",
        "ru_RU": "Рероуты могут смешиваться с любым типом",
    },
    ("*", "Pie Type"): {
        "zh_HANS": "饼菜单类型",
        "ru_RU": "Тип пирога",
    },
    ("*", "Control"): {
        "zh_HANS": "控制(自定义)",
        "ru_RU": "Контроль",
    },
    ("*", "Speed"): {
        "zh_HANS": "速度型(多层菜单)",
        "ru_RU": "Скорость",
    },
    ("*", "Pie scale"): {
        "zh_HANS": "饼菜单大小",
        "ru_RU": "Размер пирога",
    },
    ("*", "Pie scale extra"): {
        "zh_HANS": "预设面板缩放",
        "ru_RU": "Размер дополнительных панелей пирога",
    },
    ("*", "Alignment between items"): {
        "zh_HANS": "项目之间的对齐方式",
        "ru_RU": "Выравнивание между элементами",
    },
    ("*", "0 – Flat.\n1 – Rounded docked.\n2 – Gap"): {
        "zh_HANS": "0 – 平面。\n1 – 圆角停靠。\n2 – 间隙",
        "ru_RU": "0 – Гладко.\n1 – Скруглённые состыкованные.\n2 – Зазор",
    },
    ("*", "Display socket type info"): {
        "zh_HANS": "显示接口类型",
        "ru_RU": "Отображение типа сокета",
    },
    ("*", "0 – Disable.\n1 – From above.\n-1 – From below (VMT)"): {
        "zh_HANS": "0 – 禁用。\n1 – 从上方。\n-1 – 从下方 (VMT)",
        "ru_RU": "0 – Выключено.\n1 – Сверху.\n-1 – Снизу (VMT)",
    },
    ("*", "Display socket color"): {
        "zh_HANS": "显示接口颜色条",
        "ru_RU": "Отображение цвета сокета",
    },
    ("*", "The sign is side of a color. The magnitude is width of a color"): {
        "zh_HANS": "符号表示颜色的一侧,数值表示颜色条的宽度",
        "ru_RU": "Знак – сторона цвета. Значение – ширина цвета",
    },

    # VoronoiHiderTool
    ("*", "Socket value"): {
        "zh_HANS": "接口值",
        "ru_RU": "Значение сокета",
    },
    ("*", "Switching the visibility of a socket contents"): {
        "zh_HANS": "切换接口内容的可见性",
        "ru_RU": "Переключение видимости содержимого сокета.",
    },
    ("*", "Hiding the socket"): {
        "zh_HANS": "隐藏接口",
        "ru_RU": "Сокрытие сокета.",
    },
    ("*", "Automatically processing of hiding of sockets for a node"): {
        "zh_HANS": "自动处理节点接口的隐藏",
        "ru_RU": "Автоматически обработать сокрытие сокетов для нода.",
    },
    ("*", "Trigger on collapsed nodes"): {
        "zh_HANS": "仅触发已折叠节点",
        "ru_RU": "Триггериться на свёрнутые ноды",
    },
    ("*", "Hide boolean sockets"): {
        "zh_HANS": "隐藏布尔接口",
        "ru_RU": "Скрывать Boolean сокеты",
    },
    ("*", "Hide hidden boolean sockets"): {
        "zh_HANS": "隐藏已隐藏的布尔接口",
        "ru_RU": "Скрывать скрытые Boolean сокеты",
    },
    ("*", "If false"): {
        "zh_HANS": "如果为False",
        "ru_RU": "Если False",
    },
    ("*", "If true"): {
        "zh_HANS": "如果为True",
        "ru_RU": "Если True",
    },
    ("*", "Never hide geometry input socket"): {
        "zh_HANS": "永不隐藏几何输入接口",
        "ru_RU": "Никогда не скрывать входные сокеты геометрии",
    },
    ("*", "Only first"): {
        "zh_HANS": "仅第一个接口",
        "ru_RU": "Только первый",
    },
    ("*", "Unhide virtual sockets"): {
        "zh_HANS": "显示虚拟接口",
        "ru_RU": "Показывать виртуальные сокеты",
    },
    ("*", "Toggle nodes on drag"): {
        "zh_HANS": "移动光标时切换节点",
        "ru_RU": "Переключать ноды при ведении курсора",
    },

    # VoronoiQuickMathTool
    ("*", "Hide node options"): {
        "zh_HANS": "隐藏节点选项",
        "ru_RU": "Скрывать опции нода",
    },
    ("*", "Just call pie"): {
        "zh_HANS": "仅调用饼图",
        "ru_RU": "Просто вызвать пирог",
    },
    ("*", "Call pie to add a node, bypassing the sockets selection.\n0–Disable.\n1–Float.\n2–Vector.\n3–Boolean.\n4–Color.\n5–Int"): {
        "zh_HANS": "调用饼图添加节点,跳过接口选择。\n0–禁用。\n1–浮点。\n2–矢量。\n3–布尔。\n4–颜色。\n5–整数",
        "ru_RU": "Вызвать пирог для добавления нода, минуя выбор сокетов.\n0 – Выключено.\n1 – Float.\n2 – Vector.\n3 – Boolean.\n4 – Color",
    },
    ("*", "Repeat last operation"): {
        "zh_HANS": "重复上一操作",
        "ru_RU": "Повторить последнюю операцию",
    },
    ("*", "Float (quick)"): {
        "zh_HANS": "浮点（快速）",
        "ru_RU": "Скаляр (быстро)",
    },
    ("*", "Vector (quick)"): {
        "zh_HANS": "矢量（快速）",
        "ru_RU": "Вектор (быстро)",
    },
    ("*", "Bool (quick)"): {
        "zh_HANS": "布尔（快速）",
        "ru_RU": "Логический (быстро)",
    },
    ("*", "Color (quick)"): {
        "zh_HANS": "颜色（快速）",
        "ru_RU": "Цвет (быстро)",
    },
    ("*", "Include third socket"): {
        "zh_HANS": "包括第三个接口",
        "ru_RU": "Разрешить третий сокет",
    },
    ("*", "Include quick presets"): {
        "zh_HANS": "包括快速预设",
        "ru_RU": "Включить быстрые пресеты",
    },
    ("*", "Include existing values"): {
        "zh_HANS": "包括现有值",
        "ru_RU": "Включить существующие значения",
    },
    ("*", "Display icons"): {
        "zh_HANS": "显示图标",
        "ru_RU": "Отображать иконки",
    },

    # VoronoiSwapperTool
    ("*", "All links from the first socket will be on the second, from the second on the first"): {
        "zh_HANS": "第一个接口的所有连线将移至第二个，第二个的将移至第一个。",
        "ru_RU": "Все линки у первого сокета будут на втором, у второго на первом.",
    },
    ("*", "Add all links from the second socket to the first one"): {
        "zh_HANS": "将第二个接口的所有连线添加到第一个。第二个将变为空。",
        "ru_RU": "Добавить все линки со второго сокета на первый. Второй будет пустым.",
    },
    ("*", "Move all links from the second socket to the first one with replacement"): {
        "zh_HANS": "将第二个接口的所有连线转移到第一个并替换现有连线。",
        "ru_RU": "Переместить все линки со второго сокета на первый с заменой.",
    },
    ("*", "Can swap with any socket type"): {
        "zh_HANS": "可以与任何类型交换",
        "ru_RU": "Может меняться с любым типом",
    },

    # VoronoiWarperTool
    ("*", "Zoom to"): {
        "zh_HANS": "自动最大化显示",
        "ru_RU": "Центрировать",
    },
    ("*", "Select reroutes"): {
        "zh_HANS": "选择更改路线",
        "ru_RU": "Выделять рероуты",
    },
    ("*", "-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting linked reroutes"): {
        "zh_HANS": "-1 – 取消全选。\n 0 – 不做任何事。\n 1 – 选择相连的转向节点",
        "ru_RU": "-1 – Де-выделять всех.\n 0 – Ничего не делать.\n 1 – Выделять связанные рероуты",
    },
    ("*", "Select target Key"): {
        "zh_HANS": "选择目标快捷键",
        "ru_RU": "Клавиша выделения цели",
    },

    # VoronoiEnumSelectorTool
    ("*", "Box "): {
        "zh_HANS": "框 ",
        "ru_RU": "Коробка",
    },
    ("*", "Instant activation"): {
        "zh_HANS": "直接打开饼菜单",
        "ru_RU": "Моментальная активация",
    },
    ("*", "Skip drawing to a node and activation when release, and activate immediately when pressed"): {
        "zh_HANS": "不勾选可以先根据鼠标位置动态选择节点",
        "ru_RU": "Пропустить рисование к ноду и активацию при отпускании, и активировать немедленно при нажатии",
    },
    ("*", "Pie choice"): {
        "zh_HANS": "饼菜单选择",
        "ru_RU": "Выбор пирогом",
    },
    ("*", "Allows to select an enum by releasing the key"): {
        "zh_HANS": "允许通过释放键来选择枚举",
        "ru_RU": "Позволяет выбрать элемент отпусканием клавиши",
    },
    ("*", "Toggle node options"): {
        "zh_HANS": "切换节点选项",
        "ru_RU": "Переключение опций нода",
    },
    ("*", "Select target node"): {
        "zh_HANS": "选择目标节点",
        "ru_RU": "Выделять целевой нод",
    },
    ("*", "0 – Do not select.\n1 – Select.\n2 – And center.\n3 – And zooming"): {
        "zh_HANS": "0 – 不选择。\n1 – 选择。\n2 – 并居中。\n3 – 并缩放",
        "ru_RU": "0 – Не выделять.\n1 – Выделять.\n2 – и центрировать.\n3 – и приближать",
    },
    ("*", "Box scale"): {
        "zh_HANS": "下拉列表面板大小",
        "ru_RU": "Масштаб панели",
    },
    ("*", "Display enum names"): {
        "zh_HANS": "显示下拉列表属性名称",
        "ru_RU": "Отображать имена свойств перечислений",
    },
    ("*", "Dark style"): {
        "zh_HANS": "暗色风格",
        "ru_RU": "Тёмный стиль",
    },

    # VoronoiMassLinkerTool
    ("*", "Ignore existing links"): {
        "zh_HANS": "忽略现有链接",
        "ru_RU": "Игнорировать существующие связи",
    },
    ("*", "Ignore case"): {
        "zh_HANS": "忽略接口名称的大小写",
        "ru_RU": "Игнорировать регистр",
    },

    # VoronoiInterfacerTool
    ("*", "Copy a socket name to clipboard"): {
        "zh_HANS": "复制接口名称到剪贴板",
        "ru_RU": "Копировать имя сокета в буфер обмена.",
    },
    ("*", "Paste the contents of clipboard into an interface name"): {
        "zh_HANS": "将剪贴板内容粘贴到接口名称中",
        "ru_RU": "Вставить содержимое буфера обмена в имя интерфейса.",
    },
    ("*", "Swap a two interfaces"): {
        "zh_HANS": "交换两个接口",
        "ru_RU": "Поменять местами два интерфейса.",
    },
    ("*", "Move the interface to a new location, shifting everyone else"): {
        "zh_HANS": "将接口移动到新位置，移动其他所有接口",
        "ru_RU": "Переместить интерфейс на новое место, сдвигая всех остальных.",
    },
    ("*", "Create an interface using virtual sockets"): {
        "zh_HANS": "使用虚拟接口创建接口",
        "ru_RU": "Добавить интерфейс с помощью виртуальных сокетов.",
    },
    ("*", "Create an interface from a selected socket, and paste it into a specified location"): {
        "zh_HANS": "从选定的接口创建接口，并将其粘贴到指定位置",
        "ru_RU": "Создать интерфейс из выбранного сокета, и вставить его на указанное место.",
    },
    ("*", "Allow paste to any socket"): {
        "zh_HANS": "允许粘贴到任何接口",
    },

    # VoronoiPreviewAnchorTool
    ("*", "Anchor type"): {
        "zh_HANS": "转接点的类型",
        "ru_RU": "Тип якоря",
    },
    ("*", "Active anchor"): {
        "zh_HANS": "转接点设置为活动项",
        "ru_RU": "Делать якорь активным",
    },
    ("*", "Select anchor"): {
        "zh_HANS": "转接点高亮显示",
        "ru_RU": "Выделять якорь",
    },
    ("*", "Clear anchors"): {
        "zh_HANS": "删除已有转接点",
        "ru_RU": "Удалить имеющиеся якори",
    },

    # VoronoiResetTarget1NodeTool
    ("*", "Reset enums"): {
        "zh_HANS": "恢复下拉列表里的选择",
        "ru_RU": "Восстанавливать свойства перечисления",
    },
    ("*", "Reset on grag (not recommended)"): {
        "zh_HANS": "悬停时恢复(不推荐)",
        "ru_RU": "Восстанавливать при ведении курсора (не рекомендуется)",
    },
    ("*", "Select reseted node"): {
        "zh_HANS": "选择重置的节点",
        "ru_RU": "Выделять восстановленный нод",
    },

    # VoronoiLinkRepeatingTool
    ("*", "Using the last link created by some from the tools, create the same for the specified socket"): {
        "zh_HANS": "使用某个工具创建的最后一个链接，为指定的接口创建相同的链接",
        "ru_RU": "Используя последний линк, созданный каким-н. из инструментов, создать такой же для указанного сокета.",
    },
    ("*", "Using name of the last socket, find and connect for a selected node"): {
        "zh_HANS": "鼠标移动到节点旁自动恢复节点的连接",
        "ru_RU": "Используя имя последнего сокета, найти и соединить для выбранного нода.",
    },

    # VoronoiLinksTransferTool
    ("*", "Transfer by indexes"): {
        "zh_HANS": "按顺序传输",
        "ru_RU": "Переносить по индексам",
    },

    # VoronoiLazyNodeStencilsTool
    ("*", "Non-Color name"): {
        "zh_HANS": "图片纹理色彩空间名称",
        "ru_RU": "Название \"Не-цветовых данных\"",
    },
    ("*", "Last exec error"): {
        "zh_HANS": "上次运行时错误",
        "ru_RU": "Последняя ошибка выполнения",
    },

    # VoronoiRantoTool
    ("*", "Only selected"): {
        "zh_HANS": "仅选定的",
        "ru_RU": "Только выделенные",
    },
    ("*", "0 – Any node.\n1 – Selected + reroutes.\n2 – Only selected"): {
        "zh_HANS": "0 – 任意节点。\n1 – 选定+转向节点。\n2 – 仅选定的节点",
        "ru_RU": "0 – Любой нод.\n1 – Выделенные + рероуты.\n2 – Только выделенные",
    },
    ("*", "Uniform width"): {
        "zh_HANS": "统一宽度",
        "ru_RU": "Постоянная ширина",
    },
    ("*", "Node width"): {
        "zh_HANS": "节点宽度",
        "ru_RU": "Ширина нода",
    },
    ("*", "Indent x"): {
        "zh_HANS": "X缩进",
        "ru_RU": "Отступ по X",
    },
    ("*", "Indent y"): {
        "zh_HANS": "Y缩进",
        "ru_RU": "Отступ по Y",
    },
    ("*", "Uncollapse nodes"): {
        "zh_HANS": "展开节点",
        "ru_RU": "Разворачивать ноды",
    },
    ("*", "Delete reroutes"): {
        "zh_HANS": "删除转向节点",
        "ru_RU": "Удалять рероуты",
    },
    ("*", "Select nodes"): {
        "zh_HANS": "选择节点",
        "ru_RU": "Выделять ноды",
    },
    ("*", "-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting involveds node"): {
        "zh_HANS": "-1 – 取消全选。\n 0 – 不做任何事。\n 1 – 选择涉及的节点",
        "ru_RU": "-1 – Де-выделять всё.\n 0 – Ничего не делать.\n 1 – Выделять задействованные ноды",
    },
    ("*", "Include muted links"): {
        "zh_HANS": "包含禁用的连线",
        "ru_RU": "Разрешить выключенные линки",
    },
    ("*", "Include non valid links"): {
        "zh_HANS": "包含无效的连线",
        "ru_RU": "Разрешить невалидные линки",
    },
    ("*", "Accumulate"): {
        "zh_HANS": "累积",
        "ru_RU": "Накапливать",
    },
    ("*", "Live Ranto"): {
        "zh_HANS": "实时对齐",
        "ru_RU": "Ranto в реальном времени",
    },
    ("*", "Fix islands"): {
        "zh_HANS": "修复孤岛",
        "ru_RU": "Чинить острова",
    },

    # AddonPrefs
    ("*", "Language bruteforce debug"): {
        "zh_HANS": "语言暴力调试",
    },
    ("*", "Field debug"): {
        "zh_HANS": "字段调试",
    },
    ("*", "Testing draw"): {
        "zh_HANS": "测试绘制",
    },
    ("*", "Addon Prefs Tabs"): {
        "zh_HANS": "插件偏好设置标签",
    },
    ("*", "Settings"): {
        "zh_HANS": "设置",
    },
    ("*", "Appearance"): {
        "zh_HANS": "外观",
    },
    ("*", "Draw"): {
        "zh_HANS": "绘制",
    },
    ("*", "Keymap"): {
        "zh_HANS": "快捷键",
    },
    ("*", "Info"): {
        "zh_HANS": "信息",
    },
    ("*", "This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon"): {
        "zh_HANS": "危险:\"恢复\"按钮将恢复整个快捷键里\"节点编辑器\"类中的所有设置,而不仅仅是恢复此插件!下面只显示本插件的快捷键。",
        "ru_RU": "Этот список лишь копия из настроек. \"Восстановление\" восстановит всё, а не только аддон",
    },
    ("*", "Most Useful"): {
        "zh_HANS": "最有用",
        "ru_RU": "Наиболее полезные",
    },
    ("*", "Quite Useful"): {
        "zh_HANS": "很有用",
        "ru_RU": "Весьма полезные",
    },
    ("*", "Maybe Useful"): {
        "zh_HANS": "可能有用",
        "ru_RU": "Возможно полезные",
    },
    ("*", "Invalid"): {
        "zh_HANS": "无效",
    },
    ("*", "Custom"): {
        "zh_HANS": "自定义",
        "ru_RU": "Кастомные",
    },

    # Draw settings
    ("*", "Alternative uniform color"): {
        "zh_HANS": "备选颜色:统一颜色",
        "ru_RU": "Альтернативный постоянный цвет",
    },
    ("*", "Alternative nodes color"): {
        "zh_HANS": "备选颜色:节点颜色",
        "ru_RU": "Альтернативный цвет нодов",
    },
    ("*", "Cursor color"): {
        "zh_HANS": "光标颜色",
        "ru_RU": "Цвет курсора",
    },
    ("*", "Cursor color availability"): {
        "zh_HANS": "光标颜色设置",
        "ru_RU": "Наличие цвета курсора",
    },
    ("*", "If a line is drawn to the cursor, color part of it in the cursor color.\n0 – Disable.\n1 – For one line.\n2 – Always"): {
        "zh_HANS": "如果绘制到光标的线条,将其中一部分着色为光标颜色。\n0 – 禁用。\n1 – 仅一条线。\n2 – 始终",
        "ru_RU": "Если линия рисуется к курсору, окрашивать её часть в цвет курсора.\n0 – Выключено.\n1 – Для одной линии.\n2 – Всегда",
    },
    ("*", "Socket area alpha"): {
        "zh_HANS": "接口区域的透明度",
        "ru_RU": "Прозрачность области сокета",
    },
    ("*", "Font file"): {
        "zh_HANS": "字体文件",
        "ru_RU": "Файл шрифта",
    },
    ("*", "Manual adjustment"): {
        "zh_HANS": "手动调整",
        "ru_RU": "Ручная корректировка",
    },
    ("*", "The Y-axis offset of text for this font"): {
        "zh_HANS": "此字体文本的Y轴偏移量",
        "ru_RU": "Смещение текста по оси Y для данного шрифта",
    },
    ("*", "Point offset X axis"): {
        "zh_HANS": "X轴上的点偏移",
        "ru_RU": "Смещение точки по оси X",
    },
    ("*", "Frame size"): {
        "zh_HANS": "边框大小",
        "ru_RU": "Размер рамки",
    },
    ("*", "Font size"): {
        "zh_HANS": "字体大小",
        "ru_RU": "Размер шрифта",
    },
    ("*", "Marker Style"): {
        "zh_HANS": "标记样式",
        "ru_RU": "Стиль маркера",
    },
    ("*", "Socket area"): {
        "zh_HANS": "接口区域",
        "ru_RU": "Область сокета",
    },
    ("*", "Display frame style"): {
        "zh_HANS": "边框显示样式",
        "ru_RU": "Стиль отображения рамки",
    },
    ("*", "Classic"): {
        "zh_HANS": "经典",
        "ru_RU": "Классический",
    },
    ("*", "Simplified"): {
        "zh_HANS": "简化",
        "ru_RU": "Упрощённый",
    },
    ("*", "Only text"): {
        "zh_HANS": "仅文本",
        "ru_RU": "Только текст",
    },
    ("*", "Point scale"): {
        "zh_HANS": "点缩放",
        "ru_RU": "Масштаб точки",
    },
    ("*", "Text distance from cursor"): {
        "zh_HANS": "到文本的距离",
        "ru_RU": "Расстояние до текста от курсора",
    },
    ("*", "Always draw line"): {
        "zh_HANS": "始终绘制线条",
        "ru_RU": "Всегда рисовать линию",
    },
    ("*", "Draw a line to the cursor even from a single selected socket"): {
        "zh_HANS": "在鼠标移动到移动到已有连接接口的时是否还显示连线",
        "ru_RU": "Рисовать линию к курсору даже от одного выбранного сокета",
    },
    ("*", "Slide on nodes"): {
        "zh_HANS": "在节点上滑动",
        "ru_RU": "Скользить по нодам",
    },
    ("*", "Enable text shadow"): {
        "zh_HANS": "启用文本阴影",
        "ru_RU": "Включить тень текста",
    },
    ("*", "Shadow color"): {
        "zh_HANS": "阴影颜色",
        "ru_RU": "Цвет тени",
    },
    ("*", "Shadow offset"): {
        "zh_HANS": "阴影偏移",
        "ru_RU": "Смещение тени",
    },
    ("*", "Shadow blur"): {
        "zh_HANS": "阴影模糊",
        "ru_RU": "Размытие тени",
    },
    ("*", "Display text for node"): {
        "zh_HANS": "显示节点标签",
        "ru_RU": "Показывать заголовок для нода",
    },

    # Draw tab sections
    ("*", "Behavior"): {
        "zh_HANS": "行为",
        "ru_RU": "Поведение",
    },
    ("*", "Color"): {
        "zh_HANS": "颜色",
        "ru_RU": "Цвет",
    },
    ("*", "Style"): {
        "zh_HANS": "样式",
        "ru_RU": "Стиль",
    },
    ("*", "Offset"): {
        "zh_HANS": "偏移",
        "ru_RU": "Смещение",
    },

    # Settings
    ("*", "Edge pan zoom factor"): {
        "zh_HANS": "边缘滑动缩放系数",
        "ru_RU": "Фактор панорамирования масштаба",
    },
    ("*", "0.0 – Shift only; 1.0 – Scale only"): {
        "zh_HANS": "0.0 – 仅平移; 1.0 – 仅缩放",
        "ru_RU": "0.0 – Только сдвиг; 1.0 – Только масштаб",
    },
    ("*", "Edge pan speed"): {
        "zh_HANS": "边缘滑动速度",
        "ru_RU": "Скорость краевого панорамирования",
    },
    ("*", "Overwriting zoom limits"): {
        "zh_HANS": "覆盖缩放限制",
        "ru_RU": "Перезапись лимитов масштаба",
    },
    ("*", "Zoom min"): {
        "zh_HANS": "最小缩放",
        "ru_RU": "Минимальный масштаб",
    },
    ("*", "Zoom max"): {
        "zh_HANS": "最大缩放",
        "ru_RU": "Максимальный масштаб",
    },

    # Tool descriptions
    ("*", "Rename Node Only Chinese"): {
        "zh_HANS": "重命名节点,仅中文",
    },
    ("*", "Rename nodes when hiding options, currently only support Chinese"): {
        "zh_HANS": "隐藏选项时重命名存储属性等一些节点,目前只支持中文",
        "ru_RU": "Переименовать ноды при скрытии опций, сейчас только на китайском",
    },
    ("*", "Rename nodes when toggling options, currently only support Chinese"): {
        "zh_HANS": "切换选项时重命名存储属性等一些节点,目前只支持中文",
        "ru_RU": "Переименовать ноды при переключении опций, сейчас только на китайском",
    },
    ("*", "Hide Options"): {
        "zh_HANS": "隐藏选项",
        "ru_RU": "Скрыть опции",
    },
    ("*", "Show Options"): {
        "zh_HANS": "显示选项",
        "ru_RU": "Показать опции",
    },
    ("*", "Toggle Options"): {
        "zh_HANS": "切换选项",
        "ru_RU": "Переключить опции",
    },

    # Tool names
    ("*", "Node Pie Menu"): {
        "zh_HANS": "节点饼菜单",
        "ru_RU": "Пироговое меню нодов",
    },
    ("*", "Connect to Interface"): {
        "zh_HANS": "连到扩展接口",
        "ru_RU": "Подключиться к интерфейсу",
    },
    ("*", "Insert Interface"): {
        "zh_HANS": "插入接口",
        "ru_RU": "Вставить интерфейс",
    },
    ("*", "Node Group"): {
        "zh_HANS": "节点组",
        "ru_RU": "Группа нодов",
    },
    ("*", "Move Interface"): {
        "zh_HANS": "移动接口",
        "ru_RU": "Переместить интерфейс",
    },
    ("*", "Quick Constant"): {
        "zh_HANS": "快速常量",
        "ru_RU": "Быстрая константа",
    },
    ("*", "Quick Dimensions"): {
        "zh_HANS": "快速分量",
        "ru_RU": "Быстрые измерения",
    },
    ("*", "Auto Hide/Show Sockets"): {
        "zh_HANS": "自动隐藏/显示接口",
        "ru_RU": "Автоматически скрыть/показать сокеты",
    },
    ("*", "Hide Socket"): {
        "zh_HANS": "隐藏接口",
        "ru_RU": "Скрыть сокеты",
    },
    ("*", "Hide/Show Socket Value"): {
        "zh_HANS": "隐藏/显示接口值",
        "ru_RU": "Скрыть/показать значения сокетов",
    },
    ("*", "Copy Socket Name"): {
        "zh_HANS": "复制接口名",
        "ru_RU": "Копировать имя сокета",
    },
    ("*", "Paste Socket Name"): {
        "zh_HANS": "粘贴接口名",
        "ru_RU": "Вставить имя сокета",
    },
    ("*", "Swap Sockets"): {
        "zh_HANS": "交换接口",
        "ru_RU": "Поменять сокеты",
    },
    ("*", "Change Socket Type"): {
        "zh_HANS": "更改节口类型",
        "ru_RU": "Изменить тип сокета",
    },
    ("*", "Linker"): {
        "zh_HANS": "连线者",
        "ru_RU": "Линковщик",
    },
    ("*", "Preview"): {
        "zh_HANS": "预览",
        "ru_RU": "Превью",
    },
    ("*", "Quick Mix"): {
        "zh_HANS": "快速混合",
        "ru_RU": "Быстрое смешивание",
    },
    ("*", "Lazy Node Stencils"): {
        "zh_HANS": "懒人节点模板",
        "ru_RU": "Ленивые стенсилы",
    },
    ("*", "MassLinker"): {
        "zh_HANS": "批量连接",
        "ru_RU": "Массовый линковщик",
    },
    ("*", "Links Transfer"): {
        "zh_HANS": "连线转移",
        "ru_RU": "Перенос связей",
    },
    ("*", "Transfer"): {
        "zh_HANS": "转移",
        "ru_RU": "Перенос",
    },
    ("*", "Quick Math Pie"): {
        "zh_HANS": "快速运算饼菜单",
        "ru_RU": "Пирог быстрой математики",
    },
    ("*", "Enum Select Box"): {
        "zh_HANS": "菜单枚举选择框",
        "ru_RU": "Окно выбора перечислений",
    },
    ("*", "Mix Pie"): {
        "zh_HANS": "混合饼菜单",
        "ru_RU": "Пирог смешивания",
    },
    ("*", "Settings from original author (I don't understand some of them)"): {
        "zh_HANS": "原作者的一些设置(有些我也不太懂用处)",
        "ru_RU": "Некоторые настройки от оригинального автора (некоторые я тоже не совсем понимаю)",
    },
    ("*", " tool settings"): {
        "zh_HANS": "工具设置",
    },
    ("*", "Edge pan"): {
        "zh_HANS": "边缘滑动",
    },
    ("*", "Node label"): {
        "zh_HANS": "节点标签",
    },

    # Tool bl_description
    ("*", "The sacred tool. The reason this entire addon was created.\nA moment of silence in honor of NodeWrangler, the original ancestor."): {
        "zh_HANS": "核心连线工具, 本插件的起源.\n致敬NodeWrangler的原始设计",
        "ru_RU": "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника.",
    },
    ("*", "The canonical tool for instant redirection of the tree's active output.\nEven more useful when used together with VPAT."): {
        "zh_HANS": "快速预览节点输出结果的工具.\n与预览锚点工具(VPAT)配合使用效果更佳",
        "ru_RU": "Канонический инструмент для мгновенного перенаправления явного вывода дерева.\nЕщё более полезен при использовании совместно с VPAT.",
    },
    ("*", "A forced separation from VPT, a kind of \"companion manager\" for VPT.\nExplicit socket specification and creation of reroute anchors."): {
        "zh_HANS": "预览锚点管理工具, 可指定预览接口并创建转接点锚点",
        "ru_RU": "Вынужденное отделение от VPT, своеобразный \"менеджер-компаньон\" для VPT.\nЯвное указание сокета и создание рероут-якорей.",
    },
    ("*", "The canonical tool for frequent mixing needs.\nMost likely 70% will go to using \"Instance on Points\"."): {
        "zh_HANS": "快速混合工具, 常用于几何节点中的点实例等操作",
        "ru_RU": "Канонический инструмент для частых нужд смешивания.\nСкорее всего 70% уйдёт на использование \"Instance on Points\".",
    },
    ("*", "A full-fledged branch from VMT. Quick and quick-quick math at speeds.\nHas additional mini-functionality. Also see \"Quick quick math\" in the layout."): {
        "zh_HANS": "快速数学运算工具, 支持浮点/向量/布尔/颜色/整数等多种运算.\n可通过饼菜单快速选择运算类型",
        "ru_RU": "Полноценное ответвление от VMT. Быстрая и быстрая быстрая математика на спидах.\nИмеет дополнительный мини-функционал. Также см. \"Quick quick math\" в раскладе.",
    },
    ("*", "Tool for swapping links between two sockets, or adding them to one of them.\nNo link swap will occur if it ends up originating from its own node."): {
        "zh_HANS": "Alt是批量替换输出接口,Shift是互换接口",
        "ru_RU": "Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.\nДля линка обмена не будет, если в итоге он окажется исходящим из своего же нода.",
    },
    ("*", "Tool for bringing order and aesthetics to the node tree.\nMost likely 90% will go to using automatic socket hiding."): {
        "zh_HANS": "Shift是自动隐藏数值为0/颜色纯黑/未连接的接口,Ctrl是单个隐藏接口",
        "ru_RU": "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов.",
    },
    ("*", "\"Puppy cat-dog\", neither nodes nor sockets. Created for rare point special accelerations.\nVLT on max. Due to its working principle, divine in its own way."): {
        "zh_HANS": "批量连线工具, 可一次性将多个同名接口连接起来.\n左键选择节点, 右键可忽略已存在的连线",
        "ru_RU": "\"Малыш котопёс\", не ноды, не сокеты. Создан ради редких точечных спец-ускорений.\nVLT на максималках. В связи со своим принципом работы, по своему божественен.",
    },
    ("*", "Tool for convenient lazy switching of enumeration properties.\nEliminates the need for mouse aiming, clicking, and then aiming and clicking again."): {
        "zh_HANS": "快速切换节点枚举属性的工具, 支持饼菜单选择.\nCtrl+E切换节点选项显示, Alt+E切换节点选项",
        "ru_RU": "Инструмент для удобно-ленивого переключения свойств перечисления.\nИзбавляет от прицеливания мышкой, клика, а потом ещё одного прицеливания и клика.",
    },
    ("*", "A full-fledged branch from VLT, repeats any previous link from most\nother tools. Provides convenience for \"one to many\" connections."): {
        "zh_HANS": "重复上一次连线操作, 支持'一对多'快速连接.\nV键重复接口连线, Shift+V重复节点连线",
        "ru_RU": "Полноценное ответвление от VLT, повторяет любой предыдущий линк от большинства\nдругих инструментов. Обеспечивает удобство соединения \"один ко многим\".",
    },
    ("*", "Tool for accelerating the needs of separating and combining vectors (and color).\nAnd can also split geometry into components."): {
        "zh_HANS": "快速分离/合并向量、颜色、矩阵等数据.\n支持几何节点中的各种数据类型拆分",
        "ru_RU": "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие.",
    },
    ("*", "Tool for quickly adding constant value nodes.\nSupports various data types including vectors, colors, matrices and more."): {
        "zh_HANS": "快速添加常量值节点.\n支持向量、颜色、矩阵等多种数据类型",
        "ru_RU": "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие.",
    },
    ("*", "A tool on the level of \"The Great Trio\". A branch from VLT for convenient acceleration\nof the creation process and special manipulations with interfaces. \"Interface Manager\"."): {
        "zh_HANS": "接口管理工具, 支持复制/粘贴/交换/翻转/创建接口.\nSCA+A新建虚拟接口, Shift+Alt+A从选中接口创建",
        "ru_RU": "Инструмент на уровне \"The Great Trio\". Ответвление от VLT ради удобного ускорения\nпроцесса создания и спец-манипуляций с интерфейсами. \"Менеджер интерфейсов\".",
    },
    ("*", "Tool for rare needs of transferring all links from one node to another.\nIn the future, it will most likely be merged with VST."): {
        "zh_HANS": "将一个节点的所有连线转移到另一个节点.\nSCA+T按名称转移, Shift+T按索引转移",
        "ru_RU": "Инструмент для редких нужд переноса всех линков с одного нода на другой.\nВ будущем скорее всего будет слито с VST.",
    },
    ("*", "A mini-branch of topology reverse-engineering (like VPT).\nTool for \"point jumps\" along sockets."): {
        "zh_HANS": "沿连线快速跳转定位到相关节点的工具.\nS+A+W跳转, SCA+W跳转但不缩放",
        "ru_RU": "Мини-ответвление реверс-инженеринга топологии, (как у VPT).\nИнструмент для \"точечных прыжков\" по сокетам.",
    },
    ("*", "Power. Three letters for a tool, we've come to this... Encapsulates Ctrl-T from\nNodeWrangler, and the never-implemented 'VoronoiLazyNodeContinuationTool'."): {
        "zh_HANS": "代替NodeWrangler的ctrl+t, 快速从接口延伸节点模板",
        "ru_RU": "Мощь. Три буквы на инструмент, дожили... Инкапсулирует Ctrl-T от\nNodeWrangler'а, и никогда не реализованный 'VoronoiLazyNodeContinuationTool'.",
    },
    ("*", "Tool for resetting nodes without the need for aiming, with mouse guidance convenience\nand ignoring enumeration properties. Was created because NW had something similar."): {
        "zh_HANS": "快速重置节点到默认状态, 保留连线.\nBackSpace重置, Shift+BackSpace同时重置枚举属性",
        "ru_RU": "Инструмент для сброса нодов без нужды прицеливания, с удобствами ведения мышкой\nи игнорированием свойств перечислений. Был создан, потому что в NW было похожее.",
    },
    # Key descriptions
    ("*", "Hold this key to re-pick target socket without releasing the mouse"): {
        "zh_HANS": "按住此键可在不释放鼠标的情况下重新选择目标接口",
        "ru_RU": "Удерживайте эту клавишу, чтобы повторно выбрать целевой сокет, не отпуская мышь",
    },
    ("*", "Hold this key to select the target node instead of just jumping to it"): {
        "zh_HANS": "按住此键可选择目标节点, 而非仅跳转到该节点",
        "ru_RU": "Удерживайте эту клавишу, чтобы выбрать целевой узел, а не просто перейти к нему",
    },
}

def convert_to_support_format(old_dict: dict[tuple[context_s, str], dict[locale_s, str]]):
    result: dict[locale_s, dict[tuple[context_s, str], str]] = {}
    for key, translations in old_dict.items():
        for lang, text in translations.items():
            if not text: continue
            if lang not in result:
                result[lang] = {}
            result[lang][key] = text
    return result

translations_dict = convert_to_support_format(_translations_dict)
