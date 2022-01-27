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
    return getattr(model, field)


@register.filter(name='temp_zip')
def temp_zip(iter1, iter2):
    return zip(iter1, iter2)


@register.filter(name='next')
def next(list, curr_index):
    try:
        return list[int(curr_index) + 1]  # access the next element
    except:
        return ''  # return empty string in case of exception


@register.filter(name='temp_round')
def temp_round(number, places):
    return round(float(number), places)
