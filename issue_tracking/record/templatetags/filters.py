from django import template
from django.utils import timezone

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

@register.filter
def converttotimestamp(date_created):
    return timezone.localtime(date_created).strftime("%m-%d-%Y %H:%M:%S")

@register.filter
def minimizestring(string):
    if string and len(string) >= 30:
        return '{} ...'.format(string[:30])
    return string
