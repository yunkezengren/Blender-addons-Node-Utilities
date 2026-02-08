from bpy.app.translations import pgettext_iface as _iface
from bpy.types import UILayout

class LyAddQuickInactiveCol():
    def __init__(self, layout: UILayout, att='row', align=True, active=False):
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

def LyAddHandSplitProp(layout: UILayout, who, att, *, text=None, active=True, returnAsLy=False, forceBoolean=0):
    spl = layout.row().split(factor=0.42, align=True)
    spl.active = active
    row = spl.row(align=True)
    row.alignment = 'RIGHT'
    pr = who.rna_type.properties[att]
    isNotBool = pr.type!='BOOLEAN'
    isForceBoolean = not not forceBoolean
    row.label(text=pr.name*(isNotBool^isForceBoolean) if not text else text)
    if (not active)and(pr.type=='FLOAT')and(pr.subtype=='COLOR'):
        LyAddNoneBox(spl)
    else:
        if not returnAsLy:
            txt = "" if forceBoolean!=2 else ("True" if getattr(who, att) else "False")
            spl.prop(who, att, text=txt if isNotBool^isForceBoolean else None)
        else:
            return spl

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

def LyAddKeyTxtProp(layout: UILayout, prefs, att):
    rowProp = layout.row(align=True)
    LyAddNiceColorProp(rowProp, prefs, att)
    # Todo0: 我还是没搞懂你们的 prop event 怎么用, 太吓人了. 需要外部帮助.
    with LyAddQuickInactiveCol(rowProp) as row:
        row.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, att)

def LyAddLabeledBoxCol(layout: UILayout, *, text="", active=True, scale=1.0, align=True):
    colMain = layout.column(align=True)
    box = colMain.box()
    box.scale_y = 0.5
    row = box.row(align=True)
    row.alignment = 'CENTER'
    row.label(text=" ▶ ▶ ▶   " + text)
    row.active = active
    box = colMain.box()
    box.scale_y = scale
    return box.column(align=align)

def LyAddTxtAsEtb(layout: UILayout, txt: str):
    row = layout.row(align=True)
    row.label(icon='ERROR')
    col = row.column(align=True)
    for li in txt.split("\n")[:-1]:
        col.label(text=li, translate=False)

def LyAddEtb(layout: UILayout): # "你们修复bug吗? 不, 我们只发现bug."
    import traceback
    LyAddTxtAsEtb(layout, traceback.format_exc())

def LyAddThinSep(layout: UILayout, scaleY):
    row = layout.row(align=True)
    row.separator()
    row.scale_y = scaleY
