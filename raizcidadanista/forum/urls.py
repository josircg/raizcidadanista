# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required

from forum import views

urlpatterns = [
    url(r'^$', login_required(views.ForumFilterView.as_view()), name='forum'),
    url(r'^meus-grupos/$', login_required(views.ForumView.as_view()), name='forum_meus_grupos'),
    url(r'^diretorio/$', login_required(views.DiretorioView.as_view()), name='forum_diretorio'),
    url(r'^nao-lidos/$', login_required(views.NaoLidosView.as_view()), name='forum_nao_lidos'),
    url(r'^recentes/$', login_required(views.RecentesView.as_view()), name="forum_recentes"),
    url(r'^meu-perfil/$', login_required(views.MeuPerfilView.as_view()), name="forum_meu_perfil"),
    url(r'^pesquisa/$', login_required(views.PesquisaView.as_view()), name="forum_pesquisa"),
    url(r'^grupo/(?P<pk>\d+)/$', login_required(views.GrupoView.as_view()), name='forum_grupo'),
    url(r'^grupo/(?P<pk>\d+)/solicitar-ingresso/$', login_required(views.SolicitarIngressoView.as_view()), name='forum_grupo_solicitar_ingresso'),
    url(r'^grupo/(?P<pk>\d+)/sair/$', login_required(views.SaidaGrupoView.as_view()), name='forum_grupo_sair'),
    url(r'^grupo/(?P<pk>\d+)/solicitar-ingresso/(?P<user_pk>\d+)/$', login_required(views.SolicitarIngressoAprovarView.as_view()), name='forum_grupo_solicitar_ingresso_aprovar'),
    url(r'^grupo/(?P<pk>\d+)/editar/$', login_required(views.GrupoEditView.as_view()), name='forum_grupo_edit'),
    url(r'^grupo/(?P<pk>\d+)/editar-membros/$', login_required(views.GrupoEditMembrosView.as_view()), name='forum_grupo_edit_membros'),
    url(r'^grupo/(?P<pk>\d+)/adicionar-membros/$', login_required(views.GrupoAddMembrosView.as_view()), name='forum_grupo_add_membros'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/adicionar/$', login_required(views.TopicoAddView.as_view()), name='forum_topico_add'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/editar/$', login_required(views.TopicoEditView.as_view()), name='forum_topico_edit'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/$', login_required(views.TopicoView.as_view()), name='forum_topico'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/notificar/$', login_required(views.NotificarTopicoView.as_view()), name='forum_topico_notificar'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/adicionar-proposta/$', login_required(views.NovaPropostaTopicoView.as_view()), name='forum_topico_novaproposta'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<topico_pk>\d+)/proposta/(?P<pk>\d+)/$', login_required(views.PropostaTopicoView.as_view()), name='forum_topico_proposta'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<pk>\d+)/adicionar-enquete/$', login_required(views.NovaEnqueteTopicoView.as_view()), name='forum_topico_novaenquete'),
    url(r'^grupo/(?P<grupo_pk>\d+)/topico/(?P<topico_pk>\d+)/enquete/(?P<pk>\d+)/$', login_required(views.EnqueteTopicoView.as_view()), name='forum_topico_enquete'),
    url(r'^mencao/$', login_required(views.MencaoView.as_view()), name='forum_mencao'),
]
