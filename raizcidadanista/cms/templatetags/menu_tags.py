# coding: utf-8
from django import template
from cms.models import Menu
from django.template import loader, Context
from urlparse import urlparse


register = template.Library()


@register.simple_tag(takes_context=True)
def show_menu(context, name=None, template='includes/menu.html'):
    menu_itens_pk = []
    itens = Menu.objects.filter(is_active=True)
    if name:
        parent = Menu.objects.get_or_create(name=name)[0]
        itens = parent.get_descendants().filter(is_active=True)
    for menu in itens:
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
