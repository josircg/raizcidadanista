# coding:utf-8
from django import template
from django.utils.html import mark_safe
import os

register = template.Library()


@register.filter
def is_membro(circulo, user):
    if user.is_authenticated:
        return circulo.circulomembro_set.filter(membro__usuario=user).exists()
    return False


@register.simple_tag
def telegram_status():
    if int(os.popen('ps -aux | grep telegram | wc -l').read()) >= 3:
        return u'Ativo'
    return u'Inativo'