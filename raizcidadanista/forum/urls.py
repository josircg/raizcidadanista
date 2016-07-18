# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from forum import views

urlpatterns = [
    url(r'^$', login_required(views.ForumView.as_view()), name='forum'),
    url(r'^diretorio/$', login_required(views.DiretorioView.as_view()), name='forum_diretorio'),
    url(r'^nao-lidos/$', login_required(views.NaoLidosView.as_view()), name='forum_nao_lidos'),
    url(r'^recentes/$', login_required(views.RecentesView.as_view()), name="forum_recentes"),
    url(r'^meu-perfil/$', login_required(views.MeuPerfilView.as_view()), name="forum_meu_perfil"),
    url(r'^pesquisa/$', login_required(views.PesquisaView.as_view()), name="forum_pesquisa"),
    url(r'^grupo/(?P<pk>\d+)/$', login_required(views.GrupoView.as_view()), name='forum_grupo'),
    url(r'^grupo/(?P<pk>\d+)/solicitar-ingresso/$', login_required(views.SolicitarIngressoView.as_view()), name='forum_grupo_solicitar_ingresso'),
    url(r'^grupo/(?P<pk>\d+)/solicitar-ingresso/(?P<user_pk>\d+)/$', login_required(views.SolicitarIngressoAprovarView.as_view()), name='forum_grupo_solicitar_ingresso_aprovar'),
    url(r'^grupo/(?P<pk>\d+)/editar/$', login_required(views.GrupoEditView.as_view()), name='forum_grupo_edit'),
    url(r'^grupo/(?P<pk>\d+)/editar-membros/$', login_required(views.GrupoEditMembrosView.as_view()), name='forum_grupo_edit_membros'),
    url(r'^grupo/(?P<pk>\d+)/adicionar-membros/$', login_required(views.GrupoAddMembrosView.as_view()), name='forum_grupo_add_membros'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/adicionar/$', login_required(views.TopicoAddView.as_view()), name='forum_topico_add'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/$', login_required(views.TopicoView.as_view()), name='forum_topico'),
    url(r'^mencao/$', login_required(views.MencaoView.as_view()), name='forum_mencao'),
]
