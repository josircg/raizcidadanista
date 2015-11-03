# -*- coding: utf-8 -*-
"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'menu.CustomMenu'
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from admin_tools.menu import items, Menu
from admin_tools.menu.items import MenuItem



class CustomAppList(items.AppList):

    def __init__(self, title=None, **kwargs):
        self.extra = list(kwargs.pop('extra', []))
        super(CustomAppList, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        items = self._visible_models(context['request'])
        for model, perms in items:
            if not perms['change']:
                continue
            item = MenuItem(title=capfirst(model._meta.verbose_name_plural), url=self._get_admin_change_url(model, context))
            self.children.append(item)

        if self.extra:
            for item in self.extra:
                self.children.append(item)


class CustomMenu(Menu):

    def init_with_context(self, context):

        configuracoes_extra = []
        if context.get('request').user.has_perm('auth.view_filebrowser'):
            configuracoes_extra.append(items.MenuItem(title=_(u'Visualizador de Arquivos'), url=reverse('filebrowser:fb_browse')))


        self.children += [
            items.MenuItem(' ', reverse('admin:index')),
            items.Bookmarks(_('Favoritos')),
            CustomAppList(
                u'CMS',
                exclude=('raizcidadanista.cms.models.EmailAgendado', 'raizcidadanista.cms.models.Recurso', 'raizcidadanista.cms.models.Theme', ),
                models=('raizcidadanista.cms.models.Section', 'raizcidadanista.cms.models.Article', 'raizcidadanista.cms.models.ArticleComment', 'raizcidadanista.cms.models.Menu', ),
            ),
            CustomAppList(
                u'Configurações',
                models=('raizcidadanista.cms.models.Recurso', 'raizcidadanista.cms.models.Theme', ),
                extra=configuracoes_extra
            ),
            CustomAppList(
                u'Cadastro',
                models=('cadastro.models.*', ),
                exclude=('cadastro.models.ListaCadastro', ),
            ),
            CustomAppList(
                u'Fórum',
                models=('forum.models.*', ),
            ),
            CustomAppList(
                u'Financeiro',
                models=('financeiro.models.*', ),
            ),
            CustomAppList(
                u'Adminstração',
                models=('django.contrib.*', 'utils.models.*', 'raizcidadanista.cms.models.EmailAgendado', ),
                exclude=('django.contrib.sites.models.*', ),
            ),
        ]
