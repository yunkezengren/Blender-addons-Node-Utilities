import bpy

dictionary = {
    "DEFAULT": {},
    "en_US": {
        
    },
}


def i18n(text: str) -> str:
    view = bpy.context.preferences.view
    language = view.language
    trans_interface = view.use_translate_interface

    if language in ["zh_CN", "zh_HANS"] and trans_interface:
        return text
    else:
        if text in dictionary["en_US"]:
            return dictionary["en_US"][text]
        else:
            return text

