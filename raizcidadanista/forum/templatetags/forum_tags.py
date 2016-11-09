# coding: utf-8
from django import template

from forum.models import Topico, TopicoOuvinte

register = template.Library()


@register.filter
def get_notificacao_topico(user, topico):
    try:
        return TopicoOuvinte.objects.filter(topico=topico, ouvinte=user).latest('pk').notificacao
    except TopicoOuvinte.DoesNotExist:
        return TopicoOuvinte.objects.create(topico=topico, ouvinte=user).notificacao

@register.filter
def has_grupo_perm(user, grupo):
    return user.is_superuser or grupo.grupousuario_set.filter(usuario=user).exists()

@register.filter
def has_admin_grupo_perm(user, grupo):
    return user.is_superuser or grupo.grupousuario_set.filter(usuario=user, admin=True).exists()

@register.filter
def num_topicos_nao_lidos(user, grupo):
    return grupo.num_topicos_nao_lidos(user)

@register.filter
def num_topicos_nao_lidos_all(user):
    total = 0
    for grupousuario in user.grupousuario_set.all():
        total += grupousuario.grupo.num_topicos_nao_lidos(user)
    return total

@register.filter
def num_conversa_nao_lidas(user, topico):
    return topico.num_conversa_nao_lidas(user)

@register.filter
def num_conversa_nao_lidas_all(user):
    total = 0
    for topico in Topico.objects.filter(topicoouvinte__ouvinte=user):
        total += topico.num_conversa_nao_lidas(user)
    return total


@register.filter
def has_delete_conversa(conversa, user):
    return conversa.has_delete(user)

@register.filter
def percent(valor, total):
    return (float(valor)/float(total))*100
