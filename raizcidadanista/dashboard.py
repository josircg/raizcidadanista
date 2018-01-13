# -*- coding: utf-8 -*-
"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'dashboard.CustomAppIndexDashboard'
"""

from django.core.urlresolvers import reverse

from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for base-tools.
    """
    title = ''
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        request = context['request']

        financeiro_children = []
        if request.user.has_perm('auth.view_caixa'):
            financeiro_children.append({'title': u'Caixa', 'change_url': reverse('financeiro_caixa')})

        self.children += [
            modules.ModelList(
                u'Portal',
                models=('raizcidadanista.cms.models.Section', 'raizcidadanista.cms.models.Article', 'raizcidadanista.cms.models.ArticleComment', 'raizcidadanista.cms.models.Menu', 'raizcidadanista.cms.models.URLMigrate', 'raizcidadanista.cms.models.FileDownload', ),
            ),
            modules.ModelList(
                u'Cadastro',
                models=(
                    'cadastro.models.Membro', 'cadastro.models.Filiado','cadastro.models.Pessoa',
                    'cadastro.models.ColetaArticulacao', 'cadastro.models.Coligacao',
                    'cadastro.models.Campanha', 'cadastro.models.Lista',),
            ),
            modules.ModelList(
                u'Círculos',
                models=(
                    'cadastro.models.Circulo', 'cadastro.models.CirculoPendente', 'cadastro.models.CirculoEvento', 'cadastro.models.ArticleCadastro',
                    'municipios.models.*',),
            ),
            modules.ModelList(
                u'Teia Digital', [
                    'forum.models.*',
                ]
            ),
            modules.ModelList(
                u'Financeiro',
                models=[
                    'financeiro.models.*',
                ],
                children=financeiro_children
            ),
            modules.ModelList(
                u'Configurações',
                models=('raizcidadanista.cms.models.Recurso', 'raizcidadanista.cms.models.Theme', 'raizcidadanista.cms.models.URLNotFound', ),
                extra=[
                    {'title': u'Visualizador de Arquivos', 'add_url': reverse('filebrowser:fb_upload'), 'change_url': reverse('filebrowser:fb_browse')},
                ]
            ),
            modules.ModelList(
                u'Administração',
                models=('django.contrib.*', 'utils.models.*', 'raizcidadanista.cms.models.EmailAgendado', ),
                exclude=('django.contrib.sites.models.*', ),
            ),
            modules.LinkList(
                u'Links Rápidos',
                layout='inline',
                draggable=True,
                deletable=True,
                collapsible=True,
                children=[
                    [u'Portal', '/'],
                    [u'Sugerir Artigo', reverse('admin:cms_article_add_power')],
                    [u'Alterar Senha', reverse('admin:password_change')],
                    [u'Reset Menu', reverse('admin:reset_dashboard')],
                    [u'Sair', reverse('admin:logout')],
                ]
            ),
            modules.RecentActions(u'Últimas mudanças', 5),
        ]


class CustomAppIndexDashboard(AppIndexDashboard):
    """
    Custom app index dashboard for base-tools.
    """

    # we disable title because its redundant with the model list module
    title = ''

    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        # append a model list module and a recent actions module
        self.children += [
            modules.ModelList(self.app_title, self.models),
            modules.RecentActions(
                u'Ações Recentes',
                include_list=self.get_app_content_types(),
                limit=5
            )
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomAppIndexDashboard, self).init_with_context(context)
