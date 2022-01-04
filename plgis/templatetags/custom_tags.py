from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='concat')
def concat(str1, str2):
    return str1 + str2


@register.filter(name='temp_getattr')
def temp_getattr(model, field):
    print(model, field)
    return getattr(model, field)
