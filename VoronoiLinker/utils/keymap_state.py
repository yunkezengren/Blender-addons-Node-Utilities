"""在 Blender 重载脚本或重新启用插件时保留用户修改过的快捷键。"""

import bpy
from bpy.types import KeyMapItem, OperatorProperties


_STATE_KEY = "voronoi_linker.keymap_state"
_DEFAULT_IDS_KEY = "voronoi_linker.default_keymap_ids"
_EVENT_FIELDS = (
    "type", "value", "any", "shift", "ctrl", "alt", "oskey", "hyper",
    "key_modifier", "direction", "repeat", "active",
)


def _read_properties(properties: OperatorProperties | None) -> dict[str, object]:
    """只保存用户显式设置的操作符属性，避免把其他默认值写死。"""
    if properties is None:
        return {}
    values: dict[str, object] = {}
    for prop in properties.bl_rna.properties:
        name = prop.identifier
        if name == "rna_type" or not properties.is_property_set(name):
            continue
        value = getattr(properties, name)
        if hasattr(value, "bl_rna"):
            # 部分操作符属性是嵌套结构，需要递归保存。
            value = _read_properties(value)
        elif not isinstance(value, (str, int, float, bool, set)) and hasattr(value, "__iter__"):
            # Blender 的数组属性对象不能直接作为快照长期保存。
            value = tuple(value)
        values[name] = value
    return values


def _write_properties(properties: OperatorProperties, values: dict[str, object]) -> None:
    """把快照中的操作符属性写回新按键项。"""
    for name, value in values.items():
        if isinstance(value, dict):
            _write_properties(getattr(properties, name), value)
        else:
            setattr(properties, name, value)


def _read_item(item: KeyMapItem) -> dict[str, object]:
    """保存按键事件、启用状态、操作符参数及界面展开状态。"""
    return {
        "id": item.id,
        "idname": item.idname,
        "event": {name: getattr(item, name) for name in _EVENT_FIELDS},
        "properties": _read_properties(item.properties),
        "show_expanded": item.show_expanded,
    }


def _write_item(item: KeyMapItem, state: dict[str, object]) -> None:
    """恢复单个按键项的用户设置。"""
    event = state["event"]
    # 必须先设置 type：Blender 会据此确定事件类型及其他字段的合法取值。
    for name in _EVENT_FIELDS:
        setattr(item, name, event[name])
    _write_properties(item.properties, state["properties"])
    item.show_expanded = state["show_expanded"]


def capture_keymaps(addon_items: list[KeyMapItem]) -> None:
    """在注销默认按键前，从用户按键表提取 VoronoiLinker 的实际设置。"""
    wm = bpy.context.window_manager
    # 先同步 add-on 与 user keyconfig，避免读取到尚未刷新的用户按键表。
    wm.keyconfigs.update()
    user_km = wm.keyconfigs.user.keymaps.get("Node Editor")
    if user_km is None:
        return

    previous_ids: list[int] = bpy.app.driver_namespace.get(_DEFAULT_IDS_KEY, [])
    default_ids: list[int] = []
    for index, addon_item in enumerate(addon_items):
        previous_id = previous_ids[index] if index < len(previous_ids) else None
        previous = user_km.keymap_items.from_id(previous_id) if previous_id is not None else None
        # 重载时，Blender 可能给新注册的 add-on 项分配新 ID，
        # 但 user keyconfig 中对应的项仍沿用旧 ID。
        default_ids.append(previous_id if previous and previous.idname == addon_item.idname else addon_item.id)
    user_items = {item.id: item for item in user_km.keymap_items if item.idname.startswith("node.voronoi_")}
    # 模块会被重新加载，普通模块变量会重置；driver_namespace 可跨这次重载暂存快照。
    state = {
        # 每个默认项都保留一个位置；None 表示用户已删除该默认快捷键。
        "defaults": [(item_id, addon_item.idname, _read_item(user_items[item_id]) if item_id in user_items else None)
                     for item_id, addon_item in zip(default_ids, addon_items)],
        # 负 ID 是用户手动新增的按键项，不对应插件注册的默认项。
        "custom": [_read_item(item) for item in user_km.keymap_items
                   if item.idname.startswith("node.voronoi_") and item.id < 0],
    }
    bpy.app.driver_namespace[_STATE_KEY] = state


def restore_keymaps(addon_items: list[KeyMapItem]) -> None:
    """默认按键重新注册后，恢复用户的修改、删除和新增项。"""
    state = bpy.app.driver_namespace.pop(_STATE_KEY, None)
    if state is None:
        return

    wm = bpy.context.window_manager
    wm.keyconfigs.update()
    user_km = wm.keyconfigs.user.keymaps["Node Editor"]
    restored_ids: list[int] = []
    for addon_item, (previous_id, previous_idname, saved) in zip(addon_items, state["defaults"]):
        # 插件更新后若默认按键顺序或操作符改变，不把旧设置套到别的操作符上。
        if addon_item.idname != previous_idname:
            restored_ids.append(addon_item.id)
            continue
        item = user_km.keymap_items.from_id(previous_id)
        if item is None or item.idname != addon_item.idname:
            # user keyconfig 若已换用新 ID，则改用本次注册的 add-on ID。
            item = user_km.keymap_items.from_id(addon_item.id)
        restored_ids.append(item.id if item is not None else previous_id)
        if item is None:
            continue
        if saved is None:
            # 用户原先删除的默认项在重新注册后仍应保持删除状态。
            user_km.keymap_items.remove(item)
        else:
            _write_item(item, saved)

    bpy.app.driver_namespace[_DEFAULT_IDS_KEY] = restored_ids

    for saved in state["custom"]:
        event = saved["event"]
        item = user_km.keymap_items.from_id(saved["id"])
        if item is None:
            # 仅在用户项确实消失时创建，避免连续重载产生重复快捷键。
            item = user_km.keymap_items.new(saved["idname"], event["type"], event["value"])
        _write_item(item, saved)
