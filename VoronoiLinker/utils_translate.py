from .globals import dict_vlHhTranslations
from .globals import *
from .forward_func import Prefs


class TranClsItemsUtil():
    def __init__(self, tup_items):
        if type(tup_items[0])==tuple:
            self.data = dict([(li[0], li[1:]) for li in tup_items])
        else:
            self.data = tup_items
    def __getattr__(self, att):
        if type(self.data)==tuple:
            match att:
                case 'name':
                    return self.data[0]
                case 'description':
                    return self.data[1]
            assert False
        else:
            return TranClsItemsUtil(self.data[att]) #`toolProp.ENUM1.name`
    def __getitem__(self, key):
        return TranClsItemsUtil(self.data[key]) #`toolProp['ENUM1'].name`

class TranAnnotFromCls():
    def __init__(self, annot):
        self.annot = annot
    def __getattr__(self, att):
        result = self.annot.keywords[att]
        return result if att!='items' else TranClsItemsUtil(result)
def GetAnnotFromCls(cls, key): # 原来它们藏在这里, 在注解(annotations)里. 我都快放弃希望了, 以为必须手动一个个写了. 😂
    return TranAnnotFromCls(cls.__annotations__[key])


class VlTrMapForKey():
    def __init__(self, key: str, *, tc='a'):
        self.key = key
        self.data = {}
        self.tc = tc
    def __enter__(self):
        return self.data
    def __exit__(self, *_):
        for dk, dv in self.data.items():
            dict_vlHhTranslations[dk]['trans'][self.tc][self.key] = dv


def GetPrefsRnaProp(att, inx=-1):
    prefsTran = Prefs()
    prop = prefsTran.rna_type.properties[att]
    return prop if inx==-1 else getattr(prop,'enum_items')[inx]