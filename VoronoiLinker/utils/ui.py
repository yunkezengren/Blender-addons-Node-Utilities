from bpy.app.translations import pgettext_iface as _iface
from bpy.types import UILayout

class LyAddQuickInactiveCol():
    def __init__(self, layout: UILayout, att='row', align=True, active=True):
        self.ly = getattr(layout, att)(align=align)
        self.ly.active = active
    def __enter__(self):
        return self.ly
    def __exit__(self, *_):
        pass

def LyAddLeftProp(layout: UILayout, who, att, active=True):
    #layout.prop(who, att); return
    row = layout.row()
    row.alignment = 'LEFT'
    row.prop(who, att)
    row.active = active

# 弃用
def LyAddDisclosureProp(layout: UILayout, who, att, *, txt=None, active=True, isWide=False): # 注意: 如果 layout 是 row, 它不能占满整个宽度.
    tgl = getattr(who, att)
    rowMain = layout.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #:"*tgl
    rowProp.prop(who, att, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=True)
    rowProp.active = active
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, att, text=" ", emboss=False)
    return tgl

def LyAddNoneBox(layout: UILayout):
    box = layout.box()
    box.label()
    box.scale_y = 0.5

def draw_hand_split_prop(layout: UILayout, who, att, *, text=None, active=True, returnAsLy=False, bool_label_left=False, link_btn=False):
    split = layout.row().split(factor=0.4, align=True)
    split.active = active
    row = split.row(align=True)
    row.alignment = 'RIGHT'
    prop = who.rna_type.properties[att]
    not_bool = prop.type != 'BOOLEAN'
    row.label(text=prop.name * (not_bool or bool_label_left) if not text else text)
    if (not active) and (prop.type == 'FLOAT') and (prop.subtype == 'COLOR'):
        LyAddNoneBox(split)
    else:
        if not returnAsLy:
            txt = "True" if (bool_label_left and getattr(who, att)) else ("False" if bool_label_left else "")
            split.prop(who, att, text=txt if not_bool or bool_label_left else None)
            if link_btn:
                # 原作者: 我还是没搞懂你们的 prop event 怎么用, 太吓人了. 需要外部帮助.
                with LyAddQuickInactiveCol(split) as row:
                    row.operator(
                        'wm.url_open', text="", icon='URL'
                    ).url = "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text=" + getattr(who, att)
        else:
            return split

def LyAddNiceColorProp(layout: UILayout, who, att, align=False, txt="", ico='NONE', decor=3):
    rowCol = layout.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else _iface(who.rna_type.properties[att].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, att, text="", icon=ico)
    rowProp.active = decor//2%2

def draw_panel_column(layout: UILayout, text="",  scale=1.0, align=True):
    panel, body = layout.panel(idname=text, default_closed=False)
    panel.label(text=text)
    if body:
        body.scale_y = scale
        return body.column(align=align)
    return None

def LyAddThinSep(layout: UILayout, scaleY):
    row = layout.row(align=True)
    row.separator()
    row.scale_y = scaleY
