from django import template

register = template.Library()

@register.filter
def keyvalue(dict, key):    
    return dict.get(key)

@register.filter
def getcolor(string):
    try:
        index = string.index('|')
        return string[index+1:]
    except:
        return ''

@register.filter
def getmessage(string):
    try:
        index = string.index('|')
        return string[:index]
    except:
        return ''
