from bpy.types import UILayout
from bpy.app.translations import pgettext_iface as TranslateIface

class LyAddQuickInactiveCol():
    def __init__(self, where: UILayout, att='row', align=True, active=False):
        self.ly = getattr(where, att)(align=align)
        self.ly.active = active
    def __enter__(self):
        return self.ly
    def __exit__(self, *_):
        pass

def LyAddLeftProp(where: UILayout, who, att, active=True):
    #where.prop(who, att); return
    row = where.row()
    row.alignment = 'LEFT'
    row.prop(who, att)
    row.active = active

def LyAddDisclosureProp(where: UILayout, who, att, *, txt=None, active=True, isWide=False): # 注意: 如果 where 是 row, 它不能占满整个宽度.
    tgl = getattr(who, att)
    rowMain = where.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #+":"*tgl
    rowProp.prop(who, att, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
    rowProp.active = active
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, att, text=" ", emboss=False)
    return tgl

def LyAddNoneBox(where: UILayout):
    box = where.box()
    box.label()
    box.scale_y = 0.5
def LyAddHandSplitProp(where: UILayout, who, att, *, text=None, active=True, returnAsLy=False, forceBoolean=0):
    spl = where.row().split(factor=0.42, align=True)
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

def LyAddNiceColorProp(where: UILayout, who, att, align=False, txt="", ico='NONE', decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else TranslateIface(who.rna_type.properties[att].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, att, text="", icon=ico)
    rowProp.active = decor//2%2

def LyAddKeyTxtProp(where: UILayout, prefs, att):
    rowProp = where.row(align=True)
    LyAddNiceColorProp(rowProp, prefs, att)
    # Todo0: 我还是没搞懂你们的 prop event 怎么用, 太吓人了. 需要外部帮助.
    with LyAddQuickInactiveCol(rowProp) as row:
        row.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, att)

def LyAddLabeledBoxCol(where: UILayout, *, text="", active=False, scale=1.0, align=True):
    colMain = where.column(align=True)
    box = colMain.box()
    box.scale_y = 0.5
    row = box.row(align=True)
    row.alignment = 'CENTER'
    row.label(text=text)
    row.active = active
    box = colMain.box()
    box.scale_y = scale
    return box.column(align=align)

def LyAddTxtAsEtb(where: UILayout, txt: str):
    row = where.row(align=True)
    row.label(icon='ERROR')
    col = row.column(align=True)
    for li in txt.split("\n")[:-1]:
        col.label(text=li, translate=False)
def LyAddEtb(where: UILayout): # "你们修复bug吗? 不, 我们只发现bug."
    import traceback
    LyAddTxtAsEtb(where, traceback.format_exc())

