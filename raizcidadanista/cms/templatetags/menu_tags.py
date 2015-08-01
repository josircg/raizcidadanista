# coding: utf-8
from django import template
from cms.models import Menu, TipoMenu
from django.template import loader, Context
from urlparse import urlparse


register = template.Library()


@register.simple_tag(takes_context=True)
def show_menu(context, name, template='includes/menu.html'):
    menu_itens_pk = []
    for menu in Menu.objects.filter(tipo__name=name, is_active=True):
        if menu.have_perm(context.get('request').user):
            menu_itens_pk.append(menu.pk)

    return loader.get_template(template).render(Context({
            'request': context.get('request', None),
            'menu_itens': Menu.objects.filter(pk__in=menu_itens_pk),
            'template': template,
        })
    )


@register.filter
def is_active(menu, request):
    menu_url = menu.get_link()
    if menu_url:
        parsed_menu_url = urlparse(menu_url)
        return parsed_menu_url.path == request.path

    return False
