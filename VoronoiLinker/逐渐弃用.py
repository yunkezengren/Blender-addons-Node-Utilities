import bpy
import bl_keymap_utils
from textwrap import dedent
from bpy.types import AddonPreferences, KeyConfig
from .utils.ui import user_node_keymap

ADDON_VERSION = "5.7.x"

def get_keyconfig_as_py():  # 从 'bl_keymap_utils.io' 借来的. 我完全不知道它是如何工作的.

    def indent(num: int):
        return " " * num

    def keyconfig_merge(kc1: KeyConfig, kc2: KeyConfig):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1 != kc2:
            merged_keymaps.extend((km, kc2) for km in kc2.keymaps if km.name not in kc1_names)
        return merged_keymaps

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.active

    class FakeKeyConfig:
        keymaps = []

    edited_kc = FakeKeyConfig()
    edited_kc.keymaps.append(user_node_keymap())
    if kc != wm.keyconfigs.default:
        export_keymaps = keyconfig_merge(edited_kc, kc)
    else:
        export_keymaps = keyconfig_merge(edited_kc, edited_kc)
    ##
    lines = ["list_keyconfigData = \\", "["]
    keymap_count = 0
    for km, _kc_x in export_keymaps:
        km = km.active()
        lines.append(f"{indent(1)}(")
        lines.append(f"{indent(2)}{km.name!r},")
        is_modal = km.is_modal
        keymap_header = (
            f"{indent(2)}{{"
            f"\"space_type\": {km.space_type!r}, "
            f"\"region_type\": {km.region_type!r}"
        )
        if is_modal:
            keymap_header += ', "modal": True'
        lines.append(keymap_header + "},")
        lines.append(f"{indent(2)}{{\"items\":")
        lines.append(f"{indent(3)}[")
        for kmi in km.keymap_items:
            if not kmi.idname.startswith("node.voronoi_"):
                continue
            keymap_count += 1
            kmi_id = kmi.propvalue if is_modal else kmi.idname
            kmi_args = bl_keymap_utils.io.kmi_args_as_data(kmi)
            kmi_data = bl_keymap_utils.io._kmi_attrs_or_none(4, kmi)
            if kmi_data is None:
                lines.append(f"{indent(4)}({kmi_id!r}, {kmi_args}, None),")
            else:
                lines.extend((
                    f"{indent(4)}({kmi_id!r},",
                    f"{indent(5)}{kmi_args},",
                    f"{indent(5)}{{{kmi_data}{indent(6)}}},",
                    f"{indent(5)}),",
                ))
        lines.append(f"{indent(3)}],")
        lines.append(f"{indent(3)}}},")
        lines.append(f"{indent(2)}),")
    lines.append(f"] #kmi count: {keymap_count}")
    lines.append(dedent(f"""

        if True:
            import bl_keymap_utils
            import bl_keymap_utils.versioning
            kc = bpy.context.window_manager.keyconfigs.active
            kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})
            bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)
    """).strip())  # 黑魔法; 似乎和 "gpu_extras" 一样.
    return "\n".join(lines)

def get_addon_settings_as_py(prefs: AddonPreferences):
    import datetime
    from . import vt_classes

    ignored_addon_prefs = {
        'bl_idname',
        'vaUiTabs',
        'vaInfoRestore',
        'dsIsFieldDebug',
        'dsIsTestDrawing',  # tovo2v6: 是全部吗?
        'vaKmiMainstreamDiscl',
        'vaKmiOtjersDiscl',
        'vaKmiSpecialDiscl',
        'vaKmiInvalidDiscl',
        'vaKmiQqmDiscl',
        'vaKmiCustomDiscl'
    }
    for cls in vt_classes:
        ignored_addon_prefs.add(cls.disclBoxPropName)
        ignored_addon_prefs.add(cls.disclBoxPropNameInfo)

    addon_pref_items: list[tuple[str, object]] = []
    lines = [dedent(f"""
        # Exported/Importing addon settings for Voronoi Linker v{ADDON_VERSION}
        # Generated {datetime.datetime.now().strftime('%Y.%m.%d')}

        import bpy
    """).strip()]
    # 构建已更改的插件设置:
    lines.append(dedent(f"""

        prefs = bpy.context.preferences.addons[{__package__!r}].preferences

        def set_prop(att, val):
            if hasattr(prefs, att):
                setattr(prefs, att, val)

        addon_pref_items = [
    """).strip())

    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            # '_BoxDiscl' 我没忽略, 留着吧.
            if pr.identifier not in ignored_addon_prefs:
                current_value = getattr(prefs, pr.identifier)
                is_array = getattr(pr, 'is_array', False)
                if is_array:
                    is_diff = any(default != current for default, current in zip(pr.default_array, current_value))
                else:
                    is_diff = pr.default != current_value
                if (True) or (is_diff):  # 只保存差异可能不安全, 以防未保存的属性的默认值发生变化.
                    if is_array:
                        #addon_pref_items.append((li.identifier, tuple(arr)))
                        addon_pref_items.append((pr.identifier, tuple(current_value)))
                    else:
                        addon_pref_items.append((pr.identifier, current_value))

    for property_name, value in addon_pref_items:
        lines.append(f"    ({property_name!r}, {value!r}),")
    lines.append("]")
    lines.append("")
    lines.append("for att, val in addon_pref_items:")
    lines.append("    set_prop(att, val)")
    # 构建所有 VL 热键:
    lines.append("")
    lines.append("#Addon keymaps:")
    # P.s. 我不知道如何只处理已更改的热键; 这看起来太头疼了, 像是一片茂密的森林. # tovo0v6
    # 懒得逆向工程 '..\scripts\modules\bl_keymap_utils\io.py', 所以就保存全部吧.
    lines.append(get_keyconfig_as_py())  # 它根本不起作用; 恢复的那部分; 生成的脚本什么也没保存, 只有临时效果.
    # 不得不等待那个英雄来修复这一切.
    return "\n".join(lines)