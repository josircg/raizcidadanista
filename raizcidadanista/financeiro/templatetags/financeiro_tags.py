# coding: utf-8
from django import template
from datetime import datetime

register = template.Library()


@register.filter(name='strptime')
def strptime(value, mash):
    return datetime.strptime(value, mash)


@register.filter(name='have_group')
def have_group(user, group):
    return user.groups.filter(name=group).exists()

@register.filter(name='abs')
def abs_filter(val):
    return abs(val)