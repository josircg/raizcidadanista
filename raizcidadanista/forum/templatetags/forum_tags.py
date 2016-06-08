# coding: utf-8
from django import template

register = template.Library()


@register.filter
def has_grupo_perm(user, grupo):
    return grupo.grupousuario_set.filter(usuario=user).exists()

@register.filter
def has_admin_grupo_perm(user, grupo):
    return grupo.grupousuario_set.filter(usuario=user, admin=True).exists()

@register.filter
def num_topicos_nao_lidos(user, grupo):
    return grupo.num_topicos_nao_lidos(user)

@register.filter
def num_conversa_nao_lidas(user, topico):
    return topico.num_conversa_nao_lidas(user)