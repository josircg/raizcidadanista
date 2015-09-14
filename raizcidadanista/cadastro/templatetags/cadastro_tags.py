# coding:utf-8
from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter
def is_membro(circulo, user):
    if user.is_authenticated:
        return circulo.circulomembro_set.filter(membro__usuario=user).exists()
    return False
